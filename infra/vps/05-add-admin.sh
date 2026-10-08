#!/usr/bin/env bash
# Ajoute un administrateur nominatif (sudo + clé SSH) sur un VPS, sans toucher à sshd
# ni au pare-feu. À utiliser :
# - sur les VPS durcis par 00-base.sh (db, app, data) : plus léger que de relancer
#   00-base.sh ;
# - sur ceux qui n'ont pas reçu 00-base.sh (Metabase, Services, preview), où le
#   relancer remplacerait leur pare-feu par « tout refusé sauf SSH » et couperait
#   les services web.
#
# Usage : sudo ./05-add-admin.sh <utilisateur>:<clé.pub> [<utilisateur>:<clé.pub>...]
# Lancer dans une session avec terminal (ssh -t) : le mot de passe sudo du compte est
# demandé, et la personne devra le changer à sa première connexion.
# Rejouable : un compte existant garde son mot de passe, la clé n'est pas dupliquée.

# shellcheck source=lib.sh
. "$(dirname "$0")/lib.sh"

[ $# -ge 1 ] || die "Usage : $0 <utilisateur>:<clé.pub> [<utilisateur>:<clé.pub>...]"
require_root

groupadd -f ssh-users
for spec in "$@"; do
  user="${spec%%:*}"
  pubkey="${spec#*:}"
  [ "$user" != "$spec" ] || die "Format attendu : <utilisateur>:<clé.pub> (reçu : '$spec')"
  [[ "$user" =~ ^[a-z_][a-z0-9_-]*$ ]] || die "Nom d'utilisateur invalide : '$user'"
  [ -f "$pubkey" ] || die "Clé publique introuvable : $pubkey"

  if id "$user" >/dev/null 2>&1; then
    log "Compte $user existant : mot de passe conservé"
    new=false
  else
    log "Création du compte $user"
    useradd --create-home --shell /bin/bash "$user"
    new=true
  fi
  usermod -aG sudo,ssh-users "$user"
  add_authorized_key "$user" "$pubkey"

  # sudo demande le mot de passe du compte : il en faut un.
  if passwd -S "$user" | awk '{exit !($2 == "L" || $2 == "NP")}'; then
    if [ -t 0 ]; then
      echo "Choisis un mot de passe sudo TEMPORAIRE pour $user (à lui transmettre par un canal sûr) :"
      passwd "$user"
      chage -d 0 "$user"
      log "$user devra changer son mot de passe à sa première connexion"
    else
      warn "$user n'a pas de mot de passe : relance dans une session avec terminal (ssh -t)."
    fi
  fi
  if $new; then log "OK : ssh -p $SSH_PORT $user@$(public_ipv4)"; fi
done
