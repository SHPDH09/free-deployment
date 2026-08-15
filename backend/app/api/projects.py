import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user, log_audit, slugify
from app.database import get_db
from app.models import Deployment, DeploymentStatus, Project, ProjectSettings, User
from app.schemas import (
    DashboardStats,
    DeploymentResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ResponseModel,
)
from app.services.github import DeploymentService, FRAMEWORK_PRESETS, GitHubService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/frameworks/list", response_model=ResponseModel[list[dict]])
async def list_frameworks():
    frameworks = [
        {"id": k, "name": k.replace("_", " ").title(), **v}
        for k, v in FRAMEWORK_PRESETS.items()
    ]
    return ResponseModel(data=frameworks)


@router.get("", response_model=ResponseModel[list[ProjectResponse]])
async def list_projects(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.id, Project.deleted_at.is_(None))
        .order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()

    responses = []
    for p in projects:
        resp = ProjectResponse.model_validate(p)
        resp.deployment_url = f"https://{p.slug}.{settings.PLATFORM_DOMAIN}"
        responses.append(resp)

    return ResponseModel(data=responses)


@router.post("", response_model=ResponseModel[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    if count_result.scalar() >= settings.MAX_PROJECTS_PER_USER:
        raise HTTPException(status_code=400, detail="Maximum project limit reached")

    slug = slugify(data.name)
    existing = await db.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"

    preset = FRAMEWORK_PRESETS.get(data.framework or "") if data.framework else None

    project = Project(
        user_id=user.id,
        name=data.name,
        slug=slug,
        description=data.description,
        github_repo_full_name=data.github_repo_full_name,
        default_branch=data.default_branch,
        framework=data.framework or (preset and preset["framework"]),
        root_directory=data.root_directory,
        build_command=data.build_command or (preset and preset.get("build_command")),
        install_command=data.install_command or (preset and preset.get("install_command")),
        output_directory=data.output_directory or (preset and preset.get("output_directory")),
        start_command=data.start_command or (preset and preset.get("start_command")),
        node_version=data.node_version or (preset and preset.get("node_version")),
        python_version=data.python_version or (preset and preset.get("python_version")),
        deployment_type=data.deployment_type or (preset and preset.get("deployment_type", "static")),
    )
    db.add(project)
    await db.flush()

    settings_obj = ProjectSettings(project_id=project.id)
    db.add(settings_obj)
    await db.flush()

    token = await GitHubService.get_access_token(db, user.id)
    if token and settings.GITHUB_WEBHOOK_SECRET:
        try:
            webhook_url = f"{settings.API_URL}/api/webhooks/github"
            await GitHubService.create_webhook(
                token, data.github_repo_full_name, webhook_url, settings.GITHUB_WEBHOOK_SECRET
            )
        except Exception:
            pass

    await log_audit(db, user.id, "project_created", "project", project.id, request=request)

    resp = ProjectResponse.model_validate(project)
    resp.deployment_url = f"https://{project.slug}.{settings.PLATFORM_DOMAIN}"
    return ResponseModel(data=resp)


@router.get("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def get_project(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    resp = ProjectResponse.model_validate(project)
    resp.deployment_url = f"https://{project.slug}.{settings.PLATFORM_DOMAIN}"
    return ResponseModel(data=resp)


@router.patch("/{project_id}", response_model=ResponseModel[ProjectResponse])
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    resp = ProjectResponse.model_validate(project)
    resp.deployment_url = f"https://{project.slug}.{settings.PLATFORM_DOMAIN}"
    return ResponseModel(data=resp)


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from datetime import datetime, timezone
    project.deleted_at = datetime.now(timezone.utc)
    await log_audit(db, user.id, "project_deleted", "project", project.id, request=request)
    return ResponseModel(data={"deleted": True})


@router.post("/{project_id}/deploy", response_model=ResponseModel[DeploymentResponse])
async def deploy_project(
    project_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.is_suspended:
        raise HTTPException(status_code=403, detail="Project is suspended")

    commit_sha = None
    commit_message = None
    author_name = None
    author_email = None

    token = await GitHubService.get_access_token(db, user.id)
    if token:
        try:
            commit = await GitHubService.get_commit(token, project.github_repo_full_name, project.default_branch)
            commit_sha = commit.get("sha")
            commit_info = commit.get("commit", {})
            commit_message = commit_info.get("message")
            author = commit_info.get("author", {})
            author_name = author.get("name")
            author_email = author.get("email")
        except Exception:
            pass

    deployment = await DeploymentService.create_deployment(
        db,
        project,
        branch=project.default_branch,
        triggered_by="manual",
        commit_sha=commit_sha,
        commit_message=commit_message,
        author_name=author_name,
        author_email=author_email,
    )

    await log_audit(db, user.id, "deployment_triggered", "deployment", deployment.id, request=request)
    return ResponseModel(data=DeploymentResponse.model_validate(deployment))
