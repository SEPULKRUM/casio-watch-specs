import json
import unittest
from pathlib import Path

import catalog
import manual_import
import product_import
import specs


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.build_catalog()

    def test_more_than_one_hundred_distinct_source_backed_models(self):
        self.assertGreaterEqual(len(self.catalog['models']), 100)
        self.assertEqual(len(self.catalog['models']), len(set(self.catalog['models'])))
        for record in specs.load('imports/official-products-expansion-2026-11-14.json'):
            self.assertIn('dimensions_mm', record['specs'])
            self.assertIn('weight_g', record['specs'])
            for fact in record['specs'].values():
                self.assertTrue(all(s['url'].startswith('https://www.casio.com/') for s in fact['sources']))

    def test_all_three_expansion_batches_reproduce(self):
        for source, batch, convert in [
            ('research/products-expansion-2026-11-14.json', 'imports/official-products-expansion-2026-11-14.json', product_import.convert),
            ('research/module-associations-expansion-2026-11-14.json', 'imports/support-module-associations-expansion-2026-11-14.json', manual_import.convert),
            ('research/manual-specifications-expansion-2026-11-14.json', 'imports/manual-specifications-expansion-2026-11-14.json', manual_import.convert)]:
            self.assertEqual(convert(specs.load(source)), specs.load(batch))

    def test_cloth_and_leather_bands_are_retained(self):
        cloth = self.catalog['models']['PRJ-B001WM-1']
        self.assertIn('cloth', catalog.field_value(cloth, 'band_material').lower())
        leather = self.catalog['models']['LWA-M145L-4AJF']
        self.assertEqual(catalog.field_value(leather, 'band_material'), 'Genuine leather')

    def test_wave_ceptor_accuracy_not_defaulted_to_fifteen_seconds(self):
        for module_id in ('5575', '5643', '5644'):
            module = self.catalog['modules'][module_id]
            self.assertEqual(catalog.field_value(module, 'accuracy_seconds_per_month'), 30)
            self.assertIn('radio', catalog.field_value(module, 'accuracy_condition'))

    def test_japanese_lineage_not_merged_into_european_identifier(self):
        japanese = self.catalog['models']['LCW-M100TSE-1AJF']
        european = self.catalog['models']['LCW-M100TSE-1A']
        self.assertEqual(catalog.field_value(japanese, 'module_id'), '5161')
        self.assertEqual(catalog.field_value(european, 'module_id'), '5161')
        self.assertEqual(catalog.module_view(self.catalog, european)['module_link_provenance'], 'user_provided')
        self.assertEqual(catalog.module_view(self.catalog, japanese)['module_link_provenance'], 'web')
        self.assertNotEqual(japanese['id'], european['id'])

    def test_earlier_model_and_module_facts_remain_exactly_unchanged(self):
        original_paths = [p for p in Path('imports').glob('*.json') if 'expansion' not in p.name]
        baseline = specs.build(specs.load('watches.json'), [r for p in sorted(original_paths) for r in specs.load(p)])
        self.assertEqual(baseline['legacy_watches'], self.catalog['legacy_watches'])
        for bucket in ('models', 'modules'):
            for key, record in baseline[bucket].items():
                for field, fact in record['specs'].items():
                    self.assertEqual(self.catalog[bucket][key]['specs'][field], fact)

    def test_sparse_profiles_and_field_coverage_are_reported(self):
        report = catalog.coverage(self.catalog)
        self.assertTrue(report['modules_with_sparse_profiles'])
        self.assertLess(report['module_field_coverage']['power_supply'], report['modules'])
        self.assertEqual(sum(report['module_profiles_by_fact_count'].values()), report['modules'])
        self.assertEqual(report['referenced_module_ids_without_specs'], [])

    def test_unavailable_support_pages_do_not_get_sibling_module_assignment(self):
        data = self.catalog['models']['PRJ-B001-1']
        self.assertEqual(catalog.field_value(data, 'module_id'), '5732')
        self.assertEqual(catalog.module_view(self.catalog, data)['module_link_provenance'], 'user_provided')
        self.assertEqual(catalog.module_view(self.catalog, self.catalog['models']['PRJ-B001-5'])['module_link_provenance'], 'web')
        self.assertEqual(catalog.field_value(self.catalog['models']['PRJ-B001-5'], 'module_id'), '5732')
