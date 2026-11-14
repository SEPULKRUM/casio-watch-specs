"""Convert a batch of researched official product facts into model candidates.

Research notes retain selected technical facts, not entire copyrighted pages.
No module assignment or depth rating is inferred from model names or materials.
"""
import argparse
import re
from urllib.parse import urlsplit

import specs

LABELS = {
    'dimensions_mm': ('Case size (L× W× H)', 'ケースサイズ（縦×横×厚さ）'),
    'weight_g': ('Weight', '質量'),
    'case_material': ('Case and bezel material', 'ケース・ベゼル材質'),
    'band_material': ('Band', 'バンド'),
    'glass': ('Glass', 'ガラス'),
    'water_resistance_rating': ('Water resistance', '防水性'),
}
TRANSLATIONS = {
    'チタン': 'Titanium',
    '本革バンド': 'Genuine leather',
    'ステンレススチール': 'Stainless steel',
    '樹脂／ステンレススチール': 'Resin / Stainless steel',
    '樹脂バンド': 'Resin',
    'メタルバンド（ステンレスムクバンド）': 'Stainless steel',
    'メタルバンド（チタン）': 'Titanium',
    '内面反射防止コーティングサファイアガラス': 'Sapphire; anti-reflective coating on inner surface',
    '内面反射防止コーティングサファイアガラス（デュアルカーブ）': 'Dual-curved sapphire; anti-reflective coating on inner surface',
    '両面反射防止コーティングサファイアガラス': 'Sapphire; anti-reflective coating on both surfaces',
    '樹脂ガラス（表面形状：球面・曲面）': 'Resin glass; spherical/curved surface',
}


def convert(notes):
    records = []
    seen = set()
    for product in notes['products']:
        url = urlsplit(product['url'])
        if url.scheme != 'https' or url.hostname != 'www.casio.com' or url.username or url.password:
            raise ValueError('Research batch must cite an official Casio product URL')
        if '/watches/' not in url.path or '/product.' not in url.path:
            raise ValueError('Not an official product page')
        key = specs.identity(product['id'])
        if key in seen:
            raise ValueError(f'Duplicate researched model: {key}')
        seen.add(key)
        fields = product['fields']
        facts = {}
        region = url.path.split('/')[1]
        for field, labels in LABELS.items():
            present = [label for label in labels if label in fields]
            if len(present) > 1:
                raise ValueError(f'Ambiguous source labels: {field}')
            if not present:
                continue
            label = present[0]
            raw = fields[label]
            uncertainty = 'Official-source candidate; independent review pending'
            if field == 'dimensions_mm':
                match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*×\s*(\d+(?:\.\d+)?)\s*mm', raw)
                if not match:
                    raise ValueError(f'{key}: dimensions must specify L×W×H in mm')
                value = dict(zip(('length', 'width', 'thickness'), map(float, match.groups())))
            elif field == 'weight_g':
                match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*g', raw)
                if not match:
                    raise ValueError(f'{key}: weight must specify grams')
                value = float(match[1])
            elif field == 'band_material':
                parts = raw.splitlines()
                selected = [p for p in parts if re.search(r'resin|urethane|steel|titanium|leather|cloth|nylon|cordura|composite|樹脂|メタルバンド|本革|クロス|布', p, re.I)]
                if not selected:
                    continue
                value = TRANSLATIONS.get(selected[0], selected[0])
            elif field == 'case_material' and raw.lower() == 'ion plated':
                # A finish is not evidence of the underlying case metal.
                field, value = 'case_finish', 'Ion plated'
                uncertainty = 'Official page gives finish only; underlying case material unknown'
            else:
                value = TRANSLATIONS.get(raw, raw)
            evidence = f'Product specification {label}: {value}'
            source = {'url': product['url'], 'accessed': notes['accessed'],
                      'locator': f'Specifications / {label}', 'evidence': evidence,
                      'evidence_type': 'normalized_technical_fact',
                      'permission': 'official_public_reference', 'region': region,
                      'language': 'ja' if region == 'jp' else 'en',
                      'research_sha256': specs.digest(product)}
            if product.get('snapshot_sha256'):
                source['snapshot_sha256'] = product['snapshot_sha256']
            facts[field] = {'value': value, 'uncertainty': uncertainty, 'sources': [source]}
            if field == 'water_resistance_rating':
                metres = re.fullmatch(r'(\d+)-met(?:er|re) water resistance', raw, re.I)
                bar = re.fullmatch(r'(\d+)気圧防水', raw)
                if metres:
                    facts['water_resistance_m'] = dict(facts[field], value=int(metres[1]))
                elif bar:
                    facts['water_resistance_bar'] = dict(facts[field], value=int(bar[1]))
                # Generic Water Resistant deliberately has no numeric depth.
        source = {'url': product['url'], 'accessed': notes['accessed'],
                  'locator': 'Product family / official page classification',
                  'evidence': f'Official product classified as {product["series"]}',
                  'evidence_type': 'research_classification',
                  'permission': 'official_public_reference', 'region': region,
                  'language': 'ja' if region == 'jp' else 'en'}
        facts['series'] = {'value': product['series'], 'sources': [source],
                          'uncertainty': 'Research classification; regional marketing categories may differ'}
        record = {'kind': 'model', 'id': key, 'specs': facts}
        specs.validate(record)
        records.append(record)
    return records


def extract_html(html, url, accessed):
    """Read h1/h4 product specifications from a permitted official HTML snapshot."""
    from html.parser import HTMLParser
    class ProductParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.suppressed = 0
            self.heading = None
            self.parts = []
            self.titles = []
            self.label = None
            self.values = []
            self.fields = {}

        def flush(self):
            if self.label is not None:
                value = ' '.join(self.values).strip()
                if self.label in self.fields:
                    raise ValueError('Repeated specification heading')
                self.fields[self.label] = value
            self.label, self.values = None, []

        def handle_starttag(self, tag, attrs):
            if tag in ('script', 'style', 'nav'):
                self.suppressed += 1
            if self.suppressed:
                return
            if tag in ('h1', 'h2', 'h3', 'h4'):
                self.flush()
                self.heading, self.parts = tag, []

        def handle_endtag(self, tag):
            if tag in ('script', 'style', 'nav'):
                self.suppressed = max(0, self.suppressed - 1)
                return
            if self.suppressed:
                return
            if tag == self.heading:
                heading = ' '.join(self.parts).strip()
                if tag == 'h1':
                    self.titles.append(heading)
                if tag == 'h4':
                    self.label = heading
                self.heading = None

        def handle_data(self, value):
            if self.suppressed:
                return
            value = ' '.join(value.split())
            if not value:
                return
            if self.heading:
                self.parts.append(value)
            elif self.label:
                self.values.append(value)

    parser = ProductParser()
    parser.feed(html)
    parser.flush()
    titles = [title for title in parser.titles if re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+', title)]
    if len(set(titles)) != 1:
        raise ValueError('Expected one unambiguous product model heading')
    brand = urlsplit(url).path.split('/')[3]
    series = {'gshock': 'G-SHOCK', 'protrek': 'Pro Trek', 'oceanus': 'Oceanus',
              'edifice': 'Edifice', 'babyg': 'Baby-G', 'casio': 'Casio'}.get(brand)
    if series is None:
        raise ValueError('Unknown official product family path')
    labels = {label for choices in LABELS.values() for label in choices}
    fields = {k: v for k, v in parser.fields.items() if k in labels}
    if not any(label in fields for label in LABELS['dimensions_mm']):
        raise ValueError('No product specification dimensions found')
    return {'id': titles[0], 'series': series, 'url': url, 'fields': fields}


def from_snapshots(report_path, accessed):
    """Use all successful gather.py downloads without entering watches individually."""
    from pathlib import Path
    from datetime import date
    date.fromisoformat(accessed)
    products = []
    for result in specs.load(report_path):
        if result['status'] != 'downloaded':
            continue
        path = Path(result['path'])
        if path.suffix.lower() not in ('.html', '.htm'):
            continue
        import hashlib
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != result['sha256']:
            raise ValueError('Snapshot does not match fetch report checksum')
        product = extract_html(data.decode('utf-8'), result['url'], accessed)
        product['snapshot_sha256'] = result['sha256']
        products.append(product)
    if not products:
        raise ValueError('No successful HTML product snapshots in fetch report')
    return convert({'accessed': accessed, 'products': products})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notes', nargs='?')
    parser.add_argument('--snapshots', help='gather.py fetch-report.json; batch HTML extraction')
    parser.add_argument('--accessed', help='ISO date snapshots were obtained')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if bool(args.notes) == bool(args.snapshots):
        parser.error('Provide exactly one research-notes file or --snapshots report')
    if args.snapshots and not args.accessed:
        parser.error('--snapshots requires --accessed')
    from pathlib import Path
    source_path = args.notes or args.snapshots
    if Path(args.output).resolve() == Path(source_path).resolve() or Path(args.output).name == 'watches.json':
        parser.error('Output cannot replace source notes or watches.json')
    result = from_snapshots(args.snapshots, args.accessed) if args.snapshots else convert(specs.load(args.notes))
    specs.write(args.output, result)


if __name__ == '__main__':
    main()
