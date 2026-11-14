"""Discover official product URLs in local HTML or sitemap snapshots, in bulk.

Feed output to gather.py. This command makes no network requests and does not
activate sources.txt or interpret discovery as permission to fetch.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET


def discover(text, base_url):
    base = urlsplit(base_url)
    if base.scheme != 'https' or base.hostname != 'www.casio.com' or base.username or base.password:
        raise ValueError('Base must be an official HTTPS www.casio.com URL')
    links = []
    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag.lower() == 'a':
                href = dict(attrs).get('href')
                if href:
                    links.append(href)
    if text.lstrip().startswith('<?xml') or text.lstrip().startswith('<urlset') or text.lstrip().startswith('<sitemapindex'):
        root = ET.fromstring(text)
        links.extend(element.text for element in root.iter()
                     if element.tag.rsplit('}', 1)[-1] == 'loc' and element.text)
    else:
        Links().feed(text)
    result = set()
    import re
    for link in links:
        parsed = urlsplit(urljoin(base_url, link))
        if (parsed.scheme == 'https' and parsed.hostname == 'www.casio.com'
                and parsed.port in (None, 443) and not parsed.username and not parsed.password
                and re.fullmatch(r'/[a-z-]+/watches/[a-z]+/product\.[A-Za-z0-9-]+/', parsed.path)):
            result.add(urlunsplit(('https', 'www.casio.com', parsed.path, '', '')))
    return sorted(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshots', nargs='+')
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', default='build/discovered-sources.txt')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output == Path('sources.txt').resolve() or output in {Path(p).resolve() for p in args.snapshots}:
        parser.error('Output must not overwrite sources.txt or snapshots')
    urls = sorted({url for p in args.snapshots for url in discover(Path(p).read_text(encoding='utf-8'), args.base_url)})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(urls) + '\n', encoding='utf-8')
    print(f'Discovered {len(urls)} official product URLs; review permission before fetching')


if __name__ == '__main__':
    main()
