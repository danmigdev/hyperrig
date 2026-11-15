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
                                  command_grants, derive_html, descriptor_evidence, load_profile)


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
  const transport = action.transport === undefined ? 'usb-cdc' : action.transport;
  if (action.pong !== undefined) results.push(mini.acceptPong(action.pong, transport));
  else if (action.reset) { mini.resetIdentity(); results.push(null); }
  else if (action.preflight) results.push(mini.preflight(action.preflight, transport));
  else results.push(mini.commandPolicy(action.command, transport));
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
context=vm.createContext({HYPERRIG_MINI_BUILD:input.profile,DEMO:false,S:{},SerialTransport:transport,
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

    def scoped_profile(self):
        p = self.read_profile()
        p.update(hardware_verified=True, command_validation={"path": "offline-test-fixture", "sha256": "b" * 64},
                 command_capabilities={"FXP": ["FXP 1 0 50", "FXP 1 0 51"], "FXE": ["FXE 1 0", "FXE 1 1"],
                                       "PLOAD": ["PLOAD 31"], "PSAVE": ["PSAVE 31 Scratch"], "PDEL": ["PDEL 31"],
                                       "SNAP": ["SNAP 0"], "SNAPSAVE": ["SNAPSAVE 0"]})
        return p

    def test_scoped_profile_allows_only_exact_reviewed_requests(self):
        p = self.scoped_profile()
        allowed = [line for lines in p["command_capabilities"].values() for line in lines]
        forbidden = ["FXP 1 0 52", "FXP 2 0 50", "FXP 1 1 50", "FXE 2 0", "PLOAD 30", "PSAVE 30 Scratch",
                     "PSAVE 31 Other", "PSAVE 31 Scratch ", "PDEL 30", "SNAP 1", "SNAPSAVE 1", "FXA P delay",
                     "LDBEGIN 4892", "LDEND 1234", "IRBEGIN 256 0 48000", "CSAVE 0 name", "GSAVE", "UBOOT",
                     "FSDO a", "LEDCFG mode=1", "FXP 1 0 50\nPSAVE 31 Scratch"]
        start = {"pong": "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"}
        result = self.policy([start]+[{"command": c} for c in allowed+forbidden], p)
        self.assertTrue(result[0]["ok"] and result[0]["write"])
        self.assertEqual(result[0]["write_scope"], "exact-requests")
        self.assertEqual([r["allowed"] for r in result[1:]], [True]*len(allowed)+[False]*len(forbidden))
        self.assertTrue(all(r["capability"] == "command" for r in result[1:1+len(allowed)]))
        self.assertFalse(p["capabilities"]["write"])
        self.assertFalse(self.policy([{ "command": allowed[0]}], p)[0]["allowed"])
        self.assertFalse(self.policy([start,{"reset":True},{"command":allowed[0]}], p)[2]["allowed"])
        for field in ("hardware_verified", "command_validation"):
            limited = copy.deepcopy(p); limited[field] = None
            self.assertFalse(self.policy([start,{"command":allowed[0]}], limited)[1]["allowed"])
        # The runtime also has a closed command-name set; a hand-built profile
        # cannot smuggle an upload/panel command through the scoped path.
        p["command_capabilities"]["LDBEGIN"] = ["LDBEGIN 4892"]
        p["command_capabilities"]["FSDO"] = ["FSDO a"]
        self.assertEqual([r["allowed"] for r in self.policy([start,{"command":"LDBEGIN 4892"},
                                                            {"command":"FSDO a"}], p)[1:]], [False,False])

    def test_scoped_command_grammar_does_not_expand_to_slots_values_or_prefixes(self):
        good = self.scoped_profile()["command_capabilities"]
        self.assertEqual(set(command_grants(good)), set(good))
        invalid = [{"FXP": ["FXP 1 0 50", "FXP 1 0 50"]}, {"FXP": []}, {"FXP": "FXP 1 0 50"},
                   {"FXP": ["FXP 1 0 *"]}, {"FXE": ["FXE 1 2"]}, {"PLOAD": ["PLOAD 32"]},
                   {"PSAVE": ["PSAVE 31 "]}, {"PSAVE": ["PSAVE 31 " + "😀"*12]},
                   {"PSAVE": ["PSAVE 31 name\tother"]}, {"SNAP": ["SNAP 4"]},
                   {"SNAPSAVE": ["SNAPSAVE 0\nGSAVE"]}, {"LDBEGIN": ["LDBEGIN 8"]},
                   {"FSA": ["FSA 0"]}, {"*": ["*"]}, {"PDEL": [True]}]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                command_grants(value)

    def test_scoped_manifest_binds_each_request_to_trace_backup_and_image(self):
        with tempfile.TemporaryDirectory(prefix="mini-app-scoped-", dir=ROOT / "build") as temp:
            dest = Path(temp).resolve(); self.assertTrue(dest.is_relative_to((ROOT / "build").resolve()))
            def artifact(name, data):
                path = dest/name; path.write_bytes(data)
                return {"path":path.relative_to(ROOT).as_posix(), "sha256":hashlib.sha256(data).hexdigest()}
            image = artifact("fixture.bin", b"OFFLINE TEST ONLY; not firmware")
            trace = artifact("fixture-trace.jsonl", b'{"offline_test_fixture":true}\n')
            backup = artifact("fixture-backup.json", b'{"offline_test_fixture":true,"state":"before"}')
            grants = self.scoped_profile()["command_capabilities"]
            evidence = {"schema":1, "kind":"mini-app-command-validation", "target":"tank-mini",
                        "firmware_version":"tankm_fw M5.71 rel ble", "image_sha256":image["sha256"],
                        "editor_source_sha256":SOURCE_SHA, "hardware_executed":True, "transport":"usb-cdc",
                        "verified_requests":grants, "trace":trace, "backup":backup, "restoration_verified":True,
                        "observations":[{"request":line,"ack_verified":True,"readback_verified":True,
                                         "persistence_readback_verified":True} for lines in grants.values() for line in lines]}
            spec = {"target":"tank-mini", "architecture":"standalone-ultrarig-port",
                    "firmware_version":evidence["firmware_version"], "image_path":image["path"], "image_sha256":image["sha256"],
                    "hardware_verified":True, "capabilities":{"read":True,"write":False,"panel":False},
                    "command_capabilities":grants}
            def load(test_spec=None, test_evidence=None):
                s = copy.deepcopy(test_spec or spec); e = copy.deepcopy(test_evidence or evidence)
                s["command_validation"] = artifact("fixture-proof.json", json.dumps(e).encode())
                manifest = dest/"manifest.json"; manifest.write_text(json.dumps(s), encoding="utf-8")
                return load_profile(manifest)
            result = load()
            self.assertEqual(result["command_capabilities"], command_grants(grants))
            self.assertFalse(result["capabilities"]["write"] or result["capabilities"]["panel"])
            modifications = [("target","tank-g"), ("firmware_version","tankm_fw M5.70 rel ble"),
                             ("image_sha256","0"*64), ("editor_source_sha256","0"*64),
                             ("hardware_executed",False), ("transport","simulation"), ("restoration_verified",False),
                             ("verified_requests",{"FXP":["FXP 1 0 99"]}), ("observations",[]),
                             ("trace",{**trace,"sha256":"0"*64}), ("backup",{**backup,"sha256":"0"*64})]
            for key, value in modifications:
                e = copy.deepcopy(evidence); e[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): load(test_evidence=e)
            for flag in ("ack_verified", "readback_verified", "persistence_readback_verified"):
                e = copy.deepcopy(evidence)
                next(o for o in e["observations"] if o["request"].startswith("PSAVE"))[flag] = False
                with self.subTest(flag=flag), self.assertRaises(ValueError): load(test_evidence=e)
            e = copy.deepcopy(evidence); e["observations"][1] = e["observations"][0]
            with self.assertRaises(ValueError): load(test_evidence=e)
            for flag in ("hardware_verified", "read", "write", "panel"):
                s = copy.deepcopy(spec)
                if flag == "hardware_verified": s[flag] = False
                else: s["capabilities"][flag] = flag in ("write","panel")
                with self.subTest(flag=flag), self.assertRaises(ValueError): load(test_spec=s)

    def test_original_save_preflights_scene_capability_before_any_mutation(self):
        code = r"""
const fs=require('fs'),vm=require('vm'),v=JSON.parse(fs.readFileSync(0,'utf8'));
const wires=[],toasts=[],state={preset:0,saved:false,snap:false},serial={};
const context=vm.createContext({HYPERRIG_MINI_BUILD:v.profile,DEMO:false,PH:false,curPreset:0,SerialTransport:serial,
 S:{snap:-1,snaps:[0,0,0,0],pendName:''},ED:{ep:0,seq:0,p:new Map(),on:false,aeq:false},
 Log:{act:()=>{},ev:()=>{}},toast:(...a)=>toasts.push(a),renderPresets:()=>{},
 readPlist:async()=>({ok:true,list:[]}),presetName:()=> 'Scratch',SLOT:i=>'ABCD'[i%4],
 aeqSettle:async()=>{},evSince:async()=>null,edFresh:async()=>{},edMoved:()=>false,
 evMoves:()=>false,edClearUpTo:()=>{},loadPresets:()=>{},loadSnaps:async()=>{},
 reply:(lines,p)=>lines.find(l=>l.startsWith(p))||'',plist:[],plistHave:false,
 Pedal:{tr:serial,cmd:async line=>{
  const gate=context.HyperRigMini.commandPolicy(line,'usb-cdc');
  if(!gate.allowed)return ['ERR MINI_APP '+gate.reason];
  wires.push(line);
  if(line==='PSAVE 31 Scratch'){state.preset=31;state.saved=true;return ['PSAVE ok 31'];}
  if(line==='SNAPS')return ['SNAPS 0000 current=-1'];
  if(line==='SNAPSAVE 0'){state.snap=true;return ['SNAPSAVE ok 0 preset=31'];}
  throw Error('unplanned request '+line);
 }}});
vm.runInContext(fs.readFileSync('app/mini/mini-profile.js','utf8'),context);
context.HyperRigMini.acceptPong('PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32','usb-cdc');
const start=v.html.indexOf('async function sceneAOnSave('),end=v.html.indexOf('/*PRESET-IO-BEGIN*/',start);
if(start<0||end<0)throw Error('original save anchors missing');
vm.runInContext(v.html.slice(start,end),context);
(async()=>{await context.savePreset(31,null);process.stdout.write(JSON.stringify({wires,toasts,state}));})()
 .catch(e=>{process.stderr.write(String(e));process.exitCode=1});
"""
        p = self.scoped_profile(); p["command_capabilities"].pop("SNAPSAVE")
        blocked = node(code, {"html":self.html,"profile":p})
        self.assertFalse(blocked["state"]["saved"])
        self.assertEqual(blocked["wires"], [])
        self.assertIn("Preset save unavailable", blocked["toasts"][0][0])
        allowed = node(code, {"html":self.html,"profile":self.scoped_profile()})
        self.assertEqual(allowed["wires"], ["PSAVE 31 Scratch","SNAPS","SNAPSAVE 0"])
        self.assertTrue(allowed["state"]["saved"] and allowed["state"]["snap"])
        self.assertEqual(allowed["state"]["preset"], 31)

    def test_limited_profile_cannot_start_partial_all_scene_save_or_export(self):
        p = self.scoped_profile()
        result = self.policy([{"pong":"PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"},
                              {"preflight":["PSAVE 31 Scratch","SNAPSAVE 0"]},
                              {"preflight":["PSAVE 31 Scratch","SNAPSAVE 1"]}], p)
        self.assertTrue(result[1]["allowed"])
        self.assertFalse(result[2]["allowed"])
        self.assertEqual(result[2]["command"], "SNAPSAVE 1")
        save_flow = self.html[self.html.index("async function saveFlow()"):]
        self.assertLess(save_flow.index('how === "all" && !HyperRigMini.fullWriteEnabled()'),
                        save_flow.index("saveRun = true"))
        export = self.html[self.html.index("async function pioExport(all)"):]
        self.assertLess(export.index("!HyperRigMini.fullWriteEnabled()"), export.index("await"))

    def test_usb_scoped_proof_does_not_authorize_ble_or_a_changed_transport(self):
        p = self.scoped_profile()
        pong = "PONG tankm_fw M5.71 rel ble Nov 12 2026 16:05:32"
        for transport in ("ble-nus", "native-usb-unqualified", None):
            result = self.policy([{"pong":pong,"transport":transport},
                                  {"command":"FXP 1 0 50","transport":transport},
                                  {"command":"FXP 1 0 50","transport":"usb-cdc"},
                                  {"command":"FXS","transport":transport}], p)
            with self.subTest(transport=transport):
                self.assertTrue(result[0]["ok"])
                self.assertFalse(result[0]["write"])
                self.assertEqual([r["allowed"] for r in result[1:]], [False,False,True])
        result = self.policy([{"pong":pong,"transport":"usb-cdc"},
                              {"command":"FXP 1 0 50","transport":"ble-nus"},
                              {"command":"FXP 1 0 50","transport":"usb-cdc"}], p)
        self.assertEqual([r["allowed"] for r in result[1:]], [False,True])


if __name__ == "__main__":
    unittest.main()
