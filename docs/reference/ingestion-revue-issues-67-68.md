# Associations Allociné rejetées et dates réservées — issues 67 et 68

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-15

**Status:** vérification de publication en cours

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
L’identité, les crédits et les événements de diffusion ne peuvent pas encore être
publiés séparément par le contrat actuel. Cette capacité reste dans
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
imposer une récupération spéculative. La recherche de remplacements reste possible.

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
existant de Hugo est conservé ; celui de Paulo est confirmé documentairement mais
sa publication reste réservée au rattachement sûr, sans nouvelle personne ni genre
inféré. Dépendance #73.

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
Ils évoquent une duplication de personne ; aucune fusion ni suppression n’est
réalisée sans revue des associations et corrections de ces UUID. Les deux sont
hors cohorte de dates 2004–2024 actuellement, puisque la date finale est nulle.
La réserve de rattachement protège aussi d’un troisième UUID issu du nom Allociné.

## Vérifications et impact

Avant publication, le 15 novembre 2026 : 6 138 films, 181 976 associations finales,
54 577 credit-holders et 102 lignes de quarantaine active. Huit visas portent
101 lignes invalidées ; la dernière ligne appartient à Dogwatch. Neuf succès
bruts existent pour les huit associations rejetées : deux pour 155365.

La prévisualisation PostgreSQL en lecture seule restitue exactement les 101 crédits
historiques : zéro crédit manquant par `(allocine_id, credit_holder_id, role_id,
type, full_name, legal_name)`, y compris les UUID des sociétés. Le staging passe
théoriquement de 5 921 à 5 913 visas ; il ne contient plus les huit associations.

Les tests SQL vérifient les différentes tentatives, le changement de cible, le
partage d’un ID entre visas et les identifiants de sociétés de l’historique.
Compilation dbt dans un projet isolé du worker : réussie. La publication, les
contrôles finaux et les empreintes avant/après sont consignés ci-dessous après
exécution. Les résultats exploratoires ne sont pas exportés.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-15 | Joel Teixeira | Décisions sur les huit associations invalidées et les quatre réserves de date ; contrôle de l’historique et des clés avant publication. |
