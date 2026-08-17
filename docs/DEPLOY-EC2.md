# EC2 par Deploy — step by step

Main **directly tumhare AWS par deploy nahi kar sakta** (EC2 password/SSH mere paas nahi).  
Neeche **2 tareeke** — ek command ya GitHub auto-deploy.

---

## Option A: EC2 par ek command (fastest)

### 1. EC2 launch (us-east-1, RDS ke VPC mein)

- Ubuntu 22.04, t3.medium, 50GB  
- Security group: 22, 80, 443  
- RDS SG: 5432 ← EC2 security group  

### 2. SSH + bootstrap

```bash
ssh -i your-key.pem ubuntu@EC2_PUBLIC_IP

sudo bash -c 'curl -fsSL https://raw.githubusercontent.com/SHPDH09/free-deployment/cursor/deployment-platform-9c59/scripts/ec2-bootstrap.sh | bash'
```

### 3. `.env` edit (password + GitHub)

```bash
nano /opt/deploystack/.env
```

Replace `YOUR_RDS_PASSWORD`, add GitHub Client ID/Secret.

### 4. Deploy start

```bash
cd /opt/deploystack
./scripts/setup-production.sh
```

Dashboard: `http://EC2_IP:3000`

---

## Option B: GitHub se auto-deploy (main push karunga, EC2 update)

GitHub repo → **Settings** → **Secrets and variables** → **Actions** → add:

| Secret | Example |
|--------|---------|
| `EC2_HOST` | `54.xxx.xxx.xxx` |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | PEM private key (full content) |

EC2 par pehle ek baar manually `.env` set karo (`/opt/deploystack/.env`).

Phir har `git push` par GitHub Actions EC2 par deploy karega.

---

## Checklist

- [ ] EC2 running (us-east-1)
- [ ] RDS connected (tumne ✅ kiya)
- [ ] `/opt/deploystack/.env` with password
- [ ] `curl http://localhost:8000/health` → healthy
- [ ] Port 3000 open in EC2 security group
- [ ] GitHub OAuth callback URL set

---

## Mujhe deploy karne ke liye chahiye (GitHub Secrets only)

1. `EC2_HOST` — public IP  
2. `EC2_USER` — usually `ubuntu`  
3. `EC2_SSH_KEY` — private key (.pem)  

**Mat bhejo:** RDS password (EC2 par `.env` mein rakho).

Secrets add karne ke baad bolo — main workflow trigger / code push kar dunga.
