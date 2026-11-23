import copy
import unittest
from pathlib import Path

import specs

ROOT = Path(__file__).resolve().parents[1]
IMPORT = ROOT / 'imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-gmwb5000ss-shriro-archive-2026-11-23.json'


class ShriroArchiveTests(unittest.TestCase):
    def test_exact_australian_identifier_and_archive_provenance(self):
        records = specs.load(IMPORT)
        self.assertEqual([row['id'] for row in records], ['GMWB5000SS-2D'])
        for record in records:
            specs.validate(record)
            self.assertNotIn('dimensions_mm', record['specs'])
            self.assertNotIn('weight_g', record['specs'])
            self.assertNotIn('module_id', record['specs'])
            self.assertIn('catalog_source_references', record['specs'])
            for fact in record['specs'].values():
                for source in fact['sources']:
                    specs.validate_archive_source(source)
                    self.assertEqual(source['archive_timestamp'], '20250908181201')

    def test_article_does_not_overwrite_hyphenated_references(self):
        catalog = specs.load(ROOT / 'data/catalog.json')
        self.assertIn('GMWB5000SS-2D', catalog['models'])
        self.assertIn('GMW-B5000SS-2', catalog['models'])
        self.assertEqual(catalog['models']['GMWB5000SS-2D']['specs']['case_material']['value'], 'Stainless steel')
        self.assertEqual(catalog['models']['GMWB5000SS-2D']['specs']['case_material']['status'], 'pending_review')

    def test_distributor_allowlist_rejects_lookalike_domain(self):
        source = specs.load(IMPORT)[0]['specs']['series']['sources'][0]
        bad = copy.deepcopy(source)
        for field in ('url', 'original_url'):
            bad[field] = bad[field].replace('www.shopcasio.shriro.com.au', 'www.shopcasio.shriro.com.au.evil.example')
        with self.assertRaises(ValueError):
            specs.validate_archive_source(bad)


if __name__ == '__main__':
    unittest.main()
