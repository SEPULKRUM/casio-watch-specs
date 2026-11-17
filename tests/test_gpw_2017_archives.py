import copy
import json
import unittest
from pathlib import Path
import archive_import
import specs

ROOT=Path(__file__).resolve().parents[1]

class GoldTornadoArchiveTests(unittest.TestCase):
    def test_generated_batch_keeps_explicit_model_format_and_module_scope(self):
        notes=specs.load(ROOT/'research/gpw-gshock-archived-products-2026-11-16.json')
        before=specs.load(ROOT/'data/catalog.json')
        records=archive_import.convert(notes,before['models'],before['modules'])
        self.assertEqual(records,specs.load(ROOT/'imports/zzzzzzzzzzzzzzzzzzzzzzzzz-gpw-gshock-archives-2026-11-16.json'))
        model=next(r for r in records if r['id']=='GPW-2000TFB-1A')
        self.assertEqual(model['specs']['module_id']['value'],'5502')
        self.assertEqual(model['specs']['weight_g']['value'],120)
        self.assertEqual(model['specs']['dimensions_mm']['value'],{'length':66.0,'width':57.1,'thickness':18.2})
        self.assertNotIn('glass',model['specs']);self.assertNotIn('band_material',model['specs'])
        for row in records:
            specs.validate(row)
            for fact in row['specs'].values():
                for source in fact['sources']:specs.validate_archive_source(source)

    def test_format_override_cannot_merge_color_or_region_variants(self):
        notes=specs.load(ROOT/'research/gpw-gshock-archived-products-2026-11-16.json')
        bad=copy.deepcopy(notes);bad['documents'][0]['catalog_model']='GPW-2000TFB-1AJR'
        with self.assertRaises(ValueError):archive_import.convert(bad)

    def test_category_listing_is_discovery_not_invented_specifications(self):
        listing=specs.load(ROOT/'research/casio-us-gshock-listing-2017-2026-11-16.json')
        self.assertEqual(len(listing['models']),197)
        self.assertEqual(len({row['listed_model'] for row in listing['models']}),197)
        self.assertTrue(all('specs' not in row for row in listing['models']))
        index=specs.load(ROOT/'data/search-index.json');ids={r['id'] for r in index['records']}
        self.assertTrue({r['listed_model'] for r in listing['models']}<=ids)

    def test_mislabeled_measurements_are_not_imported_from_other_models(self):
        rows=specs.load(ROOT/'imports/zzzzzzzzzzzzzzzzzzzzzzzzz-gpw-gshock-archives-2026-11-16.json')
        for code in ['GW-M5610-1','GWF-D1035B-1']:
            row=next(r for r in rows if r['id']==code)
            self.assertNotIn('dimensions_mm',row['specs']);self.assertNotIn('weight_g',row['specs'])
        module=next(r for r in rows if r['id']=='5502')
        self.assertEqual(module['specs']['world_time_zones']['value'],39)
        self.assertNotIn('dimensions_mm',module['specs'])
