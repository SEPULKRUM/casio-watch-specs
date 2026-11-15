from pathlib import Path
import unittest
import specs

ROOT = Path(__file__).resolve().parents[1]


class SquareColourwaySpecs(unittest.TestCase):
    def test_variant_weights_and_source_rating_units_are_preserved(self):
        data = specs.load(ROOT / 'data/catalog.json')['models']
        self.assertEqual(data['GW-M5610MR-4']['specs']['weight_g']['value'], 52)
        self.assertEqual(data['GW-M5610TH-1']['specs']['weight_g']['value'], 51.7)
        self.assertEqual(data['GW-M5610PC-1']['specs']['weight_g']['value'], 52)
        self.assertEqual(data['GW-M5610PC-1']['specs']['water_resistance_bar']['value'], 20)
        self.assertNotIn('water_resistance_m', data['GW-M5610PC-1']['specs'])
        for model in ['GW-M5610MR-4', 'GW-M5610TH-1']:
            self.assertEqual(data[model]['specs']['water_resistance_m']['value'], 200)

    def test_only_exact_cited_physical_specifications_are_imported(self):
        rows = specs.load(ROOT / 'imports/zzzzzzzzzzzzzzz-square-colourway-physical-specifications-2026-11-15.json')
        notes = specs.load(ROOT / 'research/square-colourway-physical-specifications-2026-11-15.json')
        self.assertEqual(sum(len(r['specs']) for r in rows), 23)
        for record, note in zip(rows, notes['products']):
            specs.validate(record)
            self.assertEqual({k: v['value'] for k, v in record['specs'].items()}, note['specifications'])
            self.assertFalse({'module_id', 'display_polarity', 'color', 'release_date'} & set(record['specs']))
            for fact in record['specs'].values():
                source = fact['sources'][0]
                specs.validate_archive_source(source)
                self.assertEqual(source['displayed_model'], record['id'] + 'ER')
                self.assertIn(record['id'].lower() + 'er/', source['original_url'])
                self.assertEqual(source['snapshot_sha256'], note['source']['snapshot_sha256'])
