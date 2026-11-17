import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import unittest

import unified_index
from reference_import import MODEL

ROOT=Path(__file__).resolve().parents[1]

class UnifiedIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index=json.loads((ROOT/'data/search-index.json').read_text())
        cls.report=json.loads((ROOT/'data/reconciliation-report.json').read_text())
        cls.master=json.loads((ROOT/'research/casio-master-research-2026-11-16.json').read_text())
        cls.catalog=json.loads((ROOT/'data/catalog.json').read_text())
        cls.rows={r['id']:r for r in cls.index['records']}

    def test_every_master_reference_is_accessible_without_splitting_fitment(self):
        self.assertEqual(len(self.master['models']),29286)
        for row in self.master['models']:
            self.assertIn(row['model_id'],self.rows)
            indexed=self.rows[row['model_id']]
            if 'combined/parts' in row.get('reference_type',''):
                self.assertEqual(indexed['category'],'fitment')
            elif MODEL.fullmatch(row['model_id']) and not unified_index.BATTERY.fullmatch(row['model_id']):
                resolution=self.report.get('special_reference_category_resolutions',{}).get(row['model_id'])
                if resolution:self.assertEqual(indexed['category'],resolution)
                else:self.assertIn(indexed['category'],['watch','family','clock'])
        self.assertEqual(sum(r['category']=='fitment' for r in self.rows.values()),1212)

    def test_all_catalog_records_and_explicit_aliases_remain_exact(self):
        for identifier,row in self.catalog['models'].items():
            self.assertIn(identifier,self.rows)
            self.assertEqual(self.rows[identifier]['catalog_id'],identifier)
            for alias in row['specs'].get('supplied_aliases',{}).get('value',[]):self.assertIn(alias,self.rows)
        for code in ['GW-9400KJ-8','GW-9503KJ-2','GWF-D1035B-1','DW-8140TC-4','OCW-G1200-2AJF','GAC-2500-9A']:
            self.assertIn(code,self.rows);self.assertEqual(self.rows[code]['category'],'watch')
        self.assertNotEqual(self.rows['GW-M5610U-1']['id'],self.rows['GW-M5610U-1JF']['id'])

    def test_explicit_fitment_resolution_retains_individual_models_and_source_claims(self):
        resolution=self.index['fitment_resolutions'][0]
        self.assertEqual(resolution['model_id'],'A-151/153/155-1A')
        self.assertEqual(resolution['related_models'],['A-151-1A','A-153-1A','A-155-1A'])
        self.assertEqual(self.rows[resolution['model_id']]['category'],'fitment')
        for member in resolution['related_models']:
            self.assertEqual(self.rows[member]['category'],'watch')
            self.assertFalse(self.rows[member]['has_specifications'])
            self.assertEqual(self.rows[member]['module_ids'],[])
        self.assertTrue(all(claim['status'] for note in resolution['model_notes'] for claim in note['claims']))
        self.assertIn('factory configuration',resolution['restoration_note']['status'])

    def test_clock_family_and_uncertain_sources_do_not_inflate_individual_count(self):
        index2011=json.loads((ROOT/'research/catalog-index-2011-2026-11-15.json').read_text())
        for row in index2011['clock_rows']:self.assertEqual(self.rows[row['id']]['category'],'clock')
        for row in index2011['watch_rows']:self.assertEqual(self.rows[row['id']]['category'],'family')
        ocr=json.loads((ROOT/'research/watchnavi-2015-ocr-reference-2026-11-16.json').read_text())
        for row in ocr['placements']:self.assertIn(row['model_string'],self.rows)
        for row in ocr['unresolved_labels']:self.assertIn(row['raw_label'],self.rows)
        uncertain=json.loads((ROOT/'research/historical-catalog-1980-1989.json').read_text())['uncertain_readings']
        for row in uncertain:self.assertIn(row['reading'],self.rows)
        self.assertEqual(self.rows['DW-OOlJ-9']['category'],'uncertain')
        self.assertEqual(self.report['distinct_individual_watch_identifiers'],sum(r['category']=='watch' for r in self.rows.values()))

    def test_zero_eligible_omissions_and_consistent_duplicate_reconciliation(self):
        self.assertEqual(self.report['models_missing_from_published_search_index'],[])
        self.assertEqual(self.report['missing_model_count'],0)
        expected=set(self.report['expected_eligible_individual_identifiers'])
        self.assertEqual(expected,{r['id'] for r in self.rows.values() if r['category']=='watch'})
        self.assertEqual(self.report['total_imported_identifiers']-self.report['distinct_raw_identifiers'],self.report['duplicate_exact_identifiers'])
        self.assertEqual(self.report['reference_only_models']+self.report['models_with_specifications'],len(expected))
        self.assertEqual(self.report['index_sha256'],hashlib.sha256((ROOT/'data/search-index.json').read_bytes()).hexdigest())

    def test_all_datasets_and_import_scripts_are_in_the_audit(self):
        audited={r['path'] for r in self.report['source_audit']}
        inputs={p.relative_to(ROOT).as_posix() for folder in ['research','imports','data'] for p in (ROOT/folder).rglob('*.json') if p.relative_to(ROOT).as_posix() not in unified_index.OUTPUTS}
        self.assertTrue(inputs<=audited,inputs-audited)
        self.assertTrue({p.name for p in ROOT.glob('*import.py')}<=audited)
        self.assertIn('watches.json',audited)
        self.assertIn('research/recovered-intake-identifiers-2026-11-16.json',audited)
        self.assertEqual(self.report['published_dataset_aliases']['master-research.json'],'research/casio-master-research-2026-11-16.json')

    def test_unified_csv_contains_every_record_and_no_inherited_measurements(self):
        rows=list(csv.DictReader(io.StringIO((ROOT/'data/unified-models.csv').read_text())))
        self.assertEqual(len(rows),len(self.rows));self.assertEqual({r['model'] for r in rows},set(self.rows))
        row=next(r for r in rows if r['model']=='A-20-1A')
        self.assertFalse(row['weight_g']);self.assertFalse(row['length_mm']);self.assertFalse(row['glass'])
        self.assertEqual(row['specification_status'],'Specifications pending verification')

    def test_index_is_deterministic_in_a_fresh_process_and_checks_published_artifacts(self):
        run=subprocess.run(['python','unified_index.py','--check'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(self.index['generator_sha256'],unified_index.sha(ROOT/'unified_index.py'))
        for source in self.index['sources']:self.assertEqual(source['sha256'],unified_index.sha(ROOT/source['path']))

    def test_declared_identity_fields_and_proposed_aliases_cannot_be_skipped(self):
        keys={'model','model_id','listed_model','canonical_model','displayed_model','catalog_model','candidate_id','comparison_model','model_number','productName','productDisplayName'}
        lists={'proposed_aliases','aliases','supplied_aliases','model_strings','candidate_model_strings'}
        expected=set()
        def scan(value,key=''):
            if isinstance(value,dict):
                for name,item in value.items():
                    if name in keys and isinstance(item,str) and MODEL.fullmatch(item):expected.add(item)
                    if name in lists and isinstance(item,list):
                        expected.update(x for x in item if isinstance(x,str) and MODEL.fullmatch(x))
                    scan(item,name)
            elif isinstance(value,list):
                for item in value:scan(item,key)
        for folder in ['research','imports']:
            for path in (ROOT/folder).rglob('*.json'):scan(json.loads(path.read_text()))
        self.assertTrue(expected<=set(self.rows),sorted(expected-set(self.rows)))
        for id in ['GW-M5610U-1ER','GW-M5610U-1BER','GW-M5610-1ER']:
            self.assertIn(id,self.rows)
            self.assertEqual(self.rows[id]['category'],'watch')
