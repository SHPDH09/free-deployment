import hashlib
import hmac
import json
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models import Deployment, DeploymentStatus, Project, User
from app.schemas import DashboardStats, DeploymentResponse, ResponseModel
from app.services.github import DeploymentService, GitHubService

router = APIRouter(tags=["webhooks-dashboard"])


@router.post("/webhooks/github")
async def github_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
):
    body = await request.body()

    if settings.GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = x_github_event or payload.get("action")

    if x_github_event == "push":
        repo_full_name = payload.get("repository", {}).get("full_name")
        ref = payload.get("ref", "")
        branch = ref.replace("refs/heads/", "")

        result = await db.execute(
            select(Project).where(
                Project.github_repo_full_name == repo_full_name,
                Project.deleted_at.is_(None),
                Project.is_suspended.is_(False),
            )
        )
        projects = result.scalars().all()

        head_commit = payload.get("head_commit", {})
        commit_sha = head_commit.get("id")
        commit_message = head_commit.get("message")
        author_name = head_commit.get("author", {}).get("name")
        author_email = head_commit.get("author", {}).get("email")

        for project in projects:
            if project.default_branch != branch:
                continue

            from app.models import ProjectSettings
            settings_result = await db.execute(
                select(ProjectSettings).where(ProjectSettings.project_id == project.id)
            )
            project_settings = settings_result.scalar_one_or_none()
            if project_settings and not project_settings.auto_deploy:
                continue

            await DeploymentService.create_deployment(
                db,
                project,
                branch=branch,
                triggered_by="webhook",
                commit_sha=commit_sha,
                commit_message=commit_message,
                author_name=author_name,
                author_email=author_email,
            )

    return {"status": "ok"}


@router.get("/dashboard/stats", response_model=ResponseModel[DashboardStats])
async def dashboard_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects_count = await db.execute(
        select(func.count(Project.id)).where(
            Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    total_projects = projects_count.scalar() or 0

    project_ids_result = await db.execute(
        select(Project.id).where(Project.user_id == user.id, Project.deleted_at.is_(None))
    )
    project_ids = [r[0] for r in project_ids_result.all()]

    if not project_ids:
        return ResponseModel(
            data=DashboardStats(
                total_projects=0,
                successful_deployments=0,
                failed_deployments=0,
                active_deployments=0,
                recent_deployments=[],
                resource_usage={},
            )
        )

    success_count = await db.execute(
        select(func.count(Deployment.id)).where(
            Deployment.project_id.in_(project_ids),
            Deployment.status == DeploymentStatus.SUCCESS.value,
        )
    )
    failed_count = await db.execute(
        select(func.count(Deployment.id)).where(
            Deployment.project_id.in_(project_ids),
            Deployment.status == DeploymentStatus.FAILED.value,
        )
    )
    active_count = await db.execute(
        select(func.count(Deployment.id)).where(
            Deployment.project_id.in_(project_ids),
            Deployment.status.in_([
                DeploymentStatus.PENDING.value,
                DeploymentStatus.QUEUED.value,
                DeploymentStatus.BUILDING.value,
                DeploymentStatus.DEPLOYING.value,
            ]),
        )
    )

    recent_result = await db.execute(
        select(Deployment)
        .where(Deployment.project_id.in_(project_ids))
        .order_by(Deployment.created_at.desc())
        .limit(10)
    )
    recent = recent_result.scalars().all()

    return ResponseModel(
        data=DashboardStats(
            total_projects=total_projects,
            successful_deployments=success_count.scalar() or 0,
            failed_deployments=failed_count.scalar() or 0,
            active_deployments=active_count.scalar() or 0,
            recent_deployments=[DeploymentResponse.model_validate(d) for d in recent],
            resource_usage={
                "cpu_percent": 0,
                "memory_mb": 0,
                "disk_mb": 0,
            },
        )
    )
