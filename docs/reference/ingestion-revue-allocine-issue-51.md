# Revue des 25 conflits de visa Allociné — issue 51

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

## Périmètre et résultat de la revue

[Issue 51](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/51) : 25 films dont la date legacy est comprise entre le 1er janvier 2004 et le 31 décembre 2024 inclus, la date finale dbt absente et le dernier essai Allociné en `visa_mismatch`. Unité : film rapproché par visa CNC, sans autre filtre métier.

Les 25 dossiers ont été examinés le 14 novembre 2026. Vingt et une identités sont confirmées ; quatre restent ouvertes, car leur visa source n'est pas démontré ou désigne une autre œuvre. Les modifications du Sheet ont été relues : 25 visas uniques, 25 ID uniques et contrôles de doublons égaux à 1. Les cases de validation sont activées uniquement pour les 21 identités confirmées.

Résultat final : **21 films collectés, publiés dans dbt et contrôlés ; quatre dossiers ouverts**. Les dates manquantes du périmètre passent de 25 à 4, soit une réduction de 84 %. Le dernier flow de publication est terminé avec succès le 14 novembre 2026 à 13:01:07 UTC. La correction du crédit de réalisation de Charly et la restauration de la cellule accidentellement altérée sont vérifiées en production.

## Sources et règle de décision

Sources : fiches publiques CNC et Allociné consultées le 14 novembre 2026 ; `raw.films` pour la réalisation et l'année d'agrément source ; `raw.id_matching`, `raw.allocine_data`, `fnl.fnl_films` et `ops.v_statistics_legacy_films` pour les contrôles en production.

Pour les identités confirmées avec visa CNC exploitable : comparaison du titre actuel, de la réalisation, de la sortie en salle et du format long métrage. Les écarts de durée sont consignés ; la validation porte sur l'identité, pas sur l'exactitude de tous les enrichissements Allociné. Une année de production différente de l'année d'agrément ou de sortie ne constitue pas seule une contradiction.

Une divergence portant sur le visa source lui-même reste ouverte. Aucun visa CNC n'a été changé. Aucune date legacy n'a été recopiée. La revue est automatisée et déléguée par Joel Teixeira ; elle ne doit pas être présentée comme une vérification humaine indépendante.

## Décisions par film

Les dates ci-dessous sont les sorties en salle vérifiées avant collecte. Les durées sont exprimées en minutes, CNC / Allociné. Les lignes ouvertes conservent leur ID et leur validation décochée.

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

## Cas ouverts

- **122169 — La malette rouge.** La fiche CNC source ne fournit pas d'œuvre exploitable. Le [CNC 136385](https://www.cnc.fr/professionnels/visas-et-classification/136385) et Allociné 138197 désignent *Irina la mallette rouge*, Bernard Mazauric, sortie le 3 septembre 2014 ; durées 88/90 minutes. La réalisation source concorde, mais le rattachement au visa 122169 reste non démontré. Décision : conserver l'ID, laisser la validation décochée, rechercher la pièce d'agrément ou faire corriger la source CNC après vérification des références.
- **146143 — Duelles.** La fiche CNC 146143 ne fournit pas d'œuvre exploitable. Le catalogue CNC référence *Duelles*, Olivier Masset-Depasse, sortie le 1er mai 2019, sous **146643**, comme Allociné 255842. [Catalogue CNC](https://www.cnc.fr/professionnels/visas-et-classification?_RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2_cur=83&_RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2_metrage=LM&p_p_id=RechercheVisaClassificationControlleur_INSTANCE_bFazQlIweBh2&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal). Décision : conserver l'ID et laisser ouvert le visa 146143. La consultation directe de 146643 a aussi affiché une erreur de service ; le catalogue est la preuve disponible.
- **154816 — Une femme iranienne.** Le [CNC 154816](https://www.cnc.fr/professionnels/visas-et-classification/154816) désigne *Nature morte*, Karim Morel, court métrage de 15 minutes, visa du 23 mars 2022, sans sortie en salle renseignée. Allociné 279602 désigne *Sept hivers à Téhéran*, Steffi Niederzoll, long métrage de 99 minutes, sortie le 29 mars 2023, visa affiché 154818. Décision : aucun contournement du contrôle de visa ; identité source contradictoire à corriger en amont.
- **155994 — Néneh superstar.** La fiche CNC source ne fournit pas d'œuvre exploitable. Le [CNC 154994](https://www.cnc.fr/professionnels/visas-et-classification/154994) désigne *Nehneh Superstar*, Ramzi Ben Sliman, sortie le 25 janvier 2023, comme Allociné 291767 ; durées 97/98 minutes. Décision : conserver l'ID, validation décochée ; confirmer ou corriger le visa source avant publication.

Ces quatre lignes contiennent leurs preuves et le motif d'ouverture dans `COMMENTAIRES`. Elles ne sont pas incluses dans la collecte ciblée des identités confirmées.

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

## Contrôles de publication

La [requête de contrôle versionnée](../../ingestion/dbt/analyses/allocine_issue_51_validation.sql) a été exécutée avant publication : 25 lignes, 25 dates absentes, une ligne de matching par visa et par ID. Elle contrôle aussi le dernier essai, les horodatages ex æquo, le staging, la date finale, les genres et les réalisations publiées. Les résultats intermédiaires sont inspectés en mémoire, sans export de données.

État initial à filtres identiques : 4 913 films rapprochés avec date legacy dans 2004–2024, dont 4 888 sélectionnables par leur date dbt dans la même période et 25 dates dbt absentes. Les 25 films n'ont aucun genre publié et possèdent 26 lignes de crédits au total, dont deux réalisateurs pour Rue des cités. Le catalogue final compte 6 138 films, visas et identifiants uniques. La quarantaine complète compte 144 lignes sur 16 ID au contrôle préalable ; les volumes historiques de l'issue 52 ne constituent donc pas son état courant.

Après la dernière reconstruction, la requête versionnée a été réexécutée sur les 25 dossiers. Pour chaque cas confirmé : bon ID dans raw et staging, nouveau succès du run `c268eff8-8fb2-43e7-8178-45343d5902a8`, date attendue identique dans staging et fnl, genres présents et ensemble exact des réalisateurs. Les 25 identifiants de film sont conservés. Chaque visa et ID Allociné du lot reste associé à une seule ligne de matching ; chaque dernier horodatage est unique. Aucun doublon de clé dans les associations finales film/rôle/personne ou film/genre.

Les quatre dossiers ouverts conservent leur validation décochée, leur dernière tentative historique, leur date finale absente et leur crédit manuel antérieur. Aucun nouveau scraping ne les a traités. La quarantaine reste à 144 lignes sur 16 ID.

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

Les quatre autres visas — 122169, 146143, 154816 et 155994 — restent sans date finale et sont détaillés dans la section « Cas ouverts ».

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

L'issue 51 reste ouverte pour les quatre visas contestés. Leur reprise exige de confirmer ou corriger la source CNC, puis de reprendre le parcours ciblé documenté dans le guide métier.

Réserve préexistante sur le référentiel : `raw.credit_holders` conserve les fiches « Isild / Besco » (`16f3b992-c8a8-6b19-6950-ca5ebbdded1f`) et « Ramzi / Sliman » (`6b4d3496-a085-c6cb-9f80-ee40a89902d3`). Les références d'identité portent les noms Isild Le Besco et Ramzi Ben Sliman. Le crédit Charly est corrigé par son association ; le nom Ramzi Sliman reste une réserve du dossier ouvert 155994. Les fiches personne et leurs autres éventuelles associations ne sont pas fusionnées par cette revue.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | Qualification des 25 conflits, preuves d'identité, correction du documentaire de David Dufresne et suivi de publication. |
