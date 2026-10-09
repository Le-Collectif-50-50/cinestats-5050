# Déploiement

**Owner:** Data Team DataForGood
**Last reviewed:** 2026-10-09
**Status:** active

## Historique du document

| # | Date | Author | Observations |
| --- | --- | --- | --- |
| 1 | 2026-10-09 | Joel Teixeira | Ajout du parcours de validation en preview et clarification des branches sources de promotion. |

## Stratégie de branches

`main` est la branche de travail : les PR y sont mergées après review (1 approbation requise). `preview` et `production` sont des branches de déploiement dédiées : le script `scripts/promote.sh` les fait avancer vers `origin/main` en fast-forward par défaut. Ne pas travailler directement sur ces branches.

```
feature/xxx ──┐
              ├──► main ──┬──► preview
feature/yyy ──┘    (PR)   └──► production
```

L'ordre de validation est **preview, puis production**, mais chaque promotion prend sa source dans `main`. La preview correspond au staging. Suivre le [runbook de promotion et validation](runbooks/deploiement-promotion-preview-production.md) pour les commandes, les vérifications fonctionnelles et le contrôle du commit avant production.

## Environnements

Le projet a deux environnements, chacun sur sa propre machine, déclenchés par un push sur une branche donnée :

| Environnement | Branche | Workflow | Environment GitHub | Domaine |
|---|---|---|---|---|
| Preview | `preview` | `.github/workflows/deploy.yml` | `preview` | `preview.cinestats5050.fr` |
| Production | `production` | `.github/workflows/deploy.yml` | `production` | `cinestats5050.fr` |

Les deux peuvent aussi être déclenchés manuellement (`workflow_dispatch`) depuis leur branche ; c'est aussi par là que passe un rollback.

Pour déployer en preview : `scripts/promote.sh preview --watch`. Après validation, utiliser `scripts/promote.sh production --watch`. Ces commandes utilisent le `main` distant et refusent par défaut une divergence d'historique ; suivre le runbook avant de forcer une mise à jour.

## Flux commun

Un seul workflow, `.github/workflows/deploy.yml`, sert les deux environnements : la branche poussée choisit l'environment GitHub et ses réglages. La connexion au serveur utilise directement le client `ssh` du runner ; la construction des images utilise des actions Docker.

1. **Config** : réglages de l'environnement (fichier compose, dossier sur le serveur, URL du site).
2. **Build** : 4 images (backend, frontend, nginx, certbot) poussées sur `ghcr.io/<owner>/<repo>/<image>`. Elles sont taguées `<environnement>-<sha court>` (ex. `production-1a2b3c4`), plus `latest` en prod ou `preview`. Le tag porte l'environnement parce que l'image frontend embarque des réglages propres à chacun (URL de l'API, Umami, `robots.txt`).
3. **Deploy** :
   - **Connexion :** SSH avec la **clé d'hôte du serveur épinglée** (`SSH_KNOWN_HOSTS`, voir plus bas). Un serveur usurpé fait échouer le déploiement au lieu de recevoir les secrets.
   - **`.env` :** construit sur le runner par `scripts/render-server-env.sh`, puis envoyé par stdin en `.env.new`, créé en `600`. Les valeurs sont entre apostrophes, donc prises littéralement par compose, et les secrets n'apparaissent dans aucune ligne de commande.
   - **Fichiers :** le fichier compose, `nginx/*.conf` et `scripts/remote-deploy.sh` sont copiés d'un bloc (archive tar par SSH).
   - **`remote-deploy.sh` :** `pull`, puis `up -d --wait`, qui échoue si un service n'atteint pas l'état `healthy`. Si tout va bien, il recharge nginx, adopte `.env.new` comme `.env` et supprime les images de plus d'une semaine.
   - **Retour automatique :** si la nouvelle version ne devient pas `healthy`, le script relance celle que décrit encore `.env`. Le site reste en ligne, mais le déploiement échoue quand même pour qu'on le voie.
   - **Pas de `docker compose down` :** seuls les conteneurs modifiés sont recréés.
4. **Smoke test** depuis le runner : l'API et le site répondent, et `robots.txt` n'autorise l'indexation qu'en prod.

Le `.env` du serveur est **entièrement régénéré à chaque déploiement**, jamais édité à la main. Deux déploiements d'un même environnement ne se chevauchent jamais (`concurrency`).

### Clé d'hôte SSH (`SSH_KNOWN_HOSTS`)

C'est une **variable** de chaque environment GitHub, pas un secret : il s'agit d'une clé publique. Elle est au format `known_hosts` : `[<ip>]:<port> ssh-ed25519 AAAA…`. `infra/vps/20-docker.sh app` et `scripts/provision-preview.sh` affichent la ligne à copier.

Pour un serveur déjà en place, la lire par une connexion SSH en laquelle tu as déjà confiance :
```bash
IP=<ip>; PORT=22022
LINE="[$IP]:$PORT $(ssh -p $PORT <toi>@$IP cut -d' ' -f1,2 /etc/ssh/ssh_host_ed25519_key.pub)"
gh variable set SSH_KNOWN_HOSTS --env preview --repo Le-Collectif-50-50/cinestats-5050 --body "$LINE"
```
Si le serveur est réinstallé, sa clé change : le déploiement échoue tant que la variable n'est pas mise à jour. C'est voulu.

## Production

- Images taguées `production-<sha court>` + `latest`.
- **3 VPS OVH** durcis par `infra/vps/` (procédure complète : [`docs/runbooks/securisation-vps-prod.md`](runbooks/securisation-vps-prod.md)) :

  | VPS | Rôle | Joignable depuis Internet |
  |---|---|---|
  | `app` | nginx + frontend + backend (ce workflow) | 80, 443, SSH 22022 |
  | `db` | PostgreSQL 16 natif, sauvegardé par pgBackRest | SSH 22022, WireGuard (UDP 51820, IP des pairs seulement) |
  | `data` (Canada) | Airbyte, Prefect, dbt, scrapers | SSH 22022 |

  `app` et `data` parlent à `db` par un tunnel WireGuard (`10.50.0.0/24`, `db` = `10.50.0.1`) ; Postgres n'écoute pas sur l'IP publique.
- Déployée sous `~/cinestats5050` du compte `deploy` du VPS `app` (groupe `docker`, sans sudo).
- TLS : **DNS-01 via l'API OVH**, comme en preview (`certbot/dns-ovh`, `certbot/entrypoint-dns.sh`). Le certificat initial est émis **automatiquement** au premier déploiement, rien à faire à la main sur le serveur. Il couvre `DOMAIN`, `API_DOMAIN` et les noms de `CERT_EXTRA_DOMAINS` (les alias `www.`), puis `certbot renew` tourne toutes les 12 h. nginx ne démarre qu'une fois le certificat présent (`certbot` est `healthy`) : comptez environ 2 minutes au tout premier déploiement. Le port 80 ne sert plus qu'à rediriger vers HTTPS.
  - `CERT_EXTRA_DOMAINS` n'est lue qu'à l'émission. Pour changer la liste plus tard, supprimer `certbot/conf/live/cinestats5050.fr`, `archive/cinestats5050.fr` et `renewal/cinestats5050.fr.conf` sur le serveur, puis redéployer.
  - Il faut que les enregistrements DNS soient chez OVH (même compte que le token) : DNS-01 n'a pas besoin que le domaine pointe déjà vers le serveur.
- Le backend se connecte avec le rôle **`app_ro`, en lecture seule** (l'API n'a que des routes GET) : `DATABASE_URL=postgresql+psycopg://app_ro:***@10.50.0.1:5432/cinestats-5050-db?sslmode=require`.
- Aucune migration Alembic automatique : à jouer à la main depuis le VPS `app` avec le rôle **`app_migrator`**, seul à pouvoir modifier le schéma. Son mot de passe vient du gestionnaire de mots de passe et n'est jamais stocké sur le serveur :

  ```bash
  sudo -iu deploy
  cd ~/cinestats5050
  read -rs MIGRATOR_PW   # colle le mot de passe d'app_migrator, rien ne s'affiche
  export DATABASE_URL="postgresql+psycopg://app_migrator:$MIGRATOR_PW@10.50.0.1:5432/cinestats-5050-db?sslmode=require"
  docker compose run --rm -e DATABASE_URL backend alembic -c database/alembic.ini upgrade head
  exit                   # la session deploy et ses variables disparaissent
  ```

### Secrets (environment `production`)
`SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`, `DATABASE_URL`, `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID`, `CERTBOT_EMAIL`, `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`.

### Variables (environment `production`)
`NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`, `BACKEND_PORT`, `FRONTEND_PORT`, `SERVER_PORT` (`22022` : port SSH des VPS durcis par `infra/vps/00-base.sh`, pas le 22 par défaut), `SSH_KNOWN_HOSTS`, `DOMAIN` (`cinestats5050.fr`), `API_DOMAIN` (`api.cinestats5050.fr`), `CERT_EXTRA_DOMAINS` (`www.cinestats5050.fr www.api.cinestats5050.fr`, séparés par des espaces).

`SSH_USERNAME` vaut `deploy` et `SSH_PRIVATE_KEY` est la clé privée dédiée dont la clé publique a été passée à `infra/vps/20-docker.sh app`. L'environment `production` doit exiger un reviewer et n'autoriser que la branche `production` : un accès à ce secret équivaut à un accès root au VPS `app`.

## Preview

- Images taguées `preview-<sha court>` + `preview`.
- Déployée sous `~/cinestats5050-preview` sur une **machine dédiée**, distincte du serveur de prod.
- Base de données : **Postgres conteneurisé** dans `docker-compose.preview.yaml` (service `db`, volume `preview-db-data`), pas de dépendance à une base externe.
- **Migrations Alembic automatiques** : un service one-shot `migrate` joue `alembic -c database/alembic.ini upgrade head` avant que `backend` ne démarre (`depends_on: migrate: condition: service_completed_successfully`). C'est le but même de la preview : vérifier qu'une migration passe avant de la rejouer à la main en prod.
- **Seed automatique**, piloté par la variable `RUN_SEED` (`true`/`false`) — les 5 scripts de `database/seed/` n'étant pas garantis idempotents, mets `RUN_SEED=false` si tu vois des doublons apparaître après un merge.
- **Umami désactivé** : le build ne reçoit pas `NEXT_PUBLIC_UMAMI_WEBSITE_ID`, donc le script n'est pas injecté (voir `frontend/src/app/layout.tsx`) — les visites de test sur preview ne polluent pas les statistiques de prod.
- **Metabase réutilisé** : mêmes identifiants que la prod (même instance Metabase).
- TLS : **DNS-01 via l'API OVH** (`certbot/dns-ovh`, `certbot/entrypoint-dns.sh`). Même mécanisme qu'en prod : **le certificat initial est créé automatiquement** au premier démarrage du conteneur — rien à faire à la main sur le serveur.

### Secrets (environment `preview`)
`SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`, `DATABASE_URL` (interne, ex. `postgresql+psycopg://postgres:***@db:5432/ric_db` — le préfixe `+psycopg` est obligatoire, le projet n'a que psycopg v3 d'installé, pas psycopg2), `POSTGRES_PASSWORD`, `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID`, `CERTBOT_EMAIL`, `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY`.

### Variables (environment `preview`)
`NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`, `BACKEND_PORT`, `FRONTEND_PORT`, `SERVER_PORT` (`22022`), `SSH_KNOWN_HOSTS`, `POSTGRES_USER`, `POSTGRES_DB`, `RUN_SEED`, `DOMAIN` (`preview.cinestats5050.fr`), `API_DOMAIN` (`api.preview.cinestats5050.fr`).

Voir `docs/MIGRATION.md` pour les commandes `gh` exactes et la procédure OVH.

## Rollback

1. Dans Actions → **Deploy** → *Run workflow*, choisir la branche de l'environnement (`production` ou `preview`).
2. Renseigner `rollback_commit` : le commit à remettre, en sha court ou complet.

Rien n'est reconstruit. Le workflow redéploie les images `<environnement>-<sha>` déjà publiées, avec le compose et la config nginx de ce même commit. En ligne de commande :
```bash
gh workflow run deploy.yml --repo Le-Collectif-50-50/cinestats-5050 --ref production -f rollback_commit=1a2b3c4
```

Ce qu'il faut savoir :
- On ne peut revenir qu'à un commit déjà déployé sur cet environnement **depuis la refonte du workflow**. Les déploiements plus anciens n'ont publié que des tags `sha-<commit>`, partagés par la prod et le preview.
- Un rollback ne défait pas une migration Alembic. Si la version visée attend un schéma plus ancien, jouer d'abord `alembic downgrade` (en prod avec `app_migrator`, voir plus haut).
- Le prochain push sur la branche redéploie sa tête.

**Preview :** `docker compose down -v && docker compose up -d` sur le serveur repart en plus d'une base vide ; les migrations et le seed se rejouent automatiquement.

## Provisioning d'une nouvelle machine

- **Production** (VPS `app`, `db`, `data`) : scripts `infra/vps/`, à dérouler dans l'ordre de [`docs/runbooks/securisation-vps-prod.md`](runbooks/securisation-vps-prod.md).
- **Preview** : `scripts/provision-preview.sh` pour l'amorçage d'une VM preview vierge (Docker, arborescence, clé SSH de déploiement).
