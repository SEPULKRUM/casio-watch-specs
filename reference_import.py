"""Build a deduplicated model-reference library from a local research intake.

Only identifiers and provenance are exported. No OCR transcripts, scans, product
images, prices, specification claims or letter expansions are copied.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MODEL = re.compile(r'(?:[A-Z]{1,5}-?[A-Z]{0,3}\d{1,5}[A-Z0-9]*(?:-[A-Z0-9]+){0,3}|\d{2,3}[A-Z]{1,4}-[A-Z0-9]+(?:-[A-Z0-9]+)?)$')
NOISE_PREFIXES = {'BR', 'CR', 'SR', 'LR', 'CTL', 'CTOS', 'UCC', 'VE', 'PAWI', 'DWO'}


def build(intake, observations):
    intake = Path(intake)
    models, sources, rejected = {}, {}, []
    def source(key, **fields):
        sources.setdefault(key, fields)
        return key
    def add(raw, origin, role, page=None, combined_page=None):
        model = str(raw).strip().upper().replace('−', '-').replace('–', '-')
        if len(model) > 40 or not MODEL.fullmatch(model):
            rejected.append({'model_string': model, 'reason': 'Malformed, shorthand or unresolved reading'})
            return
        prefix_match = re.match(r'[A-Z]+', model)
        prefix = prefix_match.group() if prefix_match else ''
        if role == 'machine_ocr' and prefix in NOISE_PREFIXES:
            rejected.append({'model_string': model, 'reason': 'Possible battery identifier or OCR noise; manual review required'})
            return
        row = models.setdefault(model, {'id': model, 'prefix': prefix, 'observations': []})
        item = {'source_id': origin, 'role': role}
        if page is not None: item['line' if role == 'research_note_mention' else 'pdf_page'] = page
        if combined_page is not None: item['compilation_page'] = combined_page
        if item not in row['observations']: row['observations'].append(item)
    def load(name): return json.loads((intake / name).read_text())
    for s in load('all_uploaded_source_manifest.json'):
        source('original:' + s['id'], filename=s['filename'], availability='original_not_in_received_seven_files', sha256=s.get('sha256'))
    cat_sources = {x['source_id']: x for x in load('catalog_sources.json')}
    for line in (intake / 'catalog_watch_records.jsonl').read_text().splitlines():
        if not line.strip(): continue
        row = json.loads(line)
        key = source('handoff:' + row['source_id'], filename=row.get('source_file') or cat_sources[row['source_id']]['filename'], availability='standalone_original_not_received; compilation_page_mapping_unverified')
        add(row.get('model', row.get('model_as_read')), key, 'supplied_transcription', row.get('pdf_page'))
    for row in load('model_mention_index_REVIEW_REQUIRED.json'):
        for model in row['model_strings']:
            add(model, 'original:' + row['source_id'], 'prior_machine_index', row['pdf_page'])
    # Include model examples from the remaining ZIP notes without copying their prose.
    note_pattern = re.compile(r'\b[A-Z]{1,5}(?:-[A-Z]{1,3})?-?\d{1,5}[A-Z0-9]*(?:-[A-Z0-9]+){0,3}\b')
    note_names = ['CASIO_MODEL_PREFIX_DECODER_MASTER.md', 'CODEX_START_HERE.md', 'CODEX_PREFIX_COLOR_UI_RULES.md', 'CODEX_OFFICIAL_PRODUCT_LINKS_INSTEAD_OF_IMAGES.md', 'FINAL_SOURCE_INTAKE.md', 'START_HERE_NEW_ARCHIVE.md', 'README_SOURCE_FILES.md', 'catalog_intake_log.md', 'UPLOAD_ORDER.txt']
    for name in note_names:
        path = intake / name
        if not path.exists(): continue
        text = path.read_text()
        key = source('note:' + name, filename=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), availability='received_zip_research_note; not_primary_model_evidence')
        for line_no, line in enumerate(text.splitlines(), 1):
            for model in note_pattern.findall(line):
                if model.startswith(('SHA-', 'UTF-')): continue
                add(model, key, 'research_note_mention', line_no)
    for name, field in [('prefix_interpretations.json', 'example_models'), ('color_code_evidence.json', 'examples')]:
        path = intake / name
        if not path.exists(): continue
        key = source('note:' + name, filename=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), availability='received_zip_research_note; not_primary_model_evidence')
        for row in json.loads(path.read_text()):
            for item in row.get(field, []):
                add(item['model'] if isinstance(item, dict) else item, key, 'research_note_mention')
    parts = load('received-source-summary.json')
    for part in parts:
        source('part:' + part['filename'], filename=part['filename'], sha256=part['sha256'], availability='received_pdf', pages=part['pages'])
    def part_for(page): return next(p for p in parts if p['combined_start_page'] <= page < p['combined_start_page'] + p['pages'])
    for row in load('page-registry.json'):
        part = part_for(row['combined_page'])
        for model in row['candidate_model_strings']:
            add(model, 'part:' + part['filename'], 'machine_ocr', row['source_pdf_page'], row['combined_page'])
    for page, values in observations['pages'].items():
        page = int(page); part = part_for(page)
        for model in values:
            add(model, 'part:' + part['filename'], 'checked_compilation_index', page-part['combined_start_page']+1, page)
    for model in models.values():
        roles = {o['role'] for o in model['observations']}
        model['status'] = 'index_checked' if 'checked_compilation_index' in roles else 'supplied_transcription' if 'supplied_transcription' in roles else 'machine_candidate'
        model['evidence_status'] = 'secondary_reported' if model['status'] == 'index_checked' else 'unverified'
        model['reading_flags'] = []
        if any(x in model['id'] for x in ['SPECI', 'WATCH', 'BOOK']): model['reading_flags'].append('suspicious_text_fragment')
        if re.search(r'(?:^|-)[A-Z]*0+(?:-|$)', model['id']): model['reading_flags'].append('possible_partial_or_ocr_identifier')
    used_sources = {o['source_id'] for m in models.values() for o in m['observations']}
    for s in used_sources:
        if s not in sources: raise ValueError('Unknown source: ' + s)
    counts = {s: sum(m['status'] == s for m in models.values()) for s in ['index_checked', 'supplied_transcription', 'machine_candidate']}
    return {'schema_version': 1, 'scope': 'Model/series strings only; not verified watch or specification records. Index checks do not establish official letter meanings. Candidate strings may be partial or false positives.',
            'counts': {'model_strings': len(models), **counts, 'rejected_occurrences': len(rejected)},
            'sources': {s: sources[s] for s in sorted(used_sources)},
            'models': dict(sorted(models.items()))}, rejected


def prefix_entries(library, existing):
    grouped = {}
    for model in library['models'].values():
        if model['prefix'] and (model['status'] != 'machine_candidate' or any(o['role'] in {'prior_machine_index', 'research_note_mention'} for o in model['observations'])):
            grouped.setdefault(model['prefix'], []).append(model)
    entries = []
    for prefix, models in sorted(grouped.items()):
        if prefix in existing:
            continue
        models.sort(key=lambda m: (m['status'] != 'index_checked', m['status'] != 'supplied_transcription', m['id']))
        checked = any(m['status'] == 'index_checked' for m in models)
        historical = any(any(o['role'] in {'supplied_transcription', 'checked_compilation_index'} for o in m['observations']) for m in models)
        evidence = 'secondary_reported' if checked else 'unverified'
        description = (f'{prefix} appears in the supplied historical compilation index. Model features and individual letter meanings require separate evidence.' if checked else f'{prefix} is present in supplied research candidates. The underlying model reading and individual letter meanings need verification.')
        entries.append(['HISTORICAL CASIO' if historical else 'RESEARCH REFERENCE', prefix, description, models[0]['id'], {'status': evidence, 'source': 'https://github.com/SEPULKRUM/casio-watch-specs/blob/main/data/model-references.json'}])
    return entries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--intake', required=True)
    parser.add_argument('--observations', default='research/prefix-library-2026-11-15/index-observations.json')
    parser.add_argument('--output', default='data/model-references.json')
    args = parser.parse_args()
    data, rejected = build(args.intake, json.loads(Path(args.observations).read_text()))
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    existing_text = Path('web/prefix-data.mjs').read_text()
    match = re.search(r'(?:export )?const (?:baseEntries|entries)=(\[.*?\]);', existing_text, re.S)
    existing = {row[1] for row in json.loads(match[1])}
    new_entries = prefix_entries(data, existing)
    Path('web/research-prefix-data.mjs').write_text('// Identifier observations only; no universal letter expansions. Generated by reference_import.py.\nexport const researchEntries=' + json.dumps(new_entries, ensure_ascii=False, indent=2) + ';\n')
    print(json.dumps(dict(data['counts'], new_prefixes=len(new_entries), total_prefixes=len(existing) + len(new_entries))))
