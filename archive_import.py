"""Convert batches of reviewed historical Casio facts; no crawling or model guessing."""
import argparse
import re
from pathlib import Path

import specs


def fingerprint(model):
    return re.sub(r'[^A-Z0-9]', '', specs.identity(model))


def convert(notes, existing_model_ids=()):
    if notes.get('type') != 'archived_official_products':
        raise ValueError('Expected archived official product research')
    existing = {fingerprint(model): specs.identity(model) for model in existing_model_ids}
    seen = set()
    records = []
    for document in notes['documents']:
        model = specs.identity(document['displayed_model'])
        if (fingerprint(model) in seen or
                (fingerprint(model) in existing and existing[fingerprint(model)] != model)):
            raise ValueError('Duplicate or punctuation-variant model requires explicit reconciliation')
        seen.add(fingerprint(model))
        module = document['module_id']
        if not re.fullmatch(r'\d{3,4}', module):
            raise ValueError('Explicit module number required')
        if not document.get('module_evidence'):
            raise ValueError('Module association requires transcribed page evidence')
        source = {'url': document['archive_url'], 'original_url': document['original_url'],
                  'archive_timestamp': document['archive_timestamp'],
                  'snapshot_sha256': document['snapshot_sha256'],
                  'accessed': notes['accessed'], 'permission': 'official_public_reference',
                  'evidence_type': 'historical_technical_fact',
                  'research_sha256': specs.digest(document)}
        specs.validate_archive_source(source)
        if {'module_id', 'module_candidates'} & document['model_specs'].keys():
            raise ValueError('Module association must use its explicit evidence field')
        for kind, key, values in [('model', model, document['model_specs']),
                                  ('module', module, document['module_specs'])]:
            facts = {field: {'value': value,
                     'uncertainty': 'Historical archived official page; capture-specific transcription pending independent review',
                     'sources': [dict(source, locator=document['locator'],
                                      evidence=f'{key}: {field} = {value}')]} for field, value in values.items()}
            if kind == 'model':
                facts['module_id'] = {'value': module,
                    'uncertainty': 'Explicit historical product-page module reference; other production revisions unresolved',
                    'sources': [dict(source, locator=document['locator'], evidence=document['module_evidence'])]}
            record = {'kind': kind, 'id': key, 'specs': facts}
            specs.validate(record)
            records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notes')
    parser.add_argument('--existing-catalog', default='data/catalog.json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if (output == Path(args.notes).resolve() or output.name == 'watches.json'
            or output.parent.name == 'data'):
        parser.error('Output must be a separate import proposal')
    existing = specs.load(args.existing_catalog)['models']
    specs.write(output, convert(specs.load(args.notes), existing))


if __name__ == '__main__':
    main()
