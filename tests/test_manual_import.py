import copy
import tempfile
import unittest
from pathlib import Path

import catalog
import manual_import
import specs


class ManualImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.build_catalog()
        cls.notes = specs.load('research/module-associations-2026-11-14.json')

    def test_shared_manual_does_not_select_first_module(self):
        model = self.catalog['models']['AE-1200WH-1AV']
        view = catalog.module_view(self.catalog, model)
        self.assertIsNone(view['module'])
        self.assertIsNone(view['module_id'])
        self.assertEqual(view['module_candidates'], ['3198', '3299'])
        self.assertEqual(view['module_link_status'], 'ambiguous_pending_review')
        self.assertEqual(set(view['module_options']), {'3198', '3299'})

    def test_module_specific_calendar_and_battery_exceptions_are_separate(self):
        a = self.catalog['modules']['437']
        b = self.catalog['modules']['438']
        c = self.catalog['modules']['3208']
        self.assertEqual(catalog.field_value(a, 'calendar')['end_year'], 2079)
        self.assertEqual(catalog.field_value(c, 'calendar')['end_year'], 2099)
        self.assertEqual(catalog.field_value(a, 'power_supply')['battery_type'], 'CR2016')
        self.assertEqual(catalog.field_value(b, 'power_supply')['battery_type'], 'CR1616')

    def test_regional_mismatch_not_promoted_to_module_link(self):
        model = self.catalog['models']['A168WA-1W']
        self.assertEqual(catalog.field_value(model, 'module_id'), '3298')
        self.assertEqual(catalog.module_view(self.catalog, model)['module_link_provenance'], 'user_provided')
        self.assertNotIn('module_candidates', model['specs'])
        row = next(r for r in self.notes['observations'] if r['model'] == 'A168WA-1W')
        self.assertEqual(row['status'], 'regional_identity_mismatch')

    def test_exact_model_heading_and_official_source_required(self):
        row = copy.deepcopy(next(r for r in self.notes['observations'] if r['status'] == 'candidate'))
        row['displayed_model'] += 'JF'
        with self.assertRaises(ValueError):
            manual_import.associations({'accessed': '2026-11-14', 'observations': [row]})
        with self.assertRaises(ValueError):
            manual_import.official('https://support.casio.com.evil.example/manual/5611_en/')

    def test_imports_reproduce_research_notes(self):
        for note, batch in [('research/module-associations-2026-11-14.json', 'imports/support-module-associations-2026-11-14.json'),
                            ('research/manual-specifications-2026-11-14.json', 'imports/manual-specifications-2026-11-14.json')]:
            self.assertEqual(manual_import.convert(specs.load(note)), specs.load(batch))

    def test_reference_coverage_and_no_missing_module_specs(self):
        report = catalog.coverage(self.catalog)
        self.assertGreaterEqual(report['models_with_single_module_reference'], 21)
        self.assertGreaterEqual(len(report['models_with_ambiguous_manual']), 8)
        self.assertTrue(all(('catalog_year' in self.catalog['models'][key]['specs'] or 'supplied_model_details' in self.catalog['models'][key]['specs'] or 'catalog_2011_reference' in self.catalog['models'][key]['specs'] or 'catalog_source_references' in self.catalog['models'][key]['specs'] or 'master_research_reference' in self.catalog['models'][key]['specs'] or 'research_pdf_evidence' in self.catalog['models'][key]['specs'] or 'metal_square_evidence' in self.catalog['models'][key]['specs'] or 'series_pdf_evidence' in self.catalog['models'][key]['specs']) for key in report['models_without_any_module_reference']))
        self.assertGreaterEqual(len(report['user_provided_module_references']), 17)
        self.assertEqual(report['referenced_module_ids_without_specs'], [])
        self.assertGreaterEqual(report['modules'], 32)

    def test_current_support_reference_and_accuracy_conditions_retained(self):
        model = self.catalog['models']['GMW-B5000D-1']
        self.assertEqual(catalog.field_value(model, 'module_id'), '3539')
        self.assertIn('historical production', model['specs']['module_id']['uncertainty'])
        condition = catalog.field_value(self.catalog['modules']['3539'], 'accuracy_condition')
        self.assertIn('phone', condition)
        self.assertIn('radio', condition)

    def test_ambiguous_import_cannot_replace_exact_or_legacy_module(self):
        record = manual_import.associations(self.notes)[0]
        if 'module_candidates' not in record['specs']:
            record = next(r for r in manual_import.associations(self.notes) if 'module_candidates' in r['specs'])
        record = copy.deepcopy(record)
        record['id'] = 'GW-M5610U-1'
        result = specs.build(specs.load('watches.json'), [record])
        self.assertTrue(result['report']['conflicts'])
        self.assertEqual(result['models']['GW-M5610U-1']['module'], '3495')

    def test_invalid_or_simultaneous_alternatives_rejected(self):
        record = next(r for r in manual_import.associations(self.notes) if 'module_candidates' in r['specs'])
        for value in (['3198'], ['3198', '3198'], ['3198', 'other']):
            altered = copy.deepcopy(record)
            altered['specs']['module_candidates']['value'] = value
            with self.assertRaises(ValueError):
                specs.validate(altered)
        altered = copy.deepcopy(record)
        altered['specs']['module_id'] = dict(altered['specs']['module_candidates'], value='3198')
        with self.assertRaises(ValueError):
            specs.validate(altered)

    def test_shared_identity_and_body_exceptions(self):
        url = 'https://www.casio.com/content/dam/casio/global/support/manuals/watches/pdf/32/3299/qw3299_EN.pdf'
        self.assertEqual(manual_import.document_modules(url, 'Operation Guide 3198/3299'), ['3198', '3299'])
        with self.assertRaises(ValueError):
            manual_import.document_modules(url, 'Operation Guide 5611')
        url = 'https://www.casio.com/content/dam/casio/global/support/manuals/watches/pdf/5/593/qw593_EN.pdf'
        self.assertEqual(manual_import.document_modules(url, 'Guide 10B+7L. Battery exception: Module 1271'), ['593', '1271'])

    def test_snapshot_batch_checks_actual_link_and_exact_heading(self):
        manual = 'https://www.casio.com/content/dam/casio/global/support/manuals/watches/pdf/32/3299/qw3299_EN.pdf'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            support = root / 'support.html'
            support.write_text(f'<h1>AE-1200WH-1AV</h1><a href="{manual}">User guide</a>')
            (root / 'manual.txt').write_text('Operation Guide 3198/3299')
            manifest = {'accessed': '2026-11-14', 'documents': [{'model':'AE-1200WH-1AV',
                'support_url':'https://www.casio.com/sg/watches/casio/support.AE-1200WH-1AV/',
                'support_path':'support.html','manual_url':manual,'manual_path':'manual.txt'}]}
            specs.write(root / 'manifest.json', manifest)
            result = manual_import.from_snapshots(root / 'manifest.json')
            self.assertEqual(result[0]['specs']['module_candidates']['value'], ['3198', '3299'])
            self.assertIn('snapshot_sha256', result[0]['specs']['module_candidates']['sources'][0])
            support.write_text('<h1>AE-1200WH-1AV</h1>')
            with self.assertRaises(ValueError):
                manual_import.from_snapshots(root / 'manifest.json')
