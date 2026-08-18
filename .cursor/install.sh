#!/usr/bin/env bash
set -euo pipefail

cd /workspace

if [[ ! -f .env ]]; then
  cp .env.example .env
  sed -i 's/^SECRET_KEY=.*/SECRET_KEY=dev-secret-key-for-local-development-only/' .env
  sed -i 's/^ENCRYPTION_KEY=.*/ENCRYPTION_KEY=dev-encryption-key-32-bytes-long!!/' .env
  sed -i 's|DATABASE_URL=postgresql+asyncpg://deploy:deploy@postgres:5432/deploystack|DATABASE_URL=postgresql+asyncpg://deploy:deploy@localhost:5432/deploystack|' .env
  sed -i 's|DATABASE_URL_SYNC=postgresql://deploy:deploy@postgres:5432/deploystack|DATABASE_URL_SYNC=postgresql://deploy:deploy@localhost:5432/deploystack|' .env
  sed -i 's|REDIS_URL=redis://redis:6379/0|REDIS_URL=redis://localhost:6379/0|' .env
fi

ln -sf /workspace/.env backend/.env 2>/dev/null || cp /workspace/.env backend/.env
ln -sf /workspace/.env worker/.env 2>/dev/null || cp /workspace/.env worker/.env

rm -rf /workspace/.venv
python3 -m venv /workspace/.venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt pytest pytest-asyncio httpx
pip install -r worker/requirements.txt

cd frontend
npm ci
cd ..

mkdir -p /workspace/.data/artifacts /workspace/.data/deployments /workspace/.data/logs

if grep -q '^ARTIFACTS_PATH=' .env; then
  sed -i 's|^ARTIFACTS_PATH=.*|ARTIFACTS_PATH=/workspace/.data/artifacts|' .env
  sed -i 's|^DEPLOYMENTS_PATH=.*|DEPLOYMENTS_PATH=/workspace/.data/deployments|' .env
  sed -i 's|^LOGS_PATH=.*|LOGS_PATH=/workspace/.data/logs|' .env
fi
