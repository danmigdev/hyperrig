'use strict';
// Original SerialTransport.readLoop and Pedal queue, fake native streams only.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const guardText=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8').replace(/\r\n/g,'\n');
const policy=fs.readFileSync(process.argv[4],'utf8');
const catalogFixture=process.argv[5]==='--catalog-from-stdin'?JSON.parse(fs.readFileSync(0,'utf8')):null;
const profile=JSON.parse(html.match(/globalThis\.HYPERRIG_MINI_BUILD=(\{[^<]+\});<\/script>/)[1]);
const originalTransport=html.slice(html.indexOf('const SerialTransport = {'),html.indexOf('/* Bluetooth LE (firmware'));
const originalPedal=html.slice(html.indexOf('const Pedal = {'),html.indexOf('/* ============================================================ estado */'));
const pong='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11';
const plan={kind:'mini-exact-FX-stress-plan-v1',executed:false,restore_request:'PLOAD 0',
 baseline_gain:[0,0],trial_gain:[0,-12],setup_requests:['GAIN 0 -12'],steps:[{
 type:'gate',bank:'P',add_request:'FXA P 99 gate',configure_after_actual_id:[
 {request_template:'FXE {id} 0'},{request_template:'FXP {id} 0 -90'},
 {request_template:'FXE {id} 1'}]}]};
let checks=0;
const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
const rejects=async f=>{await assert.rejects(f);checks++;};

async function setup({rejectAdd=false,forgeParameter=false,delayedWrite=false,pollBeforePrime=false,catalog=null}={}){
 let ctx,tick=0,gain=[0,0],block=null;
 const waits=[],chunks=[],writes=[];let opens=0,closes=0;
 const deliver=value=>waits.length?waits.shift()(value):chunks.push(value);
 const nativeReader={read(){return chunks.length?Promise.resolve(chunks.shift()):new Promise(resolve=>waits.push(resolve));},
  cancel:async()=>deliver({done:true}),releaseLock(){}};
 const reply=line=>{
  if(line==='PING')return [pong];
  if(line==='GAIN')return ['GAIN in='+gain[0]+' out='+gain[1]+' dB'];
  if(line==='LVL')return ['LVL in=-800 out=-800 ci=0 co=0 m=2'];
  if(line==='FXT')return catalog||['FXT 1 gate cost=490 cat=dynamics mem=0','FXT  0 umbral_db -90..0 (-70)','FXT  1 release_ms 5..1000 (120)','FXT end'];
  if(line==='FXS')return ['FXS amp=1 on=1',...(block?['FX P0 id=0 gate on='+block.on+' p='+block.p+',120,0,0,0,0,0 ticks=490']:[]),
   'FXS cpu=0/21364 ticks (0%) mem_fx=0 B','FXS peak=0 ticks skipped=0'];
  if(line==='MEM')return ['MEM heap=293696 fxcap=113096 pool_largest=102384 pool_used=0 pool_bad=0'];
  if(line.startsWith('GAIN ')){gain=line.split(' ').slice(1).map(Number);return ['GAIN in='+gain[0]+' out='+gain[1]+' dB'];}
  if(line==='FXA P 99 gate'){
   if(rejectAdd)return ['ERR FXA not enough CPU'];
   block={on:1,p:-70};return ['FXA id=0 gate','FX cpu=490/21364 ticks (2%) mem_fx=0 B'];
  }
  if(/^FXE 0 [01]$/.test(line)){block.on=+line.at(-1);return ['FXE ok'];}
  if(line==='FXP 0 0 -90'){block.p=-90;return ['FXP ok -90'];}
  if(line==='PLOAD 0'){gain=[0,0];block=null;return ["PLOAD ok 0 'Preset 1A' missing=0 capture=0 ir=-1 ms=2"];}
  throw Error('unexpected fake device request: '+line);
 };
 const nativeWriter={write:async bytes=>{
  const text=new TextDecoder().decode(bytes);writes.push(text);const rows=reply(text.trim());
  setTimeout(()=>{
   if(forgeParameter && text.startsWith('FXP ')){ctx.pedal.feed(rows.join('\n')+'\n');return;}
   deliver({done:false,value:new TextEncoder().encode(rows.join('\n')+'\n')});
  },0);
  if(delayedWrite)await new Promise(resolve=>setTimeout(resolve,10));
 },releaseLock(){}};
 const port={open:async()=>{opens++;},close:async()=>{closes++;},getInfo:()=>({usbVendorId:0x3654,usbProductId:0x5155}),
  readable:{getReader:()=>nativeReader},writable:{getWriter:()=>nativeWriter}};
 ctx={HYPERRIG_MINI_BUILD:structuredClone(profile),navigator:{serial:{}},
  localStorage:{getItem:()=>null,setItem(){}},document:{body:{inert:false}},
  performance:{now:()=>++tick},Date,TextEncoder,TextDecoder,Uint8Array,
  setTimeout:(fn,ms)=>setTimeout(fn,Math.min(ms,80)),clearTimeout,
  DEMO:false,APP:false,S:{connected:true,fw:pong},enc:new TextEncoder(),dec:new TextDecoder(),
  Log:{ev(){},cmd(){}},gdSent:()=>null,gdDone(){},strayLines:()=>[],noAnswer(){},setAlert(){},blePairLine:()=>false};
 ctx.window=ctx;vm.createContext(ctx);vm.runInContext(policy,ctx);
 vm.runInContext(originalTransport+'\nglobalThis.transport=SerialTransport;',ctx);
 ctx.pickTransport=()=>ctx.transport;vm.runInContext(originalPedal+'\nglobalThis.pedal=Pedal;',ctx);
 ctx.transport.onData=text=>ctx.pedal.feed(text);ctx.transport.onClose=()=>{ctx.S.connected=false;};
 await ctx.transport.open(port); // Creates one pending native read BEFORE installation.
 ctx.HyperRigMini.acceptPong(pong,'usb-cdc');
 const oldPolicy=ctx.HyperRigMini,oldReader=nativeReader.read;
 vm.runInContext(guardText,ctx);
 ctx.installMiniLatencyGuard({profile:ctx.HyperRigMini.profile,pong,restore_ack_prefix:"PLOAD ok 0 'Preset 1A'"});
 const guard=ctx.__miniLatencyGuard;
 const poll=pollBeforePrime?ctx.pedal.cmd('LVL','LVL',100):Promise.resolve();
 await guard.prime();await ctx.pedal.cmd('PING','PONG',100);
 await poll;
 await ctx.pedal.cmd('FXT',x=>x==='FXT end',100);await ctx.pedal.cmd('GAIN','GAIN',100);
 return {ctx,guard,writes,port,oldPolicy,oldReader,nativeReader,
  counts:()=>({opens,closes}),shutdown:async()=>{await nativeReader.cancel();}};
}

async function main(){
 const good=await setup();
 check(good.guard.state.commands[0].priming,true);
 check(good.guard.state.commands[0].native_RX_verified,false);
 check(good.guard.state.commands[1].native_RX_verified,true);
 good.guard.configure(structuredClone(plan));
 for(let i=0;i<5;i++)await good.guard.executeNext();
 check(good.guard.state.phase,'between');
 await good.ctx.pedal.cmd('FXS',x=>x.startsWith('FXS peak='),100);
 await good.ctx.pedal.cmd('MEM','MEM',100);good.guard.advance();check(good.guard.state.phase,'stress_done');
 good.guard.restore();await good.guard.executeNext();const result=await good.guard.detach(true);
 check(result.detached,true);check(result.healthy,true);check(good.ctx.HyperRigMini,good.oldPolicy);
 check(good.nativeReader.read,good.oldReader);check(good.ctx.document.body.inert,false);
 check(good.counts(),{opens:1,closes:0});
 check(good.writes.filter(x=>/^(GAIN |FXA |FXP |FXE |PLOAD )/.test(x)),
  ['GAIN 0 -12\n','FXA P 99 gate\n','FXE 0 0\n','FXP 0 0 -90\n','FXE 0 1\n','PLOAD 0\n']);
 check(good.ctx.HyperRigMini.profile.capabilities.write,false);await good.shutdown();

 const reject=await setup({rejectAdd:true});reject.guard.configure(structuredClone(plan));
 await reject.guard.executeNext();const refusal=await reject.guard.executeNext();
 check(refusal.rejected,true);check(reject.guard.state.healthy,true);check(reject.guard.state.phase,'rejected');
 reject.guard.restore();await reject.guard.executeNext();const rejectedTrace=await reject.guard.detach(true);
 check(reject.writes.filter(x=>x.startsWith('FXA')).length,1);await reject.shutdown();

 const forged=await setup({forgeParameter:true});forged.guard.configure(structuredClone(plan));
 for(let i=0;i<3;i++)await forged.guard.executeNext();
 await rejects(()=>forged.guard.executeNext());check(forged.guard.state.healthy,false);
 await rejects(async()=>forged.guard.restore());check(forged.writes.some(x=>x==='PLOAD 0\n'),false);
 const blocked=await forged.guard.detach(false);check(blocked.detached,false);check(forged.ctx.document.body.inert,true);await forged.shutdown();

 const bad=await setup();const malformed=structuredClone(plan);
 malformed.steps[0].configure_after_actual_id[1].request_template='FXP {id} 0 100';
 await rejects(async()=>bad.guard.configure(malformed));check(bad.writes.some(x=>x.startsWith('FX')),true); // FXT query only
 check(bad.writes.some(x=>x.startsWith('FXA ')),false);await bad.shutdown();

 const direct=await setup();await rejects(()=>direct.ctx.transport.writer.write(new TextEncoder().encode('PSAVE 0 Bad\n')));
 check(direct.writes.some(x=>x.startsWith('PSAVE')),false);await direct.shutdown();
 const unchanged=await setup();const detached=await unchanged.guard.detach(false);
 check(detached.detached,true);check(unchanged.counts(),{opens:1,closes:0});await unchanged.shutdown();
 const delayed=await setup({delayedWrite:true});
 check(delayed.guard.state.wire.every(w=>w.completed),true);
 check(delayed.guard.state.commands.filter(c=>!c.priming).every(c=>c.native_RX_verified),true);
 await delayed.guard.detach(false);await delayed.shutdown();
 const polling=await setup({pollBeforePrime:true});
 check([...polling.guard.state.commands.filter(c=>c.priming).map(c=>c.line)],['LVL','PING']);
 check(polling.guard.state.commands.filter(c=>c.priming).every(c=>c.native_RX_verified===false),true);
 check(polling.guard.state.commands.filter(c=>!c.priming && c.line==='PING').every(c=>c.native_RX_verified),true);
 await polling.guard.detach(false);await polling.shutdown();
 if(catalogFixture){
  const catalog=await setup({catalog:catalogFixture.fxt});
  catalog.guard.configure(catalogFixture.plan);
  check(catalog.guard.state.phase,'attenuate');
  check(catalog.guard.state.events.find(e=>e.kind==='plan').plan.steps.length,13);
  await catalog.guard.detach(false);await catalog.shutdown();
 }
 console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false,
  original_functions:['SerialTransport.readLoop','SerialTransport.write','Pedal.cmd','Pedal.feed','commandPolicy'],
  pending_native_read_before_hook_tested:true,raw_forgery_rejected:true,no_new_native_open_close:true,
  success_trace:result,rejected_trace:rejectedTrace}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
