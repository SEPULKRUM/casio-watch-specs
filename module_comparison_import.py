"""Build scoped technical candidates from the supplied 3159 / 3495 comparison."""
import argparse,hashlib,json
from pathlib import Path
import specs
from research_pdf_import import convert
REFERENCE='research/supplied-module-comparison-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzz-module-comparison-2026-11-17.json'
WEB='web/module-comparison-data.mjs'
def artifacts(root):
 notes=specs.load(root/REFERENCE);records=convert(notes,REFERENCE,uncertainty='Supplied technical comparison; manufacturer/independent/derived evidence classifications retain their reported scope. Pending independent database review.')
 web={'schema_version':1,'source_reference':REFERENCE,'source_sha256':specs.digest(notes),'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':notes['received'],'watch_identifiers':notes['models'],'clock_identifiers':[],'identifier_occurrences':notes['models'],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:f['value'] for k,f in r['specs'].items()}} for r in records],'cautions':notes['cautions']}
 return {IMPORT:json.dumps(records,ensure_ascii=False,indent=2)+'\n',WEB:'export const moduleComparison='+json.dumps(web,ensure_ascii=False,separators=(',',':'))+';\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parent
 for name,content in artifacts(root).items():
  path=root/name
  if args.check:
   if path.read_text()!=content:raise ValueError('Stale module-comparison artifact: '+name)
  else:path.write_text(content)
if __name__=='__main__':main()
