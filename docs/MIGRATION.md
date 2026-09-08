# Migration vers `Le-Collectif-50-50/cinestats-5050`

Checklist et commandes pour finaliser la migration hors du code. **Rien ici n'est exécuté automatiquement** — copie/colle avec tes propres valeurs.

L'environment GitHub de non-prod s'appelle **`preview`** (existait déjà avant cette migration, avec des secrets/variables datant d'avril — voir §4), et le sous-domaine associé est `preview.cinestats5050.fr`. Il n'y a pas d'environment `staging` : un environment de ce nom a été créé par erreur pendant cette migration puis supprimé une fois la confusion levée.

## 1. Remote git

```bash
git remote rename origin d4g
git remote add origin git@github.com:Le-Collectif-50-50/cinestats-5050.git
git remote -v
```

## 2. Ordre de bascule

1. Créer l'environment `production` et ses secrets/variables (§3) dans le nouveau repo **avant tout push sur `main`** — sinon `deploy.yml` échoue dès la première exécution.
2. Compléter l'environment `preview` (§4) — il existe déjà, il manque encore `CERTBOT_EMAIL` et les 3 secrets OVH.
3. Pousser la branche de migration, la merger dans `develop` → le déploiement preview se déclenche. Vérifier de bout en bout (voir `docs/DEPLOYMENT.md`).
4. Merger `develop` → `main` → les images `latest` sont publiées dans le nouveau namespace, puis le serveur de prod les tire.
5. Rendre les 4 packages GHCR visibles/liés au repo si besoin (`Settings` du package → `Manage Actions access` → lier à `Le-Collectif-50-50/cinestats-5050`).
6. Réactiver Dependabot et Copilot Autofix dans les réglages de sécurité du nouveau repo (ce n'était pas versionné, donc rien ne suit automatiquement).
7. Archiver ou documenter l'état de `dataforgoodfr/13_reveler_inegalites_cinema`.

## 3. Environment `production` — secrets et variables

N'existe pas encore sur le nouveau repo (à créer en premier, avant tout push sur `main`).

```bash
REPO="Le-Collectif-50-50/cinestats-5050"

gh api repos/$REPO/environments/production -X PUT --input - <<< '{}'

gh secret set SERVER_HOST         --env production --repo $REPO --body "<ip-vps-prod>"
gh secret set SSH_USERNAME        --env production --repo $REPO --body "<user ssh existant>"
gh secret set SSH_PRIVATE_KEY     --env production --repo $REPO --body "$(cat ~/.ssh/<clé-déploiement-prod>)"
gh secret set DATABASE_URL        --env production --repo $REPO --body "postgresql+psycopg://<user>:<pass>@<host>:5432/<db>"
gh secret set METABASE_SITE_URL   --env production --repo $REPO --body "<url>"
gh secret set METABASE_SECRET_KEY --env production --repo $REPO --body "<clé>"
gh secret set METABASE_DASHBOARD_ID --env production --repo $REPO --body "<id>"

gh variable set NEXT_PUBLIC_API_URL --env production --repo $REPO --body "https://api.cinestats5050.fr"
gh variable set ALLOWED_ORIGINS     --env production --repo $REPO --body "https://cinestats5050.fr,https://www.cinestats5050.fr"
gh variable set BACKEND_PORT        --env production --repo $REPO --body "5001"
gh variable set FRONTEND_PORT       --env production --repo $REPO --body "3000"
```

## 4. Environment `preview` — état actuel

✅ **Complet** : les 12 secrets et 9 variables attendus par `deploy-preview.yml` sont posés.

| Clé | Valeur |
|---|---|
| `SERVER_HOST`, `SSH_USERNAME`, `SSH_PRIVATE_KEY` | clé de déploiement dédiée à la VM preview |
| `POSTGRES_USER` (var) | `postgres` |
| `POSTGRES_DB` (var) | `ric_db` |
| `POSTGRES_PASSWORD` (secret) | généré aléatoirement |
| `DATABASE_URL` (secret) | `postgresql+psycopg://postgres:***@db:5432/ric_db` — pointe sur le Postgres conteneurisé de `docker-compose.preview.yaml`, remplace l'ancienne valeur d'avril |
| `NEXT_PUBLIC_API_URL` (var) | `https://api.preview.cinestats5050.fr` |
| `ALLOWED_ORIGINS` (var) | `https://preview.cinestats5050.fr,https://www.preview.cinestats5050.fr` |
| `DOMAIN`, `API_DOMAIN` (var) | `preview.cinestats5050.fr` / `api.preview.cinestats5050.fr` |
| `RUN_SEED` (var) | `true` |
| `BACKEND_PORT`, `FRONTEND_PORT` (var) | `5001` / `3000` — déjà présents depuis avril, inchangés |
| `METABASE_SITE_URL`, `METABASE_SECRET_KEY`, `METABASE_DASHBOARD_ID` | déjà présents depuis avril, réutilisés tel quel |
| `CERTBOT_EMAIL` | posé |
| `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` | posés |

Reste hors GitHub : DNS `preview.cinestats5050.fr` / `api.preview.cinestats5050.fr` pointés vers la VM (voir §6), et la VM elle-même provisionnée avec `scripts/provision-preview.sh`.

`DATABASE_URL` utilise le préfixe `postgresql+psycopg://` (et non `postgresql://`) : le projet n'a que `psycopg` v3 d'installé (`poetry.lock`), pas `psycopg2` — SQLAlchemy cherche `psycopg2` par défaut avec le préfixe nu et le service `migrate` planterait au démarrage. `postgres` / `ric_db` reprennent la convention déjà utilisée dans `docker-compose.yaml` (dev) et `.env` local.

## 5. Credentials OVH pour le DNS-01

1. Aller sur https://eu.api.ovh.com/createToken/ (adapter le TLD `.ca`/`.us` selon la zone OVH réelle du domaine).
2. Renseigner :
   - **Application name** : `cinestats5050-preview-certbot`
   - **Rights** : `GET`, `POST`, `DELETE` sur le chemin `/domain/zone/*`
   - **Validity** : illimitée (le token est utilisé en continu par le renouvellement automatique)
3. Récupérer les 3 valeurs retournées : `Application Key`, `Application Secret`, `Consumer Key` — ce sont respectivement `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` du §4.
4. ⚠️ Ces clés donnent le droit d'écrire dans la zone DNS du domaine — à traiter comme un secret sensible, jamais commité.

## 6. DNS et machine preview

- Créer les enregistrements DNS chez OVH : `preview.cinestats5050.fr` et `api.preview.cinestats5050.fr` → A/AAAA vers l'IP de la VM preview.
- Provisionner la VM avec `scripts/provision-preview.sh` (Docker, arborescence `~/cinestats5050-preview`, clé SSH de déploiement autorisée).
- Aucune création manuelle de certificat n'est nécessaire : `certbot/entrypoint-dns.sh` l'émet automatiquement au premier démarrage du conteneur `certbot`.
