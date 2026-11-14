"""Source-backed bulk candidate pipeline. Standard library; PDF extraction uses pdftotext."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

MODEL_FIELDS = {'dimensions_mm', 'weight_g', 'water_resistance_m', 'case_material',
                'band_material', 'glass', 'color', 'series', 'release_date', 'module_id'}
MODULE_FIELDS = {'accuracy_seconds_per_month', 'accuracy_condition', 'power_supply',
                 'world_time_cities', 'world_time_zones', 'alarm_count', 'snooze_alarm',
                 'stopwatch', 'timer', 'illumination', 'calendar', 'radio_reception'}


def identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Identity must be a nonempty string')
    return re.sub(r'\s+', '', value).upper().replace('−', '-').replace('–', '-')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def validate(record):
    if record.get('kind') not in ('model', 'module'):
        raise ValueError('kind must be model or module')
    key = identity(record['id'])
    if record['kind'] == 'module' and not re.fullmatch(r'\d{3,4}', key):
        raise ValueError('Module ID must have 3 or 4 digits')
    if not record.get('specs') or not isinstance(record['specs'], dict):
        raise ValueError('Nonempty specs object required')
    allowed = MODEL_FIELDS if record['kind'] == 'model' else MODULE_FIELDS
    if set(record['specs']) - allowed:
        raise ValueError('Unknown or incorrectly scoped specification')
    for field, fact in record['specs'].items():
        if not isinstance(fact, dict) or fact.get('value') is None:
            raise ValueError(f'{field}: value required')
        if field in {'weight_g', 'water_resistance_m', 'accuracy_seconds_per_month',
                     'world_time_cities', 'world_time_zones', 'alarm_count'}:
            value = fact['value']
            import math
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{field}: finite nonnegative number required')
        if field == 'module_id' and not re.fullmatch(r'\d{3,4}', str(fact['value'])):
            raise ValueError('module_id must identify a 3 or 4 digit module')
        if not isinstance(fact.get('uncertainty'), str):
            raise ValueError(f'{field}: explicit uncertainty string required')
        if not isinstance(fact.get('sources'), list) or not fact['sources']:
            raise ValueError(f'{field}: sources required')
        for source in fact['sources']:
            url = urlsplit(source.get('url', ''))
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Source must be an HTTPS URL without credentials')
            if url.hostname == 'shockbase.org' or url.hostname.endswith('.shockbase.org'):
                raise ValueError('ShockBase excluded without permission')
            if source.get('permission') not in ('official_public_reference', 'licensed', 'permission_granted'):
                raise ValueError('Source permission basis required')
            if not all(isinstance(source.get(k), str) and source[k].strip()
                       for k in ('accessed', 'locator', 'evidence')):
                raise ValueError('Source date, locator and evidence required')
            from datetime import date
            date.fromisoformat(source['accessed'])
    return record['kind'], key


def build(legacy, batches, decisions=None):
    """Rebuild deterministic proposal; never mutate legacy or overwrite a verified fact."""
    catalog = {'schema_version': 1, 'models': {}, 'modules': {},
               'legacy_watches': legacy, 'report': {'duplicates': [], 'conflicts': []}}
    for watch in legacy['watches']:
        key = identity(watch['model'])
        if key in catalog['models']:
            raise ValueError(f'Duplicate legacy model: {key}')
        catalog['models'][key] = {'id': key, 'module': str(watch['module']),
                                 'specs': {}, 'legacy_record_preserved': True}
    approvals = {}
    for decision in decisions or []:
        if not all(isinstance(decision.get(k), str) and decision[k].strip()
                   for k in ('candidate_sha256', 'reviewed_by', 'note')):
            raise ValueError('Review requires hash, reviewer and note')
        approvals[decision['candidate_sha256']] = decision
    seen = set()
    used_approvals = set()
    for record in batches:
        kind, key = validate(record)
        sha = digest(record)
        if sha in seen:
            catalog['report']['duplicates'].append({'id': key, 'sha256': sha})
            continue
        seen.add(sha)
        approved = sha in approvals
        if approved:
            used_approvals.add(sha)
        bucket = catalog['models' if kind == 'model' else 'modules']
        target = bucket.setdefault(key, {'id': key, 'specs': {}})
        for field, fact in record['specs'].items():
            incoming = dict(fact, status='verified' if approved else 'pending_review',
                            candidate_sha256=sha)
            if approved:
                incoming['review'] = approvals[sha]
            if field == 'module_id' and 'module' in target and str(fact['value']) != target['module']:
                catalog['report']['conflicts'].append({'kind': kind, 'id': key,
                    'field': field, 'existing': target['module'], 'incoming': incoming})
                continue
            current = target['specs'].get(field)
            if current is not None:
                if current['value'] != incoming['value']:
                    catalog['report']['conflicts'].append({'kind': kind, 'id': key,
                        'field': field, 'existing': current, 'incoming': incoming})
                else:
                    catalog['report']['duplicates'].append({'id': key, 'field': field})
                continue
            target['specs'][field] = incoming
    if set(approvals) - used_approvals:
        raise ValueError('Review decision references a missing or changed candidate')
    return catalog


def extract(manifest_path):
    """Extract explicitly located facts from permitted local HTML, text or PDF snapshots.

    Regex rules are source-specific and output candidates only. Snapshot paths resolve
    relative to the manifest; there is no speculative inference of model/module links.
    """
    manifest = load(manifest_path)
    records = []
    for entry in manifest['documents']:
        path = Path(manifest_path).resolve().parent / entry['path']
        if path.suffix.lower() == '.pdf':
            text = subprocess.run(['pdftotext', '-layout', str(path), '-'],
                                  check=True, capture_output=True, text=True, timeout=60).stdout
        else:
            text = path.read_text(encoding='utf-8')
            if path.suffix.lower() in ('.html', '.htm'):
                from html.parser import HTMLParser
                class Text(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.parts = []
                    def handle_data(self, value):
                        self.parts.append(value)
                parser = Text()
                parser.feed(text)
                text = ' '.join(parser.parts)
        text = re.sub(r'\s+', ' ', text)
        specs = {}
        for rule in entry['rules']:
            matches = list(re.finditer(rule['pattern'], text))
            if len(matches) != 1:
                raise ValueError(f"{path}: rule {rule['field']} matched {len(matches)} times")
            match = matches[0]
            value = match.group('value')
            if rule.get('type') == 'number':
                value = float(value)
            source = dict(entry['source'], evidence=match.group(0),
                          snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            specs[rule['field']] = {'value': value, 'sources': [source],
                                   'uncertainty': 'Automatic extraction; check context and units'}
        record = {'kind': entry['kind'], 'id': entry['id'], 'specs': specs}
        validate(record)
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    ex = sub.add_parser('extract')
    ex.add_argument('manifest')
    ex.add_argument('--output', required=True)
    build_parser = sub.add_parser('build')
    build_parser.add_argument('imports', nargs='+')
    build_parser.add_argument('--legacy', default='watches.json')
    build_parser.add_argument('--reviews')
    build_parser.add_argument('--output', default='build/catalog.json')
    args = parser.parse_args()
    protected = {Path('watches.json').resolve(), Path('collector.py').resolve(),
                 Path('sources.txt').resolve(), Path('.github/workflows/collect.yml').resolve()}
    inputs = [args.manifest] if args.command == 'extract' else [args.legacy, *args.imports, *([args.reviews] if args.reviews else [])]
    if Path(args.output).resolve() in protected | {Path(p).resolve() for p in inputs}:
        parser.error('Output must not overwrite protected files or inputs')
    if args.command == 'extract':
        write(args.output, extract(args.manifest))
    else:
        records = [record for path in args.imports for record in load(path)]
        result = build(load(args.legacy), records, load(args.reviews) if args.reviews else None)
        write(args.output, result)
        print(json.dumps(result['report']))
        if result['report']['conflicts']:
            raise SystemExit(2)


if __name__ == '__main__':
    main()
