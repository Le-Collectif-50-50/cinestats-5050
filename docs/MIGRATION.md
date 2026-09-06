# Migration vers `Le-Collectif-50-50/cinestats-5050`

Checklist et commandes pour finaliser la migration hors du code. **Rien ici n'est exécuté automatiquement** — copie/colle avec tes propres valeurs.

## 1. Remote git

```bash
git remote rename origin d4g
git remote add origin git@github.com:Le-Collectif-50-50/cinestats-5050.git
git remote -v
```

## 2. Ordre de bascule

1. Créer l'environment `production` et ses secrets/variables (§3) dans le nouveau repo **avant tout push sur `main`** — sinon `deploy.yml` échoue dès la première exécution.
2. Créer l'environment `staging` et ses secrets/variables (§4).
3. Pousser la branche de migration, la merger dans `develop` → le déploiement staging se déclenche. Vérifier de bout en bout (voir la section Vérification du plan / `docs/DEPLOYMENT.md`).
4. Merger `develop` → `main` → les images `latest` sont publiées dans le nouveau namespace, puis le serveur de prod les tire.
5. Rendre les 4 packages GHCR visibles/liés au repo si besoin (`Settings` du package → `Manage Actions access` → lier à `Le-Collectif-50-50/cinestats-5050`).
6. Réactiver Dependabot et Copilot Autofix dans les réglages de sécurité du nouveau repo (ce n'était pas versionné, donc rien ne suit automatiquement).
7. Archiver ou documenter l'état de `dataforgoodfr/13_reveler_inegalites_cinema`.

## 3. Environment `production` — secrets et variables

```bash
REPO="Le-Collectif-50-50/cinestats-5050"

gh api repos/$REPO/environments/production -X PUT --input - <<< '{}'

gh secret set SERVER_HOST         --env production --repo $REPO
gh secret set SSH_USERNAME        --env production --repo $REPO
gh secret set SSH_PRIVATE_KEY     --env production --repo $REPO
gh secret set DATABASE_URL        --env production --repo $REPO
gh secret set METABASE_SITE_URL   --env production --repo $REPO
gh secret set METABASE_SECRET_KEY --env production --repo $REPO
gh secret set METABASE_DASHBOARD_ID --env production --repo $REPO

gh variable set NEXT_PUBLIC_API_URL --env production --repo $REPO --body "https://api.cinestats5050.fr"
gh variable set ALLOWED_ORIGINS     --env production --repo $REPO --body "https://cinestats5050.fr,https://www.cinestats5050.fr"
gh variable set BACKEND_PORT        --env production --repo $REPO --body "5001"
gh variable set FRONTEND_PORT       --env production --repo $REPO --body "3000"
```

## 4. Environment `staging` — secrets et variables

Nécessite d'abord la machine staging provisionnée (§6) et les credentials OVH (§5).

```bash
REPO="Le-Collectif-50-50/cinestats-5050"

gh api repos/$REPO/environments/staging -X PUT --input - <<< '{}'

gh secret set SERVER_HOST           --env staging --repo $REPO   # IP/host de la VM staging
gh secret set SSH_USERNAME          --env staging --repo $REPO
gh secret set SSH_PRIVATE_KEY       --env staging --repo $REPO
gh secret set DATABASE_URL          --env staging --repo $REPO   # ex. postgresql://ric:***@db:5432/ric
gh secret set POSTGRES_PASSWORD     --env staging --repo $REPO
gh secret set METABASE_SITE_URL     --env staging --repo $REPO   # peut être identique à prod
gh secret set METABASE_SECRET_KEY   --env staging --repo $REPO
gh secret set METABASE_DASHBOARD_ID --env staging --repo $REPO
gh secret set CERTBOT_EMAIL         --env staging --repo $REPO
gh secret set OVH_APPLICATION_KEY   --env staging --repo $REPO
gh secret set OVH_APPLICATION_SECRET --env staging --repo $REPO
gh secret set OVH_CONSUMER_KEY      --env staging --repo $REPO

gh variable set NEXT_PUBLIC_API_URL --env staging --repo $REPO --body "https://api.staging.cinestats5050.fr"
gh variable set ALLOWED_ORIGINS     --env staging --repo $REPO --body "https://staging.cinestats5050.fr"
gh variable set BACKEND_PORT        --env staging --repo $REPO --body "5001"
gh variable set FRONTEND_PORT       --env staging --repo $REPO --body "3000"
gh variable set POSTGRES_USER       --env staging --repo $REPO --body "ric"
gh variable set POSTGRES_DB         --env staging --repo $REPO --body "ric"
gh variable set RUN_SEED            --env staging --repo $REPO --body "true"
gh variable set DOMAIN              --env staging --repo $REPO --body "staging.cinestats5050.fr"
gh variable set API_DOMAIN          --env staging --repo $REPO --body "api.staging.cinestats5050.fr"
```

## 5. Credentials OVH pour le DNS-01

1. Aller sur https://eu.api.ovh.com/createToken/ (adapter le TLD `.ca`/`.us` selon la zone OVH réelle du domaine).
2. Renseigner :
   - **Application name** : `cinestats5050-staging-certbot`
   - **Rights** : `GET`, `POST`, `DELETE` sur le chemin `/domain/zone/*`
   - **Validity** : illimitée (le token est utilisé en continu par le renouvellement automatique)
3. Récupérer les 3 valeurs retournées : `Application Key`, `Application Secret`, `Consumer Key` — ce sont respectivement `OVH_APPLICATION_KEY`, `OVH_APPLICATION_SECRET`, `OVH_CONSUMER_KEY` du §4.
4. ⚠️ Ces clés donnent le droit d'écrire dans la zone DNS du domaine — à traiter comme un secret sensible, jamais commité.

## 6. DNS et machine staging

- Créer les enregistrements DNS chez OVH : `staging.cinestats5050.fr` et `api.staging.cinestats5050.fr` → A/AAAA vers l'IP de la VM staging.
- Provisionner la VM avec `scripts/provision-staging.sh` (Docker, arborescence `~/cinestats5050-staging`, clé SSH de déploiement autorisée).
- Aucune création manuelle de certificat n'est nécessaire : `certbot/entrypoint-dns.sh` l'émet automatiquement au premier démarrage du conteneur `certbot`.
