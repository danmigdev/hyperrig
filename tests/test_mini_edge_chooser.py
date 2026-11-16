"""No browser/device use: fake native WebSerial and offline entrypoints only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('edge_probe',ROOT/'analysis/hardware/probe_mini_edge_chooser.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class EdgeChooserTests(unittest.TestCase):
    def test_default_and_check_only_never_create_browser_or_server(self):
        for args in ([],['--check-only']):
            with (patch.object(probe,'run',side_effect=AssertionError('run')),
                 patch.object(probe,'edge_path',return_value=Path('FAKE/msedge.exe')),
                 contextlib.redirect_stdout(io.StringIO()) as stream):
                self.assertEqual(probe.main(args),0)
            result=json.loads(stream.getvalue())
            self.assertFalse(result['browser_started'] or result['device_io'] or result['serial_open_permitted'])

    def test_source_has_no_serial_open_call_or_transmit_api(self):
        self.assertNotIn('.open(',probe.SCRIPT)
        for method in ('getWriter','write(','send(','setSignals'):
            self.assertNotIn(method,probe.SCRIPT)
        self.assertIn("Object.defineProperty(SerialPort.prototype,'open'",probe.SCRIPT)

    def test_fake_native_request_once_metadata_only_and_open_is_blocked(self):
        node=shutil.which('node')
        if not node:self.skipTest('existing Node unavailable')
        js=r"""
const vm=require('vm'),assert=require('assert');
const source=JSON.parse(require('fs').readFileSync(0,'utf8'));
(async()=>{
 for(const reject of [false,true]){
  let nativeOpen=0,requests=0,listener,observed;
  class FakePort{async open(){nativeOpen++;}getInfo(){return {usbVendorId:0x3654,usbProductId:0x5155};}}
  const button={disabled:false,addEventListener:(_,fn)=>{listener=fn;}};
  const ctx={window:{},isSecureContext:true,SerialPort:FakePort,DOMException,
   navigator:{serial:{requestPort:async options=>{requests++;observed=options;
    if(reject)throw new DOMException('cancelled','NotFoundError');return new FakePort();}}},
   document:{getElementById:id=>id==='choose'?button:{textContent:''}}};
  vm.runInNewContext(source,ctx);const state=ctx.window.__edgeChooserProbe;
  await listener({isTrusted:false});assert.equal(requests,0);
  await listener({isTrusted:true});await listener({isTrusted:true});
  assert.equal(requests,1);assert.equal(nativeOpen,0);assert.equal(state.bytes_transmitted,0);
  assert.equal(JSON.stringify(observed),JSON.stringify({filters:[{usbVendorId:0x3654,usbProductId:0x5155}]}));
  assert.equal(state.phase,reject?'request_rejected':'metadata_returned');
  if(!reject)assert.equal(state.info.vid,0x3654);
  await assert.rejects(()=>new FakePort().open(),/forbidden/);
  assert.equal(nativeOpen,0);assert.equal(state.open_attempts_blocked,1);
 }
 process.stdout.write('PASS fake request/cancel/open prevention');
})().catch(e=>{console.error(e);process.exit(1);});
"""
        result=subprocess.run([node,'-e',js],input=json.dumps(probe.SCRIPT),text=True,
                              capture_output=True,timeout=10,check=True)
        self.assertIn('PASS',result.stdout)


if __name__=='__main__':unittest.main()
