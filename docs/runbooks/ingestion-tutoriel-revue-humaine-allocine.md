# Revoir une correspondance Allociné

**Owner:** Joel Teixeira  
**Dernière révision:** 2026-11-14  
**Status:** actif

## Objectif

Public : équipes métier Cinéstats 50/50.

Résoudre une correspondance signalée dans Metabase. Vérifier le film, documenter la décision, puis suivre sa publication. Aucun accès technique n’est nécessaire pour le parcours courant.

Les captures datent du 14 novembre 2026. Les chiffres peuvent évoluer. L’exemple « Steak » est réel. Les écrans ont été consultés uniquement. Aucune validation ni demande n’a été envoyée pour ce tutoriel. Les résultats après traitement décrivent les contrôles attendus.

## Préparer ses accès

Ouvrir ces trois espaces :

- [Metabase Operations](https://metabase.cinestats5050.fr/collection/7-cinestats-50-50-operations).
- [Source de données — id_matching](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit#gid=902822468), avec droit de modification.
- Les fiches publiques CNC et Allociné.

Un accès manque ? Contacter le référent data. Garder le visa et le titre.

## Retenir le parcours

**Repérer → Rechercher → Décider → Renseigner le Sheet → Demander une ingestion → Relancer le scraping si nécessaire → Demander une ingestion → Contrôler.**

| Action | Son effet |
| --- | --- |
| Modifier le Sheet | Enregistre la correction ou validation. |
| Demander une ingestion | Récupère le Sheet et actualise les données publiées avec les collectes déjà disponibles. |
| Lancer le scraping Allociné | Collecte à nouveau les fiches éligibles. |
| Demander une ingestion après scraping | Publie les nouveaux résultats collectés. |

**Cocher une case ne lance rien.** L’ingestion ne lance aucun scraping.

## 1. Repérer le besoin dans Metabase

1. Ouvrir [Scraping Allociné — À examiner](https://metabase.cinestats5050.fr/dashboard/7).
2. Regarder les compteurs et tableaux.
3. Choisir un film à examiner.
4. Saisir son **Visa CNC** exact. Valider avec Entrée.
5. Descendre au tableau de détails concerné.
6. Relever titre, visa, ID Allociné et motif.

![File de revue Allociné](assets/revue-humaine-allocine/01-file-revue.png)

*Repère : « Visa CNC » isole un film. « Titre contient » aide à rechercher.*

| Signal affiché | Signification | Travail métier |
| --- | --- | --- |
| Correspondances à vérifier — `needs_review` | Le rapprochement n’a pas pu être confirmé. Plusieurs films peuvent être proposés. | Rechercher l’œuvre et identifier sa bonne fiche. |
| Visas différents — `visa_mismatch` | Allociné présente un autre numéro de visa. | Vérifier s’il s’agit bien du même film. |
| Films introuvables — `not_found` | La recherche n’a rien trouvé. | Rechercher manuellement. Transmettre au référent si la reprise reste bloquée. |

Une ligne vide côté Allociné peut correspondre à plusieurs candidats. Lire le motif complet. Ne pas prendre le premier candidat par défaut.

Le filtre « Période du scraping » concerne uniquement le graphique. Les tableaux peuvent montrer des anomalies anciennes. Un graphique vide ne prouve pas leur résolution.

### Exemple : « Steak »

Ouvrir [l’exemple filtré sur 115952](https://metabase.cinestats5050.fr/dashboard/7?visa=115952).

![Détail de l’écart de visa pour Steak](assets/revue-humaine-allocine/02b-steak-detail.png)

*Repère : tableau « Visas différents — détails ».*

| Élément | Valeur observée |
| --- | --- |
| Titre CNC | Steak |
| Visa CNC | 115952 |
| ID Allociné | 110872 |
| Visa affiché par Allociné | 107925 |
| Réalisation Allociné | Quentin Dupieux |

Le signal demande une vérification. Il ne prouve pas une mauvaise correspondance.

## 2. Rechercher et comparer les preuves

1. Ouvrir le lien Allociné du tableau. Faire défiler horizontalement si nécessaire.
2. Rechercher le visa dans [Visas et classification CNC](https://www.cnc.fr/professionnels/visas-et-classification).
3. Comparer les informations ci-dessous.
4. En cas de doute, consulter le distributeur ou un dossier de presse.
5. Conserver les liens dans votre commentaire.

| Information | Vérification attendue |
| --- | --- |
| Titre | Même œuvre ; vérifier les titres alternatifs. |
| Réalisation | Même personne ou équipe de réalisation. |
| Année et sortie en salle | Dates compatibles ; distinguer salle, télévision et vidéo. |
| Pays, distribution, synopsis | Indices concordants ; écarter homonymes et remakes. |
| Visa | Noter les deux valeurs si différentes. |

Un titre identique ne suffit pas. Une différence de durée mérite examen. Elle ne tranche pas seule l’identité.

Pour « Steak », la [fiche CNC](https://www.cnc.fr/professionnels/visas-et-classification/115952) présente Quentin Dupieux, le visa 115952 et la sortie du 20 juin 2007.

![Fiche CNC de Steak](assets/revue-humaine-allocine/02c-preuve-cnc.png)

La [fiche Allociné 110872](https://www.allocine.fr/film/fichefilm_gen_cfilm=110872.html) présente le même titre, le même réalisateur et la même sortie en salle. Elle indique pourtant le visa 107925. Les durées diffèrent : CNC 84 minutes, Allociné 82 minutes. L’ensemble soutient le rapprochement. Le visa CNC reste la référence conservée.

![Visa affiché sur la fiche Allociné](assets/revue-humaine-allocine/02e-visa-allocine.png)

*Repère : « N° de Visa », dans « Infos techniques ».*

### Décider avant de modifier

| Conclusion de recherche | Décision |
| --- | --- |
| Bonne fiche, malgré un écart de visa | Conserver l’ID ; documenter puis valider manuellement. |
| Mauvaise fiche ; bonne fiche retrouvée | Corriger l’ID ; valider uniquement après vérification. |
| Plusieurs fiches plausibles | Laisser la validation décochée ; demander un second avis. |
| Aucune preuve suffisante | Documenter le doute ; conserver le cas ouvert. |
| Erreur d’affichage ou collecte bloquée | Transmettre au référent data. Une validation ne répare pas une panne. |

## 3. Renseigner la décision dans Google Sheets

1. Ouvrir l’onglet **id_matching**.
2. Rechercher le visa avec Ctrl+F ou ⌘F.
3. Vérifier le titre sur la même ligne.
4. Décocher **VALIDATION_MANUELLE** avant tout changement d’identité.
5. Compléter les champs ci-dessous.
6. Cocher uniquement après vérification concluante.
7. Attendre l’indication d’enregistrement dans Drive.

Ne pas trier une colonne seule. Ne pas créer une seconde ligne pour le même visa. Ne pas modifier le visa pour effacer l’alerte.

![Ligne Steak dans id_matching](assets/revue-humaine-allocine/03-gsheet-steak.png)

*Repère : visa 115952 et ID 110872. Ligne 994 lors de la capture. Rechercher toujours le visa : les lignes peuvent bouger.*

![Champs de justification et validation](assets/revue-humaine-allocine/03b-gsheet-validation.png)

*Repère : colonnes F à K. La case K994 est décochée dans l’état observé.*

| Colonne actuelle | Action métier |
| --- | --- |
| A — VISA | Conserver le visa CNC vérifié. Pour une correction de visa, contacter le référent data. |
| B — TITRE | Vérifier l’œuvre concernée. |
| C — ID ALLOCINE | Renseigner uniquement le nombre. Exemple : `110872`, extrait de l’adresse de la fiche. |
| F — UPDATED DATE | Saisir date et heure de revue. Exemple de format : `14/11/2026 14:30:00`. Utiliser l’heure réelle. |
| G — UPDATED BY | Renseigner votre nom. |
| H — COMMENTAIRES | Ajouter décision, preuves et liens. Conserver les remarques utiles précédentes. |
| I et J — CHECK DOUBLON… | Conserver les contrôles existants. Signaler un doublon au référent. |
| K — VALIDATION_MANUELLE | Cocher si l’ID renseigné désigne l’œuvre confirmée. Sinon laisser décoché. |

### Commentaire proposé pour « Steak »

À utiliser après votre propre vérification :

> Correspondance confirmée : Steak, Quentin Dupieux, sortie salle 20/06/2007. CNC : visa 115952 ; Allociné 110872 : visa affiché 107925. Titres, réalisation et sortie concordent. Durées différentes : 84/82 minutes. Visa CNC conservé. Sources : https://www.cnc.fr/professionnels/visas-et-classification/115952 et https://www.allocine.fr/film/fichefilm_gen_cfilm=110872.html. Revue : [date, heure, nom].

La validation concerne le rapprochement des œuvres. Elle ne certifie pas tous les champs Allociné. Après changement d’ID, refaire la vérification. La case ne mémorise pas l’ancienne identité.

### Autre cas : `needs_review`

Exemple observé : **Macunaima XXI**, visa **164876**, ID proposé **324310**. Le motif compare deux réalisateurs côté CNC avec un seul côté Allociné. Aucun visa concordant n’est disponible.

Rechercher la fiche et les crédits officiels. Confirmer la version exacte de l’œuvre. Si les preuves suffisent, renseigner l’ID puis justifier la validation. Sinon, laisser décoché et transmettre le dossier. Aucun choix n’est validé dans cet exemple.

## 4. Faire prendre en compte le Sheet

1. Ouvrir [Pipeline Overview](https://metabase.cinestats5050.fr/dashboard/2).
2. Cliquer **Demander une ingestion**.
3. Saisir votre nom ou adresse e-mail.
4. Saisir un motif précis. Exemple : « Revue Steak — visa 115952 — validation du rapprochement Allociné 110872 ».
5. Cliquer **Enregistrer la demande**.
6. Suivre les détails de la demande.
7. Attendre sa réussite avant le scraping.

![Point d’entrée de l’ingestion](assets/revue-humaine-allocine/04-pipeline-overview.png)

![Formulaire de demande d’ingestion](assets/revue-humaine-allocine/04b-formulaire-ingestion.png)

Le traitement commence après prise en charge. Le passage intervient environ toutes les cinq minutes. L’attente peut durer davantage. Éviter les envois répétés.

Ouvrir ensuite [Suivi par visa CNC](https://metabase.cinestats5050.fr/dashboard/11?visa=115952). Vérifier que l’ID synchronisé correspond au Sheet. Si la validation n’est pas visible, demander sa confirmation au référent data avant de poursuivre.

## 5. Relancer le scraping si nécessaire

| Situation | Suite |
| --- | --- |
| Validation d’un `visa_mismatch` ou `needs_review` | Nouvelle collecte nécessaire pour obtenir un résultat accepté. |
| Correction ou ajout d’ID Allociné | Nouvelle collecte nécessaire si cette cible n’a pas encore été traitée. |
| Collecte déjà réussie et données seulement non publiées | Passer à l’ingestion de publication. |
| Doute non résolu | Garder le cas ouvert. Ne pas forcer une validation. |
| `not_found` persistant, erreur ou blocage | Demander une reprise au référent data. |

### Lancement depuis Metabase

1. Revenir sur [Scraping Allociné — À examiner](https://metabase.cinestats5050.fr/dashboard/7).
2. Cliquer **Lancer le scraping Allociné**.
3. Renseigner identité et motif.
4. Conserver un petit volume convenu. Le formulaire propose 10 films.
5. Cliquer **Enregistrer la demande**.
6. Suivre la table des demandes.

![Formulaire de lancement du scraping](assets/revue-humaine-allocine/05-formulaire-scraping.png)

**Attention : le filtre visa ne cible pas ce lancement.** Le nombre limite un lot de films éligibles. Même avec « 1 », « Steak » n’est pas garanti. Pour traiter précisément votre film, transmettre au référent data : visa, titre, ID, commentaire et lien du Sheet. Demander une reprise ciblée. Aucun terminal n’est nécessaire côté métier.

Une seule demande Allociné peut rester active. Si l’envoi est refusé, consulter la demande existante.

| État | Lecture métier |
| --- | --- |
| En attente | Demande enregistrée, pas encore prise en charge. |
| Transmise / en cours | Traitement pris en charge. |
| Terminée | Traitement terminé techniquement. Vérifier votre film séparément. |
| Échec | Contacter le référent avec l’identifiant de demande et le message. |

« Terminée » ne garantit aucun succès individuel. Le lot peut même être vide. Un lancement effectué directement par le référent peut être absent de cette table.

## 6. Publier et vérifier le résultat

1. Actualiser la file de revue.
2. Filtrer à nouveau votre visa.
3. Vérifier la disparition de l’anomalie.
4. Consulter le suivi par visa. Vérifier un nouveau succès sur le bon ID.
5. Demander une nouvelle ingestion dans **Pipeline Overview**.
6. Attendre la réussite de cette demande.
7. Ouvrir [Qualité des données — dbt](https://metabase.cinestats5050.fr/dashboard/3). Examiner les alertes du traitement concerné.
8. Ouvrir [Fiche Film](https://metabase.cinestats5050.fr/dashboard/9?visa=115952). Vérifier les informations attendues.

Pour un écart accepté, les deux visas restent conservés. La disparition de l’anomalie peut précéder la publication. Elle ne remplace pas ce contrôle final.

### Clôturer le dossier

- [ ] Identité confirmée avec preuves.
- [ ] Bon ID présent dans le Sheet.
- [ ] Commentaire, auteur et date renseignés.
- [ ] Validation cohérente avec la décision.
- [ ] Modification récupérée par l’ingestion.
- [ ] Nouveau succès sur le bon film, si collecte nécessaire.
- [ ] Anomalie absente après actualisation.
- [ ] Ingestion de publication réussie.
- [ ] Fiche Film contrôlée ; réserves documentées.

Ces résultats sont attendus pour « Steak ». Aucun résultat après validation n’a été produit pour illustrer ce guide.

## Quand demander de l’aide

| Problème | Informations à transmettre au référent data |
| --- | --- |
| Preuves contradictoires | Visa, titre, liens et points de désaccord. |
| Correction absente après ingestion | Lien du Sheet, visa, heure de modification, demande concernée. |
| Film encore en revue après scraping | Visa, ID, dernière tentative et motif. Vérifier d’abord que le lot l’a traité. |
| Demande longtemps en attente | Identifiant et heure de demande. |
| Échec ou erreur de collecte | Identifiant de demande, message et visa. |
| Film absent ou incorrect après publication | Visa, champs attendus, preuves et demande d’ingestion. |

Garder les preuves dans **COMMENTAIRES**. Metabase ne constitue pas un journal complet des décisions humaines.

## Où retrouver ce tutoriel

Le [guide métier est publié dans Metabase Operations](https://metabase.cinestats5050.fr/document/1).

Un lien figure sur cinq dashboards : Pipeline Overview, Scraping Allociné — À examiner, Qualité des données — dbt, Suivi des données par visa CNC et Fiche Film.

Le présent fichier est la source versionnée. Le document Metabase reprend les étapes métier et les neuf captures. Les tableaux y sont présentés en listes. Après modification du guide, republier avec le script de maintenance ci-dessous. Les captures utilisent les URL du dépôt public, figées sur un commit publié de `main` ; conserver ces fichiers accessibles.

## Références de maintenance

Équipes métier : les étapes ci-dessus suffisent. Référent data : [fonctionnement de la revue](../../ingestion/dbt/README.md#examiner-les-correspondances-du-scraping-dans-metabase) et [reprise après validation](../../ingestion/scraping/allocine/README.md#reprendre-une-correspondance-validée-manuellement).

Depuis la racine, le référent data peut vérifier puis republier :

```bash
python3 infra/data/metabase-review-tutorial.py --env-file ingestion/.env
python3 infra/data/metabase-review-tutorial.py --env-file ingestion/.env --apply
```

La clé API reste dans l’environnement ou le fichier local hors Git. Le script actualise le document existant par son nom et sa collection. Il ajoute ou met à jour les liens, sans lancer d’ingestion ni de scraping. Publier les captures sur `main`, puis vérifier leur affichage dans Metabase. Le script utilise le commit local `origin/main` pour leurs liens : actualiser cette référence avant republication. `--image-ref <commit-publié>` permet de choisir explicitement leur version.

Captures authentiques des interfaces. Aucun écran de réussite simulé. Refaire les captures après changement du formulaire ou des colonnes.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | Guide métier illustré : recherche, décision, Sheet, ingestion, collecte et contrôle de publication. Exemple réel Steak et cas needs_review. Publication native dans Operations et liens sur cinq dashboards. |
