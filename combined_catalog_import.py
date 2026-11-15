"""Parse the supplied consolidated model specification tables without images."""
import re,json
from pathlib import Path
HEADERS=[('model_bezel',['Model','Bezel','Display / sensors','Source']),('model_date',['Model','Date shown','Distinctive exterior','Module']),('spec',['Specification','Value']),('battery',['Usage setting','Manufacturer estimate']),('bms',['Model','Dial / design','Band','Mass / fit']),('identification',['Identification','Exact supplied value']),('collaboration',['Year','Reference','Documented distinction']),('gwr',['International reference','Japan reference','Dial / bezel treatment','Module']),('oceanus',['Model','Family','Catalog distinction','JPY (tax incl.)','Source']),('platform',['Family','Case (L x W x H)','Mass','Common platform details']),('chart',['Model family in chart','Case (L x W x H)','Mass','Source scope']),('t1000',['Reference','Release','Dial','Band / mass','Notes']),('t2600',['Reference','Release','Mass','Appearance / band','Distinction']),('t2610',['Reference','Release','Mass','Finish','Notes']),('dw290',['Reference / era','Casio module','What the supplied source supports']),('reported',['Printed identifier','Reported module','Evidence limitation']),('dw285',['Model','Exterior / accents','Band','Module'])]
def parse_text(text):
 tables=[];table=None;current=None
 for pageidx,page in enumerate(text.split('\f'),1):
  table=None;current=None
  for line in page.splitlines():
   header=next(((kind,labels) for kind,labels in HEADERS if all(label in line for label in labels)),None)
   if header:
    kind,labels=header;columns=[line.index(label) for label in labels];table={'kind':kind,'page':pageidx,'columns':labels,'rows':[]};tables.append(table);current=None;continue
   if not table or not line.strip():continue
   if line.startswith('Consolidated') or line.startswith('CASIO |'):table=None;current=None;continue
   if len(line)-len(line.lstrip())<columns[0]:table=None;current=None;continue
   cells=[line[a:b].strip() for a,b in zip(columns,columns[1:]+[None])]
   if not cells[0] and current:
    for i,v in enumerate(cells):
     if v:current[i]+=' '+v
    continue
   if cells[0]:
    if not re.search(r'\S {2,}\S',line):table=None;current=None;continue
    if table['kind'] in ['model_bezel','model_date','bms','oceanus','platform','chart','t1000','t2600','t2610','gwr','dw290','reported','dw285'] and not re.match(r'^(?:DW|GBX|BMS|OCW|GWR)-',cells[0]):table=None;current=None;continue
    if table['kind']=='collaboration' and not re.fullmatch(r'\d{4}',cells[0]):table=None;current=None;continue
    current=cells;table['rows'].append(current)
 return tables

if __name__ == '__main__':
 import argparse,subprocess
 p=argparse.ArgumentParser(description='Extract selected model/specification tables while preserving source scope and PDF pages.');p.add_argument('pdf');p.add_argument('--output',required=True);args=p.parse_args()
 text=subprocess.check_output(['pdftotext','-layout',args.pdf,'-'],text=True)
 tables=parse_text(text);Path(args.output).write_text(json.dumps(tables,ensure_ascii=False,indent=2)+'\n');print(len(tables),'tables')
