# Scraping Mubi — flux piloté par le référentiel CNC

## Metadata du document

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-17

**Status:** actif

### Historique du document

| #   | Date       | Auteur        | Observations                          |
| --- | ---------- | ------------- | ------------------------------------- |
| 5 | 2026-11-17 | Joel Teixeira | Lots palmarès/éditions bornés en volume et durée, reprise persistante et publication après drainage. |
| 1   | 2026-06-25 | Joel Teixeira | Flux Mubi restreint aux films du CNC  |
| 2   | 2026-10-06 | Joel Teixeira | Compte Postgres scraper dédié et SSL configuré par environnement |
| 4 | 2026-11-16 | Joel Teixeira | Reprise persistante des éditions, performances navigateur, ciblage et parcours Airbyte/Mubi/dbt depuis Metabase (#83). |
| 3 | 2026-11-13 | Joel Teixeira | Déploiement manuel lancer-scrapping-mubi et paramètre max_films=10 transmis au CLI. |

Job de scraping Mubi **piloté par l'entrée** (input-driven), en alternative au job de découverte `ingestion/scraping/mubi/`.

Objectif : partir des films du référentiel CNC et limiter l'exploration aux éditions de festivals liées à leurs palmarès. La phase A ne collecte que ces films ; la phase B conserve tous les films des sélections concernées, y compris ceux absents du référentiel CNC. Son volume peut donc dépasser le nombre de films CNC demandés.

## Différence avec le job `mubi/`

| | `mubi/` (découverte) | `mubi_cnc/` (ce job) |
| --- | --- | --- |
| Pilotage | Crawl de tous les festivals Mubi | Liste `raw.id_matching` (films CNC) |
| Point d'entrée par film | Pages de festivals | `ID_MUBI` numérique → page du film |
| Volume | Très élevé | Borné aux films CNC |
| Tables de sortie | `raw.mubi_festival_films`, `raw.mubi_film_awards` | **Identiques** |

Les deux jobs écrivent dans les **mêmes tables** avec les **mêmes colonnes** ; les modèles dbt en aval sont inchangés. La déduplication par `record_hash` évite de réinsérer le même snapshot. Une nouvelle tentative possède un nouveau run/horodatage et reste historisée ; dbt conserve le dernier snapshot réussi au grain film ou page.

## Ce que fait la source

Deux phases séquentielles dans le parcours Prefect. Le CLI permet aussi d'exécuter un seul lot d'une phase.

**Phase A — Palmarès par film CNC**

Lit `raw.id_matching` et récupère les `ID_MUBI` non nuls (les films CNC référencés sur Mubi). Pour chaque film **non encore traité**, charge `https://mubi.com/fr/films/{ID_MUBI}/awards` (Mubi redirige l'URL par identifiant numérique vers l'URL à slug). Les récompenses sont lues depuis le tableau structuré `pageProps.awards` de la payload Next.js `__NEXT_DATA__` (plus robuste que les sélecteurs `css-*`) : chaque entrée porte `year`, `status`, `full_display_text`, et l'événement (`industry_event`) avec son `name`, son `slug` et son `type`. Écrit un enregistrement par récompense dans `raw.mubi_film_awards`, en réutilisant le même découpage `(year, distinction, award)` que le job de découverte. Collecte au passage l'ensemble des éditions `(festival_slug, year)` dont l'événement est de type `festival`.

**Phase B — Films en sélection des éditions concernées**

Scrape uniquement les éditions `(festival_slug, year)` collectées en Phase A (et non tous les festivals × toutes les années). Pour chaque édition non encore traitée, pagine `mubi.com/fr/awards-and-festivals/{slug}?page=N&year=Y` avec le même parseur HTML que le job de découverte (`extract_festival_edition_all_films`). Écrit un enregistrement par film dans `raw.mubi_festival_films`.

## Langue / locale (anglais vs français)

Le contenu localisé de Mubi (mot de distinction `Lauréat`/`Winner`, intitulé du prix, nom du festival) **dépend de la locale de l'URL**. Pour rester cohérent avec les lignes déjà écrites par le job `mubi/` dans les mêmes tables, ce job force la locale **`/fr/`** : `distinction`, `award` et `festival` sont donc en français.

Le scrape des éditions en Phase B est piloté par `industry_event.slug` (ex. `cannes`, `oscars`), qui est **invariant par langue**, jamais par le nom affiché. Figer la locale assure la cohérence des libellés. Le `record_hash` inclut aussi le run et l'horodatage : il ne reste pas stable entre deux tentatives.

## Déduplication

Trois niveaux empêchent re-scraping et lignes dupliquées :

1. **Skip incrémental (Phase A)** : un film dont l'`ID_MUBI` figure déjà dans `raw.mubi_film_awards` avec un statut complété (`success`/`no_awards`) n'est pas re-scrapé. Les statuts `error`/`blocked` ne sont pas complétés et seront réessayés au prochain run.
2. **Skip incrémental (Phase B)** : une édition `(festival_slug, year, page)` déjà présente avec un statut complété (`success`/`empty`) est ignorée ; la borne « page vide » stoppe la pagination. Au sein d'un run, chaque édition n'est scrapée qu'une fois même si plusieurs films CNC y renvoient.
3. **Dédup à l'insertion** : avant insertion, tout enregistrement dont le `record_hash` (SHA-256 du contenu) existe déjà dans la table cible — ou apparaît deux fois dans le même lot — est écarté. Le hash inclut run et horodatage : une nouvelle tentative n’est pas éliminée au seul motif que son contenu métier est identique.

## Contrat de sortie

Identique au job `mubi/`. Voir `ingestion/scraping/mubi/README.md` pour le détail des colonnes de `raw.mubi_festival_films` et `raw.mubi_film_awards`. Note : `festival_name` est renseigné avec le `festival_slug` (le nom affiché localisé n'est pas requis en aval) et `page_num` reflète la pagination de l'édition.

## Configuration

Fichier de référence : `ingestion/scraping/mubi_cnc/config.json`.

Champs spécifiques à ce job :

| Champ | Description |
| --- | --- |
| `input_schema` / `input_table` | Table de référence CNC (défaut `raw.id_matching`) |
| `input_mubi_id_column` | Colonne portant l'identifiant Mubi numérique (défaut `ID_MUBI`) |
| `scrape_limit` | Borne le nombre de films CNC traités en Phase A (tests). Le déploiement Prefect impose 10 par défaut, surchargeable par `max_films`. |

Les autres champs (`output_schema`, tables de sortie, délais, retry, navigateur) sont identiques au job `mubi/`.

Les connexions PostgreSQL utilisent `SCRAPER_POSTGRES_USER`, `SCRAPER_POSTGRES_PASSWORD` et `POSTGRES_SSLMODE`. Voir `ingestion/README.md` pour créer le rôle dédié et appliquer ses droits dans `raw`.

## Commandes

```bash
# Schéma de configuration
docker compose -f ingestion/docker-compose.yml exec prefect-worker \
  python3 /app/ingestion/scraping/mubi_cnc/main.py spec

# Connectivité + présence de la table d'entrée CNC
docker compose -f ingestion/docker-compose.yml exec prefect-worker \
  python3 /app/ingestion/scraping/mubi_cnc/main.py check \
  --config /app/ingestion/scraping/mubi_cnc/config.json

# Un lot de dix films, sans collecte de festivals
docker compose -f ingestion/docker-compose.yml exec prefect-worker \
  python3 -u /app/ingestion/scraping/mubi_cnc/main.py sync \
  --config /app/ingestion/scraping/mubi_cnc/config.json --phase awards --limit 10

# Un lot de 25 pages candidates de festivals
docker compose -f ingestion/docker-compose.yml exec prefect-worker \
  python3 -u /app/ingestion/scraping/mubi_cnc/main.py sync \
  --config /app/ingestion/scraping/mubi_cnc/config.json --phase festivals --page-limit 25
```

Pour un test limité, utiliser `config-debug.json` (`scrape_limit` réduit, `verbose: true`).

## Limites importantes

1. Le job ne peut atteindre que les films CNC dont `ID_MUBI` est renseigné dans `id_matching`. Les films sans `ID_MUBI` ne sont pas scrapés (par conception).
2. La résolution par identifiant numérique et l'extraction des récompenses reposent sur la structure `__NEXT_DATA__` de Next.js. Si Mubi change son frontend, ces mécanismes peuvent nécessiter une mise à jour.
3. Le rapprochement avec un film déjà scrapé par le job `mubi/` se fait sur `mubi_id`. Une ancienne ligne avec `mubi_id` nul ne sera pas reconnue comme traitée ; le film sera re-scrapé (les nouvelles lignes, porteuses du `mubi_id`, sont conservées par `stg_mubi_film_awards` qui ne garde que le dernier run par `film_link`).
4. Le scraping des éditions (Phase B) utilise toujours les sélecteurs HTML `css-*` de `mubi_scraper.py`, susceptibles d'être modifiés par Mubi.

## Déploiement Prefect

`Recuperer les donnees Mubi (CNC)/lancer-scrapping-mubi` reste manuel, sans
calendrier ni lancement au démarrage. Il synchronise désormais Airbyte, exécute
des lots séquentiels CNC, puis `dbt build --select +tag:phase2`. Cela publie les modèles
Mubi staging/intermediate et le suivi `ops`, sans créer de nouvelles tables
finales métier. Le CLI `sync` seul ne lance ni Airbyte ni dbt.

`max_films=10` borne les nouveaux ID Mubi de phase A. Un ID partagé valide est
collecté une seule fois. `batch_size=10` répartit ce volume dans des sous-flows
**Collecter les palmarès Mubi par lot**. Les éditions sont ensuite drainées par
des sous-flows **Collecter les éditions Mubi par lot**, avec
`festival_page_limit=25` pages candidates au maximum. Ces sous-flows sont des
runs Prefect séparés, enfants du parcours principal ; aucun déploiement ni
calendrier supplémentaire n'est créé.

Chaque lot dispose de `job_timeout_seconds=900` secondes de collecte au maximum.
Un garde-fou termine son groupe de processus après 60 secondes supplémentaires
de nettoyage, puis force l'arrêt après cinq secondes si nécessaire. Les requêtes
PostgreSQL des lots sont limitées à 30 secondes et l'attente des verrous à dix
secondes. Un verrou consultatif PostgreSQL empêche deux lots bornés Mubi de
collecter simultanément. Le nombre total de pages n'est pas prédit : une page
vide supprime les suivantes de la file.

La fin du budget de collecte conserve les checkpoints et permet un prochain lot.
Le parcours contrôle que la file diminue ; une absence de progression, une erreur
ou un blocage arrête le parcours avant dbt. Le parent peut durer plusieurs heures
si de nombreuses éditions restent à traiter, mais chaque sous-job est borné.
dbt ne démarre qu'après les lots de films demandés et le drainage des éditions.
`visa_number` cible explicitement un visa et ramène la limite à un ID.
`force_rescrape=true` exige ce visa ; il rejoue son palmarès sans supprimer
l’historique. Les pages de festivals déjà complétées restent ignorées.

```bash
python3 ingestion/scraping/mubi_cnc/main.py sync \
  --config ingestion/scraping/mubi_cnc/config.json --phase awards --visa 134877 --force --limit 1
```

Le visa absent, une correspondance ambiguë ou un ID manquant/invalide font échouer
le ciblage. Les erreurs techniques et blocages sont persistés puis signalés par
un code de sortie non nul : le flow ne publie pas dbt et la demande échoue.
Un film sans palmarès n’est confirmé `no_awards` que si l’ID de la page correspond
à l’entrée et que le tableau structuré `awards` est présent et vide.

## Reprise et performances

Le CLI `--phase awards` traite uniquement les films ; `--phase festivals` reprend
les éditions référencées par les derniers succès déjà enregistrés. Répéter la
même commande reprend les films/pages non terminés. `--job-timeout-seconds`
accepte un entier de 1 à 900. Le chemin historique sans `--phase` (`all`) reste
disponible pour compatibilité ; utiliser les phases explicites ou Prefect pour
bénéficier des lots bornés.

Le parcours Prefect attend la fin d'un lot avant le suivant, sans créneaux fixes.
Après interruption du parent, relancer le même déploiement : les succès déjà
persistés et les bornes de pages vides évitent de recommencer la collecte.

Chaque film et chaque page sont enregistrés avant le suivant. Les colonnes
additives `event_slug` et `event_type` de `raw.mubi_film_awards` conservent les
éditions à consulter. Pour une table existante, appliquer
`infra/data/2026-11-16-mubi-cnc-events.sql` avec son propriétaire (`dbt_user` en
production). Le scraper restreint n’altère pas cette table ; il signale une
migration manquante. Une nouvelle table inclut les colonnes au bootstrap. Aucune
ligne historique n’est supprimée. Après interruption entre les deux phases,
les éditions du dernier succès des films CNC sont relues même si aucun nouveau
palmarès n’est à traiter. Les lignes historiques dépourvues de ces colonnes ne
permettent pas cette reconstruction : un retraitement ciblé est nécessaire
pour les films concernés. Un nouveau succès sans palmarès remplace les anciennes
références d’éditions pour ce film.

Le connecteur CNC active `lightweight=True` et attend `domcontentloaded` au lieu
de `networkidle`, puis attend explicitement `script#__NEXT_DATA__`. Images, médias, polices et domaines publicitaires filtrés par
le navigateur partagé ne sont pas chargés. Les scripts et contrôles de consentement
restent actifs. La page précédente est fermée avant navigation ; en cas de
fermeture bloquée, la session est remplacée. Ouverture de session : 45 s maximum ;
fermeture de chaque ressource : 5 s ; fetch : 60 s par tentative, trois tentatives
avec backoff 3 puis 6 s. Un retry technique recrée la session. La rotation normale
reste toutes les six requêtes. Les temporisations de courtoisie sont conservées.
Le crawler global n’active pas ces options et reste différé.

Mesure contrôlée du 16 novembre : **57,15 s → 38,09 s** sur le même Browserless,
les trois mêmes pages, dans une session par variante (ouverture et fermeture
comprises). Données extraites identiques : palmarès Mubi 136442, Cannes 2024 page 1
(36 films), page 100 (vide). Réduction observée : **33,4 %**. Ce petit échantillon
ne mesure ni un catalogue entier, ni les retries/blocages, ni Airbyte/dbt.
Un second essai instrumenté donne 51,69 s → 37,94 s (−26,6 %), avec les mêmes
données parsées ; le détail des phases figure dans le rapport de validation.

## Piloter depuis Metabase

Le script `infra/data/metabase-mubi-review.py` crée ou actualise le dashboard
**Scraping Mubi — Suivi CNC** dans Operations. Il utilise le même éditeur que
le dashboard Allociné, avec des questions, filtres et actions propres à Mubi.

```bash
python3 infra/data/metabase-mubi-review.py --env-file ingestion/.env \
  --collection-id 7 --action-model-id 38 --check
python3 infra/data/metabase-mubi-review.py --env-file ingestion/.env \
  --collection-id 7 --action-model-id 38
```

Déployer d’abord les colonnes brutes avec
`infra/data/2026-11-16-mubi-cnc-events.sql`, puis la migration de file `infra/data/ops-ingestion-table.sql`, le
poller et le flow Mubi, puis construire `ops.v_mubi_pipeline_status`. Les anciens
runs doivent être terminés avant de recréer le worker. La migration conserve les
demandes historiques et échoue si plusieurs demandes sont déjà actives : les
résoudre avant migration, sans suppression arbitraire. Le compte Metabase utilise
le modèle de file de la même connexion (`cinestats-ops-db`). Le fichier local
d’état contient seulement les IDs des objets publiés ; le conserver pour une
mise à jour idempotente. Les clés API restent hors Git.

- **Lancer le scraping Mubi** : identité déclarative, motif, nombre maximal
  d’ID Mubi (10 par défaut). Les filtres ne ciblent pas le formulaire.
- **Scraper un visa CNC sur Mubi** : identité, motif, visa et forçage (Non par
  défaut). Saisir le visa CNC, jamais l’ID Mubi.
- Les deux actions attendent le prochain poller (environ cinq minutes), puis
  synchronisent Airbyte, collectent et publient dbt. Le suivi expose attente,
  exécution, réussite ou erreur. Une demande « Terminée » confirme le processus
  et dbt ; chaque film garde son propre statut. Sans film éligible, un lot peut
  publier sans nouvelle collecte.
- Le verrou de demande active est global : ingestion, Allociné et Mubi partagent
  une seule place. Les lancements directs Prefect/CLI contournent cette file :
  les coordonner explicitement et ne pas les superposer à une publication.
- Les filtres visa, titre et ID portent sur la couverture et l’état des films.
  La période porte uniquement sur le graphique des tentatives, en heure de Paris
  (sept jours précédents et aujourd’hui par défaut). Demandes et pages restent hors de ces filtres.
- Couverture : visas pour les IDs absents, ID Mubi distincts pour les films
  traités/en attente/en erreur. Le graphique compte une tentative par run, ID et
  horodatage. Les pages de festivals restent des pages, jamais des films ou prix.
  Aucune somme de prix/événements multi-visas n’est introduite ; voir #82.

Pour corriger une correspondance, suivre la qualification de #78 et conserver
les preuves dans le Sheet. Le dashboard ne valide pas automatiquement l’identité
d’un rapprochement CNC/Mubi.

## Vérifications

```bash
python3 -m pytest tests/ingestion/test_mubi_cnc.py \
  tests/ingestion/test_metabase_allocine.py tests/ingestion/test_prefect_deployments.py
```

`RIC_MUBI_TEST_DB=1` active un test PostgreSQL avec tables temporaires uniquement.
Il vérifie reprise des éditions, ID partagé et verrou inter-sources sans modifier
les tables métier. Vérifier aussi les actions, filtres et permissions Metabase
après publication, puis un petit run réel et les modèles dbt sans cache.

Le [dashboard Mubi de production](https://metabase.cinestats5050.fr/dashboard/12)
propose les deux actions. Les [résultats de validation et détails de livraison](../../../docs/reference/ingestion-validation-mubi-issue-83.md)
consignent les runs terminés, mesures, contrôles et limites de cette mise en service.
