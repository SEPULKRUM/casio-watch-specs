import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeModel} from '../web/decoder.mjs';
test('Gold Tornado GPW edition displays exact archived facts and a scoped TFB suffix',()=>{
 const result=decodeModel('GPW-2000TFB-1A');
 assert.deepEqual(result.segments.map(s=>s.token),['GPW','2000','TFB','1','A']);
 const suffix=result.segments.find(s=>s.token==='TFB');assert.match(suffix.description,/Gold Tornado/);assert.match(suffix.source,/20171210224041/);
 assert.match(result.officialFeatures.description,/5502/);
 const note=result.editionNotes.find(s=>s.title.includes('archived specifications'));
 for(const value of ['66.0','57.1','18.2','120','200 m'])assert.ok(note.description.includes(value));
 assert.ok(result.editionNotes.some(s=>s.source.includes('20171208233205')));
});
test('exact-edition measurements are not copied onto another GPW colorway',()=>{
 const result=decodeModel('GPW-2000-1A');assert.ok(!result.editionNotes?.some(s=>s.title.includes('archived specifications')));
});
