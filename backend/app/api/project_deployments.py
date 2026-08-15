import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import generate_verification_token
from app.database import get_db
from app.models import Deployment, Project, User
from app.schemas import DeploymentResponse, ResponseModel
from app.services.cloudflare import CloudflareService

router = APIRouter(tags=["project-nested"])


@router.get("/projects/{project_id}/deployments", response_model=ResponseModel[list[DeploymentResponse]])
async def list_project_deployments(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
        .limit(limit)
    )
    deployments = result.scalars().all()
    return ResponseModel(data=[DeploymentResponse.model_validate(d) for d in deployments])
