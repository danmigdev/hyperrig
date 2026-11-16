'use strict';
// Original setLock/phInert and both real UI extensions on a minimal offline DOM.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const html=fs.readFileSync(process.argv[2],'utf8').replace(/\r\n/g,'\n');
const oldUI=fs.readFileSync(process.argv[3],'utf8'),newUI=fs.readFileSync(process.argv[4],'utf8');
const setLock=html.slice(html.indexOf('function setLock()'),html.indexOf('var lockWas = null'));
const phInert=html.slice(html.indexOf('function phInert()'),html.indexOf('if (typeof MutationObserver !== "undefined") for (const id of PANELS)'));
assert(setLock.includes('$("fuB").innerHTML'));assert(phInert.includes('$("app").inert'));
let checks=0;const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
function fixture(){
 const nodes=new Map();
 class N{
  constructor(id='',tag='DIV',text=''){this.id=id;this.tagName=tag;this.dataset={};this.style={};this.title='';
   this.children=[];this._html=text;this.inert=false;this.isConnected=true;this.disabled=false;
   const classes=new Set();this.classList={contains:k=>classes.has(k),toggle:(k,on)=>on?classes.add(k):classes.delete(k)};
   if(id)nodes.set(id,this);}
  get innerHTML(){return this._html;}
  set innerHTML(value){for(const child of this.children)remove(child);this.children=[];this._html=value;}
  replaceChildren(...children){for(const child of this.children)if(!children.includes(child))remove(child);this.children=children;}
  querySelector(selector){if(selector.startsWith('#'))return nodes.get(selector.slice(1))||null;return null;}
  querySelectorAll(){return [];}
  setAttribute(){}removeAttribute(){}getAttribute(){return null;}
  contains(node){return this.children.includes(node)||this.children.some(x=>x.contains(node));}
  after(){}focus(){doc.activeElement=this;}blur(){}
 }
 const remove=node=>{if(node.id)nodes.delete(node.id);node.children.forEach(remove);};
 for(const id of ['lockTxt','lockSub','lockConn','lockAlt','firstUse','guideLink','lockv','app','stage','tuner','settings',
  'fsBtn','gsave','spill','snapGlide','hpf','spur','limOn','limThr','limRel','geq','gIn','gOut'])new N(id);
 const browserStep=new N('fuB','LI','Use Chrome or Edge.'),connectStep=new N('fuC','LI','Plug it in and click Connect.');
 const middle=new N('', 'LI','Install firmware');middle.children=[nodes.get('guideLink')];
 const intro=new N();intro.children=[browserStep,middle,connectStep];
 const body=new N('body'),top=new N(),lockbox=new N();
 const doc={body,activeElement:new N('neutral'),title:'',getElementById:id=>nodes.get(id)||null,
  querySelector:q=>q==='#firstUse ol'?intro:q==='.top'?top:q==='.lockbox'?lockbox:null,
  querySelectorAll:()=>[],createElement:tag=>new N('',tag.toUpperCase())};
 const transport={available:()=>true};
 const ctx={document:doc,$:doc.getElementById,S:{connected:false,firstUse:false},DEMO:false,PH:false,APP:false,
  Pedal:{tr:transport},BleTransport:{},otherTransport:()=>null,ctlReleased:false,Tabs:{busy:false},
  T:x=>x,fwHintShow(){},guideLink:()=>null,stRender(){},lockWas:null,fuTxt:null,setTimeout(){},
  isShown:()=>false,location:{hash:''},HyperRigMini:{profile:{target:'tank-mini',firmware_version:'test',
   capabilities:{read:true,panel:false},command_capabilities:{},family_capabilities:{}},
   fullWriteEnabled:()=>false,scopedWriteEnabled:()=>false,familyWriteEnabled:()=>false}};
 vm.createContext(ctx);vm.runInContext(phInert+'\n'+setLock,ctx);
 return {ctx,nodes,intro,browserStep,connectStep};
}
const old=fixture();vm.runInContext('setLock()',old.ctx);
check(old.nodes.get('gOut').inert,true);check(Array.from(old.ctx.fuTxt),['Use Chrome or Edge.','Plug it in and click Connect.']);
vm.runInContext(oldUI,old.ctx);check(old.nodes.has('fuB'),false);check(old.nodes.has('fuC'),false);
old.ctx.S.connected=true;assert.throws(()=>vm.runInContext('setLock()',old.ctx),/innerHTML/);checks++;
check(old.nodes.get('gOut').inert,true);check(old.ctx.document.body.classList.contains('locked'),false);
const fixed=fixture();vm.runInContext('setLock()',fixed.ctx);const cache=Array.from(fixed.ctx.fuTxt);
vm.runInContext(newUI,fixed.ctx);
check(fixed.nodes.get('fuB')===fixed.browserStep,true);check(fixed.nodes.get('fuC')===fixed.connectStep,true);
check(Array.from(fixed.ctx.fuTxt),cache);check(fixed.intro.children.length,3);
fixed.ctx.S.connected=true;vm.runInContext('setLock()',fixed.ctx);
check(fixed.nodes.get('gOut').inert,false);check(fixed.nodes.get('gIn').inert,false);
check(fixed.nodes.get('app').inert,false);check(Array.from(fixed.ctx.fuTxt),cache);
fixed.ctx.S.connected=false;vm.runInContext('setLock()',fixed.ctx);
check(fixed.nodes.get('gOut').inert,true);check(fixed.nodes.get('gIn').inert,true);
console.log(JSON.stringify({result:'pass',checks,original_functions:['setLock','phInert'],
 original_UI_failure_reproduced:true,original_nodes_preserved:true,device_io:false,browser_started:false}));
