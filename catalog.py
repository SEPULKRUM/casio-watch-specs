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


def module_view(catalog, model):
    module_id = field_value(model, 'module_id') or model.get('module')
    candidates = field_value(model, 'module_candidates') or []
    status = ('ambiguous_' + model['specs']['module_candidates']['status'] if candidates else
              model.get('specs', {}).get('module_id', {}).get('status',
                  'legacy_preserved' if model.get('module') else 'unknown'))
    link_fact = model['specs'].get('module_id') or model['specs'].get('module_candidates')
    kinds = {source.get('kind', 'web') for source in link_fact['sources']} if link_fact else set()
    provenance = (next(iter(kinds)) if len(kinds) == 1 else 'mixed') if kinds else ('legacy' if model.get('module') else 'unknown')
    return {'module': catalog['modules'].get(str(module_id)) if module_id else None,
            'module_id': str(module_id) if module_id else None,
            'module_candidates': candidates,
            'module_options': {key: catalog['modules'].get(key) for key in candidates},
            'module_link_status': status, 'module_link_provenance': provenance}


def coverage(catalog):
    models = catalog['models']
    counts = Counter(f['status'] for bucket in ('models', 'modules')
                     for record in catalog[bucket].values() for f in record['specs'].values())
    series = Counter(field_value(r, 'series') or 'Unclassified' for r in models.values())
    fields = ('dimensions_mm', 'weight_g', 'case_material', 'band_material', 'glass', 'water_resistance_rating')
    missing = {r['id']: [f for f in fields if f not in r['specs']] for r in models.values()}
    unknown_links = sorted(r['id'] for r in models.values()
                           if 'module' not in r and 'module_id' not in r['specs'])
    ambiguous = {r['id']: field_value(r, 'module_candidates') for r in models.values()
                 if field_value(r, 'module_candidates')}
    referenced = {key for r in models.values() for key in
                  ([str(field_value(r, 'module_id') or r.get('module'))]
                   if field_value(r, 'module_id') or r.get('module') else [])}
    user_links = {key: field_value(record, 'module_id') for key, record in models.items()
                  if module_view(catalog, record)['module_link_provenance'] == 'user_provided'}
    module_fields = Counter(field for record in catalog['modules'].values() for field in record['specs'])
    profile_sizes = Counter(str(len(record['specs'])) for record in catalog['modules'].values())
    return {'models': len(models), 'modules': len(catalog['modules']),
            'facts_by_status': dict(sorted(counts.items())),
            'models_by_series': dict(sorted(series.items())),
            'models_missing_fields': {k: v for k, v in sorted(missing.items()) if v},
            'models_without_module_link': unknown_links,
            'models_with_single_module_reference': len(models) - len(unknown_links),
            'user_provided_module_references': dict(sorted(user_links.items())),
            'models_with_ambiguous_manual': dict(sorted(ambiguous.items())),
            'models_without_any_module_reference': sorted(set(unknown_links) - set(ambiguous)),
            'referenced_module_ids_without_specs': sorted(referenced - set(catalog['modules'])),
            'candidate_module_ids_without_specs': sorted({key for values in ambiguous.values()
                                                         for key in values} - set(catalog['modules'])),
            'module_field_coverage': dict(sorted(module_fields.items())),
            'module_profiles_by_fact_count': dict(sorted(profile_sizes.items(), key=lambda p: int(p[0]))),
            'modules_with_sparse_profiles': sorted(key for key, record in catalog['modules'].items()
                                                  if len(record['specs']) < 4),
            'note': 'Coverage counts include pending candidates; unknown does not mean absent.'}


def spreadsheet_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) else text


def export_csv(catalog):
    out = io.StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(['model', 'series', 'module', 'module_candidates', 'module_link_status', 'module_link_provenance', 'length_mm', 'width_mm', 'thickness_mm',
                     'weight_g', 'water_resistance_rating', 'water_resistance_m', 'water_resistance_bar',
                     'case_material', 'case_finish', 'band_material', 'glass',
                     'verified_facts', 'pending_facts', 'source_urls', 'source_references'])
    for record in search(catalog):
        value = lambda name: field_value(record, name)
        dims = value('dimensions_mm') or {}
        facts = record['specs'].values()
        urls = sorted({source['url'] for fact in facts for source in fact['sources'] if source.get('url')})
        references = sorted({source['reference'] for fact in facts for source in fact['sources'] if source.get('reference')})
        view = module_view(catalog, record)
        row = [record['id'], value('series'), view['module_id'],
               ' | '.join(view['module_candidates']), view['module_link_status'], view['module_link_provenance'],
               dims.get('length'), dims.get('width'), dims.get('thickness'), value('weight_g'),
               value('water_resistance_rating'), value('water_resistance_m'), value('water_resistance_bar'),
               value('case_material'), value('case_finish'), value('band_material'), value('glass'),
               sum(f['status'] == 'verified' for f in facts),
               sum(f['status'] == 'pending_review' for f in facts), ' | '.join(urls), ' | '.join(references)]
        writer.writerow(['' if v is None else spreadsheet_safe(v) for v in row])
    return out.getvalue()


def validate_user_evidence(root, records):
    cache = {}
    for record in records:
        for field, fact in record['specs'].items():
            for source in fact['sources']:
                if source.get('kind') != 'user_provided':
                    continue
                # Validate reference paths before accessing any file.
                specs.validate(record)
                reference = source['reference']
                if reference not in cache:
                    cache[reference] = specs.load(root / reference)
                note = cache[reference]
                if (specs.digest(note) != source['source_sha256']
                        or note.get('type') != 'user_module_associations'
                        or note.get('provided_by') != source['provided_by']):
                    raise ValueError('User evidence is stale or attribution does not match')
                if (record['kind'] != 'model' or field != 'module_id'
                        or not any(specs.identity(row['model']) == specs.identity(record['id'])
                                   and row['module'] == fact['value'] for row in note['mappings'])):
                    raise ValueError('User citation does not contain this model/module mapping')


def build_catalog(root=Path('.')):
    paths = sorted((root / 'imports').glob('*.json'))
    if not paths:
        raise ValueError('No imports found')
    reviews_path = root / 'reviews.json'
    records = [record for path in paths for record in specs.load(path)]
    validate_user_evidence(root, records)
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
        result = {'model': model, **module_view(catalog, model)}
    else:
        result = coverage(catalog)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
