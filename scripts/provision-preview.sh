#!/usr/bin/env bash
# Amorçage d'une VM preview vierge (Debian/Ubuntu) pour cinestats-5050.
# À exécuter en root (ou via sudo) sur la machine cible, une seule fois.
#
# Ce script installe Docker + le plugin compose, crée l'arborescence attendue
# par .github/workflows/deploy-preview.yml (~/cinestats5050-preview), et
# prépare l'utilisateur de déploiement avec sa clé SSH publique.
#
# Usage : ./provision-preview.sh <deploy_user> <chemin_vers_clé_publique.pub>

set -euo pipefail

DEPLOY_USER="${1:?Usage: $0 <deploy_user> <chemin_vers_clé_publique.pub>}"
PUBKEY_FILE="${2:?Usage: $0 <deploy_user> <chemin_vers_clé_publique.pub>}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Ce script doit être lancé en root (sudo)." >&2
  exit 1
fi

if [ ! -f "$PUBKEY_FILE" ]; then
  echo "Fichier de clé publique introuvable : $PUBKEY_FILE" >&2
  exit 1
fi

echo "==> Installation de Docker Engine + plugin compose"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
else
  echo "Docker déjà installé, on passe."
fi

echo "==> Création de l'utilisateur de déploiement ($DEPLOY_USER)"
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$DEPLOY_USER"
fi
usermod -aG docker "$DEPLOY_USER"

echo "==> Installation de la clé SSH publique"
DEPLOY_HOME=$(eval echo "~$DEPLOY_USER")
install -d -m 700 -o "$DEPLOY_USER" -g "$DEPLOY_USER" "$DEPLOY_HOME/.ssh"
cat "$PUBKEY_FILE" >> "$DEPLOY_HOME/.ssh/authorized_keys"
chmod 600 "$DEPLOY_HOME/.ssh/authorized_keys"
chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_HOME/.ssh/authorized_keys"

echo "==> Arborescence de déploiement (~/cinestats5050-preview)"
install -d -m 755 -o "$DEPLOY_USER" -g "$DEPLOY_USER" \
  "$DEPLOY_HOME/cinestats5050-preview" \
  "$DEPLOY_HOME/cinestats5050-preview/certbot/conf" \
  "$DEPLOY_HOME/cinestats5050-preview/certbot/www" \
  "$DEPLOY_HOME/cinestats5050-preview/certbot/logs"

echo "==> Ouverture des ports 80/443 (si ufw est actif)"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

cat <<EOF

Terminé. Reste à faire manuellement :
  - secrets.SERVER_HOST  = IP ou hostname de cette machine
  - secrets.SSH_USERNAME = $DEPLOY_USER
  - secrets.SSH_PRIVATE_KEY = clé privée correspondant à $PUBKEY_FILE
  - vérifier que $DEPLOY_USER peut lancer 'docker compose' sans sudo
    (déconnexion/reconnexion nécessaire pour que le groupe 'docker' s'applique)
  - créer les enregistrements DNS preview.cinestats5050.fr / api.preview.cinestats5050.fr
    pointant vers cette machine (voir docs/MIGRATION.md)
EOF
