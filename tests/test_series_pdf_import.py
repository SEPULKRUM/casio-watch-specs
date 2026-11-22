import unittest
from pathlib import Path
import series_pdf_import as imp
import catalog,specs
class SeriesPDFImportTest(unittest.TestCase):
 def test_reproducible_and_source_bound(self):
  root=Path(__file__).resolve().parents[1]
  for name,content in imp.artifacts(root).items():self.assertEqual((root/name).read_text(),content)
  records=specs.load(root/imp.IMPORT);catalog.validate_user_evidence(root,records)
  self.assertEqual(len([r for r in records if r['kind']=='model']),23)
  self.assertEqual({r['id'] for r in records if r['kind']=='module'},{'3514','5454','3519'})
 def test_no_module_case_spec_leak(self):
  root=Path(__file__).resolve().parents[1]
  for r in specs.load(root/imp.IMPORT):
   if r['kind']=='module':self.assertFalse({'dimensions_mm','weight_g','case_material','band_material','glass'} & set(r['specs']))

 def test_csv_evidence_columns_match_headers(self):
  import csv,io
  root=Path(__file__).resolve().parents[1];data=specs.load(root/'data/catalog.json')
  row=next(r for r in csv.DictReader(io.StringIO(catalog.export_csv(data))) if r['model']=='PRW-69YT-7JF')
  self.assertIn('117',row['series_pdf_evidence']);self.assertEqual(row['special_variant_evidence'],'')
