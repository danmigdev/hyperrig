"""Offline tests for the full-editor MINI profile; no port or device is opened."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from tools.build_mini_app import (ROOT, SOURCE, SOURCE_SHA, build, call_sites, checked,
                                  derive_html, descriptor_evidence, load_profile)


def node(code, value):
    run = subprocess.run(["node", "-e", code], input=json.dumps(value), text=True,
                         capture_output=True, encoding="utf-8", check=True, cwd=ROOT)
    return json.loads(run.stdout)


JS_POLICY = r"""
const fs = require('fs'), vm = require('vm');
const v = JSON.parse(fs.readFileSync(0, 'utf8'));
const context = vm.createContext({HYPERRIG_MINI_BUILD:v.profile});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),context);
const mini = context.HyperRigMini;
let results = [];
for (const action of v.actions) {
  if (action.pong !== undefined) results.push(mini.acceptPong(action.pong));
  else if (action.reset) { mini.resetIdentity(); results.push(null); }
  else results.push(mini.commandPolicy(action.command));
}
process.stdout.write(JSON.stringify(results));
"""


class MiniAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = checked(SOURCE / "web/tankg.html", SOURCE_SHA).decode("utf-8")
        cls.base = load_profile()
        cls.html, cls.patches = derive_html(cls.source, cls.base)

    def read_profile(self):
        p = copy.deepcopy(self.base)
        p.update(firmware_version="tankm_fw M5.71 rel ble", image_sha256="a" * 64)
        p["capabilities"]["read"] = True
        return p

    def policy(self, actions, profile=None):
        return node(JS_POLICY, {"profile": profile or self.base, "actions": actions})

    def test_default_allows_only_identity_and_never_claims_a_port(self):
        actions = [{"command": s} for s in ("PING", "FXT", "PSAVE 0 name", "GSAVE", "FSDO a", "PING\nPSAVE 0 x")]
        self.assertEqual([r["allowed"] for r in self.policy(actions)], [True, False, False, False, False, False])
        answer = self.policy([{"pong": "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"}])[0]
        self.assertFalse(answer["ok"])
        self.assertIn("no matching firmware build", answer["reason"])

    def test_stock_g_b_wrong_version_and_unstructured_identity_rejected(self):
        wrong = ["TANK MINI_009", "PONG tankg_fw M5.71 rel ble Nov 12 2026 16:05:32",
                 "PONG tankb_fw M5.71 rel ble Nov 12 2026 16:05:32",
                 "PONG tankm_fw M5.71 rel ble tankb Nov 12 2026 16:05:32",
                 "PONG tankm_fw M5.70 rel ble Nov 12 2026 16:05:32", "PONG tankm_fw"]
        self.assertTrue(all(not r["ok"] for r in self.policy([{"pong": p} for p in wrong], self.read_profile())))

    def test_read_capability_requires_matching_identity_and_resets(self):
        result = self.policy([{"command": "FXT"}, {"pong": "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"},
                              {"command": "FXT"}, {"command": "AMPEQ info"}, {"command": "EVT 0"},
                              {"command": "FXP 1 0 50"}, {"command": "LVLSUB 100 2"},
                              {"reset": True}, {"command": "FXT"}], self.read_profile())
        self.assertTrue(result[1]["ok"])
        self.assertEqual([result[i]["allowed"] for i in [0,2,3,4,5,6,8]], [False,True,True,True,False,False,False])

    def test_mutation_and_panel_capabilities_are_distinct(self):
        p = self.read_profile(); p["capabilities"]["write"] = True
        start = {"pong": "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"}
        self.assertFalse(self.policy([start, {"command": "PSAVE 0 example"}], p)[1]["allowed"])
        p.update(hardware_verified=True, write_validation={"path": "fixture", "sha256": "b" * 64})
        commands = ["FXP 1 0 50", "SNAPSAVE 0", "LDBEGIN 4892", "PSAVE 0 example", "FSDO a", "FSA 0", "LEDCFG mode=1"]
        result = self.policy([start] + [{"command": c} for c in commands], p)
        self.assertEqual([r["allowed"] for r in result[1:]], [True,True,True,True,False,False,False])

    def test_full_editor_and_converter_features_are_retained(self):
        for name in ["parseFxs", "loadChain", "loadPreset", "loadSnaps", "readPlist", "sendChunks", "pioSim"]:
            self.assertIn(name, self.html)
        for command in ["LDBEGIN", "LDEND", "IRBEGIN", "IREND", "SNAPSAVE", "PSAVE", "FXT"]:
            self.assertIn(command, self.html)
        self.assertIn('const SLOT = i => "ABCD"[i % 4]', self.html)
        self.assertIn('const DEMO = location.hash === "#demo"', self.html)
        self.assertNotIn("0000ae40", self.html)
        self.assertNotIn("readRequest(\"presets\"", self.html)
        self.assertIn('new BroadcastChannel("hyperrig-mini-port")', self.html)

    def test_profile_gate_precedes_connected_state_and_first_query(self):
        connect = self.html[self.html.index("async function connect(known"):]
        self.assertLess(connect.index("HyperRigMini.acceptPong"), connect.index("S.connected = true"))
        self.assertLess(connect.index("HyperRigMini.acceptPong"), connect.index("await loadTypes()"))
        queue = self.html[self.html.index("  cmd(line, until"):]
        self.assertLess(queue.index("HyperRigMini.commandPolicy"), queue.index("gdSent(line)"))
        self.assertLess(queue.index("HyperRigMini.commandPolicy"), queue.index('this.tr.write(line + "\\n")'))

    def test_original_pedal_queue_sends_only_permitted_lines(self):
        code = r"""
const fs=require('fs'),vm=require('vm');
const input=JSON.parse(fs.readFileSync(0,'utf8')), wires=[];
let context;
const transport={isOpen:()=>true,write:text=>{
  wires.push(text);
  queueMicrotask(()=>context.Pedal.onLine(text==='PING\n'?'PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32':'FXT end'));
  return Promise.resolve();
}};
context=vm.createContext({HYPERRIG_MINI_BUILD:input.profile,DEMO:false,S:{},
 pickTransport:()=>transport,Log:{ev:()=>{},cmd:()=>{}},
 gdSent:()=>null,gdDone:()=>{},strayLines:()=>[],setAlert:()=>{},blePairLine:()=>false,
 noAnswer:()=>{},performance,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),context);
let start=input.html.indexOf('const Pedal = {'),end=input.html.indexOf('/* ============================================================ estado',start);
if(start<0||end<0) throw Error('original queue anchors absent');
vm.runInContext(input.html.slice(start,end)+'\nglobalThis.Pedal=Pedal;',context);
(async()=>{
 const blockedBefore=await context.Pedal.cmd('FXT','FXT');
 const ping=await context.Pedal.cmd('PING','PONG');
 const accepted=context.HyperRigMini.acceptPong(ping[0]);
 const types=await context.Pedal.cmd('FXT','FXT end');
 const blockedWrite=await context.Pedal.cmd('PSAVE 0 example','PSAVE');
 const blockedPanel=await context.Pedal.cmd('FSDO a','FSMODE');
 context.HyperRigMini.resetIdentity();
 const blockedAfter=await context.Pedal.cmd('FXT','FXT');
 process.stdout.write(JSON.stringify({wires,accepted,types,blockedBefore,blockedWrite,blockedPanel,blockedAfter}));
})().catch(e=>{process.stderr.write(String(e));process.exitCode=1});
"""
        result = node(code, {"html": self.html, "profile": self.read_profile()})
        self.assertTrue(result["accepted"]["ok"])
        self.assertEqual(result["wires"], ["PING\n", "FXT\n"])
        self.assertEqual(result["types"], ["FXT end"])
        for key in ["blockedBefore", "blockedWrite", "blockedPanel", "blockedAfter"]:
            self.assertTrue(result[key][0].startswith("ERR MINI_APP "))

    def test_patched_and_original_javascript_parse(self):
        scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", self.html, flags=re.S)
        code = "const vm=require('vm'),fs=require('fs');const scripts=JSON.parse(fs.readFileSync(0,'utf8'));scripts.forEach((s,i)=>new vm.Script(s,{filename:'inline-'+i}));process.stdout.write(JSON.stringify(scripts.length));"
        self.assertGreaterEqual(node(code, scripts), 5)
        for p in (ROOT / "app/mini").glob("*.js"):
            subprocess.run(["node", "--check", str(p)], check=True, capture_output=True)

    def test_source_drift_does_not_silently_patch_another_ui(self):
        with self.assertRaisesRegex(ValueError, "source anchor"):
            derive_html(self.source.replace('const PEDAL_NAME =', 'const RENAMED_PEDAL ='), self.base)

    def test_usb_runtime_pid_patch_and_nus_are_real_binary_evidence(self):
        e = descriptor_evidence()
        self.assertEqual(e["usb"]["runtime_pid"], "5155")
        self.assertEqual(e["usb"]["pid_patch_hex"], "5131894b")
        self.assertEqual(e["usb"]["data_interface"]["packet_bytes"], 64)
        self.assertEqual(len(e["nus_uuid_addresses"]), 4)
        self.assertFalse(e["hardware_enumeration_verified_on_mini"])

    def test_inventory_retains_response_predicates_and_dynamic_requests(self):
        calls = call_sites(self.source)
        self.assertEqual(len(calls), 168)
        ping = next(c for c in calls if c["command"] == "PING")
        self.assertEqual(ping["completion_expression"], '"PONG"')
        types = next(c for c in calls if c["command"] == "FXT")
        self.assertIn("FXT", types["completion_expression"])
        self.assertTrue(any(c["command"] is None and "prefix" in c["request_expression"] for c in calls))

    def test_build_preserves_attributions_and_emits_no_firmware_or_private_bank(self):
        with tempfile.TemporaryDirectory(prefix="mini-app-test-", dir=ROOT / "build") as temp:
            dest = Path(temp).resolve()
            self.assertTrue(dest.is_relative_to((ROOT / "build").resolve()))
            result = build(dest)
            for name in ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md"):
                self.assertEqual((dest / name).read_bytes(), (SOURCE / name).read_bytes())
            self.assertFalse(list(dest.rglob("*.bin")))
            self.assertFalse(result["stock_mini_protocol_adapter"])
            self.assertFalse(result["profile"]["capabilities"]["write"])

    def test_read_manifest_needs_matching_artifact_not_hardware_validation(self):
        with tempfile.TemporaryDirectory(prefix="mini-app-manifest-", dir=ROOT / "build") as temp:
            dest = Path(temp).resolve(); self.assertTrue(dest.is_relative_to((ROOT / "build").resolve()))
            image = dest / "offline-fixture.bin"; image.write_bytes(b"offline fixture, not firmware")
            spec = {"target":"tank-mini", "architecture":"standalone-ultrarig-port", "firmware_version":"tankm_fw M5.71 rel ble",
                    "image_path":image.relative_to(ROOT).as_posix(), "image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
                    "capabilities":{"read":True,"write":False,"panel":False}, "hardware_verified":False}
            manifest = dest / "manifest.json"; manifest.write_text(json.dumps(spec), encoding="utf-8")
            self.assertTrue(load_profile(manifest)["capabilities"]["read"])
            spec["capabilities"]["write"] = True; manifest.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hardware validation"):
                load_profile(manifest)
            spec["capabilities"]["write"] = False; image.write_bytes(b"changed")
            manifest.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pinned source changed"):
                load_profile(manifest)


if __name__ == "__main__":
    unittest.main()
