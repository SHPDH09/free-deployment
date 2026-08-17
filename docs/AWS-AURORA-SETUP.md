# AWS Aurora Setup — DeployStack

Your cluster configuration:

| Setting | Value |
|---------|--------|
| Writer endpoint | `database-1.cluster-covwo0uikrnc.us-east-1.rds.amazonaws.com` |
| Reader endpoint | `database-1.cluster-ro-covwo0uikrnc.us-east-1.rds.amazonaws.com` (do not use for app) |
| Port | `5432` |
| Master username | `postgres` |
| Database name | `postgres` |
| Region | `us-east-1` |

## 1. Create `.env` on EC2

```bash
cd /opt/deploystack
git pull
cp .env.rds.example .env
nano .env
```

Replace only `YOUR_RDS_PASSWORD` with your RDS master password.

Final database lines:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@database-1.cluster-covwo0uikrnc.us-east-1.rds.amazonaws.com:5432/postgres
DATABASE_URL_SYNC=postgresql://postgres:YOUR_PASSWORD@database-1.cluster-covwo0uikrnc.us-east-1.rds.amazonaws.com:5432/postgres
```

## 2. Security group

RDS inbound rule:

- Type: PostgreSQL
- Port: 5432
- Source: EC2 security group (recommended) or EC2 private IP

## 3. One-command setup

```bash
chmod +x scripts/setup-production.sh scripts/test-db-connection.py
python3 scripts/test-db-connection.py   # test before docker
./scripts/setup-production.sh           # start + migrate
```

## 4. Manual steps

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build redis api worker web traefik
docker compose exec api alembic upgrade head
curl http://localhost:8000/health
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Timeout | Security group / VPC |
| Password auth failed | Reset password in RDS Modify |
| SSL required | Add `?sslmode=require` to URLs |
| Read-only errors | You used `-ro-` endpoint by mistake |
