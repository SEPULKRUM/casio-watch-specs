import unittest
from pathlib import Path
import specs,catalog,dw_heritage_import as imp
class DwHeritageTests(unittest.TestCase):
 def test_reproducible_source_bindings_and_complete_scope(self):
  root=Path(__file__).resolve().parents[1];n=specs.load(root/imp.REFERENCE)
  for p,s in imp.artifacts(root).items():self.assertEqual((root/p).read_text(),s)
  catalog.validate_user_evidence(root,specs.load(root/imp.IMPORT))
  self.assertEqual(len(n['canonical_records']),22);self.assertEqual(sum(r['kind']=='watch' for r in n['canonical_records']),20)
  self.assertEqual(len(n['inventory_rows']),28)
 def test_exact_identifiers_and_collector_packages_remain_separate(self):
  n=specs.load(imp.REFERENCE);idx={r['id']:r for r in specs.load('data/search-index.json')['records']}
  for id,category in n['category_resolutions'].items():self.assertEqual(idx[id]['category'],category,id)
  self.assertNotIn('DW-5000CHONDAF1',idx);self.assertNotIn('DW-5200CHONDA',idx)
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_specimen_measurements_are_never_factory_or_variant_scalars(self):
  c=specs.load('data/catalog.json');m=c['models']
  for id,weight in [('DW-5000C',64.65),('DW-5200C',64.70)]:
   obs=m[id]['specs']['series_pdf_evidence']['value']['specimen_observation'];self.assertEqual(obs['complete_weight_g'],weight);self.assertEqual(obs['dimensions_mm']['width'],41.3)
   self.assertNotIn('weight_g',m[id]['specs']);self.assertNotIn('dimensions_mm',m[id]['specs'])
  for id in ['DW-5000C-1A','DW-5000C-1B','DW-5200C-1','DW-5200C-9','DW-5400C-1','DW-5400C-9','DW-5500C-1']:self.assertNotIn('weight_g',m[id]['specs']);self.assertNotIn('dimensions_mm',m[id]['specs'])
  self.assertEqual(m['DW-5000R-1A']['specs']['weight_g']['value'],76);self.assertEqual(m['DW-5040PG-1']['specs']['dimensions_mm']['value']['thickness'],13.8)
 def test_rejected_gold_crystal_and_leading_zero_stock_code_preserved(self):
  c=specs.load('data/catalog.json');b=c['models']['DW-5000C-1B']['specs']['series_pdf_evidence']['value'];self.assertEqual(b['gold_accent_crystal']['rejected_part_number'],'79000433');self.assertNotIn('79000433',{r['service_code'] for r in b['recorded_service_parts']})
  base=c['models']['DW-5000C']['specs']['series_pdf_evidence']['value'];self.assertEqual(base['replacement_band_records'][0]['service_code'],'09521081')
