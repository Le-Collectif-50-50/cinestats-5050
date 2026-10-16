#!/usr/bin/env bash
# Sauvegardes pgBackRest du Postgres de prod (VPS db). Prérequis : 30-postgres.sh.
#
# - repo1 : disque du VPS, pour les restaurations rapides (erreur humaine, migration ratée)
# - repo2 : OVH Object Storage (S3) dans une autre région, chiffré : survit à la perte
#           du VPS ou du datacenter et à une compromission root du VPS db
# - archivage continu des WAL (restauration à un instant précis), complète le dimanche,
#   différentielle les autres jours, ping healthchecks.io à chaque sauvegarde
#
# Usage : ./40-pgbackrest.sh [fichier_env_s3] [--config-only]
#   --config-only : écrit la config sans créer la stanza ni sauvegarder, pour
#                   restaurer sur un VPS db neuf (reprise après sinistre, voir le runbook).
# Le fichier (root, chmod 600, hors de l'historique shell) contient :
#   S3_ENDPOINT=s3.<région>.io.cloud.ovh.net
#   S3_REGION=<région>
#   S3_BUCKET=<bucket>
#   S3_KEY=<access key>
#   S3_KEY_SECRET=<secret key>
#   HEALTHCHECK_URL=https://hc-ping.com/<uuid>     (optionnel)
#   REPO2_CIPHER_PASS=<phrase existante>            (uniquement pour une reprise après sinistre)
# Sans fichier : repo1 seul, avec un avertissement (à éviter en prod).
# Rejouable : la phrase de chiffrement de repo2 n'est jamais régénérée.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ENV_FILE="${1:-}"
MODE="${2:-}"
S3_ENDPOINT="" S3_REGION="" S3_BUCKET="" S3_KEY="" S3_KEY_SECRET="" HEALTHCHECK_URL="" REPO2_CIPHER_PASS=""
[ -z "$MODE" ] || [ "$MODE" = "--config-only" ] || die "Option inconnue : $MODE"

require_root
PG_DATA="/var/lib/postgresql/$PG_VERSION/main"
PG_ETC="/etc/postgresql/$PG_VERSION/main"
PG_UNIT="postgresql@$PG_VERSION-main"
[ -d "$PG_DATA" ] || die "Cluster Postgres introuvable : lancer d'abord 30-postgres.sh."
as_pg() { sudo -u postgres "$@"; }

if [ -n "$ENV_FILE" ]; then
  [ -f "$ENV_FILE" ] || die "Fichier introuvable : $ENV_FILE"
  [ "$(stat -c %a "$ENV_FILE")" = "600" ] || warn "$ENV_FILE devrait être en chmod 600."
  # shellcheck source=/dev/null
  . "$ENV_FILE"
  for var in S3_ENDPOINT S3_REGION S3_BUCKET S3_KEY S3_KEY_SECRET; do
    [ -n "${!var}" ] || die "$var manquant dans $ENV_FILE"
  done
  REPOS="1 2"
else
  warn "Pas de dépôt hors site : une panne du VPS ou du datacenter emporterait aussi les sauvegardes."
  REPOS="1"
fi

log "Installation de pgBackRest"
apt_install pgbackrest
install -d -m 750 -o postgres -g postgres /var/lib/pgbackrest /var/log/pgbackrest
install -d -m 755 /etc/pgbackrest

CONF=/etc/pgbackrest/pgbackrest.conf
EXISTING_PASS="$(grep -s '^repo2-cipher-pass=' "$CONF" | cut -d= -f2- || true)"
if [ -n "$EXISTING_PASS" ] && [ -n "$REPO2_CIPHER_PASS" ] && [ "$EXISTING_PASS" != "$REPO2_CIPHER_PASS" ]; then
  die "REPO2_CIPHER_PASS diffère de la phrase déjà configurée : la changer rendrait repo2 illisible."
fi
CIPHER_PASS="${EXISTING_PASS:-$REPO2_CIPHER_PASS}"
if [ "$REPOS" = "1 2" ] && [ -z "$CIPHER_PASS" ]; then
  CIPHER_PASS="$(random_password)$(random_password)"
  record_secret pgbackrest_repo2_cipher_pass "$CIPHER_PASS"
fi

log "Configuration (dépôts : $REPOS)"
{
  cat <<EOF
# Généré par infra/vps/40-pgbackrest.sh : relancer le script plutôt qu'éditer.
[global]
repo1-path=/var/lib/pgbackrest
repo1-retention-full=2
EOF
  if [ "$REPOS" = "1 2" ]; then
    cat <<EOF
repo2-type=s3
repo2-path=/pgbackrest
repo2-s3-endpoint=$S3_ENDPOINT
repo2-s3-region=$S3_REGION
repo2-s3-bucket=$S3_BUCKET
repo2-s3-key=$S3_KEY
repo2-s3-key-secret=$S3_KEY_SECRET
repo2-s3-uri-style=path
repo2-retention-full=4
repo2-cipher-type=aes-256-cbc
repo2-cipher-pass=$CIPHER_PASS
EOF
  fi
  cat <<EOF
compress-type=zst
process-max=2
start-fast=y
log-level-console=info
log-level-file=detail

[main]
pg1-path=$PG_DATA
EOF
} > "$CONF.new"
chown root:postgres "$CONF.new"
chmod 640 "$CONF.new"
mv "$CONF.new" "$CONF"

log "Archivage continu des WAL"
install_file postgresql/20-pgbackrest.conf "$PG_ETC/conf.d/20-pgbackrest.conf"
if [ "$(as_pg psql -X -tAc 'SHOW archive_mode')" != "on" ]; then
  systemctl restart "$PG_UNIT"
else
  systemctl reload "$PG_UNIT"
fi

log "Sauvegardes planifiées"
install_file pgbackrest/cinestats-pgbackrest-backup /usr/local/sbin/cinestats-pgbackrest-backup 755
install_file pgbackrest/cinestats-pgbackrest-restore-test /usr/local/sbin/cinestats-pgbackrest-restore-test 755
install -m 640 -o root -g postgres /dev/null /etc/default/cinestats-pgbackrest
cat > /etc/default/cinestats-pgbackrest <<EOF
# Généré par infra/vps/40-pgbackrest.sh.
PGBACKREST_REPOS="$REPOS"
HEALTHCHECK_URL="$HEALTHCHECK_URL"
EOF
# Pas de point dans le nom : cron ignore ces fichiers dans /etc/cron.d.
install_file pgbackrest/cinestats-pgbackrest.cron /etc/cron.d/cinestats-pgbackrest

if [ "$MODE" = "--config-only" ]; then
  cat <<EOF

Config écrite, sans stanza ni sauvegarde (--config-only). Reprise après sinistre :
  sudo systemctl stop $PG_UNIT
  sudo -u postgres pgbackrest --stanza=main --repo=2 --delta restore
  sudo systemctl start $PG_UNIT
puis relancer ce script sans --config-only pour revalider la stanza et sauvegarder.
EOF
  exit 0
fi

log "Stanza et vérification de l'archivage"
as_pg pgbackrest --stanza=main stanza-create
as_pg pgbackrest --stanza=main check

for repo in $REPOS; do
  if ! as_pg pgbackrest --stanza=main --repo="$repo" info | grep -q 'full backup:'; then
    log "Première sauvegarde complète sur repo$repo"
    as_pg pgbackrest --stanza=main --repo="$repo" --type=full backup
  fi
done
as_pg pgbackrest --stanza=main info

cat <<EOF

Sauvegardes en place (dépôts : $REPOS).
EOF
if [ "$REPOS" = "1 2" ]; then
  cat <<EOF
!!! La phrase de chiffrement de repo2 est dans $CREDENTIALS_FILE (pgbackrest_repo2_cipher_pass).
!!! Sans elle, les sauvegardes hors site sont illisibles si le VPS disparaît :
!!! la copier MAINTENANT dans le gestionnaire de mots de passe de l'équipe.
EOF
fi
cat <<EOF
Tester la restauration avant d'importer les données de prod :
  sudo cinestats-pgbackrest-restore-test 1
EOF
[ "$REPOS" = "1" ] || echo "  sudo cinestats-pgbackrest-restore-test 2"
