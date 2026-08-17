import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import encrypt_value, generate_verification_token
from app.database import get_db
from app.models import Domain, EnvironmentVariable, Project, User
from app.schemas import (
    DomainCreate,
    DomainResponse,
    EnvVarCreate,
    EnvVarResponse,
    ResponseModel,
)
from app.services.cloudflare import CloudflareService

router = APIRouter(tags=["domains-env"])


async def _get_project(project_id: uuid.UUID, user: User, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(
            Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/domains", response_model=ResponseModel[list[DomainResponse]])
async def list_domains(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(project_id, user, db)
    result = await db.execute(
        select(Domain).where(Domain.project_id == project_id, Domain.deleted_at.is_(None))
    )
    domains = result.scalars().all()
    return ResponseModel(data=[DomainResponse.model_validate(d) for d in domains])


@router.post("/projects/{project_id}/domains", response_model=ResponseModel[DomainResponse])
async def add_domain(
    project_id: uuid.UUID,
    data: DomainCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project(project_id, user, db)

    existing = await db.execute(select(Domain).where(Domain.domain == data.domain))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already registered")

    verification_token = generate_verification_token()
    dns_records = CloudflareService.get_dns_instructions(
        data.domain, verification_token, settings.PLATFORM_DOMAIN
    )

    domain = Domain(
        project_id=project.id,
        domain=data.domain,
        verification_token=verification_token,
        verification_method="dns",
        dns_records=dns_records,
    )
    db.add(domain)
    await db.flush()

    return ResponseModel(data=DomainResponse.model_validate(domain))


@router.post("/domains/{domain_id}/verify", response_model=ResponseModel[DomainResponse])
async def verify_domain(
    domain_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Domain, Project)
        .join(Project, Domain.project_id == Project.id)
        .where(Domain.id == domain_id, Project.user_id == user.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain, project = row

    if domain.verification_token:
        verified = await CloudflareService.verify_domain(
            domain.domain, domain.verification_token
        )
        if verified:
            domain.is_verified = True
            domain.ssl_status = "active"

            if project.active_deployment_id and domain.is_verified:
                from app.models import Deployment
                dep_result = await db.execute(
                    select(Deployment).where(Deployment.id == project.active_deployment_id)
                )
                deployment = dep_result.scalar_one_or_none()
                if deployment and deployment.container_name:
                    from app.services.routing import RoutingService
                    port = 3000 if project.deployment_type == "server" else 80
                    await RoutingService.add_custom_domain(
                        domain.domain, deployment.container_name, port
                    )

    return ResponseModel(data=DomainResponse.model_validate(domain))


@router.delete("/domains/{domain_id}")
async def delete_domain(
    domain_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Domain, Project)
        .join(Project, Domain.project_id == Project.id)
        .where(Domain.id == domain_id, Project.user_id == user.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Domain not found")

    domain = row[0]
    from datetime import datetime, timezone
    domain.deleted_at = datetime.now(timezone.utc)
    return ResponseModel(data={"deleted": True})


@router.get("/projects/{project_id}/env", response_model=ResponseModel[list[EnvVarResponse]])
async def list_env_vars(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    environment: str = "production",
):
    await _get_project(project_id, user, db)
    result = await db.execute(
        select(EnvironmentVariable).where(
            EnvironmentVariable.project_id == project_id,
            EnvironmentVariable.environment == environment,
        )
    )
    vars = result.scalars().all()
    responses = []
    for v in vars:
        responses.append(
            EnvVarResponse(
                id=v.id,
                key=v.key,
                value="*****" if v.is_secret else None,
                environment=v.environment,
                is_secret=v.is_secret,
                created_at=v.created_at,
            )
        )
    return ResponseModel(data=responses)


@router.post("/projects/{project_id}/env", response_model=ResponseModel[EnvVarResponse])
async def create_env_var(
    project_id: uuid.UUID,
    data: EnvVarCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(project_id, user, db)

    env_var = EnvironmentVariable(
        project_id=project_id,
        key=data.key,
        value_encrypted=encrypt_value(data.value),
        environment=data.environment,
        is_secret=data.is_secret,
    )
    db.add(env_var)
    await db.flush()

    return ResponseModel(
        data=EnvVarResponse(
            id=env_var.id,
            key=env_var.key,
            value="*****" if env_var.is_secret else data.value,
            environment=env_var.environment,
            is_secret=env_var.is_secret,
            created_at=env_var.created_at,
        )
    )


@router.delete("/projects/{project_id}/env/{env_id}")
async def delete_env_var(
    project_id: uuid.UUID,
    env_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_project(project_id, user, db)
    result = await db.execute(
        select(EnvironmentVariable).where(
            EnvironmentVariable.id == env_id, EnvironmentVariable.project_id == project_id
        )
    )
    env_var = result.scalar_one_or_none()
    if not env_var:
        raise HTTPException(status_code=404, detail="Environment variable not found")
    await db.delete(env_var)
    return ResponseModel(data={"deleted": True})
