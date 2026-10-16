#!/usr/bin/env bash
# Server side of .github/workflows/deploy.yml. Runs from the deploy directory
# (~/cinestats5050 or ~/cinestats5050-preview) once the workflow has copied
# docker-compose.yml, nginx/ and the new settings (.env.new) next to it.
#
# The new release only replaces .env once every service is up and healthy;
# otherwise the release still described by .env is put back, and the deploy
# fails anyway.
#
# Usage: remote-deploy.sh <registry_user>    (registry token on stdin)

set -euo pipefail

cd "$(dirname "$0")"
REGISTRY_USER="${1:?Usage: remote-deploy.sh <registry_user> (registry token on stdin)}"
[ -f .env.new ] || { echo "Error: .env.new missing" >&2; exit 1; }

IMAGE_PREFIX="$(sed -n "s/^IMAGE_PREFIX='\(.*\)'$/\1/p" .env.new)"
REGISTRY="${IMAGE_PREFIX%%/*}"
[ -n "$REGISTRY" ] || { echo "Error: IMAGE_PREFIX missing from .env.new" >&2; exit 1; }

# certbot's bind mounts must exist before compose creates them as root.
mkdir -p certbot/conf certbot/www certbot/logs

docker login "$REGISTRY" -u "$REGISTRY_USER" --password-stdin
# Don't leave the registry credentials lying in ~/.docker/config.json.
trap 'docker logout "$REGISTRY" >/dev/null' EXIT
docker compose --env-file .env.new pull --quiet

# nginx resolves the backend/frontend hostnames once, at startup: once those
# containers are recreated it would keep proxying to their old IPs.
reload_nginx() { docker compose "$@" exec -T nginx nginx -s reload; }

# No `down`: only the containers whose image or config changed are recreated,
# and --wait fails if a service doesn't get running/healthy.
if ! docker compose --env-file .env.new up -d --remove-orphans --wait --wait-timeout 300; then
  if [ -f .env ]; then
    echo "::error::The new release didn't come up healthy: putting the previous one back."
    docker compose up -d --remove-orphans --wait --wait-timeout 300 \
      && reload_nginx \
      || echo "::error::The previous release didn't come back up either: check the server."
  fi
  exit 1
fi
reload_nginx --env-file .env.new
mv .env.new .env

# One image tag per deploy piles up: keep a week's worth for quick rollbacks.
docker image prune -af --filter "until=168h" >/dev/null

docker compose ps
