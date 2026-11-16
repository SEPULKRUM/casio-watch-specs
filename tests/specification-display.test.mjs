import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {englishText,nonEnglishScript} from '../web/english.mjs';
import {presentationFacts,waterResistanceFact} from '../web/specification-display.mjs';
import {display,label,findModels} from '../web/core.mjs';
import {modelColor} from '../web/decoder-presentation.mjs';
const catalog=JSON.parse(fs.readFileSync(new URL('../data/catalog.json',import.meta.url)));
const source={url:'https://www.casio.com/jp/',locator:'Specifications / 防水性',evidence:'20気圧防水'};
const fact=(value,status='pending_review',sources=[source])=>({value,status,sources,uncertainty:'Not independently reviewed'});
test('screenshot rating and bar are one English row with deduplicated evidence',()=>{
 const record={specs:{water_resistance_rating:fact('20気圧防水'),water_resistance_bar:fact(20),color:fact('ブラック')}};
 const before=JSON.stringify(record),rows=presentationFacts(record);
 assert.equal(rows.filter(([field])=>field.startsWith('water_resistance')).length,1);
 assert.equal(rows[0][0],'water_resistance');assert.equal(rows[0][1].value,'20 bar');
 assert.equal(rows[0][1].sources.length,1);assert.equal(rows[0][1].components.length,2);
 assert.equal(label('color'),'Color');assert.equal(display(rows[1][1].value,'color'),'Black');
 assert.equal(JSON.stringify(record),before);
});
test('every catalog model has at most one water-resistance display row',()=>{
 for(const record of Object.values(catalog.models)){
  const raw=Object.entries(record.specs).filter(([k])=>['water_resistance_rating','water_resistance_m','water_resistance_bar'].includes(k));
  const shown=presentationFacts(record).filter(([k])=>k==='water_resistance');
  assert.equal(shown.length,raw.length?1:0,record.id);
  if(raw.length)assert.equal(shown[0][1].components.length,raw.length);
 }
});
test('equivalent sourced units consolidate, while conflicting claims remain explicit',()=>{
 const normal=waterResistanceFact([['water_resistance_rating',fact('200M Water Resistant')],['water_resistance_m',fact(200)],['water_resistance_bar',fact(20)]]);
 assert.equal(normal.value,'200 m (20 bar)');assert.equal(normal.status,'pending_review');
 const conflict=waterResistanceFact([['water_resistance_m',fact(200)],['water_resistance_bar',fact(10)]]);
 assert.match(conflict.value,/200 m/);assert.match(conflict.value,/10 bar/);assert.match(conflict.value,/conflicting/);assert.equal(conflict.status,'conflicting');
});
test('diving certification, unspecified ratings and supplied qualifications survive',()=>{
 assert.match(waterResistanceFact([['water_resistance_rating',fact('ISO 200 m diving water resistance')]]).value,/ISO 200 m diving/);
 assert.equal(waterResistanceFact([['water_resistance_rating',fact('Water Resistant')]]).value,'Water Resistant');
 const daily=waterResistanceFact([['water_resistance_rating',fact('日常生活用防水')]]);assert.match(daily.value,/rating not specified/);assert.doesNotMatch(daily.value,/\d/);
 assert.match(waterResistanceFact([['water_resistance_rating',fact('100 m (supplied nominal family rating)')]]).value,/supplied nominal family rating/);
});
test('verified-only filtering cannot leak a pending rating or source',()=>{
 const pendingSource={...source,evidence:'Pending ISO claim'};
 const rows=presentationFacts({specs:{water_resistance_rating:fact('ISO 200 m diving','pending_review',[pendingSource]),water_resistance_bar:fact(20,'verified')}},{verified:true});
 assert.equal(rows[0][1].value,'20 bar');assert.equal(rows[0][1].status,'verified');assert.equal(rows[0][1].components.length,1);
 assert.ok(!rows[0][1].sources.includes(pendingSource));
});
test('equal material values for different components are not discarded',()=>{
 const rows=presentationFacts({specs:{case_material:fact('Resin'),band_material:fact('Resin')}});
 assert.deepEqual(rows.map(([field])=>field),['case_material','band_material']);
});
test('all current Japanese values, evidence and locators have complete English display translations',()=>{
 let translated=0;
 function walk(value){if(Array.isArray(value))value.forEach(walk);else if(value&&typeof value==='object')Object.values(value).forEach(walk);else if(typeof value==='string'&&nonEnglishScript.test(value)){const rendered=englishText(value);assert.ok(!nonEnglishScript.test(rendered));assert.doesNotMatch(rendered,/translation pending/,value);translated++}}
 walk(catalog);assert.ok(translated>500);
 assert.match(englishText('メタルバンド（チタンバンド／但し、中留二つ折れ部ステンレススチール）'),/Titanium.*stainless-steel folding clasp/);
 assert.match(englishText('両面反射防止コーティングサファイアガラス（デュアルカーブ）'),/both surfaces.*Dual-curved/);
 assert.equal(englishText('Colour / colourway / coloured / colours'),'Color / colorway / colored / colors');
});
test('English colors are searchable and drive matching swatches',()=>{
 const model={id:'GW-EXAMPLE-1',specs:{color:fact('ブラック')}};
 const data={schema_version:1,models:{[model.id]:model},modules:{}};
 assert.equal(findModels(data,{query:'black'}).length,1);
 const result=modelColor({segments:[{type:'variant',token:'1'}],exact:model});assert.equal(result.actual,'Black');assert.equal(result.swatch,'#111111');
});
