import asyncio
import unittest

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

    def run_search(self, directors):
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
             'original_name': 'AGON', 'cnc_director': 'BUDINA Robert'},
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


if __name__ == '__main__':
    unittest.main()
