import unittest
import parts_links

URL = 'https://boley.de/en/case-parts/casio/25194.gw-m5610-1'
MODEL = 'GW-M5610-1'
CATALOG = {'models': {MODEL: {'specs': {'module_id': {'value': '3159'}}}}}

class PartsLinksTests(unittest.TestCase):
    def test_sitemap_only_matches_exact_variants_and_approved_origin(self):
        xml = '''<urlset><url><loc>https://boley.de/case-parts/casio/25194.gw-m5610-1</loc></url>
        <url><loc>https://boley.de/case-parts/casio/1.gw-m5610-1b</loc></url>
        <url><loc>https://evil.example/case-parts/casio/2.gw-m5610-1</loc></url>
        <url><loc>https://boley.de/case-parts/casio/3.gw-m5610-1(</loc></url></urlset>'''
        d = parts_links.discover(xml, CATALOG)
        self.assertEqual(d['matches'], {MODEL: URL})

    def test_duplicate_exact_listings_require_review(self):
        xml = '<urlset>' + ''.join(f'<url><loc>https://boley.de/case-parts/casio/{i}.gw-m5610-1</loc></url>' for i in [1, 2]) + '</urlset>'
        d = parts_links.discover(xml, CATALOG)
        self.assertNotIn(MODEL, d['matches'])
        self.assertEqual(len(d['ambiguous'][MODEL]), 2)

    def test_qw_observation_is_from_listing_table_and_keeps_full_code(self):
        html = '<h1>Casio GW-M5610-1</h1><nav>QW9999-01</nav><table><tr><td>MODULE QW3159-01 / QW-3159-02</td></tr></table>'
        row = parts_links.extract(html, MODEL, URL, CATALOG)
        self.assertEqual(row['observed_qw_codes'], ['QW-3159-02', 'QW3159-01'])
        self.assertEqual(row['observed_module_ids'], ['3159'])
        self.assertEqual(row['module_comparison'], 'agrees_with_recorded_reference')
        self.assertEqual(CATALOG['models'][MODEL]['specs']['module_id']['value'], '3159')

    def test_module_disagreement_is_flagged_without_changing_catalog(self):
        html = '<h1>Casio GW-M5610-1</h1><table><td>QW3495-01</td></table>'
        row = parts_links.extract(html, MODEL, URL, CATALOG)
        self.assertEqual(row['module_comparison'], 'needs_review')
        self.assertEqual(CATALOG['models'][MODEL]['specs']['module_id']['value'], '3159')

    def test_wrong_heading_or_url_is_rejected(self):
        for url in ['https://evil.example/en/case-parts/casio/1.gw-m5610-1', 'https://boley.de/en/search?q=gw-m5610', 'https://name:secret@boley.de/en/case-parts/casio/1.gw-m5610-1']:
            with self.assertRaises(ValueError):
                parts_links.listing_url(url)
        with self.assertRaises(ValueError):
            parts_links.extract('<h1>Casio GW-M5610-1B</h1>', MODEL, URL, CATALOG)

    def test_assembly_letters_do_not_become_part_of_numeric_module(self):
        html = '<h1>Casio GW-M5610-1</h1><table><td>QW-2327YC-03TK</td></table>'
        row = parts_links.extract(html, MODEL, URL, CATALOG)
        self.assertEqual(row['observed_qw_codes'], ['QW-2327YC-03TK'])
        self.assertEqual(row['observed_module_ids'], ['2327'])
        self.assertEqual(row['module_comparison'], 'needs_review')
