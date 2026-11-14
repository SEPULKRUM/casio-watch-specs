import copy
import unittest

import archive_import
import catalog
import specs


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = specs.load('research/archived-products-2026-11-14.json')
        cls.records = archive_import.convert(cls.notes)

    def test_batch_reproduces_and_is_safe_to_regenerate(self):
        self.assertEqual(self.records, specs.load('imports/archived-products-2026-11-14.json'))
        ids = [r['id'] for r in self.records if r['kind'] == 'model']
        self.assertEqual(archive_import.convert(self.notes, ids), self.records)

    def test_capture_identity_and_bad_wrappers_rejected(self):
        record = copy.deepcopy(self.records[0])
        original = record['specs']['module_id']['sources'][0]
        for change in [
            {'original_url': 'https://www.casio.com/another-page'},
            {'archive_timestamp': '20000101000000'},
            {'archive_timestamp': '20191301000000',
             'url': original['url'].replace(original['archive_timestamp'], '20191301000000')},
            {'snapshot_sha256': ''},
            {'accessed': '2000-01-01'},
            {'url': 'https://web.archive.org/web/20191207173117/https://shockbase.org/'},
            {'url': 'https://web.archive.org/web/20191207173117/https://www.casio.com.evil.example/'},
            {'url': 'https://web.archive.org.evil.example/web/20191207173117/https://www.casio.com/'},
            {'url': original['original_url']},
        ]:
            with self.subTest(change=change):
                source = copy.deepcopy(original)
                source.update(change)
                bad = copy.deepcopy(record)
                bad['specs']['module_id']['sources'] = [source]
                with self.assertRaises(ValueError):
                    specs.validate(bad)

    def test_punctuation_duplicates_and_missing_module_evidence_rejected(self):
        with self.assertRaises(ValueError):
            archive_import.convert(self.notes, ['GW-7900B-1'])
        notes = copy.deepcopy(self.notes)
        notes['documents'].append(notes['documents'][0])
        with self.assertRaises(ValueError):
            archive_import.convert(notes)
        notes = copy.deepcopy(self.notes)
        notes['documents'][0]['module_evidence'] = ''
        with self.assertRaises(ValueError):
            archive_import.convert(notes)

    def test_historical_functions_stay_separate_and_pending(self):
        result = specs.build(specs.load('watches.json'), self.records)
        self.assertEqual(result['legacy_watches'], specs.load('watches.json'))
        self.assertEqual(result['report']['conflicts'], [])
        for record in self.records:
            built = result[record['kind'] + 's'][record['id']]
            for field, fact in built['specs'].items():
                self.assertEqual(fact['status'], 'pending_review')
                self.assertIn('archive_timestamp', fact['sources'][0])
            if record['kind'] == 'model':
                self.assertNotIn('accuracy_seconds_per_month', built['specs'])
                self.assertNotIn('case_material', built['specs'])
        self.assertEqual(catalog.field_value(result['modules']['2548'], 'calendar')['end_year'], 2039)
        self.assertEqual(catalog.field_value(result['modules']['2924'], 'accuracy_condition'), 'With no signal calibration')

    def test_conflicting_history_cannot_override_present_fact(self):
        original = copy.deepcopy(self.records[0])
        conflict = copy.deepcopy(original)
        conflict['specs']['module_id']['value'] = '9999'
        result = specs.build(specs.load('watches.json'), [original, conflict])
        self.assertTrue(result['report']['conflicts'])
        self.assertEqual(catalog.field_value(result['models'][original['id']], 'module_id'), '3200')


if __name__ == '__main__':
    unittest.main()
