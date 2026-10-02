# Fonctions partagées par les scripts infra/vps/*.sh. À sourcer, pas à exécuter.
# Cibles : Debian 12/13 et Ubuntu 24.04 (images OVH VPS).
# shellcheck shell=bash
# Les constantes ci-dessous servent aux scripts qui sourcent ce fichier.
# shellcheck disable=SC2034

set -euo pipefail

VPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="$VPS_DIR/files"

# Plan d'adressage WireGuard (voir docs/runbooks/securisation-vps-prod.md).
WG_IF=wg0
WG_PORT=51820
WG_DB_IP=10.50.0.1
WG_APP_IP=10.50.0.2
WG_DATA_IP=10.50.0.3

SSH_PORT=22022
PG_VERSION=16

export DEBIAN_FRONTEND=noninteractive
# Ubuntu : empêche needrestart de poser des questions pendant apt.
export NEEDRESTART_MODE=a

log()  { echo "==> $*"; }
warn() { echo "ATTENTION : $*" >&2; }
die()  { echo "ERREUR : $*" >&2; exit 1; }

require_root() {
  [ "$(id -u)" -eq 0 ] || die "Ce script doit être lancé en root (sudo)."
}

apt_install() {
  apt-get install -y --no-install-recommends \
    -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold "$@"
}

# Installe un fichier de files/ vers sa destination.
install_file() { # <chemin relatif dans files/> <destination> [mode]
  install -D -m "${3:-644}" "$FILES_DIR/$1" "$2"
}

# Copie un gabarit de files/ en remplaçant chaque @CLE@ par sa valeur.
render() { # <gabarit relatif dans files/> <destination> <mode> [CLE=valeur...]
  local src="$FILES_DIR/$1" dest="$2" mode="$3"
  shift 3
  local content kv key value
  content="$(cat "$src")"
  for kv in "$@"; do
    key="${kv%%=*}"
    value="${kv#*=}"
    # Motif et remplacement entre guillemets : « & » reste littéral (bash ≥ 5.2).
    content="${content//"@${key}@"/"$value"}"
  done
  if grep -qE '@[A-Z_]+@' <<<"$content"; then
    die "Variable de gabarit non remplacée dans $1"
  fi
  install -D -m "$mode" /dev/null "$dest"
  printf '%s\n' "$content" > "$dest"
}

# Ajoute une clé publique à authorized_keys (sans doublon).
add_authorized_key() { # <utilisateur> <fichier .pub>
  local user="$1" pubkey_file="$2" home key
  [ -f "$pubkey_file" ] || die "Clé publique introuvable : $pubkey_file"
  key="$(head -n1 "$pubkey_file")"
  case "$key" in
    ssh-ed25519\ *|ecdsa-sha2-*|sk-ssh-ed25519@openssh.com\ *|sk-ecdsa-sha2-*|ssh-rsa\ *) ;;
    *) die "$pubkey_file ne ressemble pas à une clé publique SSH" ;;
  esac
  home="$(getent passwd "$user" | cut -d: -f6)"
  install -d -m 700 -o "$user" -g "$user" "$home/.ssh"
  touch "$home/.ssh/authorized_keys"
  grep -qxF "$key" "$home/.ssh/authorized_keys" || echo "$key" >> "$home/.ssh/authorized_keys"
  chmod 600 "$home/.ssh/authorized_keys"
  chown "$user:$user" "$home/.ssh/authorized_keys"
}

# Mot de passe aléatoire alphanumérique (sûr dans une URL de connexion).
random_password() {
  local pw=""
  while [ "${#pw}" -lt 32 ]; do
    pw="$pw$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9')"
  done
  printf '%s' "${pw:0:32}"
}

# Interface et IPv4 publiques (celles de la route par défaut).
public_iface() { ip -4 route show default | awk '{print $5; exit}'; }
public_ipv4()  { ip -4 -o addr show dev "$(public_iface)" | awk '{split($4, a, "/"); print a[1]; exit}'; }

is_ipv4() { [[ "$1" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; }

# Fichier root-only où les scripts consignent les secrets générés.
CREDENTIALS_FILE=/root/cinestats-secrets.txt
record_secret() { # <nom> <valeur>
  install -m 600 /dev/null "$CREDENTIALS_FILE.tmp"
  { [ -f "$CREDENTIALS_FILE" ] && grep -v "^$1=" "$CREDENTIALS_FILE" || true; echo "$1=$2"; } > "$CREDENTIALS_FILE.tmp"
  mv "$CREDENTIALS_FILE.tmp" "$CREDENTIALS_FILE"
}
