from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PLATFORM_DOMAIN: str = "platform.localhost"
    PLATFORM_NAME: str = "DeployStack"
    SECRET_KEY: str = "change-me-in-production"
    ENCRYPTION_KEY: str = "change-me-32-byte-key-for-fernet"

    DATABASE_URL: str = "postgresql+asyncpg://deploy:deploy@localhost:5432/deploystack"
    DATABASE_URL_SYNC: str = "postgresql://deploy:deploy@localhost:5432/deploystack"

    REDIS_URL: str = "redis://localhost:6379/0"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_CALLBACK_URL: str = "http://localhost:3000/auth/callback"
    GITHUB_WEBHOOK_SECRET: str = ""

    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY: str = ""
    GITHUB_APP_INSTALLATION_ID: str = ""

    CLOUDFLARE_API_TOKEN: str = ""
    CLOUDFLARE_ZONE_ID: str = ""

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_S3_REGION: str = "us-east-1"
    USE_S3_ARTIFACTS: bool = False

    TRAEFIK_NETWORK: str = "traefik-public"

    MAX_CONCURRENT_BUILDS: int = 3
    BUILD_TIMEOUT_SECONDS: int = 600
    MAX_BUILD_MEMORY_MB: int = 2048
    MAX_BUILD_CPU: float = 2.0
    MAX_DEPLOYMENT_SIZE_MB: int = 500
    MAX_PROJECTS_PER_USER: int = 20
    MAX_DEPLOYMENTS_PER_DAY: int = 50

    ARTIFACTS_PATH: str = "/data/artifacts"
    DEPLOYMENTS_PATH: str = "/data/deployments"
    LOGS_PATH: str = "/data/logs"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: str = "http://localhost:8000"

    ADMIN_EMAIL: str = ""

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    @property
    def platform_url(self) -> str:
        return f"https://{self.PLATFORM_DOMAIN}"


settings = Settings()
