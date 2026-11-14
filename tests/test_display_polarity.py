import copy
import unittest

import catalog
import manual_import
import specs


class DisplayPolarityTests(unittest.TestCase):
    def test_modules_retain_distinct_displays_and_shared_function_values(self):
        data = catalog.build_catalog()
        modules = [data['modules'][key] for key in ('3261', '3281')]
        self.assertEqual(catalog.field_value(modules[0], 'display_polarity'), 'positive')
        self.assertEqual(catalog.field_value(modules[1], 'display_polarity'), 'negative')
        functions = [{k: f['value'] for k, f in m['specs'].items() if k != 'display_polarity'}
                     for m in modules]
        self.assertEqual(functions[0], functions[1])
        view = catalog.module_view(data, data['models']['G-9300-1'])
        self.assertIsNone(view['module_id'])
        self.assertEqual(catalog.field_value(view['module_options']['3261'], 'display_polarity'), 'positive')
        self.assertEqual(catalog.field_value(view['module_options']['3281'], 'display_polarity'), 'negative')

    def test_invalid_polarity_and_wrong_scope_rejected(self):
        records = manual_import.convert(specs.load('research/module-3261-3281-display-2026-11-14.json'))
        for value in ('unknown', 'Positive', '', True, 1, {}, []):
            record = copy.deepcopy(records[0])
            record['specs']['display_polarity']['value'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                specs.validate(record)
        record = copy.deepcopy(records[0])
        record.update(kind='model', id='G-9300-1')
        with self.assertRaises(ValueError):
            specs.validate(record)
