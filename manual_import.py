"""Import batches of official manual research without guessing model/module links."""
import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

import specs

HOSTS = {'www.casio.com', 'support.casio.com', 'support.casio.jp'}


def official(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in HOSTS or parsed.username
            or parsed.password or parsed.port not in (None, 443)):
        raise ValueError('Manual research requires an approved official HTTPS URL')
    return parsed


def associations(notes):
    records = []
    for row in notes['observations']:
        if row['status'] != 'candidate':
            continue
        key = specs.identity(row['model'])
        if row.get('displayed_model') != row['model']:
            raise ValueError('Support-page model must exactly match the researched model')
        support = official(row['support_url'])
        manual = official(row['manual_url'])
        if '/support.' not in support.path:
            raise ValueError('Association requires a model-specific support page')
        candidates = row['module_candidates']
        if (not isinstance(candidates, list) or not candidates
                or any(not isinstance(v, str) or not re.fullmatch(r'\d{3,4}', v) for v in candidates)
                or len(set(candidates)) != len(candidates)):
            raise ValueError('Unique documented module identifiers required')
        target = re.search(r'/manual/(\d{3,4})_|/(\d{3,4})/(?:qw|pm)', manual.path)
        if not target or next(v for v in target.groups() if v) not in candidates:
            raise ValueError('Documented modules must include the official manual endpoint identifier')
        if not row.get('manual_identity_evidence'):
            raise ValueError('Manual identity evidence required')
        shared = len(candidates) > 1
        field = 'module_candidates' if shared else 'module_id'
        value = sorted(candidates, key=int) if shared else candidates[0]
        uncertainty = ('Shared guide covers these modules; exact watch module is unresolved'
                       if shared else 'Current official support reference; historical production revisions may differ')
        sources = [
            {'url': row['support_url'], 'accessed': notes['accessed'],
             'locator': 'Primary User’s Guide / Operation Guide link',
             'evidence': f'Support page for {key} links the cited manual',
             'linked_manual_url': row['manual_url'], 'displayed_model': row['displayed_model'],
             'permission': 'official_public_reference'},
            {'url': row['manual_url'], 'accessed': notes['accessed'],
             'locator': 'Manual identity / title and module-specific notes',
             'evidence': row['manual_identity_evidence'],
             'identity_basis': row['identity_basis'],
             'permission': 'official_public_reference'}]
        record = {'kind': 'model', 'id': key,
                  'specs': {field: {'value': value, 'uncertainty': uncertainty, 'sources': sources}}}
        specs.validate(record)
        records.append(record)
    return records


def module_facts(notes):
    records = []
    for row in notes['modules']:
        official(row['source_url'])
        facts = {}
        for field, value in row['specs'].items():
            facts[field] = {'value': value,
                'uncertainty': 'Official manual research transcription; independent review pending',
                'sources': [{'url': row['source_url'], 'accessed': notes['accessed'],
                    'locator': row['locator'],
                    'evidence': f'Module {row["id"]}: {field} = {value}',
                    'evidence_type': 'normalized_technical_fact',
                    'scope_note': row.get('scope_note', 'Module-specific specification'),
                    'permission': 'official_public_reference'}]}
        record = {'kind': 'module', 'id': row['id'], 'specs': facts}
        specs.validate(record)
        records.append(record)
    return records


def document_modules(url, text):
    """Conservative identity extraction: shared guides remain alternatives."""
    parsed = official(url)
    match = re.search(r'/manual/(\d{3,4})_|/(\d{3,4})/(?:qw|pm)', parsed.path)
    if not match:
        raise ValueError('No module-specific official manual endpoint')
    endpoint = next(value for value in match.groups() if value)
    header = re.search(r'(?:Operation Guide|QW[- ])\s*((?:\d{3,4})(?:[ /_]+\d{3,4})*)', text[:3000], re.I)
    declared = re.findall(r'\d{3,4}', header[1]) if header else []
    if declared and endpoint not in declared:
        raise ValueError('Manual contents do not match endpoint module')
    candidates = {endpoint, *declared}
    for match in re.finditer(r'Module(?: No\.)?\s*(\d{3,4}(?:[/_ ]+\d{3,4})*)', text, re.I):
        candidates.update(re.findall(r'\d{3,4}', match[1]))
    for match in re.finditer(r'(?<!\d)(\d{3,4})/(\d{3,4})(?!\d)', text):
        if endpoint in match.groups():
            candidates.update(match.groups())
    return sorted(candidates, key=int)


def from_snapshots(manifest_path):
    """Batch extraction from local support-page and linked-manual snapshots."""
    import hashlib
    import subprocess
    from html.parser import HTMLParser
    manifest = specs.load(manifest_path)
    root = Path(manifest_path).resolve().parent
    observations = []
    class Support(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_h1 = False
            self.titles = []
            self.parts = []
            self.links = set()
        def handle_starttag(self, tag, attrs):
            if tag == 'h1':
                self.in_h1, self.parts = True, []
            if tag == 'a' and dict(attrs).get('href'):
                self.links.add(dict(attrs)['href'])
        def handle_data(self, value):
            if self.in_h1:
                self.parts.append(value)
        def handle_endtag(self, tag):
            if tag == 'h1' and self.in_h1:
                self.titles.append(''.join(self.parts).strip())
                self.in_h1 = False
    for document in manifest['documents']:
        support_data = (root / document['support_path']).read_bytes()
        parser = Support()
        parser.feed(support_data.decode('utf-8'))
        if parser.titles != [document['model']]:
            raise ValueError('Support snapshot must show one exact model heading')
        from urllib.parse import urljoin
        links = {urljoin(document['support_url'], link) for link in parser.links}
        if document['manual_url'] not in links:
            raise ValueError('Manual must actually be linked by the support snapshot')
        path = root / document['manual_path']
        data = path.read_bytes()
        if path.suffix.lower() == '.pdf':
            text = subprocess.run(['pdftotext', '-layout', str(path), '-'],
                check=True, capture_output=True, text=True, timeout=60).stdout
        else:
            class Text(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.parts = []
                def handle_data(self, value):
                    self.parts.append(value)
            plain = Text()
            plain.feed(data.decode('utf-8'))
            text = ' '.join(plain.parts)
        if not text.strip():
            raise ValueError('Manual has no extractable text; review/OCR required')
        candidates = document_modules(document['manual_url'], text)
        observations.append({'model': document['model'], 'displayed_model': parser.titles[0],
            'status': 'candidate', 'support_url': document['support_url'],
            'manual_url': document['manual_url'], 'module_candidates': candidates,
            'identity_basis': 'shared_manual_body' if len(candidates) > 1 else 'official_manual_endpoint',
            'manual_identity_evidence': 'Snapshot module references: ' + ', '.join(candidates),
            'support_sha256': hashlib.sha256(support_data).hexdigest(),
            'manual_sha256': hashlib.sha256(data).hexdigest()})
    records = associations({'accessed': manifest['accessed'], 'observations': observations})
    for record, observation in zip(records, observations):
        record['specs'][next(iter(record['specs']))]['sources'][0]['snapshot_sha256'] = observation['support_sha256']
        record['specs'][next(iter(record['specs']))]['sources'][1]['snapshot_sha256'] = observation['manual_sha256']
    return records


def convert(notes):
    if notes['type'] == 'module_associations':
        return associations(notes)
    if notes['type'] == 'module_specifications':
        return module_facts(notes)
    raise ValueError('Unknown manual research batch type')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notes', nargs='?')
    parser.add_argument('--support-manifest')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if bool(args.notes) == bool(args.support_manifest):
        parser.error('Provide one notes file or --support-manifest')
    input_path = args.notes or args.support_manifest
    output = Path(args.output).resolve()
    if (output == Path(input_path).resolve() or output.name == 'watches.json'
            or output.parent.name == 'data'):
        parser.error('Output must be an import proposal, not a source or published catalog')
    records = from_snapshots(args.support_manifest) if args.support_manifest else convert(specs.load(args.notes))
    specs.write(output, records)


if __name__ == '__main__':
    main()
