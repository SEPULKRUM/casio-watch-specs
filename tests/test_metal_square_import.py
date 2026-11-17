import json,unittest
from pathlib import Path
import specs,catalog,metal_square_import as importer
class MetalSquareTests(unittest.TestCase):
 def setUp(self):
  self.note=specs.load(importer.REFERENCE);self.records=importer.convert(self.note,importer.REFERENCE,uncertainty=importer.UNCERTAINTY)
 def test_reproducible_exact_citations_and_all_source_rows(self):
  self.assertEqual(len(self.note['source_rows']),58);self.assertEqual(len(self.note['models']),51)
  self.assertEqual(specs.load(importer.IMPORT),self.records)
  for p,s in importer.artifacts(Path('.')).items():self.assertEqual(Path(p).read_text(),s)
  catalog.validate_user_evidence(Path('.'),self.records)
  self.assertEqual(len(self.note['source_documents']['metal_squares']['source_urls']),12)
  self.assertEqual(len(self.note['archive_lookup']),12)
 def test_every_entry_is_accessible_with_uncertain_labels_excluded_from_watch_counts(self):
  rows={r['id']:r for r in specs.load('data/search-index.json')['records']}
  for id in self.note['models']:self.assertEqual(rows[id]['category'],'watch',id)
  resolutions=specs.load('research/supplied-seven-special-variants-2026-11-17.json')['category_resolutions']
  for id in self.note['uncertain_identifiers']:self.assertEqual(rows[id]['category'],resolutions.get(id,'uncertain'),id)
  for r in self.note['unresolved_labels']:self.assertEqual(rows[r['reading']]['category'],'uncertain')
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_series_and_approximate_specs_are_not_assigned_to_variants(self):
  records={r['id']:r for r in self.records if r['kind']=='model'}
  for id in ['GMW-B5000GD-1','GMW-B5000PC-1','GW-B5600CY-1','GW-B5600CD-9']:
   self.assertNotIn('dimensions_mm',records[id]['specs']);self.assertNotIn('weight_g',records[id]['specs']);self.assertNotIn('glass',records[id]['specs'])
  for id in ['GMW-B5000TB-1','GMW-B5000TCM-1','GW-B5600BC-1']:
   self.assertNotIn('weight_g',records[id]['specs']);self.assertIn('reported_measurements',records[id]['specs'])
  self.assertNotIn('module_id',records['G-D5000-9']['specs']);self.assertNotIn('module_id',records['GMW-B5000RD-4']['specs'])
 def test_exact_physical_specs_and_module_functions_remain_separate(self):
  c=specs.load('data/catalog.json')
  self.assertEqual(c['models']['GMW-B5000PG-9']['specs']['weight_g']['value'],167)
  self.assertEqual(c['models']['GW-B5600-2']['specs']['weight_g']['value'],53)
  self.assertEqual(c['models']['GMW-B5000TCC-1']['specs']['weight_g']['value'],104)
  for r in self.records:
   if r['kind']=='module':self.assertFalse(set(r['specs'])&{'dimensions_mm','weight_g','glass','case_material','water_resistance_m'})
  self.assertEqual(c['modules']['3540']['specs']['world_time_zones']['value'],39)
 def test_prior_verified_claims_still_preserved(self):
  c=specs.load('data/catalog.json');self.assertEqual(c['models']['GW-M5610-1']['specs']['weight_g']['status'],'verified')
  self.assertNotIn('GMW-B5000PS-1ROCKFORPEOPLE',c['models'])
