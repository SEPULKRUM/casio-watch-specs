import copy
import csv
import io
import json
import unittest
from pathlib import Path
import catalog
import reference_import
import specs
from catalog_2011_import import parse_text, expand_pages

ROOT=Path(__file__).resolve().parents[1]

class Catalog2011Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note=json.loads((ROOT/'research/catalog-index-2011-2026-11-15.json').read_text())
        cls.data=json.loads((ROOT/'data/catalog.json').read_text())
        cls.batch=json.loads((ROOT/'imports/zzzzzzzzzzzzzzzzzzzzz-catalog-index-2011-2026-11-15.json').read_text())

    def test_every_printed_row_and_group_is_preserved_at_index_scope(self):
        self.assertEqual(len(self.note['watch_rows']),311)
        self.assertEqual(len({r['id'] for r in self.note['watch_rows']}),310)
        self.assertEqual(len(self.note['clock_rows']),109)
        self.assertEqual(len({r['printed_group'] for r in self.note['watch_rows']}),16)
        for row in self.note['watch_rows']:
            model=self.data['models'][row['id']]
            self.assertEqual(catalog.field_value(model,'reference_scope'),'2011_watch_family_index')
            claim=catalog.field_value(model,'catalog_2011_reference')
            self.assertIn(row,claim['rows'])
            self.assertNotIn('dimensions_mm',model['specs'])
            self.assertNotIn('weight_g',model['specs'])
            self.assertNotIn('release_date',model['specs'])
            for f in model['specs'].values():self.assertEqual(f['status'],'pending_review')

    def test_sdb_suffix_weight_groups_are_not_collapsed_or_expanded_into_skus(self):
        model=self.data['models']['SDB-100J']
        rows=catalog.field_value(model,'catalog_2011_reference')['rows']
        self.assertEqual([r['printed_label'] for r in rows],['SDB-100J (1AJF/1BJF)','SDB-100J (3AJF/4AJF)'])
        self.assertEqual([r['indexed_weight_g'] for r in rows],[28.2,27.5])
        self.assertIsNone(catalog.field_value(model,'indexed_weight_g'))
        self.assertEqual(len(catalog.field_value(model,'reported_measurements')),2)
        for id in ['SDB-100J-1AJF','SDB-100J-1BJF','SDB-100J-3AJF','SDB-100J-4AJF']:
            self.assertNotIn(id,self.data['models'])

    def test_clocks_have_index_pages_only_and_no_guessed_hardware(self):
        for row in self.note['clock_rows']:
            model=self.data['models'][row['id']]
            self.assertEqual(catalog.field_value(model,'reference_scope'),'2011_clock_index')
            self.assertEqual(set(model['specs']),{'series','reference_scope','catalog_2011_reference'})
            self.assertEqual(row['original_pdf_product_pages'],[p+2 for p in row['printed_product_pages']])
        self.assertEqual(expand_pages('130/131'),[130,131])
        self.assertEqual(expand_pages('7-8'),[7,8])

    def test_module_cross_references_preserve_alternatives_and_unknowns(self):
        self.assertEqual(catalog.field_value(self.data['models']['LQ-139AMV'],'module_candidates'),['705','1330'])
        self.assertEqual(catalog.field_value(self.data['models']['MW-59'],'module_candidates'),['708','2784'])
        self.assertIsNone(catalog.field_value(self.data['models']['AW-590'],'module_id'))
        self.assertEqual(catalog.field_value(self.data['models']['GW-5000'],'module_id'),'3159')
        modules=[r for r in self.batch if r['kind']=='module']
        self.assertEqual(len(modules),48)
        self.assertTrue(all(set(r['specs'])=={'catalog_2011_associations'} for r in modules))
        for row in self.note['watch_rows']:
            for module in row['modules']:self.assertIn(module,self.data['modules'])

    def test_source_pages_csv_and_supplement_are_reproducible(self):
        lib=json.loads((ROOT/'data/model-references.json').read_text());before=copy.deepcopy(lib)
        supp=json.loads((ROOT/'research/reference-supplements/catalog-index-2011-2026-11-15.json').read_text())
        reference_import.add_supplement(lib,supp);self.assertEqual(before,lib)
        self.assertTrue(any(o.get('reading_scope')=='clock_index_reference_only' for o in lib['models']['DQ-735']['observations']))
        rows=list(csv.DictReader(io.StringIO(catalog.export_csv(self.data))))
        sdb=next(r for r in rows if r['model']=='SDB-100J')
        self.assertIn('28.2',sdb['catalog_2011_reference']);self.assertIn('27.5',sdb['catalog_2011_reference'])
        self.assertEqual(sdb['weight_g'],'')
        self.assertEqual(json.loads(sdb['reference_scope']),'2011_watch_family_index')
        for row in self.note['watch_rows']:
            self.assertEqual(row['original_pdf_product_pages'],[p+2 for p in row['printed_product_pages']])

    def test_parser_and_validation_keep_index_measurements_separate(self):
        labels=['Model','Case (mm)','Mass (g)','Module','Catalog p.'];widths=[33,24,12,15]
        header='   '+''.join(f'{v:<{w}}' for v,w in zip(labels,widths))+labels[-1]
        values=['TEST-1','50.0 x 40.0 x 10.0','30','705 / 1330','7-8']
        row='   '+''.join(f'{v:<{w}}' for v,w in zip(values,widths))+values[-1]
        parsed=parse_text('Cover\fTEST | 1 indexed models\n'+header+'\n'+row)
        result=parsed['watch_rows'][0]
        self.assertEqual(result['modules'],['705','1330']);self.assertEqual(result['original_pdf_product_pages'],[9,10]);self.assertEqual(result['extraction_pdf_page'],2)
        record=copy.deepcopy(next(r for r in self.batch if r['id']=='GW-5000'))
        record['specs']['indexed_dimensions_mm']['value']['thickness']=-1
        with self.assertRaises(ValueError):specs.validate(record)
