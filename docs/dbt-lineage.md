# Lineage dbt — ingestion RIC

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-23

**Status:** actif

Dépendances déclarées dans le projet dbt, des sources vers les modèles consommateurs.
[Version du code analysée](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886).

17 sources, 50 modèles, 2 seeds, 0 snapshots ; 79 dépendances directes.

Généré avec `dbt parse` puis `scripts/generate_dbt_lineage.py`. Aucune connexion à PostgreSQL. Les flèches suivent les appels `ref()` et `source()` du manifest ; les références SQL écrites en dur ne sont pas déduites.

Ce document décrit les dépendances entre relations, pas entre colonnes. Il ne prouve ni la présence des tables en base, ni le succès des traitements. Les tests, analyses, macros, modèles désactivés et traitements externes Airbyte/Prefect/scraping sont hors graphe.

## Lineage dbt complet

Cette vue rassemble toutes les relations actives du manifest, y compris celles sans dépendance. Suivre les flèches de gauche à droite pour parcourir les chaînes des sources brutes jusqu’aux modèles finaux et opérationnels. Les cadres regroupent les relations par schéma ; les sources brutes sont arrondies.

```mermaid
flowchart LR
  subgraph s0["raw"]
    n52(["raw.agreement_cnc"])
    n53(["raw.allocine_data"])
    n54(["raw.award_nominations"])
    n55(["raw.countries"])
    n56(["raw.credit_holders"])
    n57(["raw.credit_holders_genre"])
    n58(["raw.festival_awards"])
    n59(["raw.festivals"])
    n60(["raw.film_country_budget_allocation"])
    n61(["raw.film_credits"])
    n62(["raw.film_genres"])
    n63(["raw.films"])
    n64(["raw.genres"])
    n65(["raw.id_matching"])
    n66(["raw.mubi_festival_films"])
    n67(["raw.mubi_film_awards"])
    n68(["raw.roles"])
  end
  subgraph s1["staging"]
    n32["staging.stg_allocine_films"]
    n33["staging.stg_cnc_films"]
    n34["staging.stg_credit_holders_genre"]
    n35["staging.stg_fix_award_nomination"]
    n36["staging.stg_fix_countries"]
    n37["staging.stg_fix_credit_holders"]
    n38["staging.stg_fix_festival_awards"]
    n39["staging.stg_fix_festivals"]
    n40["staging.stg_fix_film_country_budget_allocation"]
    n41["staging.stg_fix_film_credits"]
    n42["staging.stg_fix_film_genres"]
    n43["staging.stg_fix_genres"]
    n44["staging.stg_fix_roles"]
    n45["staging.stg_id_matching"]
    n46["staging.stg_mubi_festival_films"]
    n47["staging.stg_mubi_film_awards"]
  end
  subgraph s2["intermediate"]
    n12["intermediate.int_allocine_films"]
    n13["intermediate.int_cnc_broadcasters"]
    n14["intermediate.int_cnc_films"]
    n15["intermediate.int_credit_holders_genre"]
    n16["intermediate.int_credit_holders_role"]
    n17["intermediate.int_film_country_budget_allocation"]
    n18["intermediate.int_film_genres"]
    n19["intermediate.int_fix_award_nomination"]
    n20["intermediate.int_fix_countries"]
    n21["intermediate.int_fix_credit_holders"]
    n22["intermediate.int_fix_festival_awards"]
    n23["intermediate.int_fix_festivals"]
    n24["intermediate.int_fix_film_country_budget_allocation"]
    n25["intermediate.int_fix_film_credits"]
    n26["intermediate.int_fix_film_genres"]
    n27["intermediate.int_fix_genres"]
    n28["intermediate.int_fix_roles"]
    n29["intermediate.int_id_matching"]
    n30["intermediate.int_mubi_festival_films"]
    n31["intermediate.int_mubi_film_awards"]
  end
  subgraph s3["fnl"]
    n4["fnl.fnl_credit_holders"]
    n5["fnl.fnl_film_country_budget_allocation"]
    n6["fnl.fnl_film_credits"]
    n7["fnl.fnl_film_genre"]
    n8["fnl.fnl_film_posters"]
    n9["fnl.fnl_films"]
    n10["fnl.fnl_genre"]
    n11["fnl.fnl_role"]
  end
  subgraph s4["ops"]
    n0["ops.allocine_rejected_credits"]
    n1["ops.allocine_rejected_results"]
    n2["ops.cnc_broadcasters_unrecognized"]
    n3["ops.film_credits_unmatched"]
    n48["ops.v_allocine_pipeline_status"]
    n49["ops.v_mubi_pipeline_status"]
    n50["ops.allocine_association_rejections"]
    n51["ops.cnc_broadcaster_aliases"]
  end
  n1 --> n0
  n5 --> n9
  n7 --> n9
  n9 --> n8
  n10 --> n9
  n12 --> n9
  n13 --> n2
  n13 --> n14
  n14 --> n9
  n15 --> n4
  n16 --> n3
  n16 --> n4
  n16 --> n6
  n16 --> n11
  n17 --> n5
  n18 --> n7
  n18 --> n10
  n21 --> n4
  n24 --> n5
  n25 --> n6
  n26 --> n7
  n27 --> n10
  n29 --> n8
  n29 --> n9
  n29 --> n30
  n29 --> n31
  n29 --> n49
  n32 --> n3
  n32 --> n8
  n32 --> n12
  n32 --> n16
  n32 --> n18
  n32 --> n48
  n33 --> n2
  n33 --> n13
  n33 --> n14
  n33 --> n17
  n33 --> n18
  n34 --> n15
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n25
  n42 --> n26
  n43 --> n27
  n44 --> n28
  n45 --> n12
  n45 --> n14
  n45 --> n16
  n45 --> n17
  n45 --> n18
  n45 --> n29
  n46 --> n30
  n47 --> n30
  n47 --> n31
  n50 --> n1
  n50 --> n32
  n51 --> n13
  n53 --> n1
  n53 --> n32
  n54 --> n35
  n55 --> n36
  n56 --> n37
  n57 --> n34
  n58 --> n38
  n59 --> n39
  n60 --> n40
  n61 --> n41
  n62 --> n42
  n63 --> n33
  n64 --> n43
  n65 --> n45
  n66 --> n46
  n67 --> n47
  n67 --> n49
  n68 --> n44
```

## Vues détaillées par schéma

<details>
<summary>Afficher les diagrammes par schéma consommateur</summary>

Chaque diagramme montre les relations du schéma et leurs parents directs. Une relation peut donc apparaître dans plusieurs diagrammes. Les sources brutes sont arrondies ; les transformations sont rectangulaires.

### fnl

```mermaid
flowchart LR
  n4["fnl.fnl_credit_holders"]
  n5["fnl.fnl_film_country_budget_allocation"]
  n6["fnl.fnl_film_credits"]
  n7["fnl.fnl_film_genre"]
  n8["fnl.fnl_film_posters"]
  n9["fnl.fnl_films"]
  n10["fnl.fnl_genre"]
  n11["fnl.fnl_role"]
  n12["intermediate.int_allocine_films"]
  n14["intermediate.int_cnc_films"]
  n15["intermediate.int_credit_holders_genre"]
  n16["intermediate.int_credit_holders_role"]
  n17["intermediate.int_film_country_budget_allocation"]
  n18["intermediate.int_film_genres"]
  n21["intermediate.int_fix_credit_holders"]
  n24["intermediate.int_fix_film_country_budget_allocation"]
  n25["intermediate.int_fix_film_credits"]
  n26["intermediate.int_fix_film_genres"]
  n27["intermediate.int_fix_genres"]
  n29["intermediate.int_id_matching"]
  n32["staging.stg_allocine_films"]
  n5 --> n9
  n7 --> n9
  n9 --> n8
  n10 --> n9
  n12 --> n9
  n14 --> n9
  n15 --> n4
  n16 --> n4
  n16 --> n6
  n16 --> n11
  n17 --> n5
  n18 --> n7
  n18 --> n10
  n21 --> n4
  n24 --> n5
  n25 --> n6
  n26 --> n7
  n27 --> n10
  n29 --> n8
  n29 --> n9
  n32 --> n8
```

### intermediate

```mermaid
flowchart LR
  n12["intermediate.int_allocine_films"]
  n13["intermediate.int_cnc_broadcasters"]
  n14["intermediate.int_cnc_films"]
  n15["intermediate.int_credit_holders_genre"]
  n16["intermediate.int_credit_holders_role"]
  n17["intermediate.int_film_country_budget_allocation"]
  n18["intermediate.int_film_genres"]
  n19["intermediate.int_fix_award_nomination"]
  n20["intermediate.int_fix_countries"]
  n21["intermediate.int_fix_credit_holders"]
  n22["intermediate.int_fix_festival_awards"]
  n23["intermediate.int_fix_festivals"]
  n24["intermediate.int_fix_film_country_budget_allocation"]
  n25["intermediate.int_fix_film_credits"]
  n26["intermediate.int_fix_film_genres"]
  n27["intermediate.int_fix_genres"]
  n28["intermediate.int_fix_roles"]
  n29["intermediate.int_id_matching"]
  n30["intermediate.int_mubi_festival_films"]
  n31["intermediate.int_mubi_film_awards"]
  n32["staging.stg_allocine_films"]
  n33["staging.stg_cnc_films"]
  n34["staging.stg_credit_holders_genre"]
  n35["staging.stg_fix_award_nomination"]
  n36["staging.stg_fix_countries"]
  n37["staging.stg_fix_credit_holders"]
  n38["staging.stg_fix_festival_awards"]
  n39["staging.stg_fix_festivals"]
  n40["staging.stg_fix_film_country_budget_allocation"]
  n41["staging.stg_fix_film_credits"]
  n42["staging.stg_fix_film_genres"]
  n43["staging.stg_fix_genres"]
  n44["staging.stg_fix_roles"]
  n45["staging.stg_id_matching"]
  n46["staging.stg_mubi_festival_films"]
  n47["staging.stg_mubi_film_awards"]
  n51["ops.cnc_broadcaster_aliases"]
  n13 --> n14
  n29 --> n30
  n29 --> n31
  n32 --> n12
  n32 --> n16
  n32 --> n18
  n33 --> n13
  n33 --> n14
  n33 --> n17
  n33 --> n18
  n34 --> n15
  n35 --> n19
  n36 --> n20
  n37 --> n21
  n38 --> n22
  n39 --> n23
  n40 --> n24
  n41 --> n25
  n42 --> n26
  n43 --> n27
  n44 --> n28
  n45 --> n12
  n45 --> n14
  n45 --> n16
  n45 --> n17
  n45 --> n18
  n45 --> n29
  n46 --> n30
  n47 --> n30
  n47 --> n31
  n51 --> n13
```

### ops

```mermaid
flowchart LR
  n0["ops.allocine_rejected_credits"]
  n1["ops.allocine_rejected_results"]
  n2["ops.cnc_broadcasters_unrecognized"]
  n3["ops.film_credits_unmatched"]
  n13["intermediate.int_cnc_broadcasters"]
  n16["intermediate.int_credit_holders_role"]
  n29["intermediate.int_id_matching"]
  n32["staging.stg_allocine_films"]
  n33["staging.stg_cnc_films"]
  n48["ops.v_allocine_pipeline_status"]
  n49["ops.v_mubi_pipeline_status"]
  n50["ops.allocine_association_rejections"]
  n51["ops.cnc_broadcaster_aliases"]
  n53(["raw.allocine_data"])
  n67(["raw.mubi_film_awards"])
  n1 --> n0
  n13 --> n2
  n16 --> n3
  n29 --> n49
  n32 --> n3
  n32 --> n48
  n33 --> n2
  n50 --> n1
  n53 --> n1
  n67 --> n49
```

### staging

```mermaid
flowchart LR
  n32["staging.stg_allocine_films"]
  n33["staging.stg_cnc_films"]
  n34["staging.stg_credit_holders_genre"]
  n35["staging.stg_fix_award_nomination"]
  n36["staging.stg_fix_countries"]
  n37["staging.stg_fix_credit_holders"]
  n38["staging.stg_fix_festival_awards"]
  n39["staging.stg_fix_festivals"]
  n40["staging.stg_fix_film_country_budget_allocation"]
  n41["staging.stg_fix_film_credits"]
  n42["staging.stg_fix_film_genres"]
  n43["staging.stg_fix_genres"]
  n44["staging.stg_fix_roles"]
  n45["staging.stg_id_matching"]
  n46["staging.stg_mubi_festival_films"]
  n47["staging.stg_mubi_film_awards"]
  n50["ops.allocine_association_rejections"]
  n53(["raw.allocine_data"])
  n54(["raw.award_nominations"])
  n55(["raw.countries"])
  n56(["raw.credit_holders"])
  n57(["raw.credit_holders_genre"])
  n58(["raw.festival_awards"])
  n59(["raw.festivals"])
  n60(["raw.film_country_budget_allocation"])
  n61(["raw.film_credits"])
  n62(["raw.film_genres"])
  n63(["raw.films"])
  n64(["raw.genres"])
  n65(["raw.id_matching"])
  n66(["raw.mubi_festival_films"])
  n67(["raw.mubi_film_awards"])
  n68(["raw.roles"])
  n50 --> n32
  n53 --> n32
  n54 --> n35
  n55 --> n36
  n56 --> n37
  n57 --> n34
  n58 --> n38
  n59 --> n39
  n60 --> n40
  n61 --> n41
  n62 --> n42
  n63 --> n33
  n64 --> n43
  n65 --> n45
  n66 --> n46
  n67 --> n47
  n68 --> n44
```

</details>

## Inventaire et dépendances directes

Les liens ouvrent les définitions à la version du code analysée.

| Relation | Type | Matérialisation | Parents directs |
| --- | --- | --- | --- |
| [ops.allocine_rejected_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/allocine_rejected_credits.sql) | model | view | [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/allocine_rejected_results.sql) |
| [ops.allocine_rejected_results](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/allocine_rejected_results.sql) | model | view | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [ops.cnc_broadcasters_unrecognized](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/cnc_broadcasters_unrecognized.sql) | model | view | [intermediate.int_cnc_broadcasters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_cnc_broadcasters.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql) |
| [ops.film_credits_unmatched](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/film_credits_unmatched.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_credit_holders.sql) | model | table | [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql), [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) |
| [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql) | model | table | [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql), [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) |
| [fnl.fnl_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_credits.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_role.sql), [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) |
| [fnl.fnl_film_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) |
| [fnl.fnl_film_posters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_posters.sql) | model | view | [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [fnl.fnl_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_films.sql) | model | table | [fnl.fnl_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_country_budget_allocation.sql), [fnl.fnl_film_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_film_genre.sql), [fnl.fnl_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_genre.sql), [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_allocine_films.sql), [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_cnc_films.sql), [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql) |
| [fnl.fnl_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_genre.sql) | model | table | [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_film_genres.sql), [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_genres.sql) |
| [fnl.fnl_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/fnl/fnl_role.sql) | model | table | [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) |
| [intermediate.int_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_allocine_films.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_cnc_broadcasters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_cnc_broadcasters.sql) | model | table | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql), [ops.cnc_broadcaster_aliases](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/seeds/cnc_broadcaster_aliases.csv) |
| [intermediate.int_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_cnc_films.sql) | model | view | [intermediate.int_cnc_broadcasters](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_cnc_broadcasters.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_genre.sql) | model | view | [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) |
| [intermediate.int_credit_holders_role](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_credit_holders_role.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_film_country_budget_allocation.sql) | model | view | [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_film_genres.sql) | model | view | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql), [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql), [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_award_nomination.sql) | model | view | [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) |
| [intermediate.int_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_countries.sql) | model | view | [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_countries.sql) |
| [intermediate.int_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_credit_holders.sql) | model | view | [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) |
| [intermediate.int_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_festival_awards.sql) | model | view | [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) |
| [intermediate.int_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_festivals.sql) | model | view | [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_festivals.sql) |
| [intermediate.int_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_country_budget_allocation.sql) | model | view | [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) |
| [intermediate.int_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_credits.sql) | model | view | [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_credits.sql) |
| [intermediate.int_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_film_genres.sql) | model | view | [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_genres.sql) |
| [intermediate.int_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_genres.sql) | model | view | [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_genres.sql) |
| [intermediate.int_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_fix_roles.sql) | model | view | [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_roles.sql) |
| [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql) | model | view | [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) |
| [intermediate.int_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_mubi_festival_films.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_mubi_festival_films.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [intermediate.int_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_mubi_film_awards.sql) | model | table | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql), [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) |
| [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql) | model | table | [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/seeds/allocine_association_rejections.csv), [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_cnc_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_cnc_films.sql) | model | table | [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_credit_holders_genre.sql) | model | table | [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_award_nomination](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_award_nomination.sql) | model | table | [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_countries.sql) | model | table | [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_credit_holders.sql) | model | table | [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_festival_awards.sql) | model | table | [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_festivals.sql) | model | table | [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_country_budget_allocation.sql) | model | table | [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_credits.sql) | model | table | [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_film_genres.sql) | model | table | [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_genres.sql) | model | table | [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_fix_roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_fix_roles.sql) | model | table | [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_id_matching.sql) | model | table | [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_mubi_festival_films.sql) | model | table | [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [staging.stg_mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_mubi_film_awards.sql) | model | table | [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [ops.v_allocine_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/v_allocine_pipeline_status.sql) | model | table | [staging.stg_allocine_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/staging/stg_allocine_films.sql) |
| [ops.v_mubi_pipeline_status](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/ops/v_mubi_pipeline_status.sql) | model | view | [intermediate.int_id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/intermediate/int_id_matching.sql), [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) |
| [ops.allocine_association_rejections](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/seeds/allocine_association_rejections.csv) | seed | seed | — |
| [ops.cnc_broadcaster_aliases](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/seeds/cnc_broadcaster_aliases.csv) | seed | seed | — |
| [raw.agreement_cnc](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.allocine_data](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.award_nominations](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.countries](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.credit_holders_genre](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festival_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.festivals](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_country_budget_allocation](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_credits](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.film_genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.genres](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.id_matching](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_festival_films](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.mubi_film_awards](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |
| [raw.roles](https://github.com/Le-Collectif-50-50/cinestats-5050/tree/6ce370b4a869a15e440577d6e930bb1d2bd78886/ingestion/dbt/models/sources.yml) | source | — | — |

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-23 | Joel Teixeira | État généré depuis la version du code liée ci-dessus. |

Les versions précédentes restent disponibles dans l’historique Git de `docs/dbt-lineage.md` sur `main`.
