# Runbook — Mise en service et sécurisation des VPS de prod

Procédure pas-à-pas pour installer et durcir les 3 VPS OVH de la production, avec les scripts de `infra/vps/`. À dérouler **dans l'ordre** : chaque étape suppose les précédentes faites.

## Vue d'ensemble

| VPS | Rôle | Localisation | Ports publics |
|---|---|---|---|
| `db` | PostgreSQL 16, sauvegardes pgBackRest | France | SSH `22022` ; WireGuard `51820/udp` (IP de `app`/`data` seulement) |
| `app` | nginx + frontend + backend (déployés par `.github/workflows/deploy.yml`) | France | `80`, `443`, SSH `22022` |
| `data` | Airbyte, Prefect, dbt, scrapers | Canada | SSH `22022` |

```
          Internet ── 80/443 ──► app ─┐
                                      │  WireGuard 10.50.0.0/24
    (SSH 22022 sur les 3, clés seules) ├──────────────────────► db 10.50.0.1 : Postgres
                                      │                         (n'écoute pas sur l'IP publique)
                              data ───┘
                         (UIs Airbyte/Prefect : tunnel SSH uniquement)
```

Principes :
- Seul `db` reçoit du trafic WireGuard. `app` (`10.50.0.2`) et `data` (`10.50.0.3`) ne se voient pas entre eux.
- Postgres n'accepte qu'une liste blanche « rôle × base × IP source ». Le backend n'a qu'un rôle en lecture seule.
- **Piège Docker :** les ports publiés par Docker contournent ufw. Sur `app` et `data`, la chaîne `DOCKER-USER` les filtre (`20-docker.sh`).
- La BDD est sauvegardée en local **et** hors site, et la restauration est testée **avant** l'import des données.

Les scripts sont idempotents : on peut les rejouer sans risque, par exemple pour ajouter un admin ou un pair.

## 0. Préparation

### 0.1 Espace client OVH
1. **Réinstaller les 3 VPS en Debian 13**, en collant ta clé SSH publique dans le formulaire de réinstallation. Le compte créé s'appelle `debian`.
2. **Activer la double authentification** sur le compte OVH et limiter les comptes qui y ont accès : quiconque contrôle ce compte peut réinstaller ou supprimer les VPS.
3. Noter les IPv4 publiques : `IP_DB`, `IP_APP`, `IP_DATA`, ainsi que celle de l'hôte Metabase si elle est fixe.

### 0.2 Sur ton poste
```bash
# Clé dédiée au déploiement GitHub Actions (sans passphrase : utilisée par la CI)
ssh-keygen -t ed25519 -N '' -C deploy@cinestats-prod -f ~/.ssh/cinestats_deploy_prod

# Copier les scripts et ta clé publique sur chaque VPS (port 22 tant que le socle n'est pas posé)
for ip in IP_DB IP_APP IP_DATA; do
  scp -r infra/vps ~/.ssh/id_ed25519.pub debian@$ip:~/
done
```

**Nom de la base : `cinestats-5050-db`.** L'app et la stack data la partagent : c'est aussi la valeur de `POSTGRES_DB` côté `data`. À cause des tirets, le nom doit être entre guillemets dans une requête SQL écrite à la main (`ALTER DATABASE "cinestats-5050-db" …`). Les scripts, les URL de connexion et `psql -d` n'en ont pas besoin.

## 1. Socle de sécurité (sur les 3 VPS)

Sur chaque VPS, connecté en `debian` (port 22) :
```bash
sudo ~/vps/00-base.sh db   <toi>:/home/debian/id_ed25519.pub     # sur db
sudo ~/vps/00-base.sh app  <toi>:/home/debian/id_ed25519.pub     # sur app
sudo ~/vps/00-base.sh data <toi>:/home/debian/id_ed25519.pub     # sur data
```
Plusieurs admins se passent à la suite : `alice:/chemin/alice.pub bob:/chemin/bob.pub`.

Ce que fait le script :
- mise à jour complète et `unattended-upgrades` (sécurité seule), avec reboot automatique si nécessaire à 04:00 (`db`), 04:30 (`data`) ou 05:00 (`app`), heure de Paris ;
- comptes admin nominatifs (sudo avec mot de passe, demandé pendant le script) ;
- sshd sur le port 22022, clés uniquement, sans root, réservé au groupe `ssh-users` ;
- ufw qui refuse tout en entrée sauf SSH, fail2ban, sysctl réseau, journal plafonné à 500 Mo, 4 Go de swap sur `data`.

**Le script s'arrête et te demande de tester une 2ᵉ connexion** :
```bash
ssh -p 22022 <toi>@IP_xxx    # puis : sudo -v
```
Si tu réponds autre chose que `o`, il remet sshd sur le port 22 et rouvre ce port. En dernier recours, la console KVM de l'espace client OVH reste disponible.

Une fois connecté avec ton compte nominatif :
```bash
sudo passwd -l debian                                  # verrouille le compte par défaut
sudo cat /etc/sudoers.d/90-cloud-init-users            # vérifier qu'il ne concerne que debian…
sudo rm /etc/sudoers.d/90-cloud-init-users             # …puis le supprimer
sudo reboot                                            # si le noyau a été mis à jour
```

À ajouter dans le `~/.ssh/config` de l'équipe (la suite du runbook utilise ces alias) :
```
Host cinestats-db
  HostName IP_DB
Host cinestats-app
  HostName IP_APP
Host cinestats-data
  HostName IP_DATA
Host cinestats-*
  Port 22022
  User <toi>
```

Puis recopier les scripts dans ton home nominatif (celui de `debian` est en `700`) :
```bash
for h in cinestats-db cinestats-app cinestats-data; do scp -r infra/vps $h:~/; done
scp ~/.ssh/cinestats_deploy_prod.pub cinestats-app:~/
```

**Optionnel : Edge Network Firewall OVH.** Si l'espace client le propose pour ces IP, c'est une 2ᵉ couche de filtrage en amont du VPS, insensible aux erreurs de config locale. Il reprend les ports publics de la vue d'ensemble. **À activer seulement après cette étape**, sinon on se coupe le port 22 utilisé pendant le socle.

## 2. Réseau privé WireGuard

Chaque commande affiche la clé publique à passer à la suivante :
```bash
# 1. sur db
sudo ~/vps/10-wireguard.sh hub                               # → clé publique de db

# 2. sur app, puis sur data
sudo ~/vps/10-wireguard.sh spoke 10.50.0.2 <clé_db> IP_DB     # sur app  → clé publique de app
sudo ~/vps/10-wireguard.sh spoke 10.50.0.3 <clé_db> IP_DB     # sur data → clé publique de data

# 3. sur db
sudo ~/vps/10-wireguard.sh add-peer app  <clé_app>  10.50.0.2 IP_APP
sudo ~/vps/10-wireguard.sh add-peer data <clé_data> 10.50.0.3 IP_DATA
sudo wg show                                                 # « latest handshake » pour chaque pair
```

**Metabase** (on a sudo sur son hôte) : y copier `infra/vps/` et lancer `sudo ./10-wireguard.sh spoke 10.50.0.4 <clé_db> IP_DB`, puis `add-peer metabase <clé_metabase> 10.50.0.4 <IP_METABASE>` sur `db`. Le script suppose Debian/Ubuntu ; sur une autre distribution, installer `wireguard-tools` à la main et reprendre le même `wg0.conf`. Si Metabase tourne dans Docker, il atteint `10.50.0.1` via le NAT de Docker, comme le backend.

## 3. PostgreSQL (sur db)

```bash
sudo ~/vps/30-postgres.sh cinestats-5050-db 10.50.0.4 wg     # Metabase en pair WireGuard (on a sudo sur son hôte)
# Variantes : sans argument Metabase (pas d'accès), ou <IP_METABASE> public
# (5432 ouvert à cette seule IP, TLS obligatoire) si Metabase ne peut pas rejoindre WireGuard.
```

Ce que fait le script :
- installe PostgreSQL 16 depuis apt.postgresql.org (les versions mineures s'appliquent automatiquement) ;
- écoute sur `localhost` et `10.50.0.1`, active TLS (certificat auto-signé) et scram-sha-256 ;
- trace les connexions avec leur IP source ;
- démarre Postgres après WireGuard ;
- crée les rôles et applique les droits de `infra/vps/sql/roles.sql`.

| Rôle | Depuis | Droits |
|---|---|---|
| `app_ro` | app | `SELECT` sur le schéma `public`, transactions en lecture seule, `statement_timeout` 10 s, 20 connexions max |
| `app_migrator` | app (ponctuellement) | propriétaire de la base : migrations Alembic et import des données |
| `airbyte_user` | data | propriétaire de `raw`, `CREATE` sur la base (voir « Écarts assumés ») |
| `dbt_user` | data | propriétaire de `staging`, `intermediate`, `fnl` ; écrit dans `raw` et `ops` |
| `prefect_user` | data | `SELECT`/`UPDATE` sur `ops.ingestion_run_requests` uniquement |
| `metabase_user` | Metabase | lecture seule de `fnl` |
| `metabase_ops_user` | Metabase | lecture de toutes les couches, écriture dans `ops` |

Les mots de passe des rôles créés sont écrits dans `/root/cinestats-secrets.txt` (root, `600`). **Les copier dans le gestionnaire de mots de passe de l'équipe**, puis `sudo shred -u /root/cinestats-secrets.txt` une fois l'étape 4 finie : elle y ajoute la phrase de chiffrement des sauvegardes.

Relancer `30-postgres.sh` régénère `pg_hba.conf` : toujours lui repasser les mêmes arguments Metabase, sinon Metabase perd son accès. Pour **réappliquer seulement les droits**, par exemple après la création de `ops.ingestion_run_requests` (runbook analytics §4.3), qui donne ses droits à `prefect_user` :
```bash
sudo -u postgres psql -X -q -d cinestats-5050-db -v db_name=cinestats-5050-db < ~/vps/sql/roles.sql
```

## 4. Sauvegardes (sur db) — avant toute donnée de prod

### Pourquoi deux dépôts
- **`repo1`, sur le disque du VPS :** restauration rapide après une erreur humaine (migration ratée, `DROP`, `dbt --full-refresh` malheureux).
- **`repo2`, hors site et chiffré, dans OVH Object Storage :** survit à ce qui emporte le VPS avec ses sauvegardes locales. Par exemple une panne disque ou d'hyperviseur, un incident de datacenter (l'incendie de Strasbourg en 2021 a détruit des serveurs et les sauvegardes stockées sur le même site), une suppression ou réinstallation par erreur depuis l'espace client, ou un attaquant root qui efface tout.

### Mise en place
1. **Object Storage OVH :** créer un bucket S3 dans une **autre région** que `db`, et un utilisateur S3 qui n'a accès qu'à ce bucket. Noter l'endpoint et la région indiqués par OVH (par exemple `s3.gra.io.cloud.ovh.net` / `gra`).
2. **healthchecks.io :** créer un check « sauvegarde db », période 1 jour, délai de grâce 2 h.
3. Lancer le script :
   ```bash
   sudo install -m 600 /dev/null /root/pgbackrest-s3.env
   sudo nano /root/pgbackrest-s3.env
   #   S3_ENDPOINT=s3.<région>.io.cloud.ovh.net
   #   S3_REGION=<région>
   #   S3_BUCKET=<bucket>
   #   S3_KEY=<access key>
   #   S3_KEY_SECRET=<secret key>
   #   HEALTHCHECK_URL=https://hc-ping.com/<uuid>
   sudo ~/vps/40-pgbackrest.sh /root/pgbackrest-s3.env
   ```
4. **Mettre la phrase de chiffrement de `repo2` dans le gestionnaire de mots de passe** (`pgbackrest_repo2_cipher_pass` dans `/root/cinestats-secrets.txt`). Sans elle, les sauvegardes hors site sont illisibles le jour où le VPS disparaît. Garder aussi le contenu de `/root/pgbackrest-s3.env` à cet endroit.
5. Tester la restauration des deux dépôts :
   ```bash
   sudo cinestats-pgbackrest-restore-test 1
   sudo cinestats-pgbackrest-restore-test 2
   ```

Ce qui est en place ensuite :
- archivage continu des WAL (au plus 15 min de données perdues), sauvegarde complète le dimanche à 01:30 et différentielle les autres jours ;
- rétention de 2 semaines en local et 4 semaines hors site ;
- un ping healthchecks.io à chaque sauvegarde (`/fail` en cas d'échec).

### Restaurer pour de vrai (incident)
```bash
# Sur le VPS db existant : revenir au dernier état, ou à un instant précis
sudo systemctl stop postgresql@16-main
sudo -u postgres pgbackrest --stanza=main --repo=1 --delta restore
#   ou : … --type=time --target="2026-10-02 14:00:00+02" --target-action=promote restore
sudo systemctl start postgresql@16-main
```
Si le VPS `db` est perdu :
1. En réinstaller un et dérouler les étapes 1 à 3 ; les pairs WireGuard se ré-ajoutent avec `add-peer`.
2. Mettre `REPO2_CIPHER_PASS=<phrase du gestionnaire>` dans `/root/pgbackrest-s3.env`.
3. Lancer `sudo ~/vps/40-pgbackrest.sh /root/pgbackrest-s3.env --config-only`.
4. Restaurer avec `--repo=2` comme ci-dessus.
5. Relancer `40-pgbackrest.sh` sans `--config-only`.

## 5. VPS app

```bash
sudo ~/vps/20-docker.sh app ~/cinestats_deploy_prod.pub
```
Ce que fait le script :
- installe Docker depuis le dépôt officiel, avec logs plafonnés et `no-new-privileges` ;
- limite `DOCKER-USER` aux ports 80 et 443 ;
- crée le compte `deploy` (groupe `docker`, sans sudo) et `~/cinestats5050`.

**GitHub** (commandes `gh` détaillées dans `docs/MIGRATION.md`) — environment `production` :
- **Secrets :**
  - `SERVER_HOST=IP_APP`, `SSH_USERNAME=deploy` ;
  - `SSH_PRIVATE_KEY` : contenu de `~/.ssh/cinestats_deploy_prod` ;
  - `DATABASE_URL=postgresql+psycopg://app_ro:<mdp>@10.50.0.1:5432/cinestats-5050-db?sslmode=require` ;
  - `CERTBOT_EMAIL` et `OVH_APPLICATION_KEY` / `OVH_APPLICATION_SECRET` / `OVH_CONSUMER_KEY` : le token OVH du certificat (voir `docs/MIGRATION.md` §6).
- **Variables :**
  - `SERVER_PORT=22022` ;
  - `DOMAIN=cinestats5050.fr`, `API_DOMAIN=api.cinestats5050.fr`, `CERT_EXTRA_DOMAINS="www.cinestats5050.fr www.api.cinestats5050.fr"` ;
  - `SSH_KNOWN_HOSTS` : la ligne affichée à la fin de `20-docker.sh`. Le workflow épingle la clé d'hôte du serveur avec.
- **Protection :** un reviewer obligatoire, déploiement limité à la branche `production`. Le secret `SSH_PRIVATE_KEY` donne l'équivalent d'un accès root à `app`. Les reviewers obligatoires sont gratuits sur un dépôt public.
  ```bash
  REPO=Le-Collectif-50-50/cinestats-5050
  ID=$(gh api users/<login_reviewer> --jq .id)
  gh api -X PUT repos/$REPO/environments/production --input - <<EOF
  {"reviewers":[{"type":"User","id":$ID}],"deployment_branch_policy":{"protected_branches":false,"custom_branch_policies":true}}
  EOF
  gh api -X POST repos/$REPO/environments/production/deployment-branch-policies -f name=production -f type=branch
  ```

**Import des données de prod existantes**, via un dump de la base actuelle, hébergée sur l'infra Data For Good :
1. Vérifier la version du serveur (`SELECT version();`) et la liste des schémas (`\dn`). Puis dumper avec un client `pg_dump` de la même version majeure, le plus simple étant via Docker :
   ```bash
   docker run --rm -v "$PWD:/out" postgres:16-alpine \
     pg_dump -Fc --no-owner --no-acl -n public -f /out/cinestats.dump "<url_base_actuelle>"
   chmod 600 cinestats.dump      # données personnelles : ne pas le laisser traîner
   ```
   Si le serveur est en version 17 ou plus, utiliser l'image correspondante et un dump texte (`-Fp`), qui se restaure mieux dans un Postgres plus ancien.
2. Copie : `scp -P 22022 cinestats.dump cinestats-db:~/`.
3. Restauration, sur `db` :
   ```bash
   # Par stdin : postgres ne peut pas lire ton home. Les tables appartiendront à app_migrator.
   sudo -u postgres pg_restore --no-owner --role=app_migrator -d cinestats-5050-db < ~/cinestats.dump
   # dump texte (-Fp) : sudo -u postgres psql -d cinestats-5050-db -c 'SET ROLE app_migrator' -f /dev/stdin < ~/cinestats.sql
   sudo -u postgres psql -X -q -d cinestats-5050-db -v db_name=cinestats-5050-db < ~/vps/sql/roles.sql   # droits d'app_ro, etc.
   sudo cinestats-pgbackrest-backup full      # première sauvegarde avec les données
   sudo cinestats-pgbackrest-restore-test 2
   shred -u ~/cinestats.dump
   ```

L'erreur `schema "public" already exists` de `pg_restore` est attendue et sans effet. `-n public` ne reprend que les tables de l'app : les schémas data (`raw`, `fnl`…) sont reconstruits par Airbyte et dbt.

**Mise en ligne :**
1. Faire pointer les enregistrements DNS `cinestats5050.fr`, `www`, `api` et `www.api` vers `IP_APP`.
2. Rien à faire pour le certificat : il est émis automatiquement au premier déploiement, par DNS-01 via l'API OVH (voir `docs/DEPLOYMENT.md`). Les secrets `CERTBOT_EMAIL`, `OVH_*` et les variables `DOMAIN`, `API_DOMAIN`, `CERT_EXTRA_DOMAINS` doivent être posés avant.
3. Lancer `scripts/promote.sh production`.
4. Les migrations Alembic se jouent à la main avec `app_migrator` (commande dans `docs/DEPLOYMENT.md`).

## 6. VPS data (Canada)

```bash
sudo ~/vps/20-docker.sh data       # DOCKER-USER : aucun port de conteneur joignable depuis Internet
```

Le filtrage protège **dès aujourd'hui** les ports que la stack actuelle publie sur toutes les interfaces : Airbyte `8000` (abctl/kind), Prefect `4222` et browserless `3000`. Pas besoin d'attendre les correctifs de la branche analytics pour ça.

Ensuite, suivre le runbook analytics (branche `analytics/fix_join`) : installation d'abctl, bootstrap Airbyte, `docker compose up`. Avec ces réglages :
- **Dans `.env` :**
  - `POSTGRES_HOST=10.50.0.1`, `POSTGRES_SSLMODE=require` ;
  - les mots de passe des rôles de l'étape 3 ;
  - pour `PREFECT_API_DATABASE_CONNECTION_URL`, une base Postgres **locale à `data`**, pas la BDD de prod.
- **Airbyte :** changer les identifiants générés (`abctl local credentials`).
- **Compte de service Google :** Sheets en lecture seule, Sheets partagés en « Lecteur ». Le JSON en `chmod 600`.
- **UIs :** uniquement par tunnel SSH :
  ```bash
  ssh -L 8000:localhost:8000 -L 4222:localhost:4222 cinestats-data
  # puis http://localhost:8000 (Airbyte) et http://localhost:4222 (Prefect)
  ```

**À transmettre à l'auteur de la branche analytics :**
1. Rendre `sslmode` configurable dans les scrapers, qui codent aujourd'hui `disable` en dur dans leurs `config.json` (lire `POSTGRES_SSLMODE`).
   - Une fois fait, passer la ligne `dbt_user` de `pg_hba` en `hostssl`, dans `30-postgres.sh`.
2. Dans `ingestion/docker-compose.yml`, publier Prefect sur `127.0.0.1` seulement et ne plus publier browserless (réseau interne).
3. Héberger la base de métadonnées Prefect sur `data`.
4. Donner aux scrapers un rôle dédié plutôt que `dbt_user`.

**RGPD :** les données (noms et genre de professionnels du cinéma) sont des données personnelles traitées au Canada. Le Canada bénéficie d'une décision d'adéquation de l'UE, mais le traitement doit figurer au registre.

## 7. Supervision

1. **Disque**, sur chaque VPS : créer un check healthchecks.io (période 15 min, grâce 30 min), puis `sudo ~/vps/50-monitoring.sh https://hc-ping.com/<uuid>`. Une alerte part au-delà de 80 % d'occupation.
2. **Sauvegardes** : check créé à l'étape 4.
3. **Disponibilité** : un service d'uptime externe (UptimeRobot, Better Stack, Uptime Kuma…) sur `https://cinestats5050.fr` et `https://api.cinestats5050.fr`, avec alerte sur l'expiration du certificat.

## 8. Vérification finale

**Depuis ton poste :**
```bash
nmap -Pn -p- IP_APP          # 80, 443, 22022 uniquement
nmap -Pn -p- IP_DB           # 22022 uniquement
nmap -Pn -p- IP_DATA         # 22022 uniquement (8000, 3000, 4222 filtrés)
ssh -p 22 <toi>@IP_DB                                            # doit expirer
ssh -p 22022 -o PreferredAuthentications=password <toi>@IP_DB    # « Permission denied (publickey) »
ssh -p 22022 root@IP_DB                                          # refusé
```

**Sur les VPS :**
- **Partout :** `sudo fail2ban-client status sshd`, `sudo ufw status verbose` et `sudo unattended-upgrade --dry-run --debug`.
- **`db` :** `sudo wg show` (poignée de main récente pour chaque pair) et `sudo -u postgres pgbackrest --stanza=main info` (les deux dépôts, `status: ok`).
- **`app`**, via un conteneur, qui est le vrai chemin du backend :
  ```bash
  sudo docker run --rm postgres:16-alpine psql "postgresql://app_ro:<mdp>@10.50.0.1/cinestats-5050-db?sslmode=require" \
    -c "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"       # → t
  # même commande avec -c "CREATE TABLE x (id int)" → refusé (lecture seule)
  ```
- **`data` :** un rôle de l'app (`app_ro`) doit y être refusé par `pg_hba`.
- **Site :** déploiement GitHub Actions réussi de bout en bout, `curl -I https://cinestats5050.fr` (en-têtes HSTS, etc.), note A ou mieux sur SSL Labs.
- **Bilan, optionnel :** `sudo apt install lynis && sudo lynis audit system`.

## 9. Exploitation courante

| Besoin | Commande |
|---|---|
| Ajouter un admin | relancer `00-base.sh <rôle> nouveau:/chemin/clé.pub` |
| Retirer un admin | `sudo gpasswd -d <user> ssh-users && sudo gpasswd -d <user> sudo && sudo passwd -l <user>` |
| Changer le mot de passe d'un rôle Postgres | `sudo -u postgres psql -c '\password app_ro'`, puis mettre à jour le secret GitHub et redéployer |
| Test de restauration (**mensuel**) | `sudo cinestats-pgbackrest-restore-test 2` |
| Mises à jour hors sécurité (Docker, etc.) | mensuellement : `sudo apt update && sudo apt full-upgrade` |
| Requête SQL d'admin | `ssh cinestats-db` puis `sudo -u postgres psql cinestats-5050-db` |
| Accès Postgres pour Metabase | relancer `30-postgres.sh cinestats-5050-db <ip> <wg\|public>` |

## Écarts assumés et limites

- **`airbyte_user` garde `CREATE` sur la base.** Airbyte lance `CREATE SCHEMA IF NOT EXISTS` à chaque synchro, et Postgres 16 exige ce droit même quand le schéma existe déjà (vérifié). Il n'a en revanche aucun droit sur le schéma `public` de l'app.
- **`dbt_user` accepte les connexions sans TLS**, tant que les scrapers forcent `sslmode=disable`. Le tunnel WireGuard chiffre quand même ce trafic.
- **SSH reste ouvert sur Internet** (port 22022) : les runners GitHub Actions n'ont pas d'IP fixe. Les protections sont les clés seules, fail2ban et l'environment GitHub protégé.
- **Le compte `deploy` équivaut à root sur `app`**, car il est dans le groupe `docker`. Sa clé ne vit que dans le secret GitHub.
- **Le certificat TLS de Postgres est auto-signé.** Les clients sont en `sslmode=require` (chiffrement, sans vérification d'identité), ce qui suffit à l'intérieur du tunnel WireGuard.
