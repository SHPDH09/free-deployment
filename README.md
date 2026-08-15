# DeployStack

A production-ready, self-hosted deployment platform similar to Vercel/Netlify. Connect GitHub repositories, build in isolated Docker containers, and deploy to your own infrastructure with automatic URLs, custom domains, and HTTPS.

## Architecture

```
GitHub → Webhook → API Server → Redis Queue → Build Workers
                                              ↓
                                    Docker Build (isolated)
                                              ↓
                                    Artifacts Storage
                                              ↓
                                    Traefik Reverse Proxy
                                              ↓
                                    Live Websites
```

### Components

| Service | Technology | Purpose |
|---------|-----------|---------|
| **API** | FastAPI + SQLAlchemy | REST API, auth, GitHub integration, queue management |
| **Worker** | Python + Docker SDK | Isolated builds, container deployment, health checks |
| **Web** | Next.js 14 + Tailwind | SaaS-style dashboard |
| **Database** | PostgreSQL 16 | Users, projects, deployments, domains, audit logs |
| **Queue** | Redis 7 | Build job queue with worker coordination |
| **Proxy** | Traefik v3 | Host-based routing, SSL termination |
| **Storage** | Local / AWS S3 | Build artifacts and deployment files |

## Features

- **GitHub OAuth** — Connect accounts, list repos/branches, webhook auto-deploy
- **Project Wizard** — Framework detection (Next.js, React, Vite, Vue, Angular, Node.js, FastAPI, Flask, Python, Static)
- **Docker Isolation** — Every build runs in a network-disabled, resource-limited container
- **Build Queue** — Pending → Building → Deploying → Success/Failed with retry support
- **Deployment URLs** — `project-name.platform.com` and preview URLs
- **Custom Domains** — DNS verification, Cloudflare integration, automatic SSL
- **Environment Variables** — Encrypted at rest, per-environment (production/preview)
- **Real-time Logs** — WebSocket streaming of build/deployment logs
- **Rollback** — Activate previous artifacts without rebuilding
- **Health Checks** — Automatic HTTP checks after deployment
- **Admin Panel** — Users, projects, workers, audit logs, suspend actions
- **RBAC** — User and admin roles with audit logging

## Quick Start (Local)

### Prerequisites

- Docker & Docker Compose
- GitHub OAuth App ([create one](https://github.com/settings/applications/new))
  - Homepage URL: `http://localhost:3000`
  - Callback URL: `http://localhost:3000/auth/callback`

### Setup

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_WEBHOOK_SECRET

# Start all services
docker compose up -d --build

# Access
# Dashboard: http://localhost:3000
# API:       http://localhost:8000
# Traefik:   http://localhost:8080 (dashboard)
```

### Local Development (without Docker)

```bash
# Start infrastructure
docker compose up -d postgres redis

# Backend
cd backend
pip install -r requirements.txt
cp ../.env .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Worker
cd worker
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

## AWS Deployment

### Recommended Infrastructure

| Resource | Purpose |
|----------|---------|
| EC2 (t3.large+) | API, worker, Traefik, Docker |
| RDS PostgreSQL | Database |
| S3 | Artifacts and logs (optional) |
| Cloudflare | DNS, SSL, DDoS protection |
| ElastiCache Redis | Queue (or Redis on EC2) |

### EC2 Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone repository
git clone <your-repo> /opt/deploystack
cd /opt/deploystack

# Configure production environment
cp .env.example .env
# Set:
#   PLATFORM_DOMAIN=your-domain.com
#   DATABASE_URL=postgresql+asyncpg://user:pass@rds-endpoint:5432/deploystack
#   REDIS_URL=redis://elasticache-endpoint:6379/0
#   USE_S3_ARTIFACTS=true
#   AWS_S3_BUCKET=your-bucket

# Deploy
docker compose up -d --build
```

### Cloudflare DNS

1. Add your platform domain to Cloudflare
2. Point A record to EC2 IP (proxied)
3. Set `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ZONE_ID` in `.env`
4. Custom domains for projects use CNAME to `cname.your-domain.com`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/github` | Get GitHub OAuth URL |
| `POST` | `/api/auth/github/callback` | Complete OAuth |
| `GET` | `/api/auth/me` | Current user |
| `GET` | `/api/projects` | List projects |
| `POST` | `/api/projects` | Create project |
| `POST` | `/api/projects/:id/deploy` | Trigger deployment |
| `GET` | `/api/projects/:id/deployments` | Deployment history |
| `POST` | `/api/deployments/:id/rollback` | Rollback deployment |
| `GET` | `/api/deployments/:id/logs` | Build logs |
| `POST` | `/api/projects/:id/domains` | Add custom domain |
| `POST` | `/api/webhooks/github` | GitHub webhook handler |

Full API docs available at `/docs` when the API is running.

## Security

- All repository code treated as untrusted
- Builds run in isolated Docker containers (no network, read-only FS, non-root, resource limits)
- Docker socket never exposed to user containers
- Environment variables encrypted with Fernet at rest
- GitHub webhook signature verification
- JWT authentication on all protected endpoints
- RBAC with admin/user roles
- Audit logging for all sensitive actions
- Rate limiting via configurable deployment/project limits

## Database Schema

Tables: `users`, `github_accounts`, `projects`, `project_settings`, `deployments`, `deployment_logs`, `deployment_artifacts`, `domains`, `environment_variables`, `build_jobs`, `workers`, `resource_usage`, `audit_logs`

All public identifiers use UUIDs. Foreign keys, indexes, and soft deletion where appropriate.

## Scaling

The architecture supports horizontal scaling:

- **Multiple workers** — Add worker containers; they auto-register and pull from Redis queue
- **Separate API servers** — Stateless API behind load balancer
- **RDS + ElastiCache** — Centralized state
- **S3 artifacts** — Shared artifact storage across workers
- **ECS/EKS migration** — Worker containers can move to orchestrated environments

## License

MIT
