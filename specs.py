"""Source-backed bulk candidate pipeline. Standard library; PDF extraction uses pdftotext."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

MODEL_FIELDS = {'dimensions_mm', 'weight_g', 'water_resistance_m', 'case_material',
                'band_material', 'glass', 'color', 'series', 'release_date', 'module_id', 'module_candidates', 'water_resistance_rating', 'water_resistance_bar', 'case_finish',
                'promotional_thickness_mm', 'technical_table_thickness_mm', 'display_polarity', 'catalog_year', 'catalog_description', 'catalog_material_finish'}
MODULE_FIELDS = {'accuracy_seconds_per_month', 'accuracy_condition', 'power_supply',
                 'world_time_cities', 'world_time_zones', 'alarm_count', 'snooze_alarm',
                 'stopwatch', 'timer', 'illumination', 'calendar', 'radio_reception', 'display_polarity',
                 'depth_meter', 'digital_compass', 'thermometer', 'dive_log', 'tide_moon', 'battery_cell', 'catalog_reference', 'catalog_features'}


def identity(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Identity must be a nonempty string')
    return re.sub(r'\s+', '', value).upper().replace('−', '-').replace('–', '-')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def validate_archive_source(source):
    """Bind a Wayback citation to its exact dated official Casio original."""
    from datetime import datetime, date
    match = re.fullmatch(r'https://web\.archive\.org/web/(\d{14})/(https?://.+)', source.get('url', ''))
    if not match:
        raise ValueError('Archive citation requires a timestamped HTTPS Wayback replay URL')
    timestamp, original = match.groups()
    captured = datetime.strptime(timestamp, '%Y%m%d%H%M%S')
    parsed = urlsplit(original)
    hosts = {'www.casio.com', 'casio.com', 'www.casio-europe.com', 'casio-europe.com',
             'support.casio.com', 'support.casio.jp'}
    if (parsed.hostname not in hosts or parsed.username or parsed.password
            or parsed.port not in (None, 80, 443) or parsed.fragment):
        raise ValueError('Archive original must be an official Casio URL without credentials')
    if (source.get('original_url') != original or source.get('archive_timestamp') != timestamp
            or source.get('permission') != 'official_public_reference'
            or not re.fullmatch(r'[0-9a-f]{64}', source.get('snapshot_sha256', ''))):
        raise ValueError('Archive citation requires matching original, timestamp and snapshot checksum')
    if captured.date() > date.fromisoformat(source.get('accessed', '')):
        raise ValueError('Archive capture cannot postdate access')


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
    if record['kind'] == 'module' and not re.fullmatch(r'\d{2,4}', key):
        raise ValueError('Module ID must have 2 to 4 digits')
    if not record.get('specs') or not isinstance(record['specs'], dict):
        raise ValueError('Nonempty specs object required')
    allowed = MODEL_FIELDS if record['kind'] == 'model' else MODULE_FIELDS
    if set(record['specs']) - allowed:
        raise ValueError('Unknown or incorrectly scoped specification')
    if {'module_id', 'module_candidates'} <= set(record['specs']):
        raise ValueError('Cannot assert a single module and ambiguous alternatives together')
    for field, fact in record['specs'].items():
        if not isinstance(fact, dict) or fact.get('value') is None:
            raise ValueError(f'{field}: value required')
        if field in {'weight_g', 'water_resistance_m', 'water_resistance_bar', 'accuracy_seconds_per_month',
                     'world_time_cities', 'world_time_zones', 'alarm_count',
                     'promotional_thickness_mm', 'technical_table_thickness_mm'}:
            value = fact['value']
            import math
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f'{field}: finite nonnegative number required')
            if field in {'promotional_thickness_mm', 'technical_table_thickness_mm'} and value == 0:
                raise ValueError(f'{field}: positive thickness required')
        if field == 'dimensions_mm':
            value = fact['value']
            import math
            if (not isinstance(value, dict) or set(value) != {'length', 'width', 'thickness'}
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in value.values())):
                raise ValueError('dimensions_mm requires positive length, width and thickness')
        if field == 'snooze_alarm' and not isinstance(fact['value'], bool):
            raise ValueError('snooze_alarm must be boolean')
        if field == 'display_polarity' and (not isinstance(fact['value'], str)
                                           or fact['value'] not in {'positive', 'negative'}):
            raise ValueError('display_polarity must be positive or negative')
        if field == 'module_candidates':
            value = fact['value']
            if (not isinstance(value, list) or len(value) < 2
                    or any(not isinstance(v, str) or not re.fullmatch(r'\d{2,4}', v) for v in value)
                    or len(set(value)) != len(value)):
                raise ValueError('module_candidates requires distinct documented module IDs')
        if field == 'module_id' and not re.fullmatch(r'\d{2,4}', str(fact['value'])):
            raise ValueError('module_id must identify a 2 to 4 digit module')
        if not isinstance(fact.get('uncertainty'), str):
            raise ValueError(f'{field}: explicit uncertainty string required')
        if not isinstance(fact.get('sources'), list) or not fact['sources']:
            raise ValueError(f'{field}: sources required')
        for source in fact['sources']:
            source_kind = source.get('kind', 'web')
            if source_kind == 'user_provided':
                from pathlib import PurePosixPath
                reference = source.get('reference', '')
                path = PurePosixPath(reference)
                if (not reference.startswith('research/') or path.is_absolute() or '..' in path.parts
                        or path.suffix != '.json' or source.get('permission') != 'user_provided'
                        or not isinstance(source.get('provided_by'), str) or not source['provided_by'].strip()
                        or not re.fullmatch(r'[0-9a-f]{64}', source.get('source_sha256', ''))):
                    raise ValueError('User evidence requires a research JSON reference, attribution and checksum')
                if source.get('url'):
                    raise ValueError('User evidence must not masquerade as a web citation')
            elif source_kind == 'web':
                url = urlsplit(source.get('url', ''))
                if url.scheme != 'https' or not url.hostname or url.username or url.password:
                    raise ValueError('Source must be an HTTPS URL without credentials')
                if url.hostname == 'shockbase.org' or url.hostname.endswith('.shockbase.org'):
                    raise ValueError('ShockBase excluded without permission')
                if source.get('permission') not in ('official_public_reference', 'licensed', 'permission_granted'):
                    raise ValueError('Source permission basis required')
                if (url.hostname == 'web.archive.org' or 'archive_timestamp' in source
                        or 'original_url' in source):
                    validate_archive_source(source)
            else:
                raise ValueError('Unknown source kind')
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
            other = 'module_candidates' if field == 'module_id' else 'module_id'
            if field in {'module_id', 'module_candidates'} and (
                    other in target['specs'] or (field == 'module_candidates' and 'module' in target)):
                catalog['report']['conflicts'].append({'kind': kind, 'id': key, 'field': field,
                    'existing': target['specs'].get(other, target.get('module')), 'incoming': incoming})
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
