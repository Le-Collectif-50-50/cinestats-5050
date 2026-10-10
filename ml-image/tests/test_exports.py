"""Régression des exports CSV, sans poids ni inférence."""
import pickle
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from scripts.utils import gather_and_save_predictions


class ExportTests(unittest.TestCase):
    def test_poster_and_trailer_exports_from_native_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stored = root / 'stored_predictions'
            output = root / 'outputs'
            stored.mkdir()
            output.mkdir()
            character = {'age': '20-29', 'gender': 'Female', 'ethnicity': 'unknown'}
            records = {
                'poster': dict(character, occupied_area=0.25),
                'trailer': dict(character, occurence=2.0, **{'area occupied': 0.1}),
            }
            for kind, record in records.items():
                with (stored / f'123_{kind}_predictions.pkl').open('wb') as stream:
                    pickle.dump([record], stream)
            source = pd.DataFrame([{'visa_number': 123, 'allocine_id': 456}])
            gather_and_save_predictions(source, str(stored), str(output))
            poster = pd.read_csv(output / 'predictions_on_posters.csv')
            trailer = pd.read_csv(output / 'predictions_on_trailers.csv')
            self.assertEqual(poster.loc[0, 'visa_number'], 123)
            self.assertEqual(trailer.loc[0, 'allocine_id'], 456)
            self.assertEqual(poster.loc[0, 'poster_percentage'], 0.25)
            self.assertEqual(trailer.loc[0, 'time_on_screen'], 2.0)
            self.assertEqual(trailer.loc[0, 'average_size_on_screen'], 0.1)
            self.assertEqual(trailer.loc[0, 'age_max'], 29)


if __name__ == '__main__':
    unittest.main()
