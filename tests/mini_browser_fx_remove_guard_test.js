'use strict';
// Real editor queue/readLoop, fake native streams; no browser or hardware.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const fixture=JSON.parse(fs.readFileSync(0,'utf8'));
const guardText=fs.readFileSync('tools/mini_browser_fx_remove_guard.js','utf8');
const html=fs.readFileSync('build/hyperrig-mini-audio-v3/app/web/tankmini.html','utf8').replace(/\r\n/g,'\n');
const policy=fs.readFileSync('app/mini/mini-profile.js','utf8');
const profile=JSON.parse(html.match(/globalThis\.HYPERRIG_MINI_BUILD=(\{[^<]+\});<\/script>/)[1]);
const transportSource=html.slice(html.indexOf('const SerialTransport = {'),html.indexOf('/* Bluetooth LE (firmware'));
const pedalSource=html.slice(html.indexOf('const Pedal = {'),html.indexOf('/* ============================================================ estado */'));
const plan={kind:'mini-exact-FXR-removal-plan-v1',executed:false,setup_requests:['GAIN 0 -12'],
  steps:[{type:'boost',bank:'Q',add_request:'FXA Q 99 boost'}],restore_request:'PLOAD 0'};
let checks=0;
const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
const reject=async f=>{await assert.rejects(f);checks++;};

async function setup({bareFXR=false,loseFXR=false,activeLatency=false}={}){
  let ctx,gain=[0,0],boost=null,tick=0,opens=0,closes=0;
  const pending=[],chunks=[],writes=[];
  const deliver=value=>pending.length?pending.shift()(value):chunks.push(value);
  const reader={read(){return chunks.length?Promise.resolve(chunks.shift()):new Promise(r=>pending.push(r));},
    cancel:async()=>deliver({done:true}),releaseLock(){}};
  const reply=line=>{
    if(line==='PING')return [fixture.pong];
    if(line==='FXT')return fixture.fxt;
    if(line==='MEM')return fixture.mem;
    if(line==='GAIN')return [`GAIN in=${gain[0]} out=${gain[1]} dB`];
    if(line==='LVL')return fixture.responses.LVL.map(x=>x.replace(/ g=-?\d+\/-?\d+ /,` g=${gain[0]}/${gain[1]} `));
    if(line==='FXS')return [fixture.responses.FXS[0],...(boost?
      [`FX Q0 id=5 boost on=1 p=${boost.value},0,0,0,0,0,0 ticks=346 l=0 g=-1 fu=0`]:[]),...fixture.responses.FXS.slice(1)];
    if(line==='GAIN 0 -12'){gain=[0,-12];return ['GAIN in=0 out=-12 dB'];}
    if(line==='FXA Q 99 boost'){boost={value:6};return ['FXA id=5 boost','FX cpu=346/23018 ticks (1%) mem_fx=0 B'];}
    if(line==='FXP 5 0 -1'){boost.value=-1;return ['FXP ok -1'];}
    if(line==='FXR 5'){
      boost=null;if(loseFXR)return null;
      return [bareFXR?'FXR ok':'FXR ok cpu=0/23018 ticks (0%) mem_fx=0 B'];
    }
    if(line==='PLOAD 0'){gain=[0,0];boost=null;return [fixture.ack+' missing=0 capture=0 ir=0 ms=3'];}
    if(fixture.responses[line])return fixture.responses[line];
    throw Error('Unexpected fake request '+line);
  };
  const writer={write:async bytes=>{
    const line=new TextDecoder().decode(bytes);writes.push(line);const rows=reply(line.trim());
    if(rows)setTimeout(()=>deliver({done:false,value:new TextEncoder().encode(rows.join('\n')+'\n')}),0);
  },releaseLock(){}};
  const port={open:async()=>{opens++;},close:async()=>{closes++;},getInfo:()=>({usbVendorId:0x3654,usbProductId:0x5155}),
    readable:{getReader:()=>reader},writable:{getWriter:()=>writer}};
  ctx={HYPERRIG_MINI_BUILD:structuredClone(profile),navigator:{serial:{}},
    localStorage:{getItem:()=>null,setItem(){}},document:{body:{inert:false}},
    performance:{now:()=>++tick},Date,TextEncoder,TextDecoder,Uint8Array,
    setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,80)),clearTimeout,DEMO:false,APP:false,
    S:{connected:true,fw:fixture.pong},enc:new TextEncoder(),dec:new TextDecoder(),
    Log:{ev(){},cmd(){}},gdSent:()=>null,gdDone(){},strayLines:()=>[],noAnswer(){},setAlert(){},blePairLine:()=>false,
    __miniLatencyGuard:Object.freeze({state:Object.freeze({detached:!activeLatency})})};
  const oldLatency=ctx.__miniLatencyGuard;ctx.window=ctx;vm.createContext(ctx);vm.runInContext(policy,ctx);
  vm.runInContext(transportSource+'\nglobalThis.transport=SerialTransport;',ctx);
  ctx.pickTransport=()=>ctx.transport;vm.runInContext(pedalSource+'\nglobalThis.pedal=Pedal;',ctx);
  ctx.transport.onData=text=>ctx.pedal.feed(text);ctx.transport.onClose=()=>{ctx.S.connected=false;};
  await ctx.transport.open(port);ctx.HyperRigMini.acceptPong(fixture.pong,'usb-cdc');
  const old={policy:ctx.HyperRigMini,read:reader.read,write:writer.write,cmd:ctx.pedal.cmd};
  vm.runInContext(guardText,ctx);
  if(activeLatency){assert.throws(()=>ctx.installMiniFXRemovalGuard({profile:ctx.HyperRigMini.profile,pong:fixture.pong,restore_ack_prefix:fixture.ack}));checks++;
    await reader.cancel();return {rejectedActive:true};}
  ctx.installMiniFXRemovalGuard({profile:ctx.HyperRigMini.profile,pong:fixture.pong,restore_ack_prefix:fixture.ack});
  const guard=ctx.__miniFXRemovalGuard;
  const query=line=>ctx.pedal.cmd(line,x=>{
    if(line==='FXT')return x==='FXT end';
    if(line==='FXS')return /^FXS (peak|pico)=/.test(x);
    if(['PLIST','CLIST','ILIST','SNAPNAME'].includes(line))return x.startsWith(line+' end');
    return x.startsWith(line.split(' ')[0]);
  },100);
  const snapshot=async()=>{const responses={};for(const key of fixture.reads)responses[key]=await query(key);return {responses};};
  await guard.prime();await query('PING');
  return {ctx,guard,writes,old,reader,writer,oldLatency,query,snapshot,
    counts:()=>({opens,closes}),close:async()=>reader.cancel()};
}

async function ready(options){
  const env=await setup(options),report={before:await env.snapshot()};
  report.actual_catalog=await env.query('FXT');env.guard.configure(structuredClone(plan));
  for(let i=0;i<3;i++)await env.guard.executeNext();
  report.temporary_instance_id=env.guard.state.created[0].id;
  report.added=await env.snapshot();report.added_memory=await env.query('MEM');
  return {env,report};
}

async function main(){
  const {env,report}=await ready();
  check(env.writes.filter(x=>/^(GAIN |FX[APR] )/.test(x)),['GAIN 0 -12\n','FXA Q 99 boost\n','FXP 5 0 -1\n']);
  check(env.guard.state.phase,'added_ack');check(report.temporary_instance_id,5);
  env.guard.remove();await env.guard.executeNext();
  report.removed=await env.snapshot();report.removed_memory=await env.query('MEM');
  env.guard.restore();await env.guard.executeNext();report.restored=await env.snapshot();
  report.guard=await env.guard.detach(true);
  check(report.guard.detached,true);check(env.ctx.__miniLatencyGuard===env.oldLatency,true);
  check(env.ctx.HyperRigMini===env.old.policy,true);check(env.reader.read===env.old.read,true);
  check(env.writer.write===env.old.write,true);check(env.ctx.pedal.cmd===env.old.cmd,true);
  check(env.counts(),{opens:1,closes:0});await env.close();
  const bare=await ready({bareFXR:true});bare.env.guard.remove();await reject(()=>bare.env.guard.executeNext());
  check(bare.env.writes.filter(x=>x==='FXR 5\n').length,1);check(bare.env.guard.state.healthy,false);
  check((await bare.env.guard.detach(false)).detached,false);await bare.env.close();
  const lost=await ready({loseFXR:true});lost.env.guard.remove();await reject(()=>lost.env.guard.executeNext());
  check(lost.env.writes.filter(x=>x==='FXR 5\n').length,1);check(lost.env.writes.includes('PLOAD 0\n'),false);
  check((await lost.env.guard.detach(false)).detached,false);await lost.env.close();
  const unplanned=await ready();await reject(()=>unplanned.env.ctx.pedal.cmd('FXR 0','FXR',100));
  check(unplanned.env.writes.some(x=>x.startsWith('FXR ')),false);await unplanned.env.guard.detach(false);await unplanned.env.close();
  check((await setup({activeLatency:true})).rejectedActive,true);
  console.log(JSON.stringify({checks,device_io:false,browser_started:false,report}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
