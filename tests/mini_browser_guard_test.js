'use strict';
const fs = require('fs'), vm = require('vm'), assert = require('assert').strict;
const source = fs.readFileSync(process.argv[2], 'utf8');
let checks = 0;
function setup({live=true, pid=0x5155}={}) {
  const calls = {requests:[], opens:[], writes:[], received:[]};
  const port = {getInfo:()=>({usbVendorId:0x3654,usbProductId:pid}),
    open:async opts=>calls.opens.push(opts)};
  const ctx = {navigator:{serial:{requestPort:async opts=>{calls.requests.push(opts);return port;}}},
    performance:{now:()=>123},DOMException,localStorage:{setItem(){}}};
  vm.createContext(ctx);
  vm.runInContext(source,ctx);
  const guard=ctx.installMiniBrowserReadonlyGuard({live,image_sha256:'a'.repeat(64),pong:'PONG exact'});
  const transport={write:async text=>calls.writes.push(text)};
  const pedal={onLine:line=>calls.received.push(line),cmd:async line=>[line+' ok']};
  guard.installApp(transport,pedal,{target:'tank-mini',image_sha256:'a'.repeat(64),capabilities:{read:true}});
  return {ctx,calls,port,guard,transport,pedal};
}
async function test() {
  {
    const {ctx,calls}=setup({live:false});
    await assert.rejects(ctx.navigator.serial.requestPort()); checks++;
    assert.equal(calls.requests.length,0); checks++;
    assert.deepEqual(Array.from(await ctx.navigator.serial.getPorts()),[]); checks++;
  }
  {
    const {ctx,calls}=setup();
    await assert.rejects(ctx.navigator.serial.requestPort()); checks++;
    assert.equal(calls.requests.length,0); checks++;
  }
  {
    const {ctx,calls,guard}=setup();
    guard.allowRequest();const port=await ctx.navigator.serial.requestPort({filters:[]});
    assert.equal(calls.requests[0].filters[0].usbVendorId,0x3654); checks++;
    assert.equal(calls.requests[0].filters[0].usbProductId,0x5155); checks++;
    await port.open({baudRate:115200});assert.equal(calls.opens.length,1); checks++;
    await assert.rejects(port.open({baudRate:115200})); checks++;
    await assert.rejects(ctx.navigator.serial.requestPort()); checks++;
  }
  {
    const {ctx,calls,guard}=setup({pid:0x4155});guard.allowRequest();
    await assert.rejects(ctx.navigator.serial.requestPort()); checks++;
    assert.equal(calls.opens.length,0); checks++;
  }
  {
    const {transport,pedal,calls,guard}=setup();
    await transport.write('PING\n');assert.deepEqual(calls.writes,['PING\n']); checks++;
    pedal.onLine('PONG exact');assert.equal(guard.state.pongMatched,true); checks++;
    for(const line of ['STAT','MEM','FXS','PLIST','SNAPS','AMPEQ info','EVT 42']) await transport.write(line+'\n');
    assert.equal(calls.writes.length,8); checks++;
  }
  {
    const {transport,calls}=setup();
    await assert.rejects(transport.write('MEM\n')); checks++;
    assert.equal(calls.writes.length,0); checks++;
  }
  {
    const {transport,pedal,calls,guard}=setup();pedal.onLine('PONG different');
    await assert.rejects(transport.write('PING\n')); checks++;
    assert.equal(guard.state.pongMatched,false); checks++;
    assert.equal(calls.writes.length,0); checks++;
  }
  for(const text of ['PSAVE 0\n','PLOAD 0\n','FXP 0 0 1\n','GSAVE\n','BLEKEY\n',
                     'PING\nGSAVE\n','PING\r\n',' PING\n','PING \n','EVT 1\0\n','TUNE\n']) {
    const {transport,pedal,calls}=setup();pedal.onLine('PONG exact');
    await assert.rejects(transport.write(text)); checks++;
    assert.equal(calls.writes.length,0); checks++;
  }
  {
    const {transport,calls}=setup();
    for(let n=0;n<5;n++)await transport.write('PING\n');
    await assert.rejects(transport.write('PING\n')); checks++;
    assert.equal(calls.writes.length,5); checks++;
  }
  {
    const {guard,transport,pedal,calls}=setup();pedal.onLine('PONG exact');guard.stop();
    await assert.rejects(transport.write('MEM\n')); checks++;
    assert.equal(calls.writes.length,0); checks++;
  }
  {
    const {guard,pedal,transport}=setup();
    assert.throws(()=>guard.installApp(transport,pedal,{target:'tank-mini',image_sha256:'a'.repeat(64),capabilities:{read:true}})); checks++;
  }
  console.log(JSON.stringify({result:'pass',checks,device_io:false,fake_serial_only:true}));
}
test().catch(error=>{console.error(error);process.exitCode=1;});
