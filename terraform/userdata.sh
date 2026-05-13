#!/bin/bash
# Bootstrap script — runs once on first EC2 boot.
# Installs Docker and prepares directories.
# The actual app clone + stack start happens via the GitHub Actions deploy workflow.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y git curl make software-properties-common

# The Ubuntu 22.04 AMI ships with ufw enabled and blocking all inbound.
# The EC2 security group handles firewall duties — disable ufw entirely.
ufw disable || true
ufw --force reset || true

# Port 22 is blocked by many ISPs. Make sshd also listen on 443
# so SSH works from any network.
sed -i 's/^#\?Port 22/Port 22\nPort 443/' /etc/ssh/sshd_config
systemctl restart ssh

# Python 3.12 (needed for `make train` on the EC2 — ML model training)
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update -y
apt-get install -y python3.12 python3.12-venv python3.12-dev

# Docker Engine
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu

# Docker Compose plugin (latest stable)
COMPOSE_TAG=$(curl -fsSL https://api.github.com/repos/docker/compose/releases/latest \
  | grep '"tag_name"' | head -1 | cut -d'"' -f4)
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_TAG}/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# App directories (the deploy workflow clones the repo into /opt/soko/app)
mkdir -p /opt/soko/app
mkdir -p /opt/soko/frontend/dist
chown -R ubuntu:ubuntu /opt/soko

echo "Bootstrap complete. Trigger the GitHub Actions deploy workflow to start Soko."
