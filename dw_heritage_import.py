"""Reproduce DW-5000 heritage research, specimen measurements and service associations."""
import argparse,hashlib,json
from pathlib import Path
import specs
from research_pdf_import import convert
REFERENCE='research/supplied-dw5000-heritage-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-dw-heritage-2026-11-17.json'
WEB='web/dw-heritage-data.mjs'
UNCERTAINTY='Supplied DW-5000 heritage research, pending independent source review. Owner specimen observations, unresolved collector labels, rejected parts and factory/model/variant scopes remain explicit.'
def artifacts(root):
 n=specs.load(root/REFERENCE);rs=convert(n,REFERENCE,uncertainty=UNCERTAINTY)
 data={'schema_version':1,'source_reference':REFERENCE,'source_sha256':specs.digest(n),'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':n['received'],'watch_identifiers':n['models'],'clock_identifiers':[],'package_identifiers':n['package_identifiers'],'uncertain_identifiers':n['uncertain_identifiers'],'category_resolutions':n['category_resolutions'],'identifier_occurrences':n['identifier_occurrences'],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:f['value'] for k,f in r['specs'].items()}} for r in rs],'inventory_rows':n['inventory_rows'],'collector_labels':n['collector_labels'],'canonical_records':n['canonical_records'],'unresolved_records':n['collector_labels'],'cautions':n['cautions']}
 return {IMPORT:json.dumps(rs,ensure_ascii=False,indent=2)+'\n',WEB:'export const dwHeritage='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for name,s in artifacts(root).items():
  p=root/name
  if a.check:
   if p.read_text()!=s:raise ValueError('Stale special-variant artifact: '+name)
  else:p.write_text(s)
if __name__=='__main__':main()
