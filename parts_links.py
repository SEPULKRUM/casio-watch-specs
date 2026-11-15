"""Discover exact Boley listings and record supplier module-code observations.

No parts tables/images are republished. Supplier evidence never changes catalog facts.
"""
import argparse
from datetime import date
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

AGENT = 'SepulkrumWatchSpecsResearch/0.3'
ORIGIN = 'https://boley.de'
SITEMAP = ORIGIN + '/sitemap-casepart-casio.xml'


def key(value):
    if not re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', value):
        raise ValueError('Unsupported model identifier')
    return value.replace('-', '').upper()


def listing_url(url):
    p = urllib.parse.urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'boley.de' or p.query or p.fragment
            or not re.fullmatch(r'/en/case-parts/casio/\d+\.[a-z0-9]+(?:-[a-z0-9]+)*', p.path)):
        raise ValueError('Expected exact Boley HTTPS Casio listing URL')
    return url


def discover(xml, catalog):
    by_model = {}
    for node in ET.fromstring(xml).iter():
        if node.tag.rsplit('}', 1)[-1] != 'loc' or not node.text:
            continue
        p = urllib.parse.urlsplit(node.text)
        if p.scheme != 'https' or p.netloc != 'boley.de' or p.query or p.fragment:
            continue
        match = re.fullmatch(r'/(?:en/)?case-parts/casio/(\d+)\.([a-z0-9]+(?:-[a-z0-9]+)*)', p.path)
        if not match:
            continue
        url = listing_url(f'{ORIGIN}/en/case-parts/casio/{match[1]}.{match[2]}')
        by_model.setdefault(key(match[2]), set()).add(url)
    matches, ambiguous = {}, {}
    for model in catalog['models']:
        try:
            urls = sorted(by_model.get(key(model), []))
        except ValueError:
            continue
        if len(urls) == 1:
            matches[model] = urls[0]
        elif urls:
            ambiguous[model] = urls
    return {'sitemap_url': SITEMAP, 'accessed': date.today().isoformat(),
            'sitemap_text_sha256': hashlib.sha256(xml.encode()).hexdigest(),
            'source_role': 'independent_supplier_model_discovery',
            'distinct_sitemap_model_identifiers': len(by_model),
            'catalog_models': len(catalog['models']), 'matches': matches,
            'ambiguous': ambiguous,
            'unmatched': sorted(set(catalog['models']) - set(matches))}


class ListingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = None
        self.headings = []
        self.table_depth = 0
        self.table_text = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag in ('h1', 'h3'):
            self.heading = []
        if tag == 'table':
            self.table_depth += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('h1', 'h3') and self.heading is not None:
            self.headings.append(' '.join(self.heading).strip())
            self.heading = None
        if tag == 'table':
            self.table_depth = max(0, self.table_depth - 1)

    def handle_data(self, text):
        if self.hidden:
            return
        if self.heading is not None:
            self.heading.append(text.strip())
        if self.table_depth:
            self.table_text.append(text.strip())


def extract(html, model, url, catalog):
    listing_url(url)
    parser = ListingParser()
    parser.feed(html)
    headings = [h[6:].strip() for h in parser.headings if h.startswith('Casio ')]
    if len(headings) != 1 or key(headings[0]) != key(model):
        raise ValueError('Exact Boley model heading does not match catalog model')
    slug = urllib.parse.urlsplit(url).path.rsplit('.', 1)[-1]
    if key(slug) != key(model):
        raise ValueError('Listing URL identity does not match model')
    codes = sorted({m[0] for m in re.finditer(r'\bQW-?\d{3,4}[A-Z]{0,4}-\d{2}[A-Z]{0,4}\b', ' '.join(parser.table_text).upper())})
    observed = sorted({re.match(r'QW-?(\d{3,4})(?=[A-Z-])', code)[1] for code in codes})
    rec = catalog['models'][model]
    expected = rec.get('specs', {}).get('module_candidates', {}).get('value') or [
        rec.get('specs', {}).get('module_id', {}).get('value') or rec.get('module')]
    expected = sorted(str(v) for v in expected if v)
    comparison = ('no_explicit_qw_code' if not observed else 'supplier_only' if not expected
                  else 'agrees_with_recorded_reference' if observed == expected else 'needs_review')
    return {'url': url, 'listed_model': headings[0], 'accessed': date.today().isoformat(),
            'snapshot_sha256': hashlib.sha256(html.encode()).hexdigest(),
            'observed_qw_codes': codes, 'observed_module_ids': observed,
            'recorded_module_ids': expected, 'module_comparison': comparison,
            'evidence_status': 'supplier_listing_checked; not independent specification verification'}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def collect(manifest, catalog, output):
    opener = urllib.request.build_opener(NoRedirect())
    def read(url):
        p = urllib.parse.urlsplit(url)
        if p.scheme != 'https' or p.netloc != 'boley.de':
            raise ValueError('Unapproved origin')
        with opener.open(urllib.request.Request(url, headers={'User-Agent': AGENT}), timeout=25) as r:
            b = r.read(12_000_001)
            if len(b) > 12_000_000:
                raise ValueError('Response too large')
            return b.decode('utf-8-sig')
    robots = urllib.robotparser.RobotFileParser()
    robots.parse(read(ORIGIN + '/robots.txt').splitlines())
    result = {'schema_version': 1, 'accessed': date.today().isoformat(), 'supplier': 'Boley',
              'scope': 'Exact checked model listing links and explicit supplier QW codes only. No parts tables, images, prices or availability republished. Catalog specification values unchanged.',
              'sitemap_url': SITEMAP, 'models': {}, 'failures': [],
              'unmatched': manifest['unmatched'], 'ambiguous': manifest['ambiguous']}
    for model, url in manifest['matches'].items():
        try:
            listing_url(url)
            if not robots.can_fetch(AGENT, url):
                raise ValueError('robots.txt disallows request')
            html = read(url)
            snapshots = Path('build/boley-snapshots')
            snapshots.mkdir(parents=True, exist_ok=True)
            (snapshots / (model + '.html')).write_text(html)
            result['models'][model] = extract(html, model, url, catalog)
            print(model, 'checked', flush=True)
        except Exception as exc:
            result['failures'].append({'model': model, 'url': url, 'reason': str(exc)[:180]})
            print(model, 'unavailable', flush=True)
            if getattr(exc, 'code', None) in (401, 403, 429):
                break
        time.sleep(2)
    attempted = set(result['models']) | {row['model'] for row in result['failures']}
    result['not_checked'] = sorted(set(manifest['matches']) - attempted)
    result['complete_for_manifest'] = not result['not_checked']
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['discover', 'collect'])
    p.add_argument('--catalog', default='data/catalog.json')
    p.add_argument('--sitemap', help='Local public Casio sitemap XML snapshot')
    p.add_argument('--manifest', help='Discovery manifest produced by discover')
    p.add_argument('--output', required=True)
    args = p.parse_args()
    catalog = json.loads(Path(args.catalog).read_text())
    if args.command == 'discover':
        if not args.sitemap:
            p.error('--sitemap is required')
        result = discover(Path(args.sitemap).read_text(encoding='utf-8-sig'), catalog)
        Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    else:
        if not args.manifest:
            p.error('--manifest is required')
        collect(json.loads(Path(args.manifest).read_text()), catalog, args.output)

if __name__ == '__main__':
    main()
