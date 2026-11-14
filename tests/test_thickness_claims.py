import copy
import csv
import io
import unittest

import catalog
import specs


class LabeledThicknessTests(unittest.TestCase):
    def test_conflicting_sections_survive_lookup_and_csv_without_a_chosen_value(self):
        data = catalog.build_catalog()
        record = data['models']['PAW2000-1']
        self.assertEqual(catalog.field_value(record, 'promotional_thickness_mm'), 11.5)
        self.assertEqual(catalog.field_value(record, 'technical_table_thickness_mm'), 11.3)
        self.assertNotIn('dimensions_mm', record['specs'])
        row = next(r for r in csv.DictReader(io.StringIO(catalog.export_csv(data)))
                   if r['model'] == 'PAW2000-1')
        self.assertEqual(row['promotional_thickness_mm'], '11.5')
        self.assertEqual(row['technical_table_thickness_mm'], '11.3')
        self.assertEqual(row['thickness_mm'], '')
        sources = [record['specs'][field]['sources'][0] for field in
                   ('promotional_thickness_mm', 'technical_table_thickness_mm')]
        self.assertNotEqual(sources[0]['locator'], sources[1]['locator'])

    def test_claims_require_positive_finite_model_scoped_numbers(self):
        original = specs.load('imports/zzzzz-paw2000-labeled-thickness-2026-11-14.json')[0]
        for field in original['specs']:
            for value in (0, -1, True, '11.5', float('nan'), float('inf')):
                with self.subTest(field=field, value=value):
                    record = copy.deepcopy(original)
                    record['specs'][field]['value'] = value
                    with self.assertRaises(ValueError):
                        specs.validate(record)
        record = copy.deepcopy(original)
        record.update(kind='module', id='3172')
        with self.assertRaises(ValueError):
            specs.validate(record)
