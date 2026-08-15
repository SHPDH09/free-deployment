import json
import os
from pathlib import Path

from app.config import settings


class RoutingService:
    DYNAMIC_CONFIG_PATH = "/etc/traefik/dynamic/deployments.json"

    @staticmethod
    def _get_local_config_path() -> str:
        local_path = os.environ.get("TRAEFIK_DYNAMIC_PATH", "./traefik/dynamic/deployments.json")
        return local_path

    @staticmethod
    async def activate_deployment(project, deployment) -> None:
        config_path = RoutingService._get_local_config_path()
        config_dir = Path(config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        routes = {}
        if Path(config_path).exists():
            with open(config_path) as f:
                routes = json.load(f).get("routes", {})

        domain = settings.PLATFORM_DOMAIN
        hostnames = [
            f"{project.slug}.{domain}",
        ]

        if deployment.is_preview and deployment.preview_url:
            preview_host = deployment.preview_url.replace("https://", "").replace("http://", "")
            hostnames.append(preview_host)

        container_port = 3000 if project.deployment_type == "server" else 80
        container_name = deployment.container_name or f"deploy-{str(deployment.id)[:8]}"

        for hostname in hostnames:
            routes[hostname] = {
                "service": container_name,
                "port": container_port,
                "deployment_id": str(deployment.id),
                "project_id": str(project.id),
            }

        config = {"routes": routes}
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    async def remove_deployment_routes(project, deployment) -> None:
        config_path = RoutingService._get_local_config_path()
        if not Path(config_path).exists():
            return

        with open(config_path) as f:
            config = json.load(f)

        routes = config.get("routes", {})
        domain = settings.PLATFORM_DOMAIN
        hostnames = [f"{project.slug}.{domain}"]

        if deployment.preview_url:
            hostnames.append(deployment.preview_url.replace("https://", "").replace("http://", ""))

        for hostname in hostnames:
            routes.pop(hostname, None)

        config["routes"] = routes
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    async def add_custom_domain(domain: str, container_name: str, port: int = 80) -> None:
        config_path = RoutingService._get_local_config_path()
        config_dir = Path(config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        routes = {}
        if Path(config_path).exists():
            with open(config_path) as f:
                routes = json.load(f).get("routes", {})

        routes[domain] = {
            "service": container_name,
            "port": port,
        }

        with open(config_path, "w") as f:
            json.dump({"routes": routes}, f, indent=2)
