"""SEPULKRUM Casio specification collector.

Reads approved Casio product URLs from sources.txt, respects robots.txt,
extracts JSON-LD Product candidates when available, and writes review_candidates.json.
Never changes watches.json or attempts to bypass HTTP access restrictions.
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources.txt'
OUTPUT = ROOT / 'review_candidates.json'
USER_AGENT = 'SepulkrumWatchSpecsResearch/0.2 (respect robots.txt)'
ALLOWED_HOSTS = {'casio.com', 'www.casio.com'}
MAX_BYTES = 2_000_000


class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag.lower() == 'script' and attributes.get('type', '').lower().split(';')[0].strip() == 'application/ld+json':
            self.inside = True
            self.parts = []

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'script' and self.inside:
            self.blocks.append(''.join(self.parts))
            self.inside = False


def product_nodes(obj):
    if isinstance(obj, list):
        for item in obj:
            yield from product_nodes(item)
    elif isinstance(obj, dict):
        types = obj.get('@type', [])
        if isinstance(types, str):
            types = [types]
        if isinstance(types, list) and any(isinstance(t, str) and t.rsplit('/', 1)[-1] == 'Product' for t in types):
            yield obj
        for key in ('@graph', 'mainEntity'):
            if key in obj:
                yield from product_nodes(obj[key])


def allowed(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password:
        return False, 'URL is not an approved HTTPS Casio domain'
    robots_url = f'{parsed.scheme}://{parsed.netloc}/robots.txt'
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        if rp.can_fetch(USER_AGENT, url):
            return True, ''
        return False, 'robots.txt does not allow this request or could not be verified'
    except Exception as exc:
        return False, f'robots.txt verification failed: {type(exc).__name__}'


def collect(url):
    permitted, reason = allowed(url)
    if not permitted:
        return {'source_url': url, 'status': 'skipped_not_permitted_or_unverified', 'reason': reason, 'products': []}
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            final_url = response.geturl()
            if final_url != url:
                redirect_allowed, _ = allowed(final_url)
                if not redirect_allowed:
                    return {'source_url': url, 'status': 'skipped_redirect', 'redirect_url': final_url, 'products': []}
            content_type = response.headers.get('Content-Type', '')
            if 'html' not in content_type.lower():
                return {'source_url': url, 'status': 'unexpected_content_type', 'content_type': content_type, 'products': []}
            html = response.read(MAX_BYTES + 1)
            if len(html) > MAX_BYTES:
                return {'source_url': url, 'status': 'page_too_large', 'products': []}
            html = html.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        code = exc.code
        status = 'access_denied' if code in (401, 403) else 'not_found' if code == 404 else 'http_error'
        return {'source_url': url, 'status': status, 'http_status': code,
                'explanation': ('Website denied automated access; do not retry to bypass restrictions' if code in (401, 403)
                                else 'Page not found' if code == 404 else 'HTTP request failed'), 'products': []}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {'source_url': url, 'status': 'network_error', 'error': str(exc)[:160], 'products': []}

    parser = JsonLdParser()
    parser.feed(html)
    found = []
    for block in parser.blocks:
        try:
            for product in product_nodes(json.loads(block)):
                name = product.get('name')
                if isinstance(name, str) and name.strip():
                    found.append({'name': name.strip(), 'sku': product.get('sku'),
                                  'model': product.get('model'), 'description': product.get('description'),
                                  'source_url': url, 'verification': 'pending_manual_review'})
        except (ValueError, TypeError):
            continue
    return {'source_url': url, 'status': 'candidate_found' if found else 'no_structured_product_data',
            'products': found, 'json_ld_blocks': len(parser.blocks)}


def main():
    if not SOURCES.exists():
        SOURCES.write_text('# Add approved Casio product URLs, one per line.\n', encoding='utf-8')
    urls = [line.strip() for line in SOURCES.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.lstrip().startswith('#')]
    results = []
    for url in dict.fromkeys(urls):
        result = collect(url)
        results.append(result)
        print(f"{result['status']}: {url}" + (f" (HTTP {result['http_status']})" if 'http_status' in result else ''))
        time.sleep(2)
    counts = {}
    for result in results:
        counts[result['status']] = counts.get(result['status'], 0) + 1
    OUTPUT.write_text(json.dumps({'generated_utc': datetime.now(timezone.utc).isoformat(),
                                  'note': 'Candidates require manual verification; watches.json unchanged',
                                  'summary': {'checked': len(results), 'statuses': counts},
                                  'results': results}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Checked {len(results)} URLs. Statuses: {counts}. Wrote {OUTPUT.name}. watches.json unchanged.')


if __name__ == '__main__':
    main()
