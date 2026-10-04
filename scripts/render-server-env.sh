#!/usr/bin/env bash
# Prints the server .env for .github/workflows/deploy.yml, built from the
# environment variables the workflow step sets from its GitHub environment.
# Values are single-quoted so docker compose takes them literally (no ${…}
# interpolation of a secret that happens to contain a dollar sign).
#
# Usage: render-server-env.sh <preview|production> > server.env

set -euo pipefail

ENVIRONMENT="${1:?Usage: render-server-env.sh <preview|production>}"

REQUIRED=(
  IMAGE_PREFIX IMAGE_TAG
  ALLOWED_ORIGINS BACKEND_PORT FRONTEND_PORT NEXT_PUBLIC_API_URL DATABASE_URL
  METABASE_SITE_URL METABASE_SECRET_KEY METABASE_DASHBOARD_ID
  DOMAIN API_DOMAIN CERTBOT_EMAIL
  OVH_APPLICATION_KEY OVH_APPLICATION_SECRET OVH_CONSUMER_KEY
)
OPTIONAL=(CERT_EXTRA_DOMAINS)
case "$ENVIRONMENT" in
  production) ;;
  preview)
    REQUIRED+=(POSTGRES_USER POSTGRES_DB POSTGRES_PASSWORD)
    OPTIONAL+=(RUN_SEED)
    ;;
  *)
    echo "Error: unknown environment '$ENVIRONMENT'" >&2
    exit 1
    ;;
esac

missing=()
for name in "${REQUIRED[@]}"; do
  [ -n "${!name:-}" ] || missing+=("$name")
done
if [ "${#missing[@]}" -gt 0 ]; then
  echo "::error::Not set in the GitHub environment '$ENVIRONMENT': ${missing[*]}" >&2
  exit 1
fi

# ${arr[@]+…}: an empty array trips set -u on bash < 4.4 (macOS).
for name in "${REQUIRED[@]}" ${OPTIONAL[@]+"${OPTIONAL[@]}"}; do
  value="${!name:-}"
  [ -n "$value" ] || continue
  case "$value" in
    *"'"* | *$'\n'*)
      echo "::error::$name contains a single quote or a newline, which a .env file can't carry" >&2
      exit 1
      ;;
  esac
  printf "%s='%s'\n" "$name" "$value"
done
