#!/usr/bin/env bash
# Compte ubuntu partagé : les administrateurs se connectent tous avec le compte ubuntu
# (leurs clés SSH sont dans son authorized_keys) et partagent donc un seul répertoire
# personnel. Choix assumé : on perd l'attribution nominative (sudo, historique du shell)
# et le sudo d'ubuntu est sans mot de passe, comme dans l'image OVH d'origine. Le journal
# SSH garde l'empreinte de la clé utilisée.
#
# Deux phases, pour ne jamais s'enfermer dehors :
#   enable <utilisateur>... : ubuntu peut se connecter (groupes ssh-users et sudo, sudoers,
#                             compte déverrouillé), reçoit les clés SSH de ces utilisateurs
#                             et leurs fichiers (~/vps, ~/cinestats-data…)
#   retire <utilisateur>... : à lancer APRÈS avoir testé « ssh ubuntu@... » avec chaque clé :
#                             vide leur authorized_keys, verrouille leur compte
#
# Usage : sudo ./08-shared-ubuntu.sh enable nicolas joel
#         sudo ./08-shared-ubuntu.sh retire nicolas joel
# Rejouable. DRY_RUN=1 : affiche ce qui serait fait, sans rien modifier.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

MODE="${1:-}"
shift || true
[ "$MODE" = enable ] || [ "$MODE" = retire ] || die "Usage : $0 <enable|retire> <utilisateur>..."
[ $# -ge 1 ] || die "Usage : $0 $MODE <utilisateur>..."
require_root

SHARED=ubuntu
DRY="${DRY_RUN:-}"
run() { if [ -n "$DRY" ]; then echo "[dry-run] $*"; else "$@"; fi; }
home_of() { getent passwd "$1" | cut -d: -f6; }

id "$SHARED" >/dev/null 2>&1 || die "Le compte $SHARED n'existe pas."
for u in "$@"; do
  id "$u" >/dev/null 2>&1 || die "Utilisateur inconnu : $u"
  [ "$u" != "$SHARED" ] || die "$SHARED ne peut pas être sa propre source."
done
UHOME="$(home_of "$SHARED")"
AUTH="$UHOME/.ssh/authorized_keys"

if [ "$MODE" = enable ]; then
  log "$SHARED peut se connecter (sshd : groupe ssh-users) et utiliser sudo"
  run groupadd -f ssh-users
  run usermod -aG sudo,ssh-users "$SHARED"
  # '!' = compte verrouillé ; '*' = pas de mot de passe, mais connexion par clé possible.
  if passwd -S "$SHARED" | awk '{exit !($2 == "L")}'; then run usermod -p '*' "$SHARED"; fi

  log "sudo sans mot de passe pour $SHARED (/etc/sudoers.d/90-cinestats-ubuntu)"
  if [ -z "$DRY" ]; then
    tmp="$(mktemp)"
    echo "$SHARED ALL=(ALL) NOPASSWD:ALL" > "$tmp"
    visudo -cf "$tmp" >/dev/null || die "sudoers invalide : abandon."
    install -m 440 -o root -g root "$tmp" /etc/sudoers.d/90-cinestats-ubuntu
    rm -f "$tmp"
  fi

  log "Clés SSH : ajoutées à $AUTH (sans doublon)"
  run install -d -m 700 -o "$SHARED" -g "$SHARED" "$UHOME/.ssh"
  [ -n "$DRY" ] || { touch "$AUTH"; chmod 600 "$AUTH"; }
  for u in "$@"; do
    src="$(home_of "$u")/.ssh/authorized_keys"
    [ -f "$src" ] || { warn "$u n'a pas d'authorized_keys"; continue; }
    added=0
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      case "$line" in \#*) continue ;; esac
      if ! grep -qxF "$line" "$AUTH" 2>/dev/null; then
        if [ -z "$DRY" ]; then echo "$line" >> "$AUTH"; fi
        added=$((added + 1))
      fi
    done < "$src"
    echo "    de $u : $added clé(s) ajoutée(s)"
  done
  [ -n "$DRY" ] || chown "$SHARED:$SHARED" "$AUTH"

  log "Fichiers de leurs répertoires personnels : rapatriés dans $UHOME"
  for u in "$@"; do
    home="$(home_of "$u")"
    for item in vps cinestats-data abctl-install.log; do
      [ -e "$home/$item" ] && [ ! -L "$home/$item" ] || continue
      if [ -e "$UHOME/$item" ]; then
        echo "    $item : déjà présent chez $SHARED, la copie de $u reste en $home/$item"
      else
        echo "    $item : $home/$item -> $UHOME/$item"
        run mv "$home/$item" "$UHOME/$item"
        run chown -R "$SHARED:$SHARED" "$UHOME/$item"
      fi
    done
  done
  cat <<EOF2

$SHARED est prêt. TESTE avant la phase « retire » (une session par clé) :
  ssh -p 22022 $SHARED@$(public_ipv4) 'id && sudo -n true && echo sudo-ok'
EOF2
else
  log "Retrait des comptes nominatifs : les clés vivent désormais sur $SHARED"
  grep -c '^[^#[:space:]]' "$AUTH" | xargs -I{} echo "    $AUTH contient {} clé(s)"
  for u in "$@"; do
    home="$(home_of "$u")"
    echo "    $u : authorized_keys vidé, compte verrouillé, retiré de sudo et ssh-users"
    [ -z "$DRY" ] || continue
    [ ! -f "$home/.ssh/authorized_keys" ] || : > "$home/.ssh/authorized_keys"
    passwd -l "$u" >/dev/null
    gpasswd -d "$u" sudo >/dev/null 2>&1 || true
    gpasswd -d "$u" ssh-users >/dev/null 2>&1 || true
  done
fi
