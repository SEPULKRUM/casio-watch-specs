import json
from pathlib import Path
import re
import tempfile
import unittest

import build_web


class WebPackagingTests(unittest.TestCase):
    def test_cache_version_covers_entrypoint_stylesheet_and_all_module_imports(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)
            build_web.build(output)
            version = json.loads((output / 'build-info.json').read_text())['asset_version']
            self.assertRegex(version, r'^[0-9a-f]{16}$')
            index = (output / 'index.html').read_text()
            self.assertIn('app.mjs?v=' + version, index)
            self.assertIn('style.css?v=' + version, index)
            count = 0
            for path in output.glob('*.mjs'):
                for target in re.findall(r"['\"](\./[^'\"]+\.mjs(?:\?[^'\"]+)?)['\"]", path.read_text()):
                    self.assertTrue(target.endswith('?v=' + version), (path.name, target))
                    self.assertTrue((output / target.split('?')[0]).exists())
                    count += 1
            self.assertGreater(count, 10)
            first = (output / 'decoder.mjs').read_bytes()
            build_web.build(output)
            self.assertEqual(json.loads((output / 'build-info.json').read_text())['asset_version'], version)
            self.assertEqual((output / 'decoder.mjs').read_bytes(), first)
