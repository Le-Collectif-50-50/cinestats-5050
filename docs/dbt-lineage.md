# Lineage dbt — ingestion RIC

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-18

**Status:** actif

Dépendances déclarées dans le projet dbt, des sources vers les modèles consommateurs.
[Version du code analysée](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f).

17 sources, 48 modèles, 1 seeds, 0 snapshots ; 74 dépendances directes.

Généré avec `dbt parse` puis `scripts/generate_dbt_lineage.py`. Aucune connexion à PostgreSQL. Les flèches suivent les appels `ref()` et `source()` du manifest ; les références SQL écrites en dur ne sont pas déduites.

Ce document décrit les dépendances entre relations, pas entre colonnes. Il ne prouve ni la présence des tables en base, ni le succès des traitements. Les tests, analyses, macros, modèles désactivés et traitements externes Airbyte/Prefect/scraping sont hors graphe.

## Lineage dbt complet

Cette vue rassemble toutes les relations actives du manifest, y compris celles sans dépendance. Suivre les flèches de gauche à droite pour parcourir les chaînes des sources brutes jusqu’aux modèles finaux et opérationnels. Les cadres regroupent les relations par schéma ; les sources brutes sont arrondies.

```mermaid
flowchart LR
  subgraph s0["raw"]
    n49(["raw.agreement_cnc"])
    n50(["raw.allocine_data"])
    n51(["raw.award_nominations"])
    n52(["raw.countries"])
    n53(["raw.credit_holders"])
    n54(["raw.credit_holders_genre"])
    n55(["raw.festival_awards"])
    n56(["raw.festivals"])
    n57(["raw.film_country_budget_allocation"])
    n58(["raw.film_credits"])
    n59(["raw.film_genres"])
    n60(["raw.films"])
    n61(["raw.genres"])
    n62(["raw.id_matching"])
    n63(["raw.mubi_festival_films"])
    n64(["raw.mubi_film_awards"])
    n65(["raw.roles"])
  end
  subgraph s1["staging"]
    n30["staging.stg_allocine_films"]
    n31["staging.stg_cnc_films"]
    n32["staging.stg_credit_holders_genre"]
    n33["staging.stg_fix_award_nomination"]
    n34["staging.stg_fix_countries"]
    n35["staging.stg_fix_credit_holders"]
    n36["staging.stg_fix_festival_awards"]
    n37["staging.stg_fix_festivals"]
    n38["staging.stg_fix_film_country_budget_allocation"]
    n39["staging.stg_fix_film_credits"]
    n40["staging.stg_fix_film_genres"]
    n41["staging.stg_fix_genres"]
    n42["staging.stg_fix_roles"]
    n43["staging.stg_id_matching"]
    n44["staging.stg_mubi_festival_films"]
    n45["staging.stg_mubi_film_awards"]
  end
  subgraph s2["intermediate"]
    n11["intermediate.int_allocine_films"]
    n12["intermediate.int_cnc_films"]
    n13["intermediate.int_credit_holders_genre"]
    n14["intermediate.int_credit_holders_role"]
    n15["intermediate.int_film_country_budget_allocation"]
    n16["intermediate.int_film_genres"]
    n17["intermediate.int_fix_award_nomination"]
    n18["intermediate.int_fix_countries"]
    n19["intermediate.int_fix_credit_holders"]
    n20["intermediate.int_fix_festival_awards"]
    n21["intermediate.int_fix_festivals"]
    n22["intermediate.int_fix_film_country_budget_allocation"]
    n23["intermediate.int_fix_film_credits"]
    n24["intermediate.int_fix_film_genres"]
    n25["intermediate.int_fix_genres"]
    n26["intermediate.int_fix_roles"]
    n27["intermediate.int_id_matching"]
    n28["intermediate.int_mubi_festival_films"]
    n29["intermediate.int_mubi_film_awards"]
  end
  subgraph s3["fnl"]
    n3["fnl.fnl_credit_holders"]
    n4["fnl.fnl_film_country_budget_allocation"]
    n5["fnl.fnl_film_credits"]
    n6["fnl.fnl_film_genre"]
    n7["fnl.fnl_film_posters"]
    n8["fnl.fnl_films"]
    n9["fnl.fnl_genre"]
    n10["fnl.fnl_role"]
  end
  subgraph s4["ops"]
    n0["ops.allocine_rejected_credits"]
    n1["ops.allocine_rejected_results"]
    n2["ops.film_credits_unmatched"]
    n46["ops.v_allocine_pipeline_status"]
    n47["ops.v_mubi_pipeline_status"]
    n48["ops.allocine_association_rejections"]
  end
  n1 --> n0
  n4 --> n8
  n6 --> n8
  n8 --> n7
  n9 --> n8
  n11 --> n8
  n12 --> n8
  n13 --> n3
  n14 --> n2
  n14 --> n3
  n14 --> n5
  n14 --> n10
  n15 --> n4
  n16 --> n6
  n16 --> n9
  n19 --> n3
  n22 --> n4
  n23 --> n5
  n24 --> n6
  n25 --> n9
  n27 --> n7
  n27 --> n8
  n27 --> n28
  n27 --> n29
  n27 --> n47
  n30 --> n2
  n30 --> n7
  n30 --> n11
  n30 --> n14
  n30 --> n16
  n30 --> n46
  n31 --> n12
  n31 --> n15
  n31 --> n16
  n32 --> n13
  n33 --> n17
  n34 --> n18
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n25
  n42 --> n26
  n43 --> n11
  n43 --> n12
  n43 --> n14
  n43 --> n15
  n43 --> n16
  n43 --> n27
  n44 --> n28
  n45 --> n28
  n45 --> n29
  n48 --> n1
  n48 --> n30
  n50 --> n1
  n50 --> n30
  n51 --> n33
  n52 --> n34
  n53 --> n35
  n54 --> n32
  n55 --> n36
  n56 --> n37
  n57 --> n38
  n58 --> n39
  n59 --> n40
  n60 --> n31
  n61 --> n41
  n62 --> n43
  n63 --> n44
  n64 --> n45
  n64 --> n47
  n65 --> n42
```

## Vues détaillées par schéma

<details>
<summary>Afficher les diagrammes par schéma consommateur</summary>

Chaque diagramme montre les relations du schéma et leurs parents directs. Une relation peut donc apparaître dans plusieurs diagrammes. Les sources brutes sont arrondies ; les transformations sont rectangulaires.

### fnl

```mermaid
flowchart LR
  n3["fnl.fnl_credit_holders"]
  n4["fnl.fnl_film_country_budget_allocation"]
  n5["fnl.fnl_film_credits"]
  n6["fnl.fnl_film_genre"]
  n7["fnl.fnl_film_posters"]
  n8["fnl.fnl_films"]
  n9["fnl.fnl_genre"]
  n10["fnl.fnl_role"]
  n11["intermediate.int_allocine_films"]
  n12["intermediate.int_cnc_films"]
  n13["intermediate.int_credit_holders_genre"]
  n14["intermediate.int_credit_holders_role"]
  n15["intermediate.int_film_country_budget_allocation"]
  n16["intermediate.int_film_genres"]
  n19["intermediate.int_fix_credit_holders"]
  n22["intermediate.int_fix_film_country_budget_allocation"]
  n23["intermediate.int_fix_film_credits"]
  n24["intermediate.int_fix_film_genres"]
  n25["intermediate.int_fix_genres"]
  n27["intermediate.int_id_matching"]
  n30["staging.stg_allocine_films"]
  n4 --> n8
  n6 --> n8
  n8 --> n7
  n9 --> n8
  n11 --> n8
  n12 --> n8
  n13 --> n3
  n14 --> n3
  n14 --> n5
  n14 --> n10
  n15 --> n4
  n16 --> n6
  n16 --> n9
  n19 --> n3
  n22 --> n4
  n23 --> n5
  n24 --> n6
  n25 --> n9
  n27 --> n7
  n27 --> n8
  n30 --> n7
```

### intermediate

```mermaid
flowchart LR
  n11["intermediate.int_allocine_films"]
  n12["intermediate.int_cnc_films"]
  n13["intermediate.int_credit_holders_genre"]
  n14["intermediate.int_credit_holders_role"]
  n15["intermediate.int_film_country_budget_allocation"]
  n16["intermediate.int_film_genres"]
  n17["intermediate.int_fix_award_nomination"]
  n18["intermediate.int_fix_countries"]
  n19["intermediate.int_fix_credit_holders"]
  n20["intermediate.int_fix_festival_awards"]
  n21["intermediate.int_fix_festivals"]
  n22["intermediate.int_fix_film_country_budget_allocation"]
  n23["intermediate.int_fix_film_credits"]
  n24["intermediate.int_fix_film_genres"]
  n25["intermediate.int_fix_genres"]
  n26["intermediate.int_fix_roles"]
  n27["intermediate.int_id_matching"]
  n28["intermediate.int_mubi_festival_films"]
  n29["intermediate.int_mubi_film_awards"]
  n30["staging.stg_allocine_films"]
  n31["staging.stg_cnc_films"]
  n32["staging.stg_credit_holders_genre"]
  n33["staging.stg_fix_award_nomination"]
  n34["staging.stg_fix_countries"]
  n35["staging.stg_fix_credit_holders"]
  n36["staging.stg_fix_festival_awards"]
  n37["staging.stg_fix_festivals"]
  n38["staging.stg_fix_film_country_budget_allocation"]
  n39["staging.stg_fix_film_credits"]
  n40["staging.stg_fix_film_genres"]
  n41["staging.stg_fix_genres"]
  n42["staging.stg_fix_roles"]
  n43["staging.stg_id_matching"]
  n44["staging.stg_mubi_festival_films"]
  n45["staging.stg_mubi_film_awards"]
  n27 --> n28
  n27 --> n29
  n30 --> n11
  n30 --> n14
  n30 --> n16
  n31 --> n12
  n31 --> n15
  n31 --> n16
  n32 --> n13
  n33 --> n17
  n34 --> n18
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n25
  n42 --> n26
  n43 --> n11
  n43 --> n12
  n43 --> n14
  n43 --> n15
  n43 --> n16
  n43 --> n27
  n44 --> n28
  n45 --> n28
  n45 --> n29
```

### ops

```mermaid
flowchart LR
  n0["ops.allocine_rejected_credits"]
  n1["ops.allocine_rejected_results"]
  n2["ops.film_credits_unmatched"]
  n14["intermediate.int_credit_holders_role"]
  n27["intermediate.int_id_matching"]
  n30["staging.stg_allocine_films"]
  n46["ops.v_allocine_pipeline_status"]
  n47["ops.v_mubi_pipeline_status"]
  n48["ops.allocine_association_rejections"]
  n50(["raw.allocine_data"])
  n64(["raw.mubi_film_awards"])
  n1 --> n0
  n14 --> n2
  n27 --> n47
  n30 --> n2
  n30 --> n46
  n48 --> n1
  n50 --> n1
  n64 --> n47
```

### staging

```mermaid
flowchart LR
  n30["staging.stg_allocine_films"]
  n31["staging.stg_cnc_films"]
  n32["staging.stg_credit_holders_genre"]
  n33["staging.stg_fix_award_nomination"]
  n34["staging.stg_fix_countries"]
  n35["staging.stg_fix_credit_holders"]
  n36["staging.stg_fix_festival_awards"]
  n37["staging.stg_fix_festivals"]
  n38["staging.stg_fix_film_country_budget_allocation"]
  n39["staging.stg_fix_film_credits"]
  n40["staging.stg_fix_film_genres"]
  n41["staging.stg_fix_genres"]
  n42["staging.stg_fix_roles"]
  n43["staging.stg_id_matching"]
  n44["staging.stg_mubi_festival_films"]
  n45["staging.stg_mubi_film_awards"]
  n48["ops.allocine_association_rejections"]
  n50(["raw.allocine_data"])
  n51(["raw.award_nominations"])
  n52(["raw.countries"])
  n53(["raw.credit_holders"])
  n54(["raw.credit_holders_genre"])
  n55(["raw.festival_awards"])
  n56(["raw.festivals"])
  n57(["raw.film_country_budget_allocation"])
  n58(["raw.film_credits"])
  n59(["raw.film_genres"])
  n60(["raw.films"])
  n61(["raw.genres"])
  n62(["raw.id_matching"])
  n63(["raw.mubi_festival_films"])
  n64(["raw.mubi_film_awards"])
  n65(["raw.roles"])
  n48 --> n30
  n50 --> n30
  n51 --> n33
  n52 --> n34
  n53 --> n35
  n54 --> n32
  n55 --> n36
  n56 --> n37
  n57 --> n38
  n58 --> n39
  n59 --> n40
  n60 --> n31
  n61 --> n41
  n62 --> n43
  n63 --> n44
  n64 --> n45
  n65 --> n42
```

</details>

## Inventaire et dépendances directes

Les liens ouvrent les définitions à la version du code analysée.

| Relation | Type | Matérialisation | Parents directs |
| --- | --- | --- | --- |
| [ops.allocine_rejected_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/allocine_rejected_credits.sql) | model | view | [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/allocine_rejected_results.sql) |
| [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/allocine_rejected_results.sql) | model | view | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [ops.film_credits_unmatched](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/film_credits_unmatched.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_credit_holders.sql) | model | table | [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql), [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) |
| [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql) | model | table | [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql), [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) |
| [fnl.fnl_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_credits.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) |
| [fnl.fnl_film_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) |
| [fnl.fnl_film_posters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_posters.sql) | model | view | [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_films.sql) | model | table | [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql), [fnl.fnl_film_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_film_genre.sql), [fnl.fnl_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_genre.sql), [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_allocine_films.sql), [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_cnc_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql) |
| [fnl.fnl_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_genres.sql) |
| [fnl.fnl_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/fnl/fnl_role.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) |
| [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_allocine_films.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_cnc_films.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql) | model | view | [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) |
| [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_film_genres.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_award_nomination.sql) | model | view | [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) |
| [intermediate.int_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_countries.sql) | model | view | [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_countries.sql) |
| [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) | model | view | [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) |
| [intermediate.int_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_festival_awards.sql) | model | view | [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) |
| [intermediate.int_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_festivals.sql) | model | view | [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_festivals.sql) |
| [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) | model | view | [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) |
| [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) | model | view | [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_credits.sql) |
| [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) | model | view | [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_genres.sql) |
| [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_genres.sql) | model | view | [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_genres.sql) |
| [intermediate.int_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_fix_roles.sql) | model | view | [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_roles.sql) |
| [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql) | model | view | [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_mubi_festival_films.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_mubi_festival_films.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [intermediate.int_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_mubi_film_awards.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql) | model | table | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_cnc_films.sql) | model | table | [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) | model | table | [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) | model | table | [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_countries.sql) | model | table | [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) | model | table | [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) | model | table | [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_festivals.sql) | model | table | [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) | model | table | [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_credits.sql) | model | table | [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_film_genres.sql) | model | table | [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_genres.sql) | model | table | [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_fix_roles.sql) | model | table | [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_id_matching.sql) | model | table | [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_mubi_festival_films.sql) | model | table | [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) | model | table | [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [ops.v_allocine_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/v_allocine_pipeline_status.sql) | model | table | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [ops.v_mubi_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/ops/v_mubi_pipeline_status.sql) | model | view | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/intermediate/int_id_matching.sql), [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) |
| [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/seeds/allocine_association_rejections.csv) | seed | seed | — |
| [raw.agreement_cnc](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/8d5436630ad4464efc36de4ff7c2199761d2541f/ingestion/dbt/models/sources.yml) | source | — | — |

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-18 | Joel Teixeira | État généré depuis la version du code liée ci-dessus. |

Les versions précédentes restent disponibles dans l’historique Git de `docs/dbt-lineage.md` sur `main`.
