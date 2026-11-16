/* Temporary exact-request experiment on one already connected USB editor.
 * No chooser, port opening, preset save/delete or general family grant. */
function installMiniLatencyGuard(config) {
  'use strict';
  const canonical = x => Array.isArray(x) ? x.map(canonical) : x && typeof x==='object' ?
    Object.fromEntries(Object.keys(x).sort().map(k=>[k,canonical(x[k])])) : x;
  const eq = (a,b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
  const clone = x => JSON.parse(JSON.stringify(x));
  const hex = b => Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
  const state = {kind:'mini-latency-exact-runtime-v1',seq:0,installed:false,detached:false,
    healthy:true,fatal:null,phase:'observing',epoch:0,hookReads:0,primed:false,pong:false,
    commands:[],wire:[],rx:[],events:[],observations:{},rxBytes:0,mutations:0,
    step:0,substep:0,created:[],restoreIssued:false,started:performance.now()};
  const event = (kind,data={}) => state.events.push({kind,seq:++state.seq,time:performance.now(),...data});
  const fail = message => {state.healthy=false;state.fatal=state.fatal||String(message);event('fatal',{message:String(message)});throw Error(message);};
  if (window.__miniLatencyGuard || DEMO || !S.connected || Pedal.tr !== SerialTransport ||
      !SerialTransport.isOpen() || !SerialTransport.reader || !SerialTransport.writer ||
      !eq(HyperRigMini.profile,config.profile) || S.fw !== config.pong ||
      !eq(SerialTransport.info(),{vid:0x3654,pid:0x5155})) throw Error('One matching real connected editor required');
  const tr=SerialTransport, pedal=Pedal, reader=tr.reader, writer=tr.writer;
  const old={policy:HyperRigMini,read:reader.read,write:writer.write,cmd:pedal.cmd,
    transportWrite:tr.write,open:tr.open,bodyInert:document.body.inert};
  const writeDone=new Map();
  let issued=null,plan=null,currentWire=null,currentCommand=null;
  const reads=new Set(('PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST '+
    'LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE LIFE CRASH CLKSTATE GAIN BPM PCOLOR').split(' '));
  const readonly = line => reads.has(line) || line==='AMPEQ info' || /^EVT [0-9]{1,10}$/.test(line);
  const nativeLines = (low,high) => {
    const chunks=state.rx.filter(x=>low<x.seq && x.seq<high).map(x=>x.hex);
    const bytes=new Uint8Array(chunks.reduce((n,x)=>n+x.length/2,0));let at=0;
    for(const s of chunks)for(let i=0;i<s.length;i+=2)bytes[at++]=parseInt(s.slice(i,i+2),16);
    return new TextDecoder('utf-8',{fatal:true}).decode(bytes).replace(/\r\n/g,'\n').split('\n');
  };
  const contained = (need,got) => {let cursor=0;for(const line of need){const n=got.indexOf(line,cursor);if(n<0)return false;cursor=n+1;}return true;};
  const expected = () => {
    if(!plan)return null;
    if(state.phase==='attenuate')return plan.setup_requests[0];
    if(state.phase==='add')return plan.steps[state.step]?.add_request;
    if(state.phase==='configure')return plan.steps[state.step].configure_after_actual_id[state.substep]
      .request_template.replace('{id}',String(state.created.at(-1).id));
    if(state.phase==='restoring')return 'PLOAD 0';
    return null;
  };
  const permitted = line => state.healthy && issued?.line===line && !issued.used && expected()===line;
  const checkActive = () => {
    if(state.detached || !state.healthy || performance.now()-state.started>10*60*1000 ||
        !S.connected || tr.reader!==reader || tr.writer!==writer || !tr.isOpen())return fail('Trial connection or finite lifetime ended');
  };
  document.body.inert=true;
  tr.open=async()=>fail('Trial cannot open or reconnect a port');
  reader.read=async function(...args){
    state.hookReads++;
    const value=await old.read.apply(this,args);
    if(!state.detached && value.value){
      state.rxBytes+=value.value.byteLength;
      if(state.rxBytes>2*1024*1024)return fail('Raw RX limit exceeded');
      state.rx.push({seq:++state.seq,time:performance.now(),hex:hex(value.value)});
    }
    if(!state.detached && value.done)state.healthy=false;
    return value;
  };
  globalThis.HyperRigMini=Object.freeze({...old.policy,commandPolicy(line,transport,...args){
    if(transport==='usb-cdc' && permitted(line))return {allowed:true,capability:'exact-latency-experiment'};
    return old.policy.commandPolicy(line,transport,...args);
  }});
  tr.write=async function(text){
    checkActive();
    if(typeof text!=='string' || !/^[\x20-\x7e]{1,31}\n$/.test(text))return fail('Bounded canonical USB text required');
    const line=text.slice(0,-1);
    if(line!==line.trim() || (!readonly(line) && !permitted(line)))return fail('Unplanned write');
    const command=state.commands.find(x=>x.line===line && !x.completed && x.wire_id==null);
    if(!command)return fail('Write bypassed original command queue');
    if(!readonly(line))issued.used=true; // Consume before the native write; never repeat an uncertain request.
    currentCommand=command;
    try{return await old.transportWrite.call(this,text);}finally{currentCommand=null;currentWire=null;}
  };
  writer.write=async function(bytes){
    if(!currentCommand || !(bytes instanceof Uint8Array) || state.wire.length>=2000)return fail('Unplanned native writer call');
    const line=currentCommand.line;
    if(hex(bytes)!==hex(new TextEncoder().encode(line+'\n')))return fail('Native TX bytes differ');
    const item={id:state.wire.length,command_id:currentCommand.id,line,hex:hex(bytes),
      seq:++state.seq,time:performance.now(),completed:false,mutation:!readonly(line)};
    currentCommand.wire_id=item.id;currentWire=item;state.wire.push(item);
    let settle;writeDone.set(item.id,new Promise(resolve=>{settle=resolve;}));
    try{const result=await old.write.call(this,bytes);item.completed=true;settle(true);return result;}
    catch(error){settle(false);return fail('Native write failed: '+String(error));}
  };
  pedal.cmd=async function(line,...args){
    checkActive();
    if(!readonly(line) && !permitted(line))return fail('No exact armed command');
    const item={id:state.commands.length,line,epoch:state.epoch,wire_id:null,completed:false,
      priming:!state.primed,seq:++state.seq};state.commands.push(item);
    if(state.commands.length>2000)return fail('Command limit exceeded');
    let reply;
    try{reply=await old.cmd.call(this,line,...args);}catch(error){return fail('Command failed: '+String(error));}
    item.lines=reply;
    if(!Array.isArray(reply) || !reply.length || item.wire_id==null ||
       reply.some(x=>typeof x!=='string'))return fail('Real completed command required');
    if(!state.wire[item.wire_id].completed){
      let timer;const okay=await Promise.race([writeDone.get(item.wire_id),
        new Promise(resolve=>{timer=setTimeout(()=>resolve(false),4000);})]);clearTimeout(timer);
      if(!okay)return fail('Native write did not complete after its reply; no retry');
    }
    item.completed=true;item.completed_seq=++state.seq;
    item.native_RX_verified=item.priming ? false : contained(reply,nativeLines(state.wire[item.wire_id].seq,item.completed_seq));
    if(!item.priming && !item.native_RX_verified)return fail('Reply absent from native RX; no retry');
    if(line==='PING'){
      if(!eq(reply,[config.pong]))return fail('Exact normal PONG differs');
      if(!item.priming)state.pong=true;
    }
    if(readonly(line)){
      if(reply.some(x=>/^ERR\b/.test(x)))return fail('Read query failed');
      state.observations[line]={epoch:state.epoch,lines:clone(reply),command_id:item.id};
    }
    return reply;
  };
  state.installed=true;event('installed',{profile_unchanged:eq(HyperRigMini.profile,config.profile)});
  const guard={state,readonly,
    async prime(){
      if(state.phase!=='observing' || state.primed)return fail('Exactly one reader-hook priming query');
      state.phase='priming';await pedal.cmd('PING','PONG',3000);
      if(!state.hookReads)return fail('Reader hook not reached after priming');
      state.primed=true;state.phase='observing';event('reader_hook_primed');
      return true;
    },
    configure(value){
      checkActive();
      if(!state.primed || !state.pong || plan || state.phase!=='observing' ||
         value?.kind!=='mini-exact-FX-stress-plan-v1' || value.executed!==false ||
         value.restore_request!=='PLOAD 0' || !Array.isArray(value.steps) || !value.steps.length || value.steps.length>16 ||
         value.setup_requests.length>1)return fail('One finite derived plan required');
      const gain=state.observations.GAIN?.lines;
      const gm=gain?.length===1 && /^GAIN in=(-?\d+) out=(-?\d+) dB$/.exec(gain[0]);
      if(!gm || !eq(value.baseline_gain,[+gm[1],+gm[2]]) ||
         !eq(value.trial_gain,[+gm[1],Math.min(+gm[2],-12)]) ||
         !eq(value.setup_requests,+gm[2]<=-12?[]:['GAIN '+gm[1]+' -12']))return fail('Plan gain differs from fresh state');
      const fxt=state.observations.FXT?.lines || [],count={P:0,Q:0};
      for(const s of value.steps){
        if(!['P','Q'].includes(s.bank) || ++count[s.bank]>10 ||
           s.add_request!=='FXA '+s.bank+' 99 '+s.type || !/^[a-z0-9_]+$/.test(s.type))return fail('Invalid exact FXA');
        const index=fxt.findIndex(x=>new RegExp('^FXT \\d+ '+s.type+' cost=').test(x));
        if(index<0)return fail('Planned type absent from actual FXT');
        const details=[];for(let i=index+1;i<fxt.length && !/^FXT \d+ \w+ cost=/.test(fxt[i]);i++)details.push(fxt[i]);
        const c=s.configure_after_actual_id;
        if(!Array.isArray(c) || c.length<2 || c.length>9 || c[0].request_template!=='FXE {id} 0' ||
           c.at(-1).request_template!=='FXE {id} 1')return fail('Finite disable/configure/enable required');
        for(const p of c.slice(1,-1)){
          const m=/^FXP \{id\} ([0-6]) (-?\d+)$/.exec(p.request_template);
          const rule=m && details.map(x=>/^FXT\s+(\d+) (\w+) (-?\d+)\.\.(-?\d+) \((-?\d+)\)$/.exec(x)).find(x=>x && x[1]===m[1]);
          if(!rule || +m[2]<+rule[3] || +m[2]>+rule[4] || +m[2]>+rule[5])return fail('FXP differs from actual conservative range');
        }
      }
      plan=clone(value);event('plan',{plan:clone(plan)});state.phase=plan.setup_requests.length?'attenuate':'add';
    },
    expected,
    async executeNext(){
      checkActive();const line=expected();if(!line || issued)return fail('No single pending mutation');
      issued={line,used:false};event('mutation_intent',{line});
      try{
        const end=line.startsWith('FXA ')?x=>/^FX cpu=|^ERR\b/.test(x):line.split(' ')[0];
        const reply=await pedal.cmd(line,end,line.startsWith('PLOAD ')?8000:4000);
        state.mutations++;state.epoch++;
        if(reply.some(x=>/^ERR (FXA|FXP|FXE)\b/.test(x))){state.phase='rejected';event('protocol_rejection',{line,reply});return {line,reply,rejected:true};}
        let okay=false;
        if(state.phase==='attenuate'){
          okay=eq(reply,['GAIN in='+plan.trial_gain[0]+' out='+plan.trial_gain[1]+' dB']);state.phase='add';
        }else if(state.phase==='add'){
          const heads=reply.map(x=>new RegExp('^FXA id=(\\d+) '+plan.steps[state.step].type+'$').exec(x)).filter(Boolean);
          okay=heads.length===1 && +heads[0][1]<16 && !state.created.some(x=>x.id===+heads[0][1]) && /^FX cpu=\d+\/\d+ ticks \(\d+%\) mem_fx=\d+ B$/.test(reply.at(-1));
          if(okay){state.created.push({id:+heads[0][1],type:plan.steps[state.step].type,bank:plan.steps[state.step].bank});state.substep=0;state.phase='configure';}
        }else if(state.phase==='configure'){
          okay=line.startsWith('FXE ')?eq(reply,['FXE ok']):eq(reply,['FXP ok '+line.split(' ')[3]]);
          state.substep++;if(state.substep===plan.steps[state.step].configure_after_actual_id.length)state.phase='between';
        }else if(state.phase==='restoring'){
          okay=reply.length===1 && reply[0].startsWith(config.restore_ack_prefix) &&
            /^ missing=0 capture=0 ir=-1 ms=\d+$/.test(reply[0].slice(config.restore_ack_prefix.length));
          state.phase='restored_ack';
        }
        if(!okay)return fail('Actual mutation ACK differs; no retry');
        event('mutation_ack',{line,reply,epoch:state.epoch});return {line,reply,rejected:false};
      }finally{issued=null;}
    },
    advance(){
      checkActive();if(state.phase!=='between' || state.observations.FXS?.epoch!==state.epoch ||
        state.observations.MEM?.epoch!==state.epoch)return fail('Fresh FX/memory readback before next addition');
      state.step++;state.phase=state.step<plan.steps.length?'add':'stress_done';return state.phase;
    },
    restore(){
      checkActive();if(!plan || state.restoreIssued || issued)return fail('At most one healthy-connection restoration');
      state.restoreIssued=true;state.phase='restoring';event('restore_intent');
    },
    async detach(restored){
      await pedal.chain;
      if(state.detached)return fail('Already detached');
      if(restored && (!state.healthy || state.phase!=='restored_ack' || !eq(HyperRigMini.profile,config.profile)))return fail('Restored ACK/profile required');
      // On uncertain failure keep the exact wrapper blocked and the UI inert.
      const unchanged=state.healthy && !state.wire.some(x=>x.mutation);
      if(!restored && !unchanged){state.healthy=false;event('left_blocked_for_diagnosis');return clone(state);}
      reader.read=old.read;writer.write=old.write;tr.write=old.transportWrite;tr.open=old.open;
      pedal.cmd=old.cmd;globalThis.HyperRigMini=old.policy;document.body.inert=old.bodyInert;
      state.detached=true;event('detached',{profile_unchanged:eq(HyperRigMini.profile,config.profile)});return clone(state);
    }
  };
  Object.defineProperty(window,'__miniLatencyGuard',{value:guard});return clone(state);
}
