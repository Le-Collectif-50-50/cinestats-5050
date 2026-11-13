#!/usr/bin/env python3
"""Publier les fiches Film et Credit Holder sur la connexion métier Metabase."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / 'ingestion/dbt/analyses/metabase'
COLLECTION = 'Cinestats 50/50 - Fiches'
NAMES = {'film': 'Fiche Film', 'holder': 'Fiche Credit Holder'}
PARAMS = {'film': [('visa', 'Visa CNC'), ('titre', 'Titre contient')],
          'holder': [('identifiant', 'ID Credit Holder'), ('nom', 'Nom contient')]}
SAMPLES = {'film': {'visa': '113336'},
           'holder': {'identifiant': 'f4bab825-8ea1-65ea-9688-d6d089bfb09a'}}
GENDER = "CASE h.gender WHEN 'female' THEN 'Femme' WHEN 'male' THEN 'Homme' ELSE 'Non renseigné / autre' END"
TYPE = "CASE h.type WHEN 'Individual' THEN 'Personne' WHEN 'Company' THEN 'Société' ELSE COALESCE(h.type, 'Non renseigné') END"


def parameters(kind):
    return [dict(id=k, name=v, slug=k, type='string/=', sectionId='string') for k, v in PARAMS[kind]]


def definitions(kind, base, dashboard_ids):
    prefix = (SQL / ('film_profile_selection.sql' if kind == 'film'
                     else 'credit_holder_profile_selection.sql')).read_text()
    film_url = f"{base}/dashboard/{dashboard_ids['film']}?visa="
    holder_url = f"{base}/dashboard/{dashboard_ids['holder']}?identifiant="
    cards = []

    def add(name, query, row, height=6, col=0, width=24, display='table', settings=None, description=''):
        cards.append(dict(name=name, query=prefix + query, row=row, col=col,
                          size_x=width, size_y=height, display=display,
                          visualization_settings=settings or {}, description=description))

    if kind == 'film':
        metrics = [('Films trouvés', 'SELECT COUNT(*) AS films FROM selected_films'),
                   ('Personnes créditées', "SELECT COUNT(*) AS personnes FROM people WHERE type = 'Individual'"),
                   ('Sociétés créditées', "SELECT COUNT(*) AS societes FROM people WHERE type = 'Company'")]
        for i, (name, query) in enumerate(metrics):
            add(name, query, 3, 3, i * 8, 8, 'scalar', description='Entités distinctes sur tous les films sélectionnés.')
        add('Identité du film', f"""
SELECT '{film_url}' || f.cnc_visa AS ouvrir_fiche,
       f.movie_name AS titre, f.cnc_visa AS visa_cnc,
       f.cnc_agreement_year AS annee_agrement, f.release_date AS sortie,
       f.duration_mn AS duree_minutes,
       (SELECT STRING_AGG(DISTINCT g.genre_name, ', ' ORDER BY g.genre_name)
        FROM fnl.fnl_film_genre fg JOIN fnl.fnl_genre g USING (genre_id)
        WHERE fg.film_id=f.film_id) AS genres,
       f.film_id AS id_film
FROM selected_films f ORDER BY f.movie_name, f.cnc_visa""", 6, 5)
        add('Crédits · personnes et sociétés', f"""
SELECT '{holder_url}' || h.credit_holder_id AS ouvrir_fiche,
       f.movie_name AS film, f.cnc_visa AS visa_cnc, h.holder_name AS nom,
       {TYPE} AS type, {GENDER} AS genre,
       COALESCE(r.role_inclusive_name, r.role_name, c.role_id::text) AS role,
       CASE r.is_key_role WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS role_cle,
       h.credit_holder_id AS id_credit_holder
FROM credits c JOIN selected_films f USING (film_id)
LEFT JOIN named_holders h USING (credit_holder_id)
LEFT JOIN fnl.fnl_role r USING (role_id)
ORDER BY f.movie_name, r.is_key_role DESC NULLS LAST, role, nom""", 11, 9,
            description='Une ligne par film × personne ou société × rôle. Rôles clés selon le référentiel actuel.')
        add('Représentation · personnes distinctes', f"""
SELECT {GENDER} AS genre, COUNT(*) AS personnes
FROM people h WHERE h.type='Individual' GROUP BY 1 ORDER BY 1""", 20, 7, 0, 10, 'bar',
            {'graph.dimensions': ['genre'], 'graph.metrics': ['personnes'], 'graph.show_values': True},
            'Personnes distinctes sur la sélection, sociétés exclues. Genre enregistré dans le référentiel ; aucune inférence supplémentaire.')
        add('Représentation par métier', f"""
SELECT COALESCE(r.role_inclusive_name, r.role_name, c.role_id::text) AS metier,
       COUNT(DISTINCT h.credit_holder_id) FILTER (WHERE h.gender='female') AS femmes,
       COUNT(DISTINCT h.credit_holder_id) FILTER (WHERE h.gender='male') AS hommes,
       COUNT(DISTINCT h.credit_holder_id) FILTER (WHERE h.gender IS NULL OR h.gender NOT IN ('female','male')) AS non_renseigne_ou_autre,
       COUNT(DISTINCT h.credit_holder_id) AS personnes
FROM credits c JOIN named_holders h USING (credit_holder_id)
LEFT JOIN fnl.fnl_role r USING (role_id)
WHERE h.type='Individual' GROUP BY 1 ORDER BY personnes DESC, metier""", 20, 7, 10, 14,
            description='Une personne peut exercer plusieurs métiers. Les lignes ne sont donc pas additives.')
        add('Budget et diffusion', """
SELECT movie_name AS film, cnc_visa AS visa_cnc, budget AS budget_euros,
       budget_category AS tranche_budget, broadcasters AS diffuseurs,
       CASE is_french_financed WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS financement_francais_majoritaire,
       filmography_rank AS rang_filmographie_realisation
FROM selected_films ORDER BY movie_name, cnc_visa""", 27, 5)
        add('Financement par pays', """
SELECT f.movie_name AS film, f.cnc_visa AS visa_cnc, b.country_name AS pays,
       b.budget_allocation AS financement_pourcent
FROM selected_films f JOIN fnl.fnl_film_country_budget_allocation b USING (film_id)
ORDER BY f.movie_name, b.budget_allocation DESC, b.country_name""", 32, 6,
            description='Pourcentages enregistrés par pays. Absence de ligne = information non disponible.')
        add('Bonus parité et dispositifs de soutien', """
SELECT movie_name AS film, cnc_visa AS visa_cnc,
       CASE has_parity_bonus WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS bonus_parite, CASE has_eof WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS eof,
       CASE has_sofica WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS sofica, CASE has_tax_credit WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS credit_impot,
       CASE has_regional_funding WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS aide_regionale, CASE has_asr WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS asr
FROM selected_films ORDER BY movie_name, cnc_visa""", 38, 5,
            description='Valeurs du référentiel CNC consolidé. Une valeur vide est inconnue, pas un non.')
    else:
        metrics = [('Credit Holders trouvés', 'SELECT COUNT(*) AS credit_holders FROM selected_holders'),
                   ('Films crédités', 'SELECT COUNT(*) AS films FROM films'),
                   ('Rôles distincts', 'SELECT COUNT(DISTINCT role_id) AS roles FROM credits')]
        for i, (name, query) in enumerate(metrics):
            add(name, query, 3, 3, i * 8, 8, 'scalar', description='Comptages distincts sur la sélection. Filmographie limitée aux films présents dans Cinestats.')
        add('Identité du Credit Holder', f"""
SELECT '{holder_url}' || h.credit_holder_id AS ouvrir_fiche,
       h.holder_name AS nom, {TYPE} AS type, {GENDER} AS genre,
       h.first_name AS prenom, h.last_name AS nom_famille,
       h.legal_name AS raison_sociale, h.birthdate AS naissance,
       h.credit_holder_id AS id_credit_holder
FROM selected_holders h ORDER BY h.holder_name, h.credit_holder_id""", 6, 5,
            description='Genre et date de naissance tels que renseignés. Les sociétés ne sont pas des personnes physiques. Les identifiants dérivés du nom ne résolvent pas les homonymes.')
        add('Filmographie et rôles', f"""
SELECT '{film_url}' || f.cnc_visa AS ouvrir_fiche_film,
       h.holder_name AS nom, f.movie_name AS film, f.cnc_visa AS visa_cnc,
       f.cnc_agreement_year AS annee_agrement, f.release_date AS sortie,
       STRING_AGG(DISTINCT COALESCE(r.role_inclusive_name, r.role_name, c.role_id::text), ', '
                  ORDER BY COALESCE(r.role_inclusive_name, r.role_name, c.role_id::text)) AS roles,
       f.budget AS budget_film_euros,
       CASE f.has_parity_bonus WHEN TRUE THEN 'Oui' WHEN FALSE THEN 'Non' ELSE 'Non renseigné' END AS bonus_parite
FROM credits c JOIN selected_holders h USING (credit_holder_id)
JOIN films f USING (film_id) LEFT JOIN fnl.fnl_role r USING (role_id)
GROUP BY h.credit_holder_id, h.holder_name, f.film_id, f.movie_name, f.cnc_visa,
         f.cnc_agreement_year, f.release_date, f.budget, f.has_parity_bonus
ORDER BY f.cnc_agreement_year DESC NULLS LAST, f.movie_name, h.holder_name""", 11, 9,
            description='Une ligne par Credit Holder × film ; rôles regroupés. Le budget est celui du film, pas une rémunération.')
        add('Films par année d’agrément', """
SELECT cnc_agreement_year AS annee, COUNT(*) AS films
FROM films WHERE cnc_agreement_year IS NOT NULL GROUP BY 1 ORDER BY 1""", 20, 7, 0, 12, 'bar',
            {'graph.dimensions': ['annee'], 'graph.metrics': ['films'], 'graph.show_values': True},
            'Films distincts par année d’agrément CNC, et non par année de sortie. Années inconnues exclues.')
        add('Métiers exercés', """
SELECT COALESCE(r.role_inclusive_name, r.role_name, c.role_id::text) AS metier,
       COUNT(DISTINCT c.film_id) AS films
FROM credits c LEFT JOIN fnl.fnl_role r USING (role_id)
GROUP BY 1 ORDER BY films DESC, metier""", 20, 7, 12, 12,
            description='Films distincts par libellé de métier. Un même film peut apparaître dans plusieurs métiers.')
        add('Personnes créditées sur les mêmes films · top 25', f"""
SELECT '{holder_url}' || h.credit_holder_id AS ouvrir_fiche,
       h.holder_name AS nom,
       COUNT(DISTINCT c.film_id) AS films_en_commun,
       h.credit_holder_id AS id_credit_holder
FROM films f JOIN fnl.fnl_film_credits c USING (film_id)
JOIN named_holders h USING (credit_holder_id)
WHERE h.type='Individual'
  AND NOT EXISTS (SELECT 1 FROM selected_holders s WHERE s.credit_holder_id=h.credit_holder_id)
GROUP BY h.credit_holder_id, h.holder_name
ORDER BY films_en_commun DESC, h.holder_name, h.credit_holder_id LIMIT 25""", 27, 7,
            description='Présence dans les crédits des mêmes films ; ne prouve pas une collaboration directe. Sélection recherchée exclue.')
    if kind == 'film':
        for card in cards:
            if card['row'] >= 11:
                card['row'] += 2
            elif card['name'] == 'Identité du film':
                card.update(col=6, size_x=18, size_y=7)
        add('Affiche du film', """
SELECT f.movie_name AS film, p.poster_url AS affiche, p.poster_url AS ouvrir_affiche,
       CASE WHEN p.poster_url IS NULL THEN 'Affiche non disponible' ELSE 'Affiche Allociné' END AS disponibilite
FROM selected_films f LEFT JOIN fnl.fnl_film_posters p USING (film_id)
ORDER BY f.movie_name, f.cnc_visa""", 6, 7, 0, 6,
            display='object', description='Affiche issue du dernier succès Allociné correspondant au film. Aperçu miniature et lien vers le grand format. Plusieurs résultats : utiliser les flèches du bloc ou affiner par visa. Une affiche absente ne déclenche aucun scraping.')
    return cards


def dataset_query(database_id, kind, query, values=None):
    tags = {k: {'id': k, 'name': k, 'display-name': v, 'type': 'text', 'required': False}
            for k, v in PARAMS[kind]}
    body = {'database': database_id, 'type': 'native', 'native': {'query': query, 'template-tags': tags}}
    if values:
        body['parameters'] = [{'type': 'category', 'target': ['variable', ['template-tag', k]], 'value': v}
                              for k, v in values.items()]
    return body


def intro(kind, base, ids):
    if kind == 'film':
        return ("## Explorer un film\n"
                "**Visa CNC exact** ou **fragment du titre**. Sans recherche : aucune sélection. "
                "Deux filtres remplis se cumulent.\n\n"
                "Plusieurs résultats ? Affinez par visa. Les liens **Ouvrir la fiche** relient films et crédits. "
                f"[Rechercher un Credit Holder]({base}/dashboard/{ids['holder']})")
    return ("## Explorer une personne ou une société\n"
            "**ID exact** ou **fragment du nom**. Sans recherche : aucune sélection. "
            "Deux filtres remplis se cumulent.\n\n"
            "Plusieurs résultats ? Affinez par ID. Filmographie limitée au catalogue Cinestats. "
            f"[Rechercher un film]({base}/dashboard/{ids['film']})")


def table_settings():
    labels = {
        'titre': 'Titre', 'film': 'Film', 'visa_cnc': 'Visa CNC',
        'annee_agrement': 'Année CNC', 'sortie': 'Sortie en salle',
        'duree_minutes': 'Durée (min)', 'genres': 'Genres', 'id_film': 'ID film',
        'nom': 'Nom', 'type': 'Type', 'genre': 'Genre', 'role': 'Rôle',
        'role_cle': 'Rôle clé', 'id_credit_holder': 'ID Credit Holder',
        'metier': 'Métier', 'femmes': 'Femmes', 'hommes': 'Hommes',
        'non_renseigne_ou_autre': 'Non renseigné / autre', 'personnes': 'Personnes',
        'budget_euros': 'Budget (€)', 'budget_film_euros': 'Budget du film (€)',
        'tranche_budget': 'Tranche de budget', 'diffuseurs': 'Diffuseurs',
        'financement_francais_majoritaire': 'Financement français ≥ 50 %',
        'rang_filmographie_realisation': 'Rang dans la filmographie',
        'pays': 'Pays', 'financement_pourcent': 'Financement (%)',
        'bonus_parite': 'Bonus parité', 'eof': 'EOF', 'sofica': 'SOFICA',
        'credit_impot': 'Crédit d’impôt', 'aide_regionale': 'Aide régionale', 'asr': 'ASR',
        'prenom': 'Prénom', 'nom_famille': 'Nom de famille', 'raison_sociale': 'Raison sociale',
        'naissance': 'Naissance', 'roles': 'Rôles', 'films': 'Films',
        'films_en_commun': 'Films en commun', 'ouvrir_fiche': 'Fiche',
        'ouvrir_fiche_film': 'Fiche film', 'affiche': 'Aperçu', 'disponibilite': 'Disponibilité',
        'ouvrir_affiche': 'Grand format',
    }
    columns = {}
    for name, label in labels.items():
        settings = {'column_title': label}
        if name in ('visa_cnc', 'annee_agrement'):
            settings.update(number_separators='.', decimals=0)
        if name in ('budget_euros', 'budget_film_euros'):
            settings.update(number_separators=', ', decimals=0)
        if name in ('ouvrir_fiche', 'ouvrir_fiche_film'):
            settings.update(view_as='link', link_text='Ouvrir la fiche')
        if name == 'affiche':
            settings.update(view_as='image')
        if name == 'ouvrir_affiche':
            settings.update(view_as='link', link_text='Voir l’affiche')
        columns[json.dumps(['name', name], separators=(',', ':'))] = settings
    return {'table.pivot': False, 'column_settings': columns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://metabase.cinestats5050.fr')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--database-name', default='cinestats-5050-db')
    parser.add_argument('--check', action='store_true', help='Valider en lecture seule les requêtes et recherches.')
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    base = args.url.rstrip('/')
    if args.preview:
        for kind in NAMES:
            print(NAMES[kind], [d['name'] for d in definitions(kind, base, dict(film=0, holder=0))])
        return
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    key = os.environ.get('METABASE_API_KEY')
    if not base.startswith('https://') or not key:
        parser.error('URL HTTPS et METABASE_API_KEY requis.')

    def api(method, path, data=None):
        request = Request(base + '/api/' + path, method=method,
                          headers={'x-api-key': key, 'Content-Type': 'application/json'},
                          data=json.dumps(data).encode() if data is not None else None)
        try:
            with urlopen(request, timeout=60) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            raise RuntimeError(f'Metabase {method} {path} : HTTP {error.code}') from None
        except URLError:
            raise RuntimeError('Metabase inaccessible : vérifier réseau et certificat TLS.') from None

    def unique(items, name):
        matches = [item for item in items if item.get('name') == name and not item.get('archived')]
        if len(matches) > 1:
            raise RuntimeError(f'Nom ambigu : {name}')
        return matches[0] if matches else None

    database = unique(api('GET', 'database')['data'], args.database_name)
    if not database:
        raise RuntimeError('Connexion métier introuvable.')
    db = database['id']
    checks = []
    for kind in NAMES:
        for definition in definitions(kind, base, dict(film=0, holder=0)):
            for values in ({}, SAMPLES[kind]):
                checks.append((kind, definition, values))

    def check(job):
        kind, definition, values = job
        result = api('POST', 'dataset', dataset_query(db, kind, definition['query'], values))
        if result.get('status') != 'completed':
            raise RuntimeError(f"Requête invalide : {definition['name']} : {result.get('error')}")
        rows = result.get('data', {}).get('rows', [])
        if not values and (rows != [[0]] if definition['display'] == 'scalar' else bool(rows)):
            raise RuntimeError(f"Recherche vide non respectée : {definition['name']}")
        return f"{kind} · {definition['name']} · {'filtré' if values else 'sans filtre'} : OK"

    with ThreadPoolExecutor(max_workers=4) as pool:
        for message in pool.map(check, checks):
            print(message, flush=True)
    # Vérifier recherche textuelle, identifiants inexistants et cumul des filtres.
    cases = [('film', {'titre': "paris je t'aime"}, 1),
             ('film', {'visa': '113336', 'titre': 'aucun-film-zzzz'}, 0),
             ('film', {'visa': 'abc'}, 0),
             ('holder', {'nom': 'leonardo di costanzo'}, 1),
             ('holder', {'identifiant': SAMPLES['holder']['identifiant'], 'nom': 'personne-zzzz'}, 0),
             ('holder', {'identifiant': 'uuid-invalide'}, 0)]
    for kind, values, expected in cases:
        query = definitions(kind, base, dict(film=0, holder=0))[0]['query']
        result = api('POST', 'dataset', dataset_query(db, kind, query, values))
        if result.get('status') != 'completed' or result['data']['rows'] != [[expected]]:
            raise RuntimeError(f'Recherche {kind} non conforme : {list(values)}')
    print('Recherches par nom, sans résultat et filtres cumulés : OK', flush=True)
    if args.check:
        return

    collection = unique(api('GET', 'collection'), COLLECTION)
    if not collection:
        collection = api('POST', 'collection', {'name': COLLECTION,
                         'description': 'Fiches métier : films, personnes et sociétés. Données finales Cinestats.',
                         'color': '#509EE3', 'parent_id': None})
    cid = collection['id']
    if collection.get('location') not in (None, '/'):
        raise RuntimeError('La collection des fiches doit être à la racine, hors Operations.')
    items = api('GET', f'collection/{cid}/items')['data']
    ids = {}
    for kind, name in NAMES.items():
        dashboard = unique([i for i in items if i['model'] == 'dashboard'], name)
        if not dashboard:
            dashboard = api('POST', 'dashboard', {'name': name, 'collection_id': cid,
                             'parameters': parameters(kind), 'description': 'Fiche métier Cinestats.'})
        ids[kind] = dashboard['id']
    for kind, dashboard_id in ids.items():
        dashboard = api('GET', f'dashboard/{dashboard_id}')
        existing = {c['card_id']: c for c in dashboard.get('dashcards', []) if c.get('card_id')}
        layout, managed = [], set()
        for index, definition in enumerate(definitions(kind, base, ids)):
            name = f"{NAMES[kind]} · {definition['name']}"
            card = unique([i for i in items if i['model'] == 'card'], name)
            settings = dict(definition['visualization_settings'])
            if definition['display'] in ('table', 'object'):
                settings.update(table_settings())
            body = {'name': name, 'collection_id': cid, 'display': definition['display'],
                    'description': definition['description'] or 'Données finales Cinestats ; filtres cumulés.',
                    'dataset_query': dataset_query(db, kind, definition['query']),
                    'visualization_settings': settings}
            if card:
                card = api('PUT', f"card/{card['id']}", body)
            else:
                card = api('POST', 'card', body)
            card_id = card['id']
            managed.add(card_id)
            placement = {k: definition[k] for k in ('row', 'col', 'size_x', 'size_y')}
            placement.update(id=existing.get(card_id, {}).get('id', -(index + 1)), card_id=card_id,
                             visualization_settings={'card.title': definition['name']},
                             parameter_mappings=[{'parameter_id': p['id'], 'card_id': card_id,
                               'target': ['variable', ['template-tag', p['id']]]} for p in parameters(kind)])
            layout.append(placement)
        virtual = {'name': None, 'display': 'text', 'dataset_query': {}, 'archived': False,
                   'visualization_settings': {}}
        old_intro = next((c for c in dashboard.get('dashcards', [])
                          if c.get('visualization_settings', {}).get('ric_profile_intro')), {})
        layout.append({'id': old_intro.get('id', -100), 'card_id': None, 'row': 0, 'col': 0,
                       'size_x': 24, 'size_y': 3, 'parameter_mappings': [],
                       'visualization_settings': {'virtual_card': virtual, 'text': intro(kind, base, ids),
                                                  'ric_profile_intro': True}})
        layout.extend(c for c in dashboard.get('dashcards', []) if c.get('card_id') not in managed
                      and not c.get('visualization_settings', {}).get('ric_profile_intro'))
        api('PUT', f'dashboard/{dashboard_id}', {
            'name': NAMES[kind], 'parameters': parameters(kind), 'dashcards': layout,
            'description': 'Fiche métier alimentée par les tables finales Cinestats. '
                           'Rechercher par identifiant exact ou nom partiel (sans distinction de casse). '
                           'Si les deux filtres sont remplis, les critères se cumulent. '
                           'Valeurs vides = données non renseignées. Actualisé après reconstruction des données finales.'})
        saved = api('GET', f'dashboard/{dashboard_id}')
        assert saved['collection_id'] == cid
        assert managed.issubset({c.get('card_id') for c in saved['dashcards']})
        for c in saved['dashcards']:
            if c.get('card_id') in managed:
                assert c['card']['dataset_query']['database'] == db
                assert {p['parameter_id'] for p in c['parameter_mappings']} == {p['id'] for p in parameters(kind)}
        print(f"Vérifié : {base}/dashboard/{dashboard_id}", flush=True)


if __name__ == '__main__':
    main()
