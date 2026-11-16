'use strict';
// Execute the original policy, Pedal queue, BLE-key helper and USB bootstrap
// branch on fake native serial only. No browser/port/device is opened.
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const guardText=fs.readFileSync(process.argv[2],'utf8');
const html=fs.readFileSync(process.argv[3],'utf8').replace(/\r\n/g,'\n');
const policy=fs.readFileSync(process.argv[4],'utf8');
const profile=JSON.parse(html.match(/globalThis\.HYPERRIG_MINI_BUILD=(\{[^<]+\});<\/script>/)[1]);
const pong='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11';
const rejection='ERR MINI_APP firmware mutations are not validated for this MINI build';
const originalPedal=html.slice(html.indexOf('const Pedal = {'),html.indexOf('/* ============================================================ estado */'));
const pairing=html.slice(html.indexOf('function parseBleBond('),html.indexOf('/*BLEPAIR-END*/'));
const fetchKey=html.slice(html.indexOf('async function bleKeyFetch('),html.indexOf('async function bleAuthTry('));
const usbStart=html.indexOf('} else if (/ ble\\b/.test(pong))');
assert(usbStart>=0);
const usbEnd=html.indexOf('\n  }\n  { const full',usbStart);
assert(usbEnd>usbStart);
const usb=html.slice(html.indexOf('const b = reply(',usbStart),usbEnd);
assert(usb.includes('await bleKeyFetch(S.btMac).catch'));
let checks=0;
const check=(a,b)=>{assert.deepEqual(a,b);checks++;};
const rejects=async f=>{await assert.rejects(f);checks++;};
async function setup({wrongReply=false}={}) {
  let tick=0,opened=false,reader;
  const pending=[],writes=[],stored=[];
  const port={getInfo:()=>({usbVendorId:0x3654,usbProductId:0x5155}),
    open:async()=>{opened=true;},close:async()=>{opened=false;},
    readable:{getReader:()=>({read:async()=>({done:false,value:pending.shift()})})}};
  const transport={isOpen:()=>opened,write:async text=>{
    writes.push(text);
    const line=text.trim();
    const response=line==='PING'?pong:line==='BLE'?"BLE on=1 mac=00:11:22:33:44:55 enc=0 bonds=0 bt=1":line==='FXT'?'FXT end':'ERR unexpected';
    pending.push(new TextEncoder().encode(response+'\n'));const received=await reader.read();
    ctx.pedal.feed(new TextDecoder().decode(received.value));
  }};
  const ctx={HYPERRIG_MINI_BUILD:structuredClone(profile),navigator:{serial:{requestPort:async()=>port}},
    localStorage:{getItem:()=>null,setItem:(...args)=>stored.push(args)},document:{addEventListener(){},querySelector:()=>null},
    performance:{now:()=>++tick},Date,DOMException,TextEncoder,TextDecoder,setTimeout,clearTimeout,
    DEMO:false,APP:false,S:{},SerialTransport:transport,pickTransport:()=>transport,
    Log:{ev(){},cmd(){}},gdSent:()=>null,gdDone(){},strayLines:()=>[],noAnswer(){},setAlert(){},blePairLine:()=>false,
    reply:(lines,prefix)=>lines.find(l=>l.startsWith(prefix))||'',pong};
  vm.createContext(ctx);vm.runInContext(policy,ctx);vm.runInContext(pairing+'\n'+fetchKey,ctx);
  vm.runInContext(originalPedal+'\nglobalThis.pedal=Pedal;',ctx);
  if(wrongReply){const command=ctx.pedal.cmd.bind(ctx.pedal);ctx.pedal.cmd=(line,...args)=>
    line==='BLE key'?Promise.resolve(['ERR MINI_APP unexpected local denial']):command(line,...args);}
  vm.runInContext(guardText,ctx);
  const guard=ctx.installMiniBrowserFirstPresetGuard({live:true,image_sha256:profile.image_sha256,pong});
  guard.installApp(transport,ctx.pedal,ctx.HyperRigMini.profile);guard.allowRequest();
  const p=await ctx.navigator.serial.requestPort();await p.open({baudRate:115200});reader=p.readable.getReader();
  await ctx.pedal.cmd('PING','PONG');ctx.HyperRigMini.acceptPong(pong,'usb-cdc');
  return {ctx,guard,writes,transport,port,stored};
}
async function main(){
  const good=await setup();
  await vm.runInContext('(async()=>{'+usb+';return await Pedal.cmd("FXT","FXT",100);})()',good.ctx);
  await good.ctx.pedal.chain;
  check(good.writes,['PING\n','BLE\n','FXT\n']);check(good.guard.state.fatal,null);
  check(good.guard.state.captureMutations,0);check(good.guard.state.mutations,0);
  const local=good.guard.state.events.filter(e=>e.kind==='local_editor_policy_rejection');
  check(local.length,1);check(local[0].line,'BLE key');check(Array.from(local[0].lines),[rejection]);
  check(local[0].local_only,true);check(local[0].wire_command_observed,false);
  check(good.guard.state.commands.some(c=>c.line==='BLE key'),false);
  check(good.ctx.HyperRigMini.profile.capabilities.write,false);
  check(good.stored.some(([key])=>key==='hyperrig.mini.blekeys'),false);
  check(good.guard.state.rx.length,3);await good.port.close();check(good.guard.state.closes,1);
  const direct=await setup();await rejects(()=>direct.transport.write('BLE key\n'));
  check(direct.writes,['PING\n']);await direct.port.close();
  const wrong=await setup({wrongReply:true});await rejects(()=>vm.runInContext('bleKeyFetch("fake")',wrong.ctx));
  check(wrong.writes,['PING\n']);check(wrong.guard.state.stopped,true);await wrong.port.close();
  const other=await setup();await rejects(()=>other.ctx.pedal.cmd('BLE pair','BLE',100));
  check(other.writes,['PING\n']);check(other.guard.state.stopped,true);await other.port.close();
  console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false,
    original_functions:['commandPolicy','Pedal.cmd','Pedal.feed','bleKeyFetch','connect USB BLE branch'],
    bootstrap_wire:['PING','BLE','FXT'],BLE_key_wire_count:0,fake_native_serial_only:true}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
