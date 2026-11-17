import unittest
from pathlib import Path
import ocean_wave_import as imp
import specs,catalog
class OceanWaveTests(unittest.TestCase):
 def test_reproducible_bound_sources(self):
  root=Path(__file__).resolve().parents[1]
  for p,s in imp.artifacts(root).items():self.assertEqual((root/p).read_text(),s)
  catalog.validate_user_evidence(root,specs.load(root/imp.IMPORT))
 def test_complete_inventory_and_separate_partial_categories(self):
  n=specs.load(imp.REFERENCE);idx=specs.load('data/search-index.json');rows={x['id']:x for x in idx['records']}
  self.assertEqual(len(n['models']),17);self.assertEqual(len(n['inventory_rows']),21)
  for id,category in n['category_resolutions'].items():self.assertEqual(rows[id]['category'],category,id)
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_nominal_mass_and_incomplete_references_never_gain_invented_facts(self):
  c=specs.load('data/catalog.json');m=c['models']
  for id in ['OCW-T1010-1AJF','OCW-T1010B-1AJF','OCW-T1010G-7AJF','OAW-100TDJ-1AJF','OAW-100TDJ-7AJF','LCW-100TDJ-2A2JF','WVA-320DJ-1E']:
   self.assertNotIn('weight_g',m[id]['specs']);self.assertNotIn('dimensions_mm',m[id]['specs'])
  for id in ['LCW-110','LCW-110T','LIW-100TDJ','LIW-110T']:self.assertNotIn('module_id',m[id]['specs'])
  self.assertNotIn('release_date',m['OCW-T1010G-7AJF']['specs'])
  self.assertNotIn('module_id',m['OCW-T1010G-7AJF']['specs'])
  for x in specs.load(imp.IMPORT):
   if x['kind']=='module':self.assertEqual(set(x['specs']),{'series_pdf_evidence'})
