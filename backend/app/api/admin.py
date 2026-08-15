import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.database import get_db
from app.models import AuditLog, Deployment, DeploymentStatus, Project, User, Worker
from app.schemas import AdminStats, DeploymentResponse, ProjectResponse, ResponseModel, UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=ResponseModel[AdminStats])
async def admin_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    users = await db.execute(select(func.count(User.id)))
    projects = await db.execute(select(func.count(Project.id)).where(Project.deleted_at.is_(None)))
    deployments = await db.execute(select(func.count(Deployment.id)))
    workers = await db.execute(select(func.count(Worker.id)))
    failed_24h = await db.execute(
        select(func.count(Deployment.id)).where(
            Deployment.status == DeploymentStatus.FAILED.value,
        )
    )

    return ResponseModel(
        data=AdminStats(
            total_users=users.scalar() or 0,
            total_projects=projects.scalar() or 0,
            total_deployments=deployments.scalar() or 0,
            active_containers=0,
            build_workers=workers.scalar() or 0,
            failed_deployments_24h=failed_24h.scalar() or 0,
            system_cpu=None,
            system_memory=None,
            system_disk=None,
        )
    )


@router.get("/users", response_model=ResponseModel[list[UserResponse]])
async def admin_list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    users = result.scalars().all()
    return ResponseModel(data=[UserResponse.model_validate(u) for u in users])


@router.get("/projects", response_model=ResponseModel[list[ProjectResponse]])
async def admin_list_projects(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    result = await db.execute(
        select(Project).where(Project.deleted_at.is_(None)).order_by(Project.created_at.desc()).limit(limit)
    )
    projects = result.scalars().all()
    return ResponseModel(data=[ProjectResponse.model_validate(p) for p in projects])


@router.get("/deployments", response_model=ResponseModel[list[DeploymentResponse]])
async def admin_list_deployments(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    result = await db.execute(
        select(Deployment).order_by(Deployment.created_at.desc()).limit(limit)
    )
    deployments = result.scalars().all()
    return ResponseModel(data=[DeploymentResponse.model_validate(d) for d in deployments])


@router.post("/projects/{project_id}/suspend")
async def suspend_project(
    project_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.is_suspended = True
    project.status = "suspended"
    return ResponseModel(data={"suspended": True})


@router.get("/audit-logs")
async def admin_audit_logs(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return ResponseModel(
        data=[
            {
                "id": str(l.id),
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": str(l.resource_id) if l.resource_id else None,
                "details": l.details,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ]
    )
