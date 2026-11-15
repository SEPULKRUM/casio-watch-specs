"""Convert selected public Casio support-feed specifications, without assets or prose."""
import math
import re
from urllib.parse import urlsplit

import specs

COLOURS = {'ブラック': 'Black', 'イエロー': 'Yellow', 'ブルー': 'Blue',
           'グリーン': 'Green', 'レッド': 'Red', 'ホワイト': 'White',
           'グレー': 'Gray', 'ブラウン': 'Brown'}


def convert(notes, catalog):
    records = []
    seen = set()
    for product in notes['products']:
        model = product['model']
        raw = product['fields']
        url = urlsplit(product['url'])
        expected = '/content/casio/locales/jp/ja/products/product.data.' + model + '.json'
        if (model in seen or model not in catalog['models'] or url.scheme != 'https'
                or url.hostname != 'www.casio.com' or url.username or url.password
                or url.port or url.query or url.fragment or url.path != expected):
            raise ValueError('Unique existing exact model and public Casio feed URL required')
        seen.add(model)
        shown = raw['productDisplayName']
        if (raw['productName'] != model or raw['sku'] != shown
                or not re.fullmatch(re.escape(model) + r'(?:JF|JR)', shown)):
            raise ValueError('Product name, displayed model and SKU must agree')
        if not re.fullmatch(r'[0-9a-f]{64}', product['snapshot_sha256']):
            raise ValueError('Source checksum required')
        prior = catalog['models'][model]['specs']
        if raw['moduleNumber'] != prior['module_id']['value']:
            raise ValueError('Feed module differs from catalog; review separately')
        values = [raw[k] for k in ['height', 'width', 'depth', 'weight']]
        if any(isinstance(x, bool) or not isinstance(x, (int, float))
               or not math.isfinite(x) or x <= 0 for x in values):
            raise ValueError('Positive finite dimensions and weight required')
        if not notes.get('unit_validation', {}).get('checked_against_visible_product_page'):
            raise ValueError('Documented unit validation required')
        colour = ' / '.join(COLOURS[x] for x in raw['colorName'].split(','))
        facts = {'dimensions_mm': dict(zip(['length', 'width', 'thickness'], values[:3])),
                 'weight_g': values[3], 'color': colour}
        locators = {'dimensions_mm': 'height, width, depth (mm)', 'weight_g': 'weight (g)',
                    'color': 'colorName (manufacturer colour categories; translated)'}
        tags = raw['hashTag']
        if '樹脂バンド' in tags:
            facts['band_material'] = 'Resin'
            locators['band_material'] = 'hashTag / 樹脂バンド (resin band)'
        if '20気圧防水' in tags:
            facts['water_resistance_bar'] = 20
            facts['water_resistance_rating'] = '20 bar'
            locators['water_resistance_bar'] = locators['water_resistance_rating'] = 'hashTag / 20気圧防水 (20 bar)'
        converted = {}
        for field, value in facts.items():
            if field in prior:
                raise ValueError('Existing fact requires separate comparison; no automatic overwrite')
            source = {'url': product['url'], 'accessed': notes['accessed'],
                      'locator': 'Public support product-data feed / ' + locators[field],
                      'evidence': f'{shown}: {field} = {value}',
                      'snapshot_sha256': product['snapshot_sha256'],
                      'permission': 'official_public_reference',
                      'evidence_type': 'normalized_technical_fact',
                      'displayed_model': shown,
                      'scope_note': f'Japanese-market {shown} feed under existing base variant {model}; no cross-region or production-revision equivalence asserted.'}
            converted[field] = {'value': value, 'sources': [source],
                                'uncertainty': 'Official Japanese-market support-feed candidate; independent review pending. Colour is a broad manufacturer category, not a complete description of every component.'}
        record = {'kind': 'model', 'id': model, 'specs': converted}
        specs.validate(record)
        records.append(record)
    return records
