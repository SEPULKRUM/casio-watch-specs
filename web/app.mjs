import {decoderDisclosure,decoderRules,evidenceName} from './decoder-rules.mjs';
import {value,moduleIds,findModels,stats,safeUrl,validateData,label,display,evidenceLabel,recordEvidenceLabel} from './core.mjs';
import {decodeModel,entries} from './decoder.mjs';
import {validateReferences,findReferences,referenceStatus} from './model-references.mjs';
import {modelColor,officialProductLink} from './decoder-presentation.mjs';
import {validateParts,partsForModel} from './parts.mjs';
const $=s=>document.querySelector(s), el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
let references=null,productLinks=null,data=null,parts=null,partsUnavailable=false,state={query:'',family:'',verified:false},activeModel=null,lastDecode=null;
const repo='https://github.com/SEPULKRUM/casio-watch-specs';
function link(text,url){const a=el('a',text);const valid=safeUrl(url);if(valid){a.href=valid;a.target='_blank';a.rel='noopener noreferrer'}return a}
function status(text){$('#data-status').textContent=text}
function setFamily(family){state.family=family;$('#family-select').value=family;render()}
function readHash(){const p=new URLSearchParams(location.hash.slice(1));return p.get('model')}
function closeDetail(){if($('#detail').open)$('#detail').close();activeModel=null;history.replaceState(null,'',location.pathname+location.search)}
function structured(v,parent){
 if(Array.isArray(v)){v.forEach((x,i)=>{if(typeof x==='object'&&x!==null){const group=el('div',undefined,'structured-group');group.append(el('strong',`Entry ${i+1}`));structured(x,group);parent.append(group)}else parent.append(el('span',`${display(x)}${i<v.length-1?' · ':''}`))});return}
 for(const [k,x] of Object.entries(v)){
  if(typeof x==='object'&&x!==null){const group=el('div',undefined,'structured-group');group.append(el('strong',label(k)));structured(x,group);parent.append(group)}
  else{const row=el('div',undefined,'structured-row');row.append(el('span',label(k)),el('span',display(x,k)));parent.append(row)}
 }
}
function fact(field,f){
 const item=el('div',undefined,'fact'),head=el('div',undefined,'fact-head');head.append(el('span',label(field),'fact-label'));
 if(typeof f.value==='object'&&f.value!==null&&field!=='dimensions_mm'){head.append(el('span','Details below','fact-value'));item.append(head);const nested=el('div',undefined,'structured');structured(f.value,nested);item.append(nested)}
 else{head.append(el('span',display(f.value,field),'fact-value'));item.append(head)}
 const details=el('details'),stat=evidenceLabel(f);details.append(el('summary',`${stat} · ${(f.sources||[]).length} source${f.sources?.length===1?'':'s'}`));const evidence=el('div',undefined,'evidence');evidence.append(el('p',f.status==='verified'?'Verification: verified':'Verification: not independently reviewed'));if(f.uncertainty)evidence.append(el('p',f.uncertainty));
 for(const s of f.sources||[]){const source=el('div',undefined,'source');let url=s.url|| (s.reference?`${repo}/blob/main/${s.reference}`:null);if(url){let name=s.kind==='user_provided'?'Owner-supplied evidence':new URL(safeUrl(url)||'https://invalid.example').hostname;source.append(link(name+' ↗',url))}source.append(el('p',`${s.accessed||''}${s.archive_timestamp?' · Archive '+s.archive_timestamp.slice(0,4)+'-'+s.archive_timestamp.slice(4,6)+'-'+s.archive_timestamp.slice(6,8):''}`,'source-location'));if(s.locator)source.append(el('p',s.locator,'source-location'));if(s.evidence)source.append(el('p',s.evidence));if(s.scope_note)source.append(el('p',s.scope_note));if(s.original_url)source.append(link('Original official URL ↗',s.original_url));evidence.append(source)}
 details.append(evidence);item.append(details);return item;
}
function addFacts(parent,record,excluded=[]){
 let total=0;for(const [field,f] of Object.entries(record?.specs||{})){if(excluded.includes(field))continue;if(state.verified&&f.status!=='verified')continue;parent.append(fact(field,f));total++}
 if(!total)parent.append(el('p','No specification fields recorded for this profile.','detail-description'));
}
function partsSection(model){
 const section=el('section',undefined,'detail-section parts-section');section.append(el('h3','Parts & service'));
 const row=partsForModel(parts,model.id);
 if(row){section.append(link(`View Boley parts listing for ${row.listed_model} ↗`,row.url),el('p',`Model listing checked ${row.accessed}. Part numbers and availability are maintained by Boley.`,'detail-description'));
  if(row.observed_qw_codes.length)section.append(el('p','Supplier module code: '+row.observed_qw_codes.join(' / '),'detail-description'));
  if(row.module_comparison==='needs_review')section.append(el('p','Boley’s QW reference differs from the recorded module reference. The assignment needs review.','unknowns'));
  if(row.observed_qw_codes.length)section.append(el('p','Supplier references are recorded separately from official Casio module evidence.','detail-description'));
 }else section.append(el('p',partsUnavailable?'Parts links are temporarily unavailable.':parts?'No exact Boley model listing has been linked yet.':'Loading parts references…','detail-description'),link('Browse Boley’s Casio directory ↗','https://boley.de/en/case-parts/casio'));
 return section;
}
function watchCard(model){
 const card=el('section',undefined,'watch-link-card');
 const url=officialProductLink(productLinks?.models?.[model.id],model.id);
 const icon=el('span','◷','watch-outline');icon.setAttribute('aria-hidden','true');card.append(icon);
 if(url)card.append(link(`SEE THE WATCH · ${model.id} ↗`,url));
 else card.append(el('p','Official Casio product page unavailable'));
 return card;
}
function openModel(id,write=true){
 const model=data.models[id];if(!model)return;activeModel=id;const body=$('#detail-body');body.replaceChildren();body.append(el('div',value(model,'series')||'Casio','detail-family'),el('h2',id));body.querySelector('h2').id='detail-title';body.append(el('span',recordEvidenceLabel(model),'pill'));
 const share=el('button','Copy model link','text-button detail-link');share.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(location.href);share.textContent='Link copied'}catch{share.textContent='Copy the address from your browser'}});body.append(share,watchCard(model),partsSection(model));
 const section=el('section',undefined,'detail-section');section.append(el('h3','Watch specifications'),el('p','Case, materials and appearance belong to this model.','detail-description'));addFacts(section,model,['series','module_id','module_candidates']);
 const missing=['dimensions_mm','weight_g','case_material','band_material','glass','water_resistance_rating'].filter(k=>!model.specs[k]);if(missing.length)section.append(el('p','Not recorded: '+missing.map(label).join(' · '),'unknowns'));body.append(section);
 const moduleSection=el('section',undefined,'detail-section'),ids=moduleIds(model),ambiguous=Boolean(value(model,'module_candidates'));moduleSection.append(el('h3',ambiguous?'Module options':'Module functions'));
 moduleSection.append(el('p',ambiguous?'The cited guide or listing covers multiple modules. The exact fitted module is unresolved; each recorded profile is shown separately.':'Module functions are stored separately from the watch case. The reference describes the available source evidence.','detail-description'));
 if(model.specs.module_id)moduleSection.append(fact('module_id',model.specs.module_id));if(model.specs.module_candidates)moduleSection.append(fact('module_candidates',model.specs.module_candidates));if(model.module)moduleSection.append(el('p',`Module ${model.module} · preserved legacy association; not independently reverified.`,'detail-description'));
 if(!ids.length)moduleSection.append(el('p','No module reference recorded.','unknowns'));
 for(const id of ids){const profile=data.modules[id],option=el('details',undefined,'module-option');if(!ambiguous)option.open=true;const sum=el('summary',`Module ${id}`);const polarity=value(profile,'display_polarity');if(polarity)sum.append(el('small',display(polarity,'display_polarity')));option.append(sum);if(profile)addFacts(option,profile);else option.append(el('p','This candidate module does not yet have a researched specification profile.','detail-description'));moduleSection.append(option)}
 body.append(moduleSection);if(write)history.replaceState(null,'',`#model=${encodeURIComponent(model.id)}`);if(!$('#detail').open)$('#detail').showModal();$('#detail').scrollTop=0;
}

function renderReferenceMatches(query){
 const root=$('#reference-matches');root.replaceChildren();
 if(!references)return;
 const found=findReferences(references,query);if(!query.trim())return;
 const header=el('p',`${found.total} matching model / series references${found.total>found.models.length?` · showing ${found.models.length}`:''}`,'reference-count');root.append(header);
 if(!found.total)return;
 root.append(el('p','Research identifiers may be partial or misread. These are separate from specification records. An index check confirms a mention, not the watch’s features.','decoder-disclosure'));
 for(const model of found.models){
  const item=el('details',undefined,'reference-item'),summary=el('summary');summary.append(el('strong',model.id),el('small',referenceStatus(model)));item.append(summary);
  if(model.reading_flags.length)item.append(el('p','Reading needs extra review: '+model.reading_flags.join(' · '),'unknowns'));
  for(const observation of model.observations.slice(0,5)){
   const source=references.sources[observation.source_id];
   const text=source.filename+(observation.pdf_page?` · PDF page ${observation.pdf_page}`:'')+(observation.compilation_page?` · compilation page ${observation.compilation_page}`:'')+(observation.line?` · line ${observation.line}`:'');
   item.append(el('p',text,'source-location'));
   if(source.availability==='received_secondary_guide')item.append(el('small','Supplied reference guide; model features and letter meanings need independent verification.'));
   else if(source.availability.startsWith('received_zip_research_note'))item.append(el('small','Supplied research note only; not primary model verification.'));
   else if(source.availability!=='received_pdf')item.append(el('small','Original source not included in the seven uploads; page claim remains unverified.'));
  }
  if(model.observations.length>5)item.append(el('small',`${model.observations.length-5} further observations in the download.`));
  const use=el('button','Decode this reference','text-button');use.type='button';use.addEventListener('click',()=>submitPrefix(model.id));item.append(use);root.append(item);
 }
}
async function loadReferences(remote=false){
 try{const url=remote?'https://raw.githubusercontent.com/SEPULKRUM/casio-watch-specs/main/data/model-references.json':'model-references.json';const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error();references=validateReferences(await r.json());$('#reference-coverage').textContent=`${entries.length} prefix patterns · ${references.counts.model_strings.toLocaleString()} research model strings · ${references.counts.index_checked} index identifiers checked`;renderPrefix($('#prefix-input').value)}
 catch{if(!references)$('#reference-coverage').textContent='Research model references unavailable; prefix decoding still works.'}
}

function renderPrefix(query,force=false){
 renderReferenceMatches(query);
 const result=decodeModel(query,data,references),root=$('#prefix-result');lastDecode=result;
 if(!result.recognized){root.replaceChildren();root.hidden=!force||result.empty;if(!root.hidden)root.append(el('p',result.reason,'decode-missing'));return result}
 root.hidden=false;root.replaceChildren();const header=el('div',undefined,'decode-header');header.append(el('h3',result.normalized),el('span',result.family,'decode-family'));root.append(header);
 if(result.references?.length)root.append(el('p',referenceStatus(result.references[0])+' · Model / series mention only; specifications are separate.','decode-coverage'));
 const chips=el('div',undefined,'decode-chips');for(const segment of result.segments)chips.append(el('span',segment.token,'decode-chip '+segment.type));root.append(chips);
 for(const segment of result.segments){
  const row=el('div',undefined,'decode-row'),description=el('div');description.append(el('h4',segment.title));
  if(segment.type==='prefix'&&segment.communityMeaning){
   const meaning=segment.communityMeaning;
   description.append(el('p','The community understands this prefix as:','community-meaning-label'),el('p',meaning.meaning,'community-meaning'),el('small',evidenceName(meaning.status)),el('small',meaning.note),link(meaning.locator+' ↗',meaning.source));
  }else{description.append(el('p',segment.description),el('small',evidenceName(segment.status||'Reference')));if(segment.source)description.append(link('Reference source ↗',segment.source));}
  row.append(el('div',segment.token,'decode-token'),description);root.append(row);
 }
 const color=modelColor(result);
 if(color){const section=el('section',undefined,'model-color');section.append(el('h4','Model color code'));const swatch=el('span',undefined,'color-swatch');swatch.style.backgroundColor=color.swatch;swatch.setAttribute('aria-hidden','true');const line=el('p');line.append(swatch,el('strong',`${color.digit} · ${color.label}`));section.append(line,el('p',color.note),el('small',evidenceName(color.evidence)));if(color.actual)section.append(el('p',`Exact catalog colour: ${color.actual}. Catalog evidence takes precedence over the heuristic (${color.actualStatus}).`));root.append(section)}
 if(result.officialFeatures){const box=el('section',undefined,'confirmed-features');box.append(el('h4','Features confirmed by Casio'),el('p',result.officialFeatures.description));if(result.officialFeatures.technologyName)box.append(el('p','Official technology name: '+result.officialFeatures.technologyName));box.append(link('Casio feature reference ↗',result.officialFeatures.source),el('small','Confirms the cited model’s features; individual letter expansions remain interpretations.'));root.append(box)}
 if(result.appearanceObservation){const observation=result.appearanceObservation,box=el('section',undefined,'confirmed-features');box.append(el('h4','Appearance observed in Casio’s product image'),el('p',`${observation.polarity==='negative'?'Negative LCD: light digits on a dark background.':'Positive LCD: dark digits on a light background.'} ${observation.accents}.`),link('Casio model reference ↗',observation.source));if(observation.comparison_model)box.append(el('p',`Compared model: ${observation.comparison_model}`));box.append(el('small','Product-image observation; the Blackout / Black Accent letter reading remains a community interpretation.'));root.append(box)}
 const coverage=el('div',undefined,'decode-coverage');
 if(result.exact){coverage.append(el('div',`Full specification record available: ${result.exact.id}`));const button=el('button','Open watch specifications','primary');button.addEventListener('click',()=>openModel(result.exact.id));coverage.append(button)}
 else coverage.append(el('div',result.prefixOnly?'Family decoded. Enter a complete model to check for an exact specification record.':`Prefix decoded. This exact model is not yet in the ${data?Object.keys(data.models).length:'current'}-model specification catalog. The model-family interpretation is available independently.`));root.append(coverage);return result;
}
function submitPrefix(model){$('#prefix-input').value=model;state.query=model;$('#search').value=model;if(data)render();renderPrefix(model,true)}

function render(){if(!data)return;renderPrefix(state.query);const found=findModels(data,state);$('#result-count').textContent=`${found.length} of ${Object.keys(data.models).length} models`;$('#list-heading').textContent=state.family||'Watch specifications';
 for(const b of document.querySelectorAll('.family'))b.setAttribute('aria-pressed',String(b.dataset.family===state.family));const list=$('#results');list.replaceChildren();
 for(const m of found){const tr=el('tr'),td=el('td'),b=el('button',undefined,'model-button');b.type='button';b.setAttribute('aria-label',`Open ${m.id}`);const mark=el('span','C','watch-mark');mark.setAttribute('aria-hidden','true');const title=el('span');title.append(el('strong',m.id));title.append(el('small',recordEvidenceLabel(m)));b.append(mark,title);b.addEventListener('click',()=>openModel(m.id));td.append(b);tr.append(td,el('td',value(m,'series')||'—'));
 const ids=moduleIds(m),mod=el('td');mod.append(el('span',ids.length?ids.join(' / '):'Unknown','module-tag'+(ids.length>1?' ambiguous':'')));tr.append(mod,el('td',value(m,'water_resistance_rating')||(value(m,'water_resistance_m')!==null?value(m,'water_resistance_m')+' m':'—')),el('td',value(m,'weight_g')!==null?display(value(m,'weight_g'),'weight_g'):'—'));const arrow=el('td'),open=el('button','↗','row-open');open.setAttribute('aria-label',`View specifications for ${m.id}`);open.addEventListener('click',()=>openModel(m.id));arrow.append(open);tr.append(arrow);list.append(tr)}
 $('#empty').hidden=found.length!==0;$('#empty-message').textContent=state.verified?'No matching models have independently verified facts yet. Turn off the verified filter to explore pending research.':lastDecode?.recognized?'The model prefix is decoded above. Full specifications for this search are not yet in the catalog.':'Try another model, material or module number.';
}
function installData(next){data=validateData(next);const s=stats(data);$('#model-count').textContent=s.models;$('#module-count').textContent=s.modules;$('#fact-count').textContent=s.fields.toLocaleString();const nav=$('#families');nav.replaceChildren();const families=[['',s.models],...Object.entries(s.families).sort((a,b)=>a[0].localeCompare(b[0]))];const select=$('#family-select');select.replaceChildren();
 for(const [family,count] of families){const b=el('button',undefined,'family');b.dataset.family=family;b.append(el('span',family||'All watches'),el('span',count,'family-count'));b.addEventListener('click',()=>setFamily(family));nav.append(b);const o=el('option',`${family||'All families'}${family?' · '+count:''}`);o.value=family;select.append(o)}
 if(state.family&&!s.families[state.family])state.family='';select.value=state.family;$('#load-error').hidden=true;render();const id=readHash();if(id)openModel(id,false);
}
async function loadParts(remote=false){try{const url=remote?'https://raw.githubusercontent.com/SEPULKRUM/casio-watch-specs/main/data/parts-links.json':'parts-links.json';const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error('Parts references unavailable');parts=validateParts(await r.json());partsUnavailable=false}catch{if(!parts)partsUnavailable=true}if(activeModel&&data&&$('#detail').open)openModel(activeModel,false)}
async function loadProductLinks(){try{const r=await fetch('official-product-links.json',{cache:'no-store'});if(!r.ok)throw Error();const next=await r.json();if(next.schema_version===1&&next.models)productLinks=next}catch{productLinks=null}if(activeModel&&data&&$('#detail').open)openModel(activeModel,false)}
async function load(remote=false){loadParts(remote);loadProductLinks();loadReferences(remote);$('#refresh').disabled=true;status(remote?'Checking GitHub…':'Loading catalog…');try{const url=remote?'https://raw.githubusercontent.com/SEPULKRUM/casio-watch-specs/main/data/catalog.json':'catalog.json';const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error(`Catalog request returned ${r.status}.`);const next=await r.json();installData(next);status(remote?'Latest GitHub data loaded':'Bundled catalog loaded');$('#updated').textContent=remote?'Refreshed just now · main branch':'Snapshot · 15 November 2026'}catch(e){if(data)status('Refresh unavailable · showing saved snapshot');else{$('#load-error').hidden=false;$('#load-message').textContent=e.message;status('Catalog unavailable')}}finally{$('#refresh').disabled=false}}
$('#decoder-disclosure').textContent=decoderDisclosure;for(const rule of decoderRules)$('#decoder-rules').append(el('li',rule));
$('#prefix-form').addEventListener('submit',e=>{e.preventDefault();submitPrefix($('#prefix-input').value)});for(const b of document.querySelectorAll('[data-model]'))b.addEventListener('click',()=>submitPrefix(b.dataset.model));$('#prefix-input').addEventListener('input',e=>renderPrefix(e.target.value));$('#search').addEventListener('input',e=>{state.query=e.target.value;const decoded=decodeModel(state.query,data,references);if(decoded.recognized)$('#prefix-input').value=state.query;render()});$('#family-select').addEventListener('change',e=>setFamily(e.target.value));$('#verified').addEventListener('change',e=>{state.verified=e.target.checked;render()});$('#refresh').addEventListener('click',()=>load(true));$('#retry').addEventListener('click',()=>load());$('#reset').addEventListener('click',()=>{state={query:'',family:'',verified:false};$('#search').value='';$('#prefix-input').value='';$('#verified').checked=false;setFamily('')});$('#close').addEventListener('click',closeDetail);$('#detail').addEventListener('cancel',e=>{e.preventDefault();closeDetail()});$('#detail').addEventListener('click',e=>{if(e.target===$('#detail')){const r=$('#detail').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right)closeDetail()}});window.addEventListener('hashchange',()=>{const id=readHash();if(id&&data)openModel(id,false);else closeDetail()});document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)&&!$('#detail').open){e.preventDefault();$('#search').focus()}});load();
