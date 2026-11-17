import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import unittest

import master_research_import as intake
import specs

ROOT = Path(__file__).resolve().parents[1]

class MasterResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note = specs.load(ROOT / intake.REFERENCE)
        cls.records = specs.load(ROOT / intake.IMPORT)
        cls.catalog = specs.load(ROOT / 'data/catalog.json')
        previous = [r for path in sorted((ROOT / 'imports').glob('*.json')) if path.name != Path(intake.IMPORT).name for r in specs.load(path)]
        cls.baseline = specs.build(specs.load(ROOT / 'watches.json'), previous, specs.load(ROOT / 'reviews.json') if (ROOT / 'reviews.json').exists() else None)
        cls.models = {r['model_id']: intake.expand_model(cls.note, r) for r in cls.note['models']}

    def test_all_csv_values_round_trip_to_original_member_checksums(self):
        tables = [('Casio_Models_Master_Enriched.csv', list(self.models.values())), ('Casio_Modules_Functions.csv', self.note['modules']), ('Casio_Model_Module_Relationships.csv', self.note['relationships']), ('Casio_Sources.csv', self.note['source_register'])]
        for name, rows in tables:
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            self.assertEqual(hashlib.sha256(stream.getvalue().encode('utf-8-sig')).hexdigest(), self.note['members'][name]['sha256'])
        text = '\n'.join(self.models) + '\n'
        # Identifier list is UTF-8, preserving its original final newline.
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), self.note['members']['Casio_All_Model_Numbers_UPDATED.txt']['sha256'])

    def test_all_references_survive_without_fabricating_fitment_skus(self):
        self.assertEqual(len(self.models), 29286)
        self.assertEqual(sum(intake.eligible(r) for r in self.models.values()), 27960)
        combined = [r for r in self.models.values() if 'combined/parts' in r['reference_type']]
        self.assertEqual(len(combined), 1212)
        self.assertFalse(intake.eligible(self.models['A-151/153/155-1A']))
        self.assertNotIn('A-20-1A', self.catalog['models'])
        self.assertNotIn('A-151/153/155-1A', self.catalog['models'])

    def test_previous_catalog_fields_are_unchanged(self):
        for bucket in ['models', 'modules']:
            for key, row in self.baseline[bucket].items():
                for field, fact in row['specs'].items():
                    self.assertEqual(self.catalog[bucket][key]['specs'][field], fact)
        self.assertEqual(set(self.catalog['models']) - set(self.baseline['models']), {r['id'] for r in self.records if r['kind']=='model'} - set(self.baseline['models']))
        self.assertGreaterEqual(len(self.catalog['modules']), 282)

    def test_import_is_reproducible_and_never_accepts_compiler_verification(self):
        note = copy.deepcopy(self.note)
        for key in ['claims', 'comparisons']: note.pop(key)
        self.assertEqual(intake.proposals(note, self.baseline), self.records)
        self.assertEqual(note, self.note)
        self.assertEqual(sum(r['kind'] == 'model' for r in self.records), 289)
        for record in self.records:
            for field, fact in record['specs'].items():
                self.assertEqual(fact['sources'][0]['kind'], 'user_provided')
                self.assertNotIn('url', fact['sources'][0])
                self.assertEqual(self.catalog['models' if record['kind'] == 'model' else 'modules'][record['id']]['specs'][field]['status'], 'pending_review')

    def test_scope_and_variant_weight_differences_are_kept(self):
        for code, weight in [('GWF-D1000BC-1', 181), ('GMC-2500-1A', 68), ('GMC-2500D-1A', 138), ('GW-9503KJ-2', 88)]:
            self.assertEqual(self.catalog['models'][code]['specs']['weight_g']['value'], weight)
        self.assertEqual(self.catalog['models']['GAC-2500-1A']['specs']['master_research_reference']['value']['reported_fields']['weight_g'], '47')
        self.assertNotIn('weight_g', self.catalog['models']['GAC-2500-1A']['specs'])
        self.assertNotIn('dimensions_mm', intake.model_values(self.models['GWF-D1000ARR-1']))
        self.assertEqual(self.models['GW-9503KJ-2']['release_date'], '2026-11')
        self.assertEqual(self.models['GW-9503KJ-2']['release_date_precision'], 'Official Casio Japan release month')
        self.assertNotIn('release_date', self.catalog['models']['GW-9503KJ-2']['specs'])

    def test_relationship_table_adds_links_without_filling_blank_source_cell(self):
        self.assertEqual(self.models['DW-290-1V']['module_reference_number'], '')
        rows = [r for r in self.note['relationships'] if r['model_id'] == 'DW-290-1V']
        self.assertEqual({r['module_reference_number'] for r in rows}, {'1219', '1189', '3231'})
        self.assertEqual(self.note['counts']['models_with_module_reference'], 116)
        self.assertEqual(sum(bool(r['module_reference_number']) for r in self.models.values()), 115)

    def test_stopwatch_capacity_and_reception_qualifiers_remain_separate(self):
        modules = {r['module_reference_number']: r for r in self.note['modules']}
        self.assertEqual(modules['3445']['stopwatch_max_display_seconds'], '359999.99')
        self.assertEqual(modules['3410']['stopwatch_max_display_seconds'], '3599999.99')
        self.assertEqual(modules['3410']['radio_max_automatic_attempts_per_day_china'], '5')
        self.assertEqual(modules['3410']['radio_max_automatic_attempts_per_day'], '6')
        self.assertEqual(modules['3410']['radio_remaining_attempts_cancelled_after_success'], 'Yes')
        self.assertEqual(modules['1431']['stopwatch_max_display_seconds'], '')
        self.assertEqual(len(self.note['comparisons']), 50)
