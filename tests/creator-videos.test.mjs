import test from 'node:test';
import assert from 'node:assert/strict';
import {creatorVideosForModel,creatorVideos} from '../web/creator-videos.mjs';
import {decodeModel} from '../web/decoder.mjs';

test('owner video is linked independently to each of the three supplied AWG variants',()=>{
 for(const model of ['AWG-500J-1A','AWG-M510-1B','AWG-500J-9A']){
  const result=creatorVideosForModel(model);
  assert.equal(result.length,1);
  assert.equal(result[0].url,'https://www.youtube.com/watch?v=jGWa9HTgiIw');
 }
 assert.equal(creatorVideosForModel('awg500j1a').length,1);
});
test('collaboration mappings do not leak to other colors or ordinary base models',()=>{
 for(const model of ['AWG-M520UA','AWG-M520UA-1EJR'])assert.equal(creatorVideosForModel(model)[0].url,'https://www.youtube.com/watch?v=qJTOpZHMlnw');
 for(const model of ['AWG-500J-1B','AWG-M510-1A','AWG-M520-1A','AWG-500J','AWG-M520UA-9JF'])assert.deepEqual(creatorVideosForModel(model),[]);
 for(const row of creatorVideos){assert.equal(new URL(row.url).hostname,'www.youtube.com');assert.ok(row.models.length||row.modules?.length);assert.match(row.attribution,/owner/)}
});
test('JR reading stays a community interpretation and keeps the suffix intact',()=>{
 for(const model of ['AWG-M520UA-1EJR','GW-M5610U-1JR']){
  const market=decodeModel(model).segments.find(s=>s.type==='market');
  assert.equal(market.token,'JR');assert.equal(market.status,'community_interpretation');
  assert.match(market.description,/Japan Release/);assert.match(market.description,/not an official Casio/);
 }
});

test('GPW owner playlist is public and scoped to the exact variant',()=>{
 const [link]=creatorVideosForModel('GPW-2000TFB-1A');
 assert.equal(link.url,'https://www.youtube.com/playlist?list=PLDqbRJ4qDRs0');
 assert.equal(link.kind,'playlist');
 assert.deepEqual(creatorVideosForModel('GPW-2000-1A'),[]);
});

test('module playlists apply to recorded associations without guessing families',()=>{
 const url='https://www.youtube.com/playlist?list=PLK00sRoqNZrA';
 for(const modules of [['3159'],['3495'],[3159],['3159','3495'],['3159','9999']])assert.equal(creatorVideosForModel('EXACT-VARIANT',modules).filter(v=>v.url===url).length,1);
 for(const modules of [[],['315'],['34950'],['9999']])assert.equal(creatorVideosForModel('GW-M5610U-1',modules).filter(v=>v.url===url).length,0);
 assert.equal(creatorVideosForModel('GPW-2000TFB-1A',['5502'])[0].kind,'playlist');
});

test('LINEAGE owner video is scoped to its exact Japanese-market model',()=>{
 assert.equal(creatorVideosForModel('LCW-M200DJ-2AJF')[0].url,'https://www.youtube.com/watch?v=JE01UC2Usdg');
 for(const id of ['LCW-M200DJ-1AJF','LCW-M200DJ','LCW-M200'])assert.deepEqual(creatorVideosForModel(id),[]);
});
