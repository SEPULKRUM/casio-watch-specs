import copy
import json
import unittest
from pathlib import Path
import catalog

ROOT = Path(__file__).resolve().parents[1]

class AnniversaryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / 'imports/zzzzzzzzzzzzzzzzz-anniversary-frogman-2026-11-15.json').read_text())

    def test_supplied_claims_bind_to_exact_record_field_and_value(self):
        catalog.validate_user_evidence(ROOT, self.rows)
        changed = copy.deepcopy(self.rows)
        changed[0]['specs']['glass']['value'] = 'Unsubstantiated replacement'
        with self.assertRaisesRegex(ValueError, 'exact specification'):
            catalog.validate_user_evidence(ROOT, changed)

    def test_supplied_claim_cannot_be_reused_for_another_model(self):
        changed = copy.deepcopy(self.rows)
        changed[0]['id'] = 'GWF-D1000-1'
        with self.assertRaisesRegex(ValueError, 'exact specification'):
            catalog.validate_user_evidence(ROOT, changed)
