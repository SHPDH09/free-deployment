#!/usr/bin/env bash
set -euo pipefail

cd /workspace

docker_cmd() {
  if docker "$@" 2>/dev/null; then
    return 0
  fi
  sudo docker "$@"
}

docker_info_ok() {
  docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1
}

start_docker() {
  if docker_info_ok; then
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
    return 0
  fi

  if ! pgrep -x dockerd >/dev/null 2>&1; then
    sudo dockerd >/tmp/dockerd.log 2>&1 &
    for _ in $(seq 1 60); do
      if docker_info_ok; then
        break
      fi
      sleep 1
    done
  fi

  if ! docker_info_ok; then
    echo "Docker daemon failed to start. See /tmp/dockerd.log" >&2
    exit 1
  fi

  sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
}

wait_for_postgres() {
  for _ in $(seq 1 60); do
    if docker_cmd compose --profile local-db exec -T postgres pg_isready -U deploy -d deploystack >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "PostgreSQL did not become ready in time" >&2
  exit 1
}

wait_for_redis() {
  for _ in $(seq 1 30); do
    if docker_cmd compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
      return 0
    fi
    sleep 1
  done
  echo "Redis did not become ready in time" >&2
  exit 1
}

start_docker

docker_cmd compose --profile local-db up -d postgres redis

wait_for_postgres
wait_for_redis

# shellcheck disable=SC1091
source .venv/bin/activate
cd backend
alembic upgrade head
cd /workspace

echo "Infrastructure ready (postgres, redis, migrations applied)."
