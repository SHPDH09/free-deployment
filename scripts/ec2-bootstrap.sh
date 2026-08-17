#!/usr/bin/env bash
# Run ONCE on a fresh Ubuntu 22.04 EC2 (us-east-1, same VPC as Aurora)
# Usage: curl -fsSL ... | bash   OR   bash scripts/ec2-bootstrap.sh
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "==> Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker "${SUDO_USER:-$USER}" || true
fi

APP_DIR="${APP_DIR:-/opt/deploystack}"
REPO_URL="${REPO_URL:-https://github.com/SHPDH09/free-deployment.git}"
BRANCH="${BRANCH:-cursor/deployment-platform-9c59}"

echo "==> Cloning DeployStack to ${APP_DIR}..."
if [[ ! -d "$APP_DIR/.git" ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
else
  cd "$APP_DIR"
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
fi

cd "$APP_DIR"

if [[ ! -f .env ]]; then
  cp .env.rds.example .env
  echo ""
  echo "IMPORTANT: Edit ${APP_DIR}/.env — set RDS password, GitHub OAuth, domain"
  echo "  nano ${APP_DIR}/.env"
  echo ""
  echo "Then run: cd ${APP_DIR} && ./scripts/setup-production.sh"
  exit 0
fi

if grep -q "YOUR_RDS_PASSWORD" .env; then
  echo "ERROR: Set YOUR_RDS_PASSWORD in ${APP_DIR}/.env first"
  exit 1
fi

chmod +x scripts/*.sh 2>/dev/null || true
./scripts/setup-production.sh

echo "==> DeployStack is running."
echo "    Dashboard: http://$(curl -sf http://checkip.amazonaws.com || echo 'YOUR-EC2-IP'):3000"
echo "    API health: curl http://localhost:8000/health"
