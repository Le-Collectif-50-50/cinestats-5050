# Rechercher les identifiants MUBI et TMDB manquants

**Owner:** Joel Teixeira  
**Dernière révision:** 2026-11-16  
**Status:** actif — CLI et intégration Prefect ; installation requise sur la base cible

Ce script lit `raw.id_matching` et recherche uniquement les `ID_MUBI` et
`ID_TMDB` vides. Le réalisateur de référence provient de `raw.films.REALISATEUR`,
rapproché par `VISA`. Les contrôles de navigation et d'identité sont adaptés de
l'outil local `visa_matching_local` ; leur fonctionnement ne dépend pas de ce
dossier local exclu de Git. Aucun traitement IMDb n'est effectué.

## Deux tables PostgreSQL pour les résultats

| Table | Contenu |
| --- | --- |
| `ops.id_matching_confirmed` | Un seul candidat concordant, titre et réalisateur vérifiés sur sa fiche détaillée ; `proposed_id` contient l'identifiant numérique. |
| `ops.id_matching_review` | Preuves insuffisantes, ambiguïtés, recherche sans résultat, blocages et erreurs ; aucun identifiant attribué. Les candidats figurent dans `evidence`. |

Chaque tentative conserve `run_id`, visa, fournisseur, statut, titre source,
raison, date UTC et preuves JSONB : référence CNC, candidats, titres, réalisateurs,
années disponibles et URL. Une nouvelle exécution ajoute un historique ; elle ne
remplace pas les précédentes conclusions. Pour consulter l'état courant, prendre
la dernière tentative par `(visa, provider)` dans **l'union des deux tables**.
Une ancienne confirmation peut être suivie d'une nouvelle tentative en revue.

Ces tables stockent des propositions. Le script ne modifie ni Google Sheets,
ni `raw.id_matching`, ni les modèles dbt. L'intégration dans la source canonique
reste manuelle ; aucune interface de décision ou publication automatique n'est
incluse. Il ne produit aucun fichier CSV ni dump de résultats.

## Préparer et lancer

Python 3.11 minimum et Chromium Playwright sont nécessaires. Depuis la racine :

```bash
python -m pip install -r ingestion/scraping/id_matching/requirements.txt
python -m playwright install chromium --only-shell
```

Le script charge `ingestion/.env` sans remplacer les variables déjà exportées.
Il utilise `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
`SCRAPER_POSTGRES_USER`, `SCRAPER_POSTGRES_PASSWORD` et `POSTGRES_SSLMODE`
(`require` par défaut). `ID_MATCHING_DATABASE_URL` permet de choisir explicitement
une autre connexion SQLAlchemy PostgreSQL avec le pilote `postgresql+psycopg`.
Les identifiants ne sont jamais passés dans les arguments CLI.

Vérifier la base cible avant toute création de tables. Faire appliquer
[`schema.sql`](schema.sql) par un administrateur sur la base ingestion. Ce fichier
crée les deux tables et accorde `USAGE`, `SELECT`, `INSERT` à `scraper_user`,
ainsi que leur lecture à `metabase_ops_user` ;
adapter ce nom si nécessaire. Le compte du script doit aussi avoir `SELECT` sur
`raw.id_matching` et `raw.films`. Aucun DDL automatique n'est exécuté par le CLI.

```bash
# Lecture des volumes, sans navigateur et sans écriture
python -m ingestion.scraping.id_matching --inspect

# Recherche réelle, résultats stdout uniquement
python -m ingestion.scraping.id_matching --visa 149572 --dry-run

# Recherche puis insertion dans ops, jusqu'à 10 visas
python -m ingestion.scraping.id_matching --limit 10

# Un seul catalogue
python -m ingestion.scraping.id_matching --provider tmdb --limit 5
```

Sans `PLAYWRIGHT_WS_ENDPOINT`, Chromium s'exécute localement ; sinon, le script
utilise le navigateur distant configuré. `--headed` exige Chromium complet.
Les résultats sont aussi affichés en JSONL sur stdout ; volumes et `run_id`
figurent sur stderr. Le code de sortie vaut 1 en cas de blocage, erreur technique
ou écriture impossible. Les résultats déjà insérés restent conservés. Il n'y a
pas de reprise automatique : une relance effectue de nouvelles tentatives,
tant que les identifiants restent vides dans la source.

## Exécuter avec Prefect

Le flow `Rechercher les identifiants MUBI et TMDB` est publié par
`ingestion/prefect/start_worker.sh` sous le nom
`rechercher-identifiants-manquants`. Son déploiement est manuel, sans calendrier,
sans lancement au démarrage et avec une concurrence limitée à un run.
Les dépendances Python sont déjà incluses dans l'image du worker ; il utilise
Browserless via `PLAYWRIGHT_WS_ENDPOINT`.

Ordre de mise en service :

1. Vérifier la base cible, appliquer `schema.sql` et contrôler les droits du compte scraper.
2. Synchroniser les sources Airbyte si nécessaire pour actualiser `raw.id_matching`
   et `raw.films`. Le flow de matching ne déclenche aucune synchronisation.
3. Livrer le code puis republier les déploiements, selon le [guide ingestion](../../README.md#publier-et-lancer-les-scrapers).
   La procédure de redémarrage du worker exige d'attendre la fin des runs actifs.
4. Lancer un petit lot en `dry_run`, puis inspecter ses preuves dans les logs.
5. Relancer sans `dry_run` pour enregistrer les propositions dans `ops`.

Depuis `ingestion/`, après publication du déploiement :

```bash
docker compose exec -T prefect-worker prefect deployment run \
  "Rechercher les identifiants MUBI et TMDB/rechercher-identifiants-manquants" \
  --param max_films=3 --param provider=all --param dry_run=true

docker compose exec -T prefect-worker prefect deployment run \
  "Rechercher les identifiants MUBI et TMDB/rechercher-identifiants-manquants" \
  --param max_films=3 --param provider=all
```

Les paramètres disponibles dans **Run** sont `provider` (`all`, `mubi`, `tmdb`),
`max_films` (10), `visa_number` (facultatif), `max_candidates` (10) et `dry_run`
(false). Les volumes doivent être des entiers strictement positifs. Avec un
visa, un seul film est ciblé. Une erreur technique ou un blocage fait échouer
le flow ; `a_revoir`, `ambigu` et `non_trouve` sont des conclusions métier normales.

Les logs relient le flow Prefect au `run_id` inscrit dans les tables. Les
tentatives sont conservées individuellement ; il n'y a ni reprise automatique
ni retry Prefect global. Le déploiement ne partage pas le verrou des demandes
Metabase et n'est pas déclenché par leur poller. Aucun modèle dbt ni source
canonique n'est publié par ce flow.

## Critères et limites

- Titre exact après normalisation des accents, ponctuation et articles finaux ;
  le titre original disponible sur la fiche constitue une variante admissible.
- Au moins un réalisateur concordant après normalisation et remise en ordre des
  mots du nom. Un titre seul ne confirme jamais une identité. Une référence CNC
  absente ou contradictoire est envoyée directement en revue.
- Une valeur d'ID déjà renseignée, même invalide, reste intacte. Pour un visa
  dupliqué, le catalogue n'est recherché que si toutes ses lignes ont cet ID vide.
- Les années des fiches sont conservées comme preuves. Une année de visa ou
  d'agrément n'est pas assimilée à une année de production. Des homonymes du même
  réalisateur peuvent subsister : « confirmé » ne signifie pas une certitude de 100 %.
- MUBI cherche dans **Tous les films**, y compris indisponibles en streaming.
  Son ID est numérique, jamais le slug. TMDB utilise les pages publiques, sans clé API.
- Une seule requête de titre et la première page sont parcourues. Par défaut,
  dix fiches au maximum sont examinées. Plusieurs candidats concordants donnent
  `ambigu` ; une fiche illisible ou une limite atteinte interdit la confirmation.
  Une absence de résultat ne prouve pas l'absence au catalogue.
- Pauses de 3 à 6 secondes entre navigations ; deux tentatives sur erreurs
  transitoires et délai maximal de 180 secondes par recherche de catalogue.
  Un HTTP 403/429 suspend le domaine jusqu'à la fin du lancement. Aucun CAPTCHA
  n'est résolu. Les changements HTML peuvent demander une adaptation des parseurs.

## Vérification

```bash
python -m pytest ingestion/scraping/id_matching/test_matching.py -q
python -m pytest tests/ingestion/test_prefect_deployments.py tests/ingestion/test_prefect_recovery.py -q
ruff check ingestion/scraping/id_matching
bash -n ingestion/prefect/start_worker.sh
```

Les tests synthétiques couvrent sélection, homonymes, noms normalisés,
ambiguïtés, limites, blocages, parseurs et routage vers les tables. Ils ne
valident pas l'accessibilité actuelle des sites ni une installation PostgreSQL.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-16 | Joel Teixeira | Recherche des IDs manquants, journal des propositions dans deux tables ops et flow Prefect manuel séparé. |
