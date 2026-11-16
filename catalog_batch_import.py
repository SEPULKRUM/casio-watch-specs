"""Parse selected facts from the supplied Oceanus, 2016 and WATCHNAVI text extractions."""
import argparse
import json
import re
import subprocess
from pathlib import Path

COLLECTIONS={'G-SHOCK','BABY-G','OCEANUS','EDIFICE','SHEEN','PRO TREK','PHYS','SPORTS GEAR','LINEAGE','WAVE CEPTOR'}

def parse_catalog(text,kind):
    sections=[];models=[];section=None;collection=None;columns=None;labels=None;mode=None;notes=[]
    for page_number,page in enumerate(text.split('\f'),1):
        for line in page.splitlines():
            s=line.strip()
            if not s or s.startswith(('CASIO OCEANUS + G-SHOCK |','CASIO WATCH COLLECTION 2016 VOL.1 /')):continue
            if kind=='oceanus' and s=='Technical details and source interpretation':mode='notes';columns=None;continue
            if kind=='2016' and s=='DATA QUALITY & SOURCE NOTES':mode='notes';columns=None;continue
            if mode=='notes':notes.append({'extraction_pdf_page':page_number,'text':s});continue
            if kind=='oceanus' and s.startswith(('OCEANUS /','G-SHOCK /')):
                collection=s.split(' /')[0];section={'collection':collection,'title':s,'description':[],'reference_notes':[],'extraction_pdf_page':page_number};sections.append(section);columns=None;mode='description';continue
            if kind=='2016' and s in COLLECTIONS:
                collection=s;section=None;columns=None;mode=None;continue
            if kind=='oceanus' and all(x in line for x in ['Exact model code','Original price (JPY)','Variant / identifying detail','PDF page','Module']):
                labels=['Exact model code','Original price (JPY)','Variant / identifying detail','PDF page','Module'];columns=[line.index(x) for x in labels];mode='table';continue
            if kind=='2016' and all(x in line for x in ['MODEL (EXACT JDM REFERENCE)','JPY + TAX','PDF p.']):
                labels=['MODEL (EXACT JDM REFERENCE)','JPY + TAX','PDF p.'];columns=[line.index(x) for x in labels];mode='table';continue
            if columns and mode=='table':
                cells=[line[a:b].strip() for a,b in zip(columns,columns[1:]+[None])]
                raw=cells[0];id=raw.replace('[CHECK]','').strip();original_page=cells[3] if kind=='oceanus' else cells[2]
                if re.fullmatch(r'[A-Z]{1,5}-[A-Z0-9]+(?:-[A-Z0-9]+){0,2}',id) and original_page.isdigit():
                    models.append({'id':id,'printed_label':raw,'uncertain_suffix':'[CHECK]' in raw,'collection':collection,'section':len(sections)-1,'extraction_pdf_page':page_number,'original_pdf_page':int(original_page),'fields':dict(zip(labels,cells))});continue
            if s.startswith('Reference note:') and section:
                section['reference_notes'].append(s);continue
            if kind=='2016' and collection and len(line)-len(line.lstrip())<=2 and not s.endswith('.') and not any(x in s for x in [';','[',']']) and len(s)<100:
                letters=[c for c in s if c.isalpha()]
                if letters and sum(c.isupper() for c in letters)/len(letters)>.9:
                    section={'collection':collection,'title':s,'description':[],'reference_notes':[],'extraction_pdf_page':page_number};sections.append(section);columns=None;mode='description';continue
            if section and mode=='description':section['description'].append(s)
    return {'models':models,'sections':sections,'technical_and_source_notes':notes}

def parse_watchnavi(text):
    placements=[];unresolved=[];year=None;current=None;columns=None;appendix=False
    for pdf_page,page in enumerate(text.split('\f'),1):
        for line in page.splitlines():
            s=line.strip()
            if 'Appendix - unresolved OCR model labels' in s:appendix=True;current=None;continue
            if appendix:
                m=re.match(r'^\s*(\d+)\s+(\d+/\d+)\s+(.+?)\s*$',line)
                if m:unresolved.append({'printed_page':int(m[1]),'original_pdf_page_reference':int(m[1])-1,'row_column':m[2],'raw_label':m[3],'extraction_pdf_page':pdf_page,'status':'unresolved_ocr_label_not_corrected'})
                continue
            if m:=re.fullmatch(r'(19\d{2}|20\d{2}) \| \d+ model entries',s):year=int(m[1]);current=None;continue
            if all(x in line for x in ['Model (OCR-derived)','Page','Caption excerpt / explicitly mentioned features']):columns=[line.index(x) for x in ['Model (OCR-derived)','Page','Caption excerpt / explicitly mentioned features']];continue
            if not columns or not year or not s or s.startswith(('G-SHOCK / WATCHNAVI','Index derived exclusively')):continue
            cells=[line[a:b].strip() for a,b in zip(columns,columns[1:]+[None])]
            if cells[0] and (m:=re.fullmatch(r'p\.\s*(\d+)',cells[1])):
                current={'printed_label':cells[0],'model_string':cells[0].rstrip('*'),'ocr_review_flag':cells[0].endswith('*'),'year_heading':year,'year_scope':'Historical heading; approximate around transitions, not a verified release date','printed_page':int(m[1]),'original_pdf_page_reference':int(m[1])-1,'extraction_pdf_page':pdf_page,'caption_lines':[cells[2]] if cells[2] else [],'feature_phrases':[],'visual_check_reported_by_compilation':False};placements.append(current);continue
            if current and not cells[0] and not cells[1] and cells[2]:
                if cells[2].startswith('Feature phrases:'):current['feature_phrases'].extend(x.strip() for x in cells[2].split(':',1)[1].split(';'))
                elif cells[2]=='Model code checked visually.':current['visual_check_reported_by_compilation']=True
                else:current['caption_lines'].append(cells[2])
    return {'placements':placements,'unresolved_labels':unresolved}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kind',choices=['oceanus','2016','watchnavi']);p.add_argument('pdf');p.add_argument('--output',required=True);args=p.parse_args();text=subprocess.check_output(['pdftotext','-layout',args.pdf,'-'],text=True);data=parse_watchnavi(text) if args.kind=='watchnavi' else parse_catalog(text,args.kind);Path(args.output).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:len(v) for k,v in data.items()}))
