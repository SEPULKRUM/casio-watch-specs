import {normalizeKnownModel,modelRule,splitVariant,ruleSources} from './decoder-rules.mjs';
import {exactReferences} from './model-references.mjs';
import {entries} from './prefix-data.mjs';
export {entries};
export const referenceUrl='https://github.com/SEPULKRUM/watch-code-decoder/blob/main/prefixes/index.html';
const compact=s=>String(s).toUpperCase().replace(/[^A-Z0-9]/g,'');
export function decodeModel(input,data=null,references=null){
 const cleaned=String(input||'').trim().toUpperCase().replace(/[−–—]/g,'-').replace(/\s+/g,'');
 if(!cleaned)return {recognized:false,empty:true,segments:[]};
 if(!/^[A-Z0-9-]+$/.test(cleaned))return {recognized:false,reason:'Enter a Casio model or prefix using letters, numbers and hyphens.',segments:[]};
 const key=compact(cleaned),exact=data?Object.values(data.models).find(m=>compact(m.id)===key):null;
 const matches=exactReferences(references,cleaned);
 if(/^\d{2,3}[A-Z]/.test(cleaned)&&matches.length)return {recognized:true,prefix:'',family:'HISTORICAL MODEL REFERENCE',normalized:cleaned,segments:[{type:'series',token:cleaned,title:'Historical numeric model identifier',description:'This source reference uses a numeric-leading designation. No alphabetical prefix or module assignment is inferred.',status:'Research reference · not a verified specification record'}],exact,references:matches,historicalReference:true};
 let family=[...entries].sort((a,b)=>b[1].length-a[1].length).find(e=>key===e[1]||(key.startsWith(e[1])&&/\d/.test(key.slice(e[1].length))));
 if(!family)return {recognized:false,reason:'This prefix is not yet covered by the reference. The model may still be valid.',segments:[],exact};
 const historicalMatches=[...matches,...(references?Object.values(references.models).filter(m=>cleaned.startsWith(m.id+'-')):[])];
 const historicalReference=historicalMatches.some(m=>m.observations.some(o=>['checked_compilation_index','supplied_transcription'].includes(o.role)));
 const historicalCollision=historicalReference&&['GM','GMW','GD','GG','GR','BA'].includes(family[1]);
 if(historicalCollision)family=['HISTORICAL CASIO',family[1],'Historical use of this identifier appears in the compilation index. Features of the modern same-prefix family are not inferred.',family[3],{status:'secondary_reported',source:'https://github.com/SEPULKRUM/casio-watch-specs/blob/main/data/model-references.json'}];
 let normalized=normalizeKnownModel(key,exact?.id||cleaned);
 if(/^PRWS3100(?:1JF)?$/.test(key))normalized=key==='PRWS3100'?'PRW-S3100':'PRW-S3100-1JF';
 if(/^GWGB1000(?:1A)?$/.test(key))normalized=key==='GWGB1000'?'GWG-B1000':'GWG-B1000-1A';
 if(/^GWM5610U?$/.test(key))normalized=key.endsWith('U')?'GW-M5610U':'GW-M5610';
 const prefix=family[1],body=normalized.slice(0,prefix.length).replace(/-/g,'')===prefix?normalized.slice(prefix.length).replace(/^-/,''):key.slice(prefix.length);
 const segments=[{type:'prefix',token:prefix,title:'Model family',description:family[2],source:family[4]?.source||referenceUrl,status:family[4]?.status||'Established family reference'}];
 if(prefix==='DW'){segments[0].description='DW is commonly read by the watch community as Digital Water Resistant. It is used on G-SHOCK and non-G-SHOCK Casio watches. Check the exact model’s water-resistance rating; the prefix alone does not establish 200 m / 20 bar.';segments[0].status='community_interpretation';segments[0].source=ruleSources.dw291;}
 if(key===prefix)return {recognized:true,prefix,family:family[0],normalized,segments,exact,references:matches,historicalReference,prefixOnly:true};
 // Known lines are normalized above; other compact inputs do not receive invented variant boundaries.
 const split=body.split('-'),main=split.shift()||'',tail=split.join('-');
 const match=main.match(/^([A-Z]*)(\d+)([A-Z0-9]*)$/);
 if(!match){segments.push({type:'unknown',token:body,title:'Unresolved model portion',description:'This portion needs a documented model-specific interpretation.',status:'Unresolved'});return {recognized:true,prefix,family:family[0],normalized,segments,exact,references:matches,historicalReference}}
 const [,modifier,number,seriesTail]=match;
 const rule=historicalReference?null:modelRule(prefix,modifier,number);
 if(rule){if(rule.family)family=[rule.family,...family.slice(1)];segments[0].description=rule.prefixDescription;segments[0].source=rule.source;segments[0].status='Community reading · Casio features confirmed separately';}
 const scopedBlack=Boolean(rule?.braceletSuffix&&/^GWB5600BC1B(?:ER)?$/.test(key));
 const prwSpecific=prefix==='PRW'&&modifier==='S'&&number==='3100';
 const updated5610=prefix==='GW'&&modifier==='M'&&number==='5610'&&seriesTail==='U';
 const gwgSpecific=prefix==='GWG'&&modifier==='B'&&number==='1000';
 if(modifier)segments.push({type:'modifier',token:modifier,title:rule?.modifierDescription?'Feature / series modifier':'Series designation',description:rule?.modifierDescription?rule.modifierDescription:prwSpecific?'Real Material Series designation for this PRW-S3100 model, featuring enhanced materials.':gwgSpecific?'B1000 connected model-line designation. Casio confirms Bluetooth smartphone linking for GWG-B1000; this is not a universal meaning of B.':'Model-line modifier. Its feature meaning has not been established for this exact model.',status:rule?.modifierDescription?'community_interpretation':prwSpecific?'Your established model-specific reference':gwgSpecific?'Model-specific official evidence':'Unresolved modifier meaning',source:rule?.modifierDescription?rule.source:gwgSpecific?'https://www.casio.com/us/watches/gshock/product.GWG-B1000-1A/':null});
 segments.push({type:'series',token:updated5610||rule?.splitSuffix?number:number+seriesTail,title:'Model series',description:prwSpecific?'3100 series with STN LCD, as described in your supplied model-specific reference.':`${updated5610||rule?.splitSuffix?number:number+seriesTail} series / model designation. This is not a production date or a module number.`,status:prwSpecific?'Your established model-specific reference':'Model identifier'});
 if(rule?.splitSuffix&&seriesTail)segments.push({type:'series-suffix',token:seriesTail,title:'Series suffix / configuration',description:seriesTail==='BC'&&rule.braceletSuffix?rule.braceletSuffix:'Additional series configuration marker. Its exact material or feature meaning has not been established here.',status:seriesTail==='BC'&&rule.braceletSuffix?'community_interpretation':'unverified',source:seriesTail==='BC'&&rule.braceletSuffix?rule.source:null});
 if(updated5610)segments.push({type:'modifier',token:'U',title:'Updated model',description:'U stands for Updated in the GW-M5610U line: module 3495 replaces module 3159 used in the older GW-M5610-1. This meaning is scoped to this model line.',status:'Owner-supplied model-specific reference'});
 if(tail){const {variant,order,market}=splitVariant(tail);
  if(variant)segments.push({type:'variant',token:variant,title:'Colour / variant code',description:scopedBlack&&variant==='1'?'Black manufacturer colour category for GW-B5600BC-1B / European SKU GW-B5600BC-1BER.':prwSpecific&&variant==='1'?'Black colour variant for this PRW-S3100 model.':exact?.specs?.color?`Exact catalog model colour: ${exact.specs.color.value}. Variant meanings are model-specific.`:'Colour / configuration designation. Its exact colour is not inferred from the number alone.',status:scopedBlack&&variant==='1'?'official_observed':prwSpecific&&variant==='1'?'Your established model-specific reference':exact?.specs?.color?'Exact model catalog evidence':'Variant meaning unresolved',source:scopedBlack?rule.source:null});
  if(order)segments.push({type:'order',token:order,title:'Additional variant / order marker',description:'Additional variation within this colour/configuration code. Its precise display, finish or packaging meaning is unverified; B in this position is not automatically Bluetooth.',status:'unverified'});
  if(market)segments.push({type:'market',token:market,title:'Market suffix',description:market==='ER'?'European-market suffix reference. This does not state the manufacturing country.':'Japanese-market model suffix. This does not state the manufacturing country.',status:'Market reference · secondary interpretation'});
 }
 const officialFeatures=rule?{...rule.officialFeatures,source:rule.source}:null;
 const scopedColor=scopedBlack?{digit:'1',label:'Black',source:rule.source,status:'official_observed',scope:'Casio colour metadata for GW-B5600BC-1B / European SKU GW-B5600BC-1BER'}:null;
 return {recognized:true,prefix,family:family[0],normalized,segments,exact,references:matches,historicalReference,officialFeatures,scopedColor};
}
