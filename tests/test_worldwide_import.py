import json, unittest
from pathlib import Path
from worldwide_import import artifacts, REFERENCE, IMPORT
ROOT=Path(__file__).resolve().parents[1]
class WorldwideImportTests(unittest.TestCase):
 def test_original_registers_and_historical_supplement_reconcile(self):
  n=json.loads((ROOT/REFERENCE).read_text());self.assertEqual(len(n['source_documents']),13);self.assertEqual(len(n['identifier_occurrences']),937)
  records=[r for r in json.loads(artifacts(ROOT)[IMPORT]) if r['kind']=='model'];self.assertEqual(len(records),930);self.assertEqual(set(n['identifier_occurrences']),{r['id'] for r in records});self.assertEqual(sum(len(r['specs']['worldwide_evidence']['value']['observations']) for r in records),937)
 def test_exact_eligible_identifiers_are_indexed_and_openable(self):
  n=json.loads((ROOT/REFERENCE).read_text());idx=json.loads((ROOT/'data/search-index.json').read_text());rows={r['id']:r for r in idx['records']};cat=json.loads((ROOT/'data/catalog.json').read_text())
  for id in n['models']:
   self.assertIn(id,rows);self.assertEqual(rows[id]['category'],'watch');self.assertIn(id,cat['models']);self.assertIn('worldwide_evidence',cat['models'][id]['specs'])
  for id,category in n['category_resolutions'].items():self.assertEqual(rows[id]['category'],category)
 def test_reproducible_artifacts_and_no_verification_promotion(self):
  for name,s in artifacts(ROOT).items():self.assertEqual((ROOT/name).read_text(),s)
  for r in json.loads(artifacts(ROOT)[IMPORT]):
   for f in r['specs'].values():self.assertIn('pending independent',f['uncertainty']);self.assertEqual(f['sources'][0]['kind'],'user_provided')
 def test_conflicting_gbd200_measurement_is_preserved_as_evidence(self):
  r=next(r for r in json.loads(artifacts(ROOT)[IMPORT]) if r['id']=='GBD-200-1');self.assertNotIn('dimensions_mm',r['specs']);self.assertIn('49.4',json.dumps(r['specs']['worldwide_evidence']))
