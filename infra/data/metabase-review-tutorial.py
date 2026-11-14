#!/usr/bin/env python3
"""Publier le guide métier illustré et ses liens dans Metabase Operations."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/runbooks/ingestion-tutoriel-revue-humaine-allocine.md'
BASE = 'https://metabase.cinestats5050.fr'
REPO = 'https://github.com/Le-Collectif-50-50/cinestats-5050/blob/main/'
RAW = 'https://raw.githubusercontent.com/Le-Collectif-50-50/cinestats-5050/main/'
NAME = 'Guide métier — Revoir une correspondance Allociné'
DASHBOARDS = {2: 'Pipeline Overview', 3: 'Qualité des données — dbt',
              7: 'Scraping Allociné — À examiner', 11: 'Suivi des données par visa CNC',
              9: 'Fiche Film'}
LABEL = 'Guide métier : revue humaine Allociné'


def target(url):
    if url.startswith(('https://', 'http://', '/')):
        return url
    path, _, anchor = url.partition('#')
    relative = (SOURCE.parent / path).resolve().relative_to(ROOT).as_posix()
    return REPO + relative + ('#' + anchor if anchor else '')


def inline(value):
    """Convertir les seuls styles présents dans le guide source."""
    nodes = []
    pattern = r'\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`|\*([^*]+)\*'
    end = 0
    for match in re.finditer(pattern, value):
        if match.start() > end:
            nodes.append({'type': 'text', 'text': value[end:match.start()]})
        if match[1]:
            nodes.append({'type': 'text', 'text': match[1], 'marks': [
                {'type': 'link', 'attrs': {'href': target(match[2])}}]})
        else:
            text = match[3] or match[4] or match[5]
            mark = 'bold' if match[3] else 'code' if match[4] else 'italic'
            if match[3]:
                for child in inline(text):
                    child.setdefault('marks', []).append({'type': 'bold'})
                    nodes.append(child)
            else:
                nodes.append({'type': 'text', 'text': text, 'marks': [{'type': mark}]})
        end = match.end()
    if end < len(value):
        nodes.append({'type': 'text', 'text': value[end:]})
    return nodes


def paragraph(value):
    return {'type': 'paragraph', 'content': inline(value)}


def document():
    """Convertir le Markdown en blocs natifs ; tableaux présentés en listes."""
    source = SOURCE.read_text().split('## Où retrouver ce tutoriel')[0]
    lines = source.splitlines()
    blocks = []
    i = 1  # Le titre est porté par le document Metabase.
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        image = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        heading = re.match(r'^(#{1,3}) (.+)', line)
        if image:
            path = (SOURCE.parent / image[2]).relative_to(ROOT).as_posix()
            blocks.append({'type': 'image', 'attrs': {
                'src': RAW + path, 'alt': image[1], 'title': image[1]}})
        elif heading:
            blocks.append({'type': 'heading', 'attrs': {'level': len(heading[1])},
                           'content': inline(heading[2])})
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            entries = []
            for row in rows[2:]:
                value = '**' + row[0] + '** — ' + ' ; '.join(row[1:])
                entries.append({'type': 'listItem', 'content': [paragraph(value)]})
            blocks.append({'type': 'bulletList', 'content': entries})
            continue
        elif re.match(r'^(?:\d+\. |\- )', line):
            ordered = bool(re.match(r'^\d+\.', line))
            entries = []
            expression = r'^\d+\. ' if ordered else r'^\- '
            while i < len(lines) and re.match(expression, lines[i].strip()):
                value = re.sub(expression, '', lines[i].strip())
                value = value.replace('[ ] ', '☐ ')
                entries.append({'type': 'listItem', 'content': [paragraph(value)]})
                i += 1
            blocks.append({'type': 'orderedList' if ordered else 'bulletList',
                           'content': entries})
            continue
        elif line.startswith('> '):
            blocks.append({'type': 'blockquote', 'content': [paragraph(line[2:])]})
        else:
            blocks.append(paragraph(line))
        i += 1
    return {'type': 'doc', 'content': blocks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=False)
    key = os.environ.get('METABASE_API_KEY')
    if not key:
        parser.error('METABASE_API_KEY requise.')

    def api(method, path, body=None):
        request = Request(BASE + '/api/' + path, method=method,
                          headers={'x-api-key': key, 'Content-Type': 'application/json'},
                          data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            raise SystemExit(f'{method} {path} : HTTP {error.code}') from None

    collection = api('GET', 'collection/7')
    assert collection['name'] == 'Cinestats 50/50 - Operations'
    items = api('GET', 'collection/7/items')['data']
    existing = [x for x in items if x['model'] == 'document' and x['name'] == NAME]
    assert len(existing) <= 1, 'Plusieurs guides homonymes ; vérifier manuellement.'
    dashboards = {did: api('GET', f'dashboard/{did}') for did in DASHBOARDS}
    for did, dash in dashboards.items():
        assert dash['name'] == DASHBOARDS[did], f'Dashboard {did} inattendu.'
    content = document()
    print(f'Guide : {len(content["content"])} blocs, '
          f'{sum(n["type"] == "image" for n in content["content"])} captures.')
    if not args.apply:
        print('Prévisualisation seule ; --apply pour publier.')
        return
    body = {'name': NAME, 'collection_id': 7, 'document': content}
    if existing:
        saved = api('PUT', f'document/{existing[0]["id"]}', body)
    else:
        saved = api('POST', 'document', body)
    did = saved['id']
    url = BASE + f'/document/{did}'
    reread = api('GET', f'document/{did}')
    assert reread['collection_id'] == 7 and reread['document'] == content
    print('Document publié et relu :', url, flush=True)
    text = (f'**[{LABEL}]({url})** — Vérifier les preuves, renseigner le Sheet, '
            'demander une ingestion, puis suivre la collecte et la publication.')
    for dashboard_id, dashboard in dashboards.items():
        if not dashboard.get('can_write', False):
            assert any(LABEL in c.get('visualization_settings', {}).get('text', '') and
                       url in c.get('visualization_settings', {}).get('text', '')
                       for c in dashboard['dashcards']), (
                           f'Dashboard {dashboard_id} : lien absent et droits insuffisants.')
            print('Lien existant vérifié (lecture seule) :',
                  BASE + f'/dashboard/{dashboard_id}', flush=True)
            continue
        cards = deepcopy(dashboard['dashcards'])
        link_card = next((c for c in cards if not c.get('card_id') and LABEL in
                          c.get('visualization_settings', {}).get('text', '')), None)
        if link_card:
            link_card['visualization_settings']['text'] = text
        else:
            for card in cards:
                card['row'] += 2
            cards.append({'id': -1, 'card_id': None, 'row': 0, 'col': 0,
                          'size_x': 24, 'size_y': 2, 'parameter_mappings': [],
                          'visualization_settings': {'text': text, 'virtual_card': {
                              'name': None, 'display': 'text', 'dataset_query': {},
                              'archived': False, 'visualization_settings': {}}}})
        api('PUT', f'dashboard/{dashboard_id}', {'dashcards': cards})
        reread = api('GET', f'dashboard/{dashboard_id}')
        assert len(reread['dashcards']) == len(cards)
        assert any(c.get('visualization_settings', {}).get('text') == text
                   for c in reread['dashcards'])
        assert reread['parameters'] == dashboard['parameters']
        assert {c.get('card_id') for c in reread['dashcards']} == {
            c.get('card_id') for c in cards}
        print('Lien enregistré et relu :', BASE + f'/dashboard/{dashboard_id}', flush=True)


if __name__ == '__main__':
    main()
