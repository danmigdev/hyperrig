"""Build the development editor for HyperRig MINI builds from source, offline.

The sealed editors tie their write commands to one firmware image by hash, with the report of a hardware trial of that
image. A build from source is a new image every time, so its package carries a read-only editor. This editor is for
the owner of a development unit: the interface of the v4 editor (revision mini-v4-usb-01), its nine USB command
families, and the commands the page sends for the amp, the whole chain with moving and parallel paths, stereo, tempo
and tuner, presets, scenes and footswitches (app/mini/mini-dev-rules.js). It also corrects faults of that editor:
- after a footswitch changed the preset, its rules threw away what they had just read and refused every edit and Save;
- after a click on an empty slot, Save asked for a slot instead of saving there;
- after the pedal refused a command on the chain, the next one was refused by the editor.
Captures and IRs, calibration, Bluetooth, firmware update and authentication stay blocked; the editor of a product build
loads NAM captures and cab IRs (tools/check_mini_library.py runs that build's own commands for them in the simulator), and has
the settings for every preset and the calibration of the input (tools/check_mini_globals.py).

It claims no qualification. hardware_verified stays false, no validation report is attached, the profile says
"development" and the page says so. The firmware cannot attest its binary. Of a build from source without the product
option the editor knows the version line of PING only, the same for v4 and for every other build. A product build
(docs/MINI_PRODUCT.md) says its version and build id with HRID: the editor made for it asks after PING, reads only when
the answer is another, and has three switches, banks of three and the gestures of that build.

The tested files are inputs, pinned by SHA-256, and stay unchanged: the policy is app/mini/mini-profile-fx.js with the
changes of POLICY below, the page and the notes are those of the v4 package with the changes of PAGE and NOTE.

Usage, from the repository root:
    python -B tools/build_mini_dev_editor.py --output build/hyperrig-mini-dev-editor-NN --area build/.../mini
    python -B tools/build_mini_dev_editor.py --check build/hyperrig-mini-dev-editor-NN
--area is the output directory of tools/build_hyperrig_mini_image.py whose area the editor is built for.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = ROOT / 'build/hyperrig-mini-installer-v4-fast-01/editor'
KIND, REVISION, PRODUCT_REVISION = 'hyperrig-mini-development-editor', 'mini-dev-05', 'mini-product-36'
PAGE_FILE = 'tank-mini.html'      # of the v4 package: tankmini.html, a pinned input
FAMILIES = ['GAIN', 'PLOAD', 'PSAVE', 'SNAPSAVE', 'FXA', 'FXP', 'FXE', 'FXR', 'SNAP']    # of mini-v4-usb-01
ADDED = ['BPM', 'TUNER', 'AMP', 'AMPX', 'AMPEQ', 'STW', 'FXM', 'FXL', 'FXOS', 'FXMIX', 'FXXO', 'PNEW', 'PNAME', 'PDEL', 'PCOLOR',
         'SNAPNAME', 'SNAPDEL', 'FSA', 'FSMODE', 'FSPRESS', 'FSLED', 'LEDCFG', 'FSDO', 'GSAVE']    # of app/mini/mini-dev-rules.js
PRODUCT_ADDED = ['KNOB', 'IRBEGIN', 'IRB', 'IREND', 'ISAVE', 'ILOAD', 'IDEL', 'IREAD', 'FXIR',
                 'LDBEGIN', 'LDB', 'LDEND', 'CSAVE', 'CLOAD', 'CDEL', 'CREAD', 'CTRIM', 'AUDIO', 'GEQ', 'HPF', 'LIM', 'SPILL', 'GLIDE', 'SPUR', 'CALIB', 'FXC', 'MIDI', 'SNAPCAP', 'HRLV', 'REC', 'RECD', 'INJBEGIN', 'INJB']
RULES = ROOT / 'app/mini/mini-dev-rules.js'
PRODUCT_FILES = ['product-ui.css', 'product-ui.js',      # of app/mini: the sizes of the controls, and the size of everything;
                 'product-try.css', 'product-presetfile.js', 'product-try.js', 'product-share.js',      # trying without saving; Patchstorage in the desktop program
                 'product-parametric.js', 'product-amp-knobs.js',    # NAM captures that keep knobs: their conversion, and the amp's panel
                 'product-midi.js',      # MIDI, in the settings
                 'product-scenecap.js',      # a capture for each scene
                 'product-backup.js',      # everything the pedal keeps in one file, and back
                 'product-tone3000.css', 'product-tone3000.js',      # TONE3000 in the desktop program, with its official logos
                 'product-globals.css', 'product-globals.js',      # the settings for every preset, and the calibration of the input
                 'product-loudness.css', 'product-loudness.js', 'product-loudness-ui.js',      # the same volume for every preset
                 'tone3000/tone3000-logo.svg', 'tone3000/t3k-mark.svg',
                 'patchstorage/patchstorage-logo.png',      # Patchstorage's logo, on its button
                 'factory/HyperRig-Factory.hyperrig.json']      # the presets to start with, after a first install
INPUTS = {
    'web/index.html': '4090b0510aefb6a32faf548b37ea94f8092d7361860de6cc18ded567d1c978bc',
    'web/mini-fx-ui.js': 'e11c95735bb57ef6d694844dd1163574b86c21c58a9f1b1984a68ec02b2d0b20',
    'web/mini-profile.js': '5a9de5e93ffbefda575864c996dab76955f783a81e5dbfec21feb9c1bfcd2a5c',
    'web/mini-ui.js': '098dc4dc3453aa9d66c297f628ee765e8fd3b2dc5802f6537e31ee30012d8188',
    'web/nam2chip.js': 'af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183',
    'web/portable-startup.js': 'afb1cf343a267c0e7ecdd36e91195fffc8eb773ad2b90d4c6b5818998f48b9ec',
    'web/serial-open-timeout.js': 'fc21cdef1c767692fac77226a71e4e3e67d9cd63cab114cceb9e784ee7ce0faa',
    'web/tankmini.html': '72c5af2bcb0ad3ec4407088a91978b5f6e5795a3cd283d939f0db1f3c106cca2',
    'LICENSE.md': 'fbf763e6b656372647ea3950abc3d35feabe2148e697dc4215e1f92387e37a4c',
    'NOTICE.md': '02849a92a5a2ee4ced154650b52fcf316954fad41311cf55e9402567159b6ed8',
    'THIRD_PARTY_LICENSES.md': '50a9a2228e6225bc038b8d50f094be5698c4bbec563b4d2309c4fbec3447fcd8',
    'profile.json': 'fca16c4e06ae06afaf1ec61f85dc47f6f5a9bac2df433e7566ad83bbcacbac59',
}
# The policy: exact text, each once. These are hooks; the rules are in app/mini/mini-dev-rules.js, and only a
# development profile reaches them.
POLICY = [
    ('  const familyTransports = new Set(["usb-cdc", "ble-nus"]);\n',
     '  const familyTransports = new Set(["usb-cdc", "ble-nus"]);\n'
     '  const developmentBuild = () => profile.hardware_verified === false && !!profile.development &&\n'
     '    profile.development.kind === "source-build" && profile.development.commands_qualified_on_this_build === false;\n'
     '  const rules = root.HyperRigDevRules;\n'
     '  if (developmentBuild()) {\n'
     '    rules.families.forEach(c => familyCommands.add(c)); rules.queries.forEach(c => query.add(c));\n'
     '    if (profile.development.product) rules.productFamilies.forEach(c => familyCommands.add(c));\n'
     '  }\n'
     '  const product = () => developmentBuild() && profile.development.product || null;\n'
     '  const acceptBuild = lines => rules.build(lines, product());\n'),
    ('  function resetIdentity() { identified = false;', '  function resetIdentity() { rules.forget(); identified = false;'),
    ('    const result = inspectPong(pong, transport); identified', '    rules.forget(); const result = inspectPong(pong, transport); identified'),
    ('  const familyWriteEnabled = transport => profile.capabilities.read === true && profile.hardware_verified === true &&\n',
     '  const familyWriteEnabled = transport => developmentBuild() ? profile.capabilities.read === true &&\n'
     '    transport === "usb-cdc" && Array.isArray((profile.family_capabilities || {})[transport]) &&\n'
     '    profile.family_capabilities[transport].some(c => familyCommands.has(c)) :\n'
     '    profile.capabilities.read === true && profile.hardware_verified === true &&\n'),
    ('l.startsWith("ERR"))) { invalidate(command); return; }\n',
     'l.startsWith("ERR"))) {\n'
     '      if (timedOut || !developmentBuild() || !rules.refused(request, lines)) invalidate(command);\n      return;\n    }\n'),
    ('      if (request === "FXT") observed.types = parseTypes(lines);\n',
     '      if (developmentBuild() && rules.observe(request, lines, observed)) return;\n'
     '      if (request === "FXT") observed.types = parseTypes(lines);\n'),
    ('    // Only live catalog types and complete current serial chains are admitted.\n',
     '    if (developmentBuild()) { const known = rules.rule(value, state, product()); if (known !== null) return known; }\n'
     '    // Only live catalog types and complete current serial chains are admitted.\n'),
    ('    const state = {...observed, presets: observed.presets && {...observed.presets}};\n',
     '    const state = {...observed, presets: observed.presets && {...observed.presets}, blocks: observed.blocks &&\n'
     '      Object.fromEntries(Object.entries(observed.blocks).map(([id, b]) => [id, {...b}]))};\n'),
    ('      // Planning PSAVE changes the destination of a following scene save.\n',
     '      if (developmentBuild()) rules.plan(command, state);\n'
     '      // Planning PSAVE changes the destination of a following scene save.\n'),
    ('root.HyperRigMini = Object.freeze({profile, ', 'root.HyperRigMini = Object.freeze({profile, developmentBuild, product, acceptBuild, '),
]
PAGE = [
    ('<title>HyperRig for TANK MINI</title>', '<title>HyperRig for TANK-MINI</title>'),
    ('"tank-mini": "TANK MINI" }', '"tank-mini": "TANK-MINI" }'),
    ('"mini-v4-preview"', '"mini-source-build"'),
    ('"v4 preview"', '"source build"'),
    ('MINI v4 preview', 'MINI source build'),
    # The slot chosen for a new preset: Save goes there. It is forgotten as soon as a preset is loaded or saved.
    ('async function newPedalboard(slot = -1) {', 'let hrSlot = -1;\nasync function newPedalboard(slot = -1) {'),
    ('await loadChain(); await loadSnaps(); await loadPresets();\n  toast(slot >= 0 ?',
     'await loadChain(); await loadSnaps(); await loadPresets();\n'
     '  hrSlot = curPreset < 0 ? slot : -1; renderPresets();\n  toast(slot >= 0 ?'),
    # An export loads presets and scenes and reads them; every command of it is in the rules, and nothing is written to the pedal.
    ('if (!DEMO && !HyperRigMini.fullWriteEnabled()) { toast("Full preset export',
     'if (!DEMO && !(HyperRigMini.fullWriteEnabled() || HyperRigMini.developmentBuild())) { toast("Full preset export'),
    (': build it, then press its Save button.`', ': build it, then press Save.`'),
    ('if (how === "all" && !HyperRigMini.fullWriteEnabled())',
     'if (how === "all" && !(HyperRigMini.fullWriteEnabled() || HyperRigMini.developmentBuild()))'),
    ('<script src="mini-profile.js">', '<script src="mini-dev-rules.js"></script>\n<script src="mini-profile.js">'),
    ('if (curPreset < 0 || !presetName()) {', 'if (curPreset < 0 && hrSlot >= 0) { const n = hrSlot; await savePreset(n); return; }\n'
     '  if (curPreset < 0 || !presetName()) {'),
    ('$("snapSave").onclick = () => edCount() ? saveFlow()',
     '$("snapSave").onclick = () => edCount() ? saveFlow() : curPreset < 0 && hrSlot >= 0 ? savePreset(hrSlot)'),
    ('function renderPresets() {', 'function renderPresets() {\n  if (curPreset >= 0 || !S.connected) hrSlot = -1;'),
    (': S.pendName ? `<span data-noi18n>${esc(S.pendName)}</span>` : "No preset";',
     ': S.pendName ? (hrSlot >= 0 ? `<b class="pnum">${slotTxt(hrSlot)}</b>` : "") + `<span data-noi18n>${esc(S.pendName)}</span>` : hrSlot >= 0 ? `<b class="pnum">${slotTxt(hrSlot)}</b>New preset` : "No preset";'),
]
INDEX = [('location.replace("tankmini.html"+', 'location.replace("' + PAGE_FILE + '"+'),
         ('<a href="tankmini.html">Open HyperRig MINI</a>', '<a href="' + PAGE_FILE + '">Open HyperRig for TANK-MINI</a>'),
         ('<title>HyperRig MINI</title>', '<title>HyperRig for TANK-MINI</title>')]
# A product build: which build it is, three switches, banks of three and its gestures.
PRODUCT_PAGE = [
    ('"mini-source-build"', '"mini-product"'),
    ('"source build"', '"__VERSION__"'),
    ('MINI source build', '__VERSION__'),
    ('</head>', '<link rel="stylesheet" href="product-ui.css">\n<link rel="stylesheet" href="product-try.css">\n<link rel="stylesheet" href="product-tone3000.css">\n</head>'),
    ('<script src="mini-ui.js"></script>', '<script src="mini-ui.js"></script>\n<script src="product-parametric.js"></script>\n<script src="product-amp-knobs.js"></script>\n<script src="product-ui.js"></script>\n<script src="product-midi.js"></script>\n<script src="product-presetfile.js"></script>\n<script src="product-try.js"></script>\n<script src="product-share.js"></script>\n<script src="product-tone3000.js"></script>'),
    ('<span class="alpha">MINI</span>', '<span class="alpha">TANK-MINI</span>'),
    # The acoustic block (mini/product/acoustic.c): its name and picture, a group of its own, 6 and 12 strings as two buttons, its tips.
    ('  doubler:   { name: "Doubler",', '  acoustic:  { name: "Acoustic",   c: "#c98f4e", ico: \'<path d="m14.6 9.4 5.2-5.2M18.300 2.700l3 3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
     '<path d="M13.8 8.600c-1.700-1.600-4.100-1.200-5.100.400-.600 1-.300 2-1.600 2.300-3.500.800-4.900 4.500-2.300 7.200 2.800 2.600 6.500 1.200 7.300-2.300.300-1.300 1.300-1 2.300-1.600 1.600-1 1.900-3.300-.600-6Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>'
     '<circle cx="9.600" cy="13.800" r="1.500" fill="currentColor"/>\' },\n  doubler:   { name: "Doubler",'),
    ('  { key: "amp", name: "Amp", c: "#d9a441" },', '  { key: "amp", name: "Amp", c: "#d9a441" },\n  { key: "acoustic", name: "Acoustic", c: "#c98f4e" },'),
    ('const WEB_CAT = { pitch: "pitch",', 'const WEB_CAT = { acoustic: "acoustic", pitch: "pitch",'),
    ('const KNOB_TIP = { ', 'const KNOB_TIP = { "ir.lowcut_hz": "Low cut: takes the boom away, 12 dB an octave. It costs no processor time.", "ir.hicut_hz": "High cut: takes the fizz away, 12 dB an octave. It costs no processor time.", "acoustic.body_pct": "Body: how much of the wooden box is heard.", "acoustic.top_db": "Top: the brightness. Less for a bright pickup, more for a dark one.",\n'
     '  "acoustic.decay_pct": "Decay: how fast notes die, as on an acoustic. 0 keeps the sustain of the electric.", "acoustic.air_pct": "Air: the wood and the room around a near microphone.",\n'
     '  "acoustic.doubles_pct": "Doubles: the second strings. Only with 12 strings.",\n  '),
    ('function plabel0(n) { if (n === "sync")', 'function plabel0(n) { if (n === "strings") return { lab: "Strings", unit: "strings" }; if (n === "sync")'),
    ('  if (unit === "onoff") return v ? "On" : "Off";', '  if (unit === "strings") return v ? "12" : "6";\n  if (unit === "onoff") return v ? "On" : "Off";'),
    ('    if (unit === "onoff") {', '    if (unit === "onoff" || unit === "strings") {'),
    ('segSel($("edOs"), { opts: ["Off", "On"], val: it.p[p.idx] ? 1 : 0, label: lab, title: "Freeze: On holds the reverb tail.", onChange',
     'segSel($("edOs"), { opts: unit === "strings" ? ["6", "12"] : ["Off", "On"], val: it.p[p.idx] ? 1 : 0, label: lab, title: unit === "strings" ? "6 or 12 strings. 12 uses more of the pedal." : "Freeze: On holds the reverb tail.", onChange'),
    # The harmonizer (mini/product/harmonizer.c): its name and picture, in the group of the pitch; the key, the scale and the intervals by their names, its tips.
    ('  acoustic:  { name: "Acoustic",', '  harmonizer: { name: "Harmonizer", sn: "Harmony", c: "#b6d84f", ico: \'<path d="M3 7h18M3 12h18M3 17h18" stroke="currentColor" stroke-width="1.3" opacity=".5"/>'
     '<path d="M13.600 16.600V3.800" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><ellipse cx="11" cy="17" rx="2.900" ry="2.200" fill="currentColor"/><ellipse cx="11" cy="11.800" rx="2.900" ry="2.200" fill="currentColor"/>\' },\n'
     '  acoustic:  { name: "Acoustic",'),
    ('const WEB_CAT = { ', 'const WEB_CAT = { harmonizer: "pitch", '),
    ('const KNOB_TIP = { ', 'const KNOB_TIP = { "harmonizer.balance_pct": "Balance: 0 is the voice 1 alone, 50 both, 100 the voice 2 alone.", "harmonizer.mezcla_pct": "Mix: 0 is what is played alone, 50 both, 100 the voices alone.",\n  '),
    ('const SYNC = ["free",', 'const HR_LIST = { hrkey: { first: 0, names: ["C", "C# / Db", "D", "D# / Eb", "E", "F", "F# / Gb", "G", "G# / Ab", "A", "A# / Bb", "B"], tip: "The key of the song. The voices stay in its scale." },\n'
     '  hrscale: { first: 0, names: ["Major", "Minor", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian", "Harmonic minor", "Melodic minor", "Fixed, major", "Fixed, minor"],\n'
     '    tip: "The scale of the song. Fixed: every note has the same interval, whatever the key." },\n'
     '  hrvoice: { first: -7, names: ["Octave below", "7th below", "6th below", "5th below", "4th below", "3rd below", "2nd below", "Off", "2nd above", "3rd above", "4th above", "5th above", "6th above", "7th above", "Octave above"],\n'
     '    tip: "What this voice sings to the note that is played. Each voice uses more of the pedal." } };\n'
     'const HR_PARAM = { key: ["Key", "hrkey"], scale: ["Scale", "hrscale"], voice1: ["Voice 1", "hrvoice"], voice2: ["Voice 2", "hrvoice"] };\n'
     'const SYNC = ["free",'),
    ('function plabel0(n) { ', 'function plabel0(n) { if (HR_PARAM[n]) return { lab: HR_PARAM[n][0], unit: HR_PARAM[n][1] }; '),
    ('function fmtVal0(v, unit) {\n', 'function fmtVal0(v, unit) {\n  if (HR_LIST[unit]) return HR_LIST[unit].names[v - HR_LIST[unit].first] || v;\n'),
    ('    if (unit === "onoff" || unit === "strings") {', '    if (HR_LIST[unit]) {\n'
     '      hrList($("edOs"), { list: HR_LIST[unit], val: it.p[p.idx], label: lab, onChange: async nv => {\n'
     '        if (gone()) return live().p[p.idx];\n'
     '        const q = edQ();\n'
     '        const r = DEMO ? "FXP ok " + nv : reply(await Pedal.cmd(`FXP ${it.id} ${p.idx} ${nv}`, "FXP"), "FXP"), cur = live();\n'
     '        if (gone()) return nv;\n'
     '        if (r.startsWith("ERR")) { toast("Couldn\'t do that: " + errText(r), "err"); return cur.p[p.idx]; }\n'
     '        const okv = r.match(/^FXP ok (-?\\d+)/);\n'
     '        cur.p[p.idx] = okv ? +okv[1] : nv; if (mine()) ed.dataset.p = cur.p.join(",");\n'
     '        edMark("p", { id: it.id, idx: p.idx, v: cur.p[p.idx] }, q);\n'
     '        if (!DEMO) { await syncGen(); if (unit === "hrvoice") resReload(); }\n'
     '        return cur.p[p.idx];\n'
     '      } });\n'
     '      continue;\n'
     '    }\n'
     '    if (unit === "onoff" || unit === "strings") {'),
    # A gear that reads as one, alone: its name is the tip and the label.
    ('<button class="btn ico" id="setBtn" title="Settings"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm8.4 4.6-1.9-.4a6.8 6.8 0 0 1-.6 1.5l1.1 1.6-1.4 1.4-1.6-1.1c-.5.3-1 .5-1.5.6l-.4 1.9h-2l-.4-1.9a6.8 6.8 0 0 1-1.5-.6l-1.6 1.1-1.4-1.4 1.1-1.6c-.3-.5-.5-1-.6-1.5l-1.9-.4v-2l1.9-.4c.1-.5.3-1 .6-1.5L5.1 6.7l1.4-1.4 1.6 1.1c.5-.3 1-.5 1.5-.6l.4-1.9h2l.4 1.9c.5.1 1 .3 1.5.6l1.6-1.1 1.4 1.4-1.1 1.6c.3.5.5 1 .6 1.5l1.9.4v2Z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg></button>',
     '<button class="btn setb" id="setBtn" title="Settings" aria-label="Settings"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M10.23 4.61L10.62 1.69L13.38 1.69L13.77 4.61L15.97 5.52L18.31 3.73L20.27 5.69L18.48 8.03L19.39 10.23L22.31 10.62L22.31 13.38L19.39 13.77L18.48 15.97L20.27 18.31L18.31 20.27L15.97 18.48L13.77 19.39L13.38 22.31L10.62 22.31L10.23 19.39L8.03 18.48L5.69 20.27L3.73 18.31L5.52 15.97L4.61 13.77L1.69 13.38L1.69 10.62L4.61 10.23L5.52 8.03L3.73 5.69L5.69 3.73L8.03 5.52ZM12.0 8.7a3.3 3.3 0 1 0 0 6.6a3.3 3.3 0 1 0 0 -6.6Z" fill="currentColor" fill-rule="evenodd"/></svg></button>'),
    ('.rel span.relno { display: block;', '.rel span.relno { display: block; white-space: nowrap;'),
    ('.stfs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));', '.stfs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));'),
    ('.stfs { grid-template-columns: repeat(2, minmax(0, 1fr)); grid-template-rows: repeat(2, minmax(0, 1fr)); }',
     '.stfs { grid-template-columns: minmax(0, 1fr); grid-template-rows: repeat(3, minmax(0, 1fr)); }'),
    ('grid-template-columns: max-content repeat(4, minmax(0, 1fr)); gap: 6px 10px;', 'grid-template-columns: max-content repeat(3, minmax(0, 1fr)); gap: 6px 10px;'),
    ('.fsfg .fsfw { grid-column: span 4; }', '.fsfg .fsfw { grid-column: span 3; }'),
    ('.fscols { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }', '.fscols { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }'),
    ('.fspick { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }', '.fspick { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }'),
    ('  if (!miniIdentity.ok) { toast(miniIdentity.reason, "err"); await Pedal.disconnect(); return new Error(miniIdentity.reason); }\n',
     '  if (!miniIdentity.ok) { toast(miniIdentity.reason, "err"); await Pedal.disconnect(); return new Error(miniIdentity.reason); }\n'
     '  { const b = HyperRigMini.acceptBuild(await Pedal.cmd("HRID", "HRID", 1500));\n'
     '    if (!b.same) Log.ev("build_differs", b); hrOtherBuild(b.same ? null : b, HyperRigMini.product()); }\n'),
    ('const fmSlot = (bank, f) => (bank - 1) * 4 + f;', 'const fmSlot = (bank, f) => (bank - 1) * 3 + f;'),
    ('/ fm=(\\d),(\\d),(\\d),(\\d)/', '/ fm=(\\d),(\\d),(\\d+),(\\d)/'),
    ('mode=(\\w+) bank=(\\d) bypass=(\\d)/', 'mode=(\\w+) bank=(\\d+) bypass=(\\d)/'),
    ('const FM_COMBO = { bankDn: "A+B", bankUp: "C+D", mode: "B+C", tuner: "B+C" };',
     'const FM_COMBO = { bankDn: "A+B", bankUp: "B+C", mode: "from this page", tuner: "B+C" };'),
    ('`<span></span>${["A", "B", "C", "D"].map(', '`<span></span>${["A", "B", "C"].map('),
    ('<span>${T("Tuner: hold {tuner}", { tuner: FM_COMBO.tuner })}</span>',
     '<span>${T("Tuner: hold {tuner}", { tuner: FM_COMBO.tuner })}</span><span>Bluetooth: hold A+B 3 s on, 6 s off</span>'),
    ('if (pk) pk.innerHTML = [0, 1, 2, 3].map(f =>', 'if (pk) pk.innerHTML = [0, 1, 2].map(f =>'),
    ('aria-label="Footswitch ${f + 1}">${f + 1}</button>`).join("");\n}', 'aria-label="Footswitch ${"ABC"[f]}">${"ABC"[f]}</button>`).join("");\n}'),
    ('el.innerHTML = [0, 1, 2, 3].map(f => {\n    const t = fsTab[f], dbl', 'el.innerHTML = [0, 1, 2].map(f => {\n    const t = fsTab[f], dbl'),
    ('<span class="num" aria-hidden="true">${f + 1}</span>Footswitch ${f + 1}</h3>', '<span class="num" aria-hidden="true">${"ABC"[f]}</span>Footswitch ${"ABC"[f]}</h3>'),
    ('  for (let f = 0; f < 4; f++) for (let g = 0; g < 3; g++) {\n    const box = $("fsC" + f + g)',
     '  for (let f = 0; f < 3; f++) for (let g = 0; g < 3; g++) {\n    const box = $("fsC" + f + g)'),
    ('let act = [0, 1, 2, 3].map(stActive);', 'let act = [0, 1, 2].map(stActive);'),
    ('const tiles = fac ? [0, 1, 2, 3].map(f => {', 'const tiles = fac ? [0, 1, 2].map(f => {'),
    ('  }) : [0, 1, 2, 3].map(f => {\n    const A = stAct(', '  }) : [0, 1, 2].map(f => {\n    const A = stAct('),
    ('<span class="num">${t.f + 1}</span>', '<span class="num">${"ABC"[t.f]}</span>'),
    ('T("The pedal: 4 footswitches with a light ring each.")', '"The pedal: three footswitches, A, B and C."'),
]
# A byte of a line can be lost on the way to the pedal: it answers with fewer bytes than it was sent (seen on the pedal,
# 2026-11-24, an IR of 4040 samples stopped at byte 1620). The same piece again, at the same place: the checksum at the end
# still covers the whole. And what the pedal said is in the error, which had kept it to itself.
PRODUCT_PAGE += [
    ('    const okp = `OK ${prefix} ${off} `, r = reply(await Pedal.cmd(`${prefix} ${off} ${hex(ch)}`, l => l.startsWith(okp) || l.startsWith("ERR"), 1500), okp);\n'
     '    if (!r.startsWith("OK") || +r.split(" ").pop() !== ch.length) throw new Error(`transfer failed at byte ${off}`);\n',
     '    const okp = `OK ${prefix} ${off} `;\n'
     '    let r = "";\n'
     '    for (let turn = 0; turn < 4; turn++) {\n'
     '      r = reply(await Pedal.cmd(`${prefix} ${off} ${hex(ch)}`, l => l.startsWith(okp) || l.startsWith("ERR"), 1500), okp);\n'
     '      if (r.startsWith("OK") && +r.split(" ").pop() === ch.length) break;\n'
     '      Log.ev("piece_again", { what: prefix, at: off, of: ch.length, turn, rep: String(r).slice(0, 80) });\n'
     '    }\n'
     '    if (!r.startsWith("OK") || +r.split(" ").pop() !== ch.length)\n'
     '      throw new Error(`transfer failed at byte ${off}` + (r ? ` (${r.slice(0, 60)})` : " (no answer)"));\n'),
]
# A scene belongs to a preset that is on the pedal: a new preset is saved first, with its scene, and the page says both.
PRODUCT_PAGE += [
    ('  Log.act("snap_save", { k });\n',
     '  Log.act("snap_save", { k });\n'
     '  if (!DEMO && curPreset < 0 && hrSlot >= 0) { const n = hrSlot; await savePreset(n); if (curPreset !== n) return; }\n'),
    ('toast(`Scene ${k + 1} saved to preset ${Math.floor(pn / PRESETS_PER_BANK) + 1}${SLOT(pn)}.`, "ok");',
     'toast(`Scene ${k + 1} and preset ${Math.floor(pn / PRESETS_PER_BANK) + 1}${SLOT(pn)} are saved.`, "ok");'),
]
# A new preset is empty: the amp the firmware puts there is taken out, and is added like any block.
PRODUCT_PAGE += [
    ('  Log.act("preset_new", { slot }); edClear();\n  await Pedal.cmd("PNEW", "PNEW");\n',
     '  Log.act("preset_new", { slot }); edClear();\n  await Pedal.cmd("PNEW", "PNEW");\n  await Pedal.cmd("AMPX 0", "AMPX");\n'),
    ('S.ampPresent = 1; S.sel = null;', 'S.ampPresent = 0; S.sel = null;'),
]
# An imported preset clears the chain first: what the pedal has then is read, so that the policy can judge the next commands by it.
PRODUCT_PAGE += [
    ('    if (pioPairErr(r) || (line === "PNEW" && !/^PNEW ok/.test(r)))',
     '    if (line === "PNEW" && /^PNEW ok/.test(r)) { await send("FXS", PIO_FXS_END, 2500); await send("GAIN", "GAIN"); await send("SNAPS", "SNAPS"); }\n'
     '    if (pioPairErr(r) || (line === "PNEW" && !/^PNEW ok/.test(r)))'),
]
# The tuner that the loading of a try switched on is the mute, not the pedal's own (hrTry.muted, in app/mini/product-try.js): the page does not open its tuner for it.
PRODUCT_PAGE += [
    ('  if (tu && !S.saveMute) {', '  if (tu && !S.saveMute && !(globalThis.hrTry && hrTry.muted)) {'),
]
# The pedal has no memory for its tuner beside a full preset: said in words (hrTunerRoom, in app/mini/product-ui.js).
PRODUCT_PAGE += [
    ('  if (/^TUNE (?:off|apagado)/.test(l) && tuFromPedal) { tuHide(); return; }\n',
     '  if (/^TUNE (?:off|apagado)/.test(l) && tuFromPedal) { tuHide(); return; }\n  hrTunerRoom(/ nomem$/.test(l));\n'),
]
# A delay longer than the memory takes: the longest that fits is found and said, not just that it did not (hrLongest, in app/mini/product-ui.js).
PRODUCT_PAGE += [
    ('      const r = DEMO ? "FXP ok " + nv : reply(await Pedal.cmd(`FXP ${it.id} ${p.idx} ${nv}`, "FXP"), "FXP");\n',
     '      const turn = dly && p.idx === 0 ? hrTimeTurned() : 0;\n'
     '      let r = DEMO ? "FXP ok " + nv : reply(await Pedal.cmd(`FXP ${it.id} ${p.idx} ${nv}`, "FXP"), "FXP");\n'
     '      if (turn && isMemErr(r)) r = await hrLongest(it.id, nv, r, turn);\n'),
]
# A capture for each scene (app/mini/product-scenecap.js): where a capture is chosen, read, uploaded and shown, and in the files of presets.
PRODUCT_PAGE += [
    ('<script src="product-ui.js"></script>', '<script src="product-scenecap.js"></script>\n<script src="product-ui.js"></script>'),
    ('Log.act(cap ? "capture_use" : "ir_use", { slot: i, name, from: "menu" });\n  busy(true, "Loading…", .5);\n  let x; const q = edQ();\n  try { x = DEMO ? "ok" : reply(await Pedal.cmd(`${cap ? "CLOAD" : "ILOAD"} ${i}`, cap ? "CLOAD" : "ILOAD", 8000), cap ? "CLOAD" : "ILOAD"); }',
     'Log.act(cap ? "capture_use" : "ir_use", { slot: i, name, from: "menu" });\n  busy(true, "Loading…", .5);\n  let x; const q = edQ();\n  try { x = DEMO ? "ok" : cap ? await hrCapUse(i) : reply(await Pedal.cmd(`ILOAD ${i}`, "ILOAD", 8000), "ILOAD"); }'),
    ('Log.act(cap ? "capture_use" : "ir_use", { slot: i, name: r[1] });\n      let x; const q = edQ();\n      try { x = DEMO ? "ok" : reply(await Pedal.cmd(`${cap ? "CLOAD" : "ILOAD"} ${i}`, cap ? "CLOAD" : "ILOAD", 8000), cap ? "CLOAD" : "ILOAD"); }',
     'Log.act(cap ? "capture_use" : "ir_use", { slot: i, name: r[1] });\n      let x; const q = edQ();\n      try { x = DEMO ? "ok" : cap ? await hrCapUse(i) : reply(await Pedal.cmd(`ILOAD ${i}`, "ILOAD", 8000), "ILOAD"); }'),
    ('S.snap = k; renderPerf(); S.sel = S.sel; document.querySelector("#editor").dataset.id = ""; await loadChain();',
     'S.snap = k; renderPerf(); S.sel = S.sel; document.querySelector("#editor").dataset.id = ""; await loadChain(); if (hrCapAny()) await hrCapShown();'),
    ('  S.snaps[k] = 1; S.snap = k; renderPerf();\n', '  S.snaps[k] = 1; S.snap = k; renderPerf(); await hrCapRead();\n'),
    ('  await loadSnapNames();\n  renderPerf();\n}', '  await loadSnapNames();\n  await hrCapRead();\n  renderPerf();\n}'),
    ('setModel(backName); S.capSlot = back; restored = true; } } catch (e) {                       }\n  }\n  if (!restored && jobs.some(j => j.st === "ok")) edMark("other", null, qc);', 'setModel(backName); S.capSlot = back; restored = true; } } catch (e) {                       }\n  }\n  if (!restored && jobs.some(j => j.st === "ok")) { if (!DEMO && S.connected) await hrCapCame(); edMark("other", null, qc); }'),
    ('    try { x = reply(await Pedal.cmd(`CLOAD ${slot}`, "CLOAD", 8000), "CLOAD"); }', '    try { x = await hrCapUse(slot); }'),
    ('const ampSig = () => `${S.amp}|${S.aeqOk}|${!!S.cinOk}|${ctHasScenes() ? 1 : 0}`;', 'const ampSig = () => `${S.amp}|${S.aeqOk}|${!!S.cinOk}|${ctHasScenes() ? 1 : 0}|${hrCapSig()}`;'),
    ('<h3>NAM Capture ${ctBadge()}</h3>', '<h3>NAM Capture ${hrCapCan() ? "" : ctBadge()}</h3><div class="hrcap" id="hrCapSeg"></div>'),
    ('  $("ampCal").onclick = () => openCalib(S.capSlot);', '  $("ampCal").onclick = () => openCalib(S.capSlot);\n  hrCapPanel();'),
    ('  $("libCt").innerHTML = ctHasScenes()', '  $("libCt").innerHTML = cap && hrCapLib() ? hrCapLib() : ctHasScenes()'),
    ('function ctSceneNote(cap) { if (', 'function ctSceneNote(cap) { if (cap && hrCap.of) return; if ('),
    ('  st.caps = pioLib(await send("CLIST", PIO_LIBEND("CLIST"), 3000), true);\n', '  st.caps = pioLib(await send("CLIST", PIO_LIBEND("CLIST"), 3000), true);\n  st.scap = await hrCapOf(send);\n  if (st.scap) st.caps.cur = st.scap.own;\n'),
    ('scenes.push({ index: k, name: (st.names && st.names[k]) || "",', 'scenes.push({ index: k, name: (st.names && st.names[k]) || "", ...(st.scap && st.scap.of[k] >= 0 && pioRef(st.caps, st.scap.of[k], att.cap) ? { capture: pioRef(st.caps, st.scap.of[k], att.cap) } : {}),'),
    ('captures: amp.present && capRef ? [capRef] : []', 'captures: amp.present ? [capRef, ...scenes.map(s => s.capture)].filter((r, i, all) => r && all.findIndex(x => x && x.name === r.name && x.bytes === r.bytes) === i) : []'),
    ('    if (u.cap >= 0) capS.set(u.cap, x.st.caps.list.find(e => e.slot === u.cap));\n', '    if (u.cap >= 0) capS.set(u.cap, x.st.caps.list.find(e => e.slot === u.cap));\n    for (const c of hrCapUsed(x.st)) capS.set(c, x.st.caps.list.find(e => e.slot === c));\n'),
    ('  walk(snd.chain);\n  return out;\n}', '  walk(snd.chain);\n  if (amp.present !== false) for (const s of pioArr(snd.scenes)) if (pioObj(s)) add(s.capture, "capture");\n  return out;\n}'),
    ('    scenes.push(st);\n', '    if (pioObj(s.capture) && present && ctx.scap) { const m = match(s.capture, ctx.caps); if (m) st.cap = m.slot; else W.warn.push({ k: "The capture \\"{name}\\" of scene {n} isn\'t on this pedal: the scene has the preset\'s.", name: pioText(s.capture.name, 40), n: k + 1 }); }\n    scenes.push(st);\n'),
    ('  apply(base, -1);\n', '  for (const s of scenes) if (s.cap != null) cmd(`SNAPCAP ${s.k} ${s.cap}`, "SNAPCAP", { tmo: 8000 });\n  apply(base, -1);\n'),
    ('const pioCtxOf = (caps, irs) => ({ types: S.types, caps, irs,', 'const pioCtxOf = (caps, irs) => ({ types: S.types, caps, irs, scap: !DEMO && !!hrCap.of,'),
]
# Everything the pedal keeps in one file (app/mini/product-backup.js): a file that has it all is offered as that, wherever it is opened.
PRODUCT_PAGE += [
    ('<script src="product-try.js"></script>', '<script src="product-try.js"></script>\n<script src="product-backup.js"></script>'),
    ('  const r = pioParse(text);\n  if (!r.ok) { Log.act("preset_import",', '  if (!DEMO && HyperRigPresetFile.isBackup(text)) return hrRestore(text);\n  const r = pioParse(text);\n  if (!r.ok) { Log.act("preset_import",'),
]
# All the presets of a file at once (hrImportAll, in app/mini/product-ui.js); the name of one without a slot beside the slot it is meant for; after an export the
# scene that was on is chosen again, which the rules allow only when the scenes are known; the pedal's names are plain letters.
PRODUCT_PAGE += [
    # A scene of an import stays in the pedal's memory only while no preset is loaded there: asked before each one.
    ('    const r = pioFind(await send(line, c.pre, c.tmo || 1500), c.pre);\n',
     '    if (!DEMO && /^(?:SNAPSAVE|SNAPNAME|PCOLOR) /.test(line)) await hrStillNew(send);\n    const r = pioFind(await send(line, c.pre, c.tmo || 1500), c.pre);\n'),
    ('  const pre = r.presets.length > 1 ? await pioChoose(r.presets) : r.presets[0];\n',
     '  let pre = r.presets[0];\n'
     '  if (r.presets.length > 1) {\n'
     '    const how = DEMO ? "one" : await uiChoice({ title: "Presets in this file: " + r.presets.length, body: "Import all of them, each to its own slot, or one of them.",\n'
     '      choices: [{ label: "All of them", value: "all", primary: true }, { label: "One of them", value: "one" }] });\n'
     '    if (how === "all") return hrImportAll(r);\n'
     '    pre = how === "one" ? await pioChoose(r.presets) : null;\n'
     '  }\n'),
    ('if (r.startsWith("PLOAD ok") && snap0 >= 0) await Pedal.cmd(`SNAP ${snap0}`, "SNAP "); }',
     'if (r.startsWith("PLOAD ok") && snap0 >= 0) { await Pedal.cmd("SNAPS", "SNAPS"); await Pedal.cmd(`SNAP ${snap0}`, "SNAP "); } }'),
    ('await Pedal.cmd(`PLOAD ${back}`, "PLOAD", 8000); if (snap0 >= 0) await Pedal.cmd(`SNAP ${snap0}`, "SNAP "); }',
     'await Pedal.cmd(`PLOAD ${back}`, "PLOAD", 8000); if (snap0 >= 0) { await Pedal.cmd("SNAPS", "SNAPS"); await Pedal.cmd(`SNAP ${snap0}`, "SNAP "); } }'),
    ('  const nm = (st.meta.name || base).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\\x20-\\x7e]/g, "_").trim() || base;',
     '  const nm = pioAscii(st.meta.name || base, 40) || pioAscii(base, 40) || "Capture";'),
    ('`CSAVE ${slot} ${name.slice(0, 23)}`', '`CSAVE ${slot} ${pioAscii(name, 23) || "Capture"}`'),
    ('`ISAVE ${saveSlot} ${f.name.replace(/\\.wav$/i, "").slice(0, 23)}`', '`ISAVE ${saveSlot} ${pioAscii(f.name.replace(/\\.wav$/i, ""), 23) || "Cab IR"}`'),
    ('`ISAVE ${j.slot} ${j.f.name.replace(/\\.wav$/i, "").slice(0, 23)}`', '`ISAVE ${j.slot} ${pioAscii(j.f.name.replace(/\\.wav$/i, ""), 23) || "Cab IR"}`'),
]
# Saving in one line (hrSaveBar, hrSave and hrSaveTo, in app/mini/product-ui.js): the page's own bar and its disks say neither what is saved nor where. A preset
# without a slot is a new one, not "no preset"; the slot it is meant for shows it; an empty scene is one to add.
PRODUCT_PAGE += [
    ('  const n = edCount(), bar = $("saveBar"); if (!bar) return;',
     '  if (typeof hrSaveBar === "function" && hrSaveBar()) return;\n  const n = edCount(), bar = $("saveBar"); if (!bar) return;'),
    ('$("saveGo").onclick = () => saveFlow();', '$("saveGo").onclick = () => !PH && !DEMO && typeof hrSave === "function" ? hrSave() : saveFlow();'),
    ('    toast("Pick a slot to save this preset.", "err");\n', '    if (!PH && !DEMO) { await hrSaveTo(); return; }\n    toast("Pick a slot to save this preset.", "err");\n'),
    ('"New preset: build your pedalboard, then save it to a slot in the list.", "ok");', '"New preset: build it, then press Save.", "ok");'),
    ('toast("Named. Save the preset to a slot so the name stays on the pedal.", "warn");', 'toast("Named. Save the preset to keep the name.", "info");'),
    ('`Scene ${k + 1} is ready, but there is no preset yet: save the preset to a slot in the list so it stays on the pedal.`, "warn");',
     '`Scene ${k + 1} added. Save the preset to keep it.`, "info");'),
    ('`Saved to scene ${k0 + 1} of preset ${slotTxt(curPreset)}.`', '`Saved to ${slotTxt(curPreset)}, scene ${k0 + 1}.`'),
    (': "No preset";', ': S.connected ? "New preset" : "No preset";'),
    ('${LANG === "es" ? "empty" : "empty"}', '+ add'),
    ('T("Empty. Click to save here.")', 'T("Click to add this scene, with the sound as it is now.")'),
    ('d.className = "pslot" + (n === curPreset ? " cur" : ""); d.dataset.preset = n;',
     'const pend = !PH && curPreset < 0 && n === hrSlot; d.className = "pslot" + (n === curPreset || pend ? " cur" : "") + (pend ? " pend" : ""); d.dataset.preset = n;'),
    (': "empty"}</span>', ': pend ? `<span data-noi18n>${esc(S.pendName || "New preset")}</span>` : "empty"}</span>'),
    ('p ? loadPreset(n) : newPedalboard(n), PH', 'p ? loadPreset(n) : pend ? null : newPedalboard(n), PH'),
]
# The effects of HyperRig from the id 40 on (mini/product/effects.c): what each looks like, its group where it is not the firmware's, its tips
# and the words of its knobs are in app/mini/effects.json.
EFFECTS = json.loads((ROOT / 'app/mini/effects.json').read_bytes())


def effect_patches(table):
    looks = ''.join('  %s: { name: %s, c: %s, ico: %s },\n' % (n, *(json.dumps(e[k]) for k in ('name', 'colour', 'icon'))) for n, e in table['effects'].items())
    groups = ''.join(f', {n}: "{e["group"]}"' for n, e in table['effects'].items() if 'group' in e)
    labels = ''.join(f' {n}: {json.dumps(v)},' for n, v in table['labels'].items())
    tips = ''.join(f'{json.dumps(n + "." + k)}: {json.dumps(v)}, ' for n, e in table['effects'].items() for k, v in e['tips'].items())
    return [('  ir:        { name: "Cab IR",', looks + '  ir:        { name: "Cab IR",'), ('doubler: "pitch" };', f'doubler: "pitch"{groups} }};'),
            ('sens: "Sensitivity",', 'sens: "Sensitivity",' + labels), ('"basseq.graves_db": "Bass: 60 Hz shelf', tips + '"basseq.graves_db": "Bass: 60 Hz shelf')]


PRODUCT_PAGE += effect_patches(EFFECTS)
# What the footswitches do is one choice (hrSetups, in app/mini/product-ui.js), and not four setups of a pedal with four switches. In live mode the firmware's A, B and C take the first block of the kinds 0, 1 and 2 of the effects:
# reverb, delay and modulation (tools/check_mini_panel.py; the kinds in tools/check_mini_effect_block.py). The page said they were unassigned.
PRODUCT_PAGE += [
    ('const fmSecOf = (f, pedal) => pedal === "tank-mini" ? null : (FM_FS[pedal] || [])[f];', 'const fmSecOf = (f, pedal) => pedal === "tank-mini" ? [0, 1, 2][f] ?? null : (FM_FS[pedal] || [])[f];'),
    ('["A (unassigned)", "B (unassigned)", "C (unassigned)"]', '["First reverb", "First delay", "First modulation"]'),
    ('pitchpro: 2, amp_clean: 3', 'pitchpro: 2, rotary: 2, amp_clean: 3'),
    ('  if (fsLay === 0) {  ', '  if (fsLay === 0 && typeof hrFactory === "function") { hrFactory(el); return; }\n  if (fsLay === 0) {  '),
    ('  const el = $("fsQuick"); if (!el || !fsTab) return;\n', '  const el = $("fsQuick"); if (!el || !fsTab) return;\n  if (typeof hrSetups === "function") { hrSetups(el); return; }\n'),
    ('  else if (d.fq) fsQuickApply(d.fq);', '  else if (d.fq) typeof hrApply === "function" ? void hrApply(d.fq) : fsQuickApply(d.fq);'),
    ('  c.title = T("Click to switch Preset / Live");\n', '  if (typeof hrModes === "function") { hrModes(c); return; }\n  c.title = T("Click to switch Preset / Live");\n'),
    ('$("fmChip").onclick = () => { if (S.fm) fmSetMode(!S.fm.live); };', '$("fmChip").onclick = () => void fsOpen();'),
]
# A NAM capture that keeps knobs (app/mini/product-parametric.js, product-amp-knobs.js): its own conversion, and the amp's controls by the names and numbers of its knobs.
PRODUCT_PAGE += [
    ('res = await Nam2Chip.convertAsync(text, { name: base,', 'res = await hrNamConvert(text, { name: base,'),
    ('${st.macs} MAC/sample; calibration ${', '${st.macs} MAC/sample${hrNamInfo(res)}; calibration ${'),
    ('  if (unit === "dB10") return (v > 0 ? "+" : "")', '  if (/^hrknob\\d$/.test(unit)) return hrKnobText(+unit.slice(6), v);\n  if (unit === "dB10") return (v > 0 ? "+" : "")'),
    ('unit: "dB10", label: AEQ_NAMES[i], step: 5,', 'unit: hrKnobOf(i) ? "hrknob" + i : "dB10", label: hrKnobName(i), step: 5,'),
    ('k.el.title = aeqTitle(i, R.hz);', 'k.el.title = hrKnobTitle(i, R.hz);'),
    ('<p class="anote">${esc(trimNote())}</p>', '<p class="anote">${esc(trimNote() + hrKnobNote())}</p>'),
    ('(S.aeqDrv || DEMO ? " " + T("Gain adds to it for more breakup; the meter shows both.") : "")',
     '((S.aeqDrv || DEMO) && !hrKnobOf(AEQ_DRIVE) ? " " + T("Gain adds to it for more breakup; the meter shows both.") : "")'),
    ('function setModel(n) { S.model = n;', 'function setModel(n) { S.model = n; if (typeof hrKnobsSoon === "function") hrKnobsSoon();'),
]
# The pedal's USB numbers: the vendor of the chip with HyperRig's product, and 3654 of the builds before the released 0.2.0.
PRODUCT_PAGE += [
    ('      || ps.find(x => (inf(x).usbVendorId || 0) === 0x3654) ||',
     '      || ps.find(x => (inf(x).usbVendorId === 0x4c4a && inf(x).usbProductId === 0x5155) || inf(x).usbVendorId === 0x3654) ||'),
]
# Eight scenes: SNAPS has a digit for each, and the page takes as many as it says. Those that are there are shown, and one to add.
PRODUCT_PAGE += [
    ('  for (let k = 0; k < 4; k++) {\n    const b = document.createElement("button");\n    const nm = S.snaps[k] ? S.snapNames[k] || "" : "";',
     '  for (let k = 0; k < S.snaps.length; k++) {\n    if (!S.snaps[k] && k !== S.snaps.indexOf(0)) continue;\n    const b = document.createElement("button");\n    const nm = S.snaps[k] ? S.snapNames[k] || "" : "";'),
    ('  const h = $("snaps"); h.innerHTML = "";', '  const h = $("snaps"); h.innerHTML = ""; h.classList.toggle("many", S.snaps.filter(Boolean).length > 3);'),
    ('return tab ? [0, 1, 2, 3].filter(f => tab[f][0][0] === 1 && tab[f][0][1] === k) : [];', 'return tab ? [0, 1, 2, 3].filter(f => tab[f][0][0] === 1 && hrScene(tab[f][0][1]) === k) : [];'),
    ('m = l.match(/SNAPS (\\d)(\\d)(\\d)(\\d) (?:current|actual)=(-?\\d+)/);', 'm = l.match(/SNAPS (\\d{4}|\\d{8}) (?:current|actual)=(-?\\d+)/);'),
    ('if (m) { S.snaps = [1, 2, 3, 4].map(i => +m[i]); S.snap = +m[5]; }', 'if (m) { S.snaps = [...m[1]].map(Number); S.snap = +m[2]; }'),
    ('  const nn = ["", "", "", ""];', '  const nn = S.snaps.map(() => "");'),
    ("const mm = l.match(/^SNAPNAME ([0-3]) '(.*)'$/);", "const mm = l.match(/^SNAPNAME ([0-7]) '(.*)'$/);"),
    ('  const valid = [0, 1, 2, 3].filter(k => S.snaps[k]), k0 = S.snap,', '  const valid = S.snaps.map((v, k) => k).filter(k => S.snaps[k]), k0 = S.snap,'),
    ('  if (t === 1) sel([0, 1, 2, 3].map(k => ["Scene " + (k + 1), k]), a, 1);', '  if (t === 1) sel([0, 1, 2, 3, 4, 5, 6, 7].map(k => ["Scene " + (k + 1), k]), a, 1);'),
    ('    sel([["no scene", 255], ...[0, 1, 2, 3].map(k => ["then scene " + (k + 1), k])], b, 2);', '    sel([["no scene", 255], ...[0, 1, 2, 3, 4, 5, 6, 7].map(k => ["then scene " + (k + 1), k])], b, 2);'),
    ('  if (t === 1) return S.snaps[a] && S.snapNames[a] ? { big:', '  if (t === 1 && hrScene(a) !== a) return stAct([1, hrScene(a), 1]);\n  if (t === 1) return S.snaps[a] && S.snapNames[a] ? { big:'),
    ('return (x[0] === 1 && S.snap === x[1] && S.snaps[x[1]]) ||', 'return (x[0] === 1 && S.snap === hrScene(x[1]) && S.snaps[hrScene(x[1])]) ||'),
    ('  if (t === 1) { if (S.snaps[a]) await goSnap(a); else toast(`Scene ${a + 1} is empty in this preset.`, "err"); }',
     '  if (t === 1) { const k = hrScene(a); if (S.snaps[k]) await goSnap(k); else toast(`Scene ${k + 1} is empty in this preset.`, "err"); }'),
    ('    const ks = [0, 1, 2, 3].filter(k => S.snaps[k]);', '    const ks = S.snaps.map((v, k) => k).filter(k => S.snaps[k]);'),
    ('  const ns = [0, 1, 2, 3].filter(k => p[4] >> k & 1).length;', '  const ns = [0, 1, 2, 3, 4, 5, 6, 7].filter(k => p[4] >> k & 1).length;'),
    ('.match(/^SNAPS (\\d)(\\d)(\\d)(\\d) /);', '.match(/^SNAPS (\\d{4}|\\d{8}) /);'),
    ('  if (!m || m.slice(1, 5).some(x => x !== "0")) return;', '  if (!m || /[^0]/.test(m[1])) return;'),
    ('scenes: [null, null, null, null], names: ["", "", "", ""], miss: [0, 0, 0, 0] };', 'scenes: Array(8).fill(null), names: Array(8).fill(""), miss: Array(8).fill(0) };'),
    ('  const sn = /^SNAPS ([01])([01])([01])([01]) (?:current|actual)=(-?\\d+)/.exec(', '  const sn = /^SNAPS ([01]{4}|[01]{8}) (?:current|actual)=(-?\\d+)/.exec('),
    ('  st.snaps = sn ? [1, 2, 3, 4].map(i => sn[i] === "1") : [false, false, false, false];', '  st.snaps = sn ? [...sn[1]].map(x => x === "1") : Array(8).fill(false);'),
    ('  st.active = sn ? +sn[5] : -1;', '  st.active = sn ? +sn[2] : -1;'),
    ("const m = /^SNAPNAME ([0-3]) '(.*)'$/.exec(l); if (m) st.names[+m[1]] = m[2]; }", "const m = /^SNAPNAME ([0-7]) '(.*)'$/.exec(l); if (m) st.names[+m[1]] = m[2]; }"),
    ('  for (let k = 0; k < 4; k++) {\n    const sc = st.scenes && st.scenes[k]; if (!sc) continue;', '  for (let k = 0; k < 8; k++) {\n    const sc = st.scenes && st.scenes[k]; if (!sc) continue;'),
    ('  for (let k = 0; k < 4; k++) {\n    if (!st.snaps[k]) continue;', '  for (let k = 0; k < 8; k++) {\n    if (!st.snaps[k]) continue;'),
    ('    if (k == null || k < 0 || k > 3 || seen.has(k)) { W.other++; continue; }', '    if (k == null || k < 0 || k > 7 || seen.has(k)) { W.other++; continue; }'),
    ('It has 4 scenes: the same blocks with other settings.', 'It has up to 8 scenes: the same blocks with other settings.'),
    ('aria-label="Scenes: each preset has 4 (the same blocks, with their own on/off and knob settings)"', 'aria-label="Scenes: each preset has up to 8 (the same blocks, with their own on/off and knob settings)"'),
    ('T("Each preset has <b>4 scenes</b>: same blocks, other settings. <b>Save</b> keeps changes.")', 'T("Each preset has up to <b>8 scenes</b>: same blocks, other settings. <b>Save</b> keeps changes.")'),
    ('  if (!r.startsWith("SNAPSAVE ok")) { toast("Couldn\'t do that: " + r, "err"); return; }',
     '  if (/no room/.test(r)) { toast("There is no room for this scene in the preset. Take a block or a scene away.", "err"); return; }\n  if (!r.startsWith("SNAPSAVE ok")) { toast("Couldn\'t do that: " + r, "err"); return; }'),
]
# A chain without room says so in plain words, and the number of blocks that still fit counts the places too (hrNoRoom and hrRoom, in
# app/mini/product-ui.js).
PRODUCT_PAGE += [
    ('cm.more === "more" ? T("~{n} more", { n: cm.n }) : T(cm.more === "almost" ? "almost full" : "full");',
     'cm.more === "more" && hrRoom() ? T("~{n} more", { n: Math.min(cm.n, hrRoom()) }) : T(cm.more === "almost" && hrRoom() ? "almost full" : "full");'),
    ('    if (!gate.allowed) { toast(gate.reason, "err"); return null; }',
     '    if (!gate.allowed) { hrNoRoom(`FXA ${hrBank(curSegs(), loc)} 99 ${type}`, gate.reason); return null; }'),
    ('    if (!gate.allowed) { toast("Chain edit unavailable: " + gate.reason, "err"); return false; }',
     '    if (!gate.allowed) { hrNoRoom(gate.command, gate.reason); return false; }'),
]
# MIDI is a setting of the pedal as the others are (app/mini/product-midi.js): read with them, changed at once, kept by Save to pedal, put back when it is not.
PRODUCT_PAGE += [
    ('const GD_LIVE = /^(GEQ \\d|', 'const GD_LIVE = /^(MIDI =|GEQ \\d|'),
    ('function gdLinesG() {\n  const L = [];', 'function gdLinesG() {\n  const L = typeof hrMidiLines === "function" ? hrMidiLines() : [];'),
    ('  if (!keepSnap) gdSnap.g = gdLinesG();',
     '  if (typeof hrMidiSay === "function" && S.connected && !DEMO && !hrOther.kind) await hrMidiSay("").catch(() => null);\n  if (!keepSnap) gdSnap.g = gdLinesG();'),
]
# A chain without a capture uses both sections of the firmware, ten blocks each and sixteen in all: where they meet (hrView, hrArrange and the others, in
# app/mini/product-ui.js) is found for each change, and not shown.
PRODUCT_PAGE += [
    ('const curSegs = () => buildSegs(S.chain, S.mix, S.xo, S.xeq);',
     'const curSegs = () => { const segs = buildSegs(S.chain, S.mix, S.xo, S.xeq); return typeof hrView === "function" ? hrView(segs) : segs; };'),
    ('  for (const b of PQ) for (const id of tid[b]) {\n    if (placed.has(id)) continue;', '  for (const [b, id] of hrMoves(sim, tid, placed)) {\n    if (placed.has(id)) continue;'),
    ('  const ns = normalize(live), n = grpCount(ns);\n  if (n.P > FX_MAXGRP || n.Q > FX_MAXGRP) return { err: "limit", bank };',
     '  const ns = hrArrange(live), n = ns && grpCount(ns);\n  if (!ns || n.P > FX_MAXGRP || n.Q > FX_MAXGRP) return { err: "limit", bank };'),
    ('  if (pv.err === "limit") return `Limit: ${FX_MAXGRP} splits ${pv.bank === "Q" ? "after" : "before"} the amp`;',
     '  if (pv.err === "limit") return S.ampPresent ? `Limit: ${FX_MAXGRP} splits ${pv.bank === "Q" ? "after" : "before"} the amp` : "No room for this split";'),
    ('const SPLIT_LIMIT_MSG = () => `Limit: ${FX_MAXGRP} splits per section.`;',
     'const SPLIT_LIMIT_MSG = () => S.ampPresent ? `Limit: ${FX_MAXGRP} splits per section.` : "There is no room for this split. Merge another one, or take a block out of one.";'),
    ('  const loc = moveStepLoc(curSegs(), id, dir);', '  const loc = hrStep(curSegs(), id, dir);'),
    ('  const ns = normalize(segs), cur = flatCurrent(S.chain);\n',
     '  const cur = flatCurrent(S.chain), ns = hrArrange(segs);\n  if (!ns) { hrNoPlace(segs); render(true); return; }\n'),
    ('  segs = normalize(segs);\n  const n = grpCount(segs);\n',
     '  const hrSegs = hrArrange(segs), hrBefore = hrMono();\n'
     '  if (!hrSegs) { hrNoPlace(segs); if (o.optimistic === false && !DEMO) await loadChain(); else render(true); return false; }\n'
     '  segs = hrSegs;\n  const n = grpCount(segs);\n'),
    ('  finally { txn--; for (const id of gone) fxGone.delete(id); }\n  return !err;', '  finally { txn--; for (const id of gone) fxGone.delete(id); }\n  hrMonoSay(hrBefore);\n  return !err;'),
    ('async function addFx(type, loc) {\n  if (!DEMO) {\n    const gate = HyperRigMiniFX.add(type, curSegs(), loc, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus");',
     'async function addFx(type, loc) {\n  if (!hrFits(loc)) return null;\n  if (!DEMO) {\n'
     '    const gate = HyperRigMiniFX.add(type, curSegs(), loc, Pedal.tr === SerialTransport ? "usb-cdc" : "ble-nus", hrBank(curSegs(), loc));'),
    ('  const bank = locBank(segs0, loc);', '  const bank = hrBank(segs0, loc);'),
    ('if (loc.t === "newgrp" && n[bank] >= FX_MAXGRP)', 'if (S.ampPresent && loc.t === "newgrp" && n[bank] >= FX_MAXGRP)'),
    ('    if (id == null) { await loadChain(); return null; }\n', '    if (id == null) { await loadChain(); return null; }\n    hrNew = { id, type };\n'),
    ('    edMark("other", null, q); await loadChain();\n', '    edMark("other", null, q); await loadChain();\n    if (!r.startsWith("ERR")) await hrSettle();\n'),
    ('await loadChain(); await loadMem().catch(() => {}); render(true);', 'await loadChain(); await loadMem().catch(() => {}); render(true);\n    if (!r.startsWith("ERR")) await hrSettle();'),
    ('  Log.act("amp_add", { loc });\n', '  const hrAt = hrAmpPlace(loc); if (hrAt == null) return;\n  Log.act("amp_add", { loc });\n'),
    ('  if (DEMO) { S.ampPresent = 1; const segs = cloneSegs(curSegs());', '  if (DEMO) { S.ampPresent = 1; loc = hrAmpLoc(hrAt); const segs = cloneSegs(curSegs());'),
    ('    await loadChain({ quiet: true });', '    await loadChain({ quiet: true });\n    loc = hrAmpLoc(hrAt);'),
    ('  for (const el of pioArr(snd.chain)) {', '  for (const el of hrImportChain(pioArr(snd.chain), snd.amp, types)) {'),
    ('  if (!stHas() || !it || !((S.chain && S.chain.Q) || []).some(x => x.id === it.id)) return;',
     '  if (!stHas() || !it) return;\n  if (!((S.chain && S.chain.Q) || []).some(x => x.id === it.id)) { hrMonoHint(h, it); return; }'),
    ('nextTo = s => s && s.k === "grp" && s.bank === bank;', 'nextTo = s => s && s.k === "grp" && (!S.ampPresent || s.bank === bank);'),
    ('    if (nG[bank] < FX_MAXGRP && ', '    if ((S.ampPresent ? nG[bank] < FX_MAXGRP : nG.P + nG.Q < 2 * FX_MAXGRP) && '),
]
# Replacing a block from its menu is one command of the pedal (hrReplace, in app/mini/product-ui.js): the page's own way takes the old block away
# first, and loses it when the new one does not fit. The category of the block comes first, and the new block has the focus. The IR that is picked
# because there was none goes where it was wanted.
PRODUCT_PAGE += [
    ('  if (!DEMO) { toast("Replace is not enabled. Add or remove individual serial effects instead.", "err"); return; }\n', '  if (!DEMO) return hrReplace(id, type);\n'),
    ('  typeList(m, name => replaceFx(it.id, name), {', '  typeList(m, name => replaceFx(it.id, name).then(id => { if (id != null) focusBlk(id); }), {'),
    ('  for (const c of CATS) {\n    const names = by[c.key] || [], ampRow',
     '  for (const c of o.cur ? [...CATS].sort((a, b) => (b.key === o.cur) - (a.key === o.cur)) : CATS) {\n    const names = by[c.key] || [], ampRow'),
    ('async function addFx(type, loc) {\n', 'async function addFx(type, loc) {\n  if (loc && loc.t === "replace") return hrReplace(loc.id, type, loc);\n'),
]
# The low and the high cut of the cab (firmware/ultrarig/mini/product/cab.c). The high one is kept as Hz below 20,000, so that 0 is off.
PRODUCT_PAGE += [
    ('if (n === "lowcut_hz") return { lab: "Low cut", unit: "lowcut" };', 'if (n === "lowcut_hz") return { lab: "Low cut", unit: "lowcut" }; if (n === "hicut_hz") return { lab: "High cut", unit: "hicut" };'),
    ('  if (unit === "lowcut") return v > 0 ? v + " Hz" : "Off";\n',
     '  if (unit === "lowcut") return v > 0 ? v + " Hz" : "Off";\n  if (unit === "hicut") return v > 0 ? ((20000 - v) / 1000).toFixed(1) + " kHz" : "Off";\n'),
]
# The battery's gauge, with what the pedal reads (hrBattery, in app/mini/product-ui.js): its LVL says nothing of it.
PRODUCT_PAGE += [
    ('  if (/^LVL /.test(l)) battShow(parseLvlBat(l));', '  if (/^LVL /.test(l)) battShow(parseLvlBat(l) || hrBattery);'),
    ('    : v != null ? T("Battery {n} %, {v} V", { n: b.pct, v }) : "";', '    : v != null ? T("Battery {n} %, {v} V", { n: b.pct, v }) : b.note || "";'),
]
# The pedal switched a block off because it had no time for it: the message has a way back (hrOverloadAction, in app/mini/product-ui.js).
PRODUCT_PAGE += [
    ('  toast(msg + ".", "err");\n  refreshFromPedal();\n', '  toast(msg + ".", "err", hrOverloadAction(m));\n  refreshFromPedal();\n'),
]
# A pedal that comes and goes twice, as one that starts again at once does: the port of the first time cannot be opened any more, and that was tried
# again and again. The port that is there now is taken.
PRODUCT_PAGE += [
    ('    const p = Pedal.tr.isKnown(port) ? port : await Pedal.tr.known();\n', '    const p = await Promise.resolve(Pedal.tr.known()).catch(() => null) || (Pedal.tr.isKnown(port) ? port : null);\n'),
]
# A scene can have another cab than the block has otherwise (its ir_slot): in a preset file, and back. What did not fit may be memory too.
PRODUCT_PAGE += [
    ('  const scenes = [];\n  for (let k = 0; k < 8; k++) {\n    const sc = st.scenes && st.scenes[k]; if (!sc) continue;\n',
     '  const scenes = [], hrCabs = new Map([...(L.chain.P || []), ...(L.chain.Q || [])].map(x => [x.id, hrIrSlot(x, types)]));\n  for (let k = 0; k < 8; k++) {\n    const sc = st.scenes && st.scenes[k]; if (!sc) continue;\n'),
    ('if (it) blocks[keyOf[id]] = { on: !!it.on, params: pioParamsOut(it, types[it.type]) }; }',
     'if (!it) continue; const b = blocks[keyOf[id]] = { on: !!it.on, params: pioParamsOut(it, types[it.type]) }, v = hrIrSlot(it, types); if (v !== hrCabs.get(id)) { b.ir = v > 0 ? pioRef(st.irs, v - 1, att.ir) : null; irNeed(b.ir || cabRef); } }'),
    ('  for (const it of [...(L.chain.P || []), ...(L.chain.Q || [])]) {\n    if (it.type !== "ir") continue;\n',
     '  for (const it of [L, ...pioArr(st.scenes).filter(Boolean)].flatMap(x => [...(x.chain.P || []), ...(x.chain.Q || [])])) {\n    if (it.type !== "ir") continue;\n'),
    # after the scenes' captures (above): the scenes' cabs
    ('  if (amp.present !== false) for (const s of pioArr(snd.scenes)) if (pioObj(s)) add(s.capture, "capture");\n  return out;\n}\n',
     '  if (amp.present !== false) for (const s of pioArr(snd.scenes)) if (pioObj(s)) add(s.capture, "capture");\n'
     '  for (const s of pioArr(snd.scenes)) for (const b of pioObj(s) && pioObj(s.blocks) ? Object.values(s.blocks) : []) if (pioObj(b) && pioObj(b.ir)) add(b.ir, "ir");\n  return out;\n}\n'),
    ('st.p[i] = pioObj(e) ? params(b.type, types[b.type], e.params, base.p[i], "scene") : base.p[i].slice(); });',
     'st.p[i] = pioObj(e) ? params(b.type, types[b.type], e.params, base.p[i], "scene") : base.p[i].slice(); st.ir[i] = b.type === "ir" && pioObj(e) && e.ir !== undefined ? hrCab(e.ir) : b.ir; });'),
    ('st = { k, name: pioAscii(s.name, 15), on: [], p: [],', 'st = { k, name: pioAscii(s.name, 15), on: [], p: [], ir: [],'),
    ('  const seen = new Set(), scenes = [];\n  for (const s of pioArr(snd.scenes)) {\n',
     '  const hrCab = ref => {\n    const m = pioObj(ref) ? match(ref, ctx.irs) : null;\n    if (pioObj(ref) && !m) W.warn.push({ k: "The cab IR \\"{name}\\" isn\'t on this pedal: the block uses the preset\'s IR instead.", name: pioText(ref.name, 40) });\n    return m ? m.slot : null;\n  };\n'
     '  const seen = new Set(), scenes = [];\n  for (const s of pioArr(snd.scenes)) {\n'),
    ('base = { on: blocks.map(b => b.on), p: blocks.map(b => b.p),', 'base = { on: blocks.map(b => b.on), p: blocks.map(b => b.p), ir: blocks.map(b => b.ir),'),
    ('let cur = { on: blocks.map(() => false), p: blocks.map(b => b.p.slice()),', 'let cur = { on: blocks.map(() => false), p: blocks.map(b => b.p.slice()), ir: blocks.map(b => b.ir),'),
    ('    blocks.forEach((b, i) => { if (!s.on[i] && cur.on[i]) cmd(`FXE {${i}} 0`, "FXE", { ref: i }); });\n',
     '    blocks.forEach((b, i) => { if (!s.on[i] && cur.on[i]) cmd(`FXE {${i}} 0`, "FXE", { ref: i }); });\n    blocks.forEach((b, i) => { if (s.ir[i] !== cur.ir[i]) cmd(`FXIR {${i}} ${s.ir[i] == null ? -1 : s.ir[i]}`, "FXIR", { ref: i, tmo: 3000 }); });\n'),
    ('cur = { on: s.on.slice(), p: s.p.map(x => x.slice()),', 'cur = { on: s.on.slice(), ir: s.ir.slice(), p: s.p.map(x => x.slice()),'),
    ('Scene {n} not saved: not enough CPU for its blocks.', 'Scene {n} not saved: not all of its blocks fit (CPU or memory).'),
    ('Scenes {list} not saved: not enough CPU for their blocks.', 'Scenes {list} not saved: not all of their blocks fit (CPU or memory).'),
]
# The capture that plays has no slot: the person is asked by name, and may keep it (hrKeepCapture, in app/mini/product-ui.js).
PRODUCT_PAGE += [
    ('  Log.act("preset_save", { n, name, replace: !!existing });\n',
     '  if (!DEMO && globalThis.hrTry && hrTry.on) await hrTry.beforeSave();\n'
     '  if (!DEMO && S.capSlot < 0 && typeof hrKeepCapture === "function") await hrKeepCapture();\n'
     '  Log.act("preset_save", { n, name, replace: !!existing });\n'),
    ('toast("This capture isn\'t in your library. Save it there first.", "warn");',
     'toast(`Saved, but the capture ${S.model ? \'"\' + S.model + \'"\' : "that plays"} is not in your library: the preset will not bring it back.`, "warn");'),
]
# The settings for every preset, and the calibration of the input (app/mini/product-globals.js): what the pedal did not take is shown as it is, and what
# the settings are for is said where they are. The page's second step of the calibration has no part in the suggestion, and its "pedal input level" is a
# number about the input of another pedal, for a second opinion that is not given here.
PRODUCT_PAGE += [
    ('<link rel="stylesheet" href="product-tone3000.css">\n', '<link rel="stylesheet" href="product-tone3000.css">\n<link rel="stylesheet" href="product-globals.css">\n'),
    ('<script src="product-tone3000.js"></script>', '<script src="product-tone3000.js"></script>\n<script src="product-globals.js"></script>'),
    ('  <section><h3>Global EQ <span class="qhelp" tabindex="0" title="Output EQ outside the presets: it applies to every preset">?</span></h3>\n',
     '  <p class="hrall">These settings are for every preset, and for bypass too. You hear a change at once; <b>Save to pedal</b> keeps it when the pedal is switched off.</p>\n'
     '  <section><h3>Global EQ <span class="qhelp" tabindex="0" title="After the blocks of every preset: at each frequency, up to 12 dB more or less. 100 Hz and 7 kHz are shelves. With stereo it makes the sound mono. Each band in use takes about 3 % of the room for blocks: a preset that is nearly full may then start with a block switched off.">?</span></h3>\n'),
    ('title="Cuts low rumble from the input. Use 25 Hz for bass."', 'title="Takes away what is below this frequency at the input: rumble, not notes. A low E is 82 Hz. Use 25 Hz for a bass."'),
    ('<h3>Output limiter <span class="qhelp" tabindex="0" title="Stops the output from clipping.">?</span></h3>',
     '<h3>Output limiter <span class="qhelp" tabindex="0" title="Holds the output of every preset under the ceiling, so that it does not clip. Release is how fast it lets go again.">?</span></h3>'),
    ('function buildGeq() {\n', 'function buildGeq() {\n  if (typeof hrEq === "function") { hrEq(); return; }\n'),
    ('    const v = +sel.value; S.hpf = v; Log.act("hpf", { hz: v });\n', '    const v = +sel.value, was = S.hpf; S.hpf = v; Log.act("hpf", { hz: v });\n'),
    ('else toast("Couldn\'t set the input HPF: " + r, "err"); }', 'else { S.hpf = was; sel.value = was; toast("Couldn\'t change the high-pass: " + errText(r || "ERR no answer"), "err"); } }'),
    ('toast("Couldn\'t change the limiter: " + r, "err");', 'toast("Couldn\'t change the limiter: " + errText(r || "ERR no answer"), "err");'),
    ('else toast("Couldn\'t change the scene transition: " + r, "err");', 'else { $("snapGlide").checked = !on; toast("Couldn\'t change the scene transition: " + errText(r || "ERR no answer"), "err"); }'),
    ('if (!DEMO && S.connected) Pedal.cmd(`SPILL ${$("spill").checked ? 1 : 0}`, "SPILL"); };',
     'if (!DEMO && S.connected) { const on = $("spill").checked; Pedal.cmd(`SPILL ${on ? 1 : 0}`, "SPILL").then(ls => { '
     'if (!reply(ls, "SPILL").startsWith("SPILL " + (on ? 1 : 0))) { $("spill").checked = !on; snapTitles(); toast("Couldn\'t change the tails. Try again.", "err"); } }, () => {}); } };'),
    ('    <li data-i="0"><b>1. Play a hard strum</b><span>Strum your loudest chord.</span></li>\n    <li data-i="1"><b>2. Play a sustained note</b><span>Hold a note at your normal level.</span></li>\n',
     '    <li data-i="0"><b>1. Play your loudest chords</b><span>For ten seconds or more, with the guitar you use. Nothing changes while the pedal listens.</span></li>\n'
     '    <li data-i="1"><b>2. See the suggestion</b><span>It is for the input trim of this capture, and it is set only when you say so.</span></li>\n'),
    ('<span>Peak <b id="calPk">\u2013</b> dBFS</span><span>RMS <b id="calRms">\u2013</b> dBFS</span><span>Reading <b id="calWin">0</b> (every 3 s)</span>',
     '<span>Input <b id="calNow">\u2013</b> dB</span><span>Loudest <b id="calPk">\u2013</b> dB</span><span>Readings <b id="calWin">0</b>, one every 3 s</span>'),
    ('<details class="caladv">', '<details class="caladv" hidden>'),
    ('T("The pedal listens and suggests the input trim.")', 'T("The pedal listens to your guitar and suggests the input trim of the capture that plays. It stops by itself after three minutes.")'),
    ('  Cal.last = c; $("calSens").value', '  Cal.last = c; Cal.slot = c.slot; $("calSens").value'),
    ('  if (!c || !Cal.open) return;\n  Cal.last = c;\n', '  if (!c || !Cal.open || typeof hrCalOther === "function" && hrCalOther(c)) return;\n  Cal.last = c;\n'),
    ('function calRender() {\n', 'function calRender() {\n  if (typeof hrCal === "function") { hrCal(); return; }\n'),
    ('  if (Cal.phase === 0) { Cal.phase = 1; Cal.rmsMax = null; calRender(); return; }\n', ''),
]
# The same volume for every preset (product-loudness-ui.js): its pieces and polls are not for the log, as those of an upload are not.
PRODUCT_PAGE += [
    ('<script src="product-tone3000.js"></script>', '<script src="product-tone3000.js"></script>\n<script src="product-loudness.js"></script>\n<script src="product-loudness-ui.js"></script>'),
    ('<link rel="stylesheet" href="product-tone3000.css">', '<link rel="stylesheet" href="product-tone3000.css">\n<link rel="stylesheet" href="product-loudness.css">'),
    ('QUIET = /^(LVL|FXS|TUNE|EVT|LDB|IRB)\\b/;', 'QUIET = /^(LVL|FXS|TUNE|EVT|LDB|IRB|RECD|INJB|HRLV$)\\b/;'),
]
# The presets to start with (product-ui.js, hrStartersSoon): asked for once the first connection is made, after a first install.
PRODUCT_PAGE += [
    ('  logCrash();\n', '  logCrash();\n  if (typeof hrStartersSoon === "function") hrStartersSoon();\n'),
]
# Bluetooth from a computer comes with 0.5.0: until then the page offers no Bluetooth connection (Connect via Bluetooth hidden).
PRODUCT_PAGE += [
    ('  available() { return !!capBle() || !!(typeof navigator !== "undefined" && navigator.bluetooth && navigator.bluetooth.requestDevice); },',
     '  available() { return !!capBle(); },'),
]
PRODUCT_POLICY = [
    ('/^SNAPS ([01]{4}) (?:current|actual)=(-?\\d+)$/', '/^SNAPS ([01]{8}) (?:current|actual)=(-?\\d+)$/'),
    ('integer(+m[2], -1, 3)', 'integer(+m[2], -1, 7)'),
    ('integer(+m[4], 0, 15)', 'integer(+m[4], 0, 255)'),
    ('const q = /^SNAP ([0-3])$/.exec(request), m = lines.length === 1 && /^SNAP ok ([0-3])', 'const q = /^SNAP ([0-7])$/.exec(request), m = lines.length === 1 && /^SNAP ok ([0-7])'),
    ('    m = /^SNAP ([0-3])$/.exec(value);', '    m = /^SNAP ([0-7])$/.exec(value);'),
    ('const q = /^SNAPSAVE ([0-3])$/.exec(request), m = lines.length === 1 && /^SNAPSAVE ok ([0-3])', 'const q = /^SNAPSAVE ([0-7])$/.exec(request), m = lines.length === 1 && /^SNAPSAVE ok ([0-7])'),
    ('    m = /^SNAPSAVE ([0-3])$/.exec(value);', '    m = /^SNAPSAVE ([0-7])$/.exec(value);'),
    ('reason: "firmware mutations are not validated for this MINI build"', 'reason: "this is not available in this version of the editor yet"'),
    ('if (["FXS", "FXA", "FXR", "FXP",', 'if (["FXS", "FXA", "FXR", "FXC", "FXP",'),
]
# The front panel of the TANK-MINI, from the proportions of M-VAVE's manual, instead of the schematic of three switches.
PRODUCT_PANEL = [
    ('    // A schematic of the three switches, not a fabricated G/B panel or pin map.\n'
     '    return \'<rect x="4" y="4" width="928" height="188" rx="18" fill="#193437" stroke="#638082"/>\' +\n'
     '      \'<text x="468" y="42" fill="#eef1f2" text-anchor="middle" font-size="22">HyperRig MINI</text>\' +\n'
     '      ["A", "B", "C"].map((s, i) => \'<circle cx="\' + (210 + i * 258) + \'" cy="113" r="25" fill="#343c42" stroke="#96a4ab"/>\' +\n'
     '        \'<text x="\' + (210 + i * 258) + \'" y="168" fill="#eef1f2" text-anchor="middle" font-size="18">\' + s + \'</text>\').join("");\n',
     '    const text = (x, y, size, t) => \'<text x="\' + x + \'" y="\' + y + \'" fill="#fdf4fa" text-anchor="middle" font-size="\' + size + \'">\' + t + \'</text>\';\n'
     '    const rule = (a, b) => \'<path d="M\' + a + \' 106H\' + b + \'" stroke="#fdf4fa" stroke-width="1" opacity=".8"/>\';\n'
     '    return \'<rect x="177" y="2" width="582" height="192" rx="6" fill="#b87ca4"/><path d="M177 13H759" stroke="#cf9abd"/>\' +\n'
     '      \'<path d="M177 172H759V188a6 6 0 0 1 -6 6H183a6 6 0 0 1 -6 -6Z" fill="#96618a"/><circle cx="235" cy="28" r="5" fill="#3f2b3a" stroke="#8d5a7f"/>\' +\n'
     '      text(354, 60, 24, "TANK-MINI") + text(352, 111, 14, "BANK-") + text(584, 111, 14, "BANK+") + rule(278, 322) + rule(382, 426) + rule(510, 554) + rule(614, 658) +\n'
     '      ["A", "B", "C"].map((s, i) => { const x = 235 + i * 233; return \'<circle cx="\' + x + \'" cy="52" r="9" fill="none" stroke="#fdf4fa"/>\' + text(x, 57, 12, s) +\n'
     '        \'<circle cx="\' + x + \'" cy="106" r="36" fill="none" stroke="#8f5d82" stroke-width="9"/><circle cx="\' + x + \'" cy="106" r="30" fill="#c7cacc"/>\' +\n'
     '        \'<circle cx="\' + x + \'" cy="106" r="19" fill="#e9ebec" stroke="#8c9195" stroke-width="5"/>\'; }).join("");\n'),
]
# Adding a block anywhere, in parallel too: the page appends it and moves it to its place.
FXUI = [
    ('    if (!Array.isArray(segs) || !segs.length ||\n'
     '        segs.some(s => !s || !["fx", "amp"].includes(s.k)) ||\n'
     '        segs.filter(s => s.k === "amp").length !== 1) return false;\n'
     '    const target = loc || {t: "serial", si: segs.length};\n'
     '    return target.t === "serial" && Number.isInteger(target.si) &&\n'
     '      (target.si === segs.findIndex(s => s.k === "amp") || target.si === segs.length);\n',
     '    if (!Array.isArray(segs) || segs.some(s => !s || !["fx", "amp", "grp"].includes(s.k)) ||\n'
     '        segs.filter(s => s.k === "amp").length > 1) return false;\n'
     '    const target = loc || {t: "serial", si: segs.length};\n'
     '    return ["serial", "newgrp", "lane"].includes(target.t) && Number.isInteger(target.si) && target.si >= 0 &&\n'
     '      target.si <= segs.length && (target.t !== "lane" || !!segs[target.si] && segs[target.si].k === "grp");\n'),
    ('reason: "Add at the end of the serial Pre or Post section. Moving and parallel routing are not enabled."};',
     'reason: "A block cannot be added at that place."};'),
    ('    const bank = target.si === segs.findIndex(s => s.k === "amp") ? "P" : "Q";\n',
     '    const amp = segs.findIndex(s => s.k === "amp");\n'
     '    const bank = given || (target.t === "lane" ? segs[target.si].bank : amp < 0 || target.si <= amp ? "P" : "Q");\n'),
    ('  function add(type, segs, loc, transport) {\n', '  function add(type, segs, loc, transport, given) {      // given: the section, when the page has found it\n'),
]
# The revision shows in the tab's title and in a coloured bar: an old tab stays in memory and looks the same otherwise.
NOTE = [
    ('document.title = "HyperRig for TANK MINI";', f'document.title = "HyperRig for TANK-MINI editor {REVISION}";'),
    ('"This editor requires HyperRig for TANK MINI."', '"This editor requires HyperRig for TANK-MINI."'),
    ('padding:10px 18px;background:#172b30;color:#e3edef;', 'padding:10px 18px;background:#5a3d00;color:#fff1cf;'),
    ('"HyperRig MINI · Offline demo" :\n'
     '    "HyperRig MINI · v4 preview · Connect by USB to edit effects, presets and scenes.";',
     '"HyperRig for TANK-MINI · Offline demo" :\n'
     f'    "EDITOR {REVISION} · development build from source: these commands are not qualified on it · " +\n'
     '    "Connect by USB to edit the amp, effects, presets and scenes, tap the tempo and tune.";'),
]
# A product build says it in words for the person who plays.
PRODUCT_NOTE = [
    ('"EDITOR __REVISION__ · development build from source: these commands are not qualified on it · " +\n'
     '    "Connect by USB to edit the amp, effects, presets and scenes, tap the tempo and tune.";',
     '"HyperRig __VERSION__ · __TEST__" +\n'
     '    "Connect the pedal by USB to begin (editor __REVISION__).";'),
]
TEST = 'Test version: not everything has been tried on the pedal yet · '      # of a version that is not a release
MARKER = 'globalThis.HYPERRIG_MINI_BUILD='


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=True) + '\n').encode('utf-8')


def changed(text, pairs, what):
    for old, new in pairs:
        require(text.count(old) == 1, f'{what}: expected once: {old[:60]!r}')
        text = text.replace(old, new)
    return text


def inputs(base=BASE):
    files = {name: (base / name).read_bytes() for name in INPUTS}
    for name, digest in INPUTS.items():
        require(sha(files[name]) == digest, f'The pinned editor file differs: {name}')
    require((ROOT / 'app/mini/mini-profile-fx.js').read_bytes() == files['web/mini-profile.js'],
            'The tested policy of the source tree differs from the v4 package')
    return files


def area_of(directory):
    directory = Path(directory).resolve()
    require(directory.is_relative_to(ROOT), 'the area directory must be inside the repository')
    record = directory / 'build-manifest.json'
    manifest = json.loads(record.read_bytes())
    image = (directory / 'hyperrig-mini.app-area.bin').read_bytes()
    require(sha(image) == manifest.get('area_sha256'), 'the area does not match its build record')
    require(manifest.get('embedded_capture', {}).get('intact') is True,
            'the build record does not say that the embedded capture is intact')
    product = manifest.get('product')
    require(product is None or set(product) == {'version', 'build_id'}, 'the product identity of the build record is not known')
    return {'area_sha256': manifest['area_sha256'], 'record_sha256': sha(record.read_bytes()),
            'source_files': len(manifest.get('source_sha256', {})), 'product': product}


def revision_of(area):
    return PRODUCT_REVISION if area.get('product') else REVISION


def added_of(area):
    return ADDED + PRODUCT_ADDED if area.get('product') else ADDED


def profile_of(base_profile, area):
    profile = copy.deepcopy(base_profile)
    profile.update(
        image_sha256=area['area_sha256'], capabilities={**base_profile['capabilities'], 'panel': True}, hardware_verified=False, family_validation={}, family_qualification={},
        family_capabilities={'usb-cdc': FAMILIES + added_of(area)}, family_evidence_model='development-unqualified',
        derived_from={'kind': 'source-build', 'builder': 'tools/build_hyperrig_mini_image.py',
                      'target_image_sha256': area['area_sha256'], 'record_sha256': area['record_sha256'],
                      'source_files': area['source_files'], 'reviewed': False,
                      'hardware_observations_inherited_as_proof': False},
        development={'kind': 'source-build', 'revision': revision_of(area), 'commands_qualified_on_this_build': False,
                     'command_rules_of': 'mini-v4-usb-01', 'added_commands': added_of(area),
                     'device_binary_hash_attestation': False})
    if area.get('product'):
        profile['development']['product'] = area['product']
    return profile


def embed(html, old, new):
    require(html.count(MARKER) == 1, 'Expected one embedded profile')
    head, tail = html.split(MARKER, 1)
    previous, end = json.JSONDecoder().raw_decode(tail)
    require(previous == old and tail[end:end + 1] == ';', 'The embedded profile differs from profile.json')
    text = json.dumps(new, ensure_ascii=True, separators=(',', ':')).replace('<', '\\u003c')
    return head + MARKER + text + tail[end:]


def files_of(area, base=BASE):
    """{path in the bundle: bytes} of the editor."""
    source = inputs(base)
    old = json.loads(source['profile.json'])
    profile = profile_of(old, area)
    out = {'editor/' + name: raw for name, raw in source.items()}
    out['editor/web/mini-profile.js'] = changed(source['web/mini-profile.js'].decode('utf-8'),
                                                POLICY + (PRODUCT_PANEL + PRODUCT_POLICY if area.get('product') else []), 'policy').encode('utf-8')
    page = changed(embed(source['web/tankmini.html'].decode('utf-8'), old, profile), PAGE, 'page')
    note = [(a, b.replace(REVISION, revision_of(area))) for a, b in NOTE]
    if area.get('product'):
        note = [(a, b.replace('HyperRig for TANK-MINI editor', 'HyperRig editor')) for a, b in note]
        version = area['product']['version']
        note += [(a.replace('__REVISION__', revision_of(area)), b.replace('__VERSION__', version).replace('__TEST__', TEST if '-' in version else '').replace('__REVISION__', revision_of(area)))
                 for a, b in PRODUCT_NOTE]
        page = changed(page, [(a, b.replace('__VERSION__', version)) for a, b in PRODUCT_PAGE], 'product page')
    del out['editor/web/tankmini.html']
    out['editor/web/' + PAGE_FILE] = page.encode('utf-8')
    out['editor/web/index.html'] = changed(source['web/index.html'].decode('utf-8'), INDEX, 'index').encode('utf-8')
    out['editor/web/mini-dev-rules.js'] = RULES.read_bytes()
    if area.get('product'):
        out.update({'editor/web/' + name.split('/')[-1]: (ROOT / 'app/mini' / name).read_bytes() for name in PRODUCT_FILES})
    out['editor/web/mini-fx-ui.js'] = changed(source['web/mini-fx-ui.js'].decode('utf-8'), FXUI, 'fx').encode('utf-8')
    out['editor/web/mini-ui.js'] = changed(source['web/mini-ui.js'].decode('utf-8'), note, 'note').encode('utf-8')
    out['editor/profile.json'] = encoded(profile)
    out['editor/qualification.json'] = encoded({
        'schema': 1, 'kind': 'hyperrig-mini-development-editor-scope', 'revision': revision_of(area),
        'image_sha256': area['area_sha256'], 'transport': 'usb-cdc', 'enabled_families': FAMILIES + added_of(area),
        'hardware_verified': False, 'qualified_on_this_image': False, 'audio_tested': False,
        'BLE_write_enabled': False, 'panel_enabled': True, 'panel_mapping_verified': False, 'blanket_write': False,
        'device_binary_hash_attestation': False})
    out['editor/DERIVATION.txt'] = (
        'HyperRig for TANK-MINI, development editor.\n'
        'Derived from the v4 editor (revision mini-v4-usb-01), which stays unchanged.\n'
        'For builds from source on a development unit. Its commands are not qualified on this build:\n'
        'the nine USB families of the v4 editor and those of mini-dev-rules.js (amp, chain, stereo, tempo,\n'
        + ('tuner, presets, scenes, footswitches, captures, cab IRs, the settings for every preset). Bluetooth writes, firmware\n' if area.get('product')
           else 'tuner, presets, scenes, footswitches). Captures and IRs, calibration, Bluetooth writes, firmware\n') +
        'update and authentication stay blocked.\n'
        'It corrects faults of that editor: edits and Save were refused after a footswitch changed the preset\n'
        'and after the pedal refused a block, and Save did not go to the empty slot chosen for a new preset.\n'
        + (f"It is for HyperRig {area['product']['version']}, build {area['product']['build_id']}: the pedal names its build\n"
           'with HRID, and on any other build the editor only reads.\n' if area.get('product') else
           'The editor cannot tell which build the pedal runs: only the version line of PING is known.\n') +
        'Original license notices are preserved.\n').encode('utf-8')
    return out


def build(output, area_directory):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    area = area_of(area_directory)
    files = files_of(area)
    for name, raw in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    meta = {'schema': 1, 'kind': KIND, 'revision': revision_of(area), 'area': area, 'base': BASE.relative_to(ROOT).as_posix(),
            'base_files_sha256': INPUTS, 'builder_sha256': sha(Path(__file__).read_bytes()),
            'files': {name: sha(raw) for name, raw in sorted(files.items())},
            'hardware_qualified': False, 'device_io': False}
    (output / 'bundle.json').write_bytes(encoded(meta))
    return check(output)


def check(output):
    """The bundle holds exactly the files of its record. No device access."""
    output = Path(output).resolve()
    meta = json.loads((output / 'bundle.json').read_bytes())
    require(meta.get('kind') == KIND and meta.get('hardware_qualified') is False, 'not a development editor')
    actual = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    require(actual == set(meta['files']) | {'bundle.json'}, 'the bundle holds other files')
    for name, digest in meta['files'].items():
        require(sha((output / name).read_bytes()) == digest, f'a bundle file differs: {name}')
    profile = json.loads((output / 'editor/profile.json').read_bytes())
    require(profile['hardware_verified'] is False and profile['development']['commands_qualified_on_this_build'] is False
            and profile['capabilities']['write'] is False
            and profile['development'].get('product') == meta['area'].get('product')
            and profile['family_capabilities'] == {'usb-cdc': FAMILIES + added_of(meta['area'])}, 'the profile claims more than it may')
    return {'result': 'pass', 'directory': str(output), 'revision': meta['revision'], 'files': len(meta['files']),
            'area_sha256': meta['area']['area_sha256'], 'families': FAMILIES + added_of(meta['area']), 'hardware_qualified': False,
            'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--output', type=Path)
    action.add_argument('--check', type=Path)
    parser.add_argument('--area', type=Path)
    args = parser.parse_args(argv)
    if args.output:
        if not args.area:
            parser.error('--output needs --area')
        result = build(args.output, args.area)
    else:
        result = check(args.check)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
