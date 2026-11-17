"""Generate exact owner-provided official support fallbacks without promoting specs."""
import argparse,json,hashlib
from pathlib import Path
REFERENCE='research/official-support-fallbacks-2026-11-17.json'
def artifact(root):
 raw=(root/REFERENCE).read_bytes();n=json.loads(raw)
 return "import {modelIdentityRules} from './model-identity-data.mjs';\nexport const officialSupportReferences="+json.dumps(n,separators=(',',':'))+';\n'+'''export function officialSupportForModel(id){
 const target=officialSupportReferences.models[id]?id:modelIdentityRules.aliases[id];
 const raw=officialSupportReferences.models[target];if(!raw)return null;
 try{const u=new URL(raw),slug=u.pathname.match(/\\/support\\.([^/]+)\\/?$/)?.[1];if(u.protocol!=='https:'||u.username||u.password||u.port||!(u.hostname==='casio.com'||u.hostname.endsWith('.casio.com'))||slug!==target)return null;return {url:u.href,model:target,kind:'support',source_reference:"'''+REFERENCE+'''"};}catch{return null}
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parent;out=r/'web/official-support.mjs';s=artifact(r)
 if a.check:
  if out.read_text()!=s:raise ValueError('Stale official support fallbacks')
 else:out.write_text(s)
if __name__=='__main__':main()
