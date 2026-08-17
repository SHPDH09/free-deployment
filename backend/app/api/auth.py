import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user, log_audit, slugify
from app.core.security import create_access_token, encrypt_value
from app.database import get_db
from app.models import GitHubAccount, Project, ProjectSettings, User, UserRole
from app.schemas import GitHubAccountResponse, GitHubRepoResponse, ResponseModel, UserResponse
from app.services.github import GitHubService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github")
async def github_login():
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": "read:user user:email repo",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"https://github.com/login/oauth/authorize?{query}"}


@router.post("/github/callback")
async def github_callback(
    request: Request,
    code: str,
    db: AsyncSession = Depends(get_db),
):
    token_data = await GitHubService.exchange_code(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    github_user = await GitHubService.get_user_info(access_token)
    email = github_user.get("email") or f"{github_user['login']}@users.noreply.github.com"

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        is_admin = email == settings.ADMIN_EMAIL and settings.ADMIN_EMAIL
        user = User(
            email=email,
            name=github_user.get("name") or github_user["login"],
            avatar_url=github_user.get("avatar_url"),
            role=UserRole.ADMIN.value if is_admin else UserRole.USER.value,
        )
        db.add(user)
        await db.flush()

    result = await db.execute(select(GitHubAccount).where(GitHubAccount.user_id == user.id))
    account = result.scalar_one_or_none()

    if account:
        account.access_token_encrypted = encrypt_value(access_token)
        account.github_username = github_user["login"]
        account.github_id = str(github_user["id"])
    else:
        account = GitHubAccount(
            user_id=user.id,
            github_id=str(github_user["id"]),
            github_username=github_user["login"],
            access_token_encrypted=encrypt_value(access_token),
            scopes=token_data.get("scope"),
        )
        db.add(account)

    await log_audit(db, user.id, "github_connected", "user", user.id, request=request)

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    return ResponseModel(data=UserResponse.model_validate(user))


@router.get("/github/account", response_model=ResponseModel[GitHubAccountResponse | None])
async def get_github_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GitHubAccount).where(GitHubAccount.user_id == user.id))
    account = result.scalar_one_or_none()
    if not account:
        return ResponseModel(data=None, message="No GitHub account connected")
    return ResponseModel(data=GitHubAccountResponse.model_validate(account))


@router.get("/github/repos", response_model=ResponseModel[list[GitHubRepoResponse]])
async def list_github_repos(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = await GitHubService.get_access_token(db, user.id)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub account not connected")

    repos = await GitHubService.list_repos(token)
    data = [
        GitHubRepoResponse(
            id=r["id"],
            name=r["name"],
            full_name=r["full_name"],
            private=r["private"],
            default_branch=r.get("default_branch", "main"),
            html_url=r["html_url"],
            description=r.get("description"),
            language=r.get("language"),
        )
        for r in repos
    ]
    return ResponseModel(data=data)


@router.get("/github/repos/{owner}/{repo}/branches")
async def list_branches(
    owner: str,
    repo: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token = await GitHubService.get_access_token(db, user.id)
    if not token:
        raise HTTPException(status_code=400, detail="GitHub account not connected")

    branches = await GitHubService.list_branches(token, f"{owner}/{repo}")
    return ResponseModel(data=[{"name": b["name"]} for b in branches])
