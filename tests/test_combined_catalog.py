import copy
import csv
import io
import json
import subprocess
import unittest
from pathlib import Path
import catalog
import reference_import
from combined_catalog_import import parse_text

ROOT=Path(__file__).resolve().parents[1]

class CombinedCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.note=json.loads((ROOT/'research/combined-model-specifications-2026-11-15.json').read_text())
        cls.data=json.loads((ROOT/'data/catalog.json').read_text())

    def test_every_selected_table_and_model_remains_source_scoped(self):
        self.assertEqual(len(self.note['tables']),29)
        self.assertEqual(len(self.note['catalog_models']),74)
        self.assertEqual(len(self.note['module_profiles']),12)
        self.assertEqual(len(self.note['source_register']),10)
        self.assertEqual(len(self.note['reported_references']),9)
        for model in self.note['catalog_models']:
            row=self.data['models'][model]
            self.assertIn('supplied_model_details',row['specs'])
            for key in ['supplied_model_details','supplied_family_specifications']:
                if key in row['specs']:
                    fact=row['specs'][key]
                    self.assertEqual(fact['status'],'pending_review')
                    self.assertEqual(fact['sources'][0]['kind'],'user_provided')
                    self.assertIn('Consolidated extraction PDF',fact['sources'][0]['locator'])

    def test_conflicts_are_preserved_without_selecting_measurement_or_cell(self):
        awg=self.data['models']['AWG-M520UA-1EJR']['specs']
        self.assertNotIn('dimensions_mm',awg)
        self.assertEqual([r['dimensions_mm']['thickness'] for r in awg['reported_measurements']['value']],[13.1,15.3])
        cell=self.data['modules']['5770']['specs']['battery_cell']['value']
        self.assertEqual(cell['product_pages_cited_by_compilation'],'SR927SW')
        self.assertEqual(cell['operation_guide_cited_by_compilation'],'SR927W')

    def test_family_and_regional_labels_are_not_extra_watch_records(self):
        for id in ['OCW-T5000','OCW-T150','OCW-T200','OCW-S100','OCW-70','OCW-S340','GWR-B3000-1AJF','AWG-M520UA']:
            self.assertNotIn(id,self.data['models'])
        self.assertEqual(catalog.field_value(self.data['models']['GWR-B3000-1A'],'supplied_aliases'),['GWR-B3000-1AJF'])
        self.assertNotIn('dimensions_mm',self.data['models']['DW-H5600-1']['specs'])
        self.assertEqual(catalog.field_value(self.data['models']['DW-H5600-1'],'module_id'),'3516')
        self.assertEqual(catalog.field_value(self.data['models']['GBX-H5600-1'],'module_id'),'3586')
        self.assertNotIn('module_id',self.data['models']['OCW-S400-2AJF']['specs'])

    def test_module_chronology_and_unverified_designations_remain_distinct(self):
        self.assertEqual(catalog.field_value(self.data['models']['DW-290-1V'],'module_candidates'),['1219','1189','3231'])
        self.assertEqual(catalog.field_value(self.data['models']['DW-290G-9V'],'module_candidates'),['1219','1189'])
        self.assertNotIn('dimensions_mm',self.data['models']['DW-290-1V']['specs'])
        self.assertNotIn('module_id',self.data['models']['DW-290B-2V']['specs'])
        for id in ['DW-290G-1V','DW-290T','DW-290MV-1VUR','OCW-T2600TA-8AJF']:
            self.assertNotIn(id,self.data['models'])
        self.assertNotIn('modern_3231_functions',catalog.field_value(self.data['modules']['1219'],'supplied_module_specifications'))
        self.assertIn('modern_3231_functions',catalog.field_value(self.data['modules']['3231'],'supplied_module_specifications'))
        self.assertEqual(catalog.field_value(self.data['modules']['5347'],'alarm_count'),0)
        self.assertEqual(len(catalog.field_value(self.data['modules']['3586'],'battery_runtime')),7)

    def test_supplement_is_idempotent_and_exposes_scope_flags(self):
        lib=json.loads((ROOT/'data/model-references.json').read_text())
        before=copy.deepcopy(lib)
        supp=json.loads((ROOT/'research/reference-supplements/combined-model-specifications-2026-11-15.json').read_text())
        reference_import.add_supplement(lib,supp)
        self.assertEqual(before,lib)
        for id,scope in [('OCW-T5000','family_label_only_not_exact_variant'),('DW-290T','reported_identifier_verification_incomplete'),('GWR-B3000-1AJF','supplied_regional_or_short_alias_not_additional_variant')]:
            self.assertTrue(any(o.get('reading_scope')==scope for o in lib['models'][id]['observations']))
        csvrows=list(csv.DictReader(io.StringIO(catalog.export_csv(self.data))))
        awg=next(r for r in csvrows if r['model']=='AWG-M520UA-1EJR')
        self.assertIn('13.1',awg['reported_measurements']);self.assertIn('15.3',awg['reported_measurements'])

    def test_parser_preserves_wrapped_values_and_pdf_page(self):
        header=' Specification                              Value'
        row=' Water resistance                           200 m / 20 bar'
        continuation='                                            stated for this family'
        tables=parse_text('Cover\f'+header+'\n'+row+'\n'+continuation)
        self.assertEqual(tables[0]['page'],2)
        self.assertEqual(tables[0]['rows'][0],['Water resistance','200 m / 20 bar stated for this family'])
