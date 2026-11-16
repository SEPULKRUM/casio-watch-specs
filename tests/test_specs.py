import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gather
import specs


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.records = specs.load('imports/module-3495.json')
        self.legacy = specs.load('watches.json')

    def test_preserve_legacy_and_separate_scopes(self):
        before = copy.deepcopy(self.legacy)
        result = specs.build(self.legacy, self.records)
        self.assertEqual(self.legacy, before)
        self.assertEqual(result['legacy_watches'], before)
        self.assertEqual(result['models']['GW-M5610U-1']['specs'], {})
        self.assertEqual(result['models']['GW-M5610U-1']['module'], '3495')
        self.assertEqual(result['modules']['3495']['specs']['alarm_count']['status'], 'pending_review')

    def test_deduplicate_normalized_identity(self):
        duplicate = copy.deepcopy(self.records[0])
        duplicate['id'] = ' 3495 '
        result = specs.build(self.legacy, self.records + [duplicate])
        self.assertEqual(len(result['modules']), 1)
        self.assertTrue(result['report']['duplicates'])

    def test_matching_pending_values_retain_independent_sources_without_promotion(self):
        original=copy.deepcopy(self.records[0]);changed=copy.deepcopy(original)
        field=next(iter(original['specs']))
        changed['specs'][field]['sources'][0]['url']='https://www.casio.com/independent-source'
        before=copy.deepcopy(original)
        result=specs.build(self.legacy,[original,changed])
        fact=result['modules']['3495']['specs'][field]
        self.assertEqual(len(fact['sources']),2)
        self.assertEqual(fact['status'],'pending_review')
        self.assertIn(specs.digest(changed),fact['corroborating_candidates'])
        self.assertEqual(original,before)

    def test_matching_unreviewed_source_cannot_modify_verified_evidence(self):
        original=copy.deepcopy(self.records[0]);changed=copy.deepcopy(original)
        field=next(iter(original['specs']))
        changed['specs'][field]['sources'][0]['url']='https://www.casio.com/independent-source'
        decision={'candidate_sha256':specs.digest(original),'reviewed_by':'test','note':'Original source reviewed'}
        result=specs.build(self.legacy,[original,changed],[decision])
        fact=result['modules']['3495']['specs'][field]
        self.assertEqual(fact['status'],'verified')
        self.assertEqual(fact['sources'],original['specs'][field]['sources'])

    def test_verified_conflict_cannot_overwrite(self):
        original = self.records[0]
        changed = copy.deepcopy(original)
        changed['specs']['alarm_count']['value'] = 99
        decision = {'candidate_sha256': specs.digest(original), 'reviewed_by': 'test', 'note': 'test review'}
        result = specs.build(self.legacy, [original, changed], [decision])
        self.assertEqual(result['modules']['3495']['specs']['alarm_count']['value'], 5)
        self.assertEqual(result['modules']['3495']['specs']['alarm_count']['status'], 'verified')
        self.assertEqual(len(result['report']['conflicts']), 1)

    def test_changed_candidate_invalidates_review(self):
        with self.assertRaises(ValueError):
            specs.build(self.legacy, self.records, [{'candidate_sha256': 'invalid', 'reviewed_by': 'a', 'note': 'b'}])

    def test_scopes_and_missing_sources_rejected(self):
        record = copy.deepcopy(self.records[0])
        record['specs']['weight_g'] = record['specs']['alarm_count']
        with self.assertRaises(ValueError):
            specs.validate(record)
        record = copy.deepcopy(self.records[0])
        record['specs']['alarm_count']['sources'] = []
        with self.assertRaises(ValueError):
            specs.validate(record)

    def test_block_shockbase(self):
        record = copy.deepcopy(self.records[0])
        record['specs']['alarm_count']['sources'][0]['url'] = 'https://shockbase.org/test'
        with self.assertRaises(ValueError):
            specs.validate(record)

    def test_extract_bulk_and_ambiguous_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manual.html').write_text('<p>Alarms: <b>5</b></p>')
            source = self.records[0]['specs']['alarm_count']['sources'][0]
            manifest = {'documents': [{'path': 'manual.html', 'kind': 'module', 'id': '3495',
                'source': source, 'rules': [{'field': 'alarm_count', 'pattern': r'Alarms: (?P<value>\d+)', 'type': 'number'}]}]}
            specs.write(root / 'manifest.json', manifest)
            result = specs.extract(root / 'manifest.json')
            self.assertEqual(result[0]['specs']['alarm_count']['value'], 5)
            (root / 'manual.html').write_text('Alarms: 5 Alarms: 6')
            with self.assertRaises(ValueError):
                specs.extract(root / 'manifest.json')

    def test_fetch_denies_redirects_and_unapproved_hosts(self):
        for url in ['http://www.casio.com/', 'https://shockbase.org/',
                    'https://www.casio.com@evil.example/', 'https://www.casio.com:444/']:
            self.assertFalse(gather.approved(url))
        self.assertIsNone(gather.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.example/'))

    @patch('gather.time.sleep')
    def test_robots_failure_prevents_product_request(self, sleep):
        import urllib.error
        with tempfile.TemporaryDirectory() as directory:
            with patch('gather.read', side_effect=urllib.error.URLError('offline')) as read:
                result = gather.gather(['https://www.casio.com/test'], directory)
                self.assertEqual(result[0]['status'], 'skipped')
                self.assertEqual(read.call_count, 1)


if __name__ == '__main__':
    unittest.main()

class AdditionalSafetyTests(unittest.TestCase):
    def test_legacy_module_link_is_locked(self):
        legacy = {'watches': [{'model': 'GW-M5610U-1', 'module': '3495'}]}
        source = specs.load('imports/module-3495.json')[0]['specs']['alarm_count']['sources']
        record = {'kind': 'model', 'id': 'gw-m5610u-1', 'specs': {
            'module_id': {'value': '3159', 'sources': source, 'uncertainty': 'test'}}}
        result = specs.build(legacy, [record])
        self.assertEqual(result['models']['GW-M5610U-1']['module'], '3495')
        self.assertTrue(result['report']['conflicts'])

    def test_invalid_numeric_fact_rejected(self):
        record = specs.load('imports/module-3495.json')[0]
        record['specs']['alarm_count']['value'] = float('nan')
        with self.assertRaises(ValueError):
            specs.validate(record)

    def test_cli_refuses_legacy_as_output(self):
        import subprocess
        before = Path('watches.json').read_bytes()
        result = subprocess.run(['python', 'specs.py', 'build', 'imports/module-3495.json',
                                 '--output', 'watches.json'], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(Path('watches.json').read_bytes(), before)
