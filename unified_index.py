"""Build one exact-identifier index from every committed Casio intake.

Identity is exact after trimming outer whitespace. Compact search never merges
records. Indexed mentions are not authenticated watch variants or verified facts.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from reference_import import MODEL

CATEGORIES = ('watch', 'family', 'clock', 'fitment', 'uncertain', 'package')
OUTPUTS = {'data/search-index.json', 'data/reconciliation-report.json', 'data/unified-models.csv'}
IDENTITY_KEYS = {'model', 'model_id', 'model_number', 'model_code', 'watch_model', 'watch_id', 'listed_model', 'canonical_model', 'displayed_model', 'displayed_sku', 'verified_exact_model', 'catalog_model', 'candidate_id', 'comparison_model', 'sku', 'productName', 'productDisplayName', 'identifier', 'example_model', 'reference_model'}
LIST_KEYS = {'models', 'model_strings', 'candidate_model_strings', 'example_models', 'examples', 'catalog_models', 'aliases', 'supplied_aliases', 'added_model_series_strings', 'imported', 'unmatched', 'related_user_mappings', 'proposed_aliases', 'market_aliases', 'related_models', 'variants'}
UNCERTAIN_KEYS = {'reading', 'raw_label', 'model_as_read', 'model_string', 'cached_search_reading', 'opened_article_reading'}
TECHNICAL_FIELDS = {'catalog_material_finish', 'dimensions_mm','weight_g','water_resistance_rating','water_resistance_m','water_resistance_bar','case_material','band_material','glass','color','case_finish','promotional_thickness_mm','technical_table_thickness_mm','display_polarity','release_date'}
BATTERY = re.compile(r'^(?:CR|SR|LR|BR|CTL|ML|QW)-?\d{3,4}(?:SW|W)?$')


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dumps(value): return json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n'
def pointer(path, key): return path+'/'+str(key).replace('~','~0').replace('/','~1')
def module_ids(row):
    specs=row.get('specs',{})
    return specs.get('module_candidates',{}).get('value') or [str(specs.get('module_id',{}).get('value') or row.get('module'))] if (specs.get('module_candidates') or specs.get('module_id') or row.get('module')) else []


def family_name(value):
    value=str(value or '').strip()
    if re.search(r'g[- ]?shock|rangeman|mudman|frogman',value,re.I): return 'G-SHOCK'
    if re.search('oceanus',value,re.I): return 'Oceanus'
    if re.search(r'pro.?trek',value,re.I): return 'Pro Trek'
    if re.search(r'baby.?g',value,re.I): return 'Baby-G'
    return value


def build(root=Path('.')):
    root=Path(root);catalog=load(root/'data/catalog.json');references=load(root/'data/model-references.json');master=load(root/'research/casio-master-research-2026-11-16.json')
    records={};sources=[];source_numbers={};audit=[];occurrences=[];ignored=Counter()
    clocks={key for key,row in catalog['models'].items() if 'clock' in str(row['specs'].get('series',{}).get('value','')).lower() or row['specs'].get('reference_scope',{}).get('value')=='2011_clock_index'}
    families={key for key,row in catalog['models'].items() if row['specs'].get('reference_scope',{}).get('value')=='2011_watch_family_index'}
    uncertain_catalog={key for key,row in catalog['models'].items() if row['specs'].get('reference_scope',{}).get('value')=='unconfirmed_identifier'}
    resolution_path=root/'research/supplied-seven-special-variants-2026-11-17.json'
    category_resolutions=load(resolution_path).get('category_resolutions',{}) if resolution_path.exists() else {}
    if any(v not in {'watch','package','uncertain'} for v in category_resolutions.values()):raise ValueError('Invalid special-reference category resolution')
    def source(path):
        name=path.as_posix() if isinstance(path,Path) else path
        if name not in source_numbers:
            source_numbers[name]=len(sources);sources.append({'path':name,'sha256':sha(root/name)})
        return source_numbers[name]
    def add(raw,path,locator,hint='watch',role='declared_identifier',family=None):
        if not isinstance(raw,str) or not raw.strip():return
        raw=raw.strip()
        if raw.startswith(('http:','https:','research/')):return
        if raw.isdigit():ignored['numeric_module_or_nonmodel_identifier']+=1;return
        if not any(c.isdigit() for c in raw):ignored['nonmodel_label']+=1;return
        if len(raw)>150 or not re.match(r'^(?:[A-Za-z]|[0-9]{1,5}[A-Za-z])',raw):ignored['prose_not_identifier']+=1;return
        if hint not in CATEGORIES:raise ValueError(hint)
        if hint=='watch' and (not MODEL.fullmatch(raw) or BATTERY.fullmatch(raw)):hint='uncertain'
        if hint=='fitment' or ('/' in raw or 'COMMON' in raw) and raw.upper()==raw:hint='fitment'
        item=records.setdefault(raw,{'id':raw,'hints':set(),'origins':[],'family_hints':[]})
        origin=[source(path),locator,role,hint]
        if origin not in item['origins']:item['origins'].append(origin)
        item['hints'].add(hint)
        if family and family_name(family) not in item['family_hints']:item['family_hints'].append(family_name(family))
        occurrences.append(raw)
    def catalog_hint(identifier):return category_resolutions[identifier] if identifier in category_resolutions else 'uncertain' if identifier in uncertain_catalog else 'clock' if identifier in clocks else 'family' if identifier in families else 'watch'
    def walk(value,path,location='',hint='watch',context=''):
        if isinstance(value,dict):
            if value.get('kind')=='module' or 'module_reference_number' in value and 'model_id' not in value:context='module'
            if 'reference_type' in value and 'combined/parts' in value['reference_type']:hint='fitment'
            scope=str(value.get('reading_status',value.get('reading_scope','')))
            if 'clock_index' in scope:hint='clock'
            elif 'family_label' in scope:hint='family'
            elif any(x in scope for x in ['ocr','requires_review','graphic_only']):hint='uncertain'
            for key,child in value.items():
                child_path=pointer(location,key)
                if key in {'counts'}:continue
                if key=='id' and isinstance(child,str) and context not in {'module','source'} and MODEL.fullmatch(child):add(child,path,child_path,hint,family=value.get('collection') or value.get('series'))
                elif key in IDENTITY_KEYS and isinstance(child,str):add(child,path,child_path,hint,family=value.get('family') or value.get('collection') or value.get('series'))
                elif key in UNCERTAIN_KEYS and isinstance(child,str) and len(child)<100 and re.fullmatch(r'[A-Za-z0-9.*?/_ ()-]+',child):add(child,path,child_path,'uncertain','unresolved_reading')
                elif key in {'base_model','family','family_title'} and isinstance(child,str) and MODEL.fullmatch(child):add(child,path,child_path,'family','base_label')
                elif key=='model_marking' and isinstance(child,str):add(child,path,child_path,'family','caseback_base_marking')
                elif key in LIST_KEYS and isinstance(child,list):
                    for i,item in enumerate(child):
                        loc=pointer(child_path,i)
                        if isinstance(item,str):add(item,path,loc,hint,'listed_identifier')
                        else:walk(item,path,loc,hint,'models')
                elif key=='id' or key in {'module_id','module','possible_module','candidate_sha256','evidence','locator','notes','description','scope','url','reference','filename','source_key','source_id'}:continue
                else:walk(child,path,child_path,'uncertain' if key in {'uncertain_readings','unresolved_labels','excluded_fragments','discrepancies','comparisons'} else hint,'source' if key in {'sources','source_register','members'} else context)
            columns=value.get('columns',[])
            if columns and isinstance(value.get('rows'),list):
                positions=[i for i,c in enumerate(columns) if re.match(r'^(?:(?:international|japan|exact|printed|catalog|jdm)\s+)?(?:model(?:\s+(?:code|number))?|reference|identifier)(?:\s*[/($]|$)',str(c),re.I) or re.match(r'^model family|^family$',str(c),re.I)]
                if positions:
                    for i,row in enumerate(value['rows']):
                        for j in positions:
                            if isinstance(row,list) and j<len(row) and isinstance(row[j],str):add(row[j],path,pointer(pointer(pointer(location,'rows'),i),j),'family' if 'family' in str(columns[j]).lower() else hint,'table_model_cell')
            if columns and isinstance(value.get('cells'),list):
                for j,col in enumerate(columns):
                    if j<len(value['cells']) and re.match(r'^(?:(?:international|japan|exact|printed)\s+)?(?:model|reference|identifier)(?:\s*[/($]|$)',str(col),re.I) and 'module' not in str(col).lower():add(value['cells'][j],path,pointer(pointer(location,'cells'),j),hint,'table_model_cell',value.get('family_title'))
        elif isinstance(value,list):
            for i,item in enumerate(value):walk(item,path,pointer(location,i),hint,context)
    input_paths=sorted({path for folder in ['data','research','imports'] for path in (root/folder).rglob('*') if path.is_file()} | set(root.glob('*.json')) | set(root.glob('*.txt')))
    for path in input_paths:
        if not path.is_file():continue
        name=path.relative_to(root).as_posix()
        if name in OUTPUTS:continue
        before=len(occurrences);method='semantic_identity_fields';reason=None;source(name)
        if path.suffix=='.json':
            data=load(path)
            if name=='data/catalog.json':
                method='catalog_records_and_explicit_aliases'
                for key,row in data['models'].items():
                    add(key,name,pointer('/models',key),catalog_hint(key),'catalog_record',row['specs'].get('series',{}).get('value'))
                    for i,alias in enumerate(row['specs'].get('supplied_aliases',{}).get('value',[])):add(alias,name,pointer('/models',key)+f'/specs/supplied_aliases/value/{i}','watch','explicit_alias')
            elif name=='data/model-references.json':
                method='reference_provenance_scopes'
                for key,row in data['models'].items():
                    hints=set()
                    for obs in row['observations']:
                        scope=obs.get('reading_scope','');role=obs['role']
                        hint='clock' if 'clock_index' in scope else 'family' if 'family_label' in scope else 'uncertain' if role in {'machine_ocr','prior_machine_index'} or 'ocr' in scope or 'requires_review' in scope else 'watch'
                        if row['reading_flags'] and role not in {'supplied_transcription','checked_compilation_index','publication_discovery'}:hint='uncertain'
                        hints.add(hint)
                    for hint in sorted(hints):add(key,name,pointer('/models',key),hint,'model_reference')
            elif name.endswith('casio-master-research-2026-11-16.json'):
                method='master_exact_raw_rows_and_relationships'
                for i,row in enumerate(data['models']):
                    add(row['model_id'],name,f'/models/{i}','fitment' if 'combined/parts' in row.get('reference_type',data['model_defaults']['reference_type']) else 'watch','master_identifier',row.get('family'))
                    records[row['model_id']]['master_row']=i
                for i,row in enumerate(data['relationships']):add(row['model_id'],name,f'/relationships/{i}/model_id','watch','explicit_module_association')
            elif 'watchnavi-2015-ocr-reference' in name:
                method='raw_ocr_placements_and_appendix'
                for i,row in enumerate(data['placements']):
                    add(row['model_string'],name,f'/placements/{i}/model_string','uncertain','ocr_reading')
                    if row.get('normalized_identifier'):add(row['normalized_identifier'],name,f'/placements/{i}/normalized_identifier','uncertain','prior_normalized_ocr_reading')
                for i,row in enumerate(data['unresolved_labels']):add(row['raw_label'],name,f'/unresolved_labels/{i}/raw_label','uncertain','unresolved_reading')
            elif name.endswith('recovered-intake-identifiers-2026-11-16.json'):
                method='recovered_original_intake_identifiers'
                for i,row in enumerate(data['records']):add(row['identifier'],name,f'/records/{i}', 'watch' if row['role']=='supplied_transcription' else 'family' if row['role']=='family_label' else 'uncertain',row['role'])
            elif name=='research/prefix-library-2026-11-15/index-observations.json':
                method='visually_checked_identifier_index'
                for page,identifiers in data['pages'].items():
                    for i,identifier in enumerate(identifiers):add(identifier,name,f'/pages/{page}/{i}','watch','checked_index_identifier')
            elif name=='data/coverage.json':reason='Derived coverage diagnostics; canonical identities audited through catalog'
            elif name in {'data/parts-links.json','data/official-product-links.json'}:
                method='exact_model_map_keys'
                for key,row in data.get('models',{}).items():add(key,name,pointer('/models',key),catalog_hint(key),'model_link_key');walk(row,name,pointer('/models',key))
            elif name=='research/catalog-index-2011-2026-11-15.json':
                method='explicit_watch_family_and_clock_index'
                for key,hint in [('watch_rows','family'),('clock_rows','clock')]:
                    for i,row in enumerate(data[key]):add(row['id'],name,f'/{key}/{i}/id',hint,'catalog_index_label',row.get('printed_group'))
            else:walk(data,name,hint='uncertain' if 'watchnavi' in name else 'watch')
        elif path.suffix=='.csv':
            method='csv_model_identifier_columns'
            for i,row in enumerate(csv.DictReader(io.StringIO(path.read_text())),2):
                for key in ['model','model_id','model_number']:
                    if row.get(key):add(row[key],name,f'CSV row {i} / {key}',catalog_hint(row[key]),'csv_identifier')
        elif path.suffix=='.txt':
            method='declared_product_url_identifiers'
            for i,line in enumerate(path.read_text().splitlines(),1):
                if line.startswith('#'):continue
                for match in re.finditer(r'/product\.([A-Z0-9-]+)(?:/|$)',line):add(match[1],name,f'line {i}','watch','declared_product_url')
        elif path.suffix=='.md':reason='Research explanation, not a model dataset'
        else:reason='Not a supported identifier dataset'
        audit.append({'path':name,'sha256':sha(path),'method':method,'identifier_occurrences':len(occurrences)-before,**({'note':reason} if reason else {})})
    # Dataset exports embedded in the existing browser are also audited, without executing JS.
    for path in sorted((root/'web').glob('*.mjs')):
        name=path.relative_to(root).as_posix();before=len(occurrences);source(name);text=path.read_text();blocks=0
        for match in re.finditer(r'(?:export\s+)?const\s+\w+\s*=\s*([\[{])',text):
            try:data,_=json.JSONDecoder().raw_decode(text[match.start(1):])
            except json.JSONDecodeError:continue
            blocks+=1
            if name in {'web/prefix-data.mjs','web/research-prefix-data.mjs'} and isinstance(data,list):
                for i,entry in enumerate(data):
                    if isinstance(entry,list) and len(entry)>3 and isinstance(entry[3],str):add(entry[3],name,f'/embedded-{blocks}/{i}/3','uncertain' if 'research-prefix' in name else 'watch' if re.search(r'-[1-9][A-Z0-9]*$',entry[3]) else 'family','prefix_example_identifier')
            walk(data,name,'/embedded-'+str(blocks),hint='uncertain' if 'watchnavi' in name or 'historical-review' in name else 'family' if 'prefix-data' in name else 'watch')
        audit.append({'path':name,'sha256':sha(path),'method':'read_only_embedded_json_dataset_audit','identifier_occurrences':len(occurrences)-before,'json_blocks':blocks})
    for path in sorted(root.glob('*import.py')):
        name=path.relative_to(root).as_posix();before=len(occurrences);source(name)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Constant) and isinstance(node.value,str) and MODEL.fullmatch(node.value):add(node.value,name,'line '+str(node.lineno),'uncertain','import_script_literal')
        audit.append({'path':name,'sha256':sha(path),'method':'import_script_literal_and_schema_audit','identifier_occurrences':len(occurrences)-before})
    prefix_families={}
    for path in ['web/prefix-data.mjs','web/research-prefix-data.mjs']:
        match=re.search(r'(?:const baseEntries|export const researchEntries)=(\[.*?\]);',(root/path).read_text(),re.S)
        for entry in json.loads(match[1]) if match else []:
            if entry[0] not in ['HISTORICAL CASIO','RESEARCH REFERENCE']:prefix_families[entry[1]]=family_name(entry[0])
    for name in ['catalog.py','specs.py','build_web.py','unified_index.py','collector.py']:
        source(name);audit.append({'path':name,'sha256':sha(root/name),'method':'pipeline_implementation_audit','identifier_occurrences':0})
    resolutions=load(root/'research/fitment-resolutions-2026-11-16.json')['resolutions']
    for resolution in resolutions:
        combined=resolution['model_id'];members=resolution['related_models']
        if combined not in records or 'fitment' not in records[combined]['hints'] or not members or len(members)!=len(set(members)):
            raise ValueError('Invalid explicit fitment resolution: '+combined)
        for member in members:
            if member not in records or 'watch' not in records[member]['hints'] or 'fitment' in records[member]['hints']:
                raise ValueError('Fitment member is not an individual identifier: '+member)
        if any(note['model_id'] not in members for note in resolution.get('model_notes',[])):
            raise ValueError('Fitment note belongs to a different model')
    rows=[]
    for key,item in sorted(records.items()):
        hints=item.pop('hints');hint=category_resolutions[key] if key in category_resolutions else 'uncertain' if key in uncertain_catalog else 'clock' if key in clocks or 'clock' in hints else 'fitment' if 'fitment' in hints else 'family' if key in families else 'watch' if 'watch' in hints else 'family' if 'family' in hints else 'uncertain'
        # An explicit 2011 family label remains a family unless another source identifies a watch variant.
        if key in families and hints<={'family','uncertain'}:hint='family'
        model=catalog['models'].get(key);prefix=re.match(r'[A-Z]+',key)
        family=(family_name(model['specs'].get('series',{}).get('value')) if model else '') or next((f for f in item.pop('family_hints') if f), '') or (prefix_families.get(prefix[0],'') if prefix and hint=='watch' else '') or 'Unclassified'
        if 'family_hints' in item:item.pop('family_hints')
        ids=module_ids(model) if model else []
        if not ids and 'master_row' in item:
            ids=list(dict.fromkeys(r['module_reference_number'] for r in master['relationships'] if r['model_id']==key))
        item.update(category=hint,family=family,module_ids=ids,catalog_id=key if model else None,has_specifications=bool(model and TECHNICAL_FIELDS&set(model['specs'])),has_checked_fields=bool(model and any(f['status']=='verified' for f in model['specs'].values())))
        rows.append(item)
    counts=Counter(row['category'] for row in rows);watch=[r for r in rows if r['category']=='watch'];freq=Counter(occurrences)
    expected={key for key,item in records.items() if any(o[3]=='watch' for o in item['origins']) and key not in clocks and key not in families and not any(o[3] in {'clock','fitment'} for o in item['origins'])}
    expected |= {row['model_id'] for row in master['models'] if MODEL.fullmatch(row['model_id']) and not BATTERY.fullmatch(row['model_id']) and 'combined/parts' not in row.get('reference_type',master['model_defaults']['reference_type']) and row['model_id'] not in clocks and row['model_id'] not in families}
    expected -= {k for k in uncertain_catalog if category_resolutions.get(k)!='watch'}
    expected -= {k for k,v in category_resolutions.items() if v!='watch'}
    index={'schema_version':1,'identity_policy':'Exact identifier after outer-whitespace trimming; punctuation, variants and regional suffixes are never merged. Compact forms are search keys only.','scope':'Watch identifiers are pending authentication unless their individual facts carry review evidence. Family, clock, fitment and uncertain categories do not inflate individual-watch counts.','generator_sha256':sha(root/'unified_index.py'),'catalog_sha256':sha(root/'data/catalog.json'),'master_source':'research/casio-master-research-2026-11-16.json','sources':sources,'counts':{'all_records':len(rows),**{k:counts[k] for k in CATEGORIES},'watch_with_specifications':sum(r['has_specifications'] for r in watch),'watch_reference_only':sum(not r['has_specifications'] for r in watch),'catalog_records':len(catalog['models']),'catalog_watch_records':sum(r['category']=='watch' and r['catalog_id'] is not None for r in rows)},'records':rows}
    index['fitment_resolutions']=resolutions
    published={r['id'] for r in rows if r['category']=='watch'}
    missing=sorted(expected-published)
    report={'schema_version':1,'definitions':{'total_imported_identifiers':'Identifier occurrences across audited datasets, including repeated exact identifiers and generated mirrors; not a watch count.','distinct_individual_watch_identifiers':'Eligible individual identifiers, not a claim that every watch or its specifications are authenticated.','models_with_specifications':'Individual watch identifiers with at least one own technical catalog field; no shared-module case data is copied.','reference_only_models':'Individual watch identifiers without their own technical catalog fields.','duplicate_exact_identifiers':'Occurrences beyond the first exact identifier; different suffixes, punctuation and regions remain separate.'},'total_imported_identifiers':len(occurrences),'distinct_raw_identifiers':len(rows),'distinct_individual_watch_identifiers':counts['watch'],'duplicate_exact_identifiers':len(occurrences)-len(rows),'identifiers_with_exact_duplicates':sum(n>1 for n in freq.values()),'reference_only_models':index['counts']['watch_reference_only'],'models_with_specifications':index['counts']['watch_with_specifications'],'unresolved_identifiers':counts['uncertain'],'category_counts':{k:counts[k] for k in CATEGORIES},'models_missing_from_published_search_index':missing,'missing_model_count':len(missing),'source_audit':audit,'ignored_nonmodel_fields':dict(ignored),'published_dataset_aliases':{'master-research.json':'research/casio-master-research-2026-11-16.json'},'expected_eligible_individual_identifiers':sorted(expected),'duplicate_identifier_details':[{'id':key,'occurrences':n} for key,n in sorted(freq.items()) if n>1],'index_sha256':hashlib.sha256(dumps(index).encode()).hexdigest()}
    report['unconfirmed_identifier_overrides']=sorted(k for k in uncertain_catalog if k not in category_resolutions)
    report['special_reference_category_resolutions']=category_resolutions
    if missing:raise ValueError('Eligible models omitted from unified index')
    return index,report


def export_csv(index,catalog):
    stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(['model','category','family','specification_status','catalog_record','module_references','length_mm','width_mm','thickness_mm','weight_g','case_material','band_material','glass','water_resistance_rating','color','source_locations'])
    for row in index['records']:
        model=catalog['models'].get(row['catalog_id'],{}) if row['catalog_id'] else {};facts=model.get('specs',{})
        value=lambda key:facts.get(key,{}).get('value','')
        dims=value('dimensions_mm') or {}
        values=[row['id'],row['category'],row['family'],'Selected facts source checked; other fields pending' if row['has_checked_fields'] else 'Specifications pending verification',row['catalog_id'] or '', ' | '.join(row['module_ids']),*[dims.get(key,'') for key in ['length','width','thickness']],*[value(key) for key in ['weight_g','case_material','band_material','glass','water_resistance_rating','color']],json.dumps([{'source':index['sources'][o[0]]['path'],'locator':o[1]} for o in row['origins']],ensure_ascii=False,separators=(',',':'))]
        writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in values])
    return stream.getvalue()


def write(root=Path('.'),check=False):
    root=Path(root);index,report=build(root)
    csv_content=export_csv(index,load(root/'data/catalog.json'))
    report['unified_csv_sha256']=hashlib.sha256(csv_content.encode()).hexdigest()
    for name,content in [('data/search-index.json',dumps(index)),('data/reconciliation-report.json',dumps(report)),('data/unified-models.csv',csv_content)]:
        path=root/name
        if check:
            if not path.exists() or path.read_text()!=content:raise ValueError('Stale unified search artifact: '+name)
        else:path.write_text(content)
    return index,report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args();index,report=write(check=args.check);print(json.dumps({k:v for k,v in report.items() if k not in ['source_audit','definitions','expected_eligible_individual_identifiers','duplicate_identifier_details']},indent=2))
