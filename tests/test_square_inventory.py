import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text())

class SquareInventoryTests(unittest.TestCase):
    def test_pdf_references_are_covered_without_regional_duplicates(self):
        inventory = read('research/owner-gwm5610-parts-inventory-2026-11-15.json')
        catalog = read('data/catalog.json')
        ids = [row['canonical_model'] for row in inventory['models']]
        self.assertEqual(len(ids), 32)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertTrue(all(model in catalog['models'] for model in ids))
        self.assertNotIn('GW-M5610U-1BER', catalog['models'])
        self.assertNotIn('GW-M5610PC-1PRDB', catalog['models'])

    def test_support_only_records_do_not_inherit_physical_specs(self):
        records = read('imports/zzzzzzzzzzzz-supplied-gwm5610-support-2026-11-15.json')
        self.assertTrue(records)
        for row in records:
            self.assertEqual(set(row['specs']), {'series', 'module_id'})
            self.assertEqual(row['specs']['module_id']['value'], '3159')
            self.assertIn('support.' + row['id'], row['specs']['module_id']['sources'][0]['url'])

    def test_new_u2_has_its_own_official_module_and_dimensions(self):
        row = read('data/catalog.json')['models']['GW-M5610U-2']['specs']
        self.assertEqual(row['module_id']['value'], '3495')
        self.assertEqual(row['dimensions_mm']['value'], {'length': 46.7, 'width': 43.2, 'thickness': 12.7})
        self.assertEqual(row['weight_g']['value'], 52)
        self.assertNotIn('display_polarity', row)
