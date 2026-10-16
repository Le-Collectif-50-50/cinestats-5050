#!/usr/bin/env bash
# node-exporter sur un VPS, scrapé par le Prometheus du VPS Services
# (repo cinestats-infra, stack monitoring/). Prérequis : 00-base.sh.
#
# - prometheus-node-exporter depuis apt, démarré et activé au boot
# - port 9100 ouvert à l'IP du Prometheus seulement (ufw), jamais à Internet
#
# Usage : ./55-exporters.sh <ip_prometheus>
# Exemple : sudo ./55-exporters.sh 203.0.113.10
# Rejouable : ne change rien si tout est déjà en place.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

PROM_IP="${1:-}"
is_ipv4 "$PROM_IP" || die "Usage : $0 <ip_prometheus (IPv4)>"
require_root

NODE_PORT=9100

log "prometheus-node-exporter"
apt_install prometheus-node-exporter
systemctl enable --now prometheus-node-exporter
systemctl is-active --quiet prometheus-node-exporter || die "prometheus-node-exporter ne démarre pas."

log "Pare-feu : $NODE_PORT/tcp ouvert à $PROM_IP seulement"
ufw allow from "$PROM_IP" to any port "$NODE_PORT" proto tcp comment 'Prometheus node-exporter'

if curl -fsS --max-time 5 "http://127.0.0.1:$NODE_PORT/metrics" | grep -q '^node_uname_info'; then
  log "node-exporter répond en local."
else
  die "node-exporter ne répond pas sur 127.0.0.1:$NODE_PORT."
fi
cat <<EOF

node-exporter prêt sur $(hostname). Depuis le VPS Prometheus ($PROM_IP), la cible
$(public_ipv4):$NODE_PORT doit passer à « UP » (cinestats-infra, monitoring/prometheus/targets/).
EOF
