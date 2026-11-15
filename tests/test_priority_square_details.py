import json
from pathlib import Path
import unittest

import manual_import
import specs

ROOT = Path(__file__).resolve().parents[1]


class PrioritySquareDetails(unittest.TestCase):
    def test_original_and_updated_timing_behaviour_stays_distinct(self):
        data = specs.load(ROOT / 'data/catalog.json')
        original = data['modules']['3159']['specs']
        updated = data['modules']['3495']['specs']
        self.assertEqual(original['stopwatch']['value']['resolution_seconds'], .01)
        self.assertEqual(updated['stopwatch']['value']['resolution_segments'], [
            {'elapsed_seconds_below': 3600, 'resolution_seconds': .01},
            {'elapsed_seconds_at_least': 3600, 'resolution_seconds': 1}])
        self.assertEqual(original['timer']['value']['min_countdown_seconds'], 60)
        self.assertEqual(updated['timer']['value']['setting_unit_seconds'], 1)
        self.assertEqual(original['world_time_zones']['value'], 29)
        self.assertEqual(updated['world_time_zones']['value'], 31)
        self.assertEqual(updated['illumination']['value']['type'], 'LED')
        self.assertIn('Electroluminescent', original['illumination']['value'])
        for model, module in [('GW-M5610-1', '3159'), ('GW-5000-1', '3159'),
                              ('GW-M5610U-1', '3495'), ('GW-5000U-1', '3495')]:
            self.assertEqual(data['models'][model]['specs']['module_id']['value'], module)

    def test_archived_variants_keep_market_and_capture_provenance(self):
        rows = specs.load(ROOT / 'imports/zzzzzzzzzzzzzz-priority-square-archived-specifications-2026-11-15.json')
        self.assertEqual({r['id'] for r in rows}, {'GW-M5610BB-1', 'GW-M5610BW-7'})
        for row in rows:
            specs.validate(row)
            self.assertNotIn('color', row['specs'])
            self.assertNotIn('display_polarity', row['specs'])
            for fact in row['specs'].values():
                source = fact['sources'][0]
                specs.validate_archive_source(source)
                self.assertEqual(source['displayed_model'], row['id'] + 'ER')
                self.assertIn('ER suffix', source['scope_note'])
            self.assertEqual(row['specs']['weight_g']['value'], 52)
            self.assertIn('case only', row['specs']['case_material']['sources'][0]['locator'])
            self.assertIn('not diving depth', row['specs']['water_resistance_m']['sources'][0]['locator'])

    def test_module_import_is_reproducible_from_selected_technical_facts(self):
        notes = specs.load(ROOT / 'research/priority-square-module-details-2026-11-15.json')
        rows = manual_import.module_facts(notes)
        for note, row in zip(notes['modules'], rows):
            for fact in row['specs'].values():
                fact['sources'][0]['snapshot_sha256'] = note['snapshot_sha256']
        expected = specs.load(ROOT / 'imports/zzzzzzzzzzzzzz-priority-square-module-details-2026-11-15.json')
        self.assertEqual(rows, expected)
        self.assertEqual(sum(len(r['specs']) for r in rows), 8)
