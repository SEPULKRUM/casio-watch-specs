import json,unittest
from pathlib import Path
import specs,catalog,module_comparison_import as importer
class ModuleComparisonTests(unittest.TestCase):
 def setUp(self):
  self.note=specs.load(importer.REFERENCE);self.records=importer.convert(self.note,importer.REFERENCE,uncertainty='Supplied technical comparison; manufacturer/independent/derived evidence classifications retain their reported scope. Pending independent database review.')
 def test_reproducible_cited_exact_claims(self):
  self.assertEqual(specs.load(importer.IMPORT),self.records)
  for p,s in importer.artifacts(Path('.')).items():self.assertEqual(Path(p).read_text(),s)
  catalog.validate_user_evidence(Path('.'),self.records)
  self.assertEqual(len(self.note['models']),33)
 def test_all_models_are_independent_search_records(self):
  rows={r['id']:r for r in specs.load('data/search-index.json')['records']}
  for id in self.note['models']:self.assertEqual(rows[id]['category'],'watch',id)
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_moyc_mass_is_never_asserted_as_factory_weight(self):
  row=next(r for r in self.records if r['id']=='GW-M5610MOYC-1ER')
  self.assertNotIn('weight_g',row['specs']);self.assertNotIn('dimensions_mm',row['specs'])
  evidence=row['specs']['module_comparison_evidence']['value']
  self.assertEqual(evidence['reported_evidence_class'],'D');self.assertEqual(evidence['estimated_weight_g'],52)
  self.assertEqual(evidence['base_model'],'GW-M5610U-1ER')
 def test_groups_keep_distinct_weights_and_module_profiles_have_no_case_specs(self):
  data=specs.load('data/catalog.json');w=lambda id:data['models'][id]['specs']['weight_g']['value']
  self.assertEqual(w('GW-M5610BC-1'),101.3);self.assertEqual(w('GW-M5610UBC-1'),102)
  self.assertEqual(w('GW-S5600-1'),47);self.assertEqual(w('GW-5035A-1'),81)
  for row in self.records:
   if row['kind']=='module':self.assertFalse(set(row['specs'])&{'dimensions_mm','weight_g','water_resistance_m','glass'})
  self.assertEqual(data['models']['GW-M5610-1']['specs']['weight_g']['status'],'verified')
 def test_classes_sources_and_legacy_sku_cautions_survive(self):
  self.assertEqual(len(self.note['source_documents']['module_comparison']['source_urls']),22)
  self.assertEqual(len(self.note['archive_lookup']),22)
  self.assertIn('Legacy GW-M5610',self.note['cautions'][0])
  self.assertEqual({r['specs']['module_comparison_evidence']['value']['reported_evidence_class'] for r in self.records if r['kind']=='model'},{'C','I','D'})
