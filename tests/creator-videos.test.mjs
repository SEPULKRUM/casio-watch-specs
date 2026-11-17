import fs from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {creatorVideosForModel,creatorVideos,isProTrekModel} from '../web/creator-videos.mjs';
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
 for(const row of creatorVideos){assert.equal(new URL(row.url).hostname,'www.youtube.com');assert.ok(row.models.length||row.modules?.length||row.families?.length||row.groups?.length);assert.match(row.attribution,/owner/)}
});
test('JR reading stays a community interpretation and keeps the suffix intact',()=>{
 for(const model of ['AWG-M520UA-1EJR','GW-M5610U-1JR']){
  const market=decodeModel(model).segments.find(s=>s.type==='market');
  assert.equal(market.token,'JR');assert.equal(market.status,'community_interpretation');
  assert.match(market.description,/Japan Release/);assert.match(market.description,/not an official Casio/);
 }
});

test('GPW owner playlist remains public when expanded to the Gravitymaster family',()=>{
 const [link]=creatorVideosForModel('GPW-2000TFB-1A');
 assert.equal(link.url,'https://www.youtube.com/playlist?list=PLDqbRJ4qDRs0');
 assert.equal(link.kind,'playlist');
 assert.equal(creatorVideosForModel('GPW-2000-1A')[0].url,'https://www.youtube.com/playlist?list=PLDqbRJ4qDRs0');
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

test('every indexed Pro Trek reference has the requested family playlist exactly once',()=>{
 const index=JSON.parse(fs.readFileSync(new URL('../data/search-index.json',import.meta.url)));
 const rows=index.records.filter(r=>/pro.?trek/i.test(r.family));assert.ok(rows.length>=591);
 for(const row of rows){const videos=creatorVideosForModel(row.id,row.module_ids,row.family);assert.equal(videos.filter(v=>v.url==='https://www.youtube.com/playlist?list=PLaV8co9Dpnac').length,1,row.id)}
});
test('family playlist covers known prefixes, legacy Pathfinder and identified Pro Trek Smart without module inference',()=>{
 const url='https://www.youtube.com/playlist?list=PLaV8co9Dpnac';
 for(const id of ['PRW-3000-1','prw30001','PRW-S3100-1JF','prws31001jf','PRG-240','PRT-B50','prtb50','PRX-8000','PRJ-70','PAW2000','PAG-240','WSD-F20-BK','WSDF30BK'])assert.ok(creatorVideosForModel(id).some(v=>v.url===url),id);
 assert.equal(isProTrekModel('NEW-REFERENCE','Pro Trek'),true);assert.equal(isProTrekModel('NEW-REFERENCE','PRO TREK / PATHFINDER'),true);
 for(const id of ['GW-M5610U-1','LCW-M200DJ-2AJF','SPF-40','WSD-F10','PRWX3000'])assert.ok(!creatorVideosForModel(id,['3159'],'Sea-Pathfinder').some(v=>v.url===url),id);
 assert.equal(isProTrekModel('OTHER-1','Not Pro Trek'),false);
});
