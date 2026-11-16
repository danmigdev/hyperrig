'use strict';
// Offline only: all ports, UI events and device replies are fake. The actual
// pinned editor save/scene/reload functions run against those fake dependencies.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const guardSource=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8');
const blob=fs.readFileSync(process.argv[4]);
let checks=0,retainedSuccess=null;
const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
const throws=f=>{assert.throws(f);checks++;};
const rejects=async f=>{await assert.rejects(f);checks++;};
const enc=new TextEncoder();
const originalFunctions=html.slice(html.indexOf('async function loadPreset(n)'),html.indexOf('/*PRESET-IO-BEGIN*/'));
assert(originalFunctions.includes('async function savePreset(n, existing)'));
const originalGains=html.slice(html.indexOf('function buildGains()'),html.indexOf('/* ============================================================ CRC32'));
const crc32=bytes=>{let c=0xffffffff;for(const b of bytes){c^=b;for(let k=0;k<8;k++)c=c&1?(c>>>1)^0xedb88320:c>>>1;}return(c^0xffffffff)>>>0;};
function setup({live=true,pong='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11',captureSlot=-1,closeFail=false}={}){
  let tick=0,reader,override=null,outputChange;
  const pending=[],calls={writes:[],opens:0,closes:0,requests:0};
  const hw={gain:[0,0],capture:captureSlot,preset:-1,scene:-1,rows:[],safe:0,mode:2};
  const handlers={};
  const attrs={'aria-valuenow':'0','aria-valuemin':'-30','aria-valuemax':'12','aria-label':'Output'};
  const knob={dataset:{k:'Output'},getAttribute:k=>attrs[k],getBoundingClientRect:()=>({width:60,height:60})};
  const nameEl={getBoundingClientRect:()=>({width:80,height:25})};
  const saveEl={contains:el=>el===saveEl,getBoundingClientRect:()=>({width:30,height:30})};
  const row={querySelector:s=>s==='[data-a="s"]'?saveEl:s==='.n'?nameEl:s==='.n.vacio'?(hw.rows.length?null:nameEl):null};
  const side={classList:{remove(){}}};
  const port={getInfo:()=>({usbVendorId:0x3654,usbProductId:0x5155}),
    open:async()=>{calls.opens++;},close:async()=>{calls.closes++;if(closeFail)throw Error('close');},
    readable:{getReader:()=>({read:async()=>({value:pending.shift(),done:false})})}};
  const profile={target:'tank-mini',image_sha256:'a'.repeat(64),hardware_verified:false,
    capabilities:{read:true,write:false,panel:false},family_capabilities:{},command_capabilities:{}};
  const ctx={navigator:{serial:{requestPort:async()=>{calls.requests++;return port;}}},DOMException,TextEncoder,Date,
    performance:{now:()=>++tick},localStorage:{setItem(){}},DEMO:false,PH:false,tab:'rig',curPreset:-1,plist:[],plistHave:true,
    S:{gain:[0,0],curPre:-1,capSlot:captureSlot,pendName:'',snap:-1,snaps:[0,0,0,0],chain:{P:[],Q:[]}},
    ED:{seq:0,ep:0,p:new Set(),on:false,aeq:false,gainN:0},
    document:{activeElement:knob,querySelector:s=>s==='.side'?side:s.startsWith('#pList ')?row:s.startsWith('#gOut')?knob:null,
      querySelectorAll:()=>[],addEventListener:(k,f)=>handlers[k]=f},
    HyperRigMini:{profile,commandPolicy:l=>({allowed:/^(PING|GAIN|LVL|FXS|PLIST|SNAPS|CLIST|ILIST|MODEL|CLKSTATE|AMPEQ|BPM|PCOLOR|STW|SNAPNAME|MEM)$/.test(l),capability:'read'}),
      preflight:()=>({allowed:false}),observeReply(){},inspectPong(){},acceptPong(){},resetIdentity(){}},
    parsePlist:ls=>{const end=/^PLIST end current=(-?\d+)$/.exec(ls.at(-1)||'');
      return{ok:!!end,cur:end?+end[1]:null,list:ls.filter(x=>x.startsWith('PRE ')).map(x=>{const m=/^PRE (\d+) \d+ -?\d+ -?\d+ '([^']+)'/.exec(x);return[+m[1],m[2]];})};},
    pioLib:ls=>{const end=/CLIST end current=(-?\d+)/.exec(ls.at(-1)||'');return{full:!!end,cur:end?+end[1]:-1,
      list:ls.filter(x=>x.startsWith('CAP ')).map(x=>{const m=/CAP (\d+) (\d+) '([^']+)'/.exec(x);return{slot:+m[1],bytes:+m[2],name:m[3]};})};},
    SLOT:n=>'ABCD'[n%4],presetName:()=>'',Log:{act(){},ev(){}},toast(){},reply:(ls,p)=>ls.find(x=>x.startsWith(p))||'',
    aeqSettle:async()=>{},edFresh:async()=>{},edMoved:()=>false,edClearUpTo(){ctx.ED.on=false;},edMark(){ctx.ED.on=true;},
    evSince:async()=>null,evMoves:()=>false,evPoll(){},stMonoNote(){},renderPresets(){},renderSaveBar(){},
    stwLoad:async()=>{},loadAmpEq:async()=>{},loadMem:async()=>{},setTab(){},uiConfirm:async()=>{throw Error('unexpected confirm');},
    $:()=>({innerHTML:''}),knob:(parent,options)=>{if(options.label==='Output')outputChange=options.onChange;return{};}};
  const response=line=>{
    if(line==='PING')return[pong];
    if(line.startsWith('CSAVE ')){hw.capture=+line.split(' ')[1];return[`CSAVE ok ${hw.capture} 'A2' 4892 B`];}
    if(/^CREAD \d+$/.test(line))return[`CREAD ${hw.capture} len=4892 crc=2144df1c id=77ac505b aux=0 fs=0 name='A2'`];
    if(/^CREAD \d+ \d+$/.test(line)){const off=+line.split(' ')[2],part=blob.subarray(off,off+96);
      return[`CREAD ${hw.capture} ${off} ${part.length} ${crc32(part).toString(16).padStart(8,'0')} ${part.toString('base64')}`];}
    if(line.startsWith('GAIN '))hw.gain=line.split(' ').slice(1).map(Number);
    if(/^GAIN(?: |$)/.test(line))return[`GAIN in=${hw.gain[0]} out=${hw.gain[1]} dB`];
    if(line.startsWith('PSAVE ')){hw.preset=+line.split(' ')[1];hw.rows=[`PRE ${hw.preset} 0 ${hw.capture} -1 'Preset 1A' t=- s=0 amp=1`];
      return[`PSAVE ok ${hw.preset} 'Preset 1A' 0 blocks capture=${hw.capture} ir=-1`];}
    if(line==='SNAPSAVE 0'){hw.scene=0;hw.rows[0]=hw.rows[0].replace('s=0','s=1');return[`SNAPSAVE ok 0 preset=${hw.preset}`];}
    if(line.startsWith('PLOAD ')){hw.gain=[0,0];hw.scene=0;return[`PLOAD ok ${hw.preset} 'Preset 1A' missing=0 capture=${hw.capture} ir=-1 ms=1`];}
    if(line==='LVL')return[`LVL in=-1440 out=-1440 ci=0 co=0 m=${hw.mode} g=${hw.gain.join('/')} p=${hw.preset}`];
    if(line==='FXS')return['FXS amp=1 on=1','FXS eng=1 posts=100 takes=100 canc=0 lat=1/1 run=0','FXS peak=10 ticks skipped=0'];
    if(line==='PLIST')return[...hw.rows,`PLIST end current=${hw.preset}`];
    if(line==='SNAPS')return[hw.scene===0?'SNAPS 1000 current=0':'SNAPS 0000 current=-1'];
    if(line==='CLIST')return[...(hw.capture>=0?[`CAP ${hw.capture} 4892 'A2' trim=0.0`]:[]),`CLIST end current=${hw.capture} slots=15`];
    if(line==='ILIST')return['ILIST end current=-1 slots=15'];
    if(line==='MODEL')return["MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0"];
    if(line==='CLKSTATE')return[`CLKSTATE mhz=360 safe=${hw.safe}`];
    if(line==='AMPEQ')return['AMPEQ volume=0 bass=0 mid=0 treble=0 presence=0 drive=0'];
    if(line==='BPM')return['BPM 120.0'];
    if(line==='PCOLOR')return[`PCOLOR none preset=${hw.preset}`];
    if(line==='STW')return['STW w=0 cur=0 live=0 cpu=0/1 deg=0'];
    if(line==='SNAPNAME')return['SNAPNAME end'];
    return[line+' ok'];
  };
  const transport={write:async text=>{calls.writes.push(text);}};
  const pedal={onLine(){},cmd:async line=>{
    const gate=ctx.HyperRigMini.commandPolicy(line,'usb-cdc');
    if(!gate.allowed)return['ERR MINI_APP blocked'];
    await transport.write(line+'\n');
    const lines=override?override(line,response):response(line);
    pending.push(enc.encode(lines.join('\r\n')+'\r\n'));await reader.read();
    for(const l of lines)pedal.onLine(l);
    return lines;
  }};
  ctx.Pedal=pedal;ctx.SerialTransport=transport;pedal.tr=transport;
  ctx.readPlist=async()=>ctx.parsePlist(await pedal.cmd('PLIST'));
  ctx.loadPresets=async()=>{const r=await ctx.readPlist();ctx.plist=r.list;ctx.curPreset=r.cur;};
  ctx.loadSnaps=async()=>{const ls=await pedal.cmd('SNAPS'),m=/SNAPS ([01]{4}) current=(-?\d+)/.exec(ls[0]);ctx.S.snaps=[...m[1]].map(Number);ctx.S.snap=+m[2];};
  ctx.loadModelName=async()=>{const ls=await pedal.cmd('CLIST');ctx.S.capSlot=ctx.pioLib(ls).cur;};
  ctx.loadChain=async()=>{await pedal.cmd('FXS');};
  vm.createContext(ctx);vm.runInContext(guardSource,ctx);vm.runInContext(originalFunctions,ctx);vm.runInContext(originalGains,ctx);
  const guard=ctx.installMiniBrowserFirstPresetGuard({live,image_sha256:'a'.repeat(64),pong});
  guard.installApp(transport,pedal,profile);ctx.buildGains();
  const open=async()=>{guard.allowRequest();const p=await ctx.navigator.serial.requestPort();await p.open({baudRate:115200});reader=p.readable.getReader();await pedal.cmd('PING');};
  const fresh=async()=>{const r={};for(const name of ['GAIN','LVL','FXS','PLIST','SNAPS','CLIST','ILIST','MODEL','CLKSTATE','AMPEQ','BPM','PCOLOR','STW','SNAPNAME'])r[name]=await pedal.cmd(name);return r;};
  const capturePlan={slot:captureSlot<0?0:captureSlot,requests:[]};
  if(captureSlot<0)capturePlan.requests.push('CSAVE 0 A2');
  capturePlan.requests.push('CREAD '+capturePlan.slot,...Array.from({length:51},(_,n)=>`CREAD ${capturePlan.slot} ${n*96}`));
  const persist=async()=>{await fresh();guard.configureCapture(capturePlan);for(const cmd of capturePlan.requests)await pedal.cmd(cmd);guard.captureDone();await ctx.loadModelName();};
  const plan={slot:0,name:'Preset 1A',gain:[0,0],down:[0,-1],capture_slot:capturePlan.slot,ir_slot:-1,blocks:0,
    save_request:'PSAVE 0 Preset 1A',load_request:'PLOAD 0'};
  const prepare=async()=>{await open();await persist();const r=await fresh();guard.configureTrial(plan,r);};
  const key=(action,changes={})=>{const reload=action==='reload',k=reload?'Enter':action==='up'?'ArrowUp':'ArrowDown';
    return handlers.keydown({key:k,code:k,target:reload?nameEl:knob,isTrusted:true,repeat:false,
      altKey:false,ctrlKey:false,metaKey:false,shiftKey:false,preventDefault(){},stopImmediatePropagation(){},...changes});};
  const step=async action=>{ctx.document.activeElement=knob;guard.arm(action);key(action);
    const value=action==='up'?0:-1;attrs['aria-valuenow']=String(value);outputChange(value);
    for(let n=0;n<20&&guard.state.phase==='ui_in_flight';n++)await Promise.resolve();
    await Promise.resolve();};
  const save=async changes=>{guard.arm('save');handlers.click({target:saveEl,isTrusted:true,preventDefault(){},stopImmediatePropagation(){},...changes});
    await ctx.savePreset(0,undefined);await Promise.resolve();};
  const reload=async()=>{ctx.document.activeElement=nameEl;guard.arm('reload');key('reload');await ctx.loadPreset(0);attrs['aria-valuenow']='0';};
  return{ctx,guard,port,calls,hw,transport,pedal,open,fresh,persist,prepare,plan,capturePlan,key,step,save,reload,knob,nameEl,attrs,
    override:fn=>override=fn,normal:response};
}
async function main(){
  {
    const x=setup();await x.prepare();check(x.ctx.HyperRigMini.profile.hardware_verified,false);
    check(x.ctx.HyperRigMini.profile.capabilities.write,false);check(x.guard.state.captureMutations,1);
    await x.step('down1');check(x.guard.state.phase,'down1_ack');await x.fresh();
    await x.step('up');check(x.guard.state.phase,'up_ack');await x.fresh();
    await x.save();check(x.guard.state.phase,'scene_ack');await x.fresh();
    await x.step('marker');check(x.guard.state.phase,'marker_ack');await x.fresh();
    await x.reload();check(x.guard.state.phase,'reload_ack');await x.fresh();x.guard.finish();x.guard.stop();await x.port.close();
    check(x.calls.writes.filter(s=>/^(GAIN |PSAVE |SNAPSAVE |PLOAD )/.test(s)),
      ['GAIN 0 -1\n','GAIN 0 0\n','PSAVE 0 Preset 1A\n','SNAPSAVE 0\n','GAIN 0 -1\n','PLOAD 0\n']);
    check(x.guard.state.mutations,6);check(x.guard.state.ui.length,5);check(x.guard.state.phase,'complete');
    check(x.hw.gain,[0,0]);check(x.hw.scene,0);check(x.guard.state.closes,1);
    check(x.guard.state.rx[0].hex,Buffer.from('PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11\r\n').toString('hex'));
    check(x.calls.writes.filter(s=>s.startsWith('CREAD ')).length,52);
    retainedSuccess=JSON.parse(JSON.stringify(x.guard.state));
  }
  {const x=setup({captureSlot:4});await x.prepare();check(x.guard.state.captureMutations,0);check(x.calls.writes.some(s=>s.startsWith('CSAVE ')),false);}
  {const x=setup({live:false});await rejects(()=>x.open());check(x.calls.opens,0);}
  {const x=setup({pong:'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe'});await x.open();await rejects(()=>x.pedal.cmd('GAIN'));check(x.calls.writes.length,1);}
  for(const [key,value]of[['safe',1],['mode',0]]){const x=setup();await x.open();x.hw[key]=value;await x.fresh();throws(()=>x.guard.configureCapture(x.capturePlan));check(x.guard.state.captureMutations,0);}
  {const x=setup();await x.open();await x.fresh();const bad=JSON.parse(JSON.stringify(x.capturePlan));bad.requests[2]='CREAD 0 96';throws(()=>x.guard.configureCapture(bad));}
  {const x=setup();await x.open();await x.fresh();x.guard.configureCapture(x.capturePlan);throws(()=>x.guard.captureDone());}
  {const x=setup();await x.prepare();await rejects(()=>x.pedal.cmd('GAIN 0 -1'));check(x.guard.state.mutations,0);}
  for(const changes of[{isTrusted:false},{repeat:true},{key:'ArrowUp'},{target:{}},{ctrlKey:true}]){
    const x=setup();await x.prepare();x.guard.arm('down1');throws(()=>x.key('down1',changes));check(x.guard.state.mutations,0);
  }
  {const x=setup();await x.prepare();throws(()=>x.guard.arm('up'));check(x.guard.state.mutations,0);}
  {const x=setup();await x.prepare();await x.step('down1');throws(()=>x.guard.arm('up'));}
  {const x=setup();await x.prepare();await x.step('down1');await x.fresh();await rejects(()=>x.pedal.cmd('GAIN 0 -1'));check(x.guard.state.mutations,1);}
  {const x=setup();await x.prepare();await x.step('down1');await x.fresh();await x.step('up');await x.fresh();
    await rejects(()=>x.save({isTrusted:false}));check(x.calls.writes.some(s=>s.startsWith('PSAVE ')),false);}
  {const x=setup();await x.prepare();await x.step('down1');await x.fresh();await x.step('up');await x.fresh();
    x.override((line,normal)=>line.startsWith('PSAVE ')?["PSAVE ok 0 'Preset 1A' 0 blocks capture=-1 ir=-1"]:normal(line));
    await rejects(()=>x.save());check(x.calls.writes.some(s=>s.startsWith('SNAPSAVE ')),false);}
  {const x=setup();await x.prepare();await x.step('down1');await x.fresh();await x.step('up');await x.fresh();await x.save();await x.fresh();
    await x.step('marker');await x.fresh();x.override((line,normal)=>line.startsWith('PLOAD ')?["PLOAD ok 0 'Preset 1A' missing=1 capture=0 ir=-1 ms=1"]:normal(line));
    await rejects(()=>x.reload());check(x.guard.state.mutations,6);}
  for(const cmd of['CSAVE 1 Other','PDEL 0','PSAVE 1 Other','SNAP 0','PNEW','UBOOT','GAIN 1 0']){
    const x=setup();await x.prepare();await rejects(()=>x.pedal.cmd(cmd));check(x.guard.state.mutations,0);
  }
  {const x=setup({closeFail:true});await x.open();await rejects(()=>x.port.close());check(x.guard.state.closes,0);check(x.guard.state.stopped,true);}
  console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false,
    actual_editor_functions_tested:['buildGains','savePreset','sceneAOnSave','loadPreset'],fake_serial_only:true,
    ...(process.argv.includes('--emit-success')?{guard:retainedSuccess}:{})}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
