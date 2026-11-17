"""Reproduce scoped four-module watch research without promoting family templates."""
import argparse,hashlib,json
from pathlib import Path
import specs
from research_pdf_import import convert
REFERENCE='research/supplied-metal-squares-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzz-metal-squares-2026-11-17.json'
WEB='web/metal-squares-data.mjs'
UNCERTAINTY='Supplied four-module technical research; series templates, approximate weights and unconfirmed identifiers retain their scope. Pending independent database review.'
def artifacts(root):
 n=specs.load(root/REFERENCE);records=convert(n,REFERENCE,uncertainty=UNCERTAINTY)
 web={'schema_version':1,'source_reference':REFERENCE,'source_sha256':specs.digest(n),'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':n['received'],'watch_identifiers':n['models'],'clock_identifiers':[],'uncertain_identifiers':n['uncertain_identifiers'],'unresolved_records':[{'id':r['reading'],'category':'uncertain','description':r['description'],'status':r['status'],'pdf_page':r['pdf_page'],'note':r['note']} for r in n['unresolved_labels']],'identifier_occurrences':[r['id'] for r in n['source_rows']],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:f['value'] for k,f in r['specs'].items()}} for r in records],'cautions':n['cautions']}
 return {IMPORT:json.dumps(records,ensure_ascii=False,indent=2)+'\n',WEB:'export const metalSquares='+json.dumps(web,ensure_ascii=False,separators=(',',':'))+';\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for n,s in artifacts(root).items():
  p=root/n
  if a.check:
   if p.read_text()!=s:raise ValueError('Stale metal-square artifact: '+n)
  else:p.write_text(s)
if __name__=='__main__':main()
