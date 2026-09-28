#!/usr/bin/env bash
set -euo pipefail
apt-get update && apt-get install -y docker.io docker-compose-plugin
mkdir -p memory data
cp -n .env.example .env || true
docker compose up -d --build
docker compose ps
