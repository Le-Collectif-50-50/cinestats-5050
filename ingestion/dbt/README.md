# dbt ingestion

## Metadata du document

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-05-26 | Joel Teixeira | Documentation du projet dbt ingestion, des tags phase1/phase2 et du schéma `ops` |
| 2 | 2026-10-06 | Joel Teixeira | Suppression des déclarations de modèles absents et alignement des modèles documentés sur le code actuel |
| 3 | 2026-10-10 | Joel Teixeira | Ajout du runbook local macOS/WSL2 pour le debug et dbt Docs |
| 4 | 2026-10-11 | Joel Teixeira | Normalisation des espaces dans les budgets CNC avant conversion numérique. Inclusion des modèles intermédiaires et finaux dans la phase 2, avec leurs dépendances amont. Alignement des clés des corrections, identifiants des sociétés et avertissements sur les correspondances externes absentes ou dupliquées. Historisation des résultats et détails dbt pour Metabase, quarantaine des crédits sans film et harmonisation des types dans les jointures Mubi |
| 5 | 2026-10-15 | Joel Teixeira | URL d’affiche nullable dans le staging Allociné ; prérequis de migration. |
| 6 | 2026-11-11 | Joel Teixeira | Couverture des 29 genres observés : corrections orthographiques, classement du Péplum et catégories explicites Divers, Erotique et Évènement Sportif. |
| 7 | 2026-11-12 | Joel Teixeira | Alignement des corrections sur le schéma Airbyte : clés composées des crédits et genres, retrait du champ Allociné des rôles et filtre GENRE_ID. Dashboard Metabase de revue du scraping Allociné, des écarts de visa et des recherches sans résultat (`not_found`). |
| 8 | 2026-11-13 | Joel Teixeira | Intégration des ajouts manuels de personnes et crédits, dernier succès Allociné par visa, contrôles de références et conversion du crédit d’impôt. |
| 9 | 2026-11-13 | Joel Teixeira | Prise en charge de la date et de l’heure dans UPDATED_DATE pour toutes les sources GSheet concernées, rétrocompatibilité et tri des corrections. Bouton Allociné dans Metabase, suivi des demandes et statuts par heure avec filtre de plage de dates. Documentation de la reprise des correspondances validées dans id_matching. Fiches métier Film et Credit Holder dans Metabase, recherche, navigation croisée et vue finale des affiches. |
| 10 | 2026-11-14 | Joel Teixeira | Deuxième bouton Allociné par visa, forçage explicite et suivi du parcours Airbyte → scraping → dbt. |

| 10 | 2026-11-14 | Joel Teixeira | Priorité du titre corrigé dans id_matching sur le titre Allociné, avec repli sur le titre CNC et tests des valeurs vides. |
| 11 | 2026-11-14 | Joel Teixeira | Dashboard de provenance par visa CNC : source synchronisée, matching, dernier essai/succès, staging, transformations, corrections et modèles finaux. Réconciliation des dashboards Operations : séparation ingestion/scraping, introductions, navigation et filtre relatif Allociné. Rangement des questions Mubi isolées. Clarification des permissions indépendantes des sous-collections. |

| 12 | 2026-11-14 | Joel Teixeira | Correctif temporaire de last_name : conservation des mots après le premier dans les crédits Allociné, limites et tests. Publication des associations film-genre manuelles, contrôles de conservation, d’unicité et de références (#57). Ajout du tutoriel métier illustré de revue humaine Allociné, publié dans Metabase Operations avec liens sur cinq dashboards. Publication automatique du lineage dbt complet dans `docs/dbt-lineage.md` sur `main`, avec vues détaillées par schéma, sans connexion PostgreSQL, et identité de publication GitHub App dédiée. |

Projet dbt Core exécuté depuis `prefect-worker`.

## Rôle

1. Lire les sources `raw` chargées par Airbyte ou par le scraper Allociné.
2. Normaliser les données dans `staging`.
3. Consolider les vues intermédiaires dans `intermediate`.
4. Publier les tables finales dans `fnl` quand elles existent.
5. Publier les vues opérationnelles dans `ops`.

`stg_allocine_films.poster_url` expose l’URL distante nullable de l’affiche. Appliquer la [migration ingestion](../../infra/data/2026-10-15-allocine-poster-url.sql) avant de reconstruire ce modèle sur une base existante. Le [guide Allociné](../scraping/allocine/README.md#affiches--migration-et-reprise-explicite) décrit le backfill explicite et les droits requis. Aucun fichier image n’est stocké par dbt. Les projections aval restent inchangées.

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

## Consulter le lineage dans GitHub

Le [document de lineage](https://github.com/Le-Collectif-50-50/cinestats-5050/blob/main/docs/dbt-lineage.md)
présente d’abord un diagramme Mermaid complet : toutes les sources et tous les modèles
actifs, regroupés par schéma, avec leurs dépendances de bout en bout dans dbt.
Les vues par schéma restent disponibles dans une section repliable, suivies
d’un inventaire lié au code analysé. GitHub affiche ces diagrammes
directement dans le Markdown, sans extension ni service supplémentaire.
Le lien devient disponible après le premier push concerné sur `main` ayant réussi.

Le workflow [dbt lineage](../../.github/workflows/dbt-lineage.yml) :

1. Se déclenche sur les PR et les push sur `main` qui modifient `ingestion/**`,
   le générateur, ses tests ou le workflow lui-même. Aucun déclenchement planifié
   ni lié à un changement des données en base.
2. Installe sur le runner les versions dbt déjà utilisées dans
   `ingestion/prefect/Dockerfile` : Core 1.11.7 et Postgres 1.10.0.
   Maintenir ces versions ensemble lors des mises à jour.
3. Exécute `dbt parse --no-partial-parse` avec un profil aux valeurs fictives.
   Cette commande ne se connecte pas à PostgreSQL et ne lance ni modèle ni scraper.
4. Convertit le `manifest.json` en Markdown/Mermaid avec un script Python
   utilisant uniquement la bibliothèque standard. Le manifest complet n’est pas publié.
5. Joint le document à chaque run sous l’artefact `dbt-lineage`. Pour une PR,
   cet artefact permet de relire le Markdown ; les diagrammes seront rendus
   dans le document publié sur GitHub après fusion.
6. Après un push sur `main`, publie le document dans `docs/dbt-lineage.md` sur
   `main`, avec un token temporaire de l’application GitHub dédiée, limité au dépôt
   et à la permission `contents: write`.
   Les PR, y compris celles de forks, ne disposent pas de cette permission.

Chaque publication modifiée ajoute un commit du bot dans `main`, limité à
`docs/dbt-lineage.md`. Le README principal est conservé. Le message du commit
contient `[skip ci]` ; le chemin du document n’entre pas non plus dans les filtres
de ce workflow. Le token de publication est révoqué à la fin du job.
Si les sources du graphe ont changé sur `main` depuis le commit analysé, le run
laisse la publication au run suivant pour éviter un graphe périmé.
Le push est effectué sans forcer : une modification concurrente de `main` peut
faire échouer la publication. Une règle interdisant les commits directs du bot
sur `main` la bloque également ; les protections ne sont pas modifiées par ce workflow.
L’artefact du run reste disponible même si la publication échoue.

### Configurer l’identité de publication

Créer l’application privée **CineStats dbt lineage** dans le compte du Collectif
50/50 et l’installer uniquement sur `cinestats-5050`, avec **Contents: Read and write**
(et Metadata: Read-only imposé par GitHub), sans webhook ni permission Workflows.
Enregistrer sa clé privée dans le secret Actions `DBT_LINEAGE_APP_PRIVATE_KEY` et
son identifiant dans la variable `DBT_LINEAGE_APP_ID`. Ne jamais versionner la clé.
Conserver le passage par PR pour les autres identités dans la protection de `main`
et ajouter uniquement cette application à `bypass_pull_request_allowances.apps`.
Le `GITHUB_TOKEN` natif ne dispose pas de cette exception.

Pour renouveler la clé : générer une nouvelle clé dans les paramètres de
l’application, remplacer le secret Actions, vérifier une publication puis révoquer
l’ancienne clé. Pour désactiver la publication : retirer l’exception de protection
et désinstaller l’application. Les contrôles et artefacts des PR restent disponibles.

Le graphe couvre les dépendances déclarées par `ref()` et `source()` entre sources,
modèles, seeds et snapshots actifs. Il ne décrit pas les colonnes, les références
SQL écrites en dur, les traitements Airbyte/Prefect/scraping, ni l’état réel en base.
Les tests, analyses et macros ne sont pas des nœuds du graphe.

Pour reproduire sans accès à PostgreSQL, depuis la racine avec l’environnement
dbt du [runbook local](runbook_dbt_local.md) activé :

```bash
export POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=1 POSTGRES_DB=lineage
export DBT_USER_POSTGRES_PASSWORD=unused DBT_SEND_ANONYMOUS_USAGE_STATS=false
dbt parse --no-partial-parse --project-dir ingestion/dbt --profiles-dir ingestion/dbt/profiles
python scripts/generate_dbt_lineage.py ingestion/dbt/target/manifest.json /tmp/dbt-lineage.md \
  --source-url "https://github.com/Le-Collectif-50-50/cinestats-5050/tree/$(git rev-parse HEAD)" \
  --revision-date "$(git show -s --format=%cs HEAD)"
python -m unittest discover -s tests/ingestion -p test_dbt_lineage.py
```

Références : [dbt parse](https://docs.getdbt.com/reference/commands/parse),
[diagrammes Mermaid sur GitHub](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams).

## Tags

1. `phase1`: `stg_cnc_films`, préparation CNC après Airbyte.
2. `phase2`: `stg_allocine_films`, `v_allocine_pipeline_status` et tous les modèles des dossiers `intermediate/` et `fnl/`, exécutés après la phase 1 avec les résultats de scraping déjà disponibles. Les deux dossiers héritent du tag dans `dbt_project.yml`.

Le flow Prefect principal exécute toujours `tag:phase1`. Il exécute `+tag:phase2` seulement quand le paramètre `run_dbt_phase_2_step` est activé.

Le préfixe `+` inclut les dépendances amont, notamment les modèles de staging non taggés. La finalisation construit ainsi les modèles `intermediate` et `fnl` et exécute les tests associés. La phase 1 reste limitée à `stg_cnc_films`.

Toutes les sources brutes référencées doivent exister et être lisibles par `dbt_user`, y compris les tables de corrections et les sorties Mubi. Le flow principal ne lance aucun scraper ; les sources Allociné et Mubi sont alimentées par leurs déploiements manuels séparés. Un échec de construction ou de test fait échouer la finalisation.

Pour vérifier le périmètre sans écrire en base, remplacer `dbt build` par `dbt ls --resource-type model` dans la commande de phase 2. Après déploiement du worker mis à jour, cette commande de build permet aussi de reconstruire les couches manquantes sans relancer Airbyte ni le scraping.

## Modèles opérationnels

1. `staging.stg_cnc_films`: projection typée de `raw.films`.
2. `staging.stg_allocine_films`: projection typée des résultats réussis de `raw.allocine_data`.
3. `intermediate.int_cnc_films`: transformations métier CNC et jointure avec `stg_id_matching`.
4. `intermediate.int_allocine_films`: projection des données Allociné et jointure avec `stg_id_matching`.
5. `ops.v_allocine_pipeline_status`: vue dashboard Metabase pour le suivi Allociné.

Le staging Allociné conserve le dernier succès par visa source (repli sur `source_record_id` si le visa est absent), selon `extracted_at`, puis `run_id` et `record_hash`. Une tentative ultérieure en erreur ne remplace pas ce succès. Les visas absents ou encore dupliqués font échouer le test dédié. Le rapprochement des métadonnées Allociné utilise le visa et l’identifiant Allociné ; la table finale joint ces métadonnées par `film_id`. Des visas distincts partageant un identifiant Allociné restent signalés dans les contrôles de matching. Cette règle ne valide pas l’identité d’un ancien résultat de scraping.

## Priorité du titre final

`fnl_films.movie_name` utilise le titre non vide de `int_id_matching.cnc_name`
(onglet `id_matching`, colonne `TITRE`) en priorité, puis le titre Allociné non vide,
puis le titre CNC de `raw.films`. Les espaces de bord sont retirés des deux premiers
choix ; une chaîne vide ou composée uniquement d'espaces déclenche le repli.
Cette priorité s'applique à tous les films : les titres du matching constituent
le choix éditorial, même lorsqu'un titre Allociné existe.

Pour le visa `144246`, le titre du matching « Dans les yeux de Thomas Pesquet »
doit ainsi remplacer « 16 levers de soleil » dans le modèle final. Cette correction
de titre ne valide ni le format de l'œuvre ni ses dates, genres ou crédits (#46).
Après déploiement du modèle, reconstruire `fnl_films` dans le cadre du run dbt
habituel pour publier le résultat. Aucun nouveau scraping n'est nécessaire lorsque
seul le titre change. Les identifiants et les associations ne sont pas modifiés.

Le test `test_film_title_matching_priority_and_fallbacks` dans
`tests/ingestion/test_dbt_manual_recovery.py` exécute le modèle complet sur six cas
PostgreSQL : correction prioritaire, titre Allociné absent, matching nul ou vide,
et repli CNC. Comme les autres tests SQL de ce module, il nécessite
`DBT_TEST_SSH` et `DBT_TEST_DATABASE` et s'exécute en transaction read-only.

## Classification des genres

Le `CASE` de `int_film_genres` classe `Judiciaire` dans `Aventure/Policier/Thriller` et accepte `Epouvante-horreur` avec ou sans accent initial pour `Fantastique/Horreur/SF`. `Péplum` rejoint `Biopic/Guerre/Histoire`. `Divers`, `Erotique` et `Évènement Sportif` conservent chacun une catégorie explicite. Ce mapping couvre les 29 genres distincts observés dans `staging.stg_allocine_films` le 11 novembre 2026. Les nouveaux genres sans correspondance restent nuls et font échouer les tests de présence des tables finales : ajouter leur classement explicitement, sans catégorie de repli « Autre ».

### Associations film-genre manuelles (#57)

`fnl_film_genre` réunit `int_film_genres` et `int_fix_film_genres` avec une
association unique par `(film_id, genre_id)`. Une correction ajoute un genre,
y compris si le scraping n’en fournit aucun. Elle ne remplace ni ne supprime
les autres genres du film. Un doublon présent dans les deux sources reste une
seule association finale.

Dans l’onglet GSheet `film_genres`, renseigner `FILM ID`, `GENRE ID`,
`UPDATED DATE` et `UPDATED BY`. Utiliser les UUID existants de `fnl_films`
et `fnl_genre`, puis synchroniser Airbyte et exécuter la phase 2 dbt. Aucun
nouveau scraping n’est nécessaire. Les règles d’admission du staging restent
inchangées, notamment son exclusion actuelle des lignes signées Hugo Laurens.
Les tests bloquants vérifient les deux références, l’unicité des associations
et la conservation des corrections admises. Une référence invalide n’est pas
filtrée silencieusement ; le test signale l’erreur.

Le test PostgreSQL
`test_manual_film_genres_added_without_replacing_scraped_associations` couvre
l’ajout sans scraping, l’ajout d’un second genre, les doublons, l’absence de
correction et les sources vides. Il utilise les mêmes prérequis read-only que
les autres tests de `tests/ingestion/test_dbt_manual_recovery.py`.

Après déploiement, reconstruire le modèle et ses dépendances avec
`dbt build --profile ric --project-dir /app/ingestion/dbt --select +fnl_film_genre`.
Le build de phase 2 habituel inclut aussi cette sélection. Pour revenir en
arrière, restaurer le SQL précédent puis reconstruire le modèle : les ajouts
manuels resteront dans la source, mais ne seront plus publiés.

## Correctif temporaire des noms (#41)

Dans les sept catégories de personnes de `int_credit_holders_role`, `last_name`
conserve désormais tous les mots après le premier, au lieu du seul deuxième mot :
`Eliane de Latour` donne `de Latour`. Les espaces multiples, insécables et fines
insécables sont normalisés dans ce champ ; un mononyme donne une chaîne vide.
`first_name`, `full_name`, les UUID et les associations restent inchangés.
Ce découpage demeure approximatif : `Jean Claude Van Damme` donne
`first_name = Jean` et `last_name = Claude Van Damme`.

Les corrections GSheet restent prioritaires, y compris une ancienne correction
tronquée : ce correctif ne répare pas ces valeurs. Les sociétés et les tables
historiques `ric_*` du backend ne sont pas concernées. La migration vers un champ
`full_name` de référence reste à décider ; l’issue #41 reste ouverte.

Après déploiement, reconstruire `int_credit_holders_role` et ses dépendants via
le build de phase 2 habituel. Aucun nouveau scraping n’est requis. Pour revenir
en arrière, rétablir le SQL précédent puis reconstruire les mêmes modèles.
Le test SQL `test_last_name_preserves_remaining_words_in_all_credit_categories`
couvre les sept catégories, les particules, espaces, mononymes et la stabilité
des identifiants avec les prérequis PostgreSQL décrits ci-dessous.

## Qualité des identifiants

Les corrections de nominations utilisent `award_nomination_id`. Les corrections de crédits sont dédupliquées par `(film_id, role_id, credit_holder_id)` et celles des associations film-genre par `(film_id, genre_id)`, en conservant la date de correction la plus récente. Les tests contrôlent la présence des composants et l’unicité de chaque association ; les anciens champs `film_credit_id` et `film_genre_id` ne sont plus exposés. Le référentiel des genres utilise `GENRE_ID` et `GENRE_NAME` dans la source ; le filtre de la ligne exemple porte sur `GENRE_ID`. Les corrections de rôles n’exposent plus `allocine_name`, absent de la source.

Dans Airbyte, ne pas dédupliquer `film_credits` sur `CREDIT HOLDER ID` seul : une personne peut avoir plusieurs rôles et films. Utiliser une clé composée des trois champs ou le mode overwrite sans déduplication. dbt ne peut pas restaurer les associations supprimées en amont.

Dans `int_id_matching`, `film_id` et `cnc_visa` doivent être renseignés et uniques. Le titre `cnc_name` doit être renseigné mais peut être partagé par plusieurs films. Les tests de présence et d'unicité des identifiants Allociné, Mubi et TMDB ont une sévérité `warn`. Les tests d'unicité de `fnl_films.film_id` et `fnl_films.cnc_visa` sont bloquants : la table finale doit contenir une ligne par film. Les avertissements sur les identifiants externes ne sont pas transformés en erreurs via `--warn-error`.

Dans `int_credit_holders_role`, les identifiants des personnes restent dérivés de leur nom complet. Ceux des sociétés sont dérivés de `company:` suivi de leur raison sociale, car leur champ `full_name` est nul. Une raison sociale absente ou vide ne produit pas d'identifiant valide : le test final `not_null` reste bloquant. Cette convention n'effectue pas de résolution des homonymes.

Les crédits dont `film_id` est nul sont exclus de `fnl_film_credits` et conservés dans `ops.film_credits_unmatched`. Cette quarantaine expose l'identifiant Allociné, la personne ou société, le rôle et les visas/titres des entrées de scraping à examiner. Le test `film_credits_unmatched_review` signale leur présence avec une sévérité `warn`. Aucune correspondance n'est attribuée automatiquement par titre ou par visa de la requête de scraping. Les personnes et sociétés restent dans leur référentiel final.

Les jointures intermédiaires Mubi convertissent les identifiants numériques du scraping en texte pour les comparer aux identifiants du matching.

## Naviguer dans les dashboards Operations

[Pipeline Overview](https://metabase.cinestats5050.fr/dashboard/2) est le point
d'entrée pour demander une ingestion et suivre les demandes Metabase de type
`ingestion`. Le statut concerne la dernière demande enregistrée, pas un état
global en temps réel. L'historique compte les demandes par heure de Paris ; les
lancements manuels Prefect ne sont pas inscrits dans cette file. Les graphiques
Allociné et leurs filtres ont été retirés de cette vue ; Metabase a archivé les
quatre questions attachées à ce dashboard (39, 40, 41 et 46).

Les introductions et liens croisent quatre parcours :

- [Qualité dbt](https://metabase.cinestats5050.fr/dashboard/3) : derniers résultats
  par contrôle, ou résultats de l'exécution sélectionnée. Le rapprochement des
  anomalies avec les titres et visas utilise toujours le matching courant.
- [Scraping Allociné](https://metabase.cinestats5050.fr/dashboard/7) : lancement
  séparé, revue métier et tentatives par heure. Le filtre de période ne concerne
  que le graphique ; les compteurs de revue ne recensent pas `error` et `blocked`.
- [Suivi par visa CNC](https://metabase.cinestats5050.fr/dashboard/11) : provenance
  et propagation d'un film entre les couches.
- [Fiche Film](https://metabase.cinestats5050.fr/dashboard/9) : données finales
  destinées à la consultation métier.

Les cinq questions Mubi sans dashboard (47 à 51) sont regroupées dans la
sous-collection **Explorations Mubi**. Leurs identifiants et requêtes sont
conservés ; leurs titres et descriptions précisent les unités. Le compteur de
matching compte des lignes, pas des films distincts, et ignore le statut
`no_awards` ; le compteur de collecte des récompenses déduplique les liens et
considère `no_awards` comme terminé. Ils ne mesurent donc pas le même périmètre.

Le [script de réconciliation](../../infra/data/metabase-operations.py) cible
explicitement cette instance et ses identifiants. Il vérifie les noms des quatre
dashboards, leur collection et la connexion avant modification. Sans `--apply`,
il valide les trois requêtes d'ingestion et le filtre temporel Allociné, puis
affiche le plan sans écrire.

```bash
python3 infra/data/metabase-operations.py --env-file ingestion/.env
python3 infra/data/metabase-operations.py --env-file ingestion/.env --apply
```

Réappliquer cette réconciliation **après** les scripts de publication des
dashboards spécialisés : ceux-ci possèdent encore leurs propres dispositions et
peuvent remplacer les introductions ou replacer les cartes. La réconciliation
préserve les filtres des dashboards spécialisés, notamment la période Allociné
déjà configurée ; elle retire uniquement les deux filtres obsolètes de Pipeline
Overview. Le type de widget temporel de la question Allociné est aligné sur le
filtre du dashboard : une période relative ne doit pas cibler un widget limité
aux plages fixes, sous peine d'erreur à l'exécution. La valeur de période reste
inchangée. Le script ne modifie ni les actions, ni les données, ni les permissions.

Pendant une reconstruction dbt, une relation peut être temporairement absente.
Actualiser le dashboard après la fin de l'ingestion avant de conclure à une
requête défectueuse. Les détails d'anomalies peuvent dépasser la limite
d'affichage de Metabase ; le nombre de lignes affichées ne représente alors pas
le total des anomalies.

### Restreindre Operations et Trigger

`Trigger` est déjà une sous-collection d'`Operations`. Ce rangement ne garantit
pas un accès identique : les permissions des sous-collections existantes doivent
être vérifiées séparément dans **Administration → Permissions → Collections**.
Pour Operations, Trigger et Explorations Mubi, attribuer **Aucun accès** à **Tous les
utilisateurs** et aux autres groupes non Ops ; attribuer **Consultation** au
groupe Operations, ou **Édition** à ses éditeurs. Les administrateurs conservent
leur accès. Les droits se cumulent : un autre groupe permissif rétablit l'accès.
Voir la [documentation Metabase](https://www.metabase.com/docs/latest/permissions/collections).

Après enregistrement, vérifier avec un compte non Ops l'absence de la collection
et le refus d'accès à son URL directe et à ses questions. Ces réglages exigent
un administrateur ; la clé API Operations utilisée pour les dashboards ne peut
pas lire ni modifier le graphe des permissions (HTTP 403).

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

## Examiner les correspondances du scraping dans Metabase

Équipes métier : suivre le [tutoriel illustré de revue humaine Allociné](../../docs/runbooks/ingestion-tutoriel-revue-humaine-allocine.md), avec recherche des preuves, décision dans Google Sheets, demandes Metabase et contrôle de publication. Disponible directement [dans Metabase Operations](https://metabase.cinestats5050.fr/document/1).

Le dashboard [Scraping Allociné — À examiner](https://metabase.cinestats5050.fr/dashboard/7) lit directement `raw.allocine_data`
sur la connexion `cinestats-ops-db`. Il comporte un bouton **Lancer le scraping Allociné**,
quatre compteurs (total, `needs_review`, `visa_mismatch`, `not_found`), trois tables de revue,
un graphique empilé des statuts par heure et une table des 50 dernières demandes.
Les filtres **Visa CNC** (égalité exacte) et **Titre contient** (recherche sans distinction
de casse, CNC ou Allociné) portent sur les compteurs, les tables de revue et le graphique.
Ils ne modifient ni le formulaire de lancement ni la table des demandes.
Le filtre **Période du scraping** est une plage de dates reliée uniquement au graphique,
sur le champ `raw.allocine_data.extracted_at`. Sans sélection, tout l’historique est affiché.
Les tables affichent les titres, visas attendu et trouvé, réalisateur Allociné,
motif, liens de vérification et dernière tentative en heure de Paris, par ancienneté.

La [requête commune](analyses/metabase/scraping_review_queue.sql) classe **tous**
les statuts avant de sélectionner les anomalies. Une seule tentative est retenue
par `source_record_id`, avec repli sur le visa puis l'empreinte pour les lignes sans
identifiant. Les dates nulles passent après les dates connues ; les égalités sont
départagées par run et empreinte. Sans séquence d'insertion, deux tentatives au même
instant ne permettent pas de prouver leur ordre chronologique.
Une réussite plus récente retire donc le film de cette file ; un ancien écart ne
reste pas affiché après résolution. Le compteur mesure les identifiants source,
pas les tentatives. Aucun historique de validation humaine n'est créé.

`needs_review` signifie une correspondance non confirmée ; `visa_mismatch` indique
un visa Allociné différent du visa source. Le diagnostic peut détailler plusieurs
candidats, sans candidat retenu ni visa Allociné unique. Les anciens résultats ne
sont pas requalifiés automatiquement. `not_found` signale une recherche sans résultat :
vérifier manuellement le titre et l'identifiant Allociné. Ce statut est considéré
comme terminé par le scraper et ne déclenche pas de reprise automatique.
Les erreurs techniques (`error`, `blocked`) restent hors des compteurs et tables de revue ;
elles figurent dans le graphique horaire.

Pour accepter un `visa_mismatch` ou `needs_review` après vérification humaine,
cocher `VALIDATION_MANUELLE` dans le Google Sheet `id_matching`, avec un ID
Allociné renseigné, puis synchroniser Airbyte et relancer le scraper. Voir la
[procédure de validation manuelle](../scraping/allocine/README.md#reprendre-une-correspondance-validée-manuellement).
Le nouveau succès conserve les deux visas et retire l'anomalie de cette file.
Une reconstruction dbt publie ensuite les enrichissements ; la case cochée ne
relance pas les succès sur le même ID à chaque passage.

La vue `ops.v_allocine_pipeline_status`, issue du staging filtré
sur `success`, ne peut pas alimenter cette file. Aucun run dbt n'est nécessaire
pour afficher cette file de revue.

### Déclencher et suivre un scraping

Le formulaire demande une identité déclarative, un motif et un **nombre maximum de films**,
entier strictement positif (10 par défaut). La demande passe par la même file PostgreSQL
et le même poller que Pipeline Overview, avec `request_type=allocine`. Elle déclenche
uniquement le scraper Allociné. Le nombre réellement traité peut être inférieur si
moins de films sont éligibles. Les règles de sélection et de reprise du scraper restent applicables.

Une seule demande Metabase Allociné peut rester active : un second envoi est refusé
par la contrainte unique tant que la première est `pending` ou `processing`.
Le poller passe toutes les 300 secondes par défaut et traite une demande par passage :
un backlog ou un worker indisponible peut allonger ce délai.
La concurrence Prefect du scraper reste limitée à 1, y compris pour les runs manuels.

La table des demandes distingue **En attente**, **Transmise / en cours**, **Terminée** et **Échec**.
« Terminée » signifie une fin technique normale, pas que tous les films ont réussi ;
un lot vide peut aussi terminer normalement. Pour une demande par visa,
« Terminée » exige un scraping confirmé (`success`), puis dbt réussi. La table
affiche le visa demandé et le choix de forçage. Le poller réconcilie les états terminaux
Prefect, y compris les annulations et crashes, au passage suivant. Les identifiants Prefect
permettent de retrouver les logs. Les runs lancés directement dans Prefect ne sont pas
inscrits dans cette file Metabase.

Le [graphique](analyses/metabase/scraping_execution_status.sql) compte les tentatives
stockées par heure de Paris et `scrape_status`, toutes exécutions confondues,
sur toute la période sélectionnée, sans limite de nombre de tranches horaires.
Le filtre est relatif, avec **sept derniers jours** par défaut. La question SQL
accepte également un paramètre relatif ; ce type doit rester aligné avec celui
du dashboard, y compris lors d'une republication.
Les heures sans tentative et les dates nulles sont exclues.
Il inclut `success`, `not_found`, `needs_review`, `visa_mismatch`, `error`, `blocked` et
les statuts inconnus. La période relative filtre les tentatives avant agrégation ; les filtres visa et titre
s’appliquent également au graphique.
L'heure est tronquée au début de la tranche : 14:37 est compté dans 14:00.
Les tentatives de plusieurs runs dans la même heure sont additionnées. Un run qui
chevauche deux heures contribue aux deux tranches selon `extracted_at`. Au passage
à l’heure d’hiver, les deux occurrences de la même heure locale sont regroupées.
Le scraper écrit le lot à la fin : ce graphique ne mesure donc pas une progression en direct.
Un run sans ligne écrite n'y figure pas ; consulter la table des demandes et Prefect.
Le `run_id` métier du scraper est distinct de l'identifiant du flow Prefect.

Le deuxième bouton **Scraper un visa CNC** demande identité, motif, visa CNC
et **Forcer le retraitement** (Non par défaut). Le visa doit être une chaîne de
chiffres strictement positive. Ce formulaire est indépendant des filtres du dashboard.
Il attend Airbyte (connexions configurées dans le worker), scrape uniquement ce visa,
puis lance `dbt build --select +tag:phase2`. Le forçage conserve l'historique et
les contrôles de correspondance. Sans film éligible ou sans résultat `success`,
la demande échoue avant dbt. Les deux boutons partagent le verrou Allociné existant.
Le bouton par lot attend lui aussi Airbyte avant le scraping, mais exige ensuite
une ingestion séparée pour publier ses résultats. Un échec Airbyte empêche le scraping.
Le parcours ciblé impose Airbyte et dbt ; les options de désactivation de
l'ingestion séparée ne s'appliquent pas à ce parcours.

### Publier les formulaires et les cartes

Ordre requis :

1. Sur la base projet vérifiée, appliquer `infra/data/ops-ingestion-table.sql` en propriétaire
   ou administrateur. La migration ajoute `request_type` (défaut `ingestion`), `max_films`,
   `visa_number`, `force_rescrape` et les contraintes Allociné, sans supprimer l'historique. Les droits existants suffisent.
2. Publier `ingestion/prefect/flows.py` sur le worker puis actualiser le déploiement
   `Recuperer les donnees Allocine/lancer-scrapping-allocine` pour exposer `request_id`,
   `visa_number`, `force_rescrape` et `airbyte_connection_names`. Publier également
   `ingestion/scraping/allocine/main.py` et `connector.py` sur le worker.
   Garder la concurrence à 1 et l'absence de calendrier. Le poller lit le nouveau code
   à son prochain run ; ne pas lancer de scraping pour valider la configuration.
3. Exécuter les commandes ci-dessous. Une synchronisation du schéma `cinestats-ops-db`
   par un administrateur est facultative pour ces requêtes SQL natives ; elle rend les
   nouvelles colonnes visibles dans l’explorateur de données.
   Le modèle de la file utilisé par Pipeline Overview est le modèle 38 sur Cinestats.
   `--action-model-id` crée ou actualise les deux actions SQL et leurs boutons ; les IDs
   `action_id` (lot) et `visa_action_id` (visa) sont conservés dans le fichier d'état. Aux passages suivants, le script le réutilise automatiquement.

Depuis la racine, vérifier puis créer ou actualiser le dashboard :

```bash
python3 infra/data/metabase-scraping-review.py --preview
python3 infra/data/metabase-scraping-review.py \
  --url https://metabase.cinestats5050.fr \
  --env-file ingestion/.env --collection-id 7 --check
python3 infra/data/metabase-scraping-review.py \
  --url https://metabase.cinestats5050.fr \
  --env-file ingestion/.env --collection-id 7 --action-model-id 38
```

`METABASE_API_KEY` peut venir de l'environnement, du fichier `.env` explicite
(`python-dotenv` requis), ou de `--api-key-file`. La clé n'est jamais imprimée.
`--check` exécute les neuf requêtes de lecture sans créer de question ni dashboard.
Il ne soumet jamais une demande de scraping.
Le compte Metabase doit pouvoir lire `raw.allocine_data` et `ops.ingestion_run_requests`,
créer une action sur le modèle des demandes et écrire dans la
collection Operations (ID 7 sur cette instance). Aucun droit ni accès public
n'est modifié ; les permissions existantes de la collection s'appliquent.

Conserver le fichier d'état local ignoré par Git
`ingestion/scraping/allocine/local-runs/metabase-review-state.json` : il contient
uniquement l'URL, les identifiants Metabase et la collection. Le réutiliser permet
les mises à jour sans doublons ; `--state-file` permet un autre emplacement.
Les cartes et filtres ajoutés manuellement sont conservés. Actualiser le dashboard
dans Metabase pour relire les résultats ; aucune relance de scraper ni correction
source n'est déclenchée par sa consultation.

## Consulter les fiches Film et Credit Holder dans Metabase

Les dashboards [Fiche Film](https://metabase.cinestats5050.fr/dashboard/9) et
[Fiche Credit Holder](https://metabase.cinestats5050.fr/dashboard/10) sont rangés
à la racine dans **Cinestats 50/50 - Fiches**, hors de la collection Operations.
Ils utilisent la connexion métier **cinestats-5050-db** et uniquement les huit
relations `fnl`, avec les droits Metabase existants. Aucune publication publique
ni modification des permissions n'est effectuée.

- **Film** : chercher par visa CNC exact ou fragment du titre final. La fiche
  affiche poster disponible, identité, genres, crédits et métiers, représentation par genre,
  budget, diffuseurs, financement par pays et dispositifs de soutien.
- **Credit Holder** : chercher par UUID exact ou fragment du prénom, nom ou
  de la raison sociale. La fiche affiche identité, filmographie, métiers,
  films par année d'agrément et personnes créditées sur les mêmes films.
- Une recherche est nécessaire : sans filtre, les listes restent vides et les
  compteurs à zéro. Les recherches textuelles ignorent la casse, mais pas les
  accents. Deux filtres remplis se cumulent avec `AND`.
- Plusieurs résultats peuvent correspondre au nom. Affiner avec le visa ou
  l'UUID, ou utiliser **Ouvrir la fiche**. Les liens dans les crédits et dans la
  filmographie permettent de naviguer entre les deux dashboards.

Les compteurs dédupliquent les entités, films et rôles par identifiant ;
les tableaux de métiers regroupent les libellés inclusifs.
La représentation par genre concerne uniquement les personnes physiques,
avec une catégorie explicite pour les genres non renseignés ou autres.
Une personne peut exercer plusieurs métiers : les lignes ne sont pas additives.
La filmographie est limitée au catalogue Cinestats, et une présence dans les
mêmes crédits ne prouve pas une collaboration directe. Les identifiants dérivés
du nom en amont ne résolvent pas les homonymes. Les valeurs vides ne signifient
pas « non » ou zéro. Le synopsis et les identifiants externes ne figurent pas dans ces fiches.

La vue `fnl.fnl_film_posters` publie l'URL d'affiche issue du dernier succès
Allociné, uniquement lorsqu'il correspond au mapping courant (visa et ID Allociné).
Elle conserve le lien avec `fnl_films` sans ouvrir les schémas `raw` ou `staging`
à la connexion métier. Le dashboard affiche une miniature et un lien vers l'affiche complète, ou
« Affiche non disponible ». La taille de l'aperçu est limitée par le rendu natif
de Metabase. Aucun scraping ni téléchargement d'image n'est déclenché.
Avant la première publication sur une autre instance, déployer les fichiers
`models/fnl/fnl_film_posters.*` et exécuter sur la cible dbt vérifiée :

```bash
dbt build --profile ric --project-dir /app/ingestion/dbt --select fnl_film_posters
```

Les [sélections SQL](analyses/metabase) et le
[script de publication](../../infra/data/metabase-entity-profiles.py) sont versionnés.
Depuis la racine :

```bash
python3 infra/data/metabase-entity-profiles.py --preview
python3 infra/data/metabase-entity-profiles.py --env-file ingestion/.env --check
python3 infra/data/metabase-entity-profiles.py --env-file ingestion/.env
```

`--check` exécute les 19 requêtes sans filtre puis avec une sélection, ainsi que
six contrôles de recherche (nom, absence de résultat et cumul des filtres).
Les exemples de validation utilisent le visa `113336` et l'UUID
`f4bab825-8ea1-65ea-9688-d6d089bfb09a` ; ils doivent exister sur l'instance cible.
Aucun résultat métier n'est sauvegardé. `METABASE_API_KEY` reste hors Git.
Sans `--check`, le script retrouve collection, dashboards et questions par
leur nom exact ; une ambiguïté arrête la publication. Réutiliser les noms permet
une mise à jour sans duplication. Les cartes ajoutées manuellement restent
présentes. Les données métier ne sont jamais modifiées.

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

## Ajouts manuels de réalisateurs et autres crédits

`fnl_credit_holders` inclut les personnes présentes uniquement dans `credit_holders`.
Les champs manuels non vides priment sur les valeurs issues du scraping ; un champ
vide ne supprime pas une valeur existante. Les identifiants doivent être des UUID
cohérents avec les personnes existantes. Une correction ne rapproche pas des
homonymes et ne fusionne pas deux UUID automatiquement.

`fnl_film_credits` réunit les crédits scrapés et `int_fix_film_credits` avec une
association unique par `(film_id, role_id, credit_holder_id)`. Une ligne manuelle
est un ajout, pas une demande de remplacement ou de suppression. Le film et le
rôle doivent déjà exister ; une nouvelle personne peut être ajoutée dans
`credit_holders` pendant la même synchronisation Airbyte. Les tests vérifient les
trois références ainsi que la conservation de chaque correction.

Les deux stagings concernés acceptent tous les auteurs, y compris Hugo Laurens.
Ils excluent explicitement les lignes de démonstration observées : la personne
`000a676c-8ef7-5b14-8a67-9431ceeb933e` nommée `Example Example`, et l’association
film `0016b072-7ad8-f224-cfd7-053b56ff2720`, rôle
`d894803c-210d-2b5b-6e7e-50f2d418bfcf`, personne
`d8f8d53c-51b8-f89b-1a8d-da48da142694`, datée du 25/04/2026 par Hugo Laurens.
Les filtres des autres onglets de correction ne sont pas modifiés.
Les dates et auteurs doivent être renseignés. Les valeurs vides des champs de
personne sont normalisées en NULL avant l’application des corrections.

`CREDIT_D_IMPOT` reconnaît `X` et `OUI`, sans distinction de casse et après
suppression des espaces extérieurs. Le code `D`, dont le sens reste à confirmer,
est conservé comme valeur inconnue (`NULL`), et non assimilé à une absence d’aide.

### Vérifications

Les tests singuliers contrôlent l’unicité des crédits, les visas Allociné et la
conservation des ajouts manuels. Les tests de schéma contrôlent les références et
l’unicité des personnes et films. Les tests SQL de régression utilisent des CTE
fictives en transaction `READ ONLY`, sans création de schéma ni écriture :

```bash
DBT_TEST_SSH=<alias-ssh> DBT_TEST_DATABASE=<base-postgresql> \
  ingestion/dbt/.venv-dbt/bin/python -m unittest discover \
  -s tests/ingestion -p test_dbt_manual_recovery.py -v
```

Le compte SSH doit permettre `sudo -n -u postgres psql`. La base doit disposer de
l’extension `unaccent`, utilisée par le modèle CNC. Sans `DBT_TEST_SSH`, ces tests
sont ignorés explicitement. Ils couvrent les ajouts, les overrides, les doublons,
les lignes exemples, les corrections de Hugo, les reprises après erreur et les
codes de crédit d’impôt. Ils ne remplacent pas un `dbt build` complet avant livraison.

## Date et heure des mises à jour GSheet

Les 12 stagings qui lisent `UPDATED_DATE` utilisent la macro commune
`gsheet_updated_timestamp`. Le nom de colonne dbt `updated_date` reste inchangé,
mais son type devient `timestamp without time zone` au lieu de `date`.
Cela couvre `films`, `id_matching` et les dix sources de corrections.
Aucune colonne `TIME` supplémentaire n’est nécessaire.

Format recommandé dans la cellule : **`13/11/2026 15:42:08`**, soit
`DD/MM/YYYY HH:MM:SS` avec une heure sur 24 heures. Les valeurs avec heures et
minutes seules sont acceptées. Les anciennes dates seules restent valides et
valent minuit. Les dates ISO `YYYY-MM-DD`, avec la même heure facultative, sont
également acceptées. Les espaces extérieurs sont supprimés ; une cellule vide
est convertie en NULL. Une date impossible ou un format non pris en charge fait
échouer la conversion, sans ignorer silencieusement l’heure.

Conserver le même fuseau de référence, Europe/Paris, dans tous les GSheets :
la valeur est une heure locale, sans conversion de fuseau dans dbt. Airbyte doit
continuer à transmettre une chaîne, pas un numéro de série de date Google Sheets.
Les dates de naissance et de nomination restent des dates, sans heure.

Les dix modèles `int_fix_*` classent les corrections par date et heure
complètes, puis par date d’extraction Airbyte et identifiant de ligne Airbyte
pour départager les égalités. Les valeurs NULL sont classées en dernier.
L’ordre physique des lignes n’est pas utilisé. Deux corrections contradictoires
avec le même horodatage restent à éviter : les métadonnées techniques ne
traduisent pas l’intention métier et peuvent changer après une nouvelle sync.
Les modèles de films et de matching ne gagnent pas de déduplication supplémentaire.

Déployer le code avant de modifier le format des GSheets, puis reconstruire les
stagings et leurs dépendances via le pipeline complet. Le parsing dbt et les
tests SQL vérifient les anciennes dates, les heures/minutes/secondes, les dates
invalides et la priorité des corrections indépendamment de leur ordre d’entrée.

## Suivi des données par visa CNC dans Metabase

Le dashboard **Suivi des données par visa CNC**, dans **Cinestats 50/50 - Operations**,
utilise la connexion `cinestats-ops-db`. Son filtre obligatoire **Visa CNC** vaut
`144246` par défaut. Chaque carte reçoit ce filtre ; changer le visa actualise
l'ensemble du suivi.

Les sections exposent la ligne `raw.films` synchronisée, toutes les lignes de
`raw.id_matching` correspondantes, le dernier essai Allociné tous statuts, le
dernier succès, les modèles staging et intermédiaires, les corrections manuelles,
les films et affiches finaux, les crédits avec leurs personnes et rôles, les genres,
les financements, les enrichissements Mubi transformés et la quarantaine liée aux
identifiants Allociné courants ou historiques. Les détails champ/valeur exposent
chaque colonne disponible, y compris les métadonnées. Les 30 essais les plus récents
complètent la lecture de l'état courant.

**Sémantique de « latest » :** les tables Airbyte sont leur snapshot courant ; elles
ne prouvent pas le contenu actuel du GSheet ni le fichier CNC originel. Les tables
dbt reflètent leur dernière reconstruction. Le dernier essai et le dernier succès
sont classés par `extracted_at DESC NULLS LAST`, puis `run_id` et `record_hash`
décroissants, comme le staging pour les succès. Les doublons de matching restent
visibles. Les champs `NULL` et les associations absentes ne sont pas remplacés par
le legacy. La concordance des identifiants ne prouve pas l'identité de l'œuvre.

Pour #46, contrôler la fiche confirmée, le format long/court, la date, les genres
et la réalisation. Le dashboard ne clôture pas le ticket automatiquement.

Vérifier les requêtes sur 144246 puis publier ou actualiser le dashboard :

```bash
python3 infra/data/metabase-visa-lineage.py --env-file ingestion/.env --check
python3 infra/data/metabase-visa-lineage.py --env-file ingestion/.env
```

La clé `METABASE_API_KEY` reste dans l'environnement ou le fichier `.env` explicite.
Le script vérifie toutes les requêtes avant publication. Il retrouve dashboard et
questions par nom dans Operations et conserve les cartes manuelles. Les noms doivent
rester uniques. Seules les descriptions, questions et dispositions Metabase sont
modifiées ; la consultation ne déclenche aucune ingestion. L'accès dépend des
permissions de la collection Operations, sans partage public créé par ce script.
Les droits de sa sous-collection Trigger se contrôlent séparément.
