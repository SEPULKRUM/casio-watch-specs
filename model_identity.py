"""Reproduce source-bound presentation rules for documented model spellings."""
import argparse,json,hashlib
from pathlib import Path
REFERENCE='research/model-identity-rules-2026-11-17.json'
def artifact(root):
 raw=(root/REFERENCE).read_bytes();data=json.loads(raw)
 return 'export const modelIdentityRules='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\nexport const modelIdentitySource='+json.dumps({'source_reference':REFERENCE,'sha256':hashlib.sha256(raw).hexdigest()},separators=(',',':'))+';\n'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parent;out=r/'web/model-identity-data.mjs';s=artifact(r)
 if a.check:
  if out.read_text()!=s:raise ValueError('Stale model identity rules')
 else:out.write_text(s)
if __name__=='__main__':main()
