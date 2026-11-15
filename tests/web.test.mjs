import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {findModels,moduleIds,stats,value,safeUrl,validateData,display} from '../web/core.mjs';
const data=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url)));
test('all models and exact family totals are available',()=>{const s=stats(data);assert.equal(findModels(data).length,s.models);assert.equal(Object.values(s.families).reduce((a,b)=>a+b,0),s.models);assert.equal(findModels(data,{family:'Edifice'}).length,s.families.Edifice)});
test('model search ignores punctuation and can search linked module facts',()=>{assert.ok(findModels(data,{query:'g-9000ms'}).some(m=>m.id==='G9000MS-1'));assert.ok(findModels(data,{query:'solar'}).length>0);assert.equal(findModels(data,{query:'does-not-exist-anywhere-9182'}).length,0)});
test('shared references stay separate and LCD polarity is preserved',()=>{assert.deepEqual(moduleIds(data.models['G-9300-1']),['3261','3281']);assert.equal(value(data.modules['3261'],'display_polarity'),'positive');assert.equal(value(data.modules['3281'],'display_polarity'),'negative')});
test('both thickness claims survive without selected dimensions',()=>{const m=data.models['PAW2000-1'];assert.equal(value(m,'promotional_thickness_mm'),11.5);assert.equal(value(m,'technical_table_thickness_mm'),11.3);assert.equal(value(m,'dimensions_mm'),null);assert.equal(display(value(m,'technical_table_thickness_mm'),'technical_table_thickness_mm'),'11.3 mm')});
test('verified filter does not present pending research as verified',()=>{assert.equal(findModels(data,{verified:true}).length,0);const copy=structuredClone(data),m=copy.models['G9000MS-1'];m.specs.weight_g.status='verified';assert.ok(findModels(copy,{verified:true}).some(r=>r.id===m.id));assert.equal(findModels(copy,{verified:true,query:'matte'}).length,0)});
test('unsafe source links and invalid catalogs are rejected',()=>{for(const u of ['javascript:alert(1)','data:text/html,hi','http://example.org','https://name:secret@example.org'])assert.equal(safeUrl(u),null);assert.equal(safeUrl('https://www.casio.com/'),'https://www.casio.com/');assert.throws(()=>validateData({schema_version:1,models:{},modules:{}}));assert.equal(validateData(data),data)});
const {decodeModel}=await import('../web/decoder.mjs');
test('GWG prefix decodes with and without a separator outside catalog coverage',()=>{for(const s of ['gwg-b1000','gwgb1000']){const r=decodeModel(s,data);assert.equal(r.prefix,'GWG');assert.equal(r.exact,undefined);assert.deepEqual(r.segments.map(s=>s.token),['GWG','B','1000']);assert.match(r.segments[1].description,/Bluetooth/)} });
test('established PRW-S3100 breakdown retains scoped S, STN and JF meanings',()=>{const r=decodeModel('PRW-S3100-1JF',data);assert.deepEqual(r.segments.map(s=>s.token),['PRW','S','3100','1','JF']);assert.match(r.segments[1].description,/Real Material/);assert.match(r.segments[2].description,/STN/);assert.match(r.segments[3].description,/Black/);assert.match(r.segments[4].description,/Japanese-market/)});
test('special PRW modifier is not generalized to unrelated S models',()=>{const r=decodeModel('PRW-S9999-1JF',data);assert.match(r.segments[1].description,/not been established/);assert.doesNotMatch(r.segments[1].description,/Real Material/);assert.doesNotMatch(r.segments[3].description,/Black/)});
test('longest family matches precede shorter ones and prefix-only lookups work',()=>{assert.equal(decodeModel('GMW-B5000D-1',data).prefix,'GMW');assert.equal(decodeModel('GWG',data).prefix,'GWG');assert.equal(decodeModel('GWG',data).prefixOnly,true)});
test('catalog exact matches remain distinct from reference-only decoding',()=>{const r=decodeModel('g9000ms1',data);assert.equal(r.exact.id,'G9000MS-1');assert.deepEqual(r.segments.map(s=>s.token),['G','9000MS','1'])});
test('unknown and HTML-like input is not guessed or executed',()=>{assert.equal(decodeModel('<img src=x>',data).recognized,false);assert.equal(decodeModel('NONSENSE',data).recognized,false);assert.equal(decodeModel('',data).empty,true)});

test('GW-M5610U separates the update marker from the series',()=>{for(const input of ['GW-M5610U','gwm5610u','GW-M5610U-1','gwm5610u1']){const r=decodeModel(input,data);assert.deepEqual(r.segments.slice(0,4).map(s=>s.token),['GW','M','5610','U']);assert.match(r.segments[3].description,/Updated/);assert.match(r.segments[3].description,/3495/);assert.match(r.segments[3].description,/3159/);assert.match(r.segments[3].status,/Owner-supplied/)}});
test('update meaning stays scoped and original 5610 has no update marker',()=>{assert.deepEqual(decodeModel('GW-M5610',data).segments.map(s=>s.token),['GW','M','5610']);assert.deepEqual(decodeModel('GW-M9999U',data).segments.map(s=>s.token),['GW','M','9999U']);});

const {evidenceLabel,recordEvidenceLabel}=await import('../web/core.mjs');
test('official provenance does not silently verify pending fields',()=>{const f=data.models['GW-M5610U-1'].specs.glass;assert.equal(evidenceLabel(f),'Official Casio source');assert.equal(f.status,'pending_review');assert.notEqual(recordEvidenceLabel(data.models['GW-M5610U-1']),'Verified')});
test('evidence labels preserve conflicts, archives and owner supplied distinctions',()=>{assert.equal(evidenceLabel({uncertainty:'Casio gives different values in its promotional description and technical table',sources:[{url:'https://www.casio.com/'}]}),'Conflicting evidence');assert.equal(evidenceLabel({sources:[{url:'https://web.archive.org/a',original_url:'https://support.casio.com/a',archive_timestamp:'20200101'}]}),'Archived Casio source');assert.equal(evidenceLabel({sources:[{kind:'user_provided'}]}),'Owner-supplied evidence');assert.equal(evidenceLabel({sources:[{url:'https://casio.com.example.org/'}]}),'Other source · unverified');assert.equal(evidenceLabel({status:'verified'}),'Verified');assert.equal(recordEvidenceLabel({specs:{a:{status:'verified'},b:{sources:[]}}}),'Mixed source evidence')});
const {partsForModel,validateParts}=await import('../web/parts.mjs');
test('parts links preserve exact variants and reject unsafe destinations',()=>{const id='GW-M5610-1',row={listed_model:id,url:'https://boley.de/en/case-parts/casio/25194.gw-m5610-1',observed_qw_codes:['QW3159-01']},p={schema_version:1,supplier:'Boley',models:{[id]:row}};assert.equal(validateParts(p),p);assert.equal(partsForModel(p,id).url,row.url);assert.equal(partsForModel(p,'GW-M5610-1B'),null);for(const url of ['javascript:alert(1)','https://boley.de.evil.example/en/case-parts/casio/25194.gw-m5610-1','https://boley.de/en/case-parts/casio/25195.gw-m5610-1b','https://boley.de/en/search?q=5610'])assert.equal(partsForModel({models:{[id]:{...row,url}}},id),null);assert.throws(()=>validateParts({schema_version:1,supplier:'Other',models:{}}))});
test('published parts manifest links only exact catalog models',()=>{const p=validateParts(JSON.parse(fs.readFileSync(new URL('../data/parts-links.json',import.meta.url))));assert.ok(Object.keys(p.models).length>0);for(const [id,row] of Object.entries(p.models)){assert.ok(data.models[id],id);assert.ok(partsForModel(p,id),id);assert.ok(row.accessed);assert.ok(/^[0-9a-f]{64}$/.test(row.snapshot_sha256))}});

const {modelColor,officialProductLink}=await import('../web/decoder-presentation.mjs');
test('colour code requires an explicit variant and never uses series digits',()=>{
 assert.equal(modelColor(decodeModel('GPW-1000')),null);assert.equal(modelColor(decodeModel('GWG-B1000')),null);const color=modelColor(decodeModel('GWG-B1000-1A'));assert.equal(color.digit,'1');assert.equal(color.label,'Black');assert.equal(color.evidence,'unverified');assert.match(color.note,/heuristic/);const result=decodeModel('GWG-B1000-7');result.exact={specs:{color:{value:'Ivory',status:'pending_review'}}};assert.equal(modelColor(result).actual,'Ivory');assert.equal(modelColor(result).label,'Ivory');
});
test('official product cards require exact-model reviewed links and reject sibling/unsafe links',()=>{
 const model='GW-M5610U-1',record={model,verified_exact_model:model,official_product_url:'https://www.casio.com/europe/watches/casio/product.GW-M5610U-1/',official_url_verified:true,official_url_source:{title:model},official_url_checked_at:'2026-11-15'};
 assert.ok(officialProductLink(record,model));assert.equal(officialProductLink(null,model),null);assert.equal(officialProductLink(record,'GW-M5610U-1B'),null);
 for(const url of ['https://casio.com.evil.example/product.GW-M5610U-1/','http://www.casio.com/product.GW-M5610U-1/','https://name:secret@casio.com/product.GW-M5610U-1/','https://www.casio.com/product.GW-M5610U-1B/'])assert.equal(officialProductLink({...record,official_product_url:url},model),null);
 assert.equal(officialProductLink({...record,official_url_verified:false},model),null);
 const app=fs.readFileSync(new URL('../web/app.mjs',import.meta.url),'utf8');assert.match(app,/noopener noreferrer/);assert.match(app,/target='_blank'/);assert.match(app,/Official Casio product page unavailable/);
 const links=JSON.parse(fs.readFileSync(new URL('../data/official-product-links.json',import.meta.url)));for(const [id,row] of Object.entries(links.models)){assert.ok(data.models[id]);if(row.official_url_verified)assert.ok(officialProductLink(row,id),id);else assert.equal(officialProductLink(row,id),null)};
});

const {validateReferences,findReferences,exactReferences,referenceStatus}=await import('../web/model-references.mjs');
const refs=validateReferences(JSON.parse(fs.readFileSync(new URL('../data/model-references.json',import.meta.url))));
test('expanded prefix library recognizes extracted families without inventing expansions',()=>{
 for(const prefix of ['CFX','TC','TGW','DGW','AWG','GPW','IRW','PRX','SPF','LP','MQW','PRJ']){const result=decodeModel(prefix,data,refs);assert.equal(result.prefix,prefix);assert.equal(result.prefixOnly,true);assert.match(result.segments[0].status,/secondary_reported|unverified/)}
 assert.equal(new Set(entriesForReferenceTest.map(x=>x[1])).size,170);
});
const {entries:entriesForReferenceTest}=await import('../web/decoder.mjs');
test('research identifiers remain separate from catalog models and candidates stay labelled',()=>{
 assert.equal(findReferences(refs,'CFX').total>0,true);assert.equal(findReferences(refs,'',12).total,0);const matches=exactReferences(refs,'gmw151v');assert.equal(matches[0].id,'GMW-15-1V');assert.match(referenceStatus(matches[0]),/secondary/);assert.ok(!data.models['GMW-15-1V']);assert.ok(findReferences(refs,'DW').total>12);assert.equal(findReferences(refs,'DW').models.length,12);
 const missing=Object.values(refs.models).find(m=>m.observations.every(o=>o.role==='prior_machine_index'));assert.equal(missing.status,'machine_candidate');assert.match(referenceStatus(missing),/unverified/);
});
test('historical prefix collisions do not inherit modern G-SHOCK features or colour guesses',()=>{
 for(const id of ['GM-40','GMW-15-1V','GD-8-1','GM-40-1']){const result=decodeModel(id,data,refs);assert.equal(result.family,'HISTORICAL CASIO',id);assert.equal(result.historicalReference,true);assert.doesNotMatch(result.segments[0].description,/Full-metal|Metal-covered/);assert.equal(modelColor(result),null);assert.equal(result.segments[0].communityMeaning,null)}
 assert.equal(decodeModel('GMW-B5000D-1',data,refs).family,'G-SHOCK');assert.equal(decodeModel('GW-M5610U-1',data,refs).segments.find(s=>s.token==='U').title,'Updated model');
});
test('numeric-leading historical identifiers are references without guessed prefixes or modules',()=>{
 const result=decodeModel('110QS-37B',data,refs);assert.equal(result.recognized,true);assert.equal(result.prefix,'');assert.equal(result.family,'HISTORICAL MODEL REFERENCE');assert.equal(result.exact,undefined);assert.equal(result.segments.length,1);assert.match(result.segments[0].description,/No alphabetical prefix or module/);
});
test('invalid reference manifests fail safely and cannot introduce markup as model IDs',()=>{
 const bad=structuredClone(refs);bad.models['<img>']={id:'<img>',status:'machine_candidate',observations:[]};assert.throws(()=>validateReferences(bad));const missing=structuredClone(refs);delete missing.sources[Object.keys(missing.sources)[0]];assert.throws(()=>validateReferences(missing));
});

const {decoderDisclosure,decoderRules,evidenceName,ruleSources}=await import('../web/decoder-rules.mjs');
test('every search has a community disclosure and official-feature distinction',()=>{
 assert.match(decoderDisclosure,/Casio.*complete, universal/);assert.match(decoderDisclosure,/watch-community/);assert.match(decoderDisclosure,/features confirmed by Casio/);
 const html=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');assert.match(html,/id="decoder-disclosure"/);assert.match(html,/id="decoder-rules"/);assert.ok(decoderRules.some(s=>s.includes('model-dependent')));assert.equal(evidenceName('community_interpretation'),'Watch-community interpretation');
});
test('GW-B5600BC-1BER separates feature B, bracelet BC, colour, order B and ER',()=>{
 for(const input of ['GW-B5600BC-1BER','gwb5600bc1ber']){const r=decodeModel(input,data,refs);assert.equal(r.normalized,'GW-B5600BC-1BER');assert.deepEqual(r.segments.map(s=>s.token),['GW','B','5600','BC','1','B','ER']);assert.match(r.segments[1].description,/Bluetooth/);assert.match(r.segments[3].description,/bracelet.*composite-band/);assert.equal(r.segments[3].status,'community_interpretation');assert.match(r.segments[5].description,/not the Bluetooth modifier/);assert.equal(r.segments[5].status,'community_interpretation');assert.match(r.segments[6].description,/European-market/);assert.match(r.segments[6].description,/not.*manufacturing/);assert.equal(r.officialFeatures.status,'official_observed');assert.match(r.officialFeatures.description,/composite band/);assert.equal(modelColor(r).label,'Black');assert.equal(modelColor(r).evidence,'official_observed')}
 assert.equal(modelColor(decodeModel('GW-B5600BC-1BJR',data,refs)).evidence,'unverified');
});
test('GMW-B5000 metal and Bluetooth associations are scoped and separate from features',()=>{
 const r=decodeModel('gmw-b5000',data,refs);assert.deepEqual(r.segments.map(s=>s.token),['GMW','B','5000']);assert.equal(modelColor(r),null);assert.match(r.segments[1].description,/Bluetooth/);assert.equal(r.segments[1].status,'community_interpretation');assert.match(r.officialFeatures.description,/metal construction/);assert.match(r.segments[0].communityMeaning.meaning,/Metal-construction/);assert.equal(r.segments[0].communityMeaning.status,'community_interpretation');assert.deepEqual(decodeModel('GMW-B5000D-1ER').segments.map(s=>s.token),['GMW','B','5000','D','1','ER']);
 assert.match(decodeModel('GMW-B9999').segments[1].description,/not been established/);assert.match(decodeModel('GW-B9999').segments[1].description,/owner-supplied community reading/);assert.equal(decodeModel('GMW-15-1V',data,refs).officialFeatures,null);
});
test('GPW alternatives remain community interpretations alongside official technology wording',()=>{
 for(const model of ['GPW-1000','GPW-2000']){const r=decodeModel(model,data,refs);assert.equal(r.family,'G-SHOCK / GRAVITYMASTER');assert.equal(r.officialFeatures.technologyName,'GPS Hybrid Wave Ceptor');assert.match(r.segments[0].description,/not an official acronym/)}
 const p=decodeModel('GPW-2000').segments[0].communityMeaning;assert.match(p.meaning,/positioning.*Pilot/);assert.equal(p.status,'community_interpretation');assert.deepEqual(decodeModel('GPW-2000-1A2').segments.map(s=>s.token),['GPW','2000','1','A2']);
});
test('DW community interpretation never assigns a universal depth or G-SHOCK identity',()=>{
 const r=decodeModel('DW-291H-1AV',data,refs);assert.match(r.segments[0].description,/Digital Water Resistant/);assert.match(r.segments[0].description,/non-G-SHOCK/);assert.match(r.segments[0].description,/prefix alone does not establish/);assert.equal(r.segments[0].status,'community_interpretation');assert.equal(r.segments[0].communityMeaning.status,'community_interpretation');assert.equal(r.officialFeatures,null);assert.deepEqual(decodeModel('GW-M5610U-1').segments.slice(0,4).map(s=>s.token),['GW','M','5610','U']);assert.match(decodeModel('GW-M5610U-1').segments[3].description,/Updated/);
});

test('official-feature source links have reviewed checksums without claiming letter definitions',()=>{
 const evidence=JSON.parse(fs.readFileSync(new URL('../research/decoder-rule-evidence-2026-11-15.json',import.meta.url)));
 for(const url of Object.values(ruleSources)){const row=evidence.observations.find(x=>x.url===url);assert.ok(row,url);assert.match(row.snapshot_sha256,/^[0-9a-f]{64}$/);assert.equal(row.letter_expansion_proved,false)}
 assert.equal(evidence.observations.find(x=>x.id==='gw-b5600bc').selected_observations.european_sku,'GW-B5600BC-1BER');
});

const {appearanceForModel,variantOrderInterpretation}=await import('../web/variant-interpretations.mjs');
test('checked -1B square variants explain blackout reading separately from observed LCD polarity',()=>{
 for(const id of ['GW-B5600BC-1B','GW-B5600BC-1BER','gwb5600bc1ber','GW-M5610-1B','GW-M5610-1BJF','GW-M5610U-1B','GW-M5610U-1BJF']){const r=decodeModel(id,data,refs),order=r.segments.find(s=>s.type==='order');assert.match(order.description,/Blackout.*Black Accent/);assert.equal(order.status,'community_interpretation');assert.equal(r.appearanceObservation.polarity,'negative');assert.equal(r.appearanceObservation.evidence_class,'official_observed');assert.match(r.appearanceObservation.observation_method,/not an explicit manufacturer suffix definition/)}
 const r=decodeModel('GW-B5600BC-1BER',data,refs);assert.match(r.segments[1].description,/Bluetooth smartphone linking/);assert.match(r.segments[5].description,/not the Bluetooth modifier/);
});
test('paired -1 variants preserve positive display observations and actual BC-1 accent colours',()=>{
 for(const id of ['GW-B5600BC-1','GW-B5600BC-1ER','GW-M5610-1','GW-M5610U-1']){const r=decodeModel(id,data,refs);assert.equal(r.appearanceObservation.polarity,'positive');assert.ok(!r.segments.some(s=>s.type==='order'&&s.token==='B'))}
 assert.match(appearanceForModel('GW-B5600BC-1').accents,/Yellow\/gold/);
});
test('-1B remains a recurring community pattern without invented polarity for unreviewed models',()=>{
 const unknown=decodeModel('GW-B9999-1B',data,refs);assert.equal(unknown.appearanceObservation,null);assert.match(unknown.segments.find(s=>s.type==='order').description,/recurring pattern is not universal/);assert.match(unknown.segments.find(s=>s.type==='order').description,/appearance remains unverified/);assert.equal(variantOrderInterpretation('2','B',null),null);
 const positive=decodeModel('F-91WM-1B',data,refs);assert.equal(positive.appearanceObservation.polarity,'positive');assert.match(positive.segments.find(s=>s.type==='order').description,/reading does not apply/);assert.equal(decodeModel('AE-1200WH-1BV',data,refs).appearanceObservation.polarity,'positive');assert.equal(appearanceForModel('F-91WM-1BJR'),null);
});
test('visual observation provenance is complete without publishing or embedding product photos',()=>{
 const note=JSON.parse(fs.readFileSync(new URL('../research/negative-variant-observations-2026-11-15.json',import.meta.url)));assert.equal(note.observations.length,8);
 for(const row of note.observations){assert.match(row.page_snapshot_sha256,/^[a-f0-9]{64}$/);assert.match(row.image_snapshot_sha256,/^[a-f0-9]{64}$/);assert.equal(row.image_published,false);assert.equal(appearanceForModel(row.model).polarity,row.polarity);assert.ok(row.source.startsWith('https://www.casio.com/'))}
 const code=fs.readFileSync(new URL('../web/variant-interpretations.mjs',import.meta.url),'utf8');assert.doesNotMatch(code,/https?:[^\s]+\.(?:png|jpg|jpeg)/i);assert.doesNotMatch(note.scope,/official universal definition/);
});

test('BC separates from the series for both reported examples and compact input',()=>{
 for(const input of ['GW-B5600BC-1BER','gwb5600bc1ber'])assert.deepEqual(decodeModel(input,data,refs).segments.map(s=>s.token),['GW','B','5600','BC','1','B','ER']);
 for(const input of ['GWF-D1000BC-1','gwfd1000bc1']){const r=decodeModel(input,data,refs);assert.deepEqual(r.segments.map(s=>s.token),['GWF','D','1000','BC','1']);const bc=r.segments.find(s=>s.token==='BC');assert.match(bc.description,/exact model.*unverified/);assert.equal(r.exact,undefined)}
});
test('original and updated 5610 BC suffixes retain separate U and avoid global U expansion',()=>{
 for(const input of ['GW-M5610BC-1','gwm5610bc1'])assert.deepEqual(decodeModel(input,data,refs).segments.map(s=>s.token),['GW','M','5610','BC','1']);
 for(const input of ['GW-M5610UBC-1','gwm5610ubc1']){const r=decodeModel(input,data,refs);assert.deepEqual(r.segments.map(s=>s.token),['GW','M','5610','U','BC','1']);assert.match(r.segments[3].description,/Updated/)}
 assert.deepEqual(decodeModel('GW-M9999U').segments.map(s=>s.token),['GW','M','9999U']);
});

test('multi-line guide adds qualified prefix associations and references without catalog inflation',()=>{
 for(const prefix of ['CMK','MDV','AEQ','WVQ','LIN','BGS','MTD','MRW'])assert.equal(decodeModel(prefix,data,refs).prefix,prefix);
 assert.equal(decodeModel('CMK',data,refs).family,'CASIO AUTOMATIC');assert.equal(decodeModel('CMK',data,refs).segments[0].status,'official_observed');assert.match(decodeModel('MDV',data,refs).segments[0].description,/do not infer 200 m/);
 const cmk=exactReferences(refs,'CMK-100TCC-8AER')[0];assert.ok(cmk);assert.equal(cmk.status,'machine_candidate');assert.ok(cmk.observations.some(o=>o.role==='supplied_guide_text'&&o.pdf_page===1));assert.equal(data.models[cmk.id],undefined);assert.equal(stats(data).models,526);
});

const {prefixMeaning}=await import('../web/prefix-meanings.mjs');
test('whole-prefix cards replace individual-letter cards and guide meanings appear in the family row',()=>{
 const r=decodeModel('AE1200',data,refs);assert.equal(r.segments[0].token,'AE');assert.equal(r.segments[0].communityMeaning.meaning,'Digital multi-function / world-time family');assert.equal(r.segments[0].communityMeaning.status,'community_interpretation');assert.match(r.segments[0].communityMeaning.locator,/PDF page 3/);assert.deepEqual(r.segments.map(s=>s.token),['AE','1200']);
 const app=fs.readFileSync(new URL('../web/app.mjs',import.meta.url),'utf8');assert.doesNotMatch(app,/prefixLetters|prefix-letters|letter-tile/);assert.match(app,/for\(const segment of result.segments\)chips.append/);assert.match(app,/The community understands this prefix as:/);
});
test('supplied guide family explanations remain scoped community readings rather than universal specs',()=>{
 for(const prefix of ['WV','WVA','WVQ','LCW','LIW','LIN','BG','BGA','BGD','BGS','BLX','MSG','F','A','W','LA','CA','DB','DBC','MQ','LQ','AE','AEQ','MDV','MTD','MRW','MTP','LTP','CMK']){const meaning=prefixMeaning(prefix);assert.ok(meaning,prefix);assert.equal(meaning.status,'community_interpretation');assert.match(meaning.note,/not an official universal/);assert.ok(meaning.source.endsWith('guide-v3-2026-11-15.json'))}
 assert.equal(prefixMeaning('NOTKNOWN'),null);assert.equal(decodeModel('GMW-15-1V',data,refs).segments[0].communityMeaning,null);assert.match(decodeModel('GW-M5610U-1').segments[3].description,/Updated/);assert.deepEqual(decodeModel('GW-B5600BC-1BER').segments.map(s=>s.token),['GW','B','5600','BC','1','B','ER']);
});


test('guide examples separate configuration, colour and export segments',()=>{
 for(const [input,tokens] of [
 ['LCW-M100TSE-1AJF',['LCW','M','100','T','SE','1','A','JF']],
 ['MDV-106B-2AV',['MDV','106','B','2','A','V']],
 ['MTP-E735AR-2A2V',['MTP','E','735','AR','2','A2','V']],
 ['CMK-100TCC-8AER',['CMK','100','T','C','C','8','A','ER']]]){
 const r=decodeModel(input);assert.deepEqual(r.segments.map(s=>s.token),tokens);assert.ok(r.guideNotes.length);assert.ok(r.guideNotes.every(n=>n.page>=1&&n.page<=5));
 }
 const c=decodeModel('CMK-100TCC-8AER').segments.filter(s=>s.token==='C');assert.match(c[0].description,/Cloth/);assert.match(c[1].description,/ion-plated/);
 assert.match(decodeModel('MTP-E735AR-2A2V').guideNotes.map(n=>n.text).join(' '),/Ice blue/);
});
test('guide regions and material meanings remain contextual',()=>{
 for(const suffix of ['JF','J','CR','ER','V','VER','DR','DF'])assert.equal(decodeModel('MDV-106B-2A'+suffix).segments.at(-1).token,suffix);
 assert.match(decodeModel('GWF-D1000BC').segments.find(s=>s.type==='modifier').description,/depth/);
 assert.equal(decodeModel('AE-1200WH').segments[0].token,'AE');
 assert.ok(!decodeModel('GW-M5610U').segments.some(s=>s.description.includes('titanium')));
});
test('branding and disclaimer match the requested sample',()=>{
 const html=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');assert.ok(!html.includes('CASIO REPAIR'));assert.ok(html.includes('Unofficial project · Not affiliated with or endorsed by Casio Computer Co., Ltd.'));assert.ok(html.includes('REPAIR · MODS · COLLECTING'));
});


test('M in GW-M5600 and GW-M5610 means Multi-Band within those square lines',()=>{
 for(const input of ['GW-M5600','GW-M5600-1','GW-M5610','GW-M5610-1','GW-M5610U','GW-M5610U-1','gwm5610u','gwm5610u1','GW-M5610UBC-1']){
  const r=decodeModel(input),m=r.segments.find(s=>s.type==='modifier'&&s.token==='M');assert.match(m.description,/Multi-Band 6/);assert.match(m.description,/Japan ×2/);assert.match(m.description,/community interpretation/);assert.equal(m.status,'community_interpretation');assert.equal(m.title,'Multi-Band reception');
  if(input.toUpperCase().includes('U'))assert.ok(r.segments.some(s=>s.token==='U'&&s.title==='Updated model'));
 }
 assert.match(decodeModel('GW-M9999').segments.find(s=>s.token==='M').description,/owner-supplied community reading/);
 assert.match(decodeModel('GMW-B5000').segments[0].communityMeaning.meaning,/Metal/);
 assert.match(decodeModel('GW-B5600').segments.find(s=>s.token==='B').description,/Bluetooth/);
});

test('supplied text interpretations are all browsable without a model lookup',async()=>{
 const {guideReferenceSections,guideModifiers,guideColours,guideMarkets}=await import('../web/guide-interpretations.mjs');
 const sections=guideReferenceSections(),text=sections.flatMap(s=>s.items).join('\n');
 for(const family of ['WV','WVA','WVQ','LCW','LIW','LIN','BG','BGA','BGD','BGS','BLX','MSG','F','A','W','LA','CA','DB','DBC','MQ','LQ','AE','AEQ','MTP','LTP'])assert.ok(text.includes(family+': '),family);
 for(const term of ['LCW-M100TSE-1AJF','MDV-106B-2AV','MTP-E735AR-2A2V','CMK-100TCC-8AER','CR2025','SR920SW','21,600','120-click','6 o’clock','V00x','S1xx'])assert.ok(text.includes(term),term);
 for(const [token,meaning] of Object.entries(guideModifiers))assert.ok(text.includes(token+': '+meaning));
 for(const [token,meaning] of Object.entries(guideColours))assert.ok(text.includes(token+': '+meaning));
 for(const [token,meaning] of Object.entries(guideMarkets))assert.ok(text.includes(token+': '+meaning));
 const html=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');assert.ok(html.includes('id="guide-reference"'));assert.ok(html.includes('There might be errors within the prefixes.'));assert.ok(html.includes('https://www.instagram.com/master_tinkerer_sommelier?'));assert.ok(html.includes('contact me on Instagram'));
});
test('GWN keeps a whole family prefix with separately sourced marine context',()=>{
 for(const input of ['GWN','GWN1000','GWN-1000']){const r=decodeModel(input),prefix=r.segments[0];assert.equal(prefix.token,'GWN');assert.match(prefix.description,/marine-oriented/);assert.match(prefix.description,/neither supplied guide defines/);assert.equal(prefix.status,'official_observed');assert.ok(prefix.source.startsWith('https://gshock.casio.com/'));}
});


test('all 66 supplied G-SHOCK readings resolve as grouped families or separate modifiers',async()=>{
 const {ownerReadings}=await import('../web/owner-prefix-readings.mjs');assert.equal(ownerReadings.length,66);
 for(const reading of ownerReadings){const [base,modifier]=reading.code.split('-');for(const input of [reading.code,reading.code+'1000',reading.code.replace('-','')+'1000']){const r=decodeModel(input);assert.ok(r.recognized,input);assert.equal(r.prefix,base,input);assert.equal(r.segments[0].token,base);assert.ok(r.segments[0].communityMeaning,input);if(modifier){const s=r.segments.find(s=>s.type==='modifier'&&s.token===modifier);assert.ok(s,input);assert.equal(s.status,'community_interpretation',input);}}}
 const {guideReferenceSections}=await import('../web/guide-interpretations.mjs');const table=guideReferenceSections().find(s=>s.title.includes('Owner-supplied G-SHOCK'));assert.equal(table.items.length,66);
 assert.match(decodeModel('GWN1000').segments[0].communityMeaning.meaning,/Nautical/);
 assert.match(decodeModel('GA-B001').segments.find(s=>s.token==='B').description,/model-dependent/);assert.equal(decodeModel('GA-B001').officialFeatures,null);
 assert.match(decodeModel('MRG').segments[0].communityMeaning.meaning,/unverified/);
 assert.equal(decodeModel('GM-40',data,refs).segments[0].communityMeaning,null);
});


test('Gold Tornado commemorative code and module specifications stay correctly scoped',()=>{
 for(const [input,tokens] of [['GWFD1035',['GWF','D10','35']],['GWFD1035B1JR',['GWF','D10','35','B','1','JR']],['GWF-D1035B-1',['GWF','D10','35','B','1']]]){const r=decodeModel(input,data,refs);assert.deepEqual(r.segments.map(s=>s.token),tokens);assert.match(r.segments.find(s=>s.token==='35').description,/35th/);}
 assert.equal(decodeModel('GWF-D1035B-1',data,refs).exact.id,'GWF-D1035B-1');assert.equal(value(data.models['GWF-D1035B-1'],'module_id'),'3445');assert.equal(value(data.models['GWF-D1035B-1'],'weight_g'),141);
 assert.equal(value(data.modules['3445'],'dive_log').records,20);assert.equal(value(data.modules['3445'],'depth_meter').step_m,0.1);assert.equal(evidenceLabel(data.modules['3445'].specs.depth_meter),'Official Casio source');assert.equal(evidenceLabel(data.modules['3445'].specs.battery_cell),'Owner-supplied evidence');
 assert.ok(!decodeModel('GW-1235').segments.some(s=>s.type==='anniversary'));assert.ok(!decodeModel('GWF-1035F-1',data,refs).segments.some(s=>s.token==='D10'));assert.ok(!decodeModel('GWF-D9999').segments.some(s=>s.type==='anniversary'));
 assert.match(decodeModel('GMW-B5000SS-2',data,refs).segments.find(s=>s.token==='SS').description,/Sky and Sea/);assert.ok(!decodeModel('GMW-B9999SS-2').editionNotes.length);
});
test('anniversary directory exposes every supplied entry without importing all as verified watches',async()=>{
 const {anniversaryDirectory}=await import('../web/anniversary.mjs');assert.equal(anniversaryDirectory.length,124);assert.equal(new Set(anniversaryDirectory.map(r=>r.id)).size,120);
 for(const item of anniversaryDirectory){assert.ok(refs.models[item.id],item.id);const r=decodeModel(item.id,data,refs);assert.ok(r.editionNotes?.length,item.id);}
 assert.equal(stats(data).models,526);
});

test('historical catalog rows display exact facts without modern prefix or colour inference',()=>{
 for(const id of ['GM-40','DW-1000','AE-60W','GF-1','56CS-528-2','PQ-5','AE2ZNAV']){const r=decodeModel(id,data,refs);assert.equal(r.exact.id,id);assert.equal(r.family,'HISTORICAL CASIO');assert.equal(r.historicalReference,true);assert.equal(modelColor(r),null);assert.ok(!r.segments[0].communityMeaning);}
 assert.equal(value(data.models['56CS-528-2'],'module_id'),'56');assert.equal(value(data.models['GM-40'],'catalog_year'),1982);assert.equal(value(data.models['W150C-1'],'module_id'),null);assert.ok(findModels(data,{query:'Pyramid'}).some(m=>m.id==='GM-40'));
 assert.match(decodeModel('GMW-B5000',data,refs).segments[0].communityMeaning.meaning,/Metal/);
});
test('uncertain historical readings remain separate from imported model identities',async()=>{
 const {historicalReview}=await import('../web/historical-review.mjs');assert.equal(historicalReview.length,56);assert.equal(historicalReview.filter(r=>r.catalog_year===1989).length,41);assert.ok(historicalReview.some(r=>r.reading==='MQ.S0W.18'));assert.ok(!data.models['MQ.S0W.18']);assert.equal(stats(data).models,526);
});

test('consolidated source aliases, family scope and explicit discrepancies remain accessible',()=>{
 const awg=decodeModel('AWG-M520UA',data,refs);assert.equal(awg.exact.id,'AWG-M520UA-1EJR');assert.equal(findModels(data,{query:'GWR-B3000-1AJF'}).length,1);assert.equal(decodeModel('GWR-B3000-1AJF',data,refs).exact.id,'GWR-B3000-1A');assert.ok(!data.models['GWR-B3000-1AJF']);
 assert.equal(evidenceLabel(data.models['AWG-M520UA-1EJR'].specs.reported_measurements),'Conflicting evidence');assert.equal(evidenceLabel(data.modules['5770'].specs.battery_cell),'Conflicting evidence');
 assert.deepEqual(moduleIds(data.models['DW-290G-9V']),['1219','1189']);assert.equal(value(data.models['DW-H5600-1'],'dimensions_mm'),null);assert.ok(findModels(data,{query:'POLAR'}).some(m=>m.id==='DW-H5600-1'));
});
test('complete compilation tables and reference-only identifiers are available without adding variants',async()=>{
 const {combinedReference}=await import('../web/combined-reference.mjs');assert.equal(combinedReference.tables.length,29);assert.equal(combinedReference.reported_references.length,9);assert.equal(combinedReference.tables.find(t=>t.kind==='chart').rows.length,6);assert.ok(refs.models['OCW-T5000'].observations.some(o=>o.reading_scope==='family_label_only_not_exact_variant'));assert.ok(!data.models['OCW-T5000']);
 const html=fs.readFileSync(new URL('../web/index.html',import.meta.url),'utf8');assert.ok(html.includes('id="combined-reference-tables"'));assert.ok(html.includes('id="combined-cautions"'));assert.equal(stats(data).models,526);
});
