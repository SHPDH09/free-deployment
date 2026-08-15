import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Deployment, DeploymentLog, Project, User
from app.schemas import DeploymentLogResponse, DeploymentResponse, ResponseModel
from app.services.github import DeploymentService

router = APIRouter(prefix="/deployments", tags=["deployments"])


async def _get_deployment_for_user(
    deployment_id: uuid.UUID, user: User, db: AsyncSession
) -> tuple[Deployment, Project]:
    result = await db.execute(
        select(Deployment, Project)
        .join(Project, Deployment.project_id == Project.id)
        .where(Deployment.id == deployment_id, Project.user_id == user.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return row[0], row[1]


@router.get("/{deployment_id}", response_model=ResponseModel[DeploymentResponse])
async def get_deployment(
    deployment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deployment, _ = await _get_deployment_for_user(deployment_id, user, db)
    return ResponseModel(data=DeploymentResponse.model_validate(deployment))


@router.get("/{deployment_id}/logs", response_model=ResponseModel[list[DeploymentLogResponse]])
async def get_deployment_logs(
    deployment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(500, le=1000),
):
    await _get_deployment_for_user(deployment_id, user, db)

    result = await db.execute(
        select(DeploymentLog)
        .where(DeploymentLog.deployment_id == deployment_id, DeploymentLog.is_user_visible.is_(True))
        .order_by(DeploymentLog.created_at.asc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return ResponseModel(data=[DeploymentLogResponse.model_validate(l) for l in logs])


@router.post("/{deployment_id}/rollback", response_model=ResponseModel[DeploymentResponse])
async def rollback_deployment(
    deployment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deployment, project = await _get_deployment_for_user(deployment_id, user, db)

    try:
        result = await DeploymentService.rollback(db, deployment, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResponseModel(data=DeploymentResponse.model_validate(result))


@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deployment, project = await _get_deployment_for_user(deployment_id, user, db)

    from app.services.routing import RoutingService
    await RoutingService.remove_deployment_routes(project, deployment)

    await db.delete(deployment)
    return ResponseModel(data={"deleted": True})
