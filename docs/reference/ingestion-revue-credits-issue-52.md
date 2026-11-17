# Revue des crédits en quarantaine — issue 52

**Owner:** Joel Teixeira

**Dernière révision:** 2026-11-14

**Status:** actif

## Périmètre et état du traitement

L’[issue 52](https://github.com/Le-Collectif-50-50/cinestats-5050/issues/52) concerne les crédits sans film associé dans `ops.film_credits_unmatched`. La revue du 14 novembre 2026 porte sur **144 lignes, 16 identifiants Allociné et 16 visas source**, sans filtre temporel. Les 280 lignes et 20 ID du diagnostic initial du 13 novembre constituent un état historique différent. La baisse antérieure de 136 lignes ne peut pas être attribuée à cette intervention.

Les 16 groupes sont qualifiés : **42 lignes sur sept ID sont rattachables**, **101 lignes sur huit ID désignent d’autres œuvres**, et **une ligne sur un ID confirmé reste différée pour sa date télévisée**. Ces volumes comptent des lignes de quarantaine, pas des personnes uniques ni des gains statistiques.

Les corrections sont **synchronisées et publiées**. La quarantaine passe de **144 à 102 lignes**, soit 42 lignes rattachées sur sept films. Ces films portent désormais 42 associations finales, contre huit avant intervention : **34 associations supplémentaires nettes**. Aucun scraping, changement de flow ou de dashboard n’a été réalisé pour cette revue. Les `visa_mismatch` actuels sont exclus de cette intervention.

## Diagnostic et contrôles avant publication

La branche scrapée de `int_credit_holders_role` rattache les crédits par ID Allociné à `stg_id_matching`. Les 16 anciens ID sont absents du matching courant. Quinze visas ont un ID vide ; le visa 155365 possède déjà un autre ID, `1000037190`. Son ancien succès `260988` reste sélectionné dans le staging, malgré un essai plus récent en `needs_review` sur la nouvelle cible.

Un statut historique `success` ne certifie donc pas l’identité. Huit groupes contiennent une réalisation incompatible avec celle de `raw.films`. Ils restent en quarantaine. Aucun ancien ID erroné n’est réintroduit ; aucun crédit n’est transféré sur la seule proximité du titre ou sur le visa de la requête.

La [requête de contrôle](../../ingestion/dbt/analyses/allocine_issue_52_validation.sql) a été exécutée avant publication. Elle contrôle les 16 décisions, les ID de film, le matching, les derniers essais, les succès retenus, les associations finales et leur intégrité. Les résultats sont inspectés sans export de données.

État initial : **6 138 films, 181 636 associations de crédits, zéro doublon de clé et zéro crédit orphelin**. Les sept films rattachables portent déjà huit réalisations manuelles. Leurs dates finales et legacy sont toutes absentes. Ils ne sont sélectionnés ni par la date dbt ni par la date legacy dans 2004–2024, sans autre filtre métier.

## Sept correspondances confirmées

| Visa CNC | ID Allociné | Œuvre source / fiche | Réalisation | Lignes en quarantaine |
| --- | --- | --- | --- | ---: |
| 111864 | 59833 | Le Coffre des ancêtres / L’Été d’Isabelle | Nurbek Egen | 1 |
| 117557 | 120326 | Nuit cannoise | Christian Vandelet | 12 |
| 126103 | 186800 | À quatre mains | Eugène Izraylit | 1 |
| 139058 | 226218 | Un pas de côté | Luc Decaster | 1 |
| 141408 | 233453 | Des vérités désagréables | Marcel Ophüls et Eyal Sivan | 2 |
| 142040 | 231782 | Camí a casa / Quatretondeta | Pol Rodríguez | 16 |
| 146222 | 287331 | Stasis / Partenonas | Mantas Kvedaravičius | 9 |
| **Total** | **7 ID** | | | **42** |

- **111864.** Le [CNC](https://www.cnc.fr/professionnels/visas-et-classification/111864) présente *L’Été d’Isabelle*, Nurbek Egen, long métrage de 105 minutes, 2005. L’[ancienne fiche Allociné](https://www.allocine.fr/film/fichefilm_gen_cfilm=59833.html) conserve le titre *Le Coffre des ancêtres*, Nurbek Egen et Natacha Régnier, avec une année de projet 2004. Les [titres alternatifs et le synopsis](https://www.senscritique.com/film/l_ete_d_isabelle/17874023/details) corroborent l’œuvre. La fiche reste incomplète. Aucune date n’est copiée du CNC vers la collecte.
- **117557.** L’[Allociné 120326](https://www.allocine.fr/film/fichefilm_gen_cfilm=120326.html) et la [présentation professionnelle du réalisateur](https://viadeo.journaldunet.com/p/christian-vandelet-4792697) confirment *Nuit cannoise*, Christian Vandelet. Le titre, la réalisation et le format concordent avec la source CNC. La fiche projet indique 2008, l’agrément source 2007. Aucune sortie en salle n’est confirmée.
- **126103.** L’[Allociné 186800](https://www.allocine.fr/film/fichefilm_gen_cfilm=186800.html) présente le long métrage *À quatre mains*, Eugène Izraylit. Le [palmarès Sopadin](https://prix-scenariste.org/fr/accueil/laureats-finalistes-et-films-1986-2/21) confirme le projet et son auteur. L’année de projet 2010 diffère de l’agrément source 2015 ; aucune sortie n’est déduite de ces années.
- **139058.** L’[Allociné 226218](https://www.allocine.fr/film/fichefilm_gen_cfilm=226218.html) présente un documentaire français de 90 minutes, Luc Decaster. La [filmographie Fémis](https://www.femis.fr/index.php?id_ancien=18488&page=fiche_ancien) confirme le long métrage *Un pas de côté*, 2014. La [Région Bretagne](https://pod.bretagne.bzh/hosting/kentika/raa/2017/RAA-486-T3_02-2017.pdf) atteste le titre ultérieur *Danse avec l’écume*. Aucune sortie n’est inventée.
- **141408.** L’[Allociné 233453](https://www.allocine.fr/film/fichefilm_gen_cfilm=233453.html) et le [programme Histoire et Cité 2015](https://2015.histoire-cite.ch/files/2015_fhc-cine_revue_web.pdf) confirment le projet documentaire et ses deux réalisateurs. L’identité est confirmée, indépendamment de l’absence de sortie connue.
- **142040.** L’[Acadèmia del Cinema Català](https://academiadelcinema.cat/ca/estrenes/2661-el-29-d-abril-arriba-quatretondeta-de-pol-rodriguez) relie explicitement le titre de travail *Camí a casa* au titre définitif *Quatretondeta*. L’[Allociné 231782](https://www.allocine.fr/film/fichefilm_gen_cfilm=231782.html) concorde sur Pol Rodríguez, les acteurs et le format de fiction de 92 minutes. La sortie espagnole du 29 avril 2016 n’est pas utilisée comme sortie française.
- **146222.** Dans son [entretien de novembre 2019](https://www.15min.lt/kultura/naujiena/kinas/rezisierius-m-kvedaravicius-dokumentinis-kinas-nera-issprendes-esmines-etines-problemos-4-1232112), Mantas Kvedaravičius explique le passage du titre *Stasis* à *Partenonas*. L’[Allociné 287331](https://www.allocine.fr/film/fichefilm_gen_cfilm=287331.html) confirme le réalisateur et la fiction de 119 minutes. Une sélection festivalière ne remplace pas une sortie française en salle.

Les pages CNC ont été consultées pour les 16 visas. Seuls 111864 et 152119 ont renvoyé une fiche d’œuvre exploitable lors de cette revue. Les autres décisions croisent la source d’agrément `raw.films`, les fiches Allociné et les preuves complémentaires ci-dessus. Une page CNC vide ne prouve pas l’inexistence du visa.

## Huit anciens rattachements refusés

Les réalisations attendues ci-dessous proviennent de `raw.films`. Chaque ancienne fiche Allociné a été relue le 14 novembre.

| Visa source | Œuvre attendue / réalisation source | Ancienne fiche refusée | Lignes maintenues |
| --- | --- | --- | ---: |
| 120846 | Cargo — Biljana Tutorov, documentaire | [109311](https://www.allocine.fr/film/fichefilm_gen_cfilm=109311.html), Cargo, Clive Gordon, fiction 2006 | 18 |
| 155365 | Les Jours d’après — Stéphanie Pillonca-Kervern, agrément 2025 | [260988](https://www.allocine.fr/film/fichefilm_gen_cfilm=260988.html), Ce soir-là et les jours d’après, Marion Laine, 2019 | 16 |
| 160111 | Il ritorno — Stefano Chiantini, agrément 2023 | [319142](https://www.allocine.fr/film/fichefilm_gen_cfilm=319142.html), Nostos: Il ritorno, Franco Piavoli, 1989 | 5 |
| 161050 | Le Roman de Renart — Anne-Laure Daffis / Léo Marchand, agrément 2025 | [5459](https://www.allocine.fr/film/fichefilm_gen_cfilm=5459.html), Ladislas et Irène Starewitch, 1930 | 21 |
| 162402 | Nuits blanches — Tiago Hespanha, documentaire, agrément 2025 | [236434](https://www.allocine.fr/film/fichefilm_gen_cfilm=236434.html), Les Nuits blanches du facteur, Andrey Konchalovsky, 2014 | 15 |
| 164127 | Le Faune — Augusto Zanovello, animation, agrément 2025 | [323303](https://www.allocine.fr/film/fichefilm_gen_cfilm=323303.html), Le Faune de marbre, Mario Bonnard, 1920 | 11 |
| 165043 | Hera — Catarina Mourão, agrément 2025 | [112135](https://www.allocine.fr/film/fichefilm_gen_cfilm=112135.html), Phir Hera Pheri, Neeraj Vora, 2006 | 8 |
| 166339 | Batty — Mohammed Raouf Sebbahi, fiction, agrément 2025 | [170268](https://www.allocine.fr/film/fichefilm_gen_cfilm=170268.html), La batte folle, Tex Avery, animation courte 1944 | 7 |
| **Total** | | **8 ID** | **101** |

Pour *Cargo*, le [catalogue du Film Center Serbia](https://www.fcs.rs/wp-content/uploads/2022/06/FCS-2017-documentaries.pdf) confirme un documentaire de Biljana Tutorov sur Darko Rundek, incompatible avec la fiction de Clive Gordon. Pour 155365, l’ID courant `1000037190`, sa validation décochée et le dernier `needs_review` sont conservés. La revue ne traite pas ce candidat actuel.

Les 101 lignes erronées restent traçables dans la quarantaine. Aucun ancien succès brut n’est effacé ou changé de statut. Retrouver la bonne fiche de ces œuvres, ou concevoir une exclusion explicite des succès obsolètes, constitue une suite distincte. Modifier la jointure pour faire disparaître l’avertissement serait incorrect.

## Dogwatch : identité confirmée, date télévisée

Le visa **152119**, source *To sail close to the wind*, correspond au documentaire de Gregoris Rentis. Le [CNC](https://www.cnc.fr/professionnels/visas-et-classification/152119) présente *Vardia — Les hommes de quart*, long métrage de 81 minutes, sortie salle indéfinie. L’[Allociné 309459](https://www.allocine.fr/film/fichefilm_gen_cfilm=309459.html) présente *Dogwatch — Les hommes de quart*, version de 73 minutes, **15 novembre 2022 directement à la télévision**.

Le succès existant contient cette date. Renseigner le matching la publierait dans `fnl.fnl_films.release_date`, sans distinction du support. Le matching reste donc vide et la validation décochée. Son unique crédit en quarantaine, Gregoris Rentis / Réalisateur, existe déjà manuellement dans les crédits finaux avec le même identifiant. Aucun crédit métier supplémentaire n’est perdu par ce report.

La reprise exige de distinguer les supports de diffusion ou de confirmer une date française de sortie en salle. La seule identité ne valide pas la date télévisée pour les statistiques cinéma.

## Corrections source et déduplication

Source : [Cinéstats 50/50 — Source de données](https://docs.google.com/spreadsheets/d/1mvKPVrZ3FAHuUB__3akr4Fr7K4MqgTba9bFwNdtL_To/edit#gid=902822468).

- `id_matching` : sept ID renseignés sur les lignes existantes ; sept validations activées après revue. Les 16 décisions et leurs anciennes métadonnées sont conservées dans `COMMENTAIRES`. Les titres, visas, autres ID et formules des lignes du lot restent inchangés. Les positions ont changé pendant les opérations concurrentes : les 16 visas ont été retrouvés puis relus aux lignes 6124 à 6139 au contrôle final. Toujours rechercher par visa, jamais réutiliser un ancien numéro de ligne.
- `film_credits!C342:E342` : l’association de réalisation d’*À quatre mains* utilise l’ID existant **573ab00e-9551-0e57-f8c2-a59df1939ace**, *Eugène Izraylit*, à la place de **5a573791-f6cc-7e08-5459-bfad0d4a2f52**, *Eugene Izraylit*. Film et rôle sont conservés. Une note conserve l’ancien ID et les anciennes métadonnées.
- `credit_holders!A687:I687` : correction de la fiche accentuée existante. Le genre `male` provient de la correction antérieure de la même personne, ligne 185 ; aucune nouvelle inférence de genre. L’ancienne fiche est conservée, sans fusion globale. La nouvelle ligne reprend les formats et contraintes natives d’une ligne existante.

Cette déduplication évite deux réalisations sémantiquement identiques. Le modèle final déduplique ensuite la même clé film/rôle/personne par son `UNION`. Un simple test d’unicité des clés n’aurait pas détecté les deux variantes de personne.

Auteur source : « Revue automatisée — mandat Joel Teixeira ». Date native : **14 novembre 2026 à 14:33:39, heure de Paris**. Les contraintes de date et de booléen sont préservées. Les valeurs, notes, validations et formules ont été relues par API. Le rendu natif consulté présentait des lignes décalées par rapport aux lectures API ; il ne constitue pas une preuve fiable de mise en page des cellules modifiées.

## Publication et contrôles finaux

Deux corrections concurrentes hors lot ont d’abord été observées : visa 122169 remplacé par 136385, et 155994 par 154994. Cette intervention ne les a pas écrites. La connexion Airbyte effective, **Google Sheets → Postgres**, synchronise les sources partagées. Le lancement d’un second run a donc été différé, conformément à la consigne de coordination.

La synchronisation parallèle `443f8ab2-34eb-4708-baf2-7c36b08ab869`, terminée le 14 novembre à **14:52:22, heure de Paris**, a repris les corrections source. La publication parallèle `77467edb-a730-4e7f-bb4d-85cfcd34ed0f`, **issue-51-publier-quatre-visas-corriges**, les a publiées avec les corrections de l’autre lot. Elle est terminée en `Completed` le **14 novembre 2026 à 15:02:19, heure de Paris**, Airbyte et phase dbt 2 activés. Aucun second run n’a été lancé pour #52.

Après cette publication, la requête versionnée et les cartes Metabase ont été exécutées pour contrôler spécifiquement #52. Les succès des sept films conservent leurs `run_id` et horodatages antérieurs ; aucune nouvelle collecte du lot n’a été nécessaire. Chaque visa et chaque nouvel ID possède exactement une ligne de matching. Les 16 identifiants de film sont conservés.

| Mesure du lot #52 | Avant | Après |
| --- | ---: | ---: |
| Lignes de quarantaine, catalogue complet | 144 | 102 |
| ID Allociné en quarantaine | 16 | 9 |
| Lignes scrapées du sous-lot confirmé rattachées à leur film | 0 | 42 |
| Associations finales sur les sept films confirmés | 8 | 42 |
| Films du sous-lot datés dans 2004–2024 côté dbt | 0 | 0 |
| Films du sous-lot datés dans 2004–2024 côté legacy | 0 | 0 |
| Dates finales absentes sur les sept films | 7 | 7 |
| Doublons de clé dans les crédits finaux, catalogue complet | 0 | 0 |
| Crédits finaux orphelins, catalogue complet | 0 | 0 |

Les **42 lignes rattachées sont toutes présentes dans `fnl.fnl_film_credits`**, avec les bons film, rôle et personne ou société. Elles comprennent 17 associations d’acteurs, huit réalisations, quatre scénarios, trois producteurs, trois productions et sept autres associations techniques ou de production exécutive. Les huit réalisations étaient déjà présentes manuellement ; leur déduplication explique la différence entre 42 lignes récupérées et 34 associations supplémentaires nettes. Ces nombres ne sont pas des personnes uniques.

La réalisation d’*À quatre mains* est unique : **Eugène Izraylit**, ID `573ab00e-9551-0e57-f8c2-a59df1939ace`, genre `male`. L’ancienne fiche reste présente dans `raw.credit_holders`. Les 101 lignes des huit œuvres erronées et la ligne de *Dogwatch* restent en quarantaine, sans rattachement indu. Le dernier `needs_review` de 155365 et son ID courant sont conservés.

Les cartes **100 — Fiche Film · Identité du film** et **101 — Fiche Film · Crédits · personnes et sociétés** ont été interrogées sans cache pour chacun des sept visas, soit **14 contrôles réussis**. Une identité par visa, dates absentes conformes et nombres de crédits exacts. La carte 101 restitue une seule réalisation pour Eugène Izraylit, avec le genre « Homme ».

Le catalogue compte toujours **6 138 films et 6 138 visas source distincts**, sans visa invalide. Son total de crédits passe de 181 636 à 181 788 ; cette variation globale comprend les corrections parallèles de #51 et ne mesure pas le gain de #52. Le gain propre à #52 est mesuré sur ses sept `film_id`, à périmètre constant.

L’intervention n’ajoute aucun film sélectionnable par date dans les statistiques 2004–2024. Elle améliore les associations du catalogue. Les dates absentes ne prouvent pas que les œuvres sont hors période ; leurs sorties restent à instruire séparément.

### Résultat dbt partagé

Invocation phase 2 : `3ba55495-7ed4-4b29-9580-ee8c10ee1443`, **45 modèles réussis, 96 tests passés, une opération réussie, aucune erreur**. Six familles d’avertissements demeurent ; deux volumes diminuent grâce aux corrections #52.

| Avertissement | Avant | Après |
| --- | ---: | ---: |
| Crédits sans film associé | 144 | 102 |
| ID Allociné absents | 243 | 236 |
| ID Mubi absents | 893 | 893 |
| ID TMDB absents | 773 | 773 |
| Valeurs Mubi dupliquées | 5 | 5 |
| Valeurs TMDB dupliquées | 2 | 2 |

La revue du lot courant est terminée. L’issue reste ouverte pour le traitement explicite des succès erronés et la réserve de support de diffusion de *Dogwatch*. La qualification complète ne signifie pas que tous les anciens crédits doivent être republiés.

## Historique du document

| # | Date | Auteur | Observations |
| --- | --- | --- | --- |
| 1 | 2026-11-14 | Joel Teixeira | Actualisation des 16 groupes, qualification des identités, corrections source et contrôles de publication. |
