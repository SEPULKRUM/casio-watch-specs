import copy
import csv
import io
import json
import unittest
from pathlib import Path
import catalog
import reference_import
from protrek_catalog_import import parse_text

ROOT=Path(__file__).resolve().parents[1]

class ProTrekCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note=json.loads((ROOT/'research/protrek-combined-specifications-2026-11-15.json').read_text())
        cls.data=json.loads((ROOT/'data/catalog.json').read_text())
        cls.batch=json.loads((ROOT/'imports/zzzzzzzzzzzzzzzzzzzz-protrek-combined-specifications-2026-11-15.json').read_text())

    def test_every_model_and_family_detail_keeps_its_page_and_original_source(self):
        self.assertEqual(len(self.note['models']),79)
        self.assertEqual(len({r['cells'][0] for r in self.note['models']}),79)
        self.assertEqual(len(self.note['detailed_families']),16)
        self.assertEqual(len(self.note['family_comparisons']),16)
        self.assertEqual(len(self.note['spf_source_comparison']),11)
        for row in self.note['models']:
            model=self.data['models'][row['cells'][0]]
            claim=catalog.field_value(model,'protrek_source_reference')
            self.assertEqual(claim['model']['Model'],row['cells'][0])
            self.assertEqual(claim['model']['original_source'],row['cells'][4])
            source=model['specs']['protrek_source_reference']['sources'][0]
            self.assertIn(f"PDF p. {row['extraction_pdf_page']}",source['locator'])
            self.assertIn(row['cells'][4],source['locator'])
            self.assertEqual(source['kind'],'user_provided')
            self.assertEqual(model['specs']['protrek_source_reference']['status'],'pending_review')

    def test_regional_references_stay_separate_and_no_module_is_inferred(self):
        for a,b in [('PRW-7000-1A','PRW-7000-1AJF'),('PRW-6100Y-1','PRW-6100Y-1JF'),('PRG-600YB-3','PRG-600YB-3JF')]:
            self.assertIn(a,self.data['models']);self.assertIn(b,self.data['models'])
            self.assertIsNone(catalog.field_value(self.data['models'][a],'supplied_aliases'))
        for record in self.batch:
            self.assertEqual(record['kind'],'model')
            self.assertNotIn('module_id',record['specs'])
            self.assertNotIn('module_candidates',record['specs'])
            self.assertNotIn('release_date',record['specs'])
        self.assertEqual(catalog.field_value(self.data['models']['PRG-270-1'],'module_id'),'3415')
        self.assertEqual(catalog.field_value(self.data['models']['PRJ-B001-1'],'module_id'),'5732')

    def test_listing_only_and_family_only_sizes_do_not_become_variant_hardware(self):
        listing=[r for r in self.note['models'] if r['cells'][4].startswith('CASIO26')]
        self.assertEqual(len(listing),11)
        for row in listing:
            record=next(r for r in self.batch if r['id']==row['cells'][0])
            self.assertNotIn('dimensions_mm',record['specs'])
            self.assertNotIn('water_resistance_m',record['specs'])
        for record in self.batch:self.assertNotIn('dimensions_mm',record['specs'])
        measurements=catalog.field_value(self.data['models']['PRW-3500T-7JF'],'reported_measurements')
        self.assertEqual(measurements[0]['dimensions_mm']['thickness'],14.5)
        self.assertEqual(measurements[1]['thickness_mm'],14.8)
        self.assertIsNone(catalog.field_value(self.data['models']['PRW-3000-1A'],'dimensions_mm'))

    def test_spf_graphic_claims_remain_unverified_and_both_depth_ranges_survive(self):
        for id in ['SPF-100-1V','SPF-100S-1V','SPF-100J-1JF','SPF-100SJ-1JF']:
            model=self.data['models'][id]
            self.assertNotIn('module_id',model['specs']);self.assertNotIn('module_candidates',model['specs'])
            self.assertNotIn('dimensions_mm',model['specs']);self.assertNotIn('weight_g',model['specs'])
            claims=catalog.field_value(model,'reported_measurements')
            self.assertEqual(claims[0]['range_m'],'0.0–80.0')
            self.assertEqual(claims[1]['range_m'],'0–60.0')
            self.assertIn('unverified',claims[2]['status'])
        self.assertNotIn('2172',self.data['modules']);self.assertNotIn('2173',self.data['modules'])
        self.assertIn('2173?',catalog.field_value(self.data['models']['SPF-100-1V'],'reported_module_claim'))

    def test_source_supplement_and_csv_preserve_family_scope(self):
        lib=json.loads((ROOT/'data/model-references.json').read_text());before=copy.deepcopy(lib)
        supp=json.loads((ROOT/'research/reference-supplements/protrek-combined-specifications-2026-11-15.json').read_text())
        reference_import.add_supplement(lib,supp);self.assertEqual(before,lib)
        self.assertTrue(any(o.get('reading_scope')=='family_label_only_not_exact_variant' for o in lib['models']['PRW-7000']['observations']))
        rows=list(csv.DictReader(io.StringIO(catalog.export_csv(self.data))))
        model=next(r for r in rows if r['model']=='SPF-100-1V')
        self.assertIn('80.0',model['protrek_source_reference']);self.assertIn('60.0',model['reported_measurements'])
        self.assertIn('SPF-IMAGE',model['protrek_source_reference'])

    def test_parser_preserves_model_row_wrapping_and_qualified_suffix(self):
        labels=['Model','Module','Water / reference size','Key functions / model note','Source page(s)']
        widths=[28,16,34,48]
        header='   '+''.join(f'{v:<{w}}' for v,w in zip(labels,widths))+labels[-1]
        values=['PRW-7000-1AJF','Not stated','200 m; family size','Triple Sensor','JP17 p9']
        row='   '+''.join(f'{v:<{w}}' for v,w in zip(values,widths))+values[-1]
        continuation='   '+''.join(f'{v:<{w}}' for v,w in zip(['','','14.5 mm','Band note'],widths))
        parsed=parse_text('Cover\fPRW-7000 Multi-Field | 1 models\n'+header+'\n'+row+'\n'+continuation)
        self.assertEqual(parsed['models'][0]['cells'][0],'PRW-7000-1AJF')
        self.assertEqual(parsed['models'][0]['cells'][2],'200 m; family size 14.5 mm')
        self.assertEqual(parsed['models'][0]['extraction_pdf_page'],2)
