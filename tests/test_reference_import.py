import json
import re
from pathlib import Path
import tempfile
import unittest

import reference_import

ROOT = Path(__file__).resolve().parents[1]


class ReferenceImportTests(unittest.TestCase):
    def test_identifiers_deduplicate_but_regional_variants_remain_separate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            files = {
                'all_uploaded_source_manifest.json': [{'id': 'source_01', 'filename': 'Missing original.pdf'}],
                'catalog_sources.json': [{'source_id': 'cat1', 'filename': 'Catalog.pdf'}],
                'model_mention_index_REVIEW_REQUIRED.json': [{'source_id': 'source_01', 'pdf_page': 4, 'model_strings': ['CFX-200', 'CFX-200-1JF', 'CFX-200-1JR', 'BAD/READ']}],
                'received-source-summary.json': [{'filename': 'PART.pdf', 'sha256': 'a'*64, 'pages': 2, 'combined_start_page': 1}],
                'page-registry.json': [{'combined_page': 1, 'source_pdf_page': 1, 'candidate_model_strings': ['CFX-200', 'CR-2025']}]
            }
            for name, data in files.items():
                (root / name).write_text(json.dumps(data))
            (root / 'catalog_watch_records.jsonl').write_text(json.dumps({'source_id': 'cat1', 'pdf_page': 2, 'model': 'CFX-200', 'module': '197', 'price': 100}) + '\n')
            data, rejected = reference_import.build(root, {'pages': {'1': ['CFX-200']}})
            self.assertEqual(set(data['models']), {'CFX-200', 'CFX-200-1JF', 'CFX-200-1JR'})
            self.assertEqual(data['models']['CFX-200']['status'], 'index_checked')
            self.assertEqual(len(data['models']['CFX-200']['observations']), 4)
            self.assertEqual(data['models']['CFX-200-1JR']['status'], 'machine_candidate')
            self.assertNotIn('module', data['models']['CFX-200'])
            self.assertNotIn('price', data['models']['CFX-200'])
            self.assertEqual(len(rejected), 2)
            entries = reference_import.prefix_entries(data, set())
            self.assertEqual(entries[0][1], 'CFX')
            self.assertEqual(entries[0][4]['status'], 'secondary_reported')
            self.assertEqual(reference_import.prefix_entries(data, {'CFX'}), [])

    def test_published_library_is_only_sourced_identifiers_and_review_statuses(self):
        data = json.loads((ROOT / 'data/model-references.json').read_text())
        self.assertEqual(len(data['models']), data['counts']['model_strings'])
        self.assertGreater(len(data['models']), 2000)
        counts = {s: 0 for s in ['index_checked', 'supplied_transcription', 'machine_candidate']}
        for id, model in data['models'].items():
            self.assertEqual(id, model['id'])
            counts[model['status']] += 1
            self.assertNotIn('specs', model)
            self.assertNotIn('module_id', model)
            self.assertNotIn('verified', model)
            for observation in model['observations']:
                self.assertIn(observation['source_id'], data['sources'])
                if 'compilation_page' in observation:
                    self.assertTrue(1 <= observation['compilation_page'] <= 219)
        for status, count in counts.items():
            self.assertEqual(count, data['counts'][status])
        self.assertEqual(data['models']['110QS-37B']['prefix'], '')
        self.assertEqual(data['models']['GMW-15-1V']['status'], 'index_checked')
        text = (ROOT / 'data/model-references.json').read_text()
        for forbidden in ['/tmp/', '/workspace/', 'productAssets', 'price_usd', 'ON THE RUN']:
            self.assertNotIn(forbidden, text)

    def test_generated_prefix_entries_match_library_provenance(self):
        library = json.loads((ROOT / 'data/model-references.json').read_text())
        original = (ROOT / 'web/prefix-data.mjs').read_text()
        base = json.loads(re.search(r'const baseEntries=(\[.*?\]);', original, re.S)[1])
        expected = reference_import.prefix_entries(library, {x[1] for x in base})
        actual = json.loads(re.search(r'export const researchEntries=(\[.*?\]);', (ROOT / 'web/research-prefix-data.mjs').read_text(), re.S)[1])
        self.assertEqual(expected, actual)
        self.assertEqual(len(base), 57)
        self.assertEqual(len(actual), 80)
        self.assertTrue(all(x[4]['status'] in {'secondary_reported', 'unverified', 'official_observed'} for x in actual))

    def test_guide_supplement_is_idempotent_page_scoped_and_does_not_import_claims(self):
        supplement = json.loads((ROOT / 'research/reference-supplements/guide-v3-2026-11-15.json').read_text())
        library = json.loads((ROOT / 'data/model-references.json').read_text())
        before = json.dumps(library, sort_keys=True)
        reference_import.add_supplement(library, supplement)
        self.assertEqual(before, json.dumps(library, sort_keys=True))
        self.assertEqual(len(supplement['models']), 79)
        ids = {m['id'] for m in supplement['models']}
        self.assertIn('CMK-100TCC-8AER', ids)
        self.assertIn('MTP-E735AR-2A3V', ids)
        self.assertIn('LTP-V007', ids)
        self.assertTrue(ids.isdisjoint(supplement['excluded_fragments']))
        self.assertEqual(library['models']['CMK-100TCC-8AER']['status'], 'machine_candidate')
        self.assertNotIn('specs', library['models']['CMK-100TCC-8AER'])
        cmk = next(p for p in library['prefix_observations'] if p['prefix'] == 'CMK')
        self.assertEqual(cmk['status'], 'official_observed')
        self.assertTrue(cmk['official_source'].startswith('https://www.casio.com/'))
