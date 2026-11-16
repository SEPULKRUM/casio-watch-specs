import copy
import json
import unittest
from pathlib import Path
import specs

ROOT=Path(__file__).resolve().parents[1]

class UnitedArrowsArchiveTests(unittest.TestCase):
    def test_archived_claims_have_bound_snapshot_provenance(self):
        rows=specs.load(ROOT/'imports/zzzzzzzzzzzzzzzzzzzzzzzz-awg-m520ua-archives-2026-11-16.json')
        for record in rows:
            specs.validate(record)
            for fact in record['specs'].values():
                for source in fact['sources']:
                    specs.validate_archive_source(source)
                    self.assertTrue(source['snapshot_sha256'])

    def test_collaboration_measurements_stay_separate_from_base_dimensions(self):
        catalog=specs.load(ROOT/'data/catalog.json');row=catalog['models']['AWG-M520UA-1EJR']['specs']
        self.assertEqual(row['weight_g']['value'],55)
        self.assertEqual(row['water_resistance_bar']['value'],20)
        self.assertNotIn('dimensions_mm',row)
        self.assertEqual([r['dimensions_mm']['thickness'] for r in row['reported_measurements']['value']],[13.1,15.3])
        urls={s['url'] for s in row['reported_measurements']['sources'] if 'url' in s}
        self.assertTrue(any('/20240413003324/' in url for url in urls))
        self.assertTrue(any('/20240721100125/' in url for url in urls))
        self.assertEqual(row['module_id']['value'],'5640')

    def test_collaboration_archive_allowlist_rejects_lookalike_domains(self):
        source=specs.load(ROOT/'imports/zzzzzzzzzzzzzzzzzzzzzzzz-awg-m520ua-archives-2026-11-16.json')[0]['specs']['weight_g']['sources'][0]
        bad=copy.deepcopy(source)
        for field in ['url','original_url']:bad[field]=bad[field].replace('store.united-arrows.co.jp','store.united-arrows.co.jp.evil.example')
        with self.assertRaises(ValueError):specs.validate_archive_source(bad)
