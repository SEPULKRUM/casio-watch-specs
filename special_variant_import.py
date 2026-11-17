"""Reproduce seven special-reference resolutions, separating packages from watches."""
import argparse,hashlib,json
from pathlib import Path
import specs
from research_pdf_import import convert
REFERENCE='research/supplied-seven-special-variants-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-seven-special-2026-11-17.json'
WEB='web/special-variants-data.mjs'
UNCERTAINTY='Supplied source-supported special-reference research; package hardware, derived measurements, module attribution and secondary reporting retain their scope. Pending independent database review.'
def artifacts(root):
 n=specs.load(root/REFERENCE);rs=convert(n,REFERENCE,uncertainty=UNCERTAINTY)
 data={'schema_version':1,'source_reference':REFERENCE,'source_sha256':specs.digest(n),'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':n['received'],'watch_identifiers':n['models'],'clock_identifiers':[],'package_identifiers':n['package_identifiers'],'uncertain_identifiers':n['uncertain_identifiers'],'category_resolutions':n['category_resolutions'],'identifier_occurrences':[r['id'] for r in n['reference_records']],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:f['value'] for k,f in r['specs'].items()}} for r in rs],'related_labels':n['related_labels'],'cautions':n['cautions']}
 return {IMPORT:json.dumps(rs,ensure_ascii=False,indent=2)+'\n',WEB:'export const specialVariants='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for name,s in artifacts(root).items():
  p=root/name
  if a.check:
   if p.read_text()!=s:raise ValueError('Stale special-variant artifact: '+name)
  else:p.write_text(s)
if __name__=='__main__':main()
