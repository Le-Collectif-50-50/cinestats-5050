# Revue du matching sans identifiant Allociné — issue 53

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

## Périmètre et état courant

Le relevé initial de l’[issue 53](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/53), le 14 novembre 2026, porte sur **236 lignes et 236 visas distincts** sans identifiant Allociné dans `raw.id_matching`. Le Google Sheet présente alors la même population. **Dix-huit correspondances sont maintenant synchronisées et publiées ; 218 lignes restent sans ID.** Le catalogue conserve 6 138 films. Le diagnostic initial de 243 lignes date du 13 novembre ; sept associations ont depuis été publiées dans [la revue #52](ingestion-revue-credits-issue-52.md).

Critère de sélection, catalogue complet sans filtre temporel :

```sql
SELECT "VISA", "TITRE", "ID_ALLOCINE"
FROM raw.id_matching
WHERE NULLIF(BTRIM("ID_ALLOCINE"::text), '') IS NULL
ORDER BY "VISA";
```

Avant correction, les derniers essais du lot se répartissent en **156 `not_found`, 64 `needs_review`, 11 `success` et cinq `visa_mismatch`**. Un ancien succès ne certifie pas l’identité : sept des onze succès désignent d’autres œuvres. Les cinq conflits actuels de visa restent exclus des corrections.

Les 236 cas sont classés avec leurs réserves. **Les dix-huit films publiés portent 206 associations finales de crédits, contre 18 avant intervention : gain net de 188 associations.** Quatre réalisations manuelles sont dédupliquées et trois corrections de personnes ajoutées, avec reprise des genres déjà établis. Neuf dates sont renseignées, dont trois dans 2004–2024. Les autres cas restent sans validation forcée.

## Recherche d’identité et de visa

Les 236 visas ont été interrogés sur le site du CNC. Les recherches complémentaires utilisent le réalisateur et les titres de travail ou définitifs. Les recherches directes et par réalisateur retrouvent 105 visas sur les 236 ; les autres résultats ne prouvent pas l’inexistence du visa. Les résultats officiels sont recoupés avec Allociné, les catalogues de festivals, la BnF, les producteurs et les distributeurs. Les 321 recherches directes Allociné incluent le titre source et, lorsqu’il diffère, le titre CNC ; 74 films ont rencontré au moins une erreur HTTP. Ces échecs techniques ne constituent pas des preuves d’absence de fiche.

Le CNC peut retrouver une œuvre dans son formulaire de recherche alors que sa page directe ne renvoie pas une fiche exploitable. C’est le cas de *Holy Field Holy War*, *La Forme des îles*, *Rocker*, *Les Madeleines* et *My Summer with Irene*. Un numéro introuvable ne doit donc pas être remplacé sur ce seul motif.

Une correspondance exige des éléments d’identité concordants : réalisation, titre définitif ou alias établi, format, année de production, synopsis, distribution et/ou visa. L’année d’agrément n’est pas une date de sortie. Aucune date CNC, étrangère, festivalière, télévisée ou VOD n’est copiée automatiquement dans la collecte Allociné.

Le `film_id` dépend du visa (`MD5(visa)::uuid`). Changer un visa impose de vérifier les lignes CNC, le matching, les crédits manuels et les éventuelles corrections liées. Les titres source et visas du présent lot sont conservés tant qu’un remplacement n’est pas confirmé et réconcilié.

## Dix-huit correspondances confirmées

Les liens CNC désignent les visas source. Pour 108532, 162647 et 164161, les fiches de visa courantes n’ont pas été retrouvées : les correspondances reposent sur la source d’agrément et les preuves externes citées.

| Visa | Titre source | ID Allociné | Titre définitif / fiche |
| --- | --- | --- | --- |
| 108532 | STRATOSPHÈRE GIRL | [54121](https://www.allocine.fr/film/fichefilm_gen_cfilm=54121.html) | Stratosphere Girl |
| 121175 | MONDE EN CHANTIER | [226863](https://www.allocine.fr/film/fichefilm_gen_cfilm=226863.html) | Holy Field Holy War |
| 122778 | COLLECTIONS DE MITHAT BEY (LES) | [171715](https://www.allocine.fr/film/fichefilm_gen_cfilm=171715.html) | 11'e 10 kala (10 to 11) |
| 123164 | ESCORT | [178537](https://www.allocine.fr/film/fichefilm_gen_cfilm=178537.html) | Escort |
| 131571 | ARCHIPELITUDE | [238434](https://www.allocine.fr/film/fichefilm_gen_cfilm=238434.html) | La Forme des îles |
| 132321 | IGUANAS | [220571](https://www.allocine.fr/film/fichefilm_gen_cfilm=220571.html) | Rocker |
| 144802 | Max Paradise ou les voies du seigneur | [299616](https://www.allocine.fr/film/fichefilm_gen_cfilm=299616.html) | Zamal Paradise |
| 145822 | Héritage (L') | [1000040394](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000040394.html) | La Terre de mon grand-père — Partie 1 : L’Héritage |
| 152946 | Cabines, la France et moi (Les) | [1000025088](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000025088.html) | Allo la France |
| 155426 | Soyons fous | [1000030792](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000030792.html) | Soyons fous |
| 155913 | Hommes, les dieux et les autres (Les) | [1000028254](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000028254.html) | Des hommes, des dieux et autres créatures |
| 157142 | Rosilene | [315137](https://www.allocine.fr/film/fichefilm_gen_cfilm=315137.html) | L’Or et le monde |
| 158123 | Portraits d'intérieurs | [1000012876](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000012876.html) | Les Madeleines |
| 158401 | Isola (L') | [326899](https://www.allocine.fr/film/fichefilm_gen_cfilm=326899.html) | My Summer with Irene |
| 159645 | Quand je serai grand | [1000025959](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000025959.html) | La Vie lumineuse |
| 162647 | Moustiques (Les) | [1000020147](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000020147.html) | Mosquitoes — Le Bambine |
| 163026 | Relève (La) | [1000037332](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000037332.html) | Belleville nous verra toujours danser |
| 164161 | Il cattivo è cattivo, il buono è buono | [328103](https://www.allocine.fr/film/fichefilm_gen_cfilm=328103.html) | Dentro |

- **108532 — Stratosphere Girl.** Titre, année et distribution (Togo Igawa, Burt Kwouk, John Ng) concordent avec le film de Matthias X. Oberg. Fiche Allociné incomplète, sortie française non renseignée. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/108532). [Preuve 1](https://www.stratospheregirl.com/_pages/director.php) [Preuve 2](https://www.filmfestival.nl/film/stratosphere-girl?switch_to=nl).
- **121175 — Holy Field Holy War.** La recherche CNC par réalisateur retrouve le visa 121175 sous ce titre définitif, Lech Kowalski, sortie du 26/03/2014. Ancien titre : Monde en chantier. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/121175). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/121175).
- **122778 — 11'e 10 kala (10 to 11).** Le CNC et le Festival de La Rochelle relient Les Collections de Mithat Bey à Pelin Esmer. Distribution Nejat İşler / Mithat Esmer et coproduction franco-turque concordantes. Pas de date française renseignée dans la fiche. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/122778). [Preuve 1](https://festival-larochelle.org/film/collections-de-mithat-bey-les/).
- **123164 — Escort.** Hélène de Crécy, 94 minutes, 2011, concordent avec le CNC et la BnF. La catégorie moyen métrage d’Allociné est incohérente avec cette durée ; identité confirmée indépendamment de ce classement. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/123164). [Preuve 1](https://catalogue.bnf.fr/ark%3A/12148/cb42695793m).
- **131571 — La Forme des îles.** Recherche CNC : visa 131571, Patrick Viret, sortie 14/10/2015. L’Académie des César et le site du réalisateur confirment le documentaire de 112 minutes ; titre de travail Archipélitude. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/131571). [Preuve 1](https://www.academie-cinema.org/films/la-forme-des-iles/-38459/) [Preuve 2](https://patrickviret.com/wp-content/uploads/2025/05/la-forme-iles-jaquette-DVD.pdf).
- **132321 — Rocker.** La recherche CNC retrouve le visa 132321, Marian Crişan, titre définitif Rocker. La fiche Allociné confirme réalisateur, fiction de 90 minutes et coproduction Roumanie/France/Allemagne. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/132321). [Preuve 1](https://www.allocine.fr/personne/fichepersonne-221773/filmographie/).
- **144802 — Zamal Paradise.** Visa Allociné 144802 identique au CNC, 156 minutes. DKpit K Dick est le nom artistique de Jean-Philippe Grosset ; source initiale Max Paradise ou les voies du seigneur. Sortie salle Allociné : 20/12/2021. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/144802). [Preuve 1](https://www.zinfos974.com/video-zamal-paradise-le-long-metrage-de-dkpit-sort-le-20-decembre/) [Preuve 2](https://tcd.trace.tv/en/media/view/361).
- **145822 — La Terre de mon grand-père — Partie 1 : L’Héritage.** Le CNC confirme le titre définitif sous le visa 145822 : Martin Esposito, documentaire de 85–86 minutes, sortie salle 22/04/2026 concordante avec Allociné. Ancien titre L’Héritage. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/145822).
- **152946 — Allo la France.** Recherche CNC : visa 152946, Floriane Devigne, sortie 18/03/2026. Swiss Films reprend le titre de travail Les cabines, la France et moi ; producteur, format, synopsis et réalisatrice concordent. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/152946). [Preuve 1](https://swissfilms.ch/fr/movie/allo-la-france/ed260e966c04457d8d0a3e6c471a2f07) [Preuve 2](https://www.oeilsauvage.com/allo-la-france).
- **155426 — Soyons fous.** Quentin Perez, documentaire de 128–129 minutes. La mention Allociné 2021001692 correspond au Numéro CNC du film ; le véritable N° de Visa est 155426. Visa conservé, validation manuelle d’identité documentée. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/155426). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/155426).
- **155913 — Des hommes, des dieux et autres créatures.** Svetlana Strelnikova, documentaire France/Grèce/Allemagne de 85–90 minutes. Le CNC comporte la graphie Strenikova ; la commission de coproduction et le catalogue documentaire établissent la réalisation exacte. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/155913). [Preuve 1](https://www.cnc.fr/professionnels/aides-et-financements/resultats-commissions/aide-a-la-coproduction-francogrecque--resultats-de-la-commission-du-22-novembre-2018_1080283) [Preuve 2](https://www.film-documentaire.fr/4DACTION/w_fiche_film/77925).
- **157142 — L’Or et le monde.** Le CNC 157142 relie Rosilene au titre définitif, 104 minutes, sortie 13/08/2025. Ico Costa correspond au nom de la source COSTA Ico (Federico). [CNC](https://www.cnc.fr/professionnels/visas-et-classification/157142). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/157142).
- **158123 — Les Madeleines.** Recherche CNC : visa 158123, Arthur Dreyfus, sortie 22/07/2026. La fiche Allociné confirme le documentaire de 83 minutes ; titre source Portraits d’intérieurs. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/158123). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/158123).
- **158401 — My Summer with Irene.** Recherche CNC : visa 158401, Carlo Sironi, sortie 24/06/2026. Fiche Allociné : Quell’estate con Irène, 91 minutes, Noée Abita, coproduction Italie/France. Titre de travail L’Isola. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/158401). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/158401).
- **159645 — La Vie lumineuse.** Le CNC relie Quand je serai grand au titre définitif, João Rosas, 99 minutes. Fiche Allociné : A Vida Luminosa, mêmes réalisateur, format et coproduction Portugal/France. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/159645). [Preuve 1](https://www.cnc.fr/professionnels/visas-et-classification/159645).
- **162647 — Mosquitoes — Le Bambine.** Les Moustiques est le titre français de Le Bambine / Mosquitoes. Les deux réalisatrices, le synopsis, la coproduction Italie/Suisse/France et Manny Films concordent ; Locarno 2025 confirme le titre et la coréalisation. Aucune date française précise n’est renseignée. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/162647). [Preuve 1](https://www.locarnofestival.ch/it/dam/jcr%3Aca55faee-3d18-4e78-b210-37bd3455494f/EN%2520Official%2520Selection%25202025.pdf) [Preuve 2](https://ticinofilmcommission.ch/it/video/96ce6c0c01ccb0e28483d7c1abd5946a/le-bambine) [Preuve 3](https://www.centralproductions.ch/portfolio/v/le-bambine).
- **163026 — Belleville nous verra toujours danser.** Recherche CNC : visa 163026, Hugo Sobelman. Distributeur et programme Cinébanlieue confirment documentaire de 87 minutes. La collecte courante donne le 10/02/2027, conforme au CNC ; un résultat web en cache indiquait le 17/02/2027. La date reste prévisionnelle. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/163026). [Preuve 1](https://www.alchimistesfilms.com/belleville-nous-verra-toujours-danser/) [Preuve 2](https://www.cinebanlieue.org/fichiers/edition/27/programme/Programme_Cinebanlieue-2026.pdf).
- **164161 — Dentro.** Elsa Amiel, documentaire de 95 minutes sur le théâtre de la prison de Volterra. Le financement régional atteste le titre de travail Il cattivo è cattivo, il buono è buono et le même projet. Fiche annoncée pour 2027, sans date salle précise. [CNC](https://www.cnc.fr/professionnels/visas-et-classification/164161). [Preuve 1](https://www.iledefrance.fr/tous-les-services/ma-region-pres-de-chez-moi/culture/cinema-et-audiovisuel/135026-aide-la-production-du-documentaire-il-cattivo-e-cattivo-il-buono-e-buono) [Preuve 2](https://www.cineforom.ch/resultats-de-l-aide-selective-2e-session-2024).

## Réserves et exclusions

- **143263 — Bonnes mères.** L’Allociné 225024 porte le visa CNC 152616, déjà associé dans le matching au titre source *Nora*. La source conserve deux projets de Hafsia Herzi, agréés en 2017 et 2020. Aucun second rattachement ni fusion des lignes financières n’est effectué. Il faut établir leur relation avant une éventuelle consolidation.
- **128285 — Être.** Le visa officiel désigne un film de Fara Sene, alors que la source indique Jean-Pascal Vinet. La proximité du titre ne résout pas cette divergence ; aucun ID ni nouveau visa n’est inventé.
- **121983 — DAU.** Les fiches 1000047642, 214100 et 280804 correspondent à plusieurs versions du projet. L’agrément source de 2008 ne suffit pas à choisir une version.
- **128897 — Mafrouza.** Les cinq candidats du scraper correspondent aux volets de la série. Le visa et la durée de chaque partie doivent être distingués.
- **160253 — Au cœur des ténèbres.** Deux fiches, 1000015175 et 288565, reprennent Rogerio Nunes. La fiche canonique reste à établir.
- **108563 — Tarfaya.** L’œuvre et son visa sont identifiés, mais la fiche 59823 ne fournit ni réalisation ni distribution suffisamment vérifiable. Le matching reste vide ; ce cas ne rejoint pas les correspondances confirmées.
- **147268 — Isabelle.** Le CNC désigne Mirko Locatelli ; la collecte de la fiche 1000005513 renvoie Jean-Paul Roux. Cet homonyme est refusé ; les autres fiches repérées désignent également d’autres réalisateurs.
- **158632 — L’Éternelle adolescente.** L’identité est recoupée, mais la mention Allociné 25852675 ne correspond ni au visa français 158632 ni au Numéro CNC 2023000177. Décision de revue du 14 novembre : maintien en réserve. Aucun changement du matching, des crédits ou des données brutes n’est effectué pour ce visa.
- **112488 — Il mare buio / Mare Nero.** [La Film Commission Campania](https://fcrc.it/mare-nero-the-dark-sea/) confirme Roberta Torre, Babe Films et le projet de 2005 ; [Cineuropa](https://cineuropa.org/it/film/70385/) relie les titres. La fiche Allociné 119779 affiche une date Amazon Prime Video du 15/05/2022 ; rattachement différé pour éviter une date de streaming dans les sorties salle.
- **160360 — La Nuit de l’enfance.** La fiche 1000044751 concorde avec Xisi Sofia Ye Chen, La Fabrica Nocturna Cinéma et le documentaire de 93 minutes. Sa date du 25/09/2026 correspond à l’ouverture des Écrans de Chine ; la sortie nationale reste à confirmer. [Catalogue documentaire](https://www.film-documentaire.fr/4DACTION/w_fiche_film/79489), [programme du festival](https://www.chine-info.com/static/content/french/LaChineenFrance/Cin%C3%A9ma/2026-09-08/1546723321273147392.html).
- **107159 et 114865.** Les œuvres *24 Passions* et *Dix millions de centimes* sont identifiées au CNC et dans des sources complémentaires. Les fiches Allociné 56043 et 54686 ne contiennent pas assez d’éléments d’identité pour une validation sur leur seul titre.
- **152119 — Dogwatch** et **151848 — Loin de la route.** Une date télévisée ne doit pas entrer dans les statistiques de sorties salle. Le premier cas reprend la réserve déjà établie dans #52 ; le second nécessite aussi de vérifier la coréalisation.
- **120846, 160111, 161050, 162402, 164127, 165043 et 166339.** Les anciens succès erronés restent traçables ; aucune réintroduction de ces ID ni suppression des données brutes.
- **149598, 158808, 162003, 165086 et 166181.** `visa_mismatch` actuels laissés hors traitement correctif.

[Bonne Mère — CNC 152616](https://www.cnc.fr/professionnels/visas-et-classification/152616), [Être — CNC 128285](https://www.cnc.fr/professionnels/visas-et-classification/128285), [24 Passions — FIDMarseille](https://archives.fidmarseille.org/film/2004-24-passions/), [Dogwatch — Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=309459.html), [Loin de la route — Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=1000019803.html).

## Coordination et contrôles de publication

Le scraping préexistant `71160481-33c3-4279-ac20-a43b0ae1913c`, commencé à 15 h 15, heure de Paris, est terminé en **Cancelled le 14 novembre à 16 h 58 min 15 s**. Son annulation n’a pas été déclenchée par cette revue. L’absence de processus Allociné dans le worker a été vérifiée avant la collecte ciblée. Le lot source et les derniers statuts sont restés inchangés après l’arrêt.

La première collecte ciblée a perdu sa connexion SSH avant réception du résultat complet, sans insertion. La reprise émet chaque fiche immédiatement et conserve les résultats en mémoire. Elle vise vingt ID explicites, dont les dix-huit retenus, l’homonyme Isabelle et le cas 158632 réservé. Aucune configuration partagée n’est modifiée. La reprise produit treize succès automatiques, deux conflits de numéro et cinq réserves d’identité, sans erreur technique. Après revue, dix-huit fiches sont insérées en succès ; les cas 147268 et 158632 ne sont pas insérés. Les cinq validations manuelles concernent 108532, 123164, 155426, 155913 et 157142. Elles appliquent la validation source explicite aux seules réserves d’identité ; aucune erreur technique n’est transformée en succès.

Les dix-huit visas ont été retrouvés par lecture fraîche des lignes existantes, puis les cellules modifiées ont été relues par API. Les colonnes de titre, visa, autres ID et formules de contrôle sont conservées. Les contraintes natives de date et de booléen sont préservées ; chaque visa et chaque ID ajouté est unique. Les trois onglets modifiés ont aussi été consultés dans le rendu Google Sheets à 100 %. Les commentaires longs restent consultables dans la barre de formule et les notes, avec les dimensions existantes.

Source : [Cinéstats 50/50 — Source de données](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit#gid=902822468). Auteur de revue : « Revue automatisée — mandat Joel Teixeira ». Date native des corrections : **14 novembre 2026 à 23 h 24 min 55 s, heure de Paris**. Les notes conservent les anciennes métadonnées et les preuves d’identité.

### Réalisations dédupliquées

| Visa | Association source | Ancienne personne | Personne retenue | Genre conservé |
| --- | --- | --- | --- | --- |
| 144802 | `film_credits!C248:E248` | Jean-Philippe Grosset | DKpit K Dick, `1ba5fc71-720b-8778-e4b7-437b0f9fbe73` | male |
| 155913 | `film_credits!C409:E409` | Svetlana Strenikova | Svetlana Strelnikova, `91bf7c98-bb52-b68e-7fcc-ca850839c109` | female |
| 157142 | `film_credits!C139:E139` | Ico (Federico) Costa | Ico Costa, `c0b1e78e-6b87-d641-27d1-348910342562` | male |
| 158123 | `film_credits!C6:E6` | Dreyfus Arthur | Arthur Dreyfus, `e1308ce2-4391-fec7-ab53-e7d022133309` | male |

Les profils correctifs `credit_holders!A688:I690` concernent Arthur Dreyfus, DKpit K Dick et Svetlana Strelnikova. La structure native de la ligne 687 est reprise. Les genres proviennent des corrections déjà présentes aux lignes 12, 169 et 343, respectivement ; aucune nouvelle inférence n’est faite. Ico Costa possède déjà une fiche avec le genre `male`. Les anciennes fiches sont conservées. Le film et le rôle de chaque association restent identiques ; aucune fusion globale d’alias n’est créée.

### Exécutions et résultat publié

La connexion Airbyte effective est **Google Sheets → Postgres**, ID `73f920cb-a0b9-4a22-b863-45158b7ed66e`. Elle synchronise les sources partagées.

- Première synchronisation : flow `9cedb360-9f52-458c-b97e-bdcd708da2c1`, job Airbyte **49**, terminé en `Completed` le 14 novembre à **23 h 32**, heure de Paris. Les dix-huit ID et leurs validations ont été vérifiés dans `raw` avant insertion.
- Collecte insérée : `939b95e5-fa2d-4428-a7c8-676651dffe2c`, **18 succès, dont cinq validations manuelles**, aucune écriture des deux candidats réservés/refusés.
- Publication : flow `e93b2968-8d47-4099-8edf-f6f20798f834`, **issue-53-publier-dix-huit-correspondances**, terminé en `Completed` le 14 novembre à **23 h 41 min 36 s**, heure de Paris. Le job Airbyte **50** reprend aussi la précision de date prévisionnelle ajoutée au commentaire de 163026, puis les deux phases dbt sont exécutées.
- Invocation dbt finale : `d3ae6782-9178-49ab-bd56-b9373dcddf6b` ; **45 modèles réussis, 96 tests passés, une opération réussie, six avertissements et aucune erreur**.

La [requête de contrôle versionnée](../../ingestion/dbt/analyses/allocine_issue_53_validation.sql) fige les 236 visas, les décisions et les comptages de crédits observés avant intervention. Les relevés initiaux en lecture seule sont comparés aux résultats publiés. Aucun export de résultats n’est requis.

| Mesure | Avant | Après |
| --- | ---: | ---: |
| Lignes sans ID Allociné, catalogue complet | 236 | 218 |
| Films du catalogue | 6 138 | 6 138 |
| Associations finales sur les 18 films retenus | 18 | 206 |
| Associations finales, catalogue complet | 181 788 | 181 976 |
| Dates absentes sur le lot initial de 236 visas | 236 | 227 |
| Films du lot datés dans 2004–2024 côté dbt, sans autre filtre | 0 | 3 |
| Films du lot datés dans 2004–2024 côté legacy, sans autre filtre | 0 | 0 |
| Crédits en quarantaine, catalogue complet | 102 | 102 |
| Doublons de clé de crédit final | 0 | 0 |
| Crédits finaux orphelins | 0 | 0 |

Les **204 associations scrapées rattachées** sont toutes présentes dans les crédits finaux. Elles incluent seize réalisations déjà présentes manuellement après déduplication. Les réalisations de *Stratosphere Girl* et *Escort* restent exclusivement manuelles, leurs fiches collectées étant incomplètes : deux associations supplémentaires portent le total final à 206. Le gain net est donc **188 associations**, et non 204 personnes. Le sous-lot possède dix-neuf réalisations, dont les deux coréalisatrices de *Mosquitoes* ; *Dentro* apporte une réalisation auparavant absente. Les identifiants des 236 films du lot sont conservés.

Les trois dates nouvelles dans 2004–2024 sont celles de **Holy Field Holy War (26/03/2014)**, **La Forme des îles (14/10/2015)** et **Zamal Paradise (20/12/2021)**. Ce décompte utilise uniquement la date finale et la jointure par visa. Il ne mesure pas à lui seul une variation des indicateurs de parité à tous leurs filtres métier. Les dates restantes concernent cinq sorties 2025–2026 et une sortie prévisionnelle en 2027. Une date absente ne prouve pas une œuvre hors période.

Les cartes Metabase **100 — Identité** et **101 — Crédits**, interrogées sans cache pour les dix-huit visas, passent **36 contrôles** : une identité par visa, date et `film_id` attendus, nombres de crédits conformes et réalisations exactes. Les quatre noms corrigés sont uniques dans les réalisations de leur film, avec leur genre conservé ; les deux réalisatrices de *Mosquitoes* restent présentes.

Les avertissements dbt restent limités aux six familles initiales : **218 ID Allociné absents** (contre 236), **893 ID Mubi absents**, **773 ID TMDB absents**, **cinq valeurs Mubi dupliquées**, **deux valeurs TMDB dupliquées** et **102 crédits en quarantaine**. Les cinq conflits actuels de visa et le visa 158632 conservent leur matching vide, leur validation décochée et leur statut antérieur. Aucun flow ni dashboard n’est modifié.

L’issue reste ouverte pour les **218 cas sans correspondance publiable**. Le registre ci-dessous distingue la réserve explicite, les homonymes, les dates de diffusion, les versions multiples et les recherches non concluantes. Ces dernières ne démontrent pas une absence de fiche.

## Registre de qualification du lot

Chaque ligne compte un visa source, sans filtre temporel. « Recherche non concluante » signifie qu’aucune fiche n’est assez étayée ; l’absence de fiche n’est pas démontrée. Les ID suivis des cas réservés ou refusés ne sont pas des rattachements validés.

| Qualification | Visas |
| --- | ---: |
| Recherche non concluante | 145 |
| Candidats non confirmés | 47 |
| Fiche trop incomplète | 3 |
| Correspondance publiée | 18 |
| Identité confirmée, date streaming | 1 |
| Ancien succès erroné (#52) | 7 |
| Versions multiples | 1 |
| Réalisation CNC incompatible | 1 |
| Série en plusieurs volets | 1 |
| Projet déjà représenté | 1 |
| Homonyme refusé | 1 |
| Conflit actuel hors correction | 5 |
| Identité probable, date TV | 1 |
| Identité confirmée, date TV | 1 |
| Réserve demandée après revue | 1 |
| Deux fiches Allociné | 1 |
| Identité confirmée, date festivalière | 1 |
| **Total** | **236** |

| Visa | Titre source | Qualification | Motif / candidat suivi |
| --- | --- | --- | --- |
| 91424 | OMBRE DE LA VILLE (L') | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 100544 | CONCORDIA | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 103114 | BANDIT (LE) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 125796, 128006, 34976, 17646, 56033 |
| 103774 | NO DEBES ESTAR AQUI | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 107159 | PASSIONS | Fiche trop incomplète | 24 Passions confirmé au CNC et au FID ; fiche Allociné sans réalisation ni durée, lien non suffisamment établi. ID 56043 |
| 107175 | SÉQUENCES MONGOLES | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 108320 | SOLITUDE DU VER À SOIE (LA) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 108532 | STRATOSPHÈRE GIRL | Correspondance publiée | Stratosphere Girl : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 54121 |
| 108563 | BAB LBHAR (LE VOYAGE IMMOBILE) | Fiche trop incomplète | Tarfaya identifié au CNC et dans les festivals ; fiche Allociné sans réalisation ni distribution vérifiable, rattachement différé. ID 59823 |
| 108627 | ROUGH FOOTAGE | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 109446 | FRIPE (LA) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 109693 | SIDNEY POITIER : UN RÊVE AMÉRICAIN | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 110129 | CORPS BIEN TEMPÉRÉS (LES) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 111790 | D'UN VILLAGE À L'AUTRE | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 112031 | PERROQUET BLEU (LE) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 112488 | IL MARE BUIO | Identité confirmée, date streaming | Mare Nero (Mare buio), Roberta Torre, Babe Films, 2005–2006 : identité recoupée avec la Film Commission Campania et la fiche Allociné. Date affichée 15/05/2022 sur Amazon Prime Video ; publication différée. ID 119779 |
| 112841 | ETRANGÈRE (L') | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000012579, 177540, 110544, 114818, 199326 |
| 113171 | CHARME DES IMPOSSIBILITÉS (LE) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 114153 | CHANTEUR (LE) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 240037, 239755, 183059, 37073, 3203 |
| 114813 | LEÇON DE CHOSES | Candidats non confirmés | Données d’identité absentes sur les fiches candidates.  ; candidats examinés : 18582, 5712 |
| 114865 | DIX MILLIONS DE CENTIMES | Fiche trop incomplète | Dix millions de centimes confirmé au CNC ; fiche Allociné sans réalisation ni durée, preuve insuffisante. ID 54686 |
| 116071 | CAROVANA | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 116418 | TERANGA BLUES | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 116494 | MOVEON.ORG | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 116737 | GUSTA EL CHILE ? (LE) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 116883 | QUI N'AIME PAS AYSE ? | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 117092 | ON VERRA DEMAIN | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 117336 | JOUR OU J'AI EU 100 ANS (LE) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 117879 | PORTE PAROLE (LE) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 118282 | EDUCATION D'UNE FEE (L') | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 118695 | APRÈS LA CHUTE | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 177265, 500 |
| 120846 | CARGO | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 121175 | MONDE EN CHANTIER | Correspondance publiée | Holy Field Holy War : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 226863 |
| 121983 | DAU | Versions multiples | DAU : 1000047642, 214100 et 280804 désignent des versions différentes ; pas de choix arbitraire.  |
| 122778 | COLLECTIONS DE MITHAT BEY (LES) | Correspondance publiée | 11'e 10 kala (10 to 11) : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 171715 |
| 123164 | ESCORT | Correspondance publiée | Escort : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 178537 |
| 123534 | SUERTE | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 58276, 59153, 201822, 46580 |
| 124852 | INSIDE | Candidats non confirmés | Les visas des candidats diffèrent de la source ; pas de bonne identité établie.  ; candidats examinés : 195051, 196960, 60285, 193483, 307991 |
| 125682 | DERNIER DES HOMMES (LE) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 125032, 5447 |
| 125837 | ICH NOU (NOS ENFANTS) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 128074 | PASSION DE MICHELANGELO (LA) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 128285 | Etre | Réalisation CNC incompatible | Le CNC 128285 désigne Être de Fara Sene ; source Jean-Pascal Vinet. Identité non résolue.  |
| 128897 | MAFROUZA | Série en plusieurs volets | Mafrouza : cinq parties candidates ; vérifier le visa de chaque volet avant association.  |
| 129487 | ESPRIT DU VIN "REVEIL DES TERROIRS" (L') | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 130208 | LAPIDATION DE SAINT ETIENNE (LA) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 131195 | CLAIR OBSCUR | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 266735, 121522, 1000019389, 1000021760, 230915 |
| 131307 | AGON | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000027388, 192608 |
| 131382 | VANITA | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 131571 | ARCHIPELITUDE | Correspondance publiée | La Forme des îles : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 238434 |
| 132000 | WEEKEND (LE) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 31052, 65267, 60460, 362, 180519 |
| 132068 | Quête du loup sauvage (La) | Candidats non confirmés | Les visas des candidats diffèrent de la source ; pas de bonne identité établie.  ; candidats examinés : 254374 |
| 132321 | IGUANAS | Correspondance publiée | Rocker : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 220571 |
| 132906 | Chromobiles | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 133878 | Loups (Les) | Candidats non confirmés | Les visas des candidats diffèrent de la source ; pas de bonne identité établie.  ; candidats examinés : 6480, 206736, 50466, 254374, 262485 |
| 135123 | La Prunelle de mes yeux | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 236460, 252068 |
| 135395 | Francisca (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 136135 | Jamel | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 136626 | Danse, l'Afrique danse | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 136921 | Orient-extrême | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 24947, 213846 |
| 137977 | Compétition | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 280861, 111637, 250197, 243132, 1000014836 |
| 138022 | Forbach forever | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 138166 | Du sable à la poussière | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 138513 | Accident | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000022814, 34, 1000049002, 1000006691, 13277 |
| 138615 | De notre situation économique | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 138820 | Entre 10 et 12 | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 139049 | Sarah Maldoror | Candidats non confirmés | Données d’identité absentes sur les fiches candidates.  ; candidats examinés : 1000011871 |
| 139683 | Snake bite | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 139978 | Vulcania | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 140024 | Un homme à la mer | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000039956, 131272, 8152 |
| 140047 | Thom | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 140197 | Profession cinéaste | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 140295 | Stage fright | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 203629, 227526, 2162, 327891, 223542 |
| 140587 | Dictashot | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 141042 | In art we trust | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 141788 | Dieudamné | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 142018 | Athènes, les éclats | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 142338 | El dorado - la rinconada | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 142351 | Cent annees de pardon | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 142369 | Soif de vivre (La) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 248422, 1438 |
| 143108 | Julie-Aïcha | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 143113 | Links of life | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 143128 | Testicules de tarzan (les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 143263 | Bonnes mères | Projet déjà représenté | Bonne Mère porte le visa CNC 152616, déjà présent dans le matching sous Nora ; aucune seconde association. ID 225024 |
| 143411 | Viens dans ma vie je vais t'en donner des sensations | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144212 | D'une folie l'autre | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144231 | Revanche d'Icare (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144547 | Barman du transatlantique (Le) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144717 | Gaucher (Le) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 5817, 43462 |
| 144737 | Virus | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000035497, 13158, 84145, 274063, 212074 |
| 144784 | Photograph-women | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144795 | Un été en Provence | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 144802 | Max Paradise ou les voies du seigneur | Correspondance publiée | Zamal Paradise : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 299616 |
| 144992 | Histoire d'Orly | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 145083 | Tout l'or du monde | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 134639, 26232, 173479 |
| 145125 | Notre folie | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 145241 | Dernières Choses (Les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 145597 | A perdre haleine | Candidats non confirmés | Données d’identité absentes sur les fiches candidates.  ; candidats examinés : 255480 |
| 145696 | Vie mode d'emploi (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 145822 | Héritage (L') | Correspondance publiée | La Terre de mon grand-père — Partie 1 : L’Héritage : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000040394 |
| 146077 | Bon soldat (Le) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 146118 | Kairos, le moment opportun | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 146202 | Richard va en enfer | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 146280 | Sujet libre | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 147034 | Lettres de la ville en désordre | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 147162 | Inès et Pedro | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 147268 | Il rumore del sol | Homonyme refusé | La collecte de 1000005513 indique Jean-Paul Roux, incompatible avec Mirko Locatelli ; candidat refusé. Autres fiches Isabelle également homonymes. ID 1000005513 |
| 147328 | Dans ce pays, personne ne savait pleurer | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 147638 | Cachalots, à la rencontre des géants | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 147829 | Magic 7 | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 125879 |
| 148023 | Mise à nue | Candidats non confirmés | Données d’identité absentes sur les fiches candidates.  ; candidats examinés : 41603 |
| 148032 | Mor L'Bab | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 148541 | Gas Gas | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 225361, 3266, 33171, 42212, 174012 |
| 148643 | Comment j'ai rencontré ma mère | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 148659 | La Paz | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 223752, 241995, 297632, 318682, 293321 |
| 149297 | Ballade pour un cœur en miettes | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 149309 | Jours flous (Les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 149598 | Pardon (Le) | Conflit actuel hors correction | Conflit actuel exclu du traitement correctif.  |
| 149637 | Vie naturelle du pou (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 149666 | Chant du rossignol (Le) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 247961, 60871, 292850 |
| 149952 | Maison de Cerbère (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 150136 | Je suis un polymorphe actif | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 150253 | Un jour de plus à Baghdad | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 150323 | Voix humaine (La) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 193932, 1000005547, 228677, 565, 281152 |
| 150377 | Jeune fille et la mort (La) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 127760, 96288 |
| 150398 | Carottes sauvages (Les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 150697 | Vallée des âmes (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 150876 | Syriens (Les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 151391 | Governance | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 151578 | P'tite Fradette (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 151669 | Inspecteur Croquette | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 151772 | Un intrus dans la villa | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 151848 | Loin de la route | Identité probable, date TV | Loin de la route : Hugo Vieira da Silva et Paulo Milhomens ; date Arte du 01/12/2025, pas une sortie salle. ID 1000019803 |
| 152119 | To sail close to the wind | Identité confirmée, date TV | Dogwatch : date du 15/11/2022 directement à la télévision ; publication différée. ID 309459 |
| 152120 | Sandra | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1794, 303206, 124646, 49695, 234347 |
| 152298 | Irréductibles | Candidats non confirmés | Les visas des candidats diffèrent de la source ; pas de bonne identité établie.  ; candidats examinés : 40647, 60631, 285935 |
| 152724 | Derrière le soleil (ex : Des espoirs) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 152946 | Cabines, la France et moi (Les) | Correspondance publiée | Allo la France : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000025088 |
| 153196 | Yulia ou l'espace des possibles | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 153313 | Serpent (Le) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 53230, 4188, 37190, 109704, 11879 |
| 154162 | Un long dimanche de funérailles | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 154203 | Porcs du Caire (Les) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 154294 | Kelly Watch the stars | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 154470 | Sang pur sang leviatini | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 154518 | Insurrection | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 221361, 49228, 227225, 232875, 204622 |
| 154918 | Dikongue Pipa, pionnier du cinéma camerounais | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 155108 | Chantons sur les toits | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 155426 | Soyons fous | Correspondance publiée | Soyons fous : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000030792 |
| 155478 | Un Mondo In Più | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 155671 | Il neige à Sidi Bou Saïd | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 155827 | Zone (La) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 266159, 127106, 3137, 209133, 251233 |
| 155913 | Hommes, les dieux et les autres (Les) | Correspondance publiée | Des hommes, des dieux et autres créatures : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000028254 |
| 155962 | Ville qui avalait des âmes (La) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 156379 | Nha terra nha força | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 156476 | A l'abri du mal | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 156594 | Africa ufolo | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 156755 | Ordre et la Force (L') | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 156899 | Heart of light | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 157038 | Avant de partir (Prima di andare via) | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 157142 | Rosilene | Correspondance publiée | L’Or et le monde : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 315137 |
| 157241 | EVJF - Addio al nubilato | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 157329 | Un espace blanc | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 157604 | Ile aux morts (L') | Recherche non concluante | Aucune fiche confirmée sous les titres recherchés ; absence non démontrée.  |
| 157857 | Français, langue étrangère | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158018 | Rosso Pompeïano | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158123 | Portraits d'intérieurs | Correspondance publiée | Les Madeleines : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000012876 |
| 158162 | War - la guerre désirée | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158401 | Isola (L') | Correspondance publiée | My Summer with Irene : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 326899 |
| 158485 | A la conquête des astéroïdes | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158594 | Truth or conséquences | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 295308, 6542 |
| 158613 | Septième degré | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158632 | La eterna adolescente | Réserve demandée après revue | Identité recoupée, numéro Allociné inexpliqué ; maintien en réserve demandé explicitement le 14/11/2026 après rejet du contrôle automatique. ID 1000025384 |
| 158676 | Blue Banks | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 158808 | Vie de château | Conflit actuel hors correction | Conflit actuel exclu du traitement correctif.  |
| 159080 | Filles d'Abraham (Les) | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 159257 | A la recherche | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 1000001353, 28190, 224105, 256696, 33960 |
| 159272 | Un couple heureux | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 159299 | Bayo Bayo Baby | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 159545 | Je m'appelle Clara | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 159645 | Quand je serai grand | Correspondance publiée | La Vie lumineuse : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000025959 |
| 159695 | Collection (La) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 271017, 265282, 56196, 323717, 30903 |
| 159782 | Angèle et mes démons | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 159817 | Urban jungle | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 29334 |
| 160111 | Il ritorno | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 160136 | Coming from the Sea | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 160203 | Fête du retour (La) | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 160253 | Au cœur des ténèbres | Deux fiches Allociné | Au cœur des ténèbres, Rogerio Nunes : fiches 1000015175 et 288565 ; fiche canonique à établir.  |
| 160261 | Earl Grey | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 160360 | Nuit de l'enfance (La) | Identité confirmée, date festivalière | Identité confirmée : Xisi Sofia Ye Chen, 93 minutes, La Fabrica Nocturna Cinéma. Le 25/09/2026 affiché en salle correspond à l’ouverture des Écrans de Chine ; sortie nationale non confirmée. Numéro affiché 2023004357 inexpliqué ; visa160360 conservé. ID 1000044751 ; candidats examinés : 1000044751 |
| 160424 | Mirari | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 160582 | Plateau | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 55448, 52254, 185850, 178228, 1000010342 |
| 160958 | Fouledh | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 161050 | Roman de Renart (Le) | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 161392 | Lalam- Poza… La tangeante des crabes | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 161414 | Bleau, l'autre monde | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 161507 | Yeux fermés (Les) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 26504, 208909, 310303, 29497, 28099 |
| 161571 | Apparition (L') | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 242050, 252874, 4870, 192941, 9750 |
| 161627 | Anoush et les vagabonds | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 161772 | Radiographie du monde, Cannes 2024 | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 162003 | Yakari - Film 2 | Conflit actuel hors correction | Conflit actuel exclu du traitement correctif.  |
| 162265 | Virage sud | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 162402 | Nuits blanches | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 162561 | Simon l'absurde | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 162647 | Moustiques (Les) | Correspondance publiée | Mosquitoes — Le Bambine : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000020147 |
| 162817 | Cas étrange de Ithzak-Meier Gitlis | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 162950 | Mal menor | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 162979 | Una madre | Candidats non confirmés | Les visas des candidats diffèrent de la source ; pas de bonne identité établie.  ; candidats examinés : 253251 |
| 163026 | Relève (La) | Correspondance publiée | Belleville nous verra toujours danser : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 1000037332 |
| 163048 | Disco inferno | Candidats non confirmés | Données d’identité absentes sur les fiches candidates.  ; candidats examinés : 320748 |
| 163313 | Majorana et les neutrinos | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163327 | Tanger Blues | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163430 | Bateau ivre (Le) | Candidats non confirmés | Homonymes ou réalisation différente/non vérifiable dans les candidats.  ; candidats examinés : 254741, 171997 |
| 163528 | Temps nouveaux | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163757 | Petites Personnes | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163783 | Futurs intérieurs | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163882 | Un taxi pour l'Espagne | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 163894 | Best Friend Forever | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 164127 | Faune (Le) | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 164161 | Il cattivo è cattivo, il buono è buono | Correspondance publiée | Dentro : ID synchronisé, collecte et crédits publiés, contrôles SQL et Metabase conformes. ID 328103 |
| 164531 | Interspecies | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 164542 | Femmes de cinéma | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 164609 | Beaucastel | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 164685 | Amour terrestre (L') | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165043 | Hera | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 165086 | Ka | Conflit actuel hors correction | Conflit actuel exclu du traitement correctif.  |
| 165133 | Grande Vacance (La) | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165302 | Il Grande Buco | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165404 | L'Archipel refuge | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165580 | Mer Etoile Femme | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165664 | Folk Play | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165820 | Coassement de la méduse (Le) | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 165850 | There Is no Forever/Keep the Fire Burnong | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 166069 | La Sera a Roma | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 166181 | Enfant du désert (L') | Conflit actuel hors correction | Conflit actuel exclu du traitement correctif.  |
| 166295 | The Blue Sweater With a Yellow Hole | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |
| 166339 | Batty | Ancien succès erroné (#52) | Ancien succès d’une autre œuvre ; rejet confirmé dans la revue #52. Bonne fiche non établie.  |
| 166360 | Finale : Allegro | Recherche non concluante | Recherche directe partiellement en erreur HTTP ; aucune fiche confirmée.  |

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | Qualification des 236 visas, publication de 18 correspondances, déduplication ciblée et contrôles SQL, dbt et Metabase. |
