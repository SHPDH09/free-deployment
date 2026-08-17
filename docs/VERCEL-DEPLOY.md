# Vercel par Deploy (Python nahi — sirf Next.js + TypeScript)

DeployStack ab **Vercel-ready** stack use karta hai:

| Layer | Tech |
|-------|------|
| Frontend + API | **Next.js 14** (TypeScript) |
| Database | **PostgreSQL** (Neon / Vercel Postgres) |
| ORM | **Prisma** |
| Auth | **JWT + GitHub OAuth** |
| Hosting | **Vercel** |

Python / FastAPI / Docker worker — **Vercel deploy ke liye zaroori nahi**.

---

## 5 minute Vercel deploy

### 1. Database (free) — Neon

1. [neon.tech](https://neon.tech) → sign up  
2. New project → copy **connection string**  
3. Example: `postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require`

### 2. Vercel

1. [vercel.com/new](https://vercel.com/new)  
2. Import **GitHub repo** `free-deployment`  
3. **Root Directory:** `frontend`  
4. Framework: Next.js (auto)

### 3. Environment Variables (Vercel dashboard)

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | Neon connection string |
| `SECRET_KEY` | random 32+ chars |
| `GITHUB_CLIENT_ID` | GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth |
| `GITHUB_CALLBACK_URL` | `https://YOUR-APP.vercel.app/auth/callback` |
| `ADMIN_EMAIL` | your email |

`NEXT_PUBLIC_API_URL` — **mat set karo** (same-origin `/api` use hoga).

### 4. GitHub OAuth App

- Callback: `https://YOUR-APP.vercel.app/auth/callback`

### 5. Deploy

Vercel **Deploy** → `prisma db push` tables banayega → site live.

---

## Flow (Vercel jaisa)

```text
GitHub repo → Vercel import → Dashboard live
Dashboard → Connect GitHub → New Project → Deploy
```

---

## Kya Vercel par chalta / nahi

| Feature | Vercel |
|---------|--------|
| Dashboard | ✅ |
| GitHub login | ✅ |
| Projects list/create | ✅ |
| PostgreSQL (Neon) | ✅ |
| Docker build workers | ❌ (Vercel limitation) |
| Custom Traefik domains | ❌ |

Docker builds chahiye to **Railway worker** alag se — ya customer sites direct **Vercel** par deploy karo.

---

## Local test

```bash
cd frontend
cp .env.example .env.local
# DATABASE_URL=neon or local postgres
npm install
npx prisma db push
npm run dev
```

Open http://localhost:3000
