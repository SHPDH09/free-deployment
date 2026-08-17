import json
import uuid
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decrypt_value
from app.models import (
    BuildJob,
    Deployment,
    DeploymentLog,
    DeploymentStatus,
    GitHubAccount,
    Project,
)

redis_client: aioredis.Redis | None = None

QUEUE_KEY = "deploystack:build_queue"
LOG_CHANNEL_PREFIX = "deploystack:logs:"


async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


class GitHubService:
    BASE_URL = "https://api.github.com"

    @staticmethod
    async def get_access_token(db: AsyncSession, user_id: uuid.UUID) -> str | None:
        result = await db.execute(select(GitHubAccount).where(GitHubAccount.user_id == user_id))
        account = result.scalar_one_or_none()
        if not account:
            return None
        return decrypt_value(account.access_token_encrypted)

    @staticmethod
    async def exchange_code(code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
            )
            if response.status_code != 200:
                raise ValueError(f"GitHub OAuth failed: {response.text}")
            return response.json()

    @staticmethod
    async def get_user_info(access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.BASE_URL}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to get GitHub user: {response.text}")
            return response.json()

    @staticmethod
    async def list_repos(access_token: str, page: int = 1, per_page: int = 100) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.BASE_URL}/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "page": page,
                    "per_page": per_page,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member",
                },
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to list repos: {response.text}")
            return response.json()

    @staticmethod
    async def list_branches(access_token: str, repo_full_name: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.BASE_URL}/repos/{repo_full_name}/branches",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to list branches: {response.text}")
            return response.json()

    @staticmethod
    async def get_commit(access_token: str, repo_full_name: str, ref: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.BASE_URL}/repos/{repo_full_name}/commits/{ref}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to get commit: {response.text}")
            return response.json()

    @staticmethod
    async def create_webhook(access_token: str, repo_full_name: str, webhook_url: str, secret: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GitHubService.BASE_URL}/repos/{repo_full_name}/hooks",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
                json={
                    "name": "web",
                    "active": True,
                    "events": ["push"],
                    "config": {
                        "url": webhook_url,
                        "content_type": "json",
                        "secret": secret,
                        "insecure_ssl": "0",
                    },
                },
            )
            if response.status_code not in (200, 201):
                raise ValueError(f"Failed to create webhook: {response.text}")
            return response.json()


FRAMEWORK_PRESETS = {
    "nextjs": {
        "framework": "nextjs",
        "deployment_type": "server",
        "install_command": "npm install",
        "build_command": "npm run build",
        "output_directory": ".next",
        "start_command": "npm start",
        "node_version": "20",
    },
    "react": {
        "framework": "react",
        "deployment_type": "static",
        "install_command": "npm install",
        "build_command": "npm run build",
        "output_directory": "build",
        "node_version": "20",
    },
    "vite": {
        "framework": "vite",
        "deployment_type": "static",
        "install_command": "npm install",
        "build_command": "npm run build",
        "output_directory": "dist",
        "node_version": "20",
    },
    "vue": {
        "framework": "vue",
        "deployment_type": "static",
        "install_command": "npm install",
        "build_command": "npm run build",
        "output_directory": "dist",
        "node_version": "20",
    },
    "angular": {
        "framework": "angular",
        "deployment_type": "static",
        "install_command": "npm install",
        "build_command": "npm run build",
        "output_directory": "dist",
        "node_version": "20",
    },
    "nodejs": {
        "framework": "nodejs",
        "deployment_type": "server",
        "install_command": "npm install",
        "build_command": "",
        "start_command": "npm start",
        "node_version": "20",
    },
    "python": {
        "framework": "python",
        "deployment_type": "server",
        "install_command": "pip install -r requirements.txt",
        "build_command": "",
        "start_command": "python main.py",
        "python_version": "3.12",
    },
    "fastapi": {
        "framework": "fastapi",
        "deployment_type": "server",
        "install_command": "pip install -r requirements.txt",
        "build_command": "",
        "start_command": "uvicorn main:app --host 0.0.0.0 --port 3000",
        "python_version": "3.12",
    },
    "flask": {
        "framework": "flask",
        "deployment_type": "server",
        "install_command": "pip install -r requirements.txt",
        "build_command": "",
        "start_command": "flask run --host=0.0.0.0 --port=3000",
        "python_version": "3.12",
    },
    "static": {
        "framework": "static",
        "deployment_type": "static",
        "install_command": "",
        "build_command": "",
        "output_directory": ".",
    },
}


def detect_framework(repo_files: list[str]) -> dict | None:
    files_lower = {f.lower() for f in repo_files}
    if any(f in files_lower for f in ("next.config.js", "next.config.ts", "next.config.mjs")):
        return FRAMEWORK_PRESETS["nextjs"]
    if any(f in files_lower for f in ("vite.config.ts", "vite.config.js")):
        return FRAMEWORK_PRESETS["vite"]
    if "angular.json" in files_lower:
        return FRAMEWORK_PRESETS["angular"]
    if "vue.config.js" in files_lower:
        return FRAMEWORK_PRESETS["vue"]
    if "package.json" in files_lower:
        return FRAMEWORK_PRESETS["react"]
    if "requirements.txt" in files_lower:
        return FRAMEWORK_PRESETS["python"]
    if any(f.endswith(".html") for f in files_lower):
        return FRAMEWORK_PRESETS["static"]
    return None


class DeploymentService:
    @staticmethod
    async def get_next_version(db: AsyncSession, project_id: uuid.UUID) -> int:
        result = await db.execute(
            select(func.max(Deployment.version)).where(Deployment.project_id == project_id)
        )
        max_version = result.scalar() or 0
        return max_version + 1

    @staticmethod
    def generate_urls(project_slug: str, deployment_id: uuid.UUID, is_preview: bool = False) -> tuple[str, str | None]:
        domain = settings.PLATFORM_DOMAIN
        production_url = f"https://{project_slug}.{domain}"
        preview_url = None
        if is_preview:
            short_id = str(deployment_id).split("-")[0]
            preview_url = f"https://{short_id}.{project_slug}.{domain}"
        return production_url, preview_url

    @staticmethod
    async def create_deployment(
        db: AsyncSession,
        project: Project,
        branch: str | None = None,
        triggered_by: str = "manual",
        is_preview: bool = False,
        commit_sha: str | None = None,
        commit_message: str | None = None,
        author_name: str | None = None,
        author_email: str | None = None,
    ) -> Deployment:
        version = await DeploymentService.get_next_version(db, project.id)
        deployment = Deployment(
            project_id=project.id,
            version=version,
            branch=branch or project.default_branch,
            is_production=not is_preview,
            is_preview=is_preview,
            status=DeploymentStatus.PENDING.value,
            build_status=DeploymentStatus.PENDING.value,
            deployment_status=DeploymentStatus.PENDING.value,
            triggered_by=triggered_by,
            commit_sha=commit_sha,
            commit_message=commit_message,
            author_name=author_name,
            author_email=author_email,
        )
        db.add(deployment)
        await db.flush()

        production_url, preview_url = DeploymentService.generate_urls(
            project.slug, deployment.id, is_preview
        )
        deployment.deployment_url = production_url if not is_preview else None
        deployment.preview_url = preview_url if is_preview else None

        build_job = BuildJob(
            deployment_id=deployment.id,
            project_id=project.id,
            status="pending",
        )
        db.add(build_job)
        await db.flush()

        await DeploymentService.enqueue_build(deployment.id, build_job.id)

        return deployment

    @staticmethod
    async def enqueue_build(deployment_id: uuid.UUID, job_id: uuid.UUID):
        redis = await get_redis()
        await redis.lpush(
            QUEUE_KEY,
            json.dumps({
                "deployment_id": str(deployment_id),
                "job_id": str(job_id),
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }),
        )

    @staticmethod
    async def add_log(
        db: AsyncSession,
        deployment_id: uuid.UUID,
        message: str,
        level: str = "info",
        step: str | None = None,
        is_user_visible: bool = True,
    ):
        log = DeploymentLog(
            deployment_id=deployment_id,
            message=message,
            level=level,
            step=step,
            is_user_visible=is_user_visible,
        )
        db.add(log)
        await db.flush()

        redis = await get_redis()
        await redis.publish(
            f"{LOG_CHANNEL_PREFIX}{deployment_id}",
            json.dumps({
                "message": message,
                "level": level,
                "step": step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )

    @staticmethod
    async def rollback(db: AsyncSession, deployment: Deployment, project: Project) -> Deployment:
        if deployment.status != DeploymentStatus.SUCCESS.value:
            raise ValueError("Can only rollback to a successful deployment")

        project.active_deployment_id = deployment.id

        from app.services.routing import RoutingService
        await RoutingService.activate_deployment(project, deployment)

        return deployment
