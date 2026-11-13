# Runbook — Stack data (VPS data)

**Owner:** Nicolas Revel

**Dernière révision:** 2026-11-13

**Status:** active

## Historique du document

| # | Date | Auteur | Observations |
|---|---|---|---|
| 1 | 2026-10-06 | Nicolas Revel | Première version du runbook | 
| 2 | 2026-10-09 | Joel Teixeira | Précision du déploiement depuis main et conservation des fichiers générés et des credentials lors des mises à jour. |
| 3 | 2026-10-11 | Joel Teixeira | Restauration de SELECT pour scraper_user et persistance de la lecture après recréation des tables Airbyte. Configuration requise pour Airbyte activé par défaut et migration du fichier .env existant. |
| 4 | 2026-11-13 | Joel Teixeira | Dépendance libatomic1 persistante dans l'image Prefect et contrôle du démarrage du pilote Playwright au build. Déploiement Allociné manuel et retrait des indications de scraping Mubi planifié. Quatre déploiements au démarrage, ingestion sans scraping et limites manuelles des scrapers. Diagnostic des timeouts casting Allociné (issue 50), isolation du navigateur et procédure de reprise. |

Déploiement de la stack d'ingestion (Prefect, dbt, scrapers, Airbyte) sur le VPS `data` (Canada, 4 vCPU / 8 Go). Le [runbook de setup ingestion](ingestion-runbook-infra-setup-dbt-core-airbyte-remote-postgres.md) décrit le parcours général ; celui-ci consigne les adaptations du VPS. Pour une livraison des changements fusionnés, utiliser explicitement `origin/main` comme indiqué ci-dessous.

Prérequis : `00-base.sh`, `10-wireguard.sh spoke` et `20-docker.sh data` faits sur le VPS (voir `securisation-vps-prod.md`), ainsi que `30-postgres.sh` sur `db`.

## 1. Côté base (VPS `db`) — fait

- `roles.sql` (rejoué par `30-postgres.sh`) crée déjà les schémas `raw`, `staging`, `intermediate`, `fnl`, `ops`, leurs propriétaires et les droits de `airbyte_user`, `dbt_user`, `scraper_user` et `prefect_user`. C'est l'équivalent du §4.3 du runbook de la branche.
- La table `ops.ingestion_run_requests` n'est pas dans `roles.sql` : elle se crée en `dbt_user` (pour que les droits par défaut des rôles Metabase s'appliquent), puis `roles.sql` se rejoue pour donner ses droits à `prefect_user` :

  ```bash
  sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d cinestats-5050-db < ops-ingestion-table.sql   # infra/data/ops-ingestion-table.sql, copié sur db
  sudo -u postgres psql -X -q -d cinestats-5050-db -v db_name=cinestats-5050-db < ~/vps/sql/roles.sql
  ```

### Maintenir la lecture des scrapers après un sync Airbyte

Sur `cinestats-db`, appliquer les droits dans la base production :

```bash
sudo -u postgres psql -X -v ON_ERROR_STOP=1 -d cinestats-5050-db <<'SQL'
GRANT SELECT ON TABLE raw.id_matching TO scraper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE airbyte_user IN SCHEMA raw
  GRANT SELECT ON TABLES TO scraper_user;
SELECT has_schema_privilege('scraper_user', 'raw', 'USAGE') AS raw_usage,
       has_table_privilege('scraper_user', 'raw.id_matching', 'SELECT') AS id_matching_select;
SQL
```

Les deux contrôles doivent renvoyer `true`. Le premier `GRANT` restaure la table actuelle ; les privilèges par défaut couvrent toutes les futures tables créées par `airbyte_user` dans `raw`, sans droits d'écriture. Ils ne modifient pas les autres tables existantes et ne s'appliquent pas aux tables créées par un autre rôle. Le `DROP` puis `CREATE` effectué par Airbyte ne supprime ainsi plus la lecture des scrapers.

Le provisionnement crée `scraper_user` dans `infra/vps/30-postgres.sh`. `infra/vps/sql/roles.sql` accorde aussi `USAGE`/`CREATE` sur `raw`, configure les privilèges par défaut et restaure `SELECT` sur `raw.id_matching` si la table existe. Copier la version actualisée de ce SQL sur le VPS avant de rejouer uniquement les droits ; ne pas relancer le provisionnement complet pour cette correction.

## 2. Copier la stack sur le VPS

Depuis ton poste, à la racine du dépôt :

```bash
git fetch origin
infra/data/deploy-ingestion.sh            # ou : infra/data/deploy-ingestion.sh <ref-git>
```

Pour livrer les changements fusionnés dans `main`, passer explicitement cette référence :

```bash
git fetch origin main
infra/data/deploy-ingestion.sh origin/main
```

La copie conserve aussi `__pycache__/`, `dbt/target/`, `dbt/logs/` et `airbyte/json_credentials/`. Les fichiers générés par Docker peuvent appartenir à root : leur exclusion évite les erreurs de suppression rsync et préserve les credentials Google. Le script copie le code ; reconstruire ensuite l'image et recréer les services concernés selon la section 4. Pour un worker déjà actif, attendre la fin des runs en cours avant son arrêt et son remplacement.

Le script copie `ingestion/` d'un commit précis (par défaut `origin/analytics/dbt_airbyte_setup`) dans `~/cinestats-data/` et y ajoute `infra/data/docker-compose.override.yml`. Il note le commit dans `~/cinestats-data/DEPLOYED_REF`. Il ne démarre rien et n'écrase jamais le `.env`.

À la première copie, il crée `~/cinestats-data/ingestion/.env` (`600`) depuis `infra/data/.env.example` et **génère `PREFECT_AUTH_STRING` sur le serveur**. Il reste à saisir à la main, dans ce fichier, deux mots de passe pris dans `/root/cinestats-secrets.txt` (VPS `db`) : `DBT_USER_POSTGRES_PASSWORD` et `INGESTION_REQUEST_POSTGRES_PASSWORD` (celui de `prefect_user`).

## 3. Écarts avec la branche analytics

| Sujet | Branche | Ici |
|---|---|---|
| Ports | Prefect publié sur toutes les interfaces, Browserless aussi | Prefect en `127.0.0.1:4222` seulement ; Browserless non publié (le worker l'atteint par le réseau de compose) |
| Base de Prefect | Postgres dédié (`PREFECT_API_DATABASE_CONNECTION_URL`) | SQLite locale dans le volume `prefect-data` : `prefect_user` ne peut pas créer de base sur le Postgres de prod |
| Browserless | 4 CPU / 4 Go, 4 sessions | 1,5 CPU / 2 Go, 2 sessions (le VPS doit aussi porter Airbyte) |
| Compose racine | modifié (`docker-compose*.yaml`) | non repris : la branche y revient à un compte Docker Hub en dur et supprime `INTERNAL_API_URL` |

Surcharge dans `infra/data/docker-compose.override.yml` (fusion vérifiée avec `docker compose config`).

## 4. Construire et démarrer

Sur le VPS, dans `~/cinestats-data/ingestion/` (l'utilisateur admin passe par `sudo docker`) :

```bash
sudo docker compose build prefect-server         # image ric-prefect, partagée avec le worker
sudo docker compose up -d prefect-server         # serveur seul, aucun flux planifié
```

Au démarrage, `ingestion/prefect/start_worker.sh` publie :

- `lancer-ingestion-complete` : Airbyte puis les deux phases dbt, sans scraping ;
- `lancer-scrapping-allocine` : manuel, aucun calendrier, `max_films=10`, concurrence 1 ;
- `lancer-scrapping-mubi` : Mubi CNC manuel, aucun calendrier, `max_films=10` films source et leurs éditions associées, concurrence 1 ;
- `traiter-les-demandes-ingestion` : poller toutes les 5 minutes par défaut, qui peut déclencher l’ingestion complète selon les demandes en base.

Aucun scraping Mubi n’est planifié par ce script. Pour publier les changements, attendre la fin des runs actifs, puis recréer le worker. Le [guide ingestion](../../ingestion/README.md#publier-et-lancer-le-scraping-seul) donne les commandes de contrôle et de lancement Allociné. Utiliser `sudo docker` sur le VPS.

### Dépannage du pilote Playwright

L'erreur `libatomic.so.1: cannot open shared object file` interrompt le scraping
avant tout accès au site. Le Dockerfile Prefect installe `libatomic1` et vérifie
le démarrage du pilote Playwright pendant le build. Une installation manuelle
dans un conteneur disparaît à sa recréation.

Après copie du Dockerfile corrigé, reconstruire l'image avec
`sudo docker compose build prefect-worker`, puis attendre la fin des runs actifs
avant `sudo docker compose up -d --no-deps --force-recreate prefect-worker`.
Vérifier le pilote dans le nouveau worker :

```bash
sudo docker compose exec -T prefect-worker python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.stop(); print("Playwright OK")'
```

Ce contrôle ne scrape aucun film et ne valide pas une ingestion complète.

## 5. Accéder à l'interface

Prefect n'est joignable que par tunnel SSH (`AllowTcpForwarding local` sur ce VPS) :

```bash
ssh -L 4222:localhost:4222 cinestats-data      # puis http://localhost:4222
```

Identifiants : la valeur de `PREFECT_AUTH_STRING` du `.env` du serveur (`utilisateur:mot_de_passe`). L'API refuse tout accès sans eux (401) ; `/api/health` et l'interface statique sont publics, sans données.

## 6. Accès web à Airbyte (SSO Authentik)

Airbyte OSS n'a qu'un mot de passe, sans SSO : il n'est jamais exposé directement. Il est publié sur `https://airbyte.cinestats5050.fr`, derrière Authentik, par ce montage :

```
navigateur → Caddy (VPS data, 80/443, Let's Encrypt) → outpost Authentik (127.0.0.1:9000) → Airbyte (127.0.0.1:8000)
                                                          └─ vérification auprès de auth.cinestats5050.fr
```

Seuls Caddy (80 et 443) et SSH sont joignables depuis Internet : 8000 (Airbyte), 4222 (Prefect) et 9000/9443 (outpost) restent filtrés (vérifié). Airbyte garde son propre mot de passe : deux couches. Le worker Prefect, sur la même machine, appelle l'API d'Airbyte en local et n'est pas concerné par le SSO.

- **Côté Authentik** : blueprint `authentik/blueprints/airbyte.yaml` du dépôt `cinestats-infra` (groupe **Airbyte Admins**, proxy provider, application, outpost distant `airbyte-outpost`). Les personnes autorisées s'ajoutent au groupe dans Authentik (*Directory → Groups*).
- **DNS** : `airbyte.cinestats5050.fr` en A vers l'IP du VPS data, avant de lancer Caddy.
- **Caddy** : `sudo ~/vps/60-caddy.sh airbyte.cinestats5050.fr 9000` (paquet officiel, empreinte SHA-512 vérifiée, ufw 80/443).
- **Outpost** : `infra/data/authentik-outpost/docker-compose.yml`, copié dans `~/cinestats-data/authentik-outpost/`. Son `.env` porte `AUTHENTIK_TOKEN`, à copier depuis Authentik (*Applications → Outposts → airbyte-outpost → View Deployment Info*) et à écrire sur le serveur avec `read -rs`, jamais dans git. Puis `sudo docker compose up -d`.
- **Vérification sans connexion** : `curl -I https://airbyte.cinestats5050.fr/` doit répondre `302` vers `/outpost.goauthentik.io/start`, et il en va de même pour `/api/v1/health`. Suivre les redirections doit arriver sur `auth.cinestats5050.fr`.
- **Accès de secours** : le tunnel SSH reste possible (`ssh -L 8000:localhost:8000 cinestats-data`) et ne passe pas par le SSO.

## 7. Reste à faire

- Airbyte est installé (`abctl` 0.30.4, mode économe : environ 3,3 Go de RAM au repos, il reste environ 3,4 Go pour le worker et Chrome). Reste à le configurer : voir ci-dessous.
- Compte de service Google (Sheets en lecture seule) et URL des 12 feuilles pour `airbyte/bootstrap.py`.
- Corrections côté code de la branche : `sslmode` configurable dans les scrapers (aujourd'hui `disable` en dur), rôle dédié aux scrapers.
- Surveiller les timeouts Allociné après correction de l’issue 50 (voir le [diagnostic ci-dessous](#incident-50--timeouts-casting-allociné)).

## 8. Configurer la phase Airbyte

La phase Airbyte du pipeline complet est activée par défaut dans le code. Le déploiement conserve le `.env` existant : les anciennes valeurs `false` doivent donc être modifiées manuellement pour le poller.

Avant de lancer une ingestion complète sur le VPS :

1. Renseigner `AIRBYTE_CLIENT_ID` et `AIRBYTE_CLIENT_SECRET` dans `~/cinestats-data/ingestion/.env`.
2. Créer ou vérifier les connexions Google Sheets vers Postgres dans Airbyte. Pour utiliser le bootstrap, déposer le compte de service Google dans `airbyte/json_credentials/` et renseigner `AIRBYTE_DESTINATION_POSTGRES_PASSWORD`.
3. Renseigner `INGESTION_REQUEST_AIRBYTE_CONNECTION_NAMES` avec les noms exacts des connexions, séparés par des virgules. Exemple pour une connexion créée par le bootstrap : `src_gsheet_films -> dst_pg_raw`. Les runs manuels et le CLI réutilisent cette liste lorsqu’aucun nom n’est fourni explicitement.
4. Passer `INGESTION_REQUEST_RUN_AIRBYTE_SYNC_STEP=true` pour les demandes Metabase. Cette variable contrôle le poller ; le paramètre `run_airbyte_sync_step` contrôle les runs manuels.
5. Après livraison du code, recréer le worker pour charger le `.env` et republier les paramètres du deployment, en attendant la fin des runs en cours : `sudo docker compose up -d --force-recreate prefect-worker`.
6. Vérifier dans Prefect que `lancer-ingestion-complete` utilise `run_airbyte_sync_step=true`. Retirer toute ancienne surcharge `false` avant de lancer le run.

Sans noms de connexions ou credentials valides, la phase Airbyte échoue avant dbt. Pour exécuter temporairement sans sync, utiliser `run_airbyte_sync_step=false` dans Prefect ou `--no-run-airbyte-sync` en CLI ; pour le poller, utiliser `INGESTION_REQUEST_RUN_AIRBYTE_SYNC_STEP=false`.

### Migration des déploiements ingestion et scraping

Le worker recrée ses quatre déploiements gérés à chaque démarrage et supprime les
anciens noms. Attendre la fin des runs avant sa recréation. Seul le poller garde
un calendrier ; les deux scrapers restent manuels et acceptent `max_films`, entier
strictement positif (10 par défaut). Le poller traduit automatiquement l’ancienne
valeur `Lancer l'ingestion complete/lancer-ingestion-donnees` du `.env` vers
`Lancer l'ingestion complete/lancer-ingestion-complete`. Les configs Allociné ne
sont plus transmises au flow d’ingestion. Le serveur Prefect et Browserless n’ont
pas besoin d’être recréés pour ce changement de code.


### Incident 50 — timeouts casting Allociné

Le 13 novembre 2026, les quatre visas `111392`, `144996`, `152608` et
`154529` échouaient sur `/casting/`. Le code effectif du connecteur et sa
configuration correspondaient au commit `0217635` (empreintes vérifiées),
avec Playwright 1.65.0, Browserless 1.61.1 et Chrome 121.0.6167.85.
Le fichier `DEPLOYED_REF` indiquait aussi `0217635`, mais des fichiers avaient
été livrés séparément : les flows et le parseur correspondaient déjà au `main`
`3939d9a`. Ce marqueur seul ne décrit donc pas tout l’arbre exécuté.
L’image Browserless observée était
`sha256:57d19e414d9fe4ae9d2ab12ba768c97f38d51246c5b31af55a009205c136012f`.
Réglages : 60 s par navigation, 240 s par tentative, deux tentatives,
une session parallèle, 1,5 CPU et 2 Gio pour Browserless.

La reproduction séquentielle sans écriture a produit huit timeouts casting
et quatre résultats `error` en 861,68 s. Les fiches principales répondaient
HTTP 200. Pendant les transitions vers le casting, les requêtes publicitaires
et vidéo continuaient (notamment `sync.drift-pixel.ai`, `ap.lijit.com` et
`static1.dmcdn.net`). Browserless atteignait environ 150 % CPU, 1,90 Gio et
893 tâches ; le compteur de throttling CPU augmentait. Aucun OOM kill ni
atteinte de la limite PID n’a été observé. Les fermetures/reconnexions
expliquaient aussi une partie du temps hors des budgets de navigation.

Sur Chromium local, les mêmes quatre couples fiche/casting étaient accessibles
sans timeout en 230,70 s. Le correctif local les lisait en 206,45 s ; dates et
réalisateurs identiques. Une comparaison complète des champs de *Matin calme*
avant/après n’a trouvé aucune différence, y compris les crédits et l’affiche.
Les quatre fiches utilisent actuellement un `span.date.blue-link` pour la date ;
le sélecteur commun accepte aussi `a.date.blue-link`, couvert par les tests.
Ces essais de transport utilisaient des entrées en mémoire sans référence CNC
ni validation manuelle : leurs statuts d’identité ne mesurent pas la couverture
métier. Le test serveur du candidat utilise les références CNC et la validation
manuelle déjà présentes en production.

Le correctif allège les ressources, ferme la page précédente avant navigation,
isole chaque film dans une session et borne ouverture/fermeture. Si la page
ne se ferme pas sous 5 s, la session entière est remplacée avant la navigation
suivante, dans le budget du film. Les deux
tentatives maximales et les délais 60/240 s restent inchangés. Une panne d’un
candidat de recherche reste technique (`error` ou `blocked`) et n’est plus
masquée par `needs_review`. Le mécanisme observé est une saturation pendant
la réutilisation des pages chargées de publicités ; le diagnostic n’isole pas
un défaut interne précis de cette ancienne version de Chrome.

Avant une reprise, attendre la fin des runs métier, relever `DEPLOYED_REF`,
les empreintes des fichiers et les versions effectives. Tester le candidat
isolé sur le même Browserless sans écrire en base. Livrer ensuite le code
validé, avec sauvegarde des fichiers remplacés. Le worker lance le scraper
dans un nouveau processus à chaque run : une modification des seuls fichiers
Python/configuration du scraper montés sous `/app` est relue sans redémarrer
les services. Une modification d’image, de `.env` ou de flows exige toujours
la procédure de reconstruction/recréation ci-dessus.

Pour des visas avec un ancien succès incomplet, suivre la
[reprise ciblée](../../ingestion/scraping/allocine/README.md#rejouer-des-visas-après-un-incident-technique),
puis publier avec `main-ingestion --no-run-airbyte-sync` lorsque les sources
`raw` sont déjà synchronisées. Contrôler les dates et crédits dans `fnl` après
la réussite dbt. Les requêtes initiales ont confirmé que les anciens succès de
Matin calme et L’Abbé Pierre n’avaient déjà aucune date, et celui de Rivière
rouge aucun réalisateur : le dernier timeout n’avait pas effacé ces valeurs.
Bamako avait un ancien `visa_mismatch`, avec `VALIDATION_MANUELLE=TRUE` dans
`raw.id_matching` ; cette validation existante doit être respectée.


La validation du correctif sur le même Browserless, sans changement de quotas
ni de délais de navigation, a réussi les quatre films en **306,50 s** : quatre
tentatives, aucun timeout de navigation et un remplacement de session après
fermeture bloquée sur L’Abbé Pierre. Les résultats sont comparés aux huit
tentatives et quatre erreurs du lot initial (861,68 s). Ce petit lot valide
la reprise de l’incident ; il ne mesure pas tout le catalogue.

Le code du commit `2440596` a été livré le 13 novembre 2026 à 19 h 40 (Paris),
avec sauvegarde sous `~/cinestats-data/backups/issue-50-2440596ba52f4cf8f2e5c5da2796b6f1c52f2dc7/`.
`~/cinestats-data/HOTFIX_50_REF` suit le commit et les empreintes du correctif
ciblé ; `DEPLOYED_REF` reste le marqueur de la copie globale antérieure.
Le `.env`, les images et les quotas n’ont pas été modifiés. Pour revenir en
arrière, attendre la fin des runs et restaurer les fichiers sauvegardés ; les
collectes déjà ajoutées restent historisées et ne sont pas supprimées.
