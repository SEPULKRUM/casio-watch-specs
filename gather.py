"""Fetch an explicit bulk URL list into snapshots; deny redirects and fail closed on robots."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

AGENT = 'SepulkrumWatchSpecsResearch/0.3'
HOSTS = {'www.casio.com', 'casio.com', 'support.casio.com'}
LIMIT = 12_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def approved(url):
    parsed = urllib.parse.urlsplit(url)
    return (parsed.scheme == 'https' and parsed.hostname in HOSTS
            and parsed.port in (None, 443) and not parsed.username and not parsed.password)


def read(opener, url):
    with opener.open(urllib.request.Request(url, headers={'User-Agent': AGENT}), timeout=30) as response:
        content = response.read(LIMIT + 1)
        if len(content) > LIMIT:
            raise ValueError('Response too large')
        return content, response.headers.get_content_type()


def gather(urls, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    opener = urllib.request.build_opener(NoRedirect())
    results = []
    blocked = set()
    for url in dict.fromkeys(urls):
        result = {'url': url}
        try:
            if not approved(url):
                raise ValueError('URL outside explicit official HTTPS allowlist')
            origin = 'https://' + urllib.parse.urlsplit(url).netloc
            if origin in blocked:
                raise ValueError('Origin blocked earlier in this run')
            robots, _ = read(opener, origin + '/robots.txt')
            rp = urllib.robotparser.RobotFileParser()
            rp.parse(robots.decode('utf-8').splitlines())
            if not rp.can_fetch(AGENT, url):
                raise ValueError('robots.txt disallows request')
            time.sleep(max(2, rp.crawl_delay(AGENT) or 0))
            data, mime = read(opener, url)
            suffix = {'text/html': '.html', 'application/pdf': '.pdf', 'text/plain': '.txt'}.get(mime)
            if suffix is None:
                raise ValueError('Unsupported content type')
            sha = hashlib.sha256(data).hexdigest()
            path = output / (sha + suffix)
            path.write_bytes(data)
            result.update(status='downloaded', path=str(path), sha256=sha)
        except urllib.error.HTTPError as exc:
            result.update(status='http_error', http_status=exc.code)
            if exc.code in (401, 403, 429):
                blocked.add('https://' + urllib.parse.urlsplit(url).netloc)
        except (ValueError, urllib.error.URLError, TimeoutError, UnicodeError) as exc:
            result.update(status='skipped', reason=str(exc)[:200])
        results.append(result)
        time.sleep(2)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', help='Text file with explicit official URLs, one per line')
    parser.add_argument('--output', default='build/snapshots')
    args = parser.parse_args()
    urls = [line.strip() for line in Path(args.sources).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')]
    results = gather(urls, args.output)
    Path(args.output, 'fetch-report.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({'downloaded': sum(r['status'] == 'downloaded' for r in results), 'checked': len(results)}))


if __name__ == '__main__':
    main()
