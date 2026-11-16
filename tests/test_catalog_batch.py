import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text())

class CatalogBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = read('research/catalog-batch-oceanus-2016-2026-11-16.json')
        cls.ocr = read('research/watchnavi-2015-ocr-reference-2026-11-16.json')
        cls.rows = read('imports/zzzzzzzzzzzzzzzzzzzzzz-catalog-batch-oceanus-2016-2026-11-16.json')

    def test_catalog_listings_are_complete_and_merged(self):
        catalogs = self.batch['catalogs']
        self.assertEqual([len(catalogs[k]['models']) for k in ['oceanus', '2016']], [112, 211])
        ids = {r['id'] for c in catalogs.values() for r in c['models']}
        self.assertEqual(ids, {r['id'] for r in self.rows})
        self.assertEqual(len(ids), 308)
        self.assertEqual(sum(len(r['specs']['catalog_source_references']['value']) for r in self.rows), 323)

    def test_shared_features_do_not_become_exact_hardware_claims(self):
        for row in self.rows:
            self.assertEqual(row['kind'], 'model')
            self.assertLessEqual(set(row['specs']), {'series', 'catalog_source_references'})
        section = self.batch['catalogs']['2016']['sections'][0]
        self.assertIn('distinct model', ' '.join(section['reference_notes']))

    def test_check_suffix_and_source_pages_survive(self):
        rows = [r for r in self.batch['catalogs']['2016']['models'] if r['uncertain_suffix']]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['printed_label'], 'PRW-6100Y-1AJF [CHECK]')
        for catalog in self.batch['catalogs'].values():
            for row in catalog['models']:
                self.assertGreater(row['original_pdf_page'], 0)
                self.assertGreater(row['extraction_pdf_page'], 0)

    def test_ocr_placements_duplicates_and_bad_readings_are_retained(self):
        rows = self.ocr['placements']
        self.assertEqual(len(rows), 2098)
        self.assertEqual(len({r['model_string'] for r in rows}), 2059)
        self.assertEqual([r['placement_id'] for r in rows], list(range(1, 2099)))
        self.assertEqual(sum(not r.get('normalized_identifier') for r in rows), 34)
        self.assertEqual(len(self.ocr['unresolved_labels']), 42)
        self.assertEqual(self.ocr['unresolved_labels'][0]['raw_label'], 'DW-OOlJ-9')
        self.assertTrue(all('release_date' not in r for r in rows))

    def test_unreliable_feature_phrase_stays_raw_research(self):
        row = self.ocr['placements'][0]
        self.assertEqual(row['model_string'], 'DW-5000C-1A')
        self.assertIn('Mud-resistant', row['feature_phrases'])
        self.assertTrue(row['ocr_review_flag'])
        self.assertTrue(row['visual_check_reported_by_compilation'])
        self.assertTrue(all('feature_phrases' not in r['specs'] for r in self.rows))
