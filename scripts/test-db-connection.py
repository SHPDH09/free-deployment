#!/usr/bin/env python3
"""Test Aurora/RDS connection using DATABASE_URL_SYNC from environment or .env file."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

url = os.environ.get("DATABASE_URL_SYNC")
if not url:
    print("ERROR: DATABASE_URL_SYNC not set. Copy .env.rds.example to .env and set password.")
    sys.exit(1)

if "YOUR_RDS_PASSWORD" in url:
    print("ERROR: Replace YOUR_RDS_PASSWORD in .env with your real RDS master password.")
    sys.exit(1)

try:
    from sqlalchemy import create_engine, text

    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        db = conn.execute(text("SELECT current_database()")).scalar()
        user = conn.execute(text("SELECT current_user")).scalar()
        print("OK — Connected to Aurora PostgreSQL")
        print(f"  Database: {db}")
        print(f"  User:     {user}")
        print(f"  Server:   {version[:60]}...")
    sys.exit(0)
except Exception as e:
    print(f"FAILED: {e}")
    print("\nChecks:")
    print("  1. RDS security group allows port 5432 from EC2 security group")
    print("  2. Password correct (URL-encode @ # % in password)")
    print("  3. Using WRITER endpoint (not cluster-ro-)")
    print("  4. Try sslmode=require in DATABASE_URL_SYNC")
    sys.exit(1)
