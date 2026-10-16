#!/usr/bin/env bash
# Alerte disque plein (> 80 %) via healthchecks.io, sur chacun des 3 VPS.
# Créer d'abord un check healthchecks.io par VPS (période 15 min, grâce 30 min).
#
# Usage : ./50-monitoring.sh <url_ping_healthchecks>
# Exemple : sudo ./50-monitoring.sh https://hc-ping.com/<uuid>

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

URL="${1:-}"
[[ "$URL" =~ ^https:// ]] || die "Usage : $0 <url_ping_healthchecks (https://...)>"
require_root

install_file monitoring/cinestats-disk-check /usr/local/sbin/cinestats-disk-check 755
install -m 600 /dev/null /etc/default/cinestats-monitoring
cat > /etc/default/cinestats-monitoring <<CONF
# Généré par infra/vps/50-monitoring.sh.
DISK_THRESHOLD=80
HEALTHCHECK_DISK_URL="$URL"
CONF
# Pas de point dans le nom : cron ignore ces fichiers dans /etc/cron.d.
install_file monitoring/cinestats-monitoring.cron /etc/cron.d/cinestats-monitoring

/usr/local/sbin/cinestats-disk-check
log "Alerte disque active : le check healthchecks.io doit passer au vert d'ici quelques secondes."
