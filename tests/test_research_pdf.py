import copy,json,unittest
from pathlib import Path
import catalog,specs,research_pdf_import as importer
class ResearchPdfTests(unittest.TestCase):
 def setUp(self):
  self.notes=specs.load(importer.REFERENCE);self.records=importer.convert(self.notes)
 def test_reproducible_and_exact_claim_citations(self):
  self.assertEqual(self.records,specs.load(importer.IMPORT))
  for name,content in importer.artifacts(Path('.')).items():self.assertEqual(Path(name).read_text(),content)
  catalog.validate_user_evidence(Path('.'),self.records)
  forged=copy.deepcopy(self.records);forged[0]['specs']['module_id']['value']='5161'
  with self.assertRaises(ValueError):catalog.validate_user_evidence(Path('.'),forged)
 def test_every_exact_watch_is_indexed(self):
  index=specs.load('data/search-index.json');byid={r['id']:r for r in index['records']}
  self.assertEqual(len(self.notes['models']),19)
  for id in self.notes['models']:self.assertEqual(byid[id]['category'],'watch',id)
  self.assertEqual(specs.load('data/reconciliation-report.json')['missing_model_count'],0)
 def test_no_inherited_physical_specs(self):
  physical={'dimensions_mm','weight_g','case_material','band_material','glass','water_resistance_m'}
  for r in self.records:
   if r['kind']=='module':self.assertFalse(set(r['specs'])&physical)
   if r['id'] in ['GW-M5610UBC-1JF','GW-M5610U-1JF','LCW-M200DJ-7AJF','DW-5000C-1B']:self.assertNotIn('dimensions_mm',r['specs'])
 def test_sources_estimates_conflicts_and_parts_scope_preserved(self):
  data=specs.load('data/catalog.json');n=data['models']['LCW-M200DJ-2AJF']['specs']['research_pdf_evidence']['value']
  self.assertEqual(n['service_parts']['source_model'],'LCW-M200DJ-7A');self.assertEqual(len(n['service_parts']['parts']),7)
  self.assertEqual(n['production_evidence']['factory_production_end'],'Unknown')
  self.assertIn('not a validated',n['production_evidence']['serial_scope'])
  self.assertEqual(data['modules']['240']['specs']['battery_cell']['value'],'BR-2320 × 1 (lithium)')
  self.assertTrue(self.notes['retained_existing_scalars'])
  self.assertEqual(len(self.notes['source_documents']),3)
  self.assertTrue(all(len(d['sha256'])==64 for d in self.notes['source_documents'].values()))
 def test_archived_exact_model_corroboration_is_scoped(self):
  row=next(r for r in self.records if r['id']=='GW-M5610U-2JF');proof=row['specs']['research_pdf_evidence']['value']['archive_corroboration']
  self.assertEqual(proof['archive_timestamp'],'20211019223435');self.assertNotIn('release_date',proof['checked_fields'])
