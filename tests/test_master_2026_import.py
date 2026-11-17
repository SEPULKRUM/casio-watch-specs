import unittest,json
from pathlib import Path
import catalog,specs,master_2026_import as importer
ROOT=Path(__file__).resolve().parents[1]
class Master2026CorrectionsTests(unittest.TestCase):
 def test_complete_current_inventory_and_history(self):
  n=specs.load(ROOT/importer.REFERENCE);records,data=importer.payload(ROOT);self.assertEqual(len(n['models']),203);self.assertEqual(len(n['dated_field_changes']),78);self.assertEqual(len(n['merged_record_archive']),2);self.assertEqual(sum('official_model_specifications' in r for r in n['models']),36);self.assertEqual({r['model'] for r in n['models']}|set(data['regional_identifiers']),{r['id'] for r in records if r['kind']=='model'})
 def test_reproducible_and_bound_to_exact_supplied_evidence(self):
  for name,s in importer.artifacts(ROOT).items():self.assertEqual((ROOT/name).read_text(),s)
  records,_=importer.payload(ROOT);catalog.validate_user_evidence(ROOT,records)
 def test_corrected_physical_fields_are_active_and_modules_stay_separate(self):
  c=specs.load(ROOT/'data/catalog.json');m=c['models']['AQ-240EAC-3A'];self.assertEqual(m['specs']['weight_g']['value'],51);self.assertEqual(m['specs']['module_id']['value'],'5154');self.assertNotIn('weight_g',c['modules']['5154']['specs']);self.assertEqual(c['models']['CMK-100TD-1A']['specs']['weight_g']['value'],98);self.assertEqual(c['models']['CMK-100TC-1A']['specs']['weight_g']['value'],55)
 def test_no_loss_of_checked_facts_or_identity_and_alias_provenance(self):
  c=specs.load(ROOT/'data/catalog.json');self.assertEqual(c['models']['GW-M5610U-1']['specs']['weight_g']['status'],'verified');i=specs.load(ROOT/'data/search-index.json');ids={r['id'] for r in i['records']};self.assertTrue({'GMA-S110XG-4','GMA-S110XG-4A'}<=ids);self.assertEqual(specs.load(ROOT/'research/model-identity-rules-2026-11-17.json')['aliases']['GMA-S110XG-4'],'GMA-S110XG-4A')
