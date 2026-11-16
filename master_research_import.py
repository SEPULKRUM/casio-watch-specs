"""Import a supplied model/module ZIP without authenticating its source claims.

CSV is authoritative for intake fidelity; SQLite and the identifier text are
cross-checked. No archive paths are extracted and no uploaded code is executed.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import reference_import
import specs

REFERENCE = 'research/casio-master-research-2026-11-16.json'
IMPORT = 'imports/zzzzzzzzzzzzzzzzzzzzzzz-master-research-2026-11-16.json'
DEFAULTS = {
    'source_presence': 'master text',
    'reference_type': 'individual identifier (not independently authenticated)',
    'field_verification_status': 'Unresearched - source identifier only',
}
LIMITS = [
    'Owner-supplied research, not independent verification. Verification labels inside the upload are the compiler\'s claims only; all imported facts remain pending review.',
    'Identifier-only entries are not complete specification records. Combined parts/fitment references stay intact and are never split into invented watch SKUs.',
    'Blank CSV fields mean unknown, not zero or absent. Partial release years/months retain their precision and market qualifications.',
    'Model-to-module associations are separate from module functions. A shared module does not establish an individual variant\'s case, band, weight or display.',
    'Source keys and cited URLs are preserved as supplied; underlying documents named in the register are not assumed received or independently checked.',
    'Stopwatch maximum display in seconds is a capacity, not a measurement-accuracy claim. Reception limits distinguish China and stop after success where stated.',
    'All existing catalog values are retained. Differing supplied candidates are shown in the research comparison list, not used to silently replace earlier facts.',
]


def eligible(row):
    return ('combined/parts' not in row.get('reference_type', '')
            and bool(reference_import.MODEL.fullmatch(row['model_id'])))


def expand_model(note, row):
    return {key: row.get(key, note['model_defaults'].get(key, '')) for key in note['model_columns']}


def load_bundle(path):
    with zipfile.ZipFile(path) as archive:
        if any(i.file_size > 20 * 1024 * 1024 for i in archive.infolist()):
            raise ValueError('Unexpected archive member size')
        names = archive.namelist()
        expected = {'README.txt', 'Casio_All_Model_Numbers_UPDATED.txt', 'Casio_Models_Master_Enriched.csv',
                    'Casio_Modules_Functions.csv', 'Casio_Model_Module_Relationships.csv',
                    'Casio_Sources.csv', 'Casio_Models_Modules.sqlite', 'Casio_Model_Research_Text_Only.pdf'}
        if set(names) != expected or len(names) != len(expected):
            raise ValueError('Unexpected or duplicate archive members')
        files = {name: archive.read(name) for name in names}
    def table(name):
        return list(csv.DictReader(io.StringIO(files[name].decode('utf-8-sig'))))
    models = table('Casio_Models_Master_Enriched.csv')
    modules = table('Casio_Modules_Functions.csv')
    mappings = table('Casio_Model_Module_Relationships.csv')
    sources = table('Casio_Sources.csv')
    for rows, key in [(models, 'model_id'), (modules, 'module_reference_number'), (sources, 'source_key')]:
        if len({r[key] for r in rows}) != len(rows):
            raise ValueError('Duplicate source identity')
    lines = files['Casio_All_Model_Numbers_UPDATED.txt'].decode('utf-8-sig').splitlines()
    if lines != [r['model_id'] for r in models]:
        raise ValueError('Text index differs from CSV order or identifiers')
    with tempfile.TemporaryDirectory() as temp:
        db = Path(temp) / 'source.sqlite'
        db.write_bytes(files['Casio_Models_Modules.sqlite'])
        with sqlite3.connect('file:' + str(db) + '?mode=ro', uri=True) as connection:
            connection.row_factory = sqlite3.Row
            for name, rows, keys in [('watch_models', models, ['model_id']),
                                      ('modules', modules, ['module_reference_number']),
                                      ('model_module_map', mappings, ['model_id', 'module_reference_number']),
                                      ('sources', sources, ['source_key'])]:
                values = [dict(r) for r in connection.execute('SELECT * FROM ' + name)]
                order = lambda r: tuple(r[k] for k in keys)
                if sorted(values, key=order) != sorted(rows, key=order):
                    raise ValueError('SQLite differs from CSV: ' + name)
    ids = {r['model_id'] for r in models}
    if any(r['model_id'] not in ids or not re.fullmatch(r'\d{2,4}', r['module_reference_number']) for r in mappings):
        raise ValueError('Invalid mapping identity')
    grouped = defaultdict(set)
    for row in mappings:
        grouped[row['model_id']].add(row['module_reference_number'])
    for row in models:
        if row['module_reference_number'] and set(filter(None, row['module_reference_number'].split(';'))) != grouped[row['model_id']]:
            raise ValueError('Primary CSV mapping disagrees with relationship table')
    sparse = [{k: v for k, v in r.items() if v and v != DEFAULTS.get(k)} for r in models]
    report_notes = [
        {'pdf_page': 1, 'text': 'GAC-2500 resin: 46.7 × 44.5 × 12.7 mm / 47 g. GMC-2500 resin strap: 46.7 × 43.8 × 12.9 mm / 68 g; GMC-2500D bracelet: 138 g. Case and mass profiles are not interchangeable.'},
        {'pdf_page': 1, 'text': 'GWF-D1000BC-1 is reported at 181 g with composite bracelet; do not reuse the 141 g resin-band Frogman weight.'},
        {'pdf_page': 1, 'text': 'The report cites the regional GW-9503KJ-2JR Japan listing for 2026-11, 88 g and 56.7 × 52.7 × 14.8 mm. CSV uses GW-9503KJ-2. Other editions do not automatically inherit this mass; the regional suffix association remains supplied research.'},
        {'pdf_page': 1, 'text': 'Modules 3260 / 3280 share a guide but can differ in LCD polarity. GW-9300 variant assignments to 3260 are provisional pending exact case-back checks.'},
        {'pdf_page': 1, 'text': 'Module 3445 maximum stopwatch display is reported as 99:59:59.99 (359999.99 seconds); module 3410 as 999:59:59.99 (3599999.99 seconds).'},
        {'pdf_page': 6, 'text': 'All numeric stopwatch and timer capacities are seconds. Missing values remain unknown. An empty automatic-attempt count does not mean automatic calibration is absent.'},
    ]
    return {
        'type': 'user_watch_specifications', 'provided_by': 'Repository owner', 'received': '2026-11-16',
        'archive': {'filename': Path(path).name.removeprefix('1-'), 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()},
        'members': {n: {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in files.items()},
        'cross_checks': {'csv_matches_sqlite': True, 'text_index_matches_csv_in_order': True},
        'relationship_only_associations': [{'model_id': row['model_id'], 'module_ids': sorted(grouped[row['model_id']]), 'note': 'Primary model CSV module cell is blank; separate relationship table supplies these historical associations'} for row in models if not row['module_reference_number'] and grouped[row['model_id']]],
        'model_columns': list(models[0]), 'model_defaults': DEFAULTS, 'models': sparse,
        'modules': modules, 'relationships': mappings, 'source_register': sources,
        'limits': LIMITS, 'report_notes': report_notes,
        'counts': {'raw_references': len(models), 'combined_fitment_references': sum('combined/parts' in r['reference_type'] for r in models),
                   'schema_compatible_individual_references': sum(eligible(r) for r in models),
                   'other_unresolved_individual_readings': sum(not eligible(r) and 'combined/parts' not in r['reference_type'] for r in models),
                   'module_profiles': len(modules), 'relationships': len(mappings), 'models_with_module_reference': len(grouped) - sum(not v for v in grouped.values()),
                   'models_with_case_source': sum(bool(r['case_spec_evidence']) for r in models), 'source_keys': len(sources)},
    }


def number(value):
    result = float(value)
    return int(result) if result.is_integer() else result


def model_values(row):
    values = {}
    family = row['family']
    if family:
        if any(word in family.upper() for word in ['G-SHOCK', 'RANGEMAN', 'MUDMAN', 'FROGMAN', 'VINTAGE 80XX']): values['series'] = 'G-SHOCK'
        elif 'OCEANUS' in family.upper(): values['series'] = 'Oceanus'
    evidence = row['case_spec_evidence'].lower()
    shared = any(word in evidence for word in ['family dimension', 'series rating', 'platform;'])
    if not shared:
        if all(row[k] for k in ['case_length_mm', 'case_width_mm', 'case_height_mm']):
            values['dimensions_mm'] = dict(zip(['length', 'width', 'thickness'], [number(row[k]) for k in ['case_length_mm', 'case_width_mm', 'case_height_mm']]))
        for source, field in [('weight_g', 'weight_g'), ('case_bezel_material', 'case_material'), ('band_material', 'band_material'), ('glass', 'glass'), ('water_resistance', 'water_resistance_rating')]:
            if row[source]: values[field] = number(row[source]) if field == 'weight_g' else row[source]
    if row['color']: values['color'] = row['color']
    return values


def module_values(row):
    values = {}
    for source, field in [('accuracy_seconds_per_month', 'accuracy_seconds_per_month'), ('accuracy_condition', 'accuracy_condition'), ('world_time_cities', 'world_time_cities'), ('world_time_zones', 'world_time_zones'), ('alarms', 'alarm_count'), ('power_supply', 'power_supply'), ('illumination', 'illumination')]:
        if row[source] and (field not in {'world_time_cities', 'world_time_zones', 'alarm_count', 'accuracy_seconds_per_month'} or re.fullmatch(r'\d+(?:\.\d+)?', row[source])):
            values[field] = number(row[source]) if field in {'world_time_cities', 'world_time_zones', 'alarm_count', 'accuracy_seconds_per_month'} else row[source]
    if row['snooze_alarm'].startswith(('Yes', 'No')): values['snooze_alarm'] = row['snooze_alarm'].startswith('Yes')
    for field, columns in {
        'stopwatch': ['stopwatch_resolution_seconds', 'stopwatch_max_display_seconds'],
        'timer': ['countdown_resolution_seconds', 'countdown_min_seconds', 'countdown_max_seconds', 'countdown_setting_increments_seconds'],
        'calendar': ['calendar_type', 'calendar_start_year', 'calendar_end_year'],
        'radio_reception': ['radio_reception_automatic', 'radio_reception_manual', 'radio_max_automatic_attempts_per_day', 'radio_max_automatic_attempts_per_day_china', 'radio_remaining_attempts_cancelled_after_success', 'radio_signals'],
    }.items():
        value = {k: number(row[k]) if re.fullmatch(r'\d+(?:\.\d+)?', row[k]) else row[k] for k in columns if row[k]}
        if value: values[field] = value
    return values


def proposals(note, baseline):
    records, comparisons = [], []
    relations = defaultdict(list)
    for i, row in enumerate(note['relationships'], 2): relations[row['model_id']].append(dict(row, csv_row=i))
    for kind, rows in [('model', note['models']), ('module', note['modules'])]:
        for index, sparse in enumerate(rows, 2):
            row = expand_model(note, sparse) if kind == 'model' else sparse
            key = row['model_id'] if kind == 'model' else row['module_reference_number']
            if kind == 'model' and (not eligible(row) or (not relations[key] and not any(row[k] for k in row if k not in {'model_id', *DEFAULTS}))):
                continue
            existing = baseline['models' if kind == 'model' else 'modules'].get(key, {})
            values = model_values(row) if kind == 'model' else module_values(row)
            if kind == 'model' and relations[key]:
                ids = list(dict.fromkeys(r['module_reference_number'] for r in relations[key]))
                values['module_id' if len(ids) == 1 else 'module_candidates'] = ids[0] if len(ids) == 1 else ids
            accepted, differences = {}, []
            for field, value in values.items():
                previous = existing.get('specs', {}).get(field, {}).get('value')
                if field in {'module_id', 'module_candidates'}:
                    previous = (existing.get('specs', {}).get('module_id', {}).get('value') or existing.get('specs', {}).get('module_candidates', {}).get('value') or existing.get('module'))
                if previous is None: accepted[field] = value
                elif previous != value:
                    difference = {'field': field, 'existing': previous, 'reported': value, 'disposition': 'Earlier value retained; supplied candidate awaits review'}
                    differences.append(difference);comparisons.append(dict(difference, kind=kind, id=key))
            field = 'master_research_reference' if kind == 'model' else 'master_module_reference'
            detail = {'source_csv': 'Casio_Models_Master_Enriched.csv' if kind == 'model' else 'Casio_Modules_Functions.csv', 'csv_row': index,
                      'reported_fields': {k: v for k, v in row.items() if v},
                      'verification': 'Supplied research only; compiler verification labels are not independent review'}
            if kind == 'model' and relations[key]: detail['reported_module_relationships'] = relations[key]
            if kind == 'module': detail['report_pdf_page'] = index + 4
            if differences: detail['existing_field_differences'] = differences
            accepted[field] = detail
            records.append({'kind': kind, 'id': key, 'specs': {f: {'value': v, 'uncertainty': LIMITS[0] + ' ' + ('Physical, release and module scope qualifiers remain in the supplied research field.' if kind == 'model' else 'Maximum stopwatch display is a capacity; unknown timing/reception values stay blank.'), 'sources': []} for f, v in accepted.items()}})
    note['comparisons'] = comparisons
    note['claims'] = [{'kind': r['kind'], 'id': r['id'], 'field': field, 'value': fact['value']} for r in records for field, fact in r['specs'].items()]
    checksum = specs.digest(note)
    for record in records:
        detail = record['specs']['master_research_reference' if record['kind'] == 'model' else 'master_module_reference']['value']
        for field, fact in record['specs'].items():
            fact['sources'] = [{'kind': 'user_provided', 'reference': REFERENCE, 'provided_by': note['provided_by'], 'source_sha256': checksum,
                                'permission': 'user_provided', 'accessed': note['received'], 'locator': detail['source_csv'] + ' / row ' + str(detail['csv_row']),
                                'evidence': record['id'] + ' / ' + field + '; exact supplied value and source qualifiers retained in research JSON'}]
        specs.validate(record)
    return records


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip');p.add_argument('--baseline', default='data/catalog.json');p.add_argument('--root', default='.')
    args = p.parse_args();root = Path(args.root)
    note = load_bundle(args.zip)
    base_references = json.loads((root / 'data/model-references.json').read_text())
    note['counts']['combined_model_reference_strings'] = len(set(base_references['models']) | {r['model_id'] for r in note['models'] if eligible(expand_model(note, r))})
    records = proposals(note, json.loads(Path(args.baseline).read_text()))
    specs.write(root / REFERENCE, note);specs.write(root / IMPORT, records)
    print(json.dumps(dict(note['counts'], enriched_catalog_models=sum(r['kind'] == 'model' for r in records), comparisons=len(note['comparisons'])), indent=2))

if __name__ == '__main__': main()
