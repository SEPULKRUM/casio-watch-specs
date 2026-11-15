import copy
from pathlib import Path
import unittest

import product_data_import
import specs

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / 'research/square-support-feed-specifications-2026-11-15.json'
BATCH = ROOT / 'imports/zzzzzzzzzzzzzzzz-square-support-feed-specifications-2026-11-15.json'


class ProductDataImportTests(unittest.TestCase):
    def setUp(self):
        self.notes = specs.load(NOTE)
        self.data = specs.load(ROOT / 'data/catalog.json')
        # Recreate the pre-import records, leaving only previous identity/module facts.
        for row in specs.load(BATCH):
            for field in row['specs']:
                self.data['models'][row['id']]['specs'].pop(field)

    def test_selected_fields_reproduce_values_without_copying_assets_or_metadata(self):
        rows = product_data_import.convert(self.notes, self.data)
        expected = specs.load(BATCH)
        self.assertEqual(len(rows), 16)
        self.assertEqual(sum(len(r['specs']) for r in rows), 96)
        for row, wanted in zip(rows, expected):
            self.assertEqual(row['id'], wanted['id'])
            self.assertEqual({k: v['value'] for k, v in row['specs'].items()},
                             {k: v['value'] for k, v in wanted['specs'].items()})
            self.assertFalse({'module_id', 'release_date', 'glass', 'case_material',
                              'display_polarity', 'water_resistance_m'} & set(row['specs']))
            self.assertNotIn('productAssets', str(row))
            self.assertEqual(row['specs']['water_resistance_bar']['value'], 20)

    def test_wrong_model_sku_url_and_module_are_rejected(self):
        mutations = [lambda p: p['fields'].update(productName='GW-M5610U-1'),
                     lambda p: p['fields'].update(sku='GW-M5610B-1JR'),
                     lambda p: p.update(url=p['url'].replace('www.casio.com', 'casio.com.example.org')),
                     lambda p: p.update(url=p['url'].replace('GW-M5610B-1.json', 'GW-M5610CC-2.json')),
                     lambda p: p['fields'].update(moduleNumber='3495')]
        for mutate in mutations:
            notes = copy.deepcopy(self.notes)
            mutate(notes['products'][0])
            with self.assertRaises(ValueError):
                product_data_import.convert(notes, self.data)

    def test_bad_numbers_missing_unit_review_and_overwrites_are_rejected(self):
        for value in [True, -1, 0, float('inf'), float('nan'), '46.7']:
            notes = copy.deepcopy(self.notes)
            notes['products'][0]['fields']['height'] = value
            with self.assertRaises(ValueError):
                product_data_import.convert(notes, self.data)
        notes = copy.deepcopy(self.notes)
        notes.pop('unit_validation')
        with self.assertRaises(ValueError):
            product_data_import.convert(notes, self.data)
        with self.assertRaises(ValueError):
            product_data_import.convert(self.notes, specs.load(ROOT / 'data/catalog.json'))

    def test_variant_weights_and_japanese_market_identity_are_preserved(self):
        data = specs.load(ROOT / 'data/catalog.json')['models']
        for model, weight in [('GW-5000B-1', 73.8), ('GW-5000HR-1', 74),
                              ('GW-M5610CC-2', 51.7), ('GW-M5610LY-1', 52)]:
            self.assertEqual(data[model]['specs']['weight_g']['value'], weight)
        source = data['GW-5000B-1']['specs']['weight_g']['sources'][0]
        self.assertEqual(source['displayed_model'], 'GW-5000B-1JR')
        self.assertIn('Japanese-market', source['scope_note'])

    def test_catalogue_descriptors_do_not_overwrite_metadata_categories(self):
        data = specs.load(ROOT / 'data/catalog.json')['models']
        colour = data['GW-M5610SD-8']['specs']['color']
        self.assertEqual(colour['value'], 'Brown')
        self.assertIn('desert beige', colour['uncertainty'])
        self.assertEqual(len(colour['sources']), 2)
        self.assertIn('PDF page 10', colour['sources'][1]['locator'])
        self.assertEqual(data['GW-5000-1']['specs']['case_finish']['value'], 'DLC-coated screw-back')
        self.assertNotIn('case_finish', data['GW-5000B-1']['specs'])
