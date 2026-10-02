#!/usr/bin/env bash
# Docker durci pour les VPS app et data (db n'a pas de Docker).
#
# - Docker Engine + compose depuis le dépôt apt officiel (pas de « curl | sh »)
# - logs plafonnés, live-restore, no-new-privileges (app)
# - chaîne DOCKER-USER : bloque l'accès Internet aux ports publiés par Docker,
#   qu'ufw ne filtre pas (app : 80/443 seulement ; data : aucun)
# - app : compte « deploy » (groupe docker, sans sudo) pour GitHub Actions
#
# Usage : ./20-docker.sh app <clé_publique_deploy.pub>
#         ./20-docker.sh data

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

ROLE="${1:-}"
case "$ROLE" in
  app)
    DEPLOY_PUBKEY="${2:?Usage : $0 app <clé_publique_deploy.pub>}"
    ALLOWED_TCP_PORTS="80 443"
    # Pas sur data : le nœud kind d'Airbyte transmettrait le drapeau à tous ses pods.
    NO_NEW_PRIVILEGES=true
    ;;
  data)
    ALLOWED_TCP_PORTS=""
    NO_NEW_PRIVILEGES=false
    ;;
  *) die "Usage : $0 <app|data> [clé_publique_deploy.pub]" ;;
esac

require_root
# shellcheck source=/dev/null
. /etc/os-release

log "Dépôt apt officiel Docker ($ID $VERSION_CODENAME)"
install -d -m 755 /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$ID $VERSION_CODENAME stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update

log "Configuration du démon (avant installation, pour que le premier démarrage l'applique)"
render docker/daemon.json /etc/docker/daemon.json 644 NO_NEW_PRIVILEGES="$NO_NEW_PRIVILEGES"
apt_install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin iptables
systemctl enable docker >/dev/null 2>&1
systemctl restart docker

log "Filtrage DOCKER-USER (ports joignables depuis Internet : ${ALLOWED_TCP_PORTS:-aucun})"
install_file docker/cinestats-docker-user-firewall /usr/local/sbin/cinestats-docker-user-firewall 755
echo "ALLOWED_TCP_PORTS=\"$ALLOWED_TCP_PORTS\"" > /etc/default/cinestats-docker-user-firewall
install_file docker/cinestats-docker-user-firewall.service /etc/systemd/system/cinestats-docker-user-firewall.service
systemctl daemon-reload
systemctl enable cinestats-docker-user-firewall >/dev/null 2>&1
systemctl restart cinestats-docker-user-firewall

if [ "$ROLE" = "app" ]; then
  # Les ports publiés passent par DOCKER-USER en IPv4 ; en IPv6, docker-proxy écoute
  # directement sur l'hôte et c'est ufw qui filtre.
  ufw allow 80/tcp comment 'HTTP (nginx)'
  ufw allow 443/tcp comment 'HTTPS (nginx)'

  log "Compte deploy pour GitHub Actions"
  if ! id deploy >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash deploy
  fi
  # Rappel : le groupe docker équivaut à root. La clé privée ne vit que dans le
  # secret SSH_PRIVATE_KEY de l'environment GitHub « production ».
  usermod -aG docker,ssh-users deploy
  add_authorized_key deploy "$DEPLOY_PUBKEY"
  DEPLOY_HOME="$(getent passwd deploy | cut -d: -f6)"
  install -d -m 755 -o deploy -g deploy \
    "$DEPLOY_HOME/cinestats5050" \
    "$DEPLOY_HOME/cinestats5050/certbot" \
    "$DEPLOY_HOME/cinestats5050/certbot/conf" \
    "$DEPLOY_HOME/cinestats5050/certbot/www" \
    "$DEPLOY_HOME/cinestats5050/certbot/logs"
fi

docker info --format 'Docker {{.ServerVersion}}, logs : {{.LoggingDriver}}'
cat <<EOF

Docker prêt sur le VPS $ROLE. Contrôle depuis ton poste (doit expirer sauf 80/443 sur app) :
  nmap -Pn -p- $(public_ipv4)
EOF
