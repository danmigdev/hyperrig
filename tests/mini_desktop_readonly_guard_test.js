'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict;
const source=fs.readFileSync(process.argv[2],'utf8');let checks=0;
function setup({pid=0x5155,closeFail=false,write=false,families={},first=false,version='tankm_fw M5.71 rel ble'}={}){
  const calls={requests:[],opens:[],writes:[],closes:0};let clock=0;
  const port={getInfo:()=>({usbVendorId:0x3654,usbProductId:pid}),open:async o=>calls.opens.push(o),
    close:async()=>{calls.closes++;if(closeFail)throw Error('native close failure');}};
  const ctx={navigator:{serial:{requestPort:async o=>{calls.requests.push(o);return port;}}},
    performance:{now:()=>clock},DOMException,localStorage:{setItem(){}}};
  vm.createContext(ctx);vm.runInContext(source,ctx);
  const guard=ctx.installMiniDesktopReadonlyGuard({live:true,image_sha256:'a'.repeat(64),pong:first?null:'PONG exact',firstHandshake:first,version});
  const transport={write:async t=>calls.writes.push(t)};
  const pedal={onLine(){},cmd:async line=>[line+' ok']};
  guard.installApp(transport,pedal,{target:'tank-mini',image_sha256:'a'.repeat(64),
    capabilities:{read:true,write,panel:false},family_capabilities:families,command_capabilities:{}});
  return {ctx,port,guard,transport,pedal,calls,time:v=>clock=v};
}
async function main(){
  {const x=setup();await assert.rejects(x.ctx.navigator.serial.requestPort());checks++;assert.equal(x.calls.requests.length,0);checks++;}
  {const x=setup({pid:0x4155});x.guard.allowRequest();await assert.rejects(x.ctx.navigator.serial.requestPort());checks++;assert.equal(x.calls.opens.length,0);checks++;}
  for(const opts of [{write:true},{families:{'usb-cdc':['GAIN']}},{families:{'ble-nus':['GAIN']}}]){assert.throws(()=>setup(opts));checks++;}
  {
    const x=setup();x.guard.allowRequest();const port=await x.ctx.navigator.serial.requestPort();
    assert.equal(x.calls.requests[0].filters[0].usbVendorId,0x3654);checks++;
    assert.equal(x.calls.requests[0].filters[0].usbProductId,0x5155);checks++;
    await port.open({baudRate:115200});assert.equal(x.calls.opens.length,1);checks++;
    await assert.rejects(port.open({baudRate:115200}));checks++;
    await assert.rejects(x.ctx.navigator.serial.requestPort());checks++;
    await port.close();assert.equal(x.guard.state.closes,1);checks++;
  }
  {
    const x=setup({closeFail:true});x.guard.allowRequest();const p=await x.ctx.navigator.serial.requestPort();
    await p.open({baudRate:115200});await assert.rejects(p.close());checks++;
    assert.equal(x.guard.state.closes,0);checks++;assert.match(x.guard.state.closeError,/native close failure/);checks++;
  }
  {
    const x=setup();await x.transport.write('PING\n');x.pedal.onLine('PONG exact');
    for(const line of ['MEM','MODEL','FXT','FXS','PLIST','SNAPS','GAIN','LVL','AMPEQ info','EVT 1'])await x.transport.write(line+'\n');
    assert.equal(x.calls.writes.length,11);checks++;
    // A visible session may continue beyond the old1000-query short probe.
    for(let n=0;n<1100;n++)await x.transport.write('LVL\n');
    assert.equal(x.calls.writes.length,1111);checks++;
    x.time(90*60*1000);await assert.rejects(x.transport.write('LVL\n'));checks++;
    assert.equal(x.calls.writes.length,1111);checks++;
  }
  for(const line of ['GAIN 0 -1','PSAVE 0 Test','SNAPSAVE 0','PDEL 0','PLOAD 0','BLEKEY','LVLSUB 100','RESET','FSPRESS 0','TUNE',
                     'PING\nGSAVE','PING\r',' PING','PING ','EVT 0\0']){
    const x=setup();x.pedal.onLine('PONG exact');await assert.rejects(x.transport.write(line+'\n'));checks++;
    assert.equal(x.calls.writes.length,0);checks++;
  }
  {const x=setup();x.pedal.onLine('PONG wrong');await assert.rejects(x.transport.write('MEM\n'));checks++;assert.equal(x.calls.writes.length,0);checks++;}
  {
    const x=setup();x.pedal.onLine('PONG exact');x.guard.state.wire.length=50000;
    await assert.rejects(x.transport.write('LVL\n'));checks++;assert.equal(x.calls.writes.length,0);checks++;
  }
  {
    const x=setup({first:true});await assert.rejects(x.transport.write('MEM\n'));checks++;
    assert.equal(x.calls.writes.length,0);checks++;assert.equal(x.guard.state.pongMatched,false);checks++;
  }
  {
    const x=setup({first:true});await x.transport.write('PING\n');
    const actual='PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11';x.pedal.onLine(actual);
    await x.transport.write('MEM\n');assert.equal(x.guard.state.observedPong,actual);checks++;
    assert.deepEqual(x.calls.writes,['PING\n','MEM\n']);checks++;
  }
  for(const pong of ['PONG tankg_fw M5.71 rel ble Nov 12 2026','PONG tankm_fw M5.70 rel ble Nov 12 2026',
    'PONG tankm_fw M5.71 rel ble','PONG tankm_fw M5.71 rel ble Nov 12 2026\nGAIN 0 0']){
    const x=setup({first:true});x.pedal.onLine(pong);await assert.rejects(x.transport.write('MEM\n'));checks++;
    assert.equal(x.guard.state.pongMatched,false);checks++;
  }
  assert.throws(()=>setup({first:true,version:'tankg_fw M5.71 rel ble'}));checks++;
  console.log(JSON.stringify({result:'pass',checks,device_io:false,browser_started:false}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
