import unittest
from pathlib import Path
import specs,catalog,special_variant_import as importer
class SpecialVariantTests(unittest.TestCase):
 def setUp(self):self.n=specs.load(importer.REFERENCE);self.records=importer.convert(self.n,importer.REFERENCE,uncertainty=importer.UNCERTAINTY)
 def test_exact_citations_and_reproducible_artifacts(self):
  self.assertEqual(specs.load(importer.IMPORT),self.records)
  for p,s in importer.artifacts(Path('.')).items():self.assertEqual(Path(p).read_text(),s)
  catalog.validate_user_evidence(Path('.'),self.records)
  self.assertEqual(len(self.n['reference_records']),7);self.assertEqual(len(self.n['archive_lookup']),13)
 def test_packages_and_watch_variants_have_distinct_counts(self):
  index=specs.load('data/search-index.json');rows={r['id']:r for r in index['records']}
  self.assertEqual(len(self.n['models']),2);self.assertEqual(len(self.n['package_identifiers']),5)
  for id in self.n['models']:self.assertEqual(rows[id]['category'],'watch')
  for id in self.n['package_identifiers']:self.assertEqual(rows[id]['category'],'package')
  self.assertEqual(index['counts']['package'],5);self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_spelling_corrections_and_original_labels_are_preserved(self):
  rows={r['id']:r for r in specs.load('data/search-index.json')['records']}
  for id in ['GMW-B5000GDLTD-1','GMW-B5000TCM-1LT','GMW-B5000PS-1 Rock for People']:self.assertEqual(rows[id]['category'],'uncertain')
  for id in ['GMW-B5000GDLTD-1ER','GMWB5000TCM-1LT','GMW-B5000PS-1ERFP']:self.assertIn(id,rows)
 def test_no_package_mass_or_inherited_festival_weight(self):
  c=specs.load('data/catalog.json')
  for id in self.n['package_identifiers']:self.assertNotIn('weight_g',c['models'][id]['specs'])
  self.assertNotIn('weight_g',c['models']['GMW-B5000PS-1ERFP']['specs'])
  self.assertEqual(c['models']['GMW-B5000SB-1A2']['specs']['weight_g']['value'],98)
  self.assertEqual(c['models']['GMW-B5000SB-1A2']['specs']['band_material']['value'],'Black resin / soft urethane')
  self.assertEqual(c['models']['GMW-B5000SB-1A2']['specs']['glass']['value'],'Mineral glass')
  self.assertNotIn('module_id',c['models']['GMW-B5000SB-1A2']['specs'])
 def test_old_verified_specs_and_original_source_intake_are_retained(self):
  c=specs.load('data/catalog.json');self.assertEqual(c['models']['GW-M5610-1']['specs']['weight_g']['status'],'verified')
  self.assertEqual(c['models']['GMW-B5000SB-1A2']['specs']['reference_scope']['value'],'unconfirmed_identifier')
  self.assertEqual(c['models']['GMW-B5000SB-1A2']['specs']['special_variant_evidence']['value']['category'],'watch')
