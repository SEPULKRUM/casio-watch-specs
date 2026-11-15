import copy
import csv
import io
import tempfile
import unittest
from pathlib import Path

import catalog
import specs
import user_import


class SuppliedMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = 'research/user-module-mappings-2026-11-14.json'
        cls.notes = specs.load(cls.reference)
        cls.records = user_import.convert(cls.notes, cls.reference)
        cls.catalog = catalog.build_catalog()

    def test_original_claims_retained_with_explicit_owner_correction(self):
        self.assertEqual(len(self.records), 17)
        for row in self.notes['mappings']:
            record = self.catalog['models'][row['model']]
            self.assertEqual(catalog.field_value(record, 'module_id'), '1275' if row['model']=='F-105W-1A' else row['module'])
            fact = record['specs']['module_id']
            self.assertEqual(fact['status'], 'pending_review')
            self.assertEqual(fact['sources'][0]['kind'], 'user_provided')
            self.assertNotIn('url', fact['sources'][0])
            self.assertTrue(fact['sources'][0]['source_sha256'])

    def test_user_batch_reproduces(self):
        # Historical note is immutable; only the explicitly superseded row is excluded.
        self.assertEqual([r for r in self.records if r['id']!='F-105W-1A'], specs.load('imports/user-module-mappings-2026-11-14.json'))
        correction = specs.load('research/f105-module-correction-2026-11-15.json')
        self.assertEqual(user_import.convert(correction, 'research/f105-module-correction-2026-11-15.json'), specs.load('imports/zzzzzzzzzzzzz-f105-module-correction-2026-11-15.json'))

    def test_user_provenance_visible_in_lookup_coverage_and_csv(self):
        view = catalog.module_view(self.catalog, self.catalog['models']['PRJ-B001-1'])
        self.assertEqual(view['module_link_provenance'], 'user_provided')
        self.assertEqual(view['module']['id'], '5732')
        report = catalog.coverage(self.catalog)
        self.assertTrue(all('catalog_year' in self.catalog['models'][key]['specs'] for key in report['models_without_any_module_reference']))
        self.assertGreaterEqual(len(report['user_provided_module_references']), 17)
        self.assertGreaterEqual(len(report['models_with_ambiguous_manual']), 17)
        rows = list(csv.DictReader(io.StringIO(catalog.export_csv(self.catalog))))
        row = next(r for r in rows if r['model'] == 'A168WA-1W')
        self.assertEqual(row['module'], '3298')
        self.assertEqual(row['module_link_provenance'], 'user_provided')
        self.assertIn(self.reference, row['source_references'])

    def test_web_source_rules_cannot_be_bypassed_by_omitting_url(self):
        record = copy.deepcopy(self.records[0])
        source = record['specs']['module_id']['sources'][0]
        del source['kind']
        with self.assertRaises(ValueError):
            specs.validate(record)
        record = copy.deepcopy(self.records[0])
        record['specs']['module_id']['sources'][0]['url'] = 'https://www.casio.com/'
        with self.assertRaises(ValueError):
            specs.validate(record)

    def test_invalid_provenance_and_duplicate_models_rejected(self):
        record = copy.deepcopy(self.records[0])
        record['specs']['module_id']['sources'][0]['reference'] = 'research/../outside.json'
        with self.assertRaises(ValueError):
            specs.validate(record)
        notes = copy.deepcopy(self.notes)
        notes['mappings'].append(notes['mappings'][0])
        with self.assertRaises(ValueError):
            user_import.convert(notes, self.reference)

    def test_stale_or_unrelated_user_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            specs.write(root / self.reference, self.notes)
            records = copy.deepcopy(self.records)
            records[0]['specs']['module_id']['value'] = '9999'
            with self.assertRaises(ValueError):
                catalog.validate_user_evidence(root, records)
            changed = copy.deepcopy(self.notes)
            changed['mappings'][0]['module'] = '9999'
            specs.write(root / self.reference, changed)
            with self.assertRaises(ValueError):
                catalog.validate_user_evidence(root, self.records)

    def test_conflict_still_cannot_replace_existing_fact(self):
        bad = copy.deepcopy(self.records[0])
        bad['id'] = 'GW-M5610U-1'
        result = specs.build(specs.load('watches.json'), [bad])
        self.assertTrue(result['report']['conflicts'])
        self.assertEqual(result['models']['GW-M5610U-1']['module'], '3495')

    def test_operations_only_manuals_do_not_gain_unsupported_accuracy(self):
        for module_id in ('1572', '2784', '2888'):
            self.assertNotIn('accuracy_seconds_per_month', self.catalog['modules'][module_id]['specs'])
        self.assertEqual(catalog.field_value(self.catalog['modules']['3298'], 'accuracy_seconds_per_month'), 30)
        self.assertEqual(catalog.field_value(self.catalog['modules']['3476'], 'accuracy_seconds_per_month'), 15)

    def test_f105_video_correction_agrees_with_supplier_without_borrowing_specs(self):
        fact = self.catalog['models']['F-105W-1A']['specs']['module_id']
        self.assertEqual(fact['value'], '1275')
        self.assertEqual(fact['sources'][0]['reference'], 'research/f105-module-correction-2026-11-15.json')
        historical = next(r for r in self.notes['mappings'] if r['model']=='F-105W-1A')
        self.assertEqual(historical['module'], '1572')
        parts = specs.load('data/parts-links.json')['models']['F-105W-1A']
        self.assertEqual(parts['observed_module_ids'], ['1275'])
        self.assertEqual(parts['recorded_module_ids'], ['1275'])
        self.assertEqual(parts['module_comparison'], 'agrees_with_recorded_reference')
        profile = self.catalog['modules']['1275']['specs']
        self.assertEqual(profile['stopwatch']['value']['max_display_seconds'], 3599.99)
        for unknown in ['accuracy_seconds_per_month','power_supply','calendar']:
            self.assertNotIn(unknown, profile)
        self.assertIn('1572', self.catalog['modules'])
