// Minimal DOM contract for executing the real detail renderer in Node. This is
// a regression unit harness, not a browser/layout test or a renderer reimplementation.
import fs from 'node:fs/promises';import vm from 'node:vm';
export class TestElement{
 constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.listeners={};this.open=false;this._text='';}
 set textContent(text){this._text=String(text);this.children=[];}
 get textContent(){return this._text+this.children.map(c=>typeof c==='string'?c:c.textContent).join('');}
 append(...nodes){for(const node of nodes){if(node&&typeof node==='object'){if(node.parent){const i=node.parent.children.indexOf(node);if(i>=0)node.parent.children.splice(i,1)}node.parent=this;}this.children.push(node)}}
 replaceChildren(...nodes){for(const child of this.children)if(child&&typeof child==='object')child.parent=null;this.children=[];this._text='';this.append(...nodes)}
 setAttribute(name,value){this.attributes[name]=String(value);if(name==='id')this.id=value;}
 addEventListener(name,fn){(this.listeners[name]??=[]).push(fn)}
 click(){for(const fn of this.listeners.click||[])fn({target:this,preventDefault(){}})}
 matches(selector){return selector.startsWith('#')?this.id===selector.slice(1):selector.startsWith('.')?String(this.className||'').split(' ').includes(selector.slice(1)):this.tagName===selector.toUpperCase()}
 querySelector(selector){for(const c of this.children){if(typeof c!=='object'||!c)continue;if(c.matches(selector))return c;const found=c.querySelector(selector);if(found)return found}return null}
 querySelectorAll(selector){const found=[];for(const c of this.children){if(typeof c!=='object'||!c)continue;if(c.matches(selector))found.push(c);found.push(...c.querySelectorAll(selector))}return found}
 showModal(){this.open=true;}close(){this.open=false;}focus(){}scrollIntoView(){}
}
export async function createDetailHarness(catalog,index,{appUrl=new URL('../../web/app.mjs',import.meta.url)}={}){
 const raw=await fs.readFile(appUrl,'utf8'),bindings={};
 for(const m of raw.matchAll(/^import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"];?$/gm)){
  const module=await import(new URL(m[2],appUrl));for(const name of m[1].split(',').map(s=>s.trim()))bindings[name]=module[name];
 }
 const roots=new Map();for(const id of ['detail-body','detail','reference-matches','prefix-result','result-count','list-heading','search-mode','results','empty','empty-message','page-number','page-count','page-prev','page-next','page-first','page-last']){const node=new TestElement(id==='detail'?'dialog':'div');node.id=id;roots.set('#'+id,node)}
 roots.get('#search-mode').selectedOptions=[{textContent:'All models'}];
 const document={createElement:tag=>new TestElement(tag),querySelector(selector){if(roots.has(selector))return roots.get(selector);for(const root of roots.values()){const found=root.querySelector(selector);if(found)return found}return null},querySelectorAll(){return []}};
 const ctx=vm.createContext({...bindings,document,URL,URLSearchParams,structuredClone,console,location:{href:'https://example.test/prefixes/',pathname:'/prefixes/',search:'',hash:''},history:{replaceState(){}},navigator:{clipboard:{writeText:async()=>{}}}});
 const body=raw.replace(/^import .*\n/gm,'').split("$('#master-query').addEventListener")[0];
 vm.runInContext(body+'\nglobalThis.detailTest={openModel,render,setInputs(c,i){data=c;searchIndex=i;parts=null;productLinks=null;masterResearch=null;},setMaster(m){masterResearch=m},setQuery(q){state.query=q;}};',ctx,{filename:appUrl.pathname});
 ctx.detailTest.setInputs(catalog,index);
 return {render:ctx.detailTest.render,query:ctx.detailTest.setQuery,roots,open:ctx.detailTest.openModel,body:roots.get('#detail-body'),dialog:roots.get('#detail'),api:ctx.detailTest,context:ctx};
}
