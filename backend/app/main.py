from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.deployments import router as deployments_router
from app.api.domains import router as domains_router
from app.api.logs import router as logs_router
from app.api.project_deployments import router as project_deployments_router
from app.api.projects import router as projects_router
from app.api.webhooks import router as webhooks_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.PLATFORM_NAME,
    description="Self-hosted deployment platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(deployments_router, prefix="/api")
app.include_router(project_deployments_router, prefix="/api")
app.include_router(domains_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(logs_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "healthy", "platform": settings.PLATFORM_NAME}


@app.get("/")
async def root():
    return {
        "name": settings.PLATFORM_NAME,
        "version": "1.0.0",
        "docs": "/docs",
    }
