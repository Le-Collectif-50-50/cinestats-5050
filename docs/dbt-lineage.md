# Lineage dbt — ingestion RIC

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-18

**Status:** actif

Dépendances déclarées dans le projet dbt, des sources vers les modèles consommateurs.
[Version du code analysée](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4).

17 sources, 42 modèles, 1 seeds, 0 snapshots ; 65 dépendances directes.

Généré avec `dbt parse` puis `scripts/generate_dbt_lineage.py`. Aucune connexion à PostgreSQL. Les flèches suivent les appels `ref()` et `source()` du manifest ; les références SQL écrites en dur ne sont pas déduites.

Ce document décrit les dépendances entre relations, pas entre colonnes. Il ne prouve ni la présence des tables en base, ni le succès des traitements. Les tests, analyses, macros, modèles désactivés et traitements externes Airbyte/Prefect/scraping sont hors graphe.

## Lineage dbt complet

Cette vue rassemble toutes les relations actives du manifest, y compris celles sans dépendance. Suivre les flèches de gauche à droite pour parcourir les chaînes des sources brutes jusqu’aux modèles finaux et opérationnels. Les cadres regroupent les relations par schéma ; les sources brutes sont arrondies.

```mermaid
flowchart LR
  subgraph s0["raw"]
    n43(["raw.agreement_cnc"])
    n44(["raw.allocine_data"])
    n45(["raw.award_nominations"])
    n46(["raw.countries"])
    n47(["raw.credit_holders"])
    n48(["raw.credit_holders_genre"])
    n49(["raw.festival_awards"])
    n50(["raw.festivals"])
    n51(["raw.film_country_budget_allocation"])
    n52(["raw.film_credits"])
    n53(["raw.film_genres"])
    n54(["raw.films"])
    n55(["raw.genres"])
    n56(["raw.id_matching"])
    n57(["raw.mubi_festival_films"])
    n58(["raw.mubi_film_awards"])
    n59(["raw.roles"])
  end
  subgraph s1["staging"]
    n26["staging.stg_allocine_films"]
    n27["staging.stg_cnc_films"]
    n28["staging.stg_credit_holders_genre"]
    n29["staging.stg_fix_award_nomination"]
    n30["staging.stg_fix_countries"]
    n31["staging.stg_fix_credit_holders"]
    n32["staging.stg_fix_festival_awards"]
    n33["staging.stg_fix_festivals"]
    n34["staging.stg_fix_film_country_budget_allocation"]
    n35["staging.stg_fix_film_credits"]
    n36["staging.stg_fix_roles"]
    n37["staging.stg_id_matching"]
    n38["staging.stg_mubi_festival_films"]
    n39["staging.stg_mubi_film_awards"]
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
    n22["intermediate.int_fix_roles"]
    n23["intermediate.int_id_matching"]
    n24["intermediate.int_mubi_festival_films"]
    n25["intermediate.int_mubi_film_awards"]
  end
  subgraph s3["fnl"]
    n3["fnl.fnl_credit_holders"]
    n4["fnl.fnl_film_country_budget_allocation"]
    n5["fnl.fnl_film_credits"]
    n6["fnl.fnl_film_posters"]
    n7["fnl.fnl_films"]
    n8["fnl.fnl_role"]
  end
  subgraph s4["ops"]
    n0["ops.allocine_rejected_credits"]
    n1["ops.allocine_rejected_results"]
    n2["ops.film_credits_unmatched"]
    n40["ops.v_allocine_pipeline_status"]
    n41["ops.v_mubi_pipeline_status"]
    n42["ops.allocine_association_rejections"]
  end
  n1 --> n0
  n4 --> n7
  n7 --> n6
  n9 --> n7
  n10 --> n7
  n11 --> n3
  n12 --> n2
  n12 --> n3
  n12 --> n5
  n12 --> n8
  n13 --> n4
  n14 --> n7
  n17 --> n3
  n20 --> n4
  n21 --> n5
  n23 --> n6
  n23 --> n7
  n23 --> n24
  n23 --> n25
  n23 --> n41
  n26 --> n2
  n26 --> n6
  n26 --> n9
  n26 --> n12
  n26 --> n14
  n26 --> n40
  n27 --> n10
  n27 --> n13
  n27 --> n14
  n28 --> n11
  n29 --> n15
  n30 --> n16
  n31 --> n17
  n32 --> n18
  n33 --> n19
  n34 --> n20
  n35 --> n21
  n36 --> n22
  n37 --> n9
  n37 --> n10
  n37 --> n12
  n37 --> n13
  n37 --> n14
  n37 --> n23
  n38 --> n24
  n39 --> n24
  n39 --> n25
  n42 --> n1
  n42 --> n26
  n44 --> n1
  n44 --> n26
  n45 --> n29
  n46 --> n30
  n47 --> n31
  n48 --> n28
  n49 --> n32
  n50 --> n33
  n51 --> n34
  n52 --> n35
  n54 --> n27
  n56 --> n37
  n57 --> n38
  n58 --> n39
  n58 --> n41
  n59 --> n36
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
  n6["fnl.fnl_film_posters"]
  n7["fnl.fnl_films"]
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
  n23["intermediate.int_id_matching"]
  n26["staging.stg_allocine_films"]
  n4 --> n7
  n7 --> n6
  n9 --> n7
  n10 --> n7
  n11 --> n3
  n12 --> n3
  n12 --> n5
  n12 --> n8
  n13 --> n4
  n14 --> n7
  n17 --> n3
  n20 --> n4
  n21 --> n5
  n23 --> n6
  n23 --> n7
  n26 --> n6
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
  n22["intermediate.int_fix_roles"]
  n23["intermediate.int_id_matching"]
  n24["intermediate.int_mubi_festival_films"]
  n25["intermediate.int_mubi_film_awards"]
  n26["staging.stg_allocine_films"]
  n27["staging.stg_cnc_films"]
  n28["staging.stg_credit_holders_genre"]
  n29["staging.stg_fix_award_nomination"]
  n30["staging.stg_fix_countries"]
  n31["staging.stg_fix_credit_holders"]
  n32["staging.stg_fix_festival_awards"]
  n33["staging.stg_fix_festivals"]
  n34["staging.stg_fix_film_country_budget_allocation"]
  n35["staging.stg_fix_film_credits"]
  n36["staging.stg_fix_roles"]
  n37["staging.stg_id_matching"]
  n38["staging.stg_mubi_festival_films"]
  n39["staging.stg_mubi_film_awards"]
  n23 --> n24
  n23 --> n25
  n26 --> n9
  n26 --> n12
  n26 --> n14
  n27 --> n10
  n27 --> n13
  n27 --> n14
  n28 --> n11
  n29 --> n15
  n30 --> n16
  n31 --> n17
  n32 --> n18
  n33 --> n19
  n34 --> n20
  n35 --> n21
  n36 --> n22
  n37 --> n9
  n37 --> n10
  n37 --> n12
  n37 --> n13
  n37 --> n14
  n37 --> n23
  n38 --> n24
  n39 --> n24
  n39 --> n25
```

### ops

```mermaid
flowchart LR
  n0["ops.allocine_rejected_credits"]
  n1["ops.allocine_rejected_results"]
  n2["ops.film_credits_unmatched"]
  n12["intermediate.int_credit_holders_role"]
  n23["intermediate.int_id_matching"]
  n26["staging.stg_allocine_films"]
  n40["ops.v_allocine_pipeline_status"]
  n41["ops.v_mubi_pipeline_status"]
  n42["ops.allocine_association_rejections"]
  n44(["raw.allocine_data"])
  n58(["raw.mubi_film_awards"])
  n1 --> n0
  n12 --> n2
  n23 --> n41
  n26 --> n2
  n26 --> n40
  n42 --> n1
  n44 --> n1
  n58 --> n41
```

### staging

```mermaid
flowchart LR
  n26["staging.stg_allocine_films"]
  n27["staging.stg_cnc_films"]
  n28["staging.stg_credit_holders_genre"]
  n29["staging.stg_fix_award_nomination"]
  n30["staging.stg_fix_countries"]
  n31["staging.stg_fix_credit_holders"]
  n32["staging.stg_fix_festival_awards"]
  n33["staging.stg_fix_festivals"]
  n34["staging.stg_fix_film_country_budget_allocation"]
  n35["staging.stg_fix_film_credits"]
  n36["staging.stg_fix_roles"]
  n37["staging.stg_id_matching"]
  n38["staging.stg_mubi_festival_films"]
  n39["staging.stg_mubi_film_awards"]
  n42["ops.allocine_association_rejections"]
  n44(["raw.allocine_data"])
  n45(["raw.award_nominations"])
  n46(["raw.countries"])
  n47(["raw.credit_holders"])
  n48(["raw.credit_holders_genre"])
  n49(["raw.festival_awards"])
  n50(["raw.festivals"])
  n51(["raw.film_country_budget_allocation"])
  n52(["raw.film_credits"])
  n54(["raw.films"])
  n56(["raw.id_matching"])
  n57(["raw.mubi_festival_films"])
  n58(["raw.mubi_film_awards"])
  n59(["raw.roles"])
  n42 --> n26
  n44 --> n26
  n45 --> n29
  n46 --> n30
  n47 --> n31
  n48 --> n28
  n49 --> n32
  n50 --> n33
  n51 --> n34
  n52 --> n35
  n54 --> n27
  n56 --> n37
  n57 --> n38
  n58 --> n39
  n59 --> n36
```

</details>

## Inventaire et dépendances directes

Les liens ouvrent les définitions à la version du code analysée.

| Relation | Type | Matérialisation | Parents directs |
| --- | --- | --- | --- |
| [ops.allocine_rejected_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/allocine_rejected_credits.sql) | model | view | [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/allocine_rejected_results.sql) |
| [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/allocine_rejected_results.sql) | model | view | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [ops.film_credits_unmatched](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/film_credits_unmatched.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_credit_holders.sql) | model | table | [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql), [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) |
| [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql) | model | table | [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql), [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) |
| [fnl.fnl_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_film_credits.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) |
| [fnl.fnl_film_posters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_film_posters.sql) | model | view | [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_films.sql) | model | table | [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql), [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_allocine_films.sql), [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_cnc_films.sql), [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql) |
| [fnl.fnl_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/fnl/fnl_role.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) |
| [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_allocine_films.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_cnc_films.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql) | model | view | [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) |
| [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_film_genres.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_award_nomination.sql) | model | view | [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) |
| [intermediate.int_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_countries.sql) | model | view | [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_countries.sql) |
| [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) | model | view | [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) |
| [intermediate.int_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_festival_awards.sql) | model | view | [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) |
| [intermediate.int_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_festivals.sql) | model | view | [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_festivals.sql) |
| [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) | model | view | [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) |
| [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) | model | view | [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_film_credits.sql) |
| [intermediate.int_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_fix_roles.sql) | model | view | [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_roles.sql) |
| [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql) | model | view | [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_mubi_festival_films.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_mubi_festival_films.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [intermediate.int_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_mubi_film_awards.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql) | model | table | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_cnc_films.sql) | model | table | [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) | model | table | [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) | model | table | [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_countries.sql) | model | table | [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) | model | table | [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) | model | table | [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_festivals.sql) | model | table | [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) | model | table | [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_film_credits.sql) | model | table | [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_fix_roles.sql) | model | table | [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_id_matching.sql) | model | table | [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_mubi_festival_films.sql) | model | table | [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) | model | table | [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [ops.v_allocine_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/v_allocine_pipeline_status.sql) | model | table | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [ops.v_mubi_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/ops/v_mubi_pipeline_status.sql) | model | view | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/intermediate/int_id_matching.sql), [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) |
| [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/seeds/allocine_association_rejections.csv) | seed | seed | — |
| [raw.agreement_cnc](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/d2c86545f0c95e25dcdd5b420675f21658bfdcc4/ingestion/dbt/models/sources.yml) | source | — | — |

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-18 | Joel Teixeira | État généré depuis la version du code liée ci-dessus. |

Les versions précédentes restent disponibles dans l’historique Git de `docs/dbt-lineage.md` sur `main`.
