import unittest
from pathlib import Path
import model_identity,official_support,specs
class ModelIdentityTests(unittest.TestCase):
 def test_generators_and_existing_identifiers(self):
  root=Path(__file__).resolve().parents[1]
  self.assertEqual((root/'web/model-identity-data.mjs').read_text(),model_identity.artifact(root))
  self.assertEqual((root/'web/official-support.mjs').read_text(),official_support.artifact(root))
  n=specs.load(root/model_identity.REFERENCE);ids={r['id'] for r in specs.load(root/'data/search-index.json')['records']}
  for alias,target in n['aliases'].items():self.assertIn(alias,ids);self.assertIn(target,ids)
