"""Parse the historical extraction tables, preserving column and page provenance."""
import re,json,hashlib
from pathlib import Path
def parse_text(text):
 rows=[];notes=[];uncertain=[];year=None;mode=None;columns=None;current=None
 for pageno,page in enumerate(text.split('\f'),1):
  for line in page.splitlines():
   if m:=re.search(r'(1980|1982|1985|1989) CATALOG',line):year=int(m[1]);mode='models';columns=None;current=None
   if m:=re.search(r'(1980|1982|1985|1989) — source-backed module notes',line):year=int(m[1]);mode='modules';columns=None;current=None
   if m:=re.search(r'(1980|1982|1985|1989) — \d+ uncertain labels',line):year=int(m[1]);mode='uncertain';columns=None;current=None
   if 'Selected module-level specifications' in line or 'Readings requiring visual verification' in line:mode=None;columns=None;current=None
   if mode=='models' and 'Model ' in line and 'Module' in line and 'Source section' in line:
    columns=[line.index(x) for x in ['Model','Module','Source section','Material / finish','Page']];current=None;continue
   if mode=='modules' and 'Module ' in line and 'Features / timekeeping' in line:
    columns=[line.index(x) for x in ['Module','Features / timekeeping','Accuracy / battery / note','Catalog']];current=None;continue
   if mode=='uncertain' and 'Unverified scan reading' in line:
    columns=[line.index(x) for x in ['Unverified scan reading','Possible module reading','PDF page']];current=None;continue
   if not columns or not line.strip() or line.lstrip().startswith('CASIO ·'):continue
   fields=[line[a:b].strip() for a,b in zip(columns,columns[1:]+[None])]
   if mode=='models':
    id,module,details,material,original_page=fields
    if id and re.fullmatch(r'[A-Z0-9][A-Z0-9-]*',id) and re.fullmatch(r'\d+|—',module) and original_page.isdigit():
     current={'id':id,'catalog_year':year,'extraction_pdf_page':pageno,'catalog_page':int(original_page),'module':None if module=='—' else module,'description':details,'material_finish':None if material=='—' else material};rows.append(current)
    elif current and not id and not module:
     if details:current['description']+=' '+details
     if material and material!='—':current['material_finish']=(current['material_finish'] or '')+' '+material
   elif mode=='modules':
    module,features,note,original=fields
    if module.isdigit():current={'module':module,'catalog_year':year,'extraction_pdf_page':pageno,'features':features,'note':note,'catalog_source':original};notes.append(current)
    elif current and not module:
     for k,v in [('features',features),('note',note),('catalog_source',original)]:
      if v and v not in ['source']:current[k]+=' '+v
   elif mode=='uncertain':
    reading,module,original_page=fields
    if reading and original_page.isdigit():uncertain.append({'reading':reading,'possible_module':None if module=='—' else module,'catalog_year':year,'catalog_page':int(original_page),'extraction_pdf_page':pageno,'status':'visual_review_required'})
 return {'models':rows,'module_notes':notes,'uncertain_readings':uncertain}

if __name__ == '__main__':
 import argparse,subprocess
 parser=argparse.ArgumentParser(description='Extract selected historical catalog facts from the supplied text-only PDF; keep uncertain labels separate.')
 parser.add_argument('pdf');parser.add_argument('--output',required=True);args=parser.parse_args()
 text=subprocess.check_output(['pdftotext','-layout',args.pdf,'-'],text=True)
 result=parse_text(text);Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 print(json.dumps({'readable_models':len(result['models']),'module_notes':len(result['module_notes']),'uncertain_readings':len(result['uncertain_readings'])}))
