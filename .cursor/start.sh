#!/usr/bin/env bash
set -euo pipefail

cd /workspace

start_postgres() {
  if PGPASSWORD=deploy psql -h localhost -U deploy -d deploystack -c 'SELECT 1' >/dev/null 2>&1; then
    return 0
  fi

  sudo service postgresql start

  sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='deploy'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE USER deploy WITH PASSWORD 'deploy' SUPERUSER;"
  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='deploystack'" | grep -q 1 \
    || sudo -u postgres psql -c "CREATE DATABASE deploystack OWNER deploy;"

  for _ in $(seq 1 30); do
    if PGPASSWORD=deploy psql -h localhost -U deploy -d deploystack -c 'SELECT 1' >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "PostgreSQL did not become ready in time" >&2
  exit 1
}

start_redis() {
  if redis-cli -h localhost ping 2>/dev/null | grep -q PONG; then
    return 0
  fi

  sudo service redis-server start

  for _ in $(seq 1 15); do
    if redis-cli -h localhost ping 2>/dev/null | grep -q PONG; then
      return 0
    fi
    sleep 1
  done

  echo "Redis did not become ready in time" >&2
  exit 1
}

start_docker() {
  if docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1; then
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
    return 0
  fi

  if ! pgrep -x dockerd >/dev/null 2>&1; then
    sudo dockerd >/tmp/dockerd.log 2>&1 &
    for _ in $(seq 1 60); do
      if docker info >/dev/null 2>&1 || sudo docker info >/dev/null 2>&1; then
        sudo chmod 666 /var/run/docker.sock 2>/dev/null || true
        return 0
      fi
      sleep 1
    done
  fi

  echo "Docker daemon is not running (worker builds may be unavailable until dockerd starts)." >&2
}

start_postgres
start_redis
start_docker || true

# shellcheck disable=SC1091
source .venv/bin/activate
cd backend
alembic upgrade head
cd /workspace

echo "Infrastructure ready (postgres, redis, migrations applied)."
