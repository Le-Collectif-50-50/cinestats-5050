# Revue des 25 conflits de visa Allociné — issue 51

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

## Périmètre et résultat de la revue

[Issue 51](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/51) : 25 films dont la date legacy est comprise entre le 1er janvier 2004 et le 31 décembre 2024 inclus, la date finale dbt absente et le dernier essai Allociné en `visa_mismatch`. Unité : film rapproché par visa CNC, sans autre filtre métier.

Les 25 dossiers ont été examinés le 14 novembre 2026. Une première publication a résolu 21 correspondances. Les quatre réserves ont ensuite été instruites à partir des visas d’exploitation présents sur Allociné, des fiches ou catalogues CNC et du distributeur : les quatre visas source étaient erronés. Ils sont corrigés dans films et id_matching, avec leurs associations manuelles. Les quatre nouvelles collectes et leur publication sont vérifiées : les 25 dossiers sont résolus.

**Résultat final : 25 films publiés et contrôlés, dates manquantes 25 → 0 à cohorte constante.** Mubi : trois IDs existants confirmés, ID Irina non retrouvé. TMDB : quatre IDs existants corroborés via Wikidata ; recherches supplémentaires arrêtées selon la consigne. Les incidents techniques et leurs réparations sont conservés dans la traçabilité ci-dessous.

## Résultat final après correction des quatre visas

Le contrôle des 25 dossiers est terminé : **25 films publiés avec date et genre ; zéro dossier restant sans date** dans la cohorte initiale. Le catalogue reste à 6 138 films, visas et film_id distincts. Les anciens visas corrigés n'apparaissent plus dans fnl.fnl_films ; les 21 autres film_id sont conservés.

| Visa initial | Visa publié | Date publiée | Genres | Crédits | Réalisation finale |
| --- | --- | --- | ---: | ---: | --- |
| 122169 | 136385 | 2014-09-03 | 2 | 33 | Bernard Mazauric |
| 146143 | 146643 | 2019-05-01 | 2 | 34 | Olivier Masset-Depasse |
| 154816 | 154818 | 2023-03-29 | 1 | 23 | Steffi Niederzoll |
| 155994 | 154994 | 2023-01-25 | 2 | 32 | Ramzi Ben Sliman |

Les quatre nouveaux succès portent le run de collecte `4537068b-fc75-44e2-a488-3a39e73fbc16`. Chaque visa extrait d'Allociné correspond exactement au visa corrigé, avec `match_strategy=provided_allocine_id` : aucune dérogation manuelle n'a été nécessaire. ID, date, réalisation et genres ont été contrôlés en mémoire avant insertion. Les tentatives anciennes restent conservées sous leurs visas historiques ; une ancienne alerte brute ne remplace pas le contrôle du visa corrigé.

La synchronisation initiale des quatre visas est le run `443f8ab2-34eb-4708-baf2-7c36b08ab869`. La publication finale est le run `77467edb-a730-4e7f-bb4d-85cfcd34ed0f`, terminé avec succès le **14 novembre 2026 à 14:02:19 UTC**, soit **15:02:19 à Paris**. La phase dbt 2, invocation `3ba55495-7ed4-4b29-9580-ee8c10ee1443`, compte **45 modèles réussis, 96 tests passés et six tests en avertissement**, sans erreur bloquante.

Les 25 dossiers possèdent 33 associations de genres, 765 associations de crédits et 26 crédits de réalisation. Les quatre fiches métier et leurs crédits ont été interrogés sans cache sous les nouveaux visas : une seule réalisation attendue par film, dont Ramzi Ben Sliman sur son profil complet, genre Homme. Les sources et leurs contraintes ont été relues par API ; les contrôles de doublons du matching sont égaux à 1.

### Comparaison à cohorte constante

| Mesure | Avant revue | Après première publication | Après correction des visas |
| --- | ---: | ---: | ---: |
| Films rapprochés avec date legacy 2004–2024 | 4 913 | 4 913 | 4 913 |
| Films sélectionnables par date dbt dans 2004–2024 | 4 888 | 4 909 | 4 913 |
| Dates dbt absentes | 25 | 4 | 0 |

La dernière comparaison utilise les quatre alias explicites ancien visa → visa corrigé pour rapprocher le legacy. Une égalité stricte avec les anciens visas ferait disparaître les quatre films du rapprochement au lieu de vérifier leur résolution. La requête SQL versionnée conserve donc `original_cnc_visa` et `cnc_visa` séparément. Les 25 dates attendues concordent avec le staging et les tables finales ; une seule ligne de matching par visa et ID, sans ex æquo au dernier horodatage. Aucun doublon de clé finale film/rôle/personne ou film/genre ; aucune référence manuelle restante aux quatre anciens film_id.

### Avertissements globaux observés au dernier run

| Test en avertissement | Volume final |
| --- | ---: |
| Crédits sans film associé | 102 lignes sur 9 ID |
| ID Allociné absents | 236 lignes |
| ID Mubi absents | 893 lignes |
| ID TMDB absents | 773 lignes |
| Unicité des ID Mubi | 5 valeurs dupliquées |
| Unicité des ID TMDB | 2 valeurs dupliquées |

Les volumes de quarantaine et d'ID Allociné absents ont évolué depuis la première publication. Cette variation globale n'est pas attribuée aux seules quatre corrections : leurs ID Allociné sont inchangés et d'autres modifications source ont été synchronisées. Le bilan ci-dessous conserve les résultats historiques de la première étape, puis les preuves de correction complémentaires.


## Sources et règle de décision

Sources : fiches publiques CNC et Allociné consultées le 14 novembre 2026 ; `raw.films` pour la réalisation et l'année d'agrément source ; `raw.id_matching`, `raw.allocine_data`, `fnl.fnl_films` et `ops.v_statistics_legacy_films` pour les contrôles en production.

Pour les identités confirmées avec visa CNC exploitable : comparaison du titre actuel, de la réalisation, de la sortie en salle et du format long métrage. Les écarts de durée sont consignés ; la validation porte sur l'identité, pas sur l'exactitude de tous les enrichissements Allociné. Une année de production différente de l'année d'agrément ou de sortie ne constitue pas seule une contradiction.

Les quatre divergences de visa source ont été résolues par des preuves externes concordantes, puis corrigées dans les deux onglets selon l’autorisation de Joel Teixeira. La réalisation, le titre, la date et, pour Sept hivers à Téhéran, les sociétés de production permettent d’écarter les homonymes. Aucune date legacy n’a été recopiée. La revue est déléguée et automatisée ; les métadonnées source le précisent.

## Décisions de la première revue (avant correction des quatre visas)

État de la première revue, avant correction des quatre visas source. Les dates sont les sorties en salle vérifiées à cette étape. Les quatre lignes marquées ouvertes ci-dessous sont désormais traitées par la correction détaillée dans la section suivante. Durées : CNC / Allociné, en minutes.

| Visa source | Titre retenu | Réalisation vérifiée | ID Allociné retenu | Sortie vérifiée | Visa Allociné actuel | Durées | Décision et preuves |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 107522 | Real'movie | Stéphane Robelin | 53320 | 2004-06-09 | 107552 | 94/95 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/107522) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=53320.html) |
| 108837 | Modigliani | Mick Davis | 54208 | 2004-09-29 | 108 834 | 128/114 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/108837) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=54208.html) |
| 109126 | Les temps qui changent | André Téchiné | 56738 | 2004-12-15 | 109926 | 100/90 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/109126) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=56738.html) |
| 109227 | Le cou de la girafe | Safy Nebbou | 54489 | 2004-09-29 | 110227 | 89/88 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/109227) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=54489.html) |
| 109669 | L'empire des loups | Chris Nahon | 55721 | 2005-04-20 | 739761 | 129/128 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/109669) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=55721.html) |
| 109743 | Ecorches | Cheyenne Carron | 55675 | 2007-07-25 | 109783 | 77/77 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/109743) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=55675.html) |
| 111560 | Les inseparables | Christine Dory | 139492 | 2008-12-10 | 115560 | 101/100 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/111560) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=139492.html) |
| 112054 | Serko | Joël Farges | 44450 | 2006-03-29 | 42389 | 100/100 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/112054) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=44450.html) |
| 112985 | Tout est pardonné | Mia Hansen-Løve | 110869 | 2007-09-26 | 112185 | 105/105 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/112985) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=110869.html) |
| 113167 | Charly | Isild Le Besco | 110153 | 2007-09-12 | 113160 | 95/95 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/113167) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=110153.html) |
| 115952 | Steak | Quentin Dupieux | 110872 | 2007-06-20 | 107925 | 84/82 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/115952) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=110872.html) |
| 122169 | La malette rouge | Voir analyse ci-dessous | 138197 | Non validée pour ce visa | Voir analyse | — | Ouvert : visa source non confirmé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/122169) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=138197.html) |
| 122490 | Le mac | Pascal Bourdiaux | 146955 | 2010-02-17 | 122 890 | 92/90 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/122490) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=146955.html) |
| 124620 | Realite | Quentin Dupieux | 204027 | 2015-02-18 | 139820 | 87/95 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/124620) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=204027.html) |
| 126410 | Qui a envie d'etre aime ? | Anne Giafferi | 188254 | 2011-02-09 | 124 410 | 89/89 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/126410) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=188254.html) |
| 127668 | Et maintenant on va ou ? | Nadine Labaki | 189935 | 2011-09-14 | 127668 | 102/110 | Identité confirmée ; visa public désormais concordant. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/127668) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=189935.html) |
| 128894 | Mauvaise fille | Patrick Mille | 191360 | 2012-11-28 | 155856 | 108/108 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/128894) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=191360.html) |
| 130274 | Rue des cités | Carine May et Hakim Zouhani | 193129 | 2013-06-05 | 130374 | 68/68 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/130274) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=193129.html) |
| 146143 | Duelles | Voir analyse ci-dessous | 255842 | Non validée pour ce visa | Voir analyse | — | Ouvert : visa source non confirmé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/146143) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=255842.html) |
| 148874 | Soul Kids | Hugo Sobelman | 292028 | 2021-11-24 | 148847 | 77/75 | Identité confirmée ; titre définitif Soul Kids rétabli. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/148874) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=292028.html) |
| 149285 | Rodéo | Lola Quivoron | 298736 | 2022-09-07 | 1490285 | 106/106 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/149285) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=298736.html) |
| 150140 | Suprêmes | Audrey Estrougo | 270890 | 2021-11-24 | 160140 | 114/112 | Identité confirmée, ID conservé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/150140) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=270890.html) |
| 152392 | Un pays qui se tient sage | David Dufresne | 283687 | 2020-09-30 | 152392 | 89/86 | ID corrigé 292588 → 283687 ; titre définitif rétabli. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/152392) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=283687.html) |
| 154816 | Une femme iranienne | Voir analyse ci-dessous | 279602 | Non validée pour ce visa | Voir analyse | — | Ouvert : le CNC désigne un autre film. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/154816) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=279602.html) |
| 155994 | Néneh superstar | Voir analyse ci-dessous | 291767 | Non validée pour ce visa | Voir analyse | — | Ouvert : visa source non confirmé. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/155994) · [Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=291767.html) |

## Correction d'identité : visa 152392

La fiche CNC 152392 désigne **Un pays qui se tient sage**, David Dufresne, long métrage, sortie le 30 septembre 2020, durée CNC 89 minutes. Le titre source « Ordre(s) et désordres » correspond au projet attribué à David Dufresne dans `raw.films`.

L'ancienne fiche Allociné 292588 désigne **Ordre ou Désordre**, Abbas Kiarostami, œuvre de 1981 de 17 minutes, reprise le 2 juin 2021, visa affiché 23460. Cette fiche est rejetée : réalisation, époque et durée incompatibles. Le libellé « Long métrage » de ses informations techniques ne suffit pas à surmonter ces contradictions.

La [fiche Allociné 283687](https://www.allocine.fr/film/fichefilm_gen_cfilm=283687.html) confirme le visa 152392, David Dufresne et la sortie du 30 septembre 2020. Le Sheet porte désormais ce nouvel ID et le titre définitif CNC. La date legacy du 2 juin 2021 appartient à l'autre œuvre et ne constitue pas une référence à reproduire. Aucun autre matching ne porte 283687 au contrôle préalable.

## Correction des quatre visas source

| Visa initial | Visa corrigé | Titre définitif | ID Allociné | Sortie en salle | Preuve du visa |
| --- | --- | --- | --- | --- | --- |
| 122169 | **136385** | Irina, la Mallette rouge | 138197 | 2014-09-03 | [CNC 136385](https://www.cnc.fr/professionnels/visas-et-classification/136385) : Bernard Mazauric, long métrage. |
| 146143 | **146643** | Duelles | 255842 | 2019-05-01 | [Catalogue CNC](https://www.cnc.fr/professionnels/visas-et-classification?_RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2_cur=83&_RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2_metrage=LM&p_p_id=RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal) : Olivier Masset-Depasse. La fiche directe affiche une erreur de service. |
| 154816 | **154818** | Sept hivers à Téhéran | 279602 | 2023-03-29 | [Distributeur Nour Films](https://www.nourfilms.com/cinema-independant/sept-hivers-a-teheran/) : visa, Steffi Niederzoll, sortie et sociétés Gloria Films / TS Production concordantes ; catalogue CNC également concordant. |
| 155994 | **154994** | Néneh superstar | 291767 | 2023-01-25 | [CNC 154994](https://www.cnc.fr/professionnels/visas-et-classification/154994) : Ramzi Ben Sliman. |

Les anciens visas 122169, 146143 et 155994 ne fournissaient pas de fiche CNC exploitable. Le visa 154816 désigne une autre œuvre : Nature morte, Karim Morel, court métrage de 15 minutes. Il ne devait pas être validé manuellement pour Sept hivers à Téhéran. La correction porte donc sur la source CNC renseignée dans le Sheet. Les titres de travail sont remplacés par les titres définitifs dans les deux onglets ; les budgets, financements et années d’agrément sont conservés.

Deux corrections (136385 et 154994) étaient déjà saisies par Joel Teixeira au début du contrôle complémentaire. Elles ont été vérifiées et complétées en traçabilité, sans créer de nouvelle ligne. Les cellules ont été relues avant écriture ; aucune collision des quatre visas corrigés n’a été trouvée.

### Reprise des associations internes

Le modèle `stg_id_matching` calcule `film_id = MD5(VISA)::UUID`. Corriger le visa change donc cet identifiant. Les quatre associations manuelles de réalisation ont été reprises dans `film_credits`. L’inventaire complet des tables brutes référant `FILM_ID` n’a trouvé aucune association correspondante dans film_genres, film_country_budget_allocation ou award_nominations.

| Ancien visa | Ancien film_id | Nouveau visa | Nouveau film_id |
| --- | --- | --- | --- |
| 122169 | 0dc67dc9-d1ee-44ef-e47e-a0b675e37dfe | 136385 | fb8c90e7-7254-2687-7ab2-10fba4061c4c |
| 146143 | 39b4073e-178b-5f0d-16c5-f2c193b08f0e | 146643 | 1b559548-7bde-6eb8-517c-a43a0c4e7c7b |
| 154816 | 109b1afe-c4a8-b130-e017-bb848bb635ee | 154818 | a2398594-505e-26c8-91e3-eac3da80e7fd |
| 155994 | 3e066d85-01f5-639a-2002-b66439baa06d | 154994 | 192a0144-5234-3de4-fa17-19a5699593f4 |

Pour Néneh superstar, l’association manuelle utilise désormais le profil existant **Ramzi Ben Sliman**, `59a4df2a-c825-4372-c29e-c3143718d7f9`, genre male, au lieu du profil tronqué Ramzi Sliman. Les autres profils et les fiches personne sont conservés. Les notes des cellules concernées gardent les anciens identifiants et métadonnées.

### Identifiants Mubi et TMDB

| Visa corrigé | Mubi | TMDB | Référence Wikidata |
| --- | --- | --- | --- |
| 136385 | Non retrouvé, cellule vide conservée | 288877 | [Q124748150](https://www.wikidata.org/wiki/Q124748150) |
| 146643 | [196085 — Duelles](https://mubi.com/films/duelles) | 477072 | [Q65153125](https://www.wikidata.org/wiki/Q65153125) |
| 154818 | [368065 — Seven Winters in Tehran](https://mubi.com/films/seven-winters-in-tehran) | 1073462 | [Q116458519](https://www.wikidata.org/wiki/Q116458519) |
| 154994 | [354963 — Neneh Superstar](https://mubi.com/films/neneh-superstar) | 1008430 | [Q115639081](https://www.wikidata.org/wiki/Q115639081) |

Les trois IDs Mubi existants sont confirmés directement par l’API publique Mubi (`/v3/films/{id}`, en-têtes Client: web et Client-Country: FR) : titre, réalisation et année concordent. Les recherches officielles Irina, Mazauric, Irina la mallette rouge, scarlet briefcase et mallette n’ont pas retrouvé le film de Bernard Mazauric. Les homonymes ont été écartés ; aucun ID Mubi n’a été inventé.

Les quatre IDs TMDB existants concordent avec la propriété P4947 des fiches Wikidata citées. Les réalisateurs P57, titres et dates ont également été recoupés. La lecture directe de TMDB répond HTTP 403 ; il s’agit donc d’une corroboration indépendante via Wikidata, et non d’une lecture de la fiche TMDB. Les identifiants sont conservés ; aucune recherche TMDB supplémentaire n’est requise. Les preuves sont dans COMMENTAIRES et les notes de D:E dans id_matching.

## Coordination et traçabilité

Les issues 46, 52 et 53 ont été relues avant correction. Les visas 144246 et 149368 de l'issue 46 ne recoupent pas le lot. Les 25 lignes disposent déjà d'un ID, contrairement au critère de l'issue 53. Aucun des 25 ID initiaux, ni le nouvel ID 283687, n'apparaît dans `ops.film_credits_unmatched` au contrôle préalable ; cette observation ne préjuge pas des effets ultérieurs de reconstruction.

Sheet : [Source de données, id_matching](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit#gid=902822468). Modifications limitées à B/C lorsque nécessaire, F:H et K ; A, D:E et les formules I:J sont préservées. Les commentaires conservent l'auteur et la date antérieurs : Hugo Laurens, 25 avril 2026. `UPDATED BY` précise « Revue automatisée — mandat Joel Teixeira ». La date est une valeur native compatible avec la validation de dates, en heure de Paris.

Premier run Prefect : `f0407144-3b0d-47a0-b0e3-6c0fd4f88d3f`, nom `issue-51-synchroniser-matching`, Airbyte activé, phase dbt 2 désactivée. Terminé le 14 novembre 2026 à 12:16:20 UTC. Invocation dbt phase 1 : `df474ac3-2639-4a2c-bb6f-c219190c0557`, un modèle réussi et un test passé. Ce run direct n'est pas une demande créée depuis Metabase.

La collecte a utilisé le connecteur déployé, uniquement les 21 visas confirmés, une session Browserless et la configuration partagée inchangée. Un premier essai avec navigateur local a été interrompu avant insertion : le binaire Chromium local était absent. La connexion Browserless a ensuite été vérifiée avant reprise. Les résultats ont été conservés en mémoire jusqu'au contrôle des ID, dates et réalisations ; les 21 succès ont ensuite été insérés.

Run de collecte : `c268eff8-8fb2-43e7-8178-45343d5902a8`, 21 visas distincts et 21 succès, aucun `error`, `blocked`, `not_found`, `visa_mismatch` ou `needs_review`. Extractions du 14 novembre 2026 de 12:18:41 à 12:44:27 UTC ; insertion ensuite vérifiée dans `raw.allocine_data`. Les 21 ID, dates de sortie et ensembles de réalisateurs concordent avec les décisions documentées ; les genres sont renseignés pour les 21 œuvres. Les tentatives historiques restent conservées.

Premier run Prefect de publication : `832a5b95-1391-4cc0-96df-9b94af8d5f17`, nom `issue-51-publier-21-correspondances`, Airbyte désactivé et phase dbt 2 activée. Terminé le 14 novembre 2026 à 12:48:10 UTC. L'absence de run concurrent d'ingestion ou de scraping a été contrôlée avant son lancement. Le matching synchronisé a été relu juste avant publication : les 25 décisions et métadonnées n'ont pas changé pendant la collecte.

Le [guide métier actualisé](../runbooks/ingestion-tutoriel-revue-humaine-allocine.md#parcours-recommandé--scraper-un-visa-cnc) propose désormais le bouton **Scraper un visa CNC**, qui synchronise, collecte le visa demandé puis publie automatiquement après succès confirmé. Ce bouton est le parcours métier pour les prochaines reprises individuelles. Le présent lot a utilisé une collecte technique explicitement filtrée sur ses 21 visas, avec contrôle des résultats en mémoire avant insertion, puis une publication séparée ; aucun lot aléatoire Metabase n'a été utilisé.

### Déduplication du crédit de réalisation de Charly

Le premier contrôle final a trouvé deux associations de réalisation pour le visa 113167 : l'ajout manuel « Isild Besco » et le nouveau scraping « Isild Le Besco ». Les tests d'unicité des clés relationnelles ne détectent pas cette duplication sémantique, car les identifiants de personne diffèrent.

L'association existante de `film_credits`, ligne 37 lors de la revue, a été rattachée à l'identifiant déjà présent `992014a3-1e3b-5a45-f143-609961bce075` (Isild Le Besco), à la place de `16f3b992-c8a8-6b19-6950-ca5ebbdded1f` (Isild Besco). Film et rôle sont conservés. Les deux fiches portaient `gender=female` ; aucune fiche personne n'a été modifiée ou supprimée. Une note sur C37 conserve les preuves, les anciennes métadonnées et l'ancien identifiant. La clé identique au crédit scrapé permet la déduplication par l'UNION du modèle final.

La republication `93716118-6e7c-45aa-9076-c01eeeab2b67` a synchronisé cette association, mais s'est arrêtée sur une autre erreur : une interaction du contrôle visuel avait temporairement remplacé le visa 165277 par une URL dans A6139 de `id_matching`. La valeur originale 165277, conservée dans la lecture préalable de l'index, a été réécrite par API ; titre et ID Allociné de cette ligne sont préservés. Aucun assouplissement du cast dbt n'a été effectué. Le run de restauration et publication `594c70f2-f567-46bf-a21b-c722fe6c247a` est terminé avec succès à 13:01:07 UTC. L'index synchronisé contient ensuite 6 138 lignes, 6 138 visas distincts et zéro visa invalide ; le visa 165277 porte de nouveau « TU NE JUGERAS POINT » et l'ID 1000052544. La lecture complète A:C du Sheet correspond à l'index initial, avec uniquement les deux titres et l'ID modifiés intentionnellement.

## Contrôles de la première publication (21 cas)

La [requête de contrôle versionnée](../../ingestion/dbt/analyses/allocine_issue_51_validation.sql) a été exécutée avant publication : 25 lignes, 25 dates absentes, une ligne de matching par visa et par ID. Elle contrôle aussi le dernier essai, les horodatages ex æquo, le staging, la date finale, les genres et les réalisations publiées. Les résultats intermédiaires sont inspectés en mémoire, sans export de données.

État initial à filtres identiques : 4 913 films rapprochés avec date legacy dans 2004–2024, dont 4 888 sélectionnables par leur date dbt dans la même période et 25 dates dbt absentes. Les 25 films n'ont aucun genre publié et possèdent 26 lignes de crédits au total, dont deux réalisateurs pour Rue des cités. Le catalogue final compte 6 138 films, visas et identifiants uniques. La quarantaine complète compte 144 lignes sur 16 ID au contrôle préalable ; les volumes historiques de l'issue 52 ne constituent donc pas son état courant.

Après la dernière reconstruction, la requête versionnée a été réexécutée sur les 25 dossiers. Pour chaque cas confirmé : bon ID dans raw et staging, nouveau succès du run `c268eff8-8fb2-43e7-8178-45343d5902a8`, date attendue identique dans staging et fnl, genres présents et ensemble exact des réalisateurs. Les 25 identifiants de film sont conservés. Chaque visa et ID Allociné du lot reste associé à une seule ligne de matching ; chaque dernier horodatage est unique. Aucun doublon de clé dans les associations finales film/rôle/personne ou film/genre.

Lors de cette première publication, les quatre réserves conservaient une validation décochée, leur dernier essai historique, une date finale absente et leur crédit manuel antérieur. Elles ont ensuite été traitées par correction de leur visa source. La quarantaine de cette étape était de 144 lignes sur 16 ID.

La carte métier **Fiche Film · Identité du film** (100) a été interrogée sans cache pour chacun des 25 visas : une fiche par visa, titres et dates conformes aux tables finales. La carte **Crédits · personnes et sociétés** (101) restitue pour Charly une seule réalisation, **Isild Le Besco**, identifiant `992014a3-1e3b-5a45-f143-609961bce075`, genre **Femme**, parmi 23 associations de crédits. Les valeurs, notes et contraintes du Sheet ont été relues par API ; les captures du contrôle natif n'étaient pas exploitables pour vérifier sa mise en page.

### Impact à périmètre constant

| Mesure | Avant | Après |
| --- | ---: | ---: |
| Films rapprochés, date legacy dans 2004–2024 | 4 913 | 4 913 |
| Films sélectionnables par date dbt dans 2004–2024 | 4 888 | 4 909 |
| Dates dbt absentes dans ce rapprochement | 25 | 4 |
| Films du lot avec genre publié | 0 | 21 |
| Catalogue fnl : films, visas et film_id distincts | 6 138 | 6 138 |

Les 21 films publiés portent 26 associations film/genre, 643 associations film/rôle/personne ou société et 22 crédits de réalisation. Ces nombres ne sont pas des nombres de personnes uniques. Vingt dates concordent avec le legacy ; le visa 152392 publie le 30 septembre 2020, date officielle de l'œuvre confirmée, à la place du 2 juin 2021 attribué par le legacy à une autre œuvre. L'impact mesuré porte sur la sélection temporelle et les associations publiées.

### Résultats individuels publiés

| Visa CNC | Date publiée | Genres publiés | Lignes de crédits |
| --- | --- | ---: | ---: |
| 107522 | 2004-06-09 | 1 | 15 |
| 108837 | 2004-09-29 | 2 | 54 |
| 109126 | 2004-12-15 | 2 | 27 |
| 109227 | 2004-09-29 | 1 | 27 |
| 109669 | 2005-04-20 | 1 | 31 |
| 109743 | 2007-07-25 | 1 | 18 |
| 111560 | 2008-12-10 | 1 | 22 |
| 112054 | 2006-03-29 | 1 | 19 |
| 112985 | 2007-09-26 | 1 | 34 |
| 113167 | 2007-09-12 | 1 | 23 |
| 115952 | 2007-06-20 | 2 | 24 |
| 122490 | 2010-02-17 | 1 | 42 |
| 124620 | 2015-02-18 | 1 | 34 |
| 126410 | 2011-02-09 | 1 | 42 |
| 127668 | 2011-09-14 | 1 | 44 |
| 128894 | 2012-11-28 | 1 | 48 |
| 130274 | 2013-06-05 | 1 | 26 |
| 148874 | 2021-11-24 | 2 | 18 |
| 149285 | 2022-09-07 | 1 | 31 |
| 150140 | 2021-11-24 | 2 | 48 |
| 152392 | 2020-09-30 | 1 | 16 |

À cette étape initiale, les quatre anciens visas 122169, 146143, 154816 et 155994 étaient sans date finale. Leurs visas corrigés et résultats complémentaires figurent dans la section « Correction des quatre visas source ».

### Résultats dbt

Dernière phase 1 : invocation `d457ea96-cf87-4f5b-8afb-c1c22bd57cd7`, un modèle réussi et un test passé. Dernière phase 2 : invocation `39163e66-cced-4e1a-b9fe-7e0c35cdc806`, **45 modèles réussis, 96 tests passés, six avertissements, aucune erreur bloquante**.

Les six avertissements et leurs volumes sont identiques à l'invocation antérieure du 14 novembre à 11:02 UTC :

| Test en avertissement | Volume |
| --- | ---: |
| Crédits sans film associé | 144 lignes |
| ID Allociné absents dans le matching | 243 lignes |
| ID Mubi absents | 893 lignes |
| ID TMDB absents | 773 lignes |
| Unicité des ID Mubi | 5 valeurs dupliquées |
| Unicité des ID TMDB | 2 valeurs dupliquées |

La clôture administrative initiale de l’issue 51 portait sur la revue des 25 dossiers, dont 21 publiés et quatre réserves explicites. Les quatre réserves sont reprises par la correction des visas documentée ci-dessus.

Réserve préexistante sur le référentiel : `raw.credit_holders` conserve les fiches « Isild / Besco » (`16f3b992-c8a8-6b19-6950-ca5ebbdded1f`) et « Ramzi / Sliman » (`6b4d3496-a085-c6cb-9f80-ee40a89902d3`). Les références d'identité portent les noms Isild Le Besco et Ramzi Ben Sliman. Le crédit Charly est corrigé par son association ; le crédit Néneh superstar est également repris sur le profil Ramzi Ben Sliman lors de la correction du visa 155994 vers 154994. Les fiches personne et leurs autres éventuelles associations ne sont pas fusionnées par cette revue.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | Qualification des 25 conflits, première publication de 21 films puis correction des quatre visas source, reprise des associations et vérification Mubi/TMDB. |
