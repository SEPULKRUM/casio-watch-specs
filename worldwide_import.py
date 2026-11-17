"""Reproduce exact-reference 2020–2026 supplied register candidates and browser addendum."""
import argparse, hashlib, json, re
from pathlib import Path
import specs
REFERENCE='research/supplied-worldwide-2020-2026-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-worldwide-2026-11-17.json'
WEB='web/worldwide-data.mjs'
UNCERTAINTY='Supplied worldwide research; pending independent archived-source verification. Listing/announcement dates are not first-release dates. Exact reference only; no cross-variant inheritance.'

def artifacts(root):
 n=specs.load(root/REFERENCE);checksum=specs.digest(n);records=[];existing={}
 for path in sorted((root/'imports').glob('*.json')):
  if path.as_posix().endswith(IMPORT):continue
  for r in specs.load(path):
   for k,v in r['specs'].items():existing.setdefault((r['kind'],r['id'],k),[]).append(v['value'])
 for entry in n['entries']:
  id=entry['id']; values={};modules=set()
  for obs in entry['observations']:
   r=obs['data'];m=r.get('module_number') or r.get('module')
   if m is not None:
    if not re.fullmatch(r'\d{2,4}',str(m)):raise ValueError('Invalid module reference')
    modules.add(str(m))
   dimensions=r.get('model_specific_measurements') or r.get('dimensions_mm') or r.get('case_dimensions_mm') or r.get('specifications') or {}
   if isinstance(dimensions,dict):
    dims=[dimensions.get(k,dimensions.get(k+'_mm')) for k in ['length','width','thickness']]
    if all(isinstance(x,(int,float)) and not isinstance(x,bool) and x>0 for x in dims):values.setdefault('dimensions_mm',[]).append(dict(zip(['length','width','thickness'],dims)))
   for field,val in [('weight_g',r.get('weight_g') or dimensions.get('weight_g') if isinstance(dimensions,dict) else r.get('weight_g')),('case_material',r.get('case_material') or (r.get('materials') or {}).get('case_bezel')),('band_material',r.get('band_material') or (r.get('materials') or {}).get('band')),('glass',r.get('crystal') or (r.get('materials') or {}).get('crystal')),('water_resistance_m',(r.get('functions') or {}).get('water_resistance_m'))]:
    if val is not None:values.setdefault(field,[]).append(val)
  evidence={'status':n['status'],'observations':[{'source_document':n['source_documents'][o['document']]['filename'],'source_sha256':n['source_documents'][o['document']]['sha256'],'source_row':o['row'],**o['data']} for o in entry['observations']]}
  fields={'worldwide_evidence':evidence}
  # Never turn a partial family or multi-watch package into a physical variant.
  category=n['category_resolutions'].get(id,'watch')
  if category=='watch':
   for k,vs in values.items():
    if all(v==vs[0] for v in vs):fields[k]=vs[0]
  if len(modules)==1:fields['module_id']=next(iter(modules))
  elif modules:fields['module_candidates']=sorted(modules)
  if category!='watch':fields['reference_scope']='worldwide_'+category+'_reference'
  rs={'kind':'model','id':id,'specs':{}}
  for k,v in list(fields.items()):
   if k!='worldwide_evidence' and existing.get(('model',id,k)):continue
   rs['specs'][k]={'value':v,'uncertainty':UNCERTAINTY,'sources':[{'kind':'user_provided','provided_by':'SEPULKRUM','permission':'user_provided','reference':REFERENCE,'source_sha256':checksum,'accessed':n['received'],'locator':id+' / exact register observations','evidence':id+': '+k+' = '+json.dumps(v,ensure_ascii=False)}]}
  specs.validate(rs);records.append(rs)
 # Module profiles record only explicit associations; no functions or physical facts are inherited.
 associated={}
 for r in records:
  for module in ([r['specs']['module_id']['value']] if 'module_id' in r['specs'] else r['specs'].get('module_candidates',{}).get('value',[])):
   associated.setdefault(module,[]).append(r['id'])
 existing_modules={k[1] for k in existing if k[0]=='module'}
 for module,ids in sorted(associated.items()):
  if module in existing_modules:continue
  value={'associated_watch_identifiers':ids,'status':'Supplied module association only; functional specifications pending verification.'}
  fact={'value':value,'uncertainty':UNCERTAINTY,'sources':[{'kind':'user_provided','provided_by':'SEPULKRUM','permission':'user_provided','reference':REFERENCE,'source_sha256':checksum,'accessed':n['received'],'locator':'Explicit module associations in register observations','evidence':json.dumps(value)}]}
  records.append({'kind':'module','id':module,'specs':{'worldwide_evidence':fact}})
 data={'schema_version':1,'source_reference':REFERENCE,'source_sha256':checksum,'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':n['received'],'watch_identifiers':n['models']+n['family_identifiers'],'clock_identifiers':[],'package_identifiers':n['package_identifiers'],'category_resolutions':n['category_resolutions'],'identifier_occurrences':n['identifier_occurrences'],'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:v['value'] for k,v in r['specs'].items()}} for r in records]}
 report={'source_documents':len(n['source_documents']),'total_imported_records':len(n['identifier_occurrences']),'distinct_exact_identifiers':len(n['entries']),'duplicate_exact_occurrences':len(n['identifier_occurrences'])-len(records),'individual_watch_identifiers':len(n['models']),'family_references':len(n['family_identifiers']),'packages':len(n['package_identifiers']),'models_missing_from_addendum':sorted(set(n['identifier_occurrences'])-{r['id'] for r in records})}
 return {IMPORT:json.dumps(records,ensure_ascii=False,indent=2)+'\n',WEB:'export const worldwide='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n','research/worldwide-import-report-2026-11-17.json':json.dumps(report,indent=2)+'\n'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for name,s in artifacts(root).items():
  target=root/name
  if a.check:
   if target.read_text()!=s:raise ValueError('Stale worldwide artifact: '+name)
  else:target.write_text(s)
if __name__=='__main__':main()
