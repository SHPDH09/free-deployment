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

import docker
import httpx
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import decrypt_value, settings

logger = logging.getLogger("builder")

engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

QUEUE_KEY = "deploystack:build_queue"
LOG_CHANNEL_PREFIX = "deploystack:logs:"


class BuildWorker:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.worker_id = settings.WORKER_ID

    def _db_session(self):
        return Session()

    def _publish_log(self, deployment_id: str, message: str, level: str = "info", step: str = None):
        redis_client.publish(
            f"{LOG_CHANNEL_PREFIX}{deployment_id}",
            json.dumps({
                "message": message,
                "level": level,
                "step": step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )

    def _add_log(self, session, deployment_id: str, message: str, level: str = "info", step: str = None):
        session.execute(
            text(
                "INSERT INTO deployment_logs (id, deployment_id, level, message, step, is_user_visible, created_at) "
                "VALUES (:id, :deployment_id, :level, :message, :step, true, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "deployment_id": deployment_id,
                "level": level,
                "message": message,
                "step": step,
                "created_at": datetime.now(timezone.utc),
            },
        )
        session.commit()
        self._publish_log(deployment_id, message, level, step)

    def _update_status(self, session, deployment_id: str, status: str, **kwargs):
        fields = {"status": status, "updated_at": datetime.now(timezone.utc)}
        fields.update(kwargs)
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["deployment_id"] = deployment_id
        session.execute(
            text(f"UPDATE deployments SET {set_clause} WHERE id = :deployment_id"),
            fields,
        )
        session.commit()

    def _get_deployment_context(self, session, deployment_id: str) -> dict | None:
        result = session.execute(
            text("""
                SELECT d.*, p.slug, p.github_repo_full_name, p.root_directory,
                       p.build_command, p.install_command, p.output_directory,
                       p.start_command, p.node_version, p.python_version,
                       p.deployment_type, p.default_branch, p.user_id,
                       ga.access_token_encrypted
                FROM deployments d
                JOIN projects p ON d.project_id = p.id
                LEFT JOIN github_accounts ga ON ga.user_id = p.user_id
                WHERE d.id = :deployment_id
            """),
            {"deployment_id": deployment_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def _get_env_vars(self, session, project_id: str, environment: str = "production") -> dict:
        result = session.execute(
            text(
                "SELECT key, value_encrypted FROM environment_variables "
                "WHERE project_id = :project_id AND environment = :environment"
            ),
            {"project_id": project_id, "environment": environment},
        )
        env = {}
        for row in result:
            try:
                env[row.key] = decrypt_value(row.value_encrypted)
            except Exception:
                pass
        return env

    def _clone_repo(self, repo_url: str, branch: str, target_dir: str, token: str | None, deployment_id: str, session):
        self._add_log(session, deployment_id, "Cloning repository...", step="clone")
        clone_url = repo_url
        if token:
            clone_url = repo_url.replace("https://", f"https://x-access-token:{token}@")

        cmd = ["git", "clone", "--depth=1", "--branch", branch, clone_url, target_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {result.stderr}")

        self._add_log(session, deployment_id, "Repository cloned successfully.", step="clone")

    def _run_build_container(self, build_dir: str, project: dict, deployment_id: str, session) -> str:
        self._add_log(session, deployment_id, "Creating isolated build environment...", step="build")

        output_dir = Path(settings.BUILDS_PATH) / deployment_id / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        is_python = project.get("python_version") or project.get("framework") in ("python", "fastapi", "flask")
        is_node = project.get("node_version") or not is_python

        if is_python and project.get("python_version"):
            base_image = f"python:{project['python_version']}-slim"
        elif is_node:
            node_ver = project.get("node_version") or "20"
            base_image = f"node:{node_ver}-slim"
        else:
            base_image = "node:20-slim"

        install_cmd = project.get("install_command") or ""
        build_cmd = project.get("build_command") or ""
        root_dir = project.get("root_directory") or "."

        script_lines = [
            "set -e",
            f"cd /workspace/{root_dir}",
        ]
        if install_cmd:
            script_lines.append(install_cmd)
        if build_cmd:
            script_lines.append(build_cmd)

        if project.get("deployment_type") == "static" and project.get("output_directory"):
            script_lines.append(f"cp -r {project['output_directory']} /output/")
        elif project.get("deployment_type") == "server":
            script_lines.append("cp -r . /output/")

        script = "\n".join(script_lines)

        container_name = f"build-{deployment_id[:8]}"
        mem_limit = f"{settings.MAX_BUILD_MEMORY_MB}m"
        cpu_quota = int(settings.MAX_BUILD_CPU * 100000)

        try:
            old = self.docker_client.containers.get(container_name)
            old.remove(force=True)
        except docker.errors.NotFound:
            pass

        container = self.docker_client.containers.run(
            image=base_image,
            name=container_name,
            command=["sh", "-c", script],
            volumes={
                build_dir: {"bind": "/workspace", "mode": "ro"},
                str(output_dir): {"bind": "/output", "mode": "rw"},
            },
            mem_limit=mem_limit,
            nano_cpus=cpu_quota,
            network_disabled=True,
            user="nobody",
            read_only=True,
            tmpfs={"/tmp": "size=512m"},
            detach=True,
            remove=False,
        )

        start_time = time.time()
        try:
            result = container.wait(timeout=settings.BUILD_TIMEOUT_SECONDS)
            logs = container.logs().decode("utf-8", errors="replace")
            for line in logs.split("\n")[:200]:
                if line.strip():
                    self._add_log(session, deployment_id, line, step="build")

            if result.get("StatusCode", 1) != 0:
                raise RuntimeError(f"Build failed with exit code {result.get('StatusCode')}")

        except Exception as e:
            try:
                container.kill()
            except Exception:
                pass
            raise RuntimeError(f"Build failed: {e}")
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass

        duration = int((time.time() - start_time) * 1000)
        self._add_log(session, deployment_id, f"Build completed in {duration}ms.", step="build")
        return str(output_dir)

    def _store_artifact(self, output_dir: str, project_id: str, deployment_id: str, session) -> str:
        artifact_path = Path(settings.ARTIFACTS_PATH) / project_id / deployment_id
        if artifact_path.exists():
            shutil.rmtree(artifact_path)
        shutil.copytree(output_dir, artifact_path)

        size = sum(f.stat().st_size for f in artifact_path.rglob("*") if f.is_file())
        max_size = settings.MAX_DEPLOYMENT_SIZE_MB * 1024 * 1024
        if size > max_size:
            shutil.rmtree(artifact_path)
            raise RuntimeError(f"Deployment size ({size} bytes) exceeds limit ({max_size} bytes)")

        session.execute(
            text(
                "INSERT INTO deployment_artifacts (id, deployment_id, project_id, storage_path, size_bytes, is_active, created_at) "
                "VALUES (:id, :deployment_id, :project_id, :storage_path, :size_bytes, false, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "deployment_id": deployment_id,
                "project_id": project_id,
                "storage_path": str(artifact_path),
                "size_bytes": size,
                "created_at": datetime.now(timezone.utc),
            },
        )
        session.commit()
        return str(artifact_path)

    def _deploy_container(self, artifact_path: str, project: dict, deployment_id: str, session) -> tuple[str, str]:
        self._add_log(session, deployment_id, "Deploying application...", step="deploy")

        container_name = f"deploy-{deployment_id[:8]}"
        deployment_type = project.get("deployment_type", "static")
        env_vars = self._get_env_vars(session, project["project_id"])

        try:
            old = self.docker_client.containers.get(container_name)
            old.remove(force=True)
        except docker.errors.NotFound:
            pass

        mem_limit = f"{project.get('max_memory_mb', 512)}m"

        if deployment_type == "static":
            image = "nginx:alpine"
            nginx_conf = f"""
events {{ worker_connections 1024; }}
http {{
    include /etc/nginx/mime.types;
    server {{
        listen 80;
        root /usr/share/nginx/html;
        index index.html;
        location / {{ try_files $uri $uri/ /index.html; }}
    }}
}}
"""
            conf_dir = Path(settings.BUILDS_PATH) / deployment_id / "nginx"
            conf_dir.mkdir(parents=True, exist_ok=True)
            (conf_dir / "nginx.conf").write_text(nginx_conf)

            container = self.docker_client.containers.run(
                image=image,
                name=container_name,
                volumes={
                    artifact_path: {"bind": "/usr/share/nginx/html", "mode": "ro"},
                    str(conf_dir / "nginx.conf"): {"bind": "/etc/nginx/nginx.conf", "mode": "ro"},
                },
                mem_limit=mem_limit,
                network=settings.TRAEFIK_NETWORK,
                detach=True,
                labels={
                    "traefik.enable": "true",
                    f"traefik.http.routers.{container_name}.rule": f"Host(`{project['slug']}.{settings.PLATFORM_DOMAIN}`)",
                    "traefik.http.services." + container_name + ".loadbalancer.server.port": "80",
                },
            )
            port = 80
        else:
            is_python = project.get("python_version") or project.get("framework") in ("python", "fastapi", "flask")
            if is_python:
                image = f"python:{project.get('python_version', '3.12')}-slim"
                start_cmd = project.get("start_command") or "python main.py"
            else:
                image = f"node:{project.get('node_version', '20')}-slim"
                start_cmd = project.get("start_command") or "npm start"

            container = self.docker_client.containers.run(
                image=image,
                name=container_name,
                command=["sh", "-c", f"cd /app && {start_cmd}"],
                volumes={artifact_path: {"bind": "/app", "mode": "ro"}},
                environment=env_vars,
                mem_limit=mem_limit,
                network=settings.TRAEFIK_NETWORK,
                detach=True,
                working_dir="/app",
                labels={
                    "traefik.enable": "true",
                    f"traefik.http.routers.{container_name}.rule": f"Host(`{project['slug']}.{settings.PLATFORM_DOMAIN}`)",
                    "traefik.http.services." + container_name + ".loadbalancer.server.port": "3000",
                },
            )
            port = 3000

        self._update_routing(project, deployment_id, container_name, port)
        self._add_log(session, deployment_id, f"Container {container_name} started.", step="deploy")
        return container.id, container_name

    def _update_routing(self, project: dict, deployment_id: str, container_name: str, port: int):
        config_path = os.environ.get("TRAEFIK_DYNAMIC_PATH", "/traefik/dynamic/deployments.json")
        config_dir = Path(config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        routes = {}
        if Path(config_path).exists():
            with open(config_path) as f:
                routes = json.load(f).get("routes", {})

        hostnames = [f"{project['slug']}.{settings.PLATFORM_DOMAIN}"]
        short_id = deployment_id.split("-")[0]
        hostnames.append(f"{short_id}.{project['slug']}.{settings.PLATFORM_DOMAIN}")

        for hostname in hostnames:
            routes[hostname] = {
                "service": container_name,
                "port": port,
                "deployment_id": deployment_id,
                "project_id": project["project_id"],
            }

        with open(config_path, "w") as f:
            json.dump({"routes": routes}, f, indent=2)

    def _health_check(self, project: dict, deployment_id: str, session) -> bool:
        self._add_log(session, deployment_id, "Running health check...", step="health")

        health_path = "/"
        try:
            result = session.execute(
                text("SELECT health_check_path FROM project_settings WHERE project_id = :project_id"),
                {"project_id": project["project_id"]},
            )
            row = result.first()
            if row:
                health_path = row[0] or "/"
        except Exception:
            pass

        url = f"http://deploy-{deployment_id[:8]}:{3000 if project.get('deployment_type') == 'server' else 80}{health_path}"

        for attempt in range(10):
            try:
                with httpx.Client(timeout=5.0) as client:
                    response = client.get(
                        f"http://{project['slug']}.{settings.PLATFORM_DOMAIN}{health_path}",
                        follow_redirects=True,
                    )
                    if response.status_code < 500:
                        self._add_log(
                            session, deployment_id,
                            f"Health check passed (HTTP {response.status_code}).",
                            step="health",
                        )
                        return True
            except Exception:
                pass
            time.sleep(2)

        self._add_log(session, deployment_id, "Health check failed.", level="error", step="health")
        return False

    def _cleanup_build(self, deployment_id: str):
        build_dir = Path(settings.BUILDS_PATH) / deployment_id
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)

    def process_job(self, job_data: dict):
        deployment_id = job_data["deployment_id"]
        job_id = job_data["job_id"]
        session = self._db_session()

        try:
            self._register_worker(session)
            self._update_status(
                session, deployment_id,
                "building",
                build_status="building",
                started_at=datetime.now(timezone.utc),
                worker_id=self.worker_id,
            )
            session.execute(
                text("UPDATE build_jobs SET status = 'building', started_at = :now, worker_id = :worker_id WHERE id = :id"),
                {"now": datetime.now(timezone.utc), "worker_id": self.worker_id, "id": job_id},
            )
            session.commit()

            ctx = self._get_deployment_context(session, deployment_id)
            if not ctx:
                raise RuntimeError("Deployment context not found")

            token = None
            if ctx.get("access_token_encrypted"):
                try:
                    token = decrypt_value(ctx["access_token_encrypted"])
                except Exception:
                    pass

            build_dir = Path(settings.BUILDS_PATH) / deployment_id / "source"
            build_dir.mkdir(parents=True, exist_ok=True)

            repo_url = f"https://github.com/{ctx['github_repo_full_name']}.git"
            branch = ctx.get("branch") or ctx.get("default_branch") or "main"

            build_start = time.time()
            self._clone_repo(repo_url, branch, str(build_dir), token, deployment_id, session)
            output_dir = self._run_build_container(str(build_dir), ctx, deployment_id, session)
            build_duration = int((time.time() - build_start) * 1000)

            artifact_path = self._store_artifact(output_dir, ctx["project_id"], deployment_id, session)

            self._update_status(
                session, deployment_id,
                "deploying",
                build_status="success",
                deployment_status="deploying",
                build_duration_ms=build_duration,
            )

            deploy_start = time.time()
            container_id, container_name = self._deploy_container(artifact_path, ctx, deployment_id, session)
            deploy_duration = int((time.time() - deploy_start) * 1000)

            healthy = self._health_check(ctx, deployment_id, session)

            if healthy:
                production_url = f"https://{ctx['slug']}.{settings.PLATFORM_DOMAIN}"
                self._update_status(
                    session, deployment_id,
                    "success",
                    deployment_status="success",
                    deploy_duration_ms=deploy_duration,
                    total_duration_ms=build_duration + deploy_duration,
                    finished_at=datetime.now(timezone.utc),
                    deployment_url=production_url,
                    container_id=container_id,
                    container_name=container_name,
                    health_check_status="healthy",
                )
                session.execute(
                    text("UPDATE projects SET active_deployment_id = :deployment_id WHERE id = :project_id"),
                    {"deployment_id": deployment_id, "project_id": ctx["project_id"]},
                )
                session.execute(
                    text("UPDATE deployment_artifacts SET is_active = true WHERE deployment_id = :deployment_id"),
                    {"deployment_id": deployment_id},
                )
                session.commit()
                self._add_log(session, deployment_id, "Deployment successful.", step="complete")
            else:
                self._update_status(
                    session, deployment_id,
                    "failed",
                    deployment_status="failed",
                    error_message="Health check failed after deployment.",
                    finished_at=datetime.now(timezone.utc),
                )

            session.execute(
                text("UPDATE build_jobs SET status = 'completed', finished_at = :now WHERE id = :id"),
                {"now": datetime.now(timezone.utc), "id": job_id},
            )
            session.commit()

        except Exception as e:
            logger.exception("Job failed: %s", e)
            error_msg = str(e)
            user_msg = error_msg
            if "npm" in error_msg.lower() or "pip" in error_msg.lower():
                user_msg = f"Deployment failed during dependency installation.\n\nReason:\n{error_msg}"

            self._add_log(session, deployment_id, user_msg, level="error", step="error")
            self._update_status(
                session, deployment_id,
                "failed",
                build_status="failed",
                deployment_status="failed",
                error_message=user_msg,
                error_details=error_msg,
                finished_at=datetime.now(timezone.utc),
            )
            session.execute(
                text("UPDATE build_jobs SET status = 'failed', error_message = :error, finished_at = :now WHERE id = :id"),
                {"error": error_msg, "now": datetime.now(timezone.utc), "id": job_id},
            )
            session.commit()
        finally:
            self._cleanup_build(deployment_id)
            session.close()

    def _register_worker(self, session):
        session.execute(
            text("""
                INSERT INTO workers (id, worker_id, hostname, status, last_heartbeat, created_at, updated_at)
                VALUES (:id, :worker_id, :hostname, 'busy', :now, :now, :now)
                ON CONFLICT (worker_id) DO UPDATE SET status = 'busy', last_heartbeat = :now, updated_at = :now
            """),
            {
                "id": str(uuid.uuid4()),
                "worker_id": self.worker_id,
                "hostname": socket.gethostname(),
                "now": datetime.now(timezone.utc),
            },
        )
        session.commit()

    def run(self):
        logger.info("Worker %s starting...", self.worker_id)
        while True:
            try:
                result = redis_client.brpop(QUEUE_KEY, timeout=5)
                if result:
                    job_data = json.loads(result[1])
                    logger.info("Processing job: %s", job_data)
                    self.process_job(job_data)
                else:
                    session = self._db_session()
                    session.execute(
                        text("UPDATE workers SET status = 'idle', last_heartbeat = :now WHERE worker_id = :worker_id"),
                        {"now": datetime.now(timezone.utc), "worker_id": self.worker_id},
                    )
                    session.commit()
                    session.close()
            except Exception as e:
                logger.exception("Worker error: %s", e)
                time.sleep(5)


if __name__ == "__main__":
    worker = BuildWorker()
    worker.run()
