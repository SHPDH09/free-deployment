import base64
import hashlib
import json
import logging
import os
import shutil
import socket
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("worker")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL_SYNC: str = "postgresql://deploy:deploy@localhost:5432/deploystack"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me"
    ENCRYPTION_KEY: str = "change-me"
    PLATFORM_DOMAIN: str = "platform.localhost"
    TRAEFIK_NETWORK: str = "traefik-public"

    MAX_CONCURRENT_BUILDS: int = 3
    BUILD_TIMEOUT_SECONDS: int = 600
    MAX_BUILD_MEMORY_MB: int = 2048
    MAX_BUILD_CPU: float = 2.0
    MAX_DEPLOYMENT_SIZE_MB: int = 500

    ARTIFACTS_PATH: str = "/data/artifacts"
    DEPLOYMENTS_PATH: str = "/data/deployments"
    LOGS_PATH: str = "/data/logs"
    BUILDS_PATH: str = "/data/builds"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"
    USE_S3_ARTIFACTS: bool = False

    WORKER_ID: str = ""


settings = Settings()
if not settings.WORKER_ID:
    settings.WORKER_ID = f"worker-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


def get_fernet():
    from cryptography.fernet import Fernet

    key = settings.ENCRYPTION_KEY
    if len(key) < 32:
        key = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()).decode()
    return Fernet(key.encode())


def decrypt_value(encrypted: str) -> str:
    return get_fernet().decrypt(encrypted.encode()).decode()

