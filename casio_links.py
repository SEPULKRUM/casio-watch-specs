"""Generate audited official Casio destinations; never guess a model URL."""
import argparse,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
REFERENCE='research/official-casio-link-checks-2026-11-17.json'
WEB='web/official-casio-links-data.mjs'
DOMAINS=('casio.com','casio.jp','casio.co.jp','casio.com.cn','casio-europe.com')
def official_url(raw):
 try:
  u=urlsplit(raw);return u.scheme=='https' and not u.username and not u.password and not u.port and any(u.hostname==d or (u.hostname or '').endswith('.'+d) for d in DOMAINS)
 except (ValueError,TypeError):return False

def reference_key(identifier,aliases=None):
 value=str(identifier).strip().upper()
 if re.search(r'-[1-9][A-Z0-9]*(?:JF|JR|ER|DR|CR|DF)$',value):value=re.sub(r'(?:JF|JR|ER|DR|CR|DF)$','',value)
 return re.sub('[^A-Z0-9]','',(aliases or {}).get(value,value))

def artifacts(root):
 source=(root/REFERENCE).read_bytes();n=json.loads(source);entries={};aliases=json.loads((root/'research/model-identity-rules-2026-11-17.json').read_text())['aliases']
 for key,row in n['selected'].items():
  if not row.get('accepted') or row.get('status')!=200 or not row.get('model_identity_confirmed') or row.get('kind') not in ('product','support') or not official_url(row.get('final_url','')):raise ValueError('Unverified or non-official selected destination')
  if reference_key(row['page_model'],aliases)!=key:raise ValueError('Destination variant mismatch')
  if row['kind']=='product' and not row.get('has_specifications'):raise ValueError('Product destination lacks specification content')
  entries[key]={'url':row['final_url'],'kind':row['kind'],'page_model':row['page_model'],'checked_at':row['checked_at']}
 data={'schema_version':1,'source_reference':REFERENCE,'source_file_sha256':hashlib.sha256(source).hexdigest(),'homepage':'https://www.casio.com/','entries':entries}
 return {WEB:'export const officialCasioLinks='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
 for name,s in artifacts(root).items():
  path=root/name
  if a.check:
   if path.read_text()!=s:raise ValueError('Stale official Casio links')
  else:path.write_text(s)
if __name__=='__main__':main()
