import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateSearchIndex,searchUnified,indexedModel,exactIndexedModels,modelForDetail,indexedStatus,inSearchMode,unifiedFamilyCounts,fitmentContext} from '../web/unified-search.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url)));
const catalog=read('../data/catalog.json'),index=validateSearchIndex(read('../data/search-index.json'),catalog),master=read('../research/casio-master-research-2026-11-16.json'),report=read('../data/reconciliation-report.json');

test('all eligible master identifiers and required examples resolve in unified search',()=>{
 for(const source of master.models)assert.ok(indexedModel(index,source.model_id),source.model_id);
 for(const id of ['GW-9400KJ-8','GW-9503KJ-2','GWF-D1035B-1','DW-8140TC-4','OCW-G1200-2AJF','GAC-2500-9A']){
  const result=searchUnified(index,catalog,{query:id},master);assert.ok(result.records.some(r=>r.id===id),id);assert.equal(result.records[0].id,id);
 }
});
test('default mode includes pending watch models and every page is accessible exactly once',()=>{
 const visited=[];let page=1,pages;
 do{const result=searchUnified(index,catalog,{page});assert.ok(result.records.length<=50);visited.push(...result.records.map(r=>r.id));pages=result.pageCount;page++}while(page<=pages);
 const expected=index.records.filter(r=>inSearchMode(r)).map(r=>r.id);
 assert.equal(visited.length,expected.length);assert.equal(new Set(visited).size,expected.length);assert.deepEqual(new Set(visited),new Set(expected));
 assert.ok(searchUnified(index,catalog,{query:'A-20-1A'}).records.some(r=>r.id==='A-20-1A'));
 assert.equal(searchUnified(index,catalog,{query:'A-20-1A',verified:true}).total,0);
});
test('region, color and edition identifiers are never merged by compact searching',()=>{
 const ids=['GW-M5610U-1','GW-M5610U-1JF','GW-M5610U-1ER','GW-M5610U-1B'];
 for(const id of ids)assert.equal(indexedModel(index,id).id,id);
 const found=searchUnified(index,catalog,{query:'gwm5610u1',pageSize:100});
 for(const id of ids)assert.ok(found.records.some(r=>r.id===id),id);
 assert.notEqual(modelForDetail(index,catalog,ids[0]).model.id,modelForDetail(index,catalog,ids[1]).model.id);
});
test('reference-only details are empty and never copy another variant case via module',()=>{
 const result=modelForDetail(index,catalog,'A-20-1A');assert.deepEqual(result.model.specs,{});assert.equal(result.model.id,'A-20-1A');assert.match(indexedStatus(result.entry),/Specifications pending verification/);
 const a=modelForDetail(index,catalog,'GW-9400KJ-8'),b=modelForDetail(index,catalog,'GW-9400-1');
 assert.deepEqual(a.module_ids,b.module_ids);assert.equal(a.model.specs.dimensions_mm,undefined);assert.ok(b.model.specs.dimensions_mm);
 assert.equal(modelForDetail(index,catalog,'DW-OOlJ-9').entry.category,'uncertain');
});
test('non-watch categories stay accessible without inflating watch totals',()=>{
 for(const category of ['watch','family','clock','fitment','uncertain','package'])assert.equal(searchUnified(index,catalog,{mode:category}).total,index.counts[category]);
 assert.equal(searchUnified(index,catalog,{mode:'all'}).total,index.counts.all_records);
 assert.equal(searchUnified(index,catalog,{mode:'specifications'}).total,report.models_with_specifications);
 assert.equal(searchUnified(index,catalog,{mode:'reference-only'}).total,report.reference_only_models);
 assert.ok(!searchUnified(index,catalog,{query:'A-151/153/155-1A'}).records.some(r=>r.id==='A-151/153/155-1A'));
 assert.ok(searchUnified(index,catalog,{query:'A-151/153/155-1A',mode:'fitment'}).records.some(r=>r.id==='A-151/153/155-1A'));
});
test('pagination clamps after filtering and family counts agree with mode totals',()=>{
 const result=searchUnified(index,catalog,{query:'GW-9503KJ-2',page:999});assert.equal(result.page,1);assert.equal(result.pageCount,1);
 assert.equal(searchUnified(index,catalog,{page:-4}).page,1);assert.equal(searchUnified(index,catalog,{pageSize:100}).records.length,100);
 assert.equal(Object.values(unifiedFamilyCounts(index)).reduce((a,b)=>a+b,0),searchUnified(index,catalog).total);
 assert.equal(searchUnified(index,catalog,{verified:true}).total,4);
});
test('truncated indexes or broken category counts fail validation rather than hiding models',()=>{
 const bad=structuredClone(index);bad.records.pop();assert.throws(()=>validateSearchIndex(bad,catalog));
 const badCount=structuredClone(index);badCount.counts.watch++;assert.throws(()=>validateSearchIndex(badCount,catalog));
 const missingCatalog=structuredClone(index);const i=missingCatalog.records.findIndex(r=>r.id==='GW-9400KJ-8');missingCatalog.records.splice(i,1);missingCatalog.counts.all_records--;missingCatalog.counts.watch--;assert.throws(()=>validateSearchIndex(missingCatalog,catalog));
});
test('explicit combined reference finds its three individual watches without copying shared specifications',()=>{
 const combined='A-151/153/155-1A',members=['A-151-1A','A-153-1A','A-155-1A'];
 const result=searchUnified(index,catalog,{query:combined});assert.deepEqual(new Set(result.records.map(r=>r.id)),new Set(members));
 assert.equal(indexedModel(index,combined).category,'fitment');
 for(const id of members){
  assert.equal(searchUnified(index,catalog,{query:id}).records[0].id,id);
  assert.equal(indexedModel(index,id).category,'watch');
  assert.deepEqual(modelForDetail(index,catalog,id).model.specs,{});
  assert.deepEqual(modelForDetail(index,catalog,id).module_ids,[]);
  assert.equal(fitmentContext(index,id)[0].model_id,combined);
 }
 assert.equal(searchUnified(index,catalog,{query:combined,verified:true}).total,0);
 assert.equal(searchUnified(index,catalog,{query:combined,mode:'fitment'}).records[0].id,combined);
 assert.equal(searchUnified(index,catalog,{query:combined,mode:'all'}).total,4);
 // Other slash labels are not split by a naming heuristic.
 assert.deepEqual(fitmentContext(index,'A-151/153G-1A'),[]);
 const bad=structuredClone(index);bad.fitment_resolutions[0].related_models.push('UNPROVEN-999');assert.throws(()=>validateSearchIndex(bad,catalog));
});
