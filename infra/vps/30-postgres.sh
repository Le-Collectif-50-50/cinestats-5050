#!/usr/bin/env bash
# PostgreSQL 16 de prod sur le VPS db, joignable uniquement via WireGuard.
# Prérequis : 00-base.sh puis « 10-wireguard.sh hub » sur ce VPS.
#
# - PostgreSQL 16 natif depuis apt.postgresql.org (versions mineures auto-appliquées)
# - écoute sur localhost + 10.50.0.1 seulement, TLS, scram-sha-256
# - pg_hba en liste blanche : un rôle, une base, une IP source
# - rôles au moindre privilège (sql/roles.sql), mots de passe générés
#
# Usage : ./30-postgres.sh <nom_base> [<ip_metabase> <wg|public>]
#   ip_metabase : 10.50.0.4 si Metabase est un pair WireGuard (« wg »), sinon son
#                 IPv4 publique (« public » : 5432 ouvert à cette seule IP, TLS obligatoire).
# Rejouable : ne régénère ni les mots de passe existants ni le certificat.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

DB_NAME="${1:-}"
METABASE_IP="${2:-}"
METABASE_VIA="${3:-}"
# Tirets acceptés (ex. cinestats-5050-db) : le nom est alors entre guillemets en SQL.
[[ "$DB_NAME" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Usage : $0 <nom_base> [<ip_metabase> <wg|public>]"
if [ -n "$METABASE_IP" ]; then
  is_ipv4 "$METABASE_IP" || die "IP Metabase invalide : $METABASE_IP"
  case "$METABASE_VIA" in
    wg) [[ "$METABASE_IP" == 10.50.0.* ]] || die "En mode wg, l'IP Metabase doit être en 10.50.0.x" ;;
    public) ;;
    *) die "Préciser « wg » ou « public » après l'IP Metabase" ;;
  esac
fi

require_root
ip -4 addr show dev "$WG_IF" 2>/dev/null | grep -q "inet $WG_DB_IP/" \
  || die "$WG_IF n'a pas l'adresse $WG_DB_IP : lancer d'abord « 10-wireguard.sh hub »."

PG_ETC="/etc/postgresql/$PG_VERSION/main"
PG_UNIT="postgresql@$PG_VERSION-main"
psql_admin() { sudo -u postgres psql -X -q -v ON_ERROR_STOP=1 "$@"; }

log "Dépôt apt.postgresql.org et PostgreSQL $PG_VERSION"
apt-get update
apt_install postgresql-common sudo
if ! ls /etc/apt/sources.list.d/pgdg.* >/dev/null 2>&1; then
  /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
fi
apt_install "postgresql-$PG_VERSION"
install_file apt/53cinestats-unattended-upgrades-pgdg /etc/apt/apt.conf.d/53cinestats-unattended-upgrades-pgdg
[ -d "$PG_ETC" ] || die "Cluster $PG_VERSION/main introuvable après installation."
grep -qE "^include_dir = 'conf.d'" "$PG_ETC/postgresql.conf" \
  || die "$PG_ETC/postgresql.conf n'inclut pas conf.d : config non standard."

log "Certificat TLS du serveur (auto-signé, SAN IP:$WG_DB_IP)"
install -d -m 700 -o postgres -g postgres "$PG_ETC/ssl"
if [ ! -f "$PG_ETC/ssl/server.crt" ]; then
  openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 -nodes -days 3650 \
    -subj "/CN=cinestats-db" -addext "subjectAltName=IP:$WG_DB_IP" \
    -keyout "$PG_ETC/ssl/server.key" -out "$PG_ETC/ssl/server.crt" 2>/dev/null
  chown postgres:postgres "$PG_ETC/ssl/server.key" "$PG_ETC/ssl/server.crt"
  chmod 600 "$PG_ETC/ssl/server.key"
fi

LISTEN_ADDRESSES="localhost,$WG_DB_IP"
if [ "$METABASE_VIA" = "public" ]; then
  LISTEN_ADDRESSES="$LISTEN_ADDRESSES,$(public_ipv4)"
fi
render postgresql/10-cinestats.conf "$PG_ETC/conf.d/10-cinestats.conf" 644 \
  LISTEN_ADDRESSES="$LISTEN_ADDRESSES" PG_VERSION="$PG_VERSION"

log "pg_hba.conf en liste blanche"
[ -f "$PG_ETC/pg_hba.conf.orig" ] || cp -p "$PG_ETC/pg_hba.conf" "$PG_ETC/pg_hba.conf.orig"
{
  cat <<EOF
# Généré par infra/vps/30-postgres.sh : ne pas éditer à la main, relancer le script.
# Liste blanche stricte (rôle × base × IP source) ; tout le reste est refusé.
# TYPE   DATABASE      USER               ADDRESS            METHOD
local    all           postgres                              peer
hostssl  $DB_NAME  app_ro             $WG_APP_IP/32      scram-sha-256
hostssl  $DB_NAME  app_migrator       $WG_APP_IP/32      scram-sha-256
hostssl  $DB_NAME  airbyte_user       $WG_DATA_IP/32      scram-sha-256
hostssl  $DB_NAME  prefect_user       $WG_DATA_IP/32      scram-sha-256
hostssl  $DB_NAME  scraper_user       $WG_DATA_IP/32      scram-sha-256
# dbt_user accepte aussi le non-TLS : les scrapers (connectés en dbt_user) forcent
# sslmode=disable. Le tunnel WireGuard chiffre quand même. Passer en hostssl dès
# que la branche analytics lit POSTGRES_SSLMODE dans les scrapers.
host     $DB_NAME  dbt_user           $WG_DATA_IP/32      scram-sha-256
EOF
  if [ -n "$METABASE_IP" ]; then
    cat <<EOF
hostssl  $DB_NAME  metabase_user      $METABASE_IP/32    scram-sha-256
hostssl  $DB_NAME  metabase_ops_user  $METABASE_IP/32    scram-sha-256
EOF
  fi
  cat <<EOF
host     all           all                0.0.0.0/0          reject
host     all           all                ::/0               reject
EOF
} > "$PG_ETC/pg_hba.conf.new"
chown postgres:postgres "$PG_ETC/pg_hba.conf.new"
chmod 640 "$PG_ETC/pg_hba.conf.new"
mv "$PG_ETC/pg_hba.conf.new" "$PG_ETC/pg_hba.conf"

log "Démarrage de Postgres après WireGuard"
install_file postgresql/10-wireguard.conf /etc/systemd/system/postgresql@.service.d/10-wireguard.conf
systemctl daemon-reload
systemctl enable "$PG_UNIT" >/dev/null 2>&1
systemctl restart "$PG_UNIT"

[ -n "$METABASE_IP" ] || warn "pg_hba sans Metabase : relancer avec <ip_metabase> <wg|public> s'il doit accéder à la base."

log "Pare-feu : 5432 joignable via $WG_IF uniquement"
ufw allow in on "$WG_IF" to any port 5432 proto tcp comment 'Postgres via WireGuard'
if [ "$METABASE_VIA" = "public" ]; then
  ufw allow from "$METABASE_IP" to any port 5432 proto tcp comment 'Postgres pour Metabase'
fi

log "Rôles (mots de passe générés pour les nouveaux uniquement)"
ROLES="app_migrator app_ro airbyte_user dbt_user prefect_user metabase_user metabase_ops_user"
for role in $ROLES; do
  if [ "$(psql_admin -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$role'")" != "1" ]; then
    pw="$(random_password)"
    # Mot de passe passé par stdin, pas en argument (invisible dans ps).
    printf "CREATE ROLE %s LOGIN PASSWORD '%s';\n" "$role" "$pw" | psql_admin
    record_secret "postgres_$role" "$pw"
  fi
done

if [ "$(psql_admin -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'")" != "1" ]; then
  log "Base $DB_NAME (propriétaire app_migrator)"
  psql_admin -c "CREATE DATABASE \"$DB_NAME\" OWNER app_migrator TEMPLATE template0 ENCODING 'UTF8'"
fi

log "Droits (sql/roles.sql)"
# Par stdin : postgres n'a pas accès au home (700) d'où le script est lancé.
psql_admin -d "$DB_NAME" -v db_name="$DB_NAME" < "$VPS_DIR/sql/roles.sql"

cat <<EOF

Postgres prêt : $DB_NAME, écoute sur $LISTEN_ADDRESSES.
Mots de passe des rôles créés : $CREDENTIALS_FILE (root uniquement).
  -> les copier dans le gestionnaire de mots de passe de l'équipe et dans les
     secrets GitHub / .env concernés, puis : sudo shred -u $CREDENTIALS_FILE
DATABASE_URL de l'app (secret GitHub, environment production) :
  postgresql+psycopg://app_ro:<mot_de_passe>@$WG_DB_IP:5432/$DB_NAME?sslmode=require
Étape suivante, AVANT d'importer des données : ./40-pgbackrest.sh
EOF
