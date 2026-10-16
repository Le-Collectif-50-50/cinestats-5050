#!/usr/bin/env bash
# Reverse proxy Caddy devant un service local (HTTPS automatique, Let's Encrypt).
# Prérequis : 00-base.sh, et l'enregistrement DNS du domaine déjà pointé vers ce VPS
# (Caddy demande son certificat au démarrage et réessaie tant que le DNS n'est pas bon).
#
# - Caddy officiel (paquet .deb de la release GitHub, empreinte SHA-512 vérifiée),
#   pas le paquet Ubuntu, trop ancien
# - un site : <domaine> -> 127.0.0.1:<port_amont>
# - ufw : 80 et 443 ouverts à tous
#
# Usage : ./60-caddy.sh <domaine> <port_amont>
# Exemple : sudo ./60-caddy.sh airbyte.cinestats5050.fr 9000
# Rejouable : le paquet n'est réinstallé que si la version diffère.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

DOMAIN="${1:-}"
UPSTREAM_PORT="${2:-}"
[[ "$DOMAIN" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$ ]] || die "Usage : $0 <domaine> <port_amont>"
[[ "$UPSTREAM_PORT" =~ ^[0-9]{2,5}$ ]] || die "Usage : $0 <domaine> <port_amont>"
require_root

CADDY_VERSION=2.11.7
BASE="https://github.com/caddyserver/caddy/releases/download/v$CADDY_VERSION"
DEB="caddy_${CADDY_VERSION}_linux_amd64.deb"

if [ "$(caddy version 2>/dev/null | awk '{print $1}')" = "v$CADDY_VERSION" ]; then
  log "Caddy $CADDY_VERSION déjà installé"
else
  log "Caddy $CADDY_VERSION (paquet officiel, empreinte vérifiée)"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/$DEB" "$BASE/$DEB"
  curl -fsSL -o "$tmp/checksums.txt" "$BASE/caddy_${CADDY_VERSION}_checksums.txt"
  (cd "$tmp" && grep " $DEB\$" checksums.txt | sha512sum -c -) || die "Empreinte de $DEB invalide : abandon."
  dpkg -i "$tmp/$DEB"
fi

log "Caddyfile : $DOMAIN -> 127.0.0.1:$UPSTREAM_PORT"
cat > /etc/caddy/Caddyfile <<CADDY
{
	email admin@cinestats5050.fr
}

$DOMAIN {
	encode zstd gzip
	header {
		Strict-Transport-Security "max-age=31536000"
		X-Content-Type-Options nosniff
		X-Frame-Options SAMEORIGIN
		-Server
	}
	reverse_proxy 127.0.0.1:$UPSTREAM_PORT
}
CADDY
caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null

log "Pare-feu : 80 et 443 ouverts"
ufw allow 80/tcp comment 'Caddy (ACME HTTP-01 + redirection)'
ufw allow 443/tcp comment 'Caddy'

systemctl enable caddy
systemctl restart caddy
sleep 2
systemctl is-active --quiet caddy || die "Caddy ne démarre pas : journalctl -u caddy"
cat <<EOF2

Caddy actif pour $DOMAIN. Le certificat est demandé dès que le DNS pointe vers $(public_ipv4) :
  journalctl -u caddy -n 30 --no-pager
EOF2
