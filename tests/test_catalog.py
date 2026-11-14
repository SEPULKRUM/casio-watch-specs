import copy
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import catalog
import discover
import product_import
import specs


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.build_catalog()

    def test_all_batches_have_sources_and_expected_family_coverage(self):
        report = catalog.coverage(self.catalog)
        self.assertGreaterEqual(report['models'], 40)
        self.assertGreaterEqual(report['modules'], 3)
        for family in ('G-SHOCK', 'Pro Trek', 'Oceanus', 'Lineage', 'Wave Ceptor'):
            self.assertGreaterEqual(report['models_by_series'][family], 3)
        for record in self.catalog['models'].values():
            for fact in record['specs'].values():
                self.assertEqual(fact['status'], 'pending_review')
                self.assertTrue(fact['sources'])

    def test_generic_water_resistance_is_not_assigned_depth(self):
        model = self.catalog['models']['F-91W-1']
        self.assertEqual(catalog.field_value(model, 'water_resistance_rating'), 'Water Resistant')
        self.assertNotIn('water_resistance_m', model['specs'])
        self.assertNotIn('water_resistance_bar', model['specs'])

    def test_japanese_bar_rating_is_not_silently_converted_to_depth(self):
        model = self.catalog['models']['OCW-S100-1AJF']
        self.assertEqual(catalog.field_value(model, 'water_resistance_bar'), 10)
        self.assertNotIn('water_resistance_m', model['specs'])

    def test_finish_is_not_mistaken_for_case_material(self):
        model = self.catalog['models']['MTP-1302D-1A1V']
        self.assertNotIn('case_material', model['specs'])
        self.assertEqual(catalog.field_value(model, 'case_finish'), 'Ion plated')

    def test_regional_suffixes_and_similar_models_stay_distinct(self):
        self.assertIn('A168WA-1W', self.catalog['models'])
        self.assertNotIn('A168WA-1', self.catalog['models'])
        self.assertIn('OCW-T200S-1AJF', self.catalog['models'])
        self.assertIn('GW-M5610U-1B', self.catalog['models'])
        self.assertEqual(self.catalog['models']['GW-M5610U-1']['module'], '3495')
        self.assertNotIn('module', self.catalog['models']['GW-M5610U-1B'])
        self.assertEqual(catalog.field_value(self.catalog['models']['GW-M5610U-1B'], 'module_id'), '3495')

    def test_search_and_csv_have_provenance(self):
        results = catalog.search(self.catalog, series='oceanus')
        self.assertGreaterEqual(len(results), 4)
        rows = list(csv.DictReader(io.StringIO(catalog.export_csv(self.catalog))))
        self.assertEqual(len(rows), len(self.catalog['models']))
        self.assertTrue(all(row['source_urls'].startswith('https://') for row in rows))
        self.assertEqual(catalog.search(self.catalog, verified_only=True), [])

    def test_verified_only_results_hide_pending_values(self):
        data = copy.deepcopy(self.catalog)
        model = data['models']['F-91W-1']
        model['specs']['weight_g']['status'] = 'verified'
        results = catalog.search(data, 'F-91W-1', verified_only=True)
        self.assertEqual(set(results[0]['specs']), {'weight_g'})

    def test_removed_verified_fact_and_review_changes_are_rejected(self):
        before = copy.deepcopy(self.catalog)
        before['models']['F-91W-1']['specs']['weight_g']['status'] = 'verified'
        for change in ('remove', 'value', 'status', 'source'):
            after = copy.deepcopy(before)
            fact = after['models']['F-91W-1']['specs']['weight_g']
            if change == 'remove':
                del after['models']['F-91W-1']['specs']['weight_g']
            elif change == 'value':
                fact['value'] = 500
            elif change == 'status':
                fact['status'] = 'pending_review'
            else:
                fact['sources'] = []
            with self.assertRaises(ValueError):
                catalog.preserve_verified(before, after)

    def test_unknown_module_not_guessed_but_explicit_link_is_available(self):
        self.assertEqual(catalog.field_value(self.catalog['models']['F-105W-1A'], 'module_id'), '1572')
        self.assertEqual(catalog.module_view(self.catalog, self.catalog['models']['F-105W-1A'])['module_link_provenance'], 'user_provided')
        self.assertEqual(catalog.field_value(self.catalog['models']['GA-B2100-1A'], 'module_id'), '5689')

    def test_research_import_reproducible(self):
        expected = specs.load('imports/official-products-2026-11-14.json')
        actual = product_import.convert(specs.load('research/products-2026-11-14.json'))
        self.assertEqual(expected, actual)

    def test_dimensions_validation_rejects_units_or_negative_values(self):
        record = specs.load('imports/official-products-2026-11-14.json')[0]
        for value in ([1, 2, 3], {'length': 1, 'width': 2, 'thickness': -1}):
            record['specs']['dimensions_mm']['value'] = value
            with self.assertRaises(ValueError):
                specs.validate(record)

    def test_csv_formula_values_are_escaped(self):
        self.assertEqual(catalog.spreadsheet_safe('=HYPERLINK("bad")'), '\'=HYPERLINK("bad")')


class DiscoveryTests(unittest.TestCase):
    def test_html_discovery_filters_and_normalizes(self):
        text = '''<a href="/intl/watches/gshock/product.DW-5600UE-1/?tracking=1">one</a>
        <a href="/intl/watches/gshock/product.DW-5600UE-1/#specs">duplicate</a>
        <a href="https://evil.example/intl/watches/gshock/product.A-1/">other</a>
        <a href="https://www.casio.com@evil.example/intl/watches/gshock/product.A-1/">bad</a>'''
        self.assertEqual(discover.discover(text, 'https://www.casio.com/intl/watches/'),
                         ['https://www.casio.com/intl/watches/gshock/product.DW-5600UE-1/'])

    def test_sitemap_discovery_does_not_follow_indexes(self):
        text = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.casio.com/intl/watches/casio/product.F-91W-1/</loc></url></urlset>'
        self.assertEqual(len(discover.discover(text, 'https://www.casio.com/')), 1)
        self.assertEqual(discover.discover('<sitemapindex><sitemap><loc>https://www.casio.com/a.xml</loc></sitemap></sitemapindex>', 'https://www.casio.com/'), [])

    def test_batch_html_adapter_and_checksum(self):
        html = '<h1>F-91W-1</h1><h2>Specifications</h2><h4>Case size (L× W× H)</h4><p>38.2 × 35.2 × 8.5 mm</p><h4>Weight</h4><p>21 g</p><h4>Water resistance</h4><p>Water Resistant</p>'
        with tempfile.TemporaryDirectory() as directory:
            import hashlib
            path = Path(directory) / 'page.html'
            path.write_text(html)
            report = Path(directory) / 'fetch-report.json'
            specs.write(report, [{'status': 'downloaded', 'path': str(path),
                'url': 'https://www.casio.com/intl/watches/casio/product.F-91W-1/',
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}])
            records = product_import.from_snapshots(report, '2026-11-14')
            self.assertEqual(records[0]['id'], 'F-91W-1')
            self.assertEqual(records[0]['specs']['weight_g']['value'], 21)
            path.write_text(html + 'changed')
            with self.assertRaises(ValueError):
                product_import.from_snapshots(report, '2026-11-14')

    def test_adapter_rejects_ambiguous_models(self):
        with self.assertRaises(ValueError):
            product_import.extract_html('<h1>A-1</h1><h1>A-2</h1>', 'https://www.casio.com/intl/watches/casio/product.A-1/', '2026-11-14')
