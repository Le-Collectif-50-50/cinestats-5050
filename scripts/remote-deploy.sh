#!/usr/bin/env bash
# Shared tail of deploy.yml and deploy-preview.yml's SSH step. The .env file
# is expected to already be written (its contents differ per environment).
#
# Usage: remote-deploy.sh <compose-file> [--down]
#   GITHUB_REPOSITORY_OWNER and GITHUB_TOKEN must be exported by the caller.

set -euo pipefail

COMPOSE_FILE="${1:?Usage: remote-deploy.sh <compose-file> [--down]}"
DO_DOWN="${2:-}"

OWNER_LOWER=$(echo "$GITHUB_REPOSITORY_OWNER" | tr '[:upper:]' '[:lower:]')
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$OWNER_LOWER" --password-stdin

mv "$COMPOSE_FILE" docker-compose.yml
docker compose pull

if [ "$DO_DOWN" = "--down" ]; then
  docker compose down
fi

docker compose up -d --remove-orphans
