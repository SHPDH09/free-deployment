# Vercel Deploy — DeployStack (100% Vercel)

Poora platform **sirf Vercel + Neon** par chalta hai. Python / AWS / Docker **nahi chahiye**.

---

## Step 1: Neon database (2 min)

1. https://neon.tech → Sign up (free)
2. Create project → **Connection string** copy
3. Example:
   ```text
   postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```

---

## Step 2: Vercel import (2 min)

1. https://vercel.com/new
2. Import GitHub repo: **SHPDH09/free-deployment**
3. Branch: `cursor/deployment-platform-9c59`
4. **Root Directory:** `frontend` ← zaroori
5. Framework: Next.js (auto detect)

---

## Step 3: Environment Variables

Vercel project → Settings → Environment Variables:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | Neon connection string |
| `SECRET_KEY` | random 32+ characters |
| `GITHUB_CLIENT_ID` | from GitHub OAuth App |
| `GITHUB_CLIENT_SECRET` | from GitHub OAuth App |
| `GITHUB_CALLBACK_URL` | `https://YOUR-PROJECT.vercel.app/auth/callback` |
| `ADMIN_EMAIL` | your GitHub email (admin access) |

**Do NOT set** `NEXT_PUBLIC_API_URL` — app uses `/api` on same domain.

---

## Step 4: GitHub OAuth App

https://github.com/settings/applications/new

| Field | Value |
|-------|--------|
| Homepage URL | `https://YOUR-PROJECT.vercel.app` |
| Callback URL | `https://YOUR-PROJECT.vercel.app/auth/callback` |

Copy Client ID + Secret → Vercel env vars.

---

## Step 5: Deploy

Click **Deploy** → wait 2–3 min → open URL.

Test: `https://YOUR-PROJECT.vercel.app/api/health`

---

## Use karo

1. Open your Vercel URL
2. **Continue with GitHub**
3. **New Project** → repo select → **Create & Deploy**
4. Dashboard, deployments, logs — sab kaam karega

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails on prisma | `DATABASE_URL` set in Vercel env |
| GitHub login fail | Callback URL exact match |
| 401 on dashboard | Login again |
| Admin panel | Set `ADMIN_EMAIL` to your GitHub email |

---

## Tech stack on Vercel

- Next.js 14 + TypeScript
- Prisma + PostgreSQL (Neon)
- API routes (no Python)
- JWT + GitHub OAuth
