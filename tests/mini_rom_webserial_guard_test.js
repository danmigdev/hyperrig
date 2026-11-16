'use strict';
const assert=require('assert').strict;
const {createMiniRomSession}=require(require('path').resolve(process.argv[2]));
const pong='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe';
let checks=0;
const equal=(a,b)=>{assert.deepEqual(a,b);checks++;};
const rejects=async f=>{await assert.rejects(f);checks++;};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup({pid=0x5155,writeError=null,closeError=false}={}) {
  const calls={requests:[],opens:[],writes:[],closes:0,cancels:0};
  const queue=[];let waiter,disconnect;
  const push=text=>{const row={value:new TextEncoder().encode(text),done:false};if(waiter){const w=waiter;waiter=null;w(row);}else queue.push(row);};
  const reader={read:()=>queue.length?Promise.resolve(queue.shift()):new Promise(r=>{waiter=r;}),
    cancel:async()=>{calls.cancels++;if(waiter){waiter({done:true});waiter=null;}},releaseLock(){}};
  const writer={write:async bytes=>{const text=new TextDecoder().decode(bytes);calls.writes.push(text);if(writeError===text)throw Error('TEST native write failure');},releaseLock(){}};
  const port={getInfo:()=>({usbVendorId:0x3654,usbProductId:pid}),open:async options=>calls.opens.push(options),
    readable:{getReader:()=>reader},writable:{getWriter:()=>writer},
    close:async()=>{calls.closes++;if(closeError)throw Error('TEST close failed');}};
  const serial={requestPort:async options=>{calls.requests.push(options);return port;},
    addEventListener:(name,fn)=>{assert.equal(name,'disconnect');disconnect=fn;},removeEventListener(){}};
  const session=createMiniRomSession({execute:true,com:'COM3',pong},serial);
  return {session,calls,push,disconnect:()=>disconnect({target:port})};
}
async function identified(x){await x.session.connect(true);x.push(pong+'\n');await tick();equal(x.session.state.identityVerified,true);}
async function main(){
  for(const config of [{execute:false,com:'COM3',pong},{execute:true,com:'COM0',pong},{execute:true,com:'COM3',pong:'PONG tankg_fw M5.71 rel ble Nov 12 2026 16:04:11'}]){
    assert.throws(()=>createMiniRomSession(config,{requestPort(){throw Error('must not be reached');}}));checks++;
  }
  {const x=setup();await rejects(()=>x.session.connect(false));equal(x.calls.requests.length,0);await x.session.close();}
  {const x=setup({pid:0x4155});await rejects(()=>x.session.connect(true));equal(x.calls.opens.length,0);equal(x.calls.writes,[]);await x.session.close();}
  {const x=setup();await x.session.connect(true);equal(x.calls.writes,['PING\n']);await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n']);await x.session.close();}
  {
    const x=setup();await x.session.connect(true);
    equal(x.calls.requests,[{filters:[{usbVendorId:0x3654,usbProductId:0x5155}]}]);equal(x.calls.opens,[{baudRate:115200}]);
    x.push(pong.slice(0,15));await tick();equal(x.session.state.identityVerified,false);
    x.push(pong.slice(15)+'\r\n');await tick();equal(x.session.state.identityVerified,true);
    await x.session.enterROM();equal(x.calls.writes,['PING\n','UBOOT\n']);equal(x.session.state.actualACKObserved,false);
    x.push('OK UBOOT\n');await tick();equal(x.session.state.actualACKObserved,true);
    x.disconnect();equal(x.session.state.disconnectObserved,true);equal(x.session.state.ROMVerified,false);
    await x.session.close();equal(x.session.state.nativeCloseVerified,true);equal(x.calls.closes,1);
    await x.session.close();equal(x.calls.closes,1);equal(x.session.state.rx.map(r=>r.hex).join(''),Buffer.from(pong+'\r\nOK UBOOT\n').toString('hex'));
  }
  {const x=setup();await identified(x);await x.session.enterROM();await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n','UBOOT\n']);await x.session.close();}
  {const x=setup();await identified(x);await rejects(()=>x.session.connect(true));equal(x.calls.requests.length,1);await x.session.close();}
  {const x=setup();await x.session.connect(true);x.push(pong.replace('tankm','tankg')+'\n');await tick();equal(x.session.state.identityVerified,false);await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n']);await x.session.close();}
  {const x=setup();await identified(x);x.disconnect();await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n']);equal(x.session.state.actualACKObserved,false);await x.session.close();}
  {const x=setup();await identified(x);await x.session.enterROM();x.disconnect();await x.session.close();equal(x.session.state.actualACKObserved,false);equal(x.session.state.ROMVerified,false);equal(x.session.state.nativeCloseVerified,true);}
  {const x=setup({closeError:true});await identified(x);await x.session.close();equal(x.session.state.nativeCloseVerified,false);equal(x.calls.closes,1);assert.match(x.session.state.closeError,/TEST close failed/);checks++;}
  {const x=setup({writeError:'PING\n'});await rejects(()=>x.session.connect(true));await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n']);await x.session.close();}
  {const x=setup({writeError:'UBOOT\n'});await identified(x);await rejects(()=>x.session.enterROM());await rejects(()=>x.session.enterROM());equal(x.calls.writes,['PING\n','UBOOT\n']);equal(x.session.state.ubootAttempted,true);equal(x.session.state.ubootWriteCompleted,false);equal(x.session.state.actualACKObserved,false);await x.session.close();}
  {const x=setup();await x.session.connect(true);x.push('OK UBOOT\n');await tick();equal(x.session.state.actualACKObserved,false);await rejects(()=>x.session.enterROM());await x.session.close();}
  {const x=setup();await x.session.connect(true);x.push('A'.repeat(4097));await tick();assert.match(x.session.state.error,/line bound/);checks++;await rejects(()=>x.session.enterROM());await x.session.close();}
  {const x=setup();equal(typeof x.session.transmit,'undefined');equal(Object.keys(x.session),['state','connect','enterROM','close']);await x.session.close();}
  console.log(JSON.stringify({tests:'fake WebSerial only',checks,hardware_io:false}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
