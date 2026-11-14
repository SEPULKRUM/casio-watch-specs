"""Import attributed user-supplied module mappings as pending candidates."""
import argparse
import re
from pathlib import Path, PurePosixPath

import specs


def convert(notes, reference):
    if notes.get('type') != 'user_module_associations':
        raise ValueError('Expected a user module-association batch')
    path = PurePosixPath(reference)
    if not reference.startswith('research/') or '..' in path.parts or path.is_absolute() or path.suffix != '.json':
        raise ValueError('Reference must name the committed research JSON file')
    records, seen = [], set()
    for index, row in enumerate(notes['mappings'], 1):
        key = specs.identity(row['model'])
        module = row['module']
        if not isinstance(module, str) or not re.fullmatch(r'\d{3,4}', module):
            raise ValueError('Module must be a 3 or 4 digit string')
        if key in seen:
            raise ValueError('Duplicate model in supplied batch')
        seen.add(key)
        source = {'kind': 'user_provided', 'reference': reference,
                  'provided_by': notes['provided_by'], 'source_sha256': specs.digest(notes),
                  'accessed': notes['received'], 'locator': f'Mappings / entry {index}',
                  'evidence': f'{key} → module {module}', 'permission': 'user_provided'}
        record = {'kind': 'model', 'id': key, 'specs': {'module_id': {
            'value': module, 'uncertainty': 'User-supplied association; official model-to-module confirmation pending',
            'sources': [source]}}}
        specs.validate(record)
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notes')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    reference = Path(args.notes).as_posix()
    output = Path(args.output).resolve()
    if output == Path(args.notes).resolve() or output.name == 'watches.json' or output.parent.name == 'data':
        parser.error('Output must be a separate import proposal')
    specs.write(output, convert(specs.load(args.notes), reference))


if __name__ == '__main__':
    main()
