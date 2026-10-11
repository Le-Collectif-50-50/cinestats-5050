# dbt ingestion

## Metadata du document

**Owner:** Data Team DataForGood

**Dernière révision:** 2026-10-11

**Status:** actif

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-26 | Joel Teixeira | Documentation du projet dbt ingestion, des tags phase1/phase2 et du schéma `ops` |
| 2 | 2026-10-06 | Joel Teixeira | Suppression des déclarations de modèles absents et alignement des modèles documentés sur le code actuel |
| 3 | 2026-10-10 | Joel Teixeira | Ajout du runbook local macOS/WSL2 pour le debug et dbt Docs |
| 4 | 2026-10-11 | Joel Teixeira | Normalisation des espaces dans les budgets CNC avant conversion numérique. Inclusion des modèles intermédiaires et finaux dans la phase 2, avec leurs dépendances amont. Alignement des clés des corrections, identifiants des sociétés et avertissements sur les correspondances externes absentes ou dupliquées. Historisation des résultats et détails dbt pour Metabase, quarantaine des crédits sans film et harmonisation des types dans les jointures Mubi |

Projet dbt Core exécuté depuis `prefect-worker`.

## Rôle

1. Lire les sources `raw` chargées par Airbyte ou par le scraper Allociné.
2. Normaliser les données dans `staging`.
3. Consolider les vues intermédiaires dans `intermediate`.
4. Publier les tables finales dans `fnl` quand elles existent.
5. Publier les vues opérationnelles dans `ops`.

Le staging `stg_cnc_films` retire les espaces classiques, insécables (U+00A0) et fines insécables (U+202F) de `DEVIS`, puis remplace la virgule décimale par un point avant conversion numérique. La multiplication par un million pour les années d'agrément à partir de 2013 reste inchangée.

## Exécution

Pour travailler sans conteneur sur macOS ou Windows via WSL2, suivre le [runbook dbt local](runbook_dbt_local.md) : environnement `.venv-dbt`, connexion, tests et serveur dbt Docs.

Depuis le container worker:

```bash
dbt parse --profile ric --project-dir /app/ingestion/dbt
dbt build --profile ric --project-dir /app/ingestion/dbt --select tag:phase1
dbt build --profile ric --project-dir /app/ingestion/dbt --select +tag:phase2
```

Depuis la racine du repo:

```bash
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt parse --profile ric --project-dir /app/ingestion/dbt
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt build --profile ric --project-dir /app/ingestion/dbt --select tag:phase1
docker compose -f ingestion/docker-compose.yml exec prefect-worker dbt build --profile ric --project-dir /app/ingestion/dbt --select +tag:phase2
```

## Tags

1. `phase1`: `stg_cnc_films`, exécuté avant scraping Allociné.
2. `phase2`: `stg_allocine_films`, `v_allocine_pipeline_status` et tous les modèles des dossiers `intermediate/` et `fnl/`, exécutés après scraping Allociné. Les deux dossiers héritent du tag dans `dbt_project.yml`.

Le flow Prefect principal exécute toujours `tag:phase1`. Il exécute `+tag:phase2` seulement quand le paramètre `run_dbt_phase_2_step` est activé.

Le préfixe `+` inclut les dépendances amont, notamment les modèles de staging non taggés. La finalisation construit ainsi les modèles `intermediate` et `fnl` et exécute les tests associés. La phase 1 reste limitée à `stg_cnc_films`.

Toutes les sources brutes référencées doivent exister et être lisibles par `dbt_user`, y compris les tables de corrections et les sorties Mubi. Le flow principal ne lance que le scraping Allociné ; les sources Mubi doivent être alimentées séparément. Un échec de construction ou de test fait échouer la finalisation.

Pour vérifier le périmètre sans écrire en base, remplacer `dbt build` par `dbt ls --resource-type model` dans la commande de phase 2. Après déploiement du worker mis à jour, cette commande de build permet aussi de reconstruire les couches manquantes sans relancer Airbyte ni le scraping.

## Modèles opérationnels

1. `staging.stg_cnc_films`: projection typée de `raw.films`.
2. `staging.stg_allocine_films`: projection typée des résultats réussis de `raw.allocine_data`.
3. `intermediate.int_cnc_films`: transformations métier CNC et jointure avec `stg_id_matching`.
4. `intermediate.int_allocine_films`: projection des données Allociné et jointure avec `stg_id_matching`.
5. `ops.v_allocine_pipeline_status`: vue dashboard Metabase pour le suivi Allociné.

Les modèles intermédiaires CNC et Allociné actuels ne sélectionnent pas automatiquement la dernière version par visa ou par enregistrement source. Les anciennes déclarations YAML de déduplication, dont les fichiers SQL sont absents, ne constituent pas des tests actifs. Leur suppression ne supprime aucune relation PostgreSQL existante.

## Qualité des identifiants

Les corrections de nominations, crédits et genres utilisent respectivement `award_nomination_id`, `film_credit_id` et `film_genre_id`. Les tests de staging et intermédiaires portent sur ces colonnes, et non sur une colonne générique `id`.

Dans `int_id_matching`, `film_id` et `cnc_visa` doivent être renseignés et uniques. Le titre `cnc_name` doit être renseigné mais peut être partagé par plusieurs films. Les tests de présence et d'unicité des identifiants Allociné, Mubi et TMDB ont une sévérité `warn`. Les tests d'unicité de `fnl_films.film_id` et `fnl_films.cnc_visa` sont également des avertissements : les doublons restent présents, sans déduplication arbitraire ni arrêt du pipeline. Leur présence impose de vérifier le grain des analyses avant de compter des films. Ne pas utiliser `--warn-error` pour cette politique.

Dans `int_credit_holders_role`, les identifiants des personnes restent dérivés de leur nom complet. Ceux des sociétés sont dérivés de `company:` suivi de leur raison sociale, car leur champ `full_name` est nul. Une raison sociale absente ou vide ne produit pas d'identifiant valide : le test final `not_null` reste bloquant. Cette convention n'effectue pas de résolution des homonymes.

Les crédits dont `film_id` est nul sont exclus de `fnl_film_credits` et conservés dans `ops.film_credits_unmatched`. Cette quarantaine expose l'identifiant Allociné, la personne ou société, le rôle et les visas/titres des entrées de scraping à examiner. Le test `film_credits_unmatched_review` signale leur présence avec une sévérité `warn`. Aucune correspondance n'est attribuée automatiquement par titre ou par visa de la requête de scraping. Les personnes et sociétés restent dans leur référentiel final.

Les jointures intermédiaires Mubi convertissent les identifiants numériques du scraping en texte pour les comparer aux identifiants du matching.

## Suivre la qualité dbt dans Metabase

Le hook `on-run-end` du projet appelle [persist_dbt_results](macros/persist_dbt_results.sql) après `build`, `test`, `run`, `seed` et `snapshot`. Il historise les résultats des modèles et tests, y compris les avertissements, erreurs et éléments ignorés :

- `ops.dbt_run_results` : une ligne par invocation et ressource dbt ; statut, modèle, colonne, nombre d'anomalies, durée et message.
- `ops.dbt_test_failures` : les lignes concernées, en JSON, pour les tests en avertissement ou en échec configurés avec `store_failures: true`.
- `ops.v_dbt_latest_results` : dernier résultat observé par ressource. Un run partiel ne masque pas les derniers résultats des autres contrôles.

Les contrôles non bloquants et le contrôle de quarantaine utilisent le stockage natif des échecs dbt dans `ops`. Le hook recopie leurs détails avec l'identifiant d'invocation, afin de conserver l'historique même lorsque dbt reconstruit les tables techniques du test. Les tables `id_matching_duplicates` et `allocine_duplicates` ne sont pas nécessaires. Les résultats centraux sont lisibles par `metabase_ops_user` ; les sources restent inchangées.

Pour un test `unique`, le nombre d'anomalies compte les **valeurs dupliquées**, et le détail contient `unique_field` et `n_records`. Pour `not_null`, il compte les **lignes** et le détail conserve les colonnes de la ligne. Ne pas additionner ces nombres comme un total de films : plusieurs tests peuvent signaler les mêmes données. Les détails sont joints à la même invocation que le résultat affiché. La requête de rapprochement des doublons utilise ensuite la version actuelle de `raw.id_matching` pour retrouver les titres et visas source.

La collecte commence au déploiement du hook ; les anciens logs ne sont pas importés. Une interruption brutale ou une erreur de compilation avant le hook peut empêcher l'enregistrement du run : conserver les logs Prefect pour ces cas. Les résultats sont conservés sans purge automatique.

Le dashboard « Qualité des données — dbt » comprend trois indicateurs (tests en avertissement, erreurs bloquantes, crédits isolés), les contrôles à examiner, les correspondances source à revoir, les détails et l'historique. Les requêtes sont versionnées dans [analyses/metabase](analyses/metabase). Prévisualisation sans clé ni appel réseau, depuis la racine :

```bash
python3 infra/data/metabase-dbt-quality.py --preview
```

Création ou mise à jour via l'API Metabase, avec une clé disposant des droits sur la connexion `cinestats-ops-db` et la collection choisie :

```bash
python3 infra/data/metabase-dbt-quality.py \
  --url https://<metabase> \
  --api-key-file /chemin/protege/cle-api-metabase \
  --collection-id <id-collection> \
  --state-file /chemin/persistant/dashboard-dbt-state.json
```

La clé reste hors Git et hors ligne de commande. Le fichier d'état conserve les identifiants du dashboard et des questions pour les actualisations ; le réutiliser évite les créations multiples. Le script conserve les cartes ajoutées manuellement. Aucune publication publique ni modification des permissions Metabase n'est effectuée. L'accès API doit être fourni séparément ; la connexion SSH au serveur ne remplace pas une authentification Metabase.

Après déploiement, relancer `dbt build --select +tag:phase2` avec les options de profil ci-dessus. Cela reconstruit les finales et la quarantaine, teste les données puis alimente le suivi. `dbt parse` vérifie la configuration mais ni les données ni l'exécution SQL.

## Permissions

Le runtime dbt utilise `dbt_user`.

Grants attendus sur la base projet:

```sql
GRANT USAGE, CREATE ON SCHEMA staging TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA intermediate TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA fnl TO dbt_user;
GRANT USAGE, CREATE ON SCHEMA ops TO dbt_user;
GRANT USAGE ON SCHEMA raw TO dbt_user;
```

## Referenced by

- [ingestion/README.md](../README.md)
