"""Reproduce the dated 2026 master corrections without erasing source history."""
import argparse,copy,hashlib,json,re
from pathlib import Path
import specs
REFERENCE='research/supplied-2026-master-corrections-2026-11-17.json'
IMPORT='imports/zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-master-2026-corrections.json'
WEB='web/master-2026-data.mjs'
UNCERTAINTY='Latest supplied 2026 manufacturer-page research. Retains exact model and field scope, dated corrections, partial audit limits and original citations. Independent archived-source content review is separate.'
def fact(n,id,field,value):
 return {'value':value,'uncertainty':UNCERTAINTY,'sources':[{'kind':'user_provided','provided_by':n['provided_by'],'permission':'user_provided','reference':REFERENCE,'source_sha256':n['_checksum'],'accessed':n['received'],'locator':id+' / corrected 2026 master record','evidence':id+': '+field+' = '+json.dumps(value,ensure_ascii=False)}]}
def payload(root):
 n=specs.load(root/REFERENCE);n['_checksum']=specs.digest(n);records=[];updates=[]
 for row in n['models']:
  id=row['model'];evidence={'current_record':row,'dated_changes':[x for x in n['dated_field_changes'] if x['model']==id],'status':n['status']}
  records.append({'kind':'model','id':id,'specs':{'master_2026_evidence':fact(n,id,'master_2026_evidence',evidence)}})
  # Only the 36 model-specific audit rows authorize scalar updates. The other rows are retained research.
  official=row.get('official_model_specifications')
  if not official:continue
  values={};m=row.get('model_specific_measurements') or {}
  if all(isinstance(m.get(k),(int,float)) and m[k]>0 for k in ['length_mm','width_mm','thickness_mm']):values['dimensions_mm']=dict(zip(['length','width','thickness'],[m[k] for k in ['length_mm','width_mm','thickness_mm']]))
  if isinstance(m.get('weight_g'),(int,float)):values['weight_g']=m['weight_g']
  for field,key in [('case_material','case_bezel_material'),('band_material','band_material'),('glass','crystal'),('water_resistance_rating','water_resistance')]:
   if official.get(key) is not None:values[field]=official[key]
  module=row.get('module_number') or row.get('module')
  if module is not None:values['module_id']=str(module)
  for field,value in values.items():updates.append({'id':id,'field':field,'fact':fact(n,id,field,value)})
 regional=[]
 canonical_ids={r['id'] for r in records}
 for row in n['models']:
  for alias in row.get('regional_references_verified',[]):
   id=alias['model_reference']
   if id in canonical_ids:continue
   canonical_ids.add(id);regional.append(id)
   evidence={'current_record':{'model':id,'related_canonical_model':row['model'],**alias,'status':'Documented regional reference; physical specifications are linked to the canonical watch, not copied.'},'dated_changes':[],'status':n['status']}
   records.append({'kind':'model','id':id,'specs':{'master_2026_evidence':fact(n,id,'master_2026_evidence',evidence)}})
 existing_modules={r['id'] for path in (root/'imports').glob('*.json') if not path.as_posix().endswith(IMPORT) for r in specs.load(path) if r['kind']=='module'}
 module_models={}
 for u in updates:
  if u['field']=='module_id' and u['fact']['value'] not in existing_modules:module_models.setdefault(u['fact']['value'],[]).append(u['id'])
 for module,ids in module_models.items():
  evidence={'associated_watch_identifiers':ids,'status':'Explicit model-specific module association; functional specifications not transcribed in this update.'}
  records.append({'kind':'module','id':module,'specs':{'master_2026_evidence':fact(n,module,'master_2026_evidence',evidence)}})
 data={'schema_version':1,'source_reference':REFERENCE,'source_sha256':n['_checksum'],'source_file_sha256':hashlib.sha256((root/REFERENCE).read_bytes()).hexdigest(),'received':n['received'],'current_identifiers':[r['model'] for r in n['models']],'watch_identifiers':[r['model'] for r in n['models'] if not r['model'].startswith(('LOV-','GSET-'))]+regional,'regional_identifiers':regional,'clock_identifiers':[],'package_identifiers':[r['model'] for r in n['models'] if r['model'].startswith(('LOV-','GSET-'))],'category_resolutions':{r['model']:'package' for r in n['models'] if r['model'].startswith(('LOV-','GSET-'))},'identifier_occurrences':[r['model'] for r in n['models']]+regional,'records':[{'kind':r['kind'],'id':r['id'],'specs':{k:f['value'] for k,f in r['specs'].items()}} for r in records],'updates':updates,'aliases':{'GMA-S110XG-4':'GMA-S110XG-4A'},'merged_record_archive':n['merged_record_archive'],'dated_field_changes':n['dated_field_changes'],'audit_methodology':n['audit_methodology']}
 return records,data

def apply_to_catalog(catalog,root):
 _,data=payload(root);history=[]
 for update in data['updates']:
  model=catalog['models'][update['id']];field=update['field'];current=model['specs'].get(field);incoming=update['fact']
  if current and current.get('status')=='verified':
   if current['value']!=incoming['value']:history.append({'id':model['id'],'field':field,'retained_source_checked':True,'current_value':current['value'],'new_supplied_value':incoming['value']})
   continue
  if current and current['value']==incoming['value']:continue
  if current:history.append({'id':model['id'],'field':field,'superseded_fact':copy.deepcopy(current)})
  model['specs'][field]={**copy.deepcopy(incoming),'status':'pending_review'}
  if field=='module_id':model['specs'].pop('module_candidates',None)
 catalog['report']['master_2026_corrections']={'audit_records':36,'dated_field_events':78,'field_updates':len(data['updates']),'superseded_or_retained':history}
 return catalog

def artifacts(root):
 records,data=payload(root)
 report={'current_records':len(data['current_identifiers']),'individual_watch_references':len(data['watch_identifiers'])-len(data['regional_identifiers']),'additional_regional_references':len(data['regional_identifiers']),'retail_packages':len(data['package_identifiers']),'documented_merges':len(data['merged_record_archive']),'audited_models':len(data['audit_methodology']['manufacturer_pages_checked_for']),'dated_field_changes':len(data['dated_field_changes']),'scalar_updates':len(data['updates']),'corrected_aliases':data['aliases'],'missing_records':sorted(set(data['watch_identifiers'])-{r['id'] for r in records})}
 return {IMPORT:json.dumps(records,ensure_ascii=False,indent=2)+'\n',WEB:'export const master2026='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n','research/master-2026-corrections-report.json':json.dumps(report,indent=2)+'\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for name,s in artifacts(root).items():
  target=root/name
  if a.check:
   if target.read_text()!=s:raise ValueError('Stale 2026 corrections: '+name)
  else:target.write_text(s)
if __name__=='__main__':main()
