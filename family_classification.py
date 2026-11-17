"""Shared conservative family-label rules; never infer modules or specifications."""
import argparse,json,hashlib,re
from pathlib import Path
REFERENCE='research/family-classification-rules.json'
PLACEHOLDERS={'','unclassified','unknown','none','null','research reference','2011 watch index','historical casio'}
def resolve_family(identifier,existing='',series='',rules=None):
 rules=rules or json.loads((Path(__file__).resolve().parent/REFERENCE).read_text())
 prefix=re.match(r'^([A-Z]+)(?=-|\d)',identifier)
 prefix=prefix[1] if prefix else ''
 known=rules['prefix_families'].get(prefix)
 existing=str(existing or '').strip();series=str(series or '').strip()
 if known and prefix in rules['specific_prefixes']:return known
 if series.lower() not in PLACEHOLDERS:return series
 if existing.lower() not in PLACEHOLDERS:return existing
 return known or existing or 'Unclassified'
def browser_artifact(root):
 raw=(root/REFERENCE).read_bytes();rules=json.loads(raw)
 meta={'source_reference':REFERENCE,'source_file_sha256':hashlib.sha256(raw).hexdigest()}
 header='export const familyRules='+json.dumps(rules,separators=(',',':'))+';\nexport const familyClassificationSource='+json.dumps(meta,separators=(',',':'))+';\n'
 return header+(root/'web/family-classification-runtime.txt').read_text()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parent;out=r/'web/family-classification.mjs';s=browser_artifact(r)
 if a.check:
  if out.read_text()!=s:raise ValueError('Stale family classification browser rules')
 else:out.write_text(s)
if __name__=='__main__':main()
