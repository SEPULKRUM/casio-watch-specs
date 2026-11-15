import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text())

class GW5000InventoryTests(unittest.TestCase):
    def test_pdf_identity_coverage_keeps_updated_generations_separate(self):
        inventory = read('research/owner-gw5000-inventory-2026-11-15.json')
        models = read('data/catalog.json')['models']
        ids = [row['canonical_model'] for row in inventory['models']]
        self.assertEqual(len(ids), 6)
        self.assertEqual(len(set(ids)), 6)
        for model in ids:
            self.assertIn(model, models)
            module = '3495' if model.startswith(('GW-5000U', 'GW-5000HS')) else '3159'
            self.assertEqual(models[model]['specs']['module_id']['value'], module)

    def test_support_import_does_not_infer_anniversary_materials(self):
        rows = read('imports/zzzzzzzzzzzz-supplied-gw5000-support-2026-11-15.json')
        self.assertEqual({row['id'] for row in rows}, {'GW-5000B-1', 'GW-5000HR-1', 'GW-5035A-1'})
        for row in rows:
            self.assertEqual(set(row['specs']), {'series', 'module_id'})
            self.assertEqual(row['specs']['module_id']['value'], '3159')
