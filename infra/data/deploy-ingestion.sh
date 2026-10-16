#!/usr/bin/env bash
# Copie la stack ingestion (airbyte/, dbt/, prefect/, scraping/) sur le VPS data,
# épinglée sur un commit de la branche analytics, avec la surcharge compose du VPS.
# Ne démarre aucun service : voir docs/runbooks/stack-data.md pour la suite.
#
# Usage : infra/data/deploy-ingestion.sh [ref-git]   (défaut : origin/analytics/dbt_airbyte_setup)
# Variable : DATA_HOST = alias SSH du VPS data (défaut : cinestats-data)
# Rejouable : le .env du serveur n'est jamais écrasé.

set -euo pipefail

HOST="${DATA_HOST:-cinestats-data}"
REF="${1:-origin/analytics/dbt_airbyte_setup}"
REMOTE_DIR=cinestats-data

cd "$(git rev-parse --show-toplevel)"
SHA="$(git rev-parse --verify --quiet "$REF^{commit}")" || { echo "Référence introuvable : $REF" >&2; exit 1; }
git cat-file -e "$SHA:ingestion/docker-compose.yml" 2>/dev/null \
  || { echo "$REF ne contient pas ingestion/ : mauvaise branche ?" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git archive "$SHA" ingestion | tar -x -C "$TMP"

echo "==> Copie de ingestion/ (${SHA:0:7}) vers $HOST:~/$REMOTE_DIR"
# REMOTE_DIR est une constante : le développement côté client est voulu.
# shellcheck disable=SC2029
ssh "$HOST" "mkdir -p ~/$REMOTE_DIR/ingestion"
# Preserve runtime files created by containers (often owned by root) and secrets.
rsync -a --delete \
  --exclude '.env' \
  --exclude '__pycache__/' \
  --exclude '/dbt/target/' \
  --exclude '/dbt/logs/' \
  --exclude '/airbyte/json_credentials/' \
  -e ssh "$TMP/ingestion/" "$HOST:$REMOTE_DIR/ingestion/"
scp -q infra/data/docker-compose.override.yml "$HOST:$REMOTE_DIR/ingestion/docker-compose.override.yml"
scp -q infra/data/.env.example "$HOST:$REMOTE_DIR/env.template"

# Premier déploiement : .env créé depuis le modèle, secret Prefect généré sur place
# (il n'apparaît donc jamais sur ton poste ni dans git).
ssh "$HOST" bash -s -- "$REMOTE_DIR" "$SHA" <<'REMOTE'
set -euo pipefail
dir="$HOME/$1"; env_file="$dir/ingestion/.env"
echo "$2" > "$dir/DEPLOYED_REF"
if [ -f "$env_file" ]; then
  echo "==> .env déjà présent : conservé tel quel."
else
  install -m 600 "$dir/env.template" "$env_file"
  secret="cinestats:$(openssl rand -hex 16)"
  sed -i "s|^PREFECT_AUTH_STRING=.*|PREFECT_AUTH_STRING=$secret|" "$env_file"
  echo "==> .env créé (600). PREFECT_AUTH_STRING généré. Reste à saisir à la main, dans $env_file :"
  echo "      DBT_USER_POSTGRES_PASSWORD, INGESTION_REQUEST_POSTGRES_PASSWORD"
fi
REMOTE
echo "==> Terminé. Rien n'est démarré."
