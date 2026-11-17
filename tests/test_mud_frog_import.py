import unittest,json
from pathlib import Path
import mud_frog_import as imp
import specs,catalog
class MudFrogImportTest(unittest.TestCase):
 def test_reproducible_source_binding(self):
  root=Path(__file__).resolve().parents[1]
  for name,content in imp.artifacts(root).items():self.assertEqual((root/name).read_text(),content)
  catalog.validate_user_evidence(root,specs.load(root/imp.IMPORT))
 def test_all_exact_references_and_classifications(self):
  n=specs.load(imp.REFERENCE);idx=specs.load('data/search-index.json');rows={r['id']:r for r in idx['records']}
  for id in n['models']:self.assertEqual(rows[id]['category'],'watch',id)
  for id in n['package_identifiers']:self.assertEqual(rows[id]['category'],'package',id)
  for id in n['uncertain_identifiers']:self.assertEqual(rows[id]['category'],'uncertain',id)
  self.assertEqual(len(n['release_records']),45);self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_no_shared_weight_or_conflicting_length_promotion(self):
  c=specs.load('data/catalog.json');m=c['models']
  for id in ['GWF-T1000BS-1JR','GWF-T1030A-1JR','GWF-T1030E-9JR','GWF-1000G-1JR','GWF-D1000NV-2JF']:self.assertNotIn('weight_g',m[id]['specs'])
  self.assertNotIn('dimensions_mm',m['GWG-1000-1A']['specs'])
  self.assertEqual(m['GWF-D1000BC-1JF']['specs']['weight_g']['value'],181)
  self.assertEqual(m['GWG-B1000-1A3']['specs']['weight_g']['value'],114)
  for r in specs.load(imp.IMPORT):
   if r['kind']=='module':self.assertEqual(set(r['specs']),{'series_pdf_evidence'})
