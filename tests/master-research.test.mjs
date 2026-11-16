import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateMaster,expandMasterModel,mergeMasterReferences,searchMaster,masterCategory} from '../web/master-research.mjs';
import {validateReferences,exactReferences} from '../web/model-references.mjs';
import {decodeModel} from '../web/decoder.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url)));
const note=validateMaster(read('../research/casio-master-research-2026-11-16.json'));
const base=read('../data/model-references.json');
const merged=validateReferences(mergeMasterReferences(base,note));
test('master extends research references without promoting authentication',()=>{
 assert.equal(merged.counts.model_strings,31906);
 assert.equal(Object.keys(base.models).length,4334);
 const row=exactReferences(merged,'a201a').find(r=>r.id==='A-20-1A');
 assert.equal(row.status,'machine_candidate');assert.equal(row.evidence_status,'unverified');assert.equal(row.observations.at(-1).csv_row,2);
 assert.deepEqual(mergeMasterReferences(merged,note),merged);
 assert.equal(merged.counts.index_checked,base.counts.index_checked);
});
test('pagination covers every raw identifier and retains combined strings intact',()=>{
 const ids=[];for(let offset=0;offset<29286;offset+=40)ids.push(...searchMaster(note,'','all',offset).rows.map(r=>r.row.model_id));
 assert.deepEqual(ids,note.models.map(r=>r.model_id));
 assert.equal(searchMaster(note,'','fitment').total,1212);
 assert.equal(searchMaster(note,'','unresolved').total,114);
 assert.equal(searchMaster(note,'','individual').total,27960);
 assert.equal(merged.models['A-151/153/155-1A'],undefined);
});
test('case-source and module filters retain source semantics',()=>{
 assert.equal(searchMaster(note,'','enriched').total,57);
 assert.equal(searchMaster(note,'','module').total,116);
 assert.ok(searchMaster(note,'DW-290-1V','module').rows.some(r=>r.row.model_id==='DW-290-1V'));
 const row=searchMaster(note,'GWF-D1000BC-1').rows.find(r=>r.row.model_id==='GWF-D1000BC-1');
 assert.equal(expandMasterModel(note,row.row).weight_g,'181');
});
test('only the supplied GAC family is added; raw labels do not create letter meanings',()=>{
 const r=decodeModel('GAC-2500-1A',null,merged);assert.equal(r.prefix,'GAC');assert.match(r.segments[0].description,/pending independent review/);
 assert.equal(masterCategory(note,{model_id:'<script>1</script>'}),'unresolved');
 assert.throws(()=>validateMaster({...note,models:[...note.models,note.models[0]]}));
 const unknown=expandMasterModel(note,note.models[0]);assert.equal(unknown.weight_g,'');assert.equal(unknown.case_height_mm,'');
});
