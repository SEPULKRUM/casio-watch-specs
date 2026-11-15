// Evidence categories describe the claim, independently of tile and watch colours.
export const letterPalette=['#8a2940','#17607b','#654397','#386337','#72562e','#684766'];
const colorNames=['','Black','Blue','Green','Red','Brown','Purple','White','Silver / gray','Yellow / gold'];
export const colorSwatches=['','#111111','#176db4','#287b43','#c73336','#805334','#75459c','#ffffff','#a5a8ae','#d1ad3e'];
export function prefixLetters(prefix){
 return [...prefix].map((letter,index)=>{
  let meaning='Meaning unverified',evidence='unverified';
  if(index===0&&letter==='G'&& !['GL','GLX'].includes(prefix)){meaning='G-SHOCK brand association; no universal letter expansion established';evidence='secondary_reported'}
  if(prefix==='GPW'&&letter==='P'){meaning='Positioning / GPS — proposed community interpretation';evidence='community_interpretation'}
  if(['GPW','GWG','GW','GMW','PRW'].includes(prefix)&&letter==='W'){meaning='Wave Ceptor — proposed community interpretation';evidence='community_interpretation'}
  return {letter,position:index+1,meaning,evidence,background:letterPalette[index%letterPalette.length]};
 });
}
export function modelColor(result){
 const variant=result.segments?.find(s=>s.type==='variant');
 const digit=variant?.token.match(/^[1-9]/)?.[0];
 if(!digit)return null;
 const fact=result.exact?.specs?.color;
 if(fact){const actual=String(fact.value),index=colorNames.findIndex(name=>name&&actual.toLowerCase()===name.toLowerCase());return {digit,label:actual,swatch:colorSwatches[index>0?index:8],evidence:'secondary_reported',note:`Exact catalog colour overrides the working ${colorNames[Number(digit)]} heuristic. Inspect the model specification evidence for provenance.`,actual,actualStatus:fact.status||'unverified'};}
 return {digit,label:colorNames[Number(digit)],swatch:colorSwatches[Number(digit)],evidence:'unverified',note:'Working colour heuristic; not a universal official Casio key.',actual:fact?String(fact.value):null,actualStatus:fact?.status||null};
}
export function officialProductLink(record,model){
 if(!record||record.model!==model||record.official_url_verified!==true||!record.official_url_source||!/^\d{4}-\d{2}-\d{2}$/.test(record.official_url_checked_at||''))return null;
 try{const u=new URL(record.official_product_url);if(u.protocol!=='https:'||u.username||u.password||u.port||!(u.hostname==='casio.com'||u.hostname.endsWith('.casio.com')))return null;
 // The reviewed exact model is mandatory; a matching Casio host alone is insufficient.
 if(record.verified_exact_model!==model)return null;
 const slug=u.pathname.match(/\/product\.([^/]+)\/?$/)?.[1];
 const compact=s=>s.toUpperCase().replace(/[^A-Z0-9]/g,'');
 if(!slug||compact(slug)!==compact(model))return null;
 return u.href;
 }catch{return null}
}
