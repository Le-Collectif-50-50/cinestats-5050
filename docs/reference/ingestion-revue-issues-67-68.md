# Associations Allociné rejetées et dates réservées — issues 67 et 68

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-15

**Status:** publié et vérifié ; rattachements réservés suivis séparément

## Périmètre et décision

La revue porte sur huit associations historiques invalidées (#67) et quatre films
réservés pour leurs dates/supports (#68), tous millésimes d’agrément confondus.
Les données brutes, corrections de genre et tableaux de bord sont conservés.
Les `visa_mismatch` exclus des revues #52/#53 ne sont pas réexaminés.

Pour #67, le rejet est une décision sur le triplet
`(source_record_id, visa_number, allocine_id)`. Il porte sur toutes les tentatives
de cette association, y compris une recollecte future, sans interdire cet ID à un
autre visa. Le registre versionné conserve motif, URL, date, auteur et run/hash
témoin. `ops.allocine_rejected_results` conserve toutes les tentatives avec leur
décision ; `ops.allocine_rejected_credits` restitue les crédits du dernier succès
rejeté par visa. Le brut reste inchangé. Le staging retire les rejets **avant** le
classement des succès, empêchant le repli sur un autre ancien succès invalidé.

Pour #68, les quatre matching restent vides et les quatre dates finales restent
nulles : les dates observées ne prouvent pas une sortie nationale française.
Le rattachement Allociné publierait sa date sans qualification de support. Les
crédits prouvés peuvent toutefois être corrigés par le circuit manuel existant.
La séparation générale des événements de diffusion reste dans
[#73](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/73).
Aucun scraping ni changement de support ou de schéma de diffusion n’est exécuté.

## Huit décisions de rejet et recherches de remplacement (#67)

Les titres et réalisations attendus sont contrôlés contre `raw.films` et la revue
[#52](ingestion-revue-credits-issue-52.md). Les sources ci-dessous établissent la
mauvaise identité historique ou documentent le projet attendu ; elles ne valent
pas validation automatique d’une autre fiche Allociné.

| Visa | ID rejeté | Crédits historiques | Décision et remplacement |
| --- | --- | ---: | --- |
| 120846 | 109311 | 18 | Rejet : Cargo de Clive Gordon. Attendu Biljana Tutorov, documentaire Cargo / Toi seul entends l’orage. Aucun nouvel ID établi ; titre définitif à prendre en compte dans une recherche ultérieure. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=109311.html), [catalogue FCS](https://www.fcs.rs/wp-content/uploads/2022/06/FCS-2017-documentaries.pdf). |
| 155365 | 260988 | 16 | Rejet : Marion Laine, 2019. Le candidat courant **1000037190** reste séparé : Stéphanie Pillonca, dernier essai `needs_review` ; lien visa/fiche insuffisamment prouvé pour publier ses crédits. Le champ source `VALIDATION_MANUELLE` est désormais TRUE, observé le 15/11 ; il est conservé, sans le présenter comme une preuve indépendante. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=260988.html), [candidat](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000037190.html). |
| 160111 | 319142 | 5 | Rejet : Nostos de Franco Piavoli, 1989. Le titre attendu Il ritorno / Stefano Chiantini est attesté par Rai Cultura ; aucun remplacement Allociné confirmé. Ne pas publier une autre œuvre de la filmographie du réalisateur sur la seule proximité du titre. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=319142.html), [Rai Cultura](https://www.raicultura.it/cinema/articoli/2022/09/Il-ritorno-di-Stefano-Chiantini--51a742b2-2f1e-4068-926b-a7c6effa14a8.html). |
| 161050 | 5459 | 21 | Rejet : Starewitch, 1930. Projet Daffis / Marchand distinct, encore documenté dans les aides au développement CNC 2024 ; aucune fiche de remplacement établie. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=5459.html), [CNC](https://www.cnc.fr/professionnels/aides-et-financements/resultats-commissions/aide-au-developpement-de-projets-doeuvres-cinematographiques-de-longue-duree--resultats-de-la-commission-18-novembre-2024_2306872). |
| 162402 | 236434 | 15 | Rejet : Les Nuits blanches du facteur / Konchalovsky. Attendu Tiago Hespanha, agrément 2025 ; aucun candidat Allociné indépendamment confirmé. Maintien sans ID. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=236434.html). |
| 164127 | 323303 | 11 | Rejet : Le Faune de marbre / Mario Bonnard, 1920. Attendu Augusto Zanovello, animation, agrément 2025 ; aucune nouvelle fiche établie. Maintien sans ID. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=323303.html). |
| 165043 | 112135 | 8 | Rejet : Phir Hera Pheri / Neeraj Vora. Le projet Hera / Catarina Mourão est documenté par le catalogue ICA 2026 ; aucun ID Allociné confirmé. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=112135.html), [catalogue ICA 2026](https://ica-ip.pt/fotos/downloads/30_01_ica_2026_estatistica_v02_922395551698c6192b595c.pdf). |
| 166339 | 170268 | 7 | Rejet : court métrage de Tex Avery, 1944. Attendu Mohammed Raouf Sebbahi, fiction, agrément 2025 ; aucune fiche de remplacement établie. Maintien sans ID. [Ancienne fiche](https://www.allocine.fr/film/fichefilm_gen_cfilm=170268.html). |
| **Total** | **8 associations** | **101** | **Sept ID vides et un candidat courant séparé, sans validation automatique.** |

Ces maintiens sans ID sont des recherches non résolues, et non la preuve de
l’absence d’une fiche. Les huit décisions satisfont l’invalidation demandée sans
imposer une récupération spéculative. La recherche de remplacements reste ouverte dans
[#76](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/76), qui reprend
explicitement ces huit œuvres sans modifier les lots #69 et #70.

## Quatre décisions de date et de support (#68)

### 152119 — To sail close to the wind / Vardia / Dogwatch

Identité confirmée : Gregoris Rentis, documentaire gréco-français, Good Fortune
Films. La [fiche du réalisateur](https://www.grentis.com/home-2) indique 78 minutes,
2022. Le [festival Visions du Réel](https://www.visionsdureel.ch/en/film/2022/dogwatch/)
confirme Vardia / Dogwatch et 78 minutes. La revue CNC antérieure relève 81 minutes ;
[Allociné 309459](https://www.allocine.fr/film/fichefilm_gen_cfilm=309459.html)
indique 73 minutes et le 15/11/2022 directement à la télévision.

Les différences 73/78/81 minutes restent des **versions ou métadonnées non
réconciliées**, pas la preuve d’œuvres distinctes. Le point d’accès CNC n’a pas
restitué une fiche exploitable lors de cette revue ; les 81 minutes ne sont pas
revendiquées comme une nouvelle mesure. Réserve de version explicite. Le crédit
manuel Gregoris Rentis est conservé, une seule fois. Matching différé jusqu’à #73 ;
aucune date TV transformée en date salle.

### 151848 — Loin de la route / Longe da estrada

Identité et **coréalisation confirmées** par le
[dossier du producteur Leopardo Filmes](https://leopardofilmes.com/filme/download-presskit/133/presskit-longe-da-estrada) :
Hugo Vieira da Silva, coréalisé avec Paulo MilHomens. Le
[programme ArteKino](https://www.ube.fr/wp-content/uploads/2025/10/AK-FLYER-2025_EN.pdf)
confirme les deux réalisateurs, la coproduction Portugal/France, 2023 et 105 minutes.

Le [programme officiel ArteKino](https://artekinofestival.arte.tv/blog/festival-de-cinema-europeen-en-ligne-1er-au-31-decembre/)
qualifie la diffusion du 1er au 31 décembre 2025 de **festival en ligne**.
La date du 01/12/2025 de la fiche candidate 1000019803 n’est donc pas qualifiée
ici de première sortie salle, ni de diffusion TV linéaire. Un autre catalogue
publie 68 minutes : le rapprochement de versions n’est pas établi. Le crédit
existant de Hugo est conservé. Le crédit de Paulo est ajouté dans le circuit
manuel, avec son UUID existant `8ed2a8af-cb72-6381-639f-1cd6299e75e9` :
aucun nouveau profil ni changement de genre. La date et le matching restent
réservés à #73.

### 112488 — Il mare buio / Mare Nero

Identité confirmée : Roberta Torre, Babe Films / Cattleya / Rai Cinema, projet
2005–2006. [Film Commission Campania](https://fcrc.it/mare-nero-the-dark-sea/) et
[Cineuropa](https://cineuropa.org/fr/film/70385/) relient Mare Nero / Mare buio.
Cineuropa documente 83 minutes et une sortie **italienne** du 25/08/2006 : cette
information ne prouve pas une sortie salle française.

[Allociné 119779](https://www.allocine.fr/film/fichefilm_gen_cfilm=119779.html)
affiche le 15/05/2022 sur Amazon Prime Video. Maintien de la réalisation manuelle
Roberta Torre ; ni date italienne ni date VOD recopiée comme date salle française.
Matching différé jusqu’à #73. Aucune preuve supplémentaire d’une sortie nationale
française n’a été établie.

### 160360 — La Nuit de l’enfance / From Dawn to Dawn

Identité confirmée : Xisi Sofia Ye Chen, 93 minutes, Espagne/France, 2026. Le
[programme officiel Visions du Réel](https://www.visionsdureel.ch/en/vdr-2026-screening-at-forum-des-images-in-paris/)
relie les deux titres et documente une séance au Forum des images le 12/11/2026.
Le [programme des Écrans de Chine](https://www.chine-info.com/static/content/french/LaChineenFrance/Cin%C3%A9ma/2026-09-08/1546723321273147392.html)
situe le 25/09/2026 à 20h au 5 Caumartin dans l’ouverture du festival. Le libellé
« en salle » d’[Allociné 1000044751](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000044751.html)
ne suffit pas à transformer cette séance festivalière en sortie nationale.

Le numéro **2023004357**, affiché comme visa par Allociné, reste **non qualifié**.
Le point d’accès CNC n’a pas rendu une fiche exploitable ; le format du numéro ne
suffit pas à conclure qu’il s’agit d’une immatriculation. Visa source **160360
conservé**, matching différé jusqu’à #73.

Deux UUID de réalisation existent déjà sur ce visa :
`647965a6-f111-f5bd-2109-bfc8c7ef6d75` (Ye Chen Xisi Sofia) et
`6d9243e0-503f-d657-df7d-c7b471096891` (Sofia Ye Chen Xisi).
La source CNC `raw.films.REALISATEUR` contient **YE CHEN Xisi Sofia**. Les deux
UUID n’ont chacun qu’une association, sur ce même film et le même rôle, et le
programme officiel n’indique qu’une réalisatrice. La seule association redondante
vers `6d9243e0…` est retirée ; `647965a6…`, conforme à la source CNC, est conservé.
Les deux fiches personne, leurs UUID et leurs genres female restent conservés :
aucune fusion globale, aucun nouveau découpage arbitraire du nom. La note de la
ligne manuelle conservée garde l’ancien UUID, auteur, date et source de décision.
La date nulle exclut ce film de la cohorte de sorties 2004–2024.

## Vérifications et impact

Avant publication, le 15 novembre 2026 : 6 138 films, 181 976 associations finales,
54 577 credit-holders et 102 lignes de quarantaine active. Huit visas portent
101 lignes invalidées ; la dernière ligne appartient à Dogwatch. Neuf succès
bruts existent pour les huit associations rejetées : deux pour 155365.

La prévisualisation PostgreSQL en lecture seule restitue exactement les 101 crédits
historiques : zéro crédit manquant par `(allocine_id, credit_holder_id, role_id,
type, full_name, legal_name)`, y compris les UUID des sociétés. Le staging passe
théoriquement de 5 921 à 5 913 visas ; il ne contient plus les huit associations.

**Publication #67 terminée** le 15/11/2026 à 18h02 CET : 47 modèles, un seed,
114 tests de données, aucune erreur et six avertissements. Les avertissements
restants sont : 218 ID Allociné absents, 893 ID Mubi absents, 773 ID TMDb absents,
cinq valeurs Mubi dupliquées, deux valeurs TMDb dupliquées et une ligne de
quarantaine (Dogwatch). Les 13 régressions SQL PostgreSQL et Ruff passent.

| Mesure | Avant #67 | Après #67, avant corrections #68 |
| --- | ---: | ---: |
| Films finaux | 6 138 | 6 138 |
| Associations finales de crédits | 181 976 | 181 976 |
| Credit-holders finaux | 54 577 | 54 513 |
| Crédits en quarantaine active | 102 | 1 |
| Crédits rejetés consultables séparément | Non séparés | 101 |
| Tentatives des associations rejetées | 9 dans raw | 9 dans raw et vue de rejet |
| Doublons de clé de crédit / crédits orphelins | 0 / 0 | 0 / 0 |

Les 64 credit-holders retirés du référentiel dérivé ne portent aucun crédit publié :
ils provenaient uniquement des mauvaises fiches. Les bruts et les corrections de
personnes ne sont pas supprimés. Cela ne représente pas 64 personnes perdues dans
les statistiques.

Empreintes avant/après #67 identiques : films
`022ec3294ce3f64af0b437e2e5d30f97`, crédits
`9c65787c0e408388dc3aec0ab856636b`. La jointure complète films/crédits/personnes/rôles
sur les sorties du 01/01/2004 au 31/12/2024 contient **160 578 lignes**, empreinte
`02ecf80eae807fee74637cc981627142`, également identique. À clés et filtres constants,
**aucun changement statistique** n’est imputable à l’invalidation. Les sept
rattachements #52 et les dix-huit #53 sont donc préservés.

Les 24 lectures Metabase sans cache (identité et crédits des douze films, cartes
100 et 101) passent après #67, puis à nouveau après les corrections manuelles #68.
Le contrôle des cohortes antérieures retrouve les sept films #52 et les dix-huit
#53 avec leurs matching, staging et UUID attendus, sans erreur.

### Publication des deux corrections manuelles #68

Dans le [Google Sheet source](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit?gid=538542575#gid=538542575),
onglet `film_credits` : ajout du crédit Paulo, puis retrait de la seule ligne
redondante de Sofia. Les positions finales sont **ligne 410** (Paulo) et
**ligne 158** (réalisation conservée de La Nuit de l’enfance). Les notes gardent les
sources et les décisions. Les formats et la validation de date sont conservés,
contrôlés par l’API native ; aucune vérification visuelle Google n’est revendiquée.
Les deux fiches personne de Sofia restent présentes.

Deux ingestions complètes sans scraping ont été exécutées séquentiellement :

- `qualified-flamingo`, `99933aff-56b5-46d8-bf92-d8a4c5d9bd06`, Airbyte **58**,
  publication du crédit Paulo, état **Completed**.
- `cautious-bonobo`, `bcdc8458-feb0-4a91-b7e3-eb470d1bb3bb`, Airbyte **59**,
  publication de la déduplication, état **Completed**, terminé le 15/11 à **18h12 CET**.

L’invocation finale de phase 2 est
`af52dfab-7b36-4e57-a725-7c2a666f3b78` : 47 modèles, un seed, 114 tests,
aucune erreur, les six avertissements décrits ci-dessus. Les 218 ID Allociné
absents restent inchangés : ce traitement n’invente aucun nouveau matching.

Résultat final : **6 138 films**, **181 976 associations**, **54 513 credit-holders**,
**une ligne de quarantaine active**, **101 crédits rejetés archivés**, aucun doublon
de clé ni crédit orphelin. Le staging conserve **5 913 visas**.

Les deux changements d’association se compensent en nombre : un ajout (Paulo,
151848) et un retrait redondant (Sofia, 160360). L’empreinte finale des crédits est
`fc3f6a244a99f4a827df57326c747faa`. En annulant analytiquement **uniquement** ces
deux changements, l’empreinte initiale
`9c65787c0e408388dc3aec0ab856636b` est retrouvée exactement : aucune autre
association finale n’a changé.

Les quatre matching et dates restent vides après Airbyte 59. Les empreintes des
films et des **160 578 lignes de statistiques 2004–2024** sont toujours identiques
à l’état initial. **Effet mesuré sur cette cohorte : zéro**. Les deux films corrigés
n’y entrent pas, parce que leur date reste inconnue. Ce constat ne valide pas la
complétude de leurs crédits pour tout le catalogue sans filtre de date.

Metabase, cartes 100/101 sans cache : une seule identité par film ; Hugo et Paulo
sur 151848 ; une seule réalisation sur 160360 ; Gregoris Rentis conservé une fois
sur 152119 ; Roberta Torre conservée sur 112488. Les huit visas #67 ne récupèrent
aucun crédit des mauvaises fiches.

Les [requêtes de contrôle](../../ingestion/dbt/analyses/allocine_issues_67_68_validation.sql)
permettent de reproduire compteurs, intégrité, empreintes et reconstitution.
Les résultats exploratoires ne sont pas exportés.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-15 | Joel Teixeira | Décisions sur les huit associations invalidées et les quatre réserves de date ; contrôle de l’historique et des clés avant publication. |
