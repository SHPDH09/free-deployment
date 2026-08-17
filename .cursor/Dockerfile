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
    && echo 'ubuntu ALL=(ALL) NOPASSWD: /usr/bin/dockerd, /usr/bin/docker, /usr/libexec/docker/cli-plugins/docker-compose' > /etc/sudoers.d/ubuntu-docker \
    && chmod 440 /etc/sudoers.d/ubuntu-docker

USER ubuntu
