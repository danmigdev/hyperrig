'use strict';
// Original editor command queue and native stream read-loop; fake device only.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const guardSource=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8');
const policy=fs.readFileSync('app/mini/mini-profile.js','utf8');
const profile=JSON.parse(html.match(/globalThis\.HYPERRIG_MINI_BUILD=(\{[^<]+\});<\/script>/)[1]);
const transportSource=html.slice(html.indexOf('const SerialTransport = {'),html.indexOf('/* Bluetooth LE (firmware'));
const pedalSource=html.slice(html.indexOf('const Pedal = {'),html.indexOf('/* ============================================================ estado */'));
const PONG='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11';
let checks=0;
const check=(a,b)=>{assert.deepEqual(JSON.parse(JSON.stringify(a)),b);checks++;};
const rejects=async f=>{await assert.rejects(f);checks++;};
async function setup({empty=0,partial=false,writeError=false,pendingWrite=false,wrongPong=false,delayedWrite=false}={}){
  let ctx,tick=0,ping=0,opens=0,closes=0;
  const writes=[],waits=[],chunks=[];
  const deliver=v=>waits.length?waits.shift()(v):chunks.push(v);
  const reader={read:()=>chunks.length?Promise.resolve(chunks.shift()):new Promise(r=>waits.push(r)),
    cancel:async()=>deliver({done:true}),releaseLock(){}};
  const writer={write:async bytes=>{
    const text=new TextDecoder().decode(bytes);writes.push(text);
    if(writeError)throw Error('fake native write failure');
    if(pendingWrite)return new Promise(()=>{});
    if(text==='PING\n'){
      ping++;
      if(partial)setTimeout(()=>deliver({done:false,value:new TextEncoder().encode('PO')}),0);
      else if(ping>empty)setTimeout(()=>deliver({done:false,value:new TextEncoder().encode((wrongPong?'PONG wrong':PONG)+'\n')}),0);
    }
    if(delayedWrite)await new Promise(resolve=>setTimeout(resolve,10));
  },releaseLock(){}};
  const port={getInfo:()=>({usbVendorId:0x3654,usbProductId:0x5155}),
    open:async()=>{opens++;},close:async()=>{closes++;},
    readable:{getReader:()=>reader},writable:{getWriter:()=>writer}};
  ctx={HYPERRIG_MINI_BUILD:profile,navigator:{serial:{requestPort:async()=>port}},
    localStorage:{getItem:()=>null,setItem(){}},document:{addEventListener(){}},
    performance:{now:()=>++tick},Date,DOMException,TextEncoder,TextDecoder,Uint8Array,
    setTimeout:(f,ms)=>setTimeout(f,Math.min(ms,20)),clearTimeout,
    DEMO:false,APP:false,S:{connected:false},enc:new TextEncoder(),dec:new TextDecoder(),
    Log:{ev(){},cmd(){},cmdTxt:x=>x},gdSent:()=>null,gdDone(){},strayLines:()=>[],noAnswer(){},setAlert(){},blePairLine:()=>false};
  ctx.window=ctx;vm.createContext(ctx);vm.runInContext(policy,ctx);
  vm.runInContext(guardSource,ctx);
  vm.runInContext(transportSource+'\nglobalThis.transport=SerialTransport;',ctx);
  ctx.pickTransport=()=>ctx.transport;
  vm.runInContext(pedalSource+'\nglobalThis.pedal=Pedal;',ctx);
  const guard=ctx.installMiniBrowserSavedReloadGuard({live:true,image_sha256:profile.image_sha256,pong:PONG});
  guard.installApp(ctx.transport,ctx.pedal,ctx.HyperRigMini.profile);guard.allowRequest();
  await ctx.pedal.connect();
  const ask=()=>ctx.pedal.cmd('PING','PONG',700);
  const shutdown=async()=>{guard.stop();await ctx.pedal.disconnect();};
  return {ctx,guard,port,reader,writer,ask,shutdown,writes,deliver,counts:()=>({opens,closes})};
}
async function main(){
  const good=await setup({empty:2});
  let pong='';for(let k=0;k<5&&!pong;k++)pong=(await good.ask()).find(x=>x.startsWith('PONG'))||'';
  check(pong,PONG);check(good.writes,['PING\n','PING\n','PING\n']);
  check(good.guard.state.bootstrap_attempts.map(a=>a.status),['empty_timeout','empty_timeout','pong']);
  check(good.guard.state.editorCompletions.map(e=>e.timed_out),[true,true,false]);
  check(good.guard.state.nativeWrites.every(w=>w.completed&&w.hex==='50494e470a'),true);
  await good.shutdown();check(good.guard.state.fatal,null);check(good.guard.state.nativeErrors.length,0);
  check(good.guard.state.events.some(e=>e.kind==='native_reader_ended_after_stop'),true);
  check(good.counts(),{opens:1,closes:1});
  const successful=JSON.parse(JSON.stringify(good.guard.state));
  const delayed=await setup({delayedWrite:true});check(await delayed.ask(),[PONG]);
  check(delayed.guard.state.editorCompletions[0].seq<delayed.guard.state.nativeWrites[0].completed_seq,true);
  check(delayed.guard.state.nativeWrites[0].completed_seq<delayed.guard.state.bootstrap_attempts[0].completion_seq,true);
  await delayed.shutdown();const delayedTrace=JSON.parse(JSON.stringify(delayed.guard.state));
  const max=await setup({empty:5});for(let k=0;k<5;k++)check(await max.ask(),[]);
  check(max.guard.state.bootstrap_attempts.at(-1).repeat_permitted,false);
  await rejects(()=>max.ask());check(max.writes.length,5);await max.shutdown();
  for(const options of [{partial:true},{writeError:true},{pendingWrite:true},{wrongPong:true}]){
    const bad=await setup(options);await rejects(()=>bad.ask());check(bad.writes.length,1);
    await rejects(()=>bad.ask());check(bad.writes.length,1);await bad.shutdown();
  }
  const gap=await setup({empty:1});check(await gap.ask(),[]);
  gap.deliver({done:false,value:new TextEncoder().encode('PO')});await new Promise(r=>setTimeout(r,2));
  await rejects(()=>gap.ask());check(gap.writes.length,1);await gap.shutdown();
  const ended=await setup({empty:1});await ended.reader.cancel();await new Promise(r=>setTimeout(r,2));
  await rejects(()=>ended.ask());check(ended.writes.length,0);check(ended.guard.state.nativeErrors.length,1);await ended.shutdown();
  const query=await setup();await query.ask();query.ctx.HyperRigMini.acceptPong(PONG,'usb-cdc');
  await rejects(()=>query.ctx.pedal.cmd('MODEL','MODEL',700));
  check(query.writes,['PING\n','MODEL\n']);await query.shutdown();
  const wrongArgs=await setup();await rejects(()=>wrongArgs.ctx.pedal.cmd('PING','PONG',3000));
  check(wrongArgs.writes,[]);await wrongArgs.shutdown();
  console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false,
    original_functions:['SerialTransport.open','SerialTransport.readLoop','SerialTransport.write','SerialTransport.close','Pedal.cmd'],
    cleanup_cancel_done_observed:true,success_guard:successful,delayed_guard:delayedTrace}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
