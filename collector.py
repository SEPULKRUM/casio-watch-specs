"""SEPULKRUM Casio specification collector (safe starter).

Reads Casio product URLs from sources.txt (one URL per line), fetches publicly
accessible JSON-LD Product data, and writes review_candidates.json.
No unverified information is added to watches.json automatically.
Only use URLs whose automated access is permitted by the site's rules.
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / "sources.txt"
OUTPUT = ROOT / "review_candidates.json"
USER_AGENT = "SepulkrumWatchSpecsResearch/0.1 (respect robots.txt)"


class JsonLdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.inside = True
            self.parts = []

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.inside:
            self.blocks.append("".join(self.parts))
            self.inside = False


def product_nodes(obj):
    if isinstance(obj, list):
        for item in obj:
            yield from product_nodes(item)
    elif isinstance(obj, dict):
        typ = obj.get("@type", [])
        types = typ if isinstance(typ, list) else [typ]
        if "Product" in types:
            yield obj
        for key in ("@graph", "mainEntity"):
            if key in obj:
                yield from product_nodes(obj[key])


def allowed(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("casio.com", "www.casio.com"):
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return False  # Fail closed when permission cannot be checked


def collect(url):
    if not allowed(url):
        return {"source_url": url, "status": "skipped_not_permitted_or_unverified"}
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.url != url and not allowed(response.url):
                return {"source_url": url, "status": "skipped_redirect"}
            html = response.read(2_000_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"source_url": url, "status": "fetch_error", "error": str(exc)[:160]}
    parser = JsonLdParser()
    parser.feed(html)
    found = []
    for block in parser.blocks:
        try:
            for product in product_nodes(json.loads(block)):
                name = product.get("name")
                if isinstance(name, str) and name.strip():
                    found.append({"name": name.strip(), "sku": product.get("sku"),
                                  "model": product.get("model"), "description": product.get("description"),
                                  "source_url": url, "verification": "pending_manual_review"})
        except (ValueError, TypeError):
            continue
    return {"source_url": url, "status": "candidate_found" if found else "no_structured_product_data", "products": found}


def main():
    if not SOURCES.exists():
        SOURCES.write_text("# Add approved Casio product URLs, one per line.\n", encoding="utf-8")
    urls = [line.strip() for line in SOURCES.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]
    results = []
    for url in dict.fromkeys(urls):
        results.append(collect(url))
        time.sleep(2)
    OUTPUT.write_text(json.dumps({"generated_utc": datetime.now(timezone.utc).isoformat(),
                                  "note": "Candidates require verification; watches.json unchanged",
                                  "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(results)} URLs. Wrote {OUTPUT.name}. watches.json unchanged.")


if __name__ == "__main__":
    main()
