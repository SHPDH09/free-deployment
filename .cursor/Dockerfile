FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        build-essential \
        python3 \
        python3-pip \
        python3-venv \
        fuse-overlayfs \
        iptables \
        uidmap \
        sudo \
        postgresql \
        postgresql-contrib \
        redis-server \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://get.docker.com | sh \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Docker-in-Cloud-Agent: userspace storage driver and legacy iptables
RUN mkdir -p /etc/docker \
    && printf '{\n  "storage-driver": "fuse-overlayfs"\n}\n' > /etc/docker/daemon.json \
    && update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true \
    && update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true \
    && groupadd -f docker \
    && usermod -aG docker ubuntu \
    && echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ubuntu \
    && chmod 440 /etc/sudoers.d/ubuntu

# Local PostgreSQL for development
RUN PG_CONF=$(ls /etc/postgresql/*/main/postgresql.conf | head -1) \
    && PG_HBA=$(ls /etc/postgresql/*/main/pg_hba.conf | head -1) \
    && sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" "$PG_CONF" \
    && echo "host all all 127.0.0.1/32 md5" >> "$PG_HBA" \
    && echo "host all all ::1/128 md5" >> "$PG_HBA" \
    && service postgresql start \
    && su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='deploy'\" | grep -q 1 || psql -c \"CREATE USER deploy WITH PASSWORD 'deploy' SUPERUSER;\"" \
    && su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='deploystack'\" | grep -q 1 || psql -c \"CREATE DATABASE deploystack OWNER deploy;\"" \
    && service postgresql stop

USER ubuntu
