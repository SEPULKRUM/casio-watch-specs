"""Build, search and export the source-backed Casio catalog without dependencies."""
import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

import specs


def preserve_verified(previous, current):
    if previous.get('legacy_watches') != current.get('legacy_watches'):
        raise ValueError('Legacy data changed; explicit migration review required')
    for bucket in ('models', 'modules'):
        for key, record in previous[bucket].items():
            for field, fact in record['specs'].items():
                if fact['status'] == 'verified':
                    new = current[bucket].get(key, {}).get('specs', {}).get(field)
                    if new != fact:
                        raise ValueError(f'Cannot change or remove verified fact: {bucket}/{key}/{field}')


def field_value(record, name, verified_only=False):
    fact = record['specs'].get(name)
    if fact is None or (verified_only and fact['status'] != 'verified'):
        return None
    return fact['value']


def search(catalog, query='', series=None, verified_only=False):
    records = []
    for model in catalog['models'].values():
        if series and str(field_value(model, 'series', verified_only)).casefold() != series.casefold():
            continue
        if verified_only and not any(f['status'] == 'verified' for f in model['specs'].values()):
            continue
        values = {k: fact['value'] for k, fact in model['specs'].items()
                  if not verified_only or fact['status'] == 'verified'}
        if query.casefold() not in (model['id'] + ' ' + json.dumps(values, ensure_ascii=False)).casefold():
            continue
        # Do not leak pending fields into verified-only search results.
        record = dict(model, specs={k: f for k, f in model['specs'].items()
                                   if not verified_only or f['status'] == 'verified'})
        records.append(record)
    return sorted(records, key=lambda r: r['id'])


def coverage(catalog):
    models = catalog['models']
    counts = Counter(f['status'] for bucket in ('models', 'modules')
                     for record in catalog[bucket].values() for f in record['specs'].values())
    series = Counter(field_value(r, 'series') or 'Unclassified' for r in models.values())
    fields = ('dimensions_mm', 'weight_g', 'case_material', 'band_material', 'glass', 'water_resistance_rating')
    missing = {r['id']: [f for f in fields if f not in r['specs']] for r in models.values()}
    unknown_links = sorted(r['id'] for r in models.values()
                           if 'module' not in r and 'module_id' not in r['specs'])
    return {'models': len(models), 'modules': len(catalog['modules']),
            'facts_by_status': dict(sorted(counts.items())),
            'models_by_series': dict(sorted(series.items())),
            'models_missing_fields': {k: v for k, v in sorted(missing.items()) if v},
            'models_without_module_link': unknown_links,
            'note': 'Coverage counts include pending candidates; unknown does not mean absent.'}


def spreadsheet_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def export_csv(catalog):
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    writer.writerow(['model', 'series', 'module', 'length_mm', 'width_mm', 'thickness_mm',
                     'weight_g', 'water_resistance_rating', 'water_resistance_m', 'water_resistance_bar',
                     'case_material', 'case_finish', 'band_material', 'glass',
                     'verified_facts', 'pending_facts', 'source_urls'])
    for record in search(catalog):
        value = lambda name: field_value(record, name)
        dims = value('dimensions_mm') or {}
        facts = record['specs'].values()
        urls = sorted({source['url'] for fact in facts for source in fact['sources']})
        row = [record['id'], value('series'), value('module_id') or record.get('module'),
               dims.get('length'), dims.get('width'), dims.get('thickness'), value('weight_g'),
               value('water_resistance_rating'), value('water_resistance_m'), value('water_resistance_bar'),
               value('case_material'), value('case_finish'), value('band_material'), value('glass'),
               sum(f['status'] == 'verified' for f in facts),
               sum(f['status'] == 'pending_review' for f in facts), ' | '.join(urls)]
        writer.writerow(['' if v is None else spreadsheet_safe(v) for v in row])
    return out.getvalue()


def build_catalog(root=Path('.')):
    paths = sorted((root / 'imports').glob('*.json'))
    if not paths:
        raise ValueError('No imports found')
    reviews_path = root / 'reviews.json'
    records = [record for path in paths for record in specs.load(path)]
    result = specs.build(specs.load(root / 'watches.json'), records,
                         specs.load(reviews_path) if reviews_path.exists() else None)
    if result['report']['conflicts']:
        raise ValueError('Conflicting facts: resolve before publishing catalog')
    prior = root / 'data/catalog.json'
    if prior.exists():
        preserve_verified(specs.load(prior), result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', default='data/catalog.json')
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--check', action='store_true', help='Fail if committed outputs differ')
    query = sub.add_parser('search')
    query.add_argument('query', nargs='?', default='')
    query.add_argument('--series')
    query.add_argument('--verified-only', action='store_true')
    show = sub.add_parser('show')
    show.add_argument('model')
    sub.add_parser('coverage')
    args = parser.parse_args()
    if args.command == 'build':
        catalog = build_catalog()
        outputs = {'data/catalog.json': json.dumps(catalog, ensure_ascii=False, indent=2) + '\n',
                   'data/coverage.json': json.dumps(coverage(catalog), ensure_ascii=False, indent=2) + '\n',
                   'data/watches.csv': export_csv(catalog)}
        for name, content in outputs.items():
            path = Path(name)
            if args.check:
                if not path.exists() or path.read_bytes() != content.encode():
                    raise SystemExit(f'Stale generated output: {path}; run python catalog.py build')
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                temp = path.with_suffix(path.suffix + '.tmp')
                temp.write_bytes(content.encode())
                temp.replace(path)
        print(json.dumps(coverage(catalog), ensure_ascii=False, indent=2))
        return
    catalog = specs.load(args.catalog)
    if args.command == 'search':
        result = search(catalog, args.query, args.series, args.verified_only)
    elif args.command == 'show':
        key = specs.identity(args.model)
        if key not in catalog['models']:
            raise SystemExit(f'Unknown model: {key}')
        model = catalog['models'][key]
        module_id = field_value(model, 'module_id') or model.get('module')
        result = {'model': model, 'module': catalog['modules'].get(str(module_id)),
                  'module_link_status': model.get('specs', {}).get('module_id', {}).get('status',
                       'legacy_preserved' if model.get('module') else 'unknown')}
    else:
        result = coverage(catalog)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
