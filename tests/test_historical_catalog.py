import copy
import csv
import io
import json
import unittest
from pathlib import Path
import catalog
import reference_import
from historical_catalog_import import parse_text

ROOT = Path(__file__).resolve().parents[1]

class HistoricalCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note = json.loads((ROOT / 'research/historical-catalog-1980-1989.json').read_text())
        cls.data = json.loads((ROOT / 'data/catalog.json').read_text())

    def test_all_readable_rows_and_original_page_locators_survive(self):
        rows = self.note['models']
        self.assertEqual(len(rows), 263)
        for year, count in [(1980,26),(1982,43),(1985,166),(1989,28)]:
            self.assertEqual(sum(r['catalog_year']==year for r in rows),count)
        for row in rows:
            model=self.data['models'][row['id']]
            self.assertEqual(catalog.field_value(model,'catalog_description'),row['description'])
            if row['material_finish'] is not None:
                self.assertEqual(catalog.field_value(model,'catalog_material_finish'),row['material_finish'])
            elif catalog.field_value(model,'catalog_material_finish') is not None:
                # A blank older source may gain later exact-reference evidence.
                self.assertIn('catalog_1983_evidence',model['specs'])
            self.assertEqual(catalog.field_value(model,'module_id'),row['module'])
            for fact in model['specs'].values():
                self.assertEqual(fact['status'],'pending_review')
                if not any(source.get('reference') == 'research/historical-catalog-1980-1989.json' for source in fact['sources']):
                    continue
                self.assertIn(f"catalog p. {row['catalog_page']}",fact['sources'][0]['locator'])
                self.assertIn(f"PDF p. {row['extraction_pdf_page']}",fact['sources'][0]['locator'])

    def test_unknowns_and_review_labels_do_not_become_asserted_modules(self):
        self.assertEqual(len(self.note['uncertain_readings']),56)
        self.assertEqual(sum(r['module'] is None for r in self.note['models']),11)
        self.assertIsNone(catalog.field_value(self.data['models']['W150C-1'],'module_id'))
        self.assertEqual(catalog.field_value(self.data['models']['56CS-528-2'],'module_id'),'56')
        self.assertIn('56',self.data['modules'])
        self.assertNotIn('case_material',self.data['models']['C-801-1']['specs'])
        self.assertNotIn('release_date',self.data['models']['GM-40']['specs'])
        self.assertEqual(catalog.field_value(self.data['models']['PQ-5'],'series'),'Casio Historical Clocks')

    def test_module_notes_do_not_spread_between_adjacent_columns(self):
        self.assertEqual(len(self.note['module_notes']),14)
        self.assertNotIn('accuracy_seconds_per_month',self.data['modules']['317']['specs'])
        notes=catalog.field_value(self.data['modules']['317'],'catalog_features')
        self.assertIn('not attributed',notes[0]['note'])
        self.assertNotIn('catalog_features',self.data['modules']['56']['specs'])
        self.assertTrue(catalog.field_value(self.data['modules']['79'],'catalog_features'))

    def test_csv_and_supplement_keep_historical_evidence(self):
        rows=list(csv.DictReader(io.StringIO(catalog.export_csv(self.data))))
        row=next(r for r in rows if r['model']=='GM-40')
        self.assertIn('Pyramid',row['catalog_description'])
        self.assertEqual(row['catalog_year'],'1982')
        self.assertIn('historical-catalog',row['source_references'])
        lib=json.loads((ROOT/'data/model-references.json').read_text())
        supplement=json.loads((ROOT/'research/reference-supplements/historical-catalog-1980-1989-2026-11-15.json').read_text())
        before=copy.deepcopy(lib);reference_import.add_supplement(lib,supplement);self.assertEqual(before,lib)
        self.assertTrue(any(o.get('historical_context') for o in lib['models']['GM-40']['observations']))

    def test_parser_keeps_wrapped_details_and_two_different_page_numbers(self):
        header=f"   {'Model':<25}{'Module':<14}{'Source section / explicit details':<65}{'Material / finish':<25}Page"
        row=f"   {'TEST-1':<25}{'56':<14}{'Calculator':<65}{'Chrome plated':<25}7"
        continuation=f"   {'':<25}{'':<14}{'Eight digits':<65}"
        text='Cover\f1980 CATALOG\n'+header+'\n'+row+'\n'+continuation
        parsed=parse_text(text)['models'][0]
        self.assertEqual(parsed['description'],'Calculator Eight digits')
        self.assertEqual(parsed['extraction_pdf_page'],2)
        self.assertEqual(parsed['catalog_page'],7)
