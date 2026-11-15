"""Derive the complete HyperRig editor with an explicit TANK MINI board profile.

Offline only: no server, browser, installer, transport or device is started.
The original editor/DSP/model converters and licences remain source evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hyperrig.branding import rename_text

SOURCE = ROOT / "recovered/ultrarig-original"
SOURCE_SHA = "247d152045a9d8f987281e7e943c1ea359ccc2db1392f6a0cb439587717e88e6"
CONVERTER_SHA = "af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183"
FW_SOURCE = ROOT / "analysis/firmware/m571_g_app/app.bin"
FW_SHA = "4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e"
LICENSES = ("LICENSE.md", "NOTICE.md", "THIRD_PARTY_LICENSES.md")
SCOPED_COMMANDS = {
    "FXP": r"FXP (?:0|[1-9]\d*) (?:0|[1-9]\d*) -?(?:0|[1-9]\d*)",
    "FXE": r"FXE (?:0|[1-9]\d*) [01]",
    "PLOAD": r"PLOAD (?:[0-9]|[12][0-9]|3[01])",
    "PSAVE": r"PSAVE (?:[0-9]|[12][0-9]|3[01]) [^\r\n\x00-\x1f\x7f]+",
    "PDEL": r"PDEL (?:[0-9]|[12][0-9]|3[01])",
    "SNAP": r"SNAP [0-3]",
    "SNAPSAVE": r"SNAPSAVE [0-3]",
}
PERSISTENT_COMMANDS = {"PSAVE", "PDEL", "SNAPSAVE"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def checked(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError(f"pinned source changed: {path}")
    return data


def local_evidence(reference: dict, label: str) -> bytes:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError(label + " needs exact path/sha256 fields")
    if not isinstance(reference["path"], str) or not re.fullmatch(r"[a-f0-9]{64}", str(reference["sha256"])):
        raise ValueError(label + " needs a local path and SHA-256")
    path = (ROOT / reference["path"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(label + " must be a file inside the workspace")
    data = checked(path, reference["sha256"])
    if not data:
        raise ValueError(label + " is empty")
    return data


def command_grants(value: dict) -> dict:
    """Closed grammar and exact requests: a checked value grants no range."""
    if not isinstance(value, dict) or any(c not in SCOPED_COMMANDS for c in value):
        raise ValueError("unsupported scoped command capability")
    result = {}
    for command, requests in value.items():
        if (not isinstance(requests, list) or not requests or len(requests) > 256
                or any(not isinstance(line, str) for line in requests)
                or len(set(requests)) != len(requests)):
            raise ValueError("scoped commands need distinct nonempty exact request lists")
        for line in requests:
            if line != line.strip() or not re.fullmatch(SCOPED_COMMANDS[command], line, flags=re.ASCII):
                raise ValueError("invalid scoped request: " + repr(line))
            if command == "PSAVE" and len(line.split(" ", 2)[2].encode("utf-16-le")) // 2 > 23:
                raise ValueError("PSAVE names are limited to 23 UTF-16 units")
            # M4.83+ USB line capacity, excluding LF, as in the original editor.
            if len(line.encode("utf-8")) > 190:
                raise ValueError("scoped request exceeds USB line capacity")
        result[command] = sorted(requests)
    return dict(sorted(result.items()))


def load_command_validation(spec: dict, caps: dict) -> tuple[dict, dict | None]:
    grants = command_grants(spec.get("command_capabilities", {}))
    proof = spec.get("command_validation")
    if not grants:
        if proof is not None:
            raise ValueError("command evidence without requested capabilities")
        return {}, None
    if caps.get("write"):
        raise ValueError("choose scoped commands or the legacy full-write profile, not both")
    if spec.get("hardware_verified") is not True or caps.get("read") is not True:
        raise ValueError("scoped commands require hardware evidence and read capability")
    evidence = json.loads(local_evidence(proof, "command validation"))
    if (not isinstance(evidence, dict) or evidence.get("schema") != 1
            or evidence.get("kind") != "mini-app-command-validation"
            or evidence.get("target") != "tank-mini"
            or evidence.get("firmware_version") != spec["firmware_version"]
            or evidence.get("image_sha256") != spec["image_sha256"]
            or evidence.get("hardware_executed") is not True
            or evidence.get("transport") != "usb-cdc"
            or evidence.get("editor_source_sha256") != SOURCE_SHA):
        raise ValueError("command evidence does not match this image/editor/transport")
    verified = command_grants(evidence.get("verified_requests", {}))
    if verified != grants:
        raise ValueError("command evidence must attest exactly the requested subset")
    # The report is a reviewed assertion, not a PONG hash attestation or a
    # generated hardware result. Bind it to the actual retained trace/backup.
    local_evidence(evidence.get("trace"), "command trace")
    local_evidence(evidence.get("backup"), "pre-test state backup")
    if evidence.get("restoration_verified") is not True:
        raise ValueError("command validation needs a verified restoration")
    observations = evidence.get("observations")
    wanted = {line for requests in grants.values() for line in requests}
    if (not isinstance(observations, list) or len(observations) != len(wanted)
            or any(not isinstance(o, dict) for o in observations)
            or any(not isinstance(o.get("request"), str) for o in observations)
            or {o.get("request") for o in observations} != wanted):
        raise ValueError("each exact request needs its own observation")
    for observation in observations:
        command = observation["request"].split(" ")[0]
        if observation.get("ack_verified") is not True or observation.get("readback_verified") is not True:
            raise ValueError("command observation needs ACK and readback verification")
        if command in PERSISTENT_COMMANDS and observation.get("persistence_readback_verified") is not True:
            raise ValueError("persistent command needs reload/delete readback verification")
    return grants, copy.deepcopy(proof)


def load_profile(manifest: Path | None = None) -> dict:
    profile = json.loads((ROOT / "app/mini/board-profile.json").read_text("utf-8"))
    if manifest is None:
        return profile
    spec = json.loads(manifest.read_text("utf-8"))
    if spec.get("target") != "tank-mini" or spec.get("architecture") != "standalone-ultrarig-port":
        raise ValueError("manifest is not for the standalone UltraRig MINI port")
    version = spec.get("firmware_version", "")
    if not re.fullmatch(r"tankm_fw M\d+\.\d+(?: [a-zA-Z0-9+_.-]+)*", version) or re.search(r"\btank[gb]\b", version):
        raise ValueError("manifest needs the exact tankm_fw version, without G/B suffix")
    path = (ROOT / spec["image_path"]).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("image must be inside the workspace")
    checked(path, spec["image_sha256"])
    caps = spec.get("capabilities", {})
    if not isinstance(caps, dict) or set(caps) - {"identity", "read", "write", "panel"}:
        raise ValueError("unknown capability field")
    if any(type(value) is not bool for value in caps.values()):
        raise ValueError("capabilities must be booleans")
    if caps.get("panel"):
        raise ValueError("three-switch panel mapping is not implemented/validated yet")
    grants, command_validation = load_command_validation(spec, caps)
    if caps.get("write"):
        proof = spec.get("write_validation") or {}
        proof_path = (ROOT / proof.get("path", "")).resolve()
        if not proof_path.is_relative_to(ROOT) or not proof_path.is_file():
            raise ValueError("write capability needs a hardware validation report")
        evidence = json.loads(checked(proof_path, proof.get("sha256", "")))
        if (spec.get("hardware_verified") is not True or evidence.get("target") != "tank-mini"
                or evidence.get("image_sha256") != spec["image_sha256"]
                or evidence.get("all_required_editor_mutations_verified") is not True
                or not caps.get("read")):
            raise ValueError("write evidence does not validate this image and editor contract")
    profile.update(firmware_version=version, image_sha256=spec["image_sha256"],
                   hardware_verified=spec.get("hardware_verified") is True,
                   write_validation=copy.deepcopy(spec.get("write_validation")),
                   command_capabilities=grants, command_validation=command_validation)
    profile["capabilities"].update(read=caps.get("read", False), write=caps.get("write", False))
    return profile


def derive_html(source: str, profile: dict) -> tuple[str, list[dict]]:
    html = rename_text(source)
    patches = []

    def replace(old: str, new: str, name: str) -> None:
        nonlocal html
        if html.count(old) != 1:
            raise ValueError(f"source anchor is not unique: {name}")
        html = html.replace(old, new)
        patches.append({"name": name, "before_sha256": sha(old.encode()), "after_sha256": sha(new.encode())})

    replace('<title>HyperRig for Tank-G and Tank-B</title>', '<title>HyperRig for TANK MINI</title>', "document title")
    replace('const PEDAL_NAME = { "tank-g": "Tank-G", "tank-b": "Tank-B" };',
            'const PEDAL_NAME = { "tank-g": "Tank-G", "tank-b": "Tank-B", "tank-mini": "TANK MINI" };', "board name")
    replace('const pongBoard = pong => / v1$/.test(pongVer(pong)) ? "v1" : "v2";',
            'const pongBoard = pong => /^PONG tankm_fw\\b/.test(pong) ? "mini" : "unsupported";', "board identity")
    replace('const pongPedal = pong => / tankb( v1)?$/.test(pongVer(pong)) ? "tank-b" : "tank-g";',
            'const pongPedal = pong => /^PONG tankm_fw\\b/.test(pong) ? "tank-mini" : "unsupported";', "no G/B fallback")
    replace('const demoPedal = search => /(^|[?&])model=(b|tank-?b)(&|$)/i.test(search || "") ? "tank-b" : "tank-g";',
            'const demoPedal = search => "tank-mini";', "explicit offline MINI demo")
    replace('const pedalKey = () => S.pedal === "tank-b" ? "tank-b" : "tank-g";',
            'const pedalKey = () => S.pedal === "tank-mini" || !S.pedal ? "tank-mini" : "unsupported";', "MINI board key")
    replace('const INTENT_KEY = "tankg.conn", BOOT_OPEN_MS = 400;',
            'const INTENT_KEY = "hyperrig.mini.conn", BOOT_OPEN_MS = 400;', "separate saved MINI connection")
    replace('const BLE_KEYS = "tankg.blekeys";',
            'const BLE_KEYS = "hyperrig.mini.blekeys";', "separate MINI Bluetooth credentials")
    replace('new BroadcastChannel("tankg-port")', 'new BroadcastChannel("hyperrig-mini-port")', "separate MINI tab ownership")
    replace('  cmd(line, until, timeout = 1500) {',
            '  cmd(line, until, timeout = 1500) {\n    if (!DEMO) { const gate = HyperRigMini.commandPolicy(line, this.tr === SerialTransport ? "usb-cdc" : "ble-nus"); if (!gate.allowed) {\n      Log.ev("mini_command_blocked", { command: String(line).split(" ")[0], reason: gate.reason });\n      return Promise.resolve(["ERR MINI_APP " + gate.reason]);\n    } }', "command capabilities before queue or write")
    replace('  S.connected = true; S.connAt = Date.now(); autoRe = null; ctlReleased = false; Tabs.busy = false; S.firstUse = false;',
            '  const miniIdentity = HyperRigMini.acceptPong(pong, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");\n  if (!miniIdentity.ok) { toast(miniIdentity.reason, "err"); await Pedal.disconnect(); return new Error(miniIdentity.reason); }\n  S.connected = true; S.connAt = Date.now(); autoRe = null; ctlReleased = false; Tabs.busy = false; S.firstUse = false;', "verify MINI before first query or mutation")
    replace('function onDisconnected(e) {', 'function onDisconnected(e) {\n  HyperRigMini.resetIdentity();', "clear session capability on disconnect")
    replace('  Log.act("preset_save", { n, name, replace: !!existing });',
            '  if (!DEMO) {\n'
            '    const required = [`PSAVE ${n} ${name}`, "SNAPSAVE 0"];\n'
            '    if (S.snap >= 0 && (ED.p.size || ED.on || ED.aeq)) required.push(`SNAPSAVE ${S.snap}`);\n'
            '    const gate = HyperRigMini.preflight(required, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");\n'
            '    if (!gate.allowed) { toast("Preset save unavailable: " + gate.reason, "err"); return; }\n'
            '  }\n'
            '  Log.act("preset_save", { n, name, replace: !!existing });', "preflight preset and automatic scene saves")
    replace('  saveRun = true; let go = false;',
            '  if (!DEMO) {\n'
            '    if (how === "all" && !HyperRigMini.fullWriteEnabled()) { toast("Saving all scenes is not validated for this limited MINI profile.", "err"); return; }\n'
            '    if (how !== "all") {\n'
            '      const required = how === "one" ? [`SNAPSAVE ${k0}`] : [`PSAVE ${curPreset} ${presetName()}`, "SNAPSAVE 0"];\n'
            '      const gate = HyperRigMini.preflight(required, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");\n'
            '      if (!gate.allowed) { toast("Save unavailable: " + gate.reason, "err"); return; }\n'
            '    }\n'
            '  }\n'
            '  saveRun = true; let go = false;', "preflight save bar and exclude unqualified multi-scene writes")
    # Export can traverse scenes, mute audio and reload presets. It is not a
    # harmless backup operation in a partially qualified command profile.
    replace('async function pioExport(all) {',
            'async function pioExport(all) {\n'
            '  if (!DEMO && !HyperRigMini.fullWriteEnabled()) { toast("Full preset export changes scenes and is not validated for this limited MINI profile.", "err"); return; }',
            "no partial preset export in a limited profile")
    replace('  const board = DEMO ? `${pedalName()} demo` : `${pedalName()} ${S.board || "v2"}`, fw = S.fwName || "HyperRig";',
            '  const board = DEMO ? `${pedalName()} demo` : pedalName(), fw = S.fwName || "HyperRig";', "no invented MINI revision")
    replace('const fmSecOf = (f, pedal) => (FM_FS[pedal] || FM_FS["tank-g"])[f];',
            'const fmSecOf = (f, pedal) => pedal === "tank-mini" ? null : (FM_FS[pedal] || [])[f];', "no implicit four-switch assignment")
    replace('const fmLiveFs = pedal => [0, 1, 2, 3].map(f => FM_SEC_NAME[fmSecOf(f, pedal)]);',
            'const fmLiveFs = pedal => pedal === "tank-mini" ? ["A (unassigned)", "B (unassigned)", "C (unassigned)"] : [0, 1, 2, 3].map(f => FM_SEC_NAME[fmSecOf(f, pedal)]);', "three-switch profile")
    replace('function taTankG(o = {}) {',
            'function taTankG(o = {}) {\n  if ((o.pedal || pedalKey()) === "tank-mini") return HyperRigMini.panelSvg();', "MINI schematic without fabricated G/B knobs")
    replace('function fsDots() {',
            'function fsDots() {\n  if (pedalKey() === "tank-mini") { $("fswDots").innerHTML = "<i></i><i></i><i></i>"; return; }', "three neutral switch indicators")
    for func in ("fsOpen", "stageOpen"):
        replace(f'async function {func}() {{', f'async function {func}() {{\n  if (!HyperRigMini.profile.capabilities.panel) {{ toast("MINI switch and LED assignments still require validation", "err"); return; }}', f"gate {func}")
    replace('function fwHintHtml(o) {',
            'function fwHintHtml(o) {\n  return "<h4>HyperRig MINI port in development</h4><p>This app requires standalone tankm_fw firmware. Stock MINI and Tank-G/B images are incompatible. The offline demo is available.</p>";\n', "remove G/B installation advice")
    replace('function demoWhyHtml(c, url, via) {',
            'function demoWhyHtml(c, url, via) {\n  return \'<span>Offline editor demo. A standalone HyperRig MINI firmware build is required for a real connection.</span><button type="button" class="btn mini primary" id="demoExit">Exit demo</button>\';', "demo does not promise compatibility with stock MINI")
    # Original scripts, demo, converters, queues and feature handlers remain.
    config = json.dumps(profile, separators=(",", ":"), ensure_ascii=True).replace("<", "\\u003c")
    injected = f'<script>globalThis.HYPERRIG_MINI_BUILD={config};</script>\n<script src="mini-profile.js"></script>\n'
    first_script = html.index("<script>")
    html = html[:first_script] + injected + html[first_script:]
    replace("</body>", '<script src="mini-ui.js"></script>\n</body>', "MINI status UI")
    return html, patches


def call_sites(source: str) -> list[dict]:
    """Balanced argument scan, retaining unresolved JS expressions verbatim.

    This is an inventory, not a JavaScript evaluator or a claim that every
    dynamic command has been statically resolved.
    """
    found = []
    for match in re.finditer(r"Pedal\.cmd\(", source):
        i = start = match.end()
        stack, quote, escaped, args = [], None, False, []
        while i < len(source):
            ch = source[i]
            if quote:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
            elif ch in "\"'`":
                quote = ch
            elif ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if ch == ")" and not stack:
                    args.append(source[start:i].strip())
                    break
                if stack:
                    stack.pop()
            elif ch == "," and not stack:
                args.append(source[start:i].strip())
                start = i + 1
            i += 1
        if not args:
            continue
        first = args[0]
        literal = re.match(r'^["\'`]([A-Z][A-Z0-9]+)(?:[ "\'`]|$)', first)
        found.append({"line": source.count("\n", 0, match.start()) + 1,
                      "command": literal[1] if literal else None,
                      "request_expression": first,
                      "completion_expression": args[1] if len(args) > 1 else None,
                      "timeout_expression": args[2] if len(args) > 2 else "1500 (default)",
                      "dynamic": literal is None or "${" in first})
    return found


def descriptor_evidence() -> dict:
    app = checked(FW_SOURCE, FW_SHA)
    descriptor = bytes.fromhex("120100020000004054365541000101020301")
    if app[0x34F65:0x34F65 + 18] != descriptor:
        raise ValueError("USB device descriptor bytes differ")
    patch_address = 0x0201B9F0
    if app[patch_address - 0x02000120:patch_address - 0x02000120 + 4] != bytes.fromhex("5131894b"):
        raise ValueError("USB runtime PID patch bytes differ")
    uuids = {}
    for n in range(1, 5):
        normal = f"6e40000{n}-b5a3-f393-e0a9-e50e24dcca9e"
        encoded = bytes.fromhex(normal.replace("-", ""))[::-1]
        offsets = [m.start() for m in re.finditer(re.escape(encoded), app)]
        if not offsets:
            raise ValueError(f"NUS UUID missing: {normal}")
        uuids[normal] = [f"0x{0x02000120 + off:08x}" for off in offsets]
    config = app[0x34F99:0x34F99 + 75]
    expected_config = bytes.fromhex("090200000001008032080b000202020100090400000102020100052400100105240103010424020205240600010705820308000109040100020a0000000705020240000007058302400000")
    if config != expected_config:
        raise ValueError("CDC template bytes differ")
    def cstring(address):
        offset = address - 0x02000120
        return app[offset:app.index(0, offset)].decode("ascii")
    return {"source": relative(FW_SOURCE), "source_sha256": FW_SHA, "hardware_enumeration_verified_on_mini": False,
            "usb": {"device_template_address": "0x02035085", "device_template_hex": descriptor.hex(),
                    "template_vid": "3654", "template_pid": "4155", "runtime_pid": "5155",
                    "pid_patch_address": "0x0201b9f0", "pid_patch_hex": "5131894b",
                    "pid_patch_semantics": "r1=0x51; b[r0+11]=r1 after 18-byte descriptor copy at 0x0201b9e2",
                    "configuration_template_address": "0x020350b9", "configuration_template_hex": config.hex(),
                    "control_interface": {"number": 0, "class": 2, "subclass": 2, "protocol": 1, "interrupt_in": "82", "packet_bytes": 8},
                    "data_interface": {"number": 1, "class": 10, "bulk_out": "02", "bulk_in": "83", "packet_bytes": 64},
                    "product_string_address": "0x0203a264", "product_original": "Tank-G UltraRig"},
            "nus_uuid_addresses": uuids,
            "firmware_read_guard_list": {"address": "0x020388c4", "text": cstring(0x020388C4),
                                         "note": "Original firmware string evidence; no claim that a MINI build executes these handlers yet."},
            "firmware_command_list": {"address": "0x02038b09", "text": cstring(0x02038B09)}}


def build(output: Path, manifest: Path | None = None, report: Path | None = None) -> dict:
    output = output.resolve()
    if not output.is_relative_to(ROOT / "build"):
        raise ValueError("generated app must stay under build/")
    source_bytes = checked(SOURCE / "web/tankg.html", SOURCE_SHA)
    converter_bytes = checked(SOURCE / "web/nam2chip.js", CONVERTER_SHA)
    profile = load_profile(manifest)
    html, patches = derive_html(source_bytes.decode("utf-8"), profile)
    output.mkdir(parents=True, exist_ok=True)
    web = output / "web"
    web.mkdir(exist_ok=True)
    (web / "tankmini.html").write_text(html, encoding="utf-8", newline="\n")
    (web / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>HyperRig MINI</title><script>location.replace("tankmini.html"+location.search+location.hash)</script><a href="tankmini.html">Open HyperRig MINI</a>', encoding="utf-8")
    (web / "nam2chip.js").write_text(rename_text(converter_bytes.decode("utf-8")), encoding="utf-8", newline="\n")
    for name in ("mini-profile.js", "mini-ui.js"):
        (web / name).write_bytes((ROOT / "app/mini" / name).read_bytes())
    for name in LICENSES:
        (output / name).write_bytes((SOURCE / name).read_bytes())
    (output / "DERIVATION.txt").write_text(
        "HyperRig MINI derives the complete original UltraRig alpha11 editor.\n"
        "Original licences/notices are retained verbatim. No stock MINI control bridge is included.\n"
        "Default build is offline demo / identity-only; it is not evidence of a running MINI firmware.\n"
        "Firmware images/installers and personal preset backups are not included.\n", encoding="utf-8")
    calls = call_sites(source_bytes.decode("utf-8"))
    result = {"project": "HyperRig", "target": "tank-mini", "architecture": "standalone-ultrarig-port",
              "source_editor": relative(SOURCE / "web/tankg.html"), "source_sha256": SOURCE_SHA,
              "source_converter_sha256": CONVERTER_SHA, "full_original_editor_preserved": True,
              "implementation_files": {relative(p): sha(p.read_bytes()) for p in [Path(__file__), *sorted((ROOT / "app/mini").glob("*"))] if p.is_file()},
              "stock_mini_protocol_adapter": False, "firmware_hardware_verified": profile["hardware_verified"],
              "profile": profile, "patches": patches, "call_sites": calls,
              "scoped_mutations": {"supported_commands": sorted(SCOPED_COMMANDS),
                                   "scope": "exact request strings, no wildcard/prefix/range expansion",
                                   "hardware_validation_required": True, "enabled_by_default": False,
                                   "snapshot_context": "SNAP/SNAPSAVE and FXP/FXE act on current firmware state; wire grants are not a board-state lock"},
              "command_names": sorted({c["command"] for c in calls if c["command"]}),
              "dynamic_call_site_count": sum(c["dynamic"] for c in calls),
              "inventory_scope": "All textual Pedal.cmd call sites; unresolved JS expressions are retained, not inferred as resolved commands.",
              "firmware_transport": descriptor_evidence(),
              "required_startup_queries": ["PING", "BLE (if advertised)", "FXT", "MODEL", "CLIST", "MEM", "FXXO", "LVL", "FXS", "FXMIX (if needed)", "PLIST", "SNAPS", "SNAPNAME", "AMPEQ", "AMPEQ info", "GEQ", "HPF", "SPILL", "GLIDE", "SPUR", "LIM", "PSTAT", "CRASH"],
              "asynchronous_responses": ["@L", "@K", "NOISE ms=", "CALIB", "ERR CALIB stopped"],
              "board_assumptions": {"original_switches": 4, "original_knobs": 15, "mini_switches": 3,
                  "mini_pins_and_led_mapping": "unresolved; physical-control commands blocked",
                  "original_presets": "8 banks x 4 slots; original storage/protocol retained pending port storage audit",
                  "stock_21_preset_layout_used": False, "capture_formats": "original NAM converter / A2L1; no conversion to stock AM4"},
              "output": relative(output), "files": {relative(p): sha(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}}
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/hyperrig-mini")
    parser.add_argument("--firmware-manifest", type=Path, help="reviewed standalone port artifact; optional, default identity only")
    parser.add_argument("--report", type=Path, default=ROOT / "research/mini-app-protocol.json")
    args = parser.parse_args()
    result = build(args.output, args.firmware_manifest, args.report)
    print(json.dumps({"output": result["output"], "call_sites": len(result["call_sites"]),
                      "command_names": len(result["command_names"]), "capabilities": result["profile"]["capabilities"],
                      "device_io": False}, indent=2))


if __name__ == "__main__":
    main()
