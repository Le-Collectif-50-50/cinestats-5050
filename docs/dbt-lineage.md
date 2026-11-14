# Lineage dbt — ingestion RIC

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

Dépendances déclarées dans le projet dbt, des sources vers les modèles consommateurs.
[Version du code analysée](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78).

17 sources, 45 modèles, 0 seeds, 0 snapshots ; 66 dépendances directes.

Généré avec `dbt parse` puis `scripts/generate_dbt_lineage.py`. Aucune connexion à PostgreSQL. Les flèches suivent les appels `ref()` et `source()` du manifest ; les références SQL écrites en dur ne sont pas déduites.

Ce document décrit les dépendances entre relations, pas entre colonnes. Il ne prouve ni la présence des tables en base, ni le succès des traitements. Les tests, analyses, macros, modèles désactivés et traitements externes Airbyte/Prefect/scraping sont hors graphe.

## Lineage dbt complet

Cette vue rassemble toutes les relations actives du manifest, y compris celles sans dépendance. Suivre les flèches de gauche à droite pour parcourir les chaînes des sources brutes jusqu’aux modèles finaux et opérationnels. Les cadres regroupent les relations par schéma ; les sources brutes sont arrondies.

```mermaid
flowchart LR
  subgraph s0["raw"]
    n45(["raw.agreement_cnc"])
    n46(["raw.allocine_data"])
    n47(["raw.award_nominations"])
    n48(["raw.countries"])
    n49(["raw.credit_holders"])
    n50(["raw.credit_holders_genre"])
    n51(["raw.festival_awards"])
    n52(["raw.festivals"])
    n53(["raw.film_country_budget_allocation"])
    n54(["raw.film_credits"])
    n55(["raw.film_genres"])
    n56(["raw.films"])
    n57(["raw.genres"])
    n58(["raw.id_matching"])
    n59(["raw.mubi_festival_films"])
    n60(["raw.mubi_film_awards"])
    n61(["raw.roles"])
  end
  subgraph s1["staging"]
    n28["staging.stg_allocine_films"]
    n29["staging.stg_cnc_films"]
    n30["staging.stg_credit_holders_genre"]
    n31["staging.stg_fix_award_nomination"]
    n32["staging.stg_fix_countries"]
    n33["staging.stg_fix_credit_holders"]
    n34["staging.stg_fix_festival_awards"]
    n35["staging.stg_fix_festivals"]
    n36["staging.stg_fix_film_country_budget_allocation"]
    n37["staging.stg_fix_film_credits"]
    n38["staging.stg_fix_film_genres"]
    n39["staging.stg_fix_genres"]
    n40["staging.stg_fix_roles"]
    n41["staging.stg_id_matching"]
    n42["staging.stg_mubi_festival_films"]
    n43["staging.stg_mubi_film_awards"]
  end
  subgraph s2["intermediate"]
    n9["intermediate.int_allocine_films"]
    n10["intermediate.int_cnc_films"]
    n11["intermediate.int_credit_holders_genre"]
    n12["intermediate.int_credit_holders_role"]
    n13["intermediate.int_film_country_budget_allocation"]
    n14["intermediate.int_film_genres"]
    n15["intermediate.int_fix_award_nomination"]
    n16["intermediate.int_fix_countries"]
    n17["intermediate.int_fix_credit_holders"]
    n18["intermediate.int_fix_festival_awards"]
    n19["intermediate.int_fix_festivals"]
    n20["intermediate.int_fix_film_country_budget_allocation"]
    n21["intermediate.int_fix_film_credits"]
    n22["intermediate.int_fix_film_genres"]
    n23["intermediate.int_fix_genres"]
    n24["intermediate.int_fix_roles"]
    n25["intermediate.int_id_matching"]
    n26["intermediate.int_mubi_festival_films"]
    n27["intermediate.int_mubi_film_awards"]
  end
  subgraph s3["fnl"]
    n1["fnl.fnl_credit_holders"]
    n2["fnl.fnl_film_country_budget_allocation"]
    n3["fnl.fnl_film_credits"]
    n4["fnl.fnl_film_genre"]
    n5["fnl.fnl_film_posters"]
    n6["fnl.fnl_films"]
    n7["fnl.fnl_genre"]
    n8["fnl.fnl_role"]
  end
  subgraph s4["ops"]
    n0["ops.film_credits_unmatched"]
    n44["ops.v_allocine_pipeline_status"]
  end
  n6 --> n5
  n9 --> n6
  n10 --> n6
  n11 --> n1
  n12 --> n0
  n12 --> n1
  n12 --> n3
  n12 --> n8
  n13 --> n2
  n13 --> n6
  n14 --> n4
  n14 --> n7
  n17 --> n1
  n20 --> n2
  n21 --> n3
  n22 --> n4
  n23 --> n7
  n25 --> n5
  n25 --> n6
  n25 --> n26
  n25 --> n27
  n28 --> n0
  n28 --> n5
  n28 --> n9
  n28 --> n12
  n28 --> n14
  n28 --> n44
  n29 --> n10
  n29 --> n13
  n29 --> n14
  n30 --> n11
  n31 --> n15
  n32 --> n16
  n33 --> n17
  n34 --> n18
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n9
  n41 --> n10
  n41 --> n12
  n41 --> n13
  n41 --> n14
  n41 --> n25
  n42 --> n26
  n43 --> n26
  n43 --> n27
  n46 --> n28
  n47 --> n31
  n48 --> n32
  n49 --> n33
  n50 --> n30
  n51 --> n34
  n52 --> n35
  n53 --> n36
  n54 --> n37
  n55 --> n38
  n56 --> n29
  n57 --> n39
  n58 --> n41
  n59 --> n42
  n60 --> n43
  n61 --> n40
```

## Vues détaillées par schéma

<details>
<summary>Afficher les diagrammes par schéma consommateur</summary>

Chaque diagramme montre les relations du schéma et leurs parents directs. Une relation peut donc apparaître dans plusieurs diagrammes. Les sources brutes sont arrondies ; les transformations sont rectangulaires.

### fnl

```mermaid
flowchart LR
  n1["fnl.fnl_credit_holders"]
  n2["fnl.fnl_film_country_budget_allocation"]
  n3["fnl.fnl_film_credits"]
  n4["fnl.fnl_film_genre"]
  n5["fnl.fnl_film_posters"]
  n6["fnl.fnl_films"]
  n7["fnl.fnl_genre"]
  n8["fnl.fnl_role"]
  n9["intermediate.int_allocine_films"]
  n10["intermediate.int_cnc_films"]
  n11["intermediate.int_credit_holders_genre"]
  n12["intermediate.int_credit_holders_role"]
  n13["intermediate.int_film_country_budget_allocation"]
  n14["intermediate.int_film_genres"]
  n17["intermediate.int_fix_credit_holders"]
  n20["intermediate.int_fix_film_country_budget_allocation"]
  n21["intermediate.int_fix_film_credits"]
  n22["intermediate.int_fix_film_genres"]
  n23["intermediate.int_fix_genres"]
  n25["intermediate.int_id_matching"]
  n28["staging.stg_allocine_films"]
  n6 --> n5
  n9 --> n6
  n10 --> n6
  n11 --> n1
  n12 --> n1
  n12 --> n3
  n12 --> n8
  n13 --> n2
  n13 --> n6
  n14 --> n4
  n14 --> n7
  n17 --> n1
  n20 --> n2
  n21 --> n3
  n22 --> n4
  n23 --> n7
  n25 --> n5
  n25 --> n6
  n28 --> n5
```

### intermediate

```mermaid
flowchart LR
  n9["intermediate.int_allocine_films"]
  n10["intermediate.int_cnc_films"]
  n11["intermediate.int_credit_holders_genre"]
  n12["intermediate.int_credit_holders_role"]
  n13["intermediate.int_film_country_budget_allocation"]
  n14["intermediate.int_film_genres"]
  n15["intermediate.int_fix_award_nomination"]
  n16["intermediate.int_fix_countries"]
  n17["intermediate.int_fix_credit_holders"]
  n18["intermediate.int_fix_festival_awards"]
  n19["intermediate.int_fix_festivals"]
  n20["intermediate.int_fix_film_country_budget_allocation"]
  n21["intermediate.int_fix_film_credits"]
  n22["intermediate.int_fix_film_genres"]
  n23["intermediate.int_fix_genres"]
  n24["intermediate.int_fix_roles"]
  n25["intermediate.int_id_matching"]
  n26["intermediate.int_mubi_festival_films"]
  n27["intermediate.int_mubi_film_awards"]
  n28["staging.stg_allocine_films"]
  n29["staging.stg_cnc_films"]
  n30["staging.stg_credit_holders_genre"]
  n31["staging.stg_fix_award_nomination"]
  n32["staging.stg_fix_countries"]
  n33["staging.stg_fix_credit_holders"]
  n34["staging.stg_fix_festival_awards"]
  n35["staging.stg_fix_festivals"]
  n36["staging.stg_fix_film_country_budget_allocation"]
  n37["staging.stg_fix_film_credits"]
  n38["staging.stg_fix_film_genres"]
  n39["staging.stg_fix_genres"]
  n40["staging.stg_fix_roles"]
  n41["staging.stg_id_matching"]
  n42["staging.stg_mubi_festival_films"]
  n43["staging.stg_mubi_film_awards"]
  n25 --> n26
  n25 --> n27
  n28 --> n9
  n28 --> n12
  n28 --> n14
  n29 --> n10
  n29 --> n13
  n29 --> n14
  n30 --> n11
  n31 --> n15
  n32 --> n16
  n33 --> n17
  n34 --> n18
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n9
  n41 --> n10
  n41 --> n12
  n41 --> n13
  n41 --> n14
  n41 --> n25
  n42 --> n26
  n43 --> n26
  n43 --> n27
```

### ops

```mermaid
flowchart LR
  n0["ops.film_credits_unmatched"]
  n12["intermediate.int_credit_holders_role"]
  n28["staging.stg_allocine_films"]
  n44["ops.v_allocine_pipeline_status"]
  n12 --> n0
  n28 --> n0
  n28 --> n44
```

### staging

```mermaid
flowchart LR
  n28["staging.stg_allocine_films"]
  n29["staging.stg_cnc_films"]
  n30["staging.stg_credit_holders_genre"]
  n31["staging.stg_fix_award_nomination"]
  n32["staging.stg_fix_countries"]
  n33["staging.stg_fix_credit_holders"]
  n34["staging.stg_fix_festival_awards"]
  n35["staging.stg_fix_festivals"]
  n36["staging.stg_fix_film_country_budget_allocation"]
  n37["staging.stg_fix_film_credits"]
  n38["staging.stg_fix_film_genres"]
  n39["staging.stg_fix_genres"]
  n40["staging.stg_fix_roles"]
  n41["staging.stg_id_matching"]
  n42["staging.stg_mubi_festival_films"]
  n43["staging.stg_mubi_film_awards"]
  n46(["raw.allocine_data"])
  n47(["raw.award_nominations"])
  n48(["raw.countries"])
  n49(["raw.credit_holders"])
  n50(["raw.credit_holders_genre"])
  n51(["raw.festival_awards"])
  n52(["raw.festivals"])
  n53(["raw.film_country_budget_allocation"])
  n54(["raw.film_credits"])
  n55(["raw.film_genres"])
  n56(["raw.films"])
  n57(["raw.genres"])
  n58(["raw.id_matching"])
  n59(["raw.mubi_festival_films"])
  n60(["raw.mubi_film_awards"])
  n61(["raw.roles"])
  n46 --> n28
  n47 --> n31
  n48 --> n32
  n49 --> n33
  n50 --> n30
  n51 --> n34
  n52 --> n35
  n53 --> n36
  n54 --> n37
  n55 --> n38
  n56 --> n29
  n57 --> n39
  n58 --> n41
  n59 --> n42
  n60 --> n43
  n61 --> n40
```

</details>

## Inventaire et dépendances directes

Les liens ouvrent les définitions à la version du code analysée.

| Relation | Type | Matérialisation | Parents directs |
| --- | --- | --- | --- |
| [ops.film_credits_unmatched](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/ops/film_credits_unmatched.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_credit_holders.sql) | model | table | [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql), [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) |
| [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql) | model | table | [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql), [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) |
| [fnl.fnl_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_film_credits.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) |
| [fnl.fnl_film_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_film_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) |
| [fnl.fnl_film_posters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_film_posters.sql) | model | view | [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_films.sql) | model | table | [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_allocine_films.sql), [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_cnc_films.sql), [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_id_matching.sql) |
| [fnl.fnl_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_genres.sql) |
| [fnl.fnl_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/fnl/fnl_role.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) |
| [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_allocine_films.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_cnc_films.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql) | model | view | [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) |
| [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_film_genres.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_award_nomination.sql) | model | view | [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) |
| [intermediate.int_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_countries.sql) | model | view | [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_countries.sql) |
| [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) | model | view | [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) |
| [intermediate.int_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_festival_awards.sql) | model | view | [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) |
| [intermediate.int_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_festivals.sql) | model | view | [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_festivals.sql) |
| [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) | model | view | [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) |
| [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) | model | view | [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_credits.sql) |
| [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) | model | view | [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_genres.sql) |
| [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_genres.sql) | model | view | [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_genres.sql) |
| [intermediate.int_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_fix_roles.sql) | model | view | [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_roles.sql) |
| [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_id_matching.sql) | model | view | [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_mubi_festival_films.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_mubi_festival_films.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [intermediate.int_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_mubi_film_awards.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql) | model | table | [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_cnc_films.sql) | model | table | [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) | model | table | [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) | model | table | [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_countries.sql) | model | table | [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) | model | table | [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) | model | table | [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_festivals.sql) | model | table | [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) | model | table | [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_credits.sql) | model | table | [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_film_genres.sql) | model | table | [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_genres.sql) | model | table | [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_fix_roles.sql) | model | table | [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_id_matching.sql) | model | table | [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_mubi_festival_films.sql) | model | table | [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) | model | table | [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) |
| [ops.v_allocine_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/ops/v_allocine_pipeline_status.sql) | model | table | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [raw.agreement_cnc](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/e74eb57977702e64282f87aa6fa8c6fc4f58ac78/ingestion/dbt/models/sources.yml) | source | — | — |

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | État généré depuis la version du code liée ci-dessus. |

Les versions précédentes restent disponibles dans l’historique Git de `docs/dbt-lineage.md` sur `main`.
