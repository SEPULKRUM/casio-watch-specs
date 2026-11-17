import unittest
from pathlib import Path
import family_classification as f
class FamilyClassificationTests(unittest.TestCase):
 def test_shared_reproducible_rules(self):
  r=Path(__file__).resolve().parents[1];self.assertEqual((r/'web/family-classification.mjs').read_text(),f.browser_artifact(r))
 def test_known_families_do_not_supply_modules(self):
  for id in ['OAW-100TDJ-1A','OAW-100TDJ-1AJF','OAW-100TDJ-7AJF']:self.assertEqual(f.resolve_family(id,'Unclassified'),'OVERLAND')
  self.assertEqual(f.resolve_family('LCW-M200DJ-2AJF','Oceanus'),'LINEAGE');self.assertEqual(f.resolve_family('UNKNOWN-1A','Unclassified'),'Unclassified')
