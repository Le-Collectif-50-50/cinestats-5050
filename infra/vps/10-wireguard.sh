#!/usr/bin/env bash
# Réseau privé WireGuard en étoile centré sur db (10.50.0.1).
# app (10.50.0.2) et data (10.50.0.3) ne voient que db, pas l'un l'autre.
#
# Ordre (chaque commande affiche la clé publique à passer à la suivante) :
#   1. sur db   : ./10-wireguard.sh hub
#   2. sur app  : ./10-wireguard.sh spoke 10.50.0.2 <clé_publique_db> <ip_publique_db>
#      sur data : ./10-wireguard.sh spoke 10.50.0.3 <clé_publique_db> <ip_publique_db>
#   3. sur db   : ./10-wireguard.sh add-peer app  <clé_publique_app>  10.50.0.2 <ip_publique_app>
#                 ./10-wireguard.sh add-peer data <clé_publique_data> 10.50.0.3 <ip_publique_data>
#   (Metabase, si on a root sur son hôte : spoke 10.50.0.4 là-bas, puis add-peer metabase sur db.)

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

require_root

CONF="/etc/wireguard/$WG_IF.conf"
KEY="/etc/wireguard/$WG_IF.key"

usage() { sed -n '5,11p' "$0" >&2; exit 1; }

is_wg_ip()  { [[ "$1" =~ ^10\.50\.0\.([2-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-4])$ ]]; }
is_wg_key() { [[ "$1" =~ ^[A-Za-z0-9+/]{43}=$ ]]; }

ensure_key() {
  command -v wg >/dev/null || { apt-get update; apt_install wireguard-tools; }
  install -d -m 700 /etc/wireguard
  if [ ! -f "$KEY" ]; then
    (umask 077 && wg genkey > "$KEY")
  fi
}

pubkey() { wg pubkey < "$KEY"; }

case "${1:-}" in
  hub)
    ensure_key
    if [ ! -f "$CONF" ]; then
      (umask 077 && cat > "$CONF" <<EOF
# Hub WireGuard (db), géré par infra/vps/10-wireguard.sh. Pairs ajoutés par « add-peer ».
[Interface]
Address = $WG_DB_IP/24
ListenPort = $WG_PORT
PrivateKey = $(cat "$KEY")
EOF
      )
    fi
    systemctl enable --now "wg-quick@$WG_IF"
    log "Hub prêt. Clé publique de db : $(pubkey)"
    ;;

  add-peer)
    [ $# -eq 5 ] || usage
    name="$2" peer_key="$3" peer_wg_ip="$4" peer_public_ip="$5"
    [ -f "$CONF" ] || die "Lancer d'abord : $0 hub"
    [[ "$name" =~ ^[a-z0-9-]+$ ]] || die "Nom de pair invalide : $name"
    is_wg_key "$peer_key" || die "Clé publique WireGuard invalide : $peer_key"
    is_wg_ip "$peer_wg_ip" || die "IP WireGuard attendue dans 10.50.0.2-254 : $peer_wg_ip"
    is_ipv4 "$peer_public_ip" || die "IPv4 publique invalide : $peer_public_ip"
    if grep -qF "PublicKey = $peer_key" "$CONF"; then
      log "Pair $name déjà présent, rien à faire."
    else
      grep -qE "^AllowedIPs = $peer_wg_ip/32$" "$CONF" && die "$peer_wg_ip est déjà attribuée à un autre pair."
      cat >> "$CONF" <<EOF

[Peer]
# $name ($peer_public_ip)
PublicKey = $peer_key
AllowedIPs = $peer_wg_ip/32
EOF
      # Applique sans couper les tunnels existants.
      wg syncconf "$WG_IF" <(wg-quick strip "$WG_IF")
    fi
    ufw allow from "$peer_public_ip" to any port "$WG_PORT" proto udp comment "WireGuard $name"
    log "Pair $name ajouté. Vérifier la poignée de main : sudo wg show"
    ;;

  spoke)
    [ $# -eq 4 ] || usage
    my_wg_ip="$2" hub_key="$3" hub_public_ip="$4"
    is_wg_ip "$my_wg_ip" || die "IP WireGuard attendue dans 10.50.0.2-254 : $my_wg_ip"
    is_wg_key "$hub_key" || die "Clé publique WireGuard invalide : $hub_key"
    is_ipv4 "$hub_public_ip" || die "IPv4 publique invalide : $hub_public_ip"
    ensure_key
    (umask 077 && cat > "$CONF" <<EOF
# Pair WireGuard, géré par infra/vps/10-wireguard.sh. Seul db est joignable.
[Interface]
Address = $my_wg_ip/32
PrivateKey = $(cat "$KEY")

[Peer]
# db (hub)
PublicKey = $hub_key
Endpoint = $hub_public_ip:$WG_PORT
AllowedIPs = $WG_DB_IP/32
PersistentKeepalive = 25
EOF
    )
    systemctl enable "wg-quick@$WG_IF" >/dev/null 2>&1
    systemctl restart "wg-quick@$WG_IF"
    cat <<EOF
Pair prêt. À lancer maintenant sur db :
  sudo ./10-wireguard.sh add-peer <nom> $(pubkey) $my_wg_ip $(public_ipv4)
EOF
    ;;

  *) usage ;;
esac
