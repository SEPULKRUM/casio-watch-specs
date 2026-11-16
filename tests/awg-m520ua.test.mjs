import test from 'node:test';
import assert from 'node:assert/strict';
import {decodeModel} from '../web/decoder.mjs';

test('United Arrows code stays together in full and compact model inputs',()=>{
 for(const input of ['AWG-M520UA-1EJR','awgm520ua1ejr']){
  const result=decodeModel(input);
  assert.equal(result.normalized,'AWG-M520UA-1EJR');
  assert.deepEqual(result.segments.map(s=>s.token),['AWG','M','520','UA','1','E','JR']);
  assert.match(result.segments.find(s=>s.token==='UA').description,/United Arrows/i);
  assert.equal(result.segments.find(s=>s.token==='E').status,'unverified');
  assert.match(result.segments.find(s=>s.token==='JR').description,/unverified/i);
  assert.equal(result.officialFeatures,undefined);
 }
});
test('base model exposes primary evidence, secondary report and owner video without invented suffixes',()=>{
 const result=decodeModel('AWG-M520UA');
 assert.deepEqual(result.segments.map(s=>s.token),['AWG','M','520','UA']);
 assert.equal(result.editionNotes.length,3);
 assert.ok(result.editionNotes.some(s=>s.source.includes('store.united-arrows.co.jp')));
 assert.ok(result.editionNotes.some(s=>s.source.includes('g-central.com')));
 const video=result.editionNotes.find(s=>s.source==='https://www.youtube.com/watch?v=qJTOpZHMlnw');
 assert.equal(video.linkLabel,'Watch my video ↗');
 assert.match(video.status,/Owner-supplied/);
});
test('collaboration interpretation does not change ordinary AWG models or unrelated suffixes',()=>{
 for(const model of ['AWG-M520-1A','AWG-M520BB-1A','GW-M5610U-1'])assert.ok(!decodeModel(model).editionNotes?.some(s=>s.source.includes('qJTOpZHMlnw')));
 assert.ok(!decodeModel('AWG-M520UA-9JF').editionNotes?.some(s=>s.source.includes('qJTOpZHMlnw')));
});
