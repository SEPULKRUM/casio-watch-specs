import unittest,json
from pathlib import Path
import casio_links
ROOT=Path(__file__).resolve().parents[1]
class OfficialCasioLinksTests(unittest.TestCase):
 def test_registry_is_reproducible_and_every_selected_destination_has_live_identity_evidence(self):
  for name,s in casio_links.artifacts(ROOT).items():self.assertEqual((ROOT/name).read_text(),s)
  n=json.loads((ROOT/casio_links.REFERENCE).read_text());self.assertEqual(len(n['selected']),n['discovery']['selected_groups']);self.assertEqual(len(n['checks']),n['discovery']['checked_requests'])
  aliases=json.loads((ROOT/'research/model-identity-rules-2026-11-17.json').read_text())['aliases']
  accepted_products={casio_links.reference_key(r['page_model'],aliases) for r in n['checks'] if r.get('accepted') and r['kind']=='product'}
  for key,row in n['selected'].items():
   self.assertEqual(casio_links.reference_key(row['page_model'],aliases),key)
   if row['kind']=='support':self.assertNotIn(key,accepted_products)
   self.assertTrue(row['accepted']);self.assertEqual(row['status'],200);self.assertTrue(row['model_identity_confirmed']);self.assertTrue(casio_links.official_url(row['final_url']));self.assertEqual(len(row['sha256']),64)
   if row['kind']=='product':self.assertTrue(row['has_specifications'])
 def test_host_validation_rejects_spoofed_domains_and_credentials(self):
  for u in ['http://www.casio.com/','https://casio.com.evil.example/','https://a:b@www.casio.com/','https://www.casio.com:444/']:self.assertFalse(casio_links.official_url(u))
  for u in ['https://www.casio.com/','https://support.casio.jp/','https://www.casio.com.cn/']:self.assertTrue(casio_links.official_url(u))
