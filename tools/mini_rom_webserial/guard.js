'use strict';

// Standalone recovery session: two possible transmitted lines, each at most once.
// Native SerialPort and streams remain private. No editor or reconnect code runs.
function createMiniRomSession(config, serial, render = () => {}) {
  if (!config || config.execute !== true || !/^COM[1-9][0-9]{0,3}$/.test(config.com) ||
      !/^PONG tankm_fw M5\.71 rel ble Nov 12 2026 16:04:11(?: safe)?$/.test(config.pong)) {
    throw new Error('explicit execution and exact prior MINI identity required');
  }
  if (!serial || typeof serial.requestPort !== 'function') throw new Error('native WebSerial unavailable');
  const state = {schema:1, com:config.com, expectedPong:config.pong, requests:0, opens:0,
    closeAttempts:0, nativeCloseVerified:false, closed:false, identityVerified:false,
    pingAttempted:false, pingWriteCompleted:false, ubootAttempted:false, ubootWriteCompleted:false,
    actualACKObserved:false, disconnectObserved:false, disconnectedBeforeCommand:false,
    firmwareWrite:false, automaticRetry:false, ROMVerified:false, error:null,
    rxBytes:0, rx:[], tx:[], lines:[], events:[]};
  let port, writer, reader, readTask, pending = '', closing = false;
  const decoder = new TextDecoder('utf-8', {fatal:true});
  const encoder = new TextEncoder();
  const event = (name, extra={}) => {state.events.push({event:name, utc:new Date().toISOString(), ...extra}); render(state);};
  const fail = message => {state.error ||= String(message);event('failure',{message:String(message)});throw new Error(message);};
  const check = (value, message) => {if(!value) fail(message);};
  const hex = bytes => Array.from(bytes, x=>x.toString(16).padStart(2,'0')).join('');
  async function bounded(promise, timeout, label) {
    let timer;
    try {return await Promise.race([promise,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error(label+' timeout; no retry')),timeout);})]);}
    finally {clearTimeout(timer);}
  }
  function observe(bytes) {
    check(bytes instanceof Uint8Array,'non-byte RX');
    state.rxBytes += bytes.length;check(state.rxBytes <= 131072,'RX bound exceeded');
    state.rx.push({utc:new Date().toISOString(),hex:hex(bytes)});
    pending += decoder.decode(bytes,{stream:true});check(pending.length<=4096,'RX line bound exceeded');
    while(pending.includes('\n')) {
      const index=pending.indexOf('\n'), line=pending.slice(0,index).replace(/\r$/,'');pending=pending.slice(index+1);
      state.lines.push(line);check(state.lines.length<=256,'RX record bound exceeded');
      if(line.startsWith('PONG')) {
        check(state.pingAttempted && line===config.pong,'actual PONG differs from installed MINI proof');
        check(!state.ubootAttempted,'late PONG after UBOOT');
        state.identityVerified=true;event('actual_PONG',{line});
      }
      if(line==='OK UBOOT') {
        check(state.ubootAttempted,'unsolicited UBOOT ACK');
        state.actualACKObserved=true;event('actual_UBOOT_ACK',{line});
      }
      if(line.startsWith('ERR')) fail('target error: '+line);
    }
    render(state);
  }
  async function receive() {
    try {
      reader=port.readable.getReader();
      while(!closing) {
        const next=await reader.read();
        if(next.done){event('RX_stream_end');break;}
        if(next.value) observe(next.value);
      }
    } catch(error) {
      state.readError=String(error);event('RX_error',{message:String(error)});
      // A real USB reset can make a read reject. This never fabricates an ACK.
      if(!closing&&!state.ubootAttempted) state.error ||= String(error);
    } finally {
      try{reader?.releaseLock();}catch(error){state.readerReleaseError=String(error);}
      reader=undefined;
    }
  }
  async function transmit(line) {
    check(!closing&&!state.closed&&!state.error,'session stopped');
    check(writer&&state.opens===1,'native port not open');
    if(line==='PING\n') {
      check(!state.pingAttempted&&!state.ubootAttempted,'duplicate/out-of-order PING');
      state.pingAttempted=true;
    } else if(line==='UBOOT\n') {
      check(state.identityVerified&&state.pingWriteCompleted&&!state.ubootAttempted,'UBOOT requires fresh identity, completed PING, and no earlier attempt');
      state.ubootAttempted=true;
    } else fail('command is not PING/UBOOT');
    const bytes=encoder.encode(line), row={utc:new Date().toISOString(),hex:hex(bytes),line,completed:false};
    state.tx.push(row);event('TX_intent',{line});
    try {
      await bounded(writer.write(bytes),3000,'native write');
      row.completed=true;row.completed_utc=new Date().toISOString();
      if(line==='PING\n')state.pingWriteCompleted=true;else state.ubootWriteCompleted=true;
      event('TX_completed',{line});
    } catch(error) {state.writeError=String(error);state.error ||= String(error);event('TX_error',{line,message:String(error)});throw error;}
  }
  async function connect(trusted) {
    check(trusted===true,'trusted user activation required');
    check(state.requests===0&&!state.closed&&!closing,'only one chooser permitted');
    state.requests++;event('chooser_requested');
    try {
      port=await serial.requestPort({filters:[{usbVendorId:0x3654,usbProductId:0x5155}]});
      state.portInfo=port.getInfo();
      check(state.portInfo.usbVendorId===0x3654&&state.portInfo.usbProductId===0x5155,'selected device is not MINI candidate');
      check(state.opens===0,'only one native open permitted');
      state.opens++;event('native_open_intent');
      await bounded(port.open({baudRate:115200}),5000,'native open');
      event('native_open_completed');
      check(port.writable&&port.readable,'native serial streams unavailable');
      writer=port.writable.getWriter();readTask=receive();
      await transmit('PING\n');
      event('awaiting_actual_PONG');
    } catch(error) {state.error ||= String(error);event('connect_error',{message:String(error)});throw error;}
  }
  const disconnected = e => {
    if(!port || (e.target!==port&&e.port!==port))return;
    state.disconnectObserved=true;state.disconnectUTC=new Date().toISOString();
    state.disconnectedBeforeCommand=!state.ubootAttempted;
    if(!state.ubootAttempted)state.error ||= 'native disconnect before command';
    event('native_disconnect');
  };
  serial.addEventListener?.('disconnect',disconnected);
  async function close() {
    if(closing||state.closed)return state;
    closing=true;event('close_requested');
    try{if(reader)await bounded(reader.cancel(),2000,'reader cancel');}catch(error){state.cancelError=String(error);}
    try{if(readTask)await bounded(readTask,2000,'reader shutdown');}catch(error){state.readShutdownError=String(error);}
    try{writer?.releaseLock();writer=undefined;}catch(error){state.writerReleaseError=String(error);}
    if(port&&state.opens) {
      state.closeAttempts++;
      try{await bounded(port.close(),2000,'native close');state.nativeCloseVerified=true;event('native_close_completed');}
      catch(error){state.closeError=String(error);event('native_close_error',{message:String(error)});}
    }
    serial.removeEventListener?.('disconnect',disconnected);
    state.closed=true;event('session_stopped');return state;
  }
  // No arbitrary write API is exported. Parent journals before invoking enterROM.
  return Object.freeze({state,connect,enterROM:()=>transmit('UBOOT\n'),close});
}
if(typeof module!=='undefined')module.exports={createMiniRomSession};
