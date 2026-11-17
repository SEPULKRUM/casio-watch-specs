import copy,json,unittest
from pathlib import Path
import specs,catalog,supplied_catalog_import as importer

class SuppliedCatalogTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.batch=specs.load(importer.REFERENCE);cls.records=importer.convert(cls.batch)
 def test_every_image_and_exact_identifier_is_retained(self):
  self.assertEqual(len(self.batch['pages']),24)
  self.assertEqual({x['file'] for x in self.batch['pages']},{f'IMG_{i}.JPG' for i in range(3230,3254)})
  watches={x['model_id'] for x in self.batch['models']};clocks={x['model_id'] for x in self.batch['clocks']}
  self.assertEqual(len(watches),78);self.assertEqual(len(clocks),5);self.assertEqual(len(self.records),112)
  self.assertEqual({x['id'] for x in self.records if x['kind']=='model'},watches|clocks)
  self.assertEqual(len(self.batch['models']),82) # packaging repeats, not invented variants
 def test_physical_claims_never_enter_modules_or_unrelated_variants(self):
  for record in self.records:
   specs.validate(record)
   if record['kind']=='module':self.assertFalse(set(record['specs'])&{'dimensions_mm','weight_g','case_material','band_material','water_resistance_m','glass'})
  self.assertNotIn('DW-5000C-1A',{r['id'] for r in self.records})
  self.assertTrue(all('catalog_1983_evidence' in r['specs'] for r in self.records))
 def test_reproducible_generated_import_and_no_citation_forgery(self):
  path=next(Path('imports').glob('*supplied-catalog-1983*.json'))
  self.assertEqual(self.records,specs.load(path));self.assertEqual(Path('web/catalog-1983-data.mjs').read_text(),importer.web_artifact(self.batch));catalog.validate_user_evidence(Path('.'),self.records)
  forged=copy.deepcopy(self.records);forged[0]['specs']['catalog_1983_evidence']['value']={'invented':True}
  with self.assertRaisesRegex(ValueError,'exact specification'):catalog.validate_user_evidence(Path('.'),forged)
 def test_every_source_watch_and_clock_remains_searchable_in_correct_category(self):
  data=specs.load('data/search-index.json');byid={r['id']:r for r in data['records']}
  for r in self.batch['models']:self.assertIn(byid[r['model_id']]['category'],['watch','family'])
  for r in self.batch['clocks']:self.assertEqual(byid[r['model_id']]['category'],'clock')
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_historical_battery_types_and_source_discrepancies_preserved(self):
  modules={r['module_id']:r for r in self.batch['modules']}
  self.assertIn('BR-2320',modules['240']['battery_cell']);self.assertIn('726R',modules['189']['battery_cell']);self.assertIn('926R',modules['243']['battery_cell'])
  self.assertEqual(modules['155']['accuracy_seconds_per_month'],30)
  self.assertEqual(modules['244']['accuracy_seconds_per_month'],30)
  self.assertIn('13°F',modules['215']['thermometer']);self.assertGreaterEqual(len(self.batch['discrepancies']),7)
