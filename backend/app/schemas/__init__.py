import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    data: T
    message: str = "success"


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    per_page: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    created_at: datetime


class GitHubAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    github_username: str
    scopes: str | None
    created_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    github_repo_full_name: str
    default_branch: str = "main"
    framework: str | None = None
    root_directory: str = "."
    build_command: str | None = None
    install_command: str | None = None
    output_directory: str | None = None
    start_command: str | None = None
    node_version: str | None = None
    python_version: str | None = None
    deployment_type: str = "static"
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    default_branch: str | None = None
    framework: str | None = None
    root_directory: str | None = None
    build_command: str | None = None
    install_command: str | None = None
    output_directory: str | None = None
    start_command: str | None = None
    node_version: str | None = None
    python_version: str | None = None
    deployment_type: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    github_repo_full_name: str
    default_branch: str
    framework: str | None
    root_directory: str
    build_command: str | None
    install_command: str | None
    output_directory: str | None
    start_command: str | None
    node_version: str | None
    python_version: str | None
    deployment_type: str
    status: str
    is_suspended: bool
    active_deployment_id: uuid.UUID | None
    deployment_url: str | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    commit_sha: str | None
    commit_message: str | None
    branch: str
    author_name: str | None
    author_email: str | None
    status: str
    build_status: str
    deployment_status: str
    is_production: bool
    is_preview: bool
    deployment_url: str | None
    preview_url: str | None
    build_duration_ms: int | None
    deploy_duration_ms: int | None
    total_duration_ms: int | None
    error_message: str | None
    health_check_status: str | None
    triggered_by: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class DeploymentLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    level: str
    message: str
    step: str | None
    created_at: datetime


class DomainCreate(BaseModel):
    domain: str = Field(..., min_length=3, max_length=255)


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    domain: str
    is_primary: bool
    is_verified: bool
    verification_method: str | None
    dns_records: dict | list | None
    ssl_status: str
    created_at: datetime


class EnvVarCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: str
    environment: str = "production"
    is_secret: bool = True


class EnvVarResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: str | None = None
    environment: str
    is_secret: bool
    created_at: datetime


class DashboardStats(BaseModel):
    total_projects: int
    successful_deployments: int
    failed_deployments: int
    active_deployments: int
    recent_deployments: list[DeploymentResponse]
    resource_usage: dict[str, Any]


class GitHubRepoResponse(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    default_branch: str
    html_url: str
    description: str | None
    language: str | None


class FrameworkPreset(BaseModel):
    id: str
    name: str
    framework: str
    deployment_type: str
    install_command: str | None
    build_command: str | None
    output_directory: str | None
    start_command: str | None


class AdminStats(BaseModel):
    total_users: int
    total_projects: int
    total_deployments: int
    active_containers: int
    build_workers: int
    failed_deployments_24h: int
    system_cpu: float | None
    system_memory: float | None
    system_disk: float | None
