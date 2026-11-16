"""Offline original-method tests; fake timers and ports, no browser/device."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert').strict,crypto=require('crypto');
const input=JSON.parse(fs.readFileSync(0,'utf8')),html=fs.readFileSync(input.html,'utf8').replace(/\r\n/g,'\n');
const start=html.indexOf('async open(known) {');
const original=html.slice(start,html.indexOf('\n  },',start)+4);
const helper=fs.readFileSync(input.helper,'utf8'),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const flush=async()=>{for(let n=0;n<12;n++)await Promise.resolve();};
function setup(){let now=0,id=0;const timers=new Map(),calls={open:0,close:0,read:0};
 const ctx={setTimeout:(fn,ms)=>{timers.set(++id,{fn,at:now+ms});return id;},clearTimeout:n=>timers.delete(n)};
 vm.createContext(ctx);vm.runInContext(helper,ctx);
 const transport=vm.runInContext('({port:null,'+original+'})',ctx);
 transport.readLoop=()=>calls.read++;
 const advance=async time=>{now=time;for(const [key,t] of [...timers])if(t.at<=time){timers.delete(key);t.fn();}await flush();};
 const port=delay=>({open:options=>{assert.equal(options.baudRate,115200);calls.open++;
   return new Promise(resolve=>ctx.setTimeout(resolve,delay));},close:async()=>{calls.close++;},writable:{getWriter:()=>({})}});
 return {ctx,transport,calls,advance,port};}
(async()=>{
 const slow=setup(),read=slow.transport.readLoop;
 const metadata=slow.ctx.installMiniSerialOpenTimeout(slow.transport);
 assert.equal(slow.calls.open,0);assert.equal(slow.transport.readLoop,read);
 assert.equal(metadata.original_source_sha256,hash(original));
 assert.equal(metadata.extended_source_sha256,hash(slow.transport.open.toString()));
 assert.equal(slow.transport.open.toString(),original.replace(')), 5000); })]);',')), 30000); })]);'));
 let result='pending';const job=slow.transport.open(slow.port(18000)).then(()=>result='open',()=>result='error');
 await flush();await slow.advance(5000);assert.equal(result,'pending');assert.equal(slow.calls.close,0);
 await slow.advance(18000);await job;assert.equal(result,'open');assert.deepEqual(slow.calls,{open:1,close:0,read:1});
 const timeout=setup();timeout.ctx.installMiniSerialOpenTimeout(timeout.transport);
 let error;const overdue=timeout.transport.open(timeout.port(40000)).catch(e=>error=e);
 await flush();await timeout.advance(30000);await overdue;
 assert(error.message.includes('did not respond'));assert.deepEqual(timeout.calls,{open:1,close:1,read:0});
 assert.equal(timeout.transport.port,null);
 const altered=setup();altered.transport.open=async function open(){};
 assert.throws(()=>altered.ctx.installMiniSerialOpenTimeout(altered.transport),/source differs/);
 const active=setup();active.transport.port={};assert.throws(()=>active.ctx.installMiniSerialOpenTimeout(active.transport),/unopened/);
 assert.throws(()=>slow.ctx.installMiniSerialOpenTimeout(slow.transport),/unopened/);
 console.log(JSON.stringify({slow_pass:true,timeout_pass:true,source_rejection:true,metadata}));
})().catch(error=>{console.error(error);process.exitCode=1;});
"""


class SerialOpenExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node=shutil.which('node')
        if not node:raise unittest.SkipTest('existing Node unavailable; no installation')
        result=subprocess.run([node,'-e',SCRIPT],input=json.dumps({
            'html':str(ROOT/'build/hyperrig-mini-ui-v2/app/web/tankmini.html'),
            'helper':str(ROOT/'tools/mini_browser_serial_open.js')}),
            text=True,capture_output=True,check=True)
        cls.result=json.loads(result.stdout)

    def test_original_native_open_at_18_seconds_succeeds_without_close_or_replay(self):
        self.assertTrue(self.result['slow_pass'])
        self.assertEqual(self.result['metadata']['timeout_ms'],30000)

    def test_30_second_timeout_keeps_original_single_open_cleanup_and_exact_source_gate(self):
        self.assertTrue(self.result['timeout_pass'] and self.result['source_rejection'])
        self.assertFalse(self.result['metadata']['reconnect_added'])


if __name__=='__main__':unittest.main()
