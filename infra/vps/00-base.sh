#!/usr/bin/env bash
# Socle de sécurité commun aux 3 VPS de prod (db, app, data).
# À lancer en root (sudo), une fois par VPS, depuis une session SSH sur le port 22.
#
# - mises à jour + unattended-upgrades (sécurité, reboot automatique décalé par VPS)
# - comptes admin nommés (sudo + clé SSH), groupe ssh-users
# - sshd : port 22022, clés uniquement, pas de root (avec retour arrière si le test échoue)
# - ufw (tout refusé en entrée sauf SSH), fail2ban, sysctl réseau, journald
#
# Usage : ./00-base.sh <db|app|data> <utilisateur>:<clé.pub> [<utilisateur>:<clé.pub>...]
# Exemple : sudo ./00-base.sh db nicolas:/tmp/nicolas.pub

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ROLE="${1:-}"
shift || true
[ $# -ge 1 ] || die "Usage : $0 <db|app|data> <utilisateur>:<clé.pub> [<utilisateur>:<clé.pub>...]"

case "$ROLE" in
  db)   REBOOT_TIME=04:00; ALLOW_TCP_FORWARDING=no ;;
  data) REBOOT_TIME=04:30; ALLOW_TCP_FORWARDING=local ;;
  app)  REBOOT_TIME=05:00; ALLOW_TCP_FORWARDING=no ;;
  *) die "Rôle inconnu : '$ROLE' (attendu : db, app ou data)" ;;
esac

require_root

log "Mises à jour système"
apt-get update
apt-get full-upgrade -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold
apt_install ufw fail2ban python3-systemd unattended-upgrades apt-listchanges \
  curl ca-certificates gnupg openssl iproute2 cron

log "Fuseau horaire et synchronisation NTP"
timedatectl set-timezone Europe/Paris
# Garde chrony s'il est déjà là, sinon le client NTP de systemd.
dpkg -s chrony >/dev/null 2>&1 || apt_install systemd-timesyncd
timedatectl set-ntp true || warn "Synchronisation NTP non activée : vérifier 'timedatectl status'."

log "Mises à jour automatiques (reboot si nécessaire à $REBOOT_TIME)"
install_file apt/20auto-upgrades /etc/apt/apt.conf.d/20auto-upgrades
render apt/52cinestats-unattended-upgrades /etc/apt/apt.conf.d/52cinestats-unattended-upgrades 644 \
  REBOOT_TIME="$REBOOT_TIME"

log "Comptes administrateurs"
groupadd -f ssh-users
for spec in "$@"; do
  user="${spec%%:*}"
  pubkey="${spec#*:}"
  [[ "$user" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Nom d'utilisateur invalide : '$user'"
  [ "$user" != "$spec" ] || die "Format attendu : <utilisateur>:<clé.pub> (reçu : '$spec')"
  if ! id "$user" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "$user"
  fi
  usermod -aG sudo,ssh-users "$user"
  add_authorized_key "$user" "$pubkey"
  # sudo demande le mot de passe du compte : il en faut un.
  if passwd -S "$user" | awk '{exit !($2 == "L" || $2 == "NP")}'; then
    if [ -t 0 ]; then
      echo "Choisis le mot de passe sudo de $user :"
      passwd "$user"
    else
      warn "$user n'a pas de mot de passe : lance 'sudo passwd $user' avant de fermer cette session."
    fi
  fi
done

if [ "$ROLE" = "data" ] && [ -z "$(swapon --show --noheadings)" ]; then
  log "Swap de 4 Go (Airbyte + Prefect + Chrome tiennent juste dans 8 Go)"
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo 'vm.swappiness = 10' > /etc/sysctl.d/98-cinestats-swap.conf
fi

log "Paramètres réseau du noyau"
install_file sysctl/99-cinestats.conf /etc/sysctl.d/99-cinestats.conf
sysctl --system >/dev/null

log "Journal systemd persistant, plafonné à 500 Mo"
install_file journald/10-cinestats.conf /etc/systemd/journald.conf.d/10-cinestats.conf
systemctl restart systemd-journald

log "Pare-feu ufw (entrée : SSH $SSH_PORT uniquement)"
ufw default deny incoming
ufw default allow outgoing
# « allow » et non « limit » : un déploiement GitHub Actions ouvre 5 connexions
# SSH d'affilée, ce qui déclencherait la limite d'ufw (6 / 30 s). fail2ban couvre.
ufw allow "$SSH_PORT/tcp" comment 'SSH'
ufw --force enable

log "fail2ban (jail sshd sur le port $SSH_PORT)"
render fail2ban/cinestats-sshd.local /etc/fail2ban/jail.d/cinestats-sshd.local 644 SSH_PORT="$SSH_PORT"
systemctl enable fail2ban >/dev/null 2>&1
systemctl restart fail2ban

log "Durcissement sshd"
grep -qE '^Include /etc/ssh/sshd_config\.d/\*\.conf' /etc/ssh/sshd_config \
  || die "/etc/ssh/sshd_config n'inclut pas sshd_config.d/*.conf : config non standard, à vérifier à la main."
SSHD_DROPIN=/etc/ssh/sshd_config.d/10-cinestats.conf
render ssh/10-cinestats.conf "$SSHD_DROPIN" 644 \
  SSH_PORT="$SSH_PORT" ALLOW_TCP_FORWARDING="$ALLOW_TCP_FORWARDING"
sshd -t || { rm -f "$SSHD_DROPIN"; die "Config sshd invalide, drop-in retiré."; }

restart_sshd() {
  # Ubuntu 24.04 active sshd par socket systemd, dont le port ne suit pas sshd_config
  # sans régénération : on repasse en service classique, comme sur Debian.
  if systemctl is-enabled --quiet ssh.socket 2>/dev/null || systemctl is-active --quiet ssh.socket; then
    systemctl disable --now ssh.socket
    systemctl enable ssh.service
  fi
  systemctl restart ssh.service
}
restart_sshd
sshd -T | grep -E '^(port|permitrootlogin|passwordauthentication|allowgroups|allowtcpforwarding) '

first_user="${1%%:*}"
if [ -t 0 ]; then
  cat <<EOF

>>> NE FERME PAS CETTE SESSION. Dans un autre terminal, teste :
      ssh -p $SSH_PORT $first_user@$(public_ipv4)
    puis 'sudo -v' une fois connecté.
EOF
  read -r -p "La connexion et sudo fonctionnent ? [o/N] " answer || answer=""
  if [ "$answer" != "o" ] && [ "$answer" != "O" ]; then
    warn "Retour arrière : sshd repasse sur sa config d'origine (port 22)."
    rm -f "$SSHD_DROPIN"
    ufw allow 22/tcp comment 'SSH (retour arrière)'
    restart_sshd
    die "Durcissement SSH annulé. Corrige le problème puis relance le script."
  fi
  ufw delete allow 22/tcp >/dev/null 2>&1 || true
else
  warn "Pas de terminal interactif : teste 'ssh -p $SSH_PORT $first_user@<ip>' AVANT de fermer cette session."
fi

cat <<EOF

Socle appliqué sur le VPS $ROLE. Reste à faire à la main (voir le runbook) :
  - verrouiller le compte par défaut OVH une fois ton accès nominatif vérifié :
      sudo passwd -l debian   (ou ubuntu) ; sudo cat /etc/sudoers.d/90-cloud-init-users  puis le supprimer
  - redémarrer si le noyau a été mis à jour : sudo reboot
EOF
