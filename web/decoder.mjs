import {entries} from './prefix-data.mjs';
export {entries};
export const referenceUrl='https://github.com/SEPULKRUM/watch-code-decoder/blob/main/prefixes/index.html';
const compact=s=>String(s).toUpperCase().replace(/[^A-Z0-9]/g,'');
export function decodeModel(input,data=null){
 const cleaned=String(input||'').trim().toUpperCase().replace(/[−–—]/g,'-').replace(/\s+/g,'');
 if(!cleaned)return {recognized:false,empty:true,segments:[]};
 if(!/^[A-Z0-9-]+$/.test(cleaned))return {recognized:false,reason:'Enter a Casio model or prefix using letters, numbers and hyphens.',segments:[]};
 const key=compact(cleaned),exact=data?Object.values(data.models).find(m=>compact(m.id)===key):null;
 const family=[...entries].sort((a,b)=>b[1].length-a[1].length).find(e=>key===e[1]||(key.startsWith(e[1])&&/\d/.test(key.slice(e[1].length))));
 if(!family)return {recognized:false,reason:'This prefix is not yet covered by the reference. The model may still be valid.',segments:[],exact};
 let normalized=exact?.id||cleaned;
 if(/^PRWS3100(?:1JF)?$/.test(key))normalized=key==='PRWS3100'?'PRW-S3100':'PRW-S3100-1JF';
 if(/^GWGB1000(?:1A)?$/.test(key))normalized=key==='GWGB1000'?'GWG-B1000':'GWG-B1000-1A';
 const prefix=family[1],body=normalized.slice(0,prefix.length).replace(/-/g,'')===prefix?normalized.slice(prefix.length).replace(/^-/,''):key.slice(prefix.length);
 const segments=[{type:'prefix',token:prefix,title:'Model family',description:family[2],source:referenceUrl,status:'Established family reference'}];
 if(key===prefix)return {recognized:true,prefix,family:family[0],normalized,segments,exact,prefixOnly:true};
 // Delimiters preserve suffix boundaries; compact input is not given invented variant boundaries.
 const split=body.split('-'),main=split.shift()||'',tail=split.join('-');
 const match=main.match(/^([A-Z]*)(\d+)([A-Z0-9]*)$/);
 if(!match){segments.push({type:'unknown',token:body,title:'Unresolved model portion',description:'This portion needs a documented model-specific interpretation.',status:'Unresolved'});return {recognized:true,prefix,family:family[0],normalized,segments,exact}}
 const [,modifier,number,seriesTail]=match;
 const prwSpecific=prefix==='PRW'&&modifier==='S'&&number==='3100';
 const gwgSpecific=prefix==='GWG'&&modifier==='B'&&number==='1000';
 if(modifier)segments.push({type:'modifier',token:modifier,title:'Series designation',description:prwSpecific?'Real Material Series designation for this PRW-S3100 model, featuring enhanced materials.':gwgSpecific?'B1000 connected model-line designation. Casio confirms Bluetooth smartphone linking for GWG-B1000; this is not a universal meaning of B.':'Model-line modifier. Its feature meaning has not been established for this exact model.',status:prwSpecific?'Your established model-specific reference':gwgSpecific?'Model-specific official evidence':'Unresolved modifier meaning',source:gwgSpecific?'https://www.casio.com/us/watches/gshock/product.GWG-B1000-1A/':null});
 segments.push({type:'series',token:number+seriesTail,title:'Model series',description:prwSpecific?'3100 series with STN LCD, as described in your supplied model-specific reference.':`${number+seriesTail} series / model designation. This is not a production date or a module number.`,status:prwSpecific?'Your established model-specific reference':'Model identifier'});
 if(tail){let variant=tail,market='';if(tail.endsWith('JF')){market='JF';variant=tail.slice(0,-2)}
  if(variant)segments.push({type:'variant',token:variant,title:'Variant designation',description:prwSpecific&&variant==='1'?'Black colour variant for this PRW-S3100 model.':exact?.specs?.color?`Exact catalog model colour: ${exact.specs.color.value}. Variant meanings are model-specific.`:'Colour / configuration designation. Its exact colour is not inferred from the number alone.',status:prwSpecific&&variant==='1'?'Your established model-specific reference':exact?.specs?.color?'Exact model catalog evidence':'Variant meaning unresolved'});
  if(market)segments.push({type:'market',token:market,title:'Market suffix',description:'Japanese-market model suffix. This does not state the manufacturing country.',status:'Your established suffix reference'});
 }
 return {recognized:true,prefix,family:family[0],normalized,segments,exact};
}
