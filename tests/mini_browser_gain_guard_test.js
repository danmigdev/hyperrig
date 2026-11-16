'use strict';
// All ports, bytes, UI events and responses here are fake. No browser/device.
const fs = require('fs'), vm = require('vm'), assert = require('assert').strict;
const source = fs.readFileSync(process.argv[2], 'utf8');
let checks = 0;
const check = (actual, expected) => { assert.deepEqual(actual, expected); checks++; };
const rejects = async fn => { await assert.rejects(fn); checks++; };
const throws = fn => { assert.throws(fn); checks++; };
function setup({live=true,pid=0x5155,gain=[0,0],closeFail=false}={}) {
  const calls = {requests:[],opens:[],writes:[],closes:0};
  const queue = [];
  const port = {getInfo:()=>({usbVendorId:0x3654,usbProductId:pid}),
    open:async opts=>calls.opens.push(opts),
    close:async()=>{calls.closes++;if(closeFail)throw new Error('native close fail');},
    readable:{getReader:()=>({read:async()=>({value:queue.shift(),done:false})})}};
  const attrs = {'aria-valuenow':String(gain[1]),'aria-valuemin':'-30','aria-valuemax':'12','aria-label':'Uscita'};
  const knob = {dataset:{k:'Output'},getAttribute:key=>attrs[key],getBoundingClientRect:()=>({width:60,height:60})};
  let handler;
  const ctx = {navigator:{serial:{requestPort:async opts=>{calls.requests.push(opts);return port;}}},
    performance:{now:()=>123},DOMException,TextEncoder,localStorage:{setItem(){}},
    document:{activeElement:knob,querySelector:()=>knob,addEventListener:(name,fn)=>{if(name==='keydown')handler=fn;}},
    S:{gain:[...gain]},parsePlist:lines=>({ok:lines.at(-1)==='PLIST end current=0'}),
    HyperRigMini:{commandPolicy:line=>/^LVLSUB |^BLEKEY$/.test(line)?{allowed:false}:{allowed:true,capability:'family'}}};
  vm.createContext(ctx); vm.runInContext(source,ctx);
  const guard=ctx.installMiniBrowserGainGuard({live,image_sha256:'a'.repeat(64),pong:'PONG exact',gain});
  const transport={write:async text=>calls.writes.push(text)};
  let hw=[...gain], reader=null, override=null;
  const replies = line => {
    if (/^GAIN /.test(line)) hw=line.split(' ').slice(1).map(Number);
    if (/^GAIN(?: |$)/.test(line)) return [`GAIN in=${hw[0]} out=${hw[1]} dB`];
    if (line==='LVL') return [`LVL in=-700 out=-800 g=${hw[0]}/${hw[1]} amp=0`];
    if (line==='FXS') return ['FXS amp=0 on=0','FXS peak=1 ticks skipped=0'];
    if (line==='PLIST') return ['PLIST end current=0'];
    if (line==='SNAPS') return ['SNAPS 1000 current=0'];
    if (line==='PING') return ['PONG exact'];
    return [line+' ok'];
  };
  const pedal={onLine(){},cmd:async line=>{
    if (/^LVLSUB |^BLEKEY$/.test(line)) return ['ERR MINI_APP unqualified'];
    await transport.write(line+'\n');
    const lines=override?override(line):replies(line);
    if(reader){queue.push(new TextEncoder().encode(lines.join('\r\n')+'\r\n'));await reader.read();}
    for(const l of lines)pedal.onLine(l);
    return lines;
  }};
  guard.installApp(transport,pedal,{target:'tank-mini',image_sha256:'a'.repeat(64),hardware_verified:true,
    capabilities:{read:true,write:false},family_capabilities:{'usb-cdc':['GAIN']}});
  const open=async()=>{guard.allowRequest();const p=await ctx.navigator.serial.requestPort();await p.open({baudRate:115200});reader=p.readable.getReader();await pedal.cmd('PING');};
  const fresh=async()=>{for(const line of ['GAIN','LVL','FXS','PLIST','SNAPS'])await pedal.cmd(line);};
  const key=(direction,changes={})=>handler({key:direction==='down'?'ArrowDown':'ArrowUp',code:direction==='down'?'ArrowDown':'ArrowUp',
    target:knob,isTrusted:true,repeat:false,altKey:false,ctrlKey:false,metaKey:false,shiftKey:false,
    preventDefault(){},stopImmediatePropagation(){},...changes});
  const step=async direction=>{guard.arm(direction);key(direction);ctx.S.gain[1]+=direction==='down'?-1:1;
    attrs['aria-valuenow']=String(ctx.S.gain[1]);await pedal.cmd('GAIN '+ctx.S.gain.join(' '));};
  return {ctx,calls,port,guard,transport,pedal,open,fresh,key,step,attrs,knob,
    override:fn=>{override=fn;},normal:replies,setHW:values=>{hw=[...values];}};
}
async function main(){
  for(const gain of [[0,-30],[0,13],[true,0],[0.5,0],[0],null]) throws(()=>setup({gain}));
  {
    const x=setup({live:false});await rejects(()=>x.ctx.navigator.serial.requestPort());check(x.calls.requests.length,0);
    check(Array.from(await x.ctx.navigator.serial.getPorts()),[]);
  }
  {const x=setup();await rejects(()=>x.ctx.navigator.serial.requestPort());check(x.calls.requests.length,0);}
  {const x=setup({pid:0x4155});await rejects(()=>x.open());check(x.calls.opens.length,0);}
  {
    const x=setup();await x.open();check(x.calls.requests[0].filters[0].usbVendorId,0x3654);
    check(x.calls.requests[0].filters[0].usbProductId,0x5155);check(x.calls.opens.length,1);
    await rejects(()=>x.port.open({baudRate:115200}));check(x.calls.opens.length,1);
    await rejects(()=>x.ctx.navigator.serial.requestPort());check(x.calls.requests.length,1);
  }
  {const x=setup();await rejects(()=>x.transport.write('GAIN 0 -1\n'));check(x.calls.writes.length,0);}
  for(const text of ['GAIN 0 -1\n','GAIN 0 0\n','PSAVE 0 HyperRig_Test\n','PDEL 0\n','SNAPSAVE 0\n','FXP 1 0 1\n',
    'GAIN 0 -1\nGAIN 0 0\n',' GAIN 0 -1\n','GAIN 0 -1 \n','GAIN 0 -1\r\n','RESET\n']){
    const x=setup();await x.open();const n=x.calls.writes.length;
    await rejects(()=>x.transport.write(text));check(x.calls.writes.length,n);
  }
  {const x=setup();await x.open();throws(()=>x.guard.arm('down'));check(x.guard.state.mutations,0);}
  {const x=setup();await x.open();await x.fresh();throws(()=>x.guard.arm('up'));check(x.guard.state.mutations,0);}
  for(const changes of [{isTrusted:false},{repeat:true},{altKey:true},{ctrlKey:true},{metaKey:true},{shiftKey:true},
                        {key:'ArrowUp'},{code:'ArrowUp'},{target:{}}]){
    const x=setup();await x.open();await x.fresh();x.guard.arm('down');
    throws(()=>x.key('down',changes));check(x.guard.state.mutations,0);
  }
  for(const bad of ['aria','state','focus','identity']){
    const x=setup();await x.open();await x.fresh();
    if(bad==='aria')x.attrs['aria-valuenow']='1';if(bad==='state')x.ctx.S.gain=[1,0];
    if(bad==='focus')x.ctx.document.activeElement={};if(bad==='identity')x.knob.dataset.k='Input';
    throws(()=>x.guard.arm('down'));check(x.guard.state.mutations,0);
  }
  {
    const x=setup();await x.open();await x.fresh();x.guard.arm('down');
    await rejects(()=>x.transport.write('GAIN 0 -1\n'));check(x.guard.state.mutations,0);
  }
  {
    const x=setup();await x.open();await x.fresh();await x.step('down');check(x.guard.state.phase,'down_ack');
    throws(()=>x.guard.arm('up'));check(x.guard.state.mutations,1);
  }
  {
    const x=setup();await x.open();await x.fresh();await x.step('down');await x.fresh();
    const n=x.calls.writes.length;await rejects(()=>x.transport.write('GAIN 0 -1\n'));check(x.calls.writes.length,n);
  }
  for(const answer of [['GAIN in=0 out=0 dB'],['ERR GAIN'],[],['GAIN in=0 out=-1 dB','extra']]){
    const x=setup();await x.open();await x.fresh();x.override(line=>line.startsWith('GAIN ')?answer:x.normal(line));
    await rejects(()=>x.step('down'));check(x.guard.state.mutations,1);check(x.guard.state.stopped,true);
  }
  {
    const x=setup();await x.open();await x.fresh();await x.step('down');x.setHW([0,0]);await x.fresh();
    throws(()=>x.guard.arm('up'));check(x.guard.state.mutations,1);
  }
  {
    const x=setup();await x.open();await x.fresh();await x.step('down');await x.fresh();await x.step('up');
    throws(()=>x.guard.finish());check(x.guard.state.mutations,2);
  }
  {
    const x=setup();await x.open();await x.fresh();await x.step('down');await x.fresh();await x.step('up');await x.fresh();
    x.guard.finish();check(x.guard.state.phase,'complete');check(x.guard.state.mutations,2);
    check(x.calls.writes.filter(v=>v.startsWith('GAIN ')),['GAIN 0 -1\n','GAIN 0 0\n']);
    check(x.guard.state.ui.map(e=>e.key).join(','),'ArrowDown,ArrowUp');check(x.guard.state.ui.every(e=>e.trusted),true);
    check(x.guard.state.rx.length>0,true);check(x.guard.state.rx[0].hex,Buffer.from('PONG exact\r\n').toString('hex'));
    check(x.guard.state.wire.find(e=>e.origin==='Output ArrowDown').hex,Buffer.from('GAIN 0 -1\n').toString('hex'));
    await x.port.close();check(x.guard.state.closes,1);check(x.guard.state.closeError,null);
    const n=x.calls.writes.length;await rejects(()=>x.transport.write('GAIN 0 0\n'));check(x.calls.writes.length,n);
  }
  {
    const x=setup({closeFail:true});await x.open();await rejects(()=>x.port.close());
    check(x.guard.state.closes,0);check(x.guard.state.stopped,true);
  }
  {
    const x=setup();await x.open();await x.pedal.cmd('LVLSUB 100 2');await x.pedal.cmd('BLEKEY');
    check(x.calls.writes,['PING\n']);check(x.guard.state.stopped,false);
    check(x.guard.state.events.filter(e=>e.kind==='local_editor_policy_rejection').length,2);
  }
  {
    const x=setup();await x.open();x.pedal.onLine('PONG different');await rejects(()=>x.transport.write('PING\n'));
    check(x.calls.writes,['PING\n']);
  }
  {
    const x=setup();await x.open();x.override(()=>['PLIST truncated']);await rejects(()=>x.pedal.cmd('PLIST'));
    const n=x.calls.writes.length;await rejects(()=>x.pedal.cmd('PLIST'));check(x.calls.writes.length,n);
  }
  console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false,fake_serial_only:true}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
