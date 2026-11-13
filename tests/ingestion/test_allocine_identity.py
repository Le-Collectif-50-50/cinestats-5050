import asyncio
import unittest

import pytest

from ingestion.scraping.browser import WebsiteBlockedError
from ingestion.scraping.allocine.allocine_scraper import AllocineScraper
from ingestion.scraping.allocine.connector import AllocineAirbyteSource, _identity_status


class IdentityTests(unittest.TestCase):
    def test_director_normalization_and_corealisation(self):
        self.assertEqual(_identity_status('1', '-', 'BUDINA Robert', ['Robert Budina'])[0], 'success')
        self.assertEqual(_identity_status('1', None, 'DUPONT Élodie / MARTIN Jean', ['Jean Martin', 'Elodie Dupont'])[0], 'success')
        self.assertEqual(_identity_status('1', None, 'BUDINA Robert', ['Giulio Bertelli'])[0], 'needs_review')
        self.assertEqual(_identity_status('1', None, 'BUDINA Robert', [])[0], 'needs_review')
        self.assertEqual(_identity_status('1', None, 'BUDINA Robert / X', ['Robert Budina'])[0], 'needs_review')
        self.assertEqual(_identity_status('1', None, 'BUDINA Robert / MARTIN Jean', ['Robert Budina'])[0], 'needs_review')

    def test_visa_precedence(self):
        self.assertEqual(_identity_status('1', '2', 'BUDINA Robert', ['Robert Budina'])[0], 'visa_mismatch')
        self.assertEqual(_identity_status('1', '1', None, [])[0], 'success')

    def test_directors_from_movie_structured_data(self):
        html = '<script type="application/ld+json">{"@graph":[{"@type":"Movie","director":[{"name":"Robert Budina"}]}]}</script>'
        self.assertEqual(AllocineScraper().extract_film_details(html)['directors'], ['Robert Budina'])

    def test_search_candidates_are_distinct(self):
        html = ''.join(f'<a class="meta-title-link" href="/film/fichefilm_gen_cfilm={i}.html">Agon</a>' for i in [10, 10, 20])
        self.assertEqual([r['id'] for r in AllocineScraper().extract_searched_films(html)], [10, 20])

    def run_search(self, directors, manual_validation=False):
        class Session:
            async def fetch_html(self, url):
                return url

        class Scraper(AllocineScraper):
            def extract_searched_films(self, html):
                return [{'id': i, 'title': 'Agon'} for i in directors]

            def extract_film_details(self, html):
                return {'allocine_visa_number': '-'}

            def extract_film_casting(self, html):
                value = directors[int(html.split('fichefilm-')[1].split('/')[0])]
                if isinstance(value, Exception):
                    raise value
                return {'Direction': value}

        return asyncio.run(AllocineAirbyteSource()._scrape_one_record(
            'test', Session(), Scraper(),
            {'source_record_id': '131307', 'visa_number': '131307',
             'original_name': 'AGON', 'cnc_director': 'BUDINA Robert',
             'manual_validation': manual_validation},
        ))

    def test_wrong_first_candidate_then_correct_director(self):
        row = self.run_search({10: ['Giulio Bertelli'], 20: ['Robert Budina']})
        self.assertEqual(row['scrape_status'], 'success')
        self.assertEqual(row['allocine_id'], 20)
        self.assertEqual(row['match_strategy'], 'search')

    def test_incomplete_search_needs_review(self):
        row = self.run_search({10: ['Robert Budina'], 20: RuntimeError('timeout')})
        self.assertEqual(row['scrape_status'], 'needs_review')
        row = self.run_search({10: ['Robert Budina'], **{i: ['Other Director'] for i in range(20, 25)}})
        self.assertEqual(row['scrape_status'], 'needs_review')

    def test_multiple_matches_or_missing_director_need_review(self):
        for candidates in ({10: ['Robert Budina'], 20: ['Robert Budina']}, {10: []}):
            row = self.run_search(candidates)
            self.assertEqual(row['scrape_status'], 'needs_review')
            self.assertIsNone(row['allocine_id'])

    def test_checked_search_does_not_validate_unverified_candidates(self):
        row = self.run_search({10: ['Other Director']}, manual_validation=True)
        self.assertEqual(row['scrape_status'], 'needs_review')
        self.assertIsNone(row['allocine_id'])


def scrape_provided_id(validation, candidate_visa='999999', error=None, directors=None,
                       source_director=None):
    class Session:
        async def fetch_html(self, url):
            if error:
                raise error
            return url

    class Scraper(AllocineScraper):
        def extract_film_details(self, html):
            return {'allocine_visa_number': candidate_visa, 'duration': '1h 55min'}

        def extract_film_casting(self, html):
            return {'Direction': directors or [], 'Casting': ['Personne test']}

    return asyncio.run(AllocineAirbyteSource()._scrape_one_record(
        'test', Session(), Scraper(),
        {'source_record_id': '111392', 'visa_number': '111392', 'allocine_id': 111149,
         'original_name': 'Bamako', 'manual_validation': validation,
         'cnc_director': source_director},
    ))


@pytest.mark.parametrize('validation', [True, 'TRUE', ' vrai ', '1'])
@pytest.mark.parametrize('visa', ['999999', None])
def test_manual_override_preserves_both_visas_and_payload(validation, visa):
    # Visa fictif : ce test ne dépend pas de la fiche Allociné en ligne.
    row = scrape_provided_id(validation, candidate_visa=visa)
    assert row['scrape_status'] == 'success'
    assert row['match_strategy'] == 'manual_validation'
    assert row['visa_number'] == '111392'
    assert row['allocine_visa_number'] == visa
    assert row['allocine_id'] == 111149
    assert row['casting'] == ['Personne test']
    assert row['error_message'] is None


@pytest.mark.parametrize('validation', [False, 'FALSE', 'FAUX', '0', None, '', 'approved'])
@pytest.mark.parametrize('visa, status', [('999999', 'visa_mismatch'), (None, 'needs_review')])
def test_unchecked_or_unknown_validation_keeps_identity_checks(validation, visa, status):
    row = scrape_provided_id(validation, candidate_visa=visa)
    assert row['scrape_status'] == status
    assert row['match_strategy'] == 'provided_allocine_id'


@pytest.mark.parametrize('validation', [False, True, None])
def test_matching_visa_succeeds_without_manual_override(validation):
    row = scrape_provided_id(validation, candidate_visa='111392')
    assert row['scrape_status'] == 'success'
    assert row['match_strategy'] == 'provided_allocine_id'


def test_matching_director_without_visa_succeeds_without_validation():
    row = scrape_provided_id(False, candidate_visa=None, directors=['Abderrahmane Sissako'],
                            source_director='SISSAKO Abderrahmane')
    assert row['scrape_status'] == 'success'
    assert row['match_strategy'] == 'provided_allocine_id'


@pytest.mark.parametrize('error, status', [
    (RuntimeError('technical failure'), 'error'),
    (WebsiteBlockedError('blocked'), 'blocked'),
])
def test_manual_validation_does_not_hide_technical_failure(error, status):
    row = scrape_provided_id(True, error=error)
    assert row['scrape_status'] == status
    assert row['match_strategy'] == 'provided_allocine_id'
    assert str(error) in row['error_message']


if __name__ == '__main__':
    unittest.main()
