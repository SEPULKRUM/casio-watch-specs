import test from 'node:test';
import assert from 'node:assert/strict';
import {watchnaviReference as reference} from '../web/watchnavi-reference.mjs';
import {searchWatchnavi} from '../web/watchnavi-search.mjs';
test('pagination exposes every original placement exactly once',()=>{
 const ids=[];
 for(let offset=0;offset<reference.placements.length;offset+=40)ids.push(...searchWatchnavi(reference,'',offset).rows.map(r=>r.placement_id));
 assert.deepEqual(ids,reference.placements.map(r=>r.placement_id));
});
test('compact lookup retains source reading and OCR flags',()=>{
 const result=searchWatchnavi(reference,'dw5000c1a');
 assert.ok(result.rows.some(r=>r.model_string==='DW-5000C-1A'&&r.ocr_review_flag));
 assert.ok(searchWatchnavi(reference,'1983').rows.some(r=>r.year_heading===1983));
});
test('search does not silently repair letter O into digit zero',()=>{
 const sample={placements:[{model_string:'DW-OOlJ-9',caption_lines:[],feature_phrases:[],year_heading:1983}]};
 assert.equal(searchWatchnavi(sample,'DW-001J-9').total,0);
 assert.equal(searchWatchnavi(sample,'DW-OOlJ-9').total,1);
});
