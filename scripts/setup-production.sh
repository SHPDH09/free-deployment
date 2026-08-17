#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  if [[ -f .env.rds.example ]]; then
    cp .env.rds.example .env
    echo "Created .env from .env.rds.example"
    echo "Edit .env now: set YOUR_RDS_PASSWORD and domain/GitHub values"
    echo "  nano .env"
    exit 1
  fi
  echo "No .env file. Copy .env.rds.example to .env first."
  exit 1
fi

if grep -q "YOUR_RDS_PASSWORD" .env; then
  echo "ERROR: Replace YOUR_RDS_PASSWORD in .env before running setup."
  exit 1
fi

echo "==> Starting services (Aurora RDS, no local postgres)..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build redis api worker web traefik

echo "==> Waiting for API container..."
sleep 8

echo "==> Running database migrations..."
docker compose exec -T api alembic upgrade head

echo "==> Health check..."
curl -sf http://localhost:8000/health && echo ""

echo ""
echo "Done. Open dashboard on port 3000 or your domain."
echo "API docs: http://localhost:8000/docs"
