"""Build pending technical candidates and a bounded browser addendum from supplied PDF research."""
import argparse
import hashlib
import json
from pathlib import Path
import specs
REFERENCE = 'research/supplied-prw69-ocwg1200-2026-11-17.json'
IMPORT = 'imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-prw69-ocwg1200-2026-11-17.json'
WEB = 'web/series-pdfs-data.mjs'

def convert(notes, reference=REFERENCE, uncertainty=None):
    if notes.get('type') != 'user_watch_specifications':
        raise ValueError('Expected supplied technical research')
    checksum = specs.digest(notes)
    records = {}
    for claim in notes['claims']:
        key = (claim['kind'], claim['id'])
        record = records.setdefault(key, {'kind': key[0], 'id': key[1], 'specs': {}})
        if claim['field'] in record['specs']:
            raise ValueError('Duplicate claim field')
        record['specs'][claim['field']] = {
            'value': claim['value'],
            'uncertainty': uncertainty or 'Owner-supplied research conversation; pending independent verification. Exact model scope; estimates and parts fitment retain their qualifications.',
            'sources': [{'kind': 'user_provided', 'provided_by': notes['provided_by'],
                'permission': 'user_provided', 'reference': reference, 'source_sha256': checksum,
                'accessed': notes['received'],
                'locator': notes['source_documents'][claim['document']]['filename'] + ' / PDF pages ' + ', '.join(map(str, claim['pdf_pages'])),
                'evidence': claim['id'] + ': ' + claim['field'] + ' = ' + json.dumps(claim['value'], ensure_ascii=False)}]}
    for record in records.values():
        specs.validate(record)
    return list(records.values())

def artifacts(root):
    notes=specs.load(root/REFERENCE);records=convert(notes,REFERENCE,uncertainty='Supplied exact-model PDF research; pending archive verification. Estimates, module-attribution caveats and exact regional scope remain explicit.')
    web={'schema_version':1,'source_reference':REFERENCE,'source_sha256':specs.digest(notes),'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':notes['received'],'watch_identifiers':notes['models'],'clock_identifiers':[],'identifier_occurrences':notes['models'],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:v['value'] for k,v in r['specs'].items()}} for r in records],'cautions':notes['cautions']}
    return {IMPORT:json.dumps(records,ensure_ascii=False,indent=2)+'\n',WEB:'export const seriesPdfs='+json.dumps(web,ensure_ascii=False,separators=(',',':'))+';\n'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    for name, content in artifacts(root).items():
        path = root / name
        if args.check:
            if path.read_text() != content:
                raise ValueError('Stale PDF research artifact: ' + name)
        else:
            path.write_text(content)

if __name__ == '__main__':
    main()
