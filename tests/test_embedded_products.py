import json
import unittest

import product_import


class EmbeddedProductTests(unittest.TestCase):
    url = 'https://www.casio.com/us/watches/gshock/product.GW-7900B-1/'

    def page(self, width='46.3', model='GW7900B-1'):
        payload = {'Product': [{'subItemsList': [
            {'subItemTitle': 'Case size (L× W× H)',
             'subItemValuesList': [f'52 × {width} × 16.3 mm']},
            {'subItemTitle': 'Water resistance',
             'subItemValuesList': ['200-meter water resistance']}]}]}
        return f'<h1>{model}</h1><script>window.data={{"specificationsItemList":{json.dumps(payload)}}}</script>'

    def test_embedded_json_converts_to_sourced_dimensions(self):
        product = product_import.extract_html(self.page(), self.url, '2026-11-14')
        result = product_import.convert({'accessed': '2026-11-14', 'products': [product]})[0]
        self.assertEqual(result['id'], 'GW7900B-1')
        self.assertEqual(result['specs']['dimensions_mm']['value'],
                         {'length': 52, 'width': 46.3, 'thickness': 16.3})
        self.assertEqual(result['specs']['water_resistance_m']['value'], 200)

    def test_suffix_mismatch_and_conflicting_components_rejected(self):
        for html in [self.page(model='GW7900B-1JF'), self.page() + self.page(width='45'),
                     self.page() + '<h4>Case size (L× W× H)</h4>1 × 2 × 3 mm']:
            with self.subTest(html=html), self.assertRaises(ValueError):
                product_import.extract_html(html, self.url, '2026-11-14')

    def test_malformed_and_duplicate_json_rejected(self):
        for payload in ['{', '{"Product":[],"Product":[]}', '{"Product":"wrong"}']:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                product_import.extract_html('<h1>GW7900B-1</h1><script>{"specificationsItemList":'
                                            + payload + '}</script>', self.url, '2026-11-14')

    def test_source_discrepancy_annotation_is_retained_and_scoped(self):
        product = product_import.extract_html(self.page(), self.url, '2026-11-14')
        product['field_uncertainty'] = {'dimensions_mm': 'Current page differs from archived measurements'}
        records = product_import.convert({'accessed': '2026-11-14', 'products': [product]})
        self.assertEqual(records[0]['specs']['dimensions_mm']['uncertainty'],
                         product['field_uncertainty']['dimensions_mm'])
        product['field_uncertainty']['unknown_field'] = 'Not supported'
        with self.assertRaises(ValueError):
            product_import.convert({'accessed': '2026-11-14', 'products': [product]})
