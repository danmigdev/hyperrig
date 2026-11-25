"""Trying without saving (app/mini/product-try.js), used as a person does, with the simulated pedal of check_mini_dev_editor.py. No device is opened.

The pedal here also keeps what a preset has of its own (its volume, capture, cab IR, colour) and what each scene has, and says what it plays. Checked: a file of
presets is heard one after the other, quietly at first and up to a limit, and nothing is written to the pedal before Keep; Back gives exactly what played, with
the changes that were not saved; what could not come back is asked first; Keep; captures and cab IRs from files; a footswitch, a disconnection, a restart and
errors in the middle; what is refused meanwhile; leaving the page; a file made to do harm. This is no test of a pedal or of its sound.

Usage, from the repository root; tools/check_mini_dev_editor.py and tools/check_desktop_editor.py run these steps too:
    python -B tools/check_mini_try.py --bundle build/hyperrig-mini-dev-editor-NN --output build/CHECK-NN
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_dev_editor as editor  # noqa: E402

require = editor.require
QUIET = 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !Pedal.busy'
TOASTS = '[...document.querySelectorAll(".toast, .toasts > *, #toasts > *")]'

# What the simulated pedal has more here.
MORE = r'''
(() => {
  const p = __pedal, keep = p.keep, load = p.load, copy = v => JSON.parse(JSON.stringify(v));
  p.color = null; p.scene_values = {}; p.writes = []; p.loud_at = null; p.fail = null; p.log = [];
  const values = () => ({chain: ["P", "Q"].map(b => p.chain[b].map(x => [x.id, x.on, x.p.slice()])), gain: p.gain.slice(), amp: p.amp, ampeq: p.ampeq.slice()});
  p.keep = function () { return {...keep.call(this), gain: this.gain.slice(), color: this.color, c_slot: this.cap_slot, i_slot: this.ir_slot, ampx: this.ampx ?? 1, scene_values: copy(this.scene_values)}; };
  p.load = function (n) { this.ampx = 1; load.call(this, n); const s = this.store[n];
    if (s.c_slot >= 0 && this.caps[s.c_slot]) { this.cap = this.caps[s.c_slot]; this.cap_slot = s.c_slot; }
    if (s.i_slot >= 0 && this.irs[s.i_slot]) { this.ir = this.irs[s.i_slot]; this.ir_slot = s.i_slot; } };
  /* What is kept when the power goes, and what is heard. */
  p.kept = () => JSON.stringify([p.presets, p.store, Object.entries(p.caps).map(([k, x]) => [k, x.name, x.trim, crc(x.data)]), Object.entries(p.irs).map(([k, x]) => [k, x.name, crc(x.data)])]);
  const crc = d => { let c = 5381; for (const b of d) c = (c * 33 ^ b) >>> 0; return c; };
  p.heard = () => JSON.stringify({chain: ["P", "Q"].map(b => p.chain[b].map(x => [x.type, x.on, x.lane || 0, x.type === "ir" ? [x.p.filter((v, i) => i !== 2), crc((x.p[2] ? p.irs[x.p[2] - 1] : p.ir).data)] : x.p])), gain: p.gain, bpm: p.bpm, ampeq: p.ampeq, amp: p.amp,
    ampx: p.ampx ?? 1, capture: (p.ampx ?? 1) ? [crc(p.cap.data), p.cap.trim] : null, cap_slot: p.cap_slot, ir_slot: p.ir_slot, preset: p.current, scene: p.scene, scenes: p.scenes, names: p.names, stereo: p.stereo, color: p.color, tuner: p.tuner[0]});
  const press = p.press;
  p.ev = [];
  p.press = function (n) { if (this.tuner[0]) { this.tuner[0] = 0; return; }      // a switch closes the tuner, and nothing else
    this.ev.push([this.ev.length + 1, Math.round(performance.now()), "preset_f", n]); press.call(this, n); };
  p.restart = () => { p.changes = 1; p.gain = [0, 0]; p.cap = p.caps[9]; p.cap_slot = 9; const n = Object.keys(p.store)[0]; p.load(+n); };
  p.before = line => {
    const [word, ...a] = line.split(" ");
    if (word === "EVT") return [...p.ev.filter(e => e[0] > +a[0]).map(e => `EV ${e[0]} ${e[1]} ${e[2]} ${e[3]} 0`), `EVT end ${p.ev.length} 0 0 ${Math.round(performance.now())}`];
    if (p.fail) { const r = p.fail(line); if (r) return r; }
    if (/^(PSAVE|SNAPSAVE|SNAPDEL|PNAME|PDEL|CSAVE|CDEL|ISAVE|IDEL|GSAVE)$/.test(word) && (a.length || word === "GSAVE") && !(word === "SNAPSAVE" && p.current < 0)) p.writes.push(line);
    if (word === "PNEW") { p.scene_values = {}; p.gain = [0, 0]; p.changes++; }
    if (word === "SNAPSAVE") p.scene_values[a[0]] = values();
    if (word === "SNAP" && p.scenes[+a[0]] === "1" && p.scene_values[a[0]]) { const v = copy(p.scene_values[a[0]]); p.gain = v.gain; p.amp = v.amp; p.ampeq = v.ampeq; p.changes++;
      for (const [k, b] of [["P", 0], ["Q", 1]]) for (const [id, on, q] of v.chain[b]) { const x = p.chain[k].find(y => y.id === id); if (x) { x.on = on; x.p = q; } } }
    if (/^(FXA|FXR|FXM|PLOAD|CLOAD|ILOAD|LDEND|IREND)$/.test(word)) p.changes++;
    if (word === "PCOLOR") { if (a.length) p.color = a[0] === "none" ? null : a[0]; return [`PCOLOR ${p.color || "none"} preset=${p.current}`]; }
    if (word === "FXIR" && a[1] === "-1") { for (const k of ["P", "Q"]) for (const x of p.chain[k]) if (x.id === +a[0]) x.p[2] = 0; p.changes++; return [`FXIR ok ${a[0]} -1`]; }      // as the application does
    if (word === "GAIN" && a.length) p.log.push(+a[1]);
    if (line === "LVL") { const loud = p.loud_at !== null && p.gain[1] >= p.loud_at;
      return [`LVL in=-240 out=${loud ? -12 : -253} ci=0 co=0 fx=0/22718 mem=0 sk=0 m=2 g=${p.gain.join("/")} b=${p.bpm} s=${p.scene} a=${p.amp} e=131732/154950 am=118688 c=${p.changes} p=${p.current} tu=${p.tuner[0]} lim=0 ce=0 und=0 ovl=0 ` +
        `cin=-241 ctg=-180 fm=0,0,1,0 stuck=0 bat=-1,0,1`]; }
    return null;
  };
})()'''


def wav(seed, samples=3000):
    """A .wav of 48 kHz, as JavaScript that makes the file."""
    return f'''(() => {{ const n = {samples}, b = new DataView(new ArrayBuffer(44 + 2 * n)), s = (o, t) => [...t].forEach((c, i) => b.setUint8(o + i, c.charCodeAt(0)));
      s(0, "RIFF"); b.setUint32(4, 36 + 2 * n, true); s(8, "WAVEfmt "); b.setUint32(16, 16, true); b.setUint16(20, 1, true); b.setUint16(22, 1, true); b.setUint32(24, 48000, true); b.setUint32(28, 96000, true);
      b.setUint16(32, 2, true); b.setUint16(34, 16, true); s(36, "data"); b.setUint32(40, 2 * n, true); let seed = {seed};
      for (let i = 0; i < n; i++) {{ seed = seed * 16807 % 2147483647; b.setInt16(44 + 2 * i, Math.round((seed / 2147483647 - .5) * 50000 * Math.exp(-i / 400)), true); }}
      return new File([b.buffer], "Cab {seed}.wav", {{type: "audio/wav"}}); }})()'''


def attachment(kind, name, seed, size):
    raw = (b'A2L1' if kind == 'capture' else b'') + bytes((seed * 31 + i * 7) & 255 for i in range(size - (4 if kind == 'capture' else 0)))
    out = {'kind': kind, 'name': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'data': base64.b64encode(raw).decode()}
    return {**out, 'format': 'a2l1', 'trim_db': 1.5, 'in_dbu': None} if kind == 'capture' else {**out, 'format': 'tkgj', 'rate_khz': 48, 'gain_mdb': -1500}


def block(kind, ident, **params):
    return {'id': ident, 'type': kind, 'on': True, 'params': params}


def document():
    """Three presets as a stranger shares them: one loud and with scenes, one with a capture and a cab IR inside, one that needs what is not there."""
    cap, ir = attachment('capture', 'Stranger amp', 3, 600), attachment('ir', 'Stranger cab', 5, 1200)
    ref = lambda a, k: {'name': a['name'], 'bytes': a['bytes'], 'sha256': a['sha256'], 'attachment': k}
    def preset(name, chain, **sound):
        base = {'chain': chain, 'amp': {'present': True, 'on': True, 'capture': None}, 'cab_ir': None, 'gain_db': {'in': 2, 'out': -4}, 'tempo_bpm_x10': 1400, 'color': None, 'scenes': [], 'active_scene': None}
        return {'meta': {'name': name, 'author': 'A stranger', 'description': 'Bright.', 'tags': []}, 'compat': {}, 'sound': {**base, **sound}}
    scene = lambda k, out, on: {'index': k, 'name': f'Part {k + 1}', 'gain_db': {'in': 2, 'out': out}, 'amp_on': True, 'blocks': {'b1': {'on': on, 'params': {'umbral_db': -50}}}}
    loud = preset('Loud one', [block('gate', 'b1', umbral_db=-60), {'amp': True}, block('comp', 'b2', ratio_x10=30)], gain_db={'in': 2, 'out': 12}, scenes=[scene(0, 12, True), scene(1, 3, False)], active_scene=0)
    full = preset('With its files', [block('boost', 'b1'), {'amp': True}, {**block('ir', 'b2'), 'ir': None}], amp={'present': True, 'on': True, 'capture': ref(cap, 'cap1')}, cab_ir=ref(ir, 'ir1'))
    lacking = preset('Lacking', [block('gate', 'b1'), block('wonderfx', 'b2'), {'amp': True}, {**block('ir', 'b3'), 'ir': {'name': 'Nowhere', 'bytes': 500}}], amp={'present': True, 'on': True, 'capture': {'name': 'No such amp', 'bytes': 4892}})
    return json.dumps({'format': 'hyperrig-preset', 'version': 1, 'min_reader': 1, 'kind': 'bank', 'presets': [loud, full, lacking], 'attachments': {'cap1': cap, 'ir1': ir}}), cap, ir


class Steps:
    def __init__(self, page, output):
        self.page, self.cdp, self.output, self.said = page, page.cdp, output, {}

    def ev(self, text):
        return self.cdp.evaluate(text)

    def wait(self, text, what, seconds=30):
        try:
            self.page.wait(text, what, seconds)
        except ValueError:
            raise ValueError(f"timeout: {what}: try {self.ev('[hrTry.state, hrTry.notes, document.getElementById(`hrTry`).innerText]')}, said {self.toasts()}, dialog {self.ev('document.querySelector(`.mdlg`)?.innerText')}, "
                             f"errors {self.ev('__errors')}, last sent {self.ev('__pedal.sent.slice(-6)')}") from None

    def toasts(self):
        return self.ev('__said')

    def clear(self):
        self.ev(TOASTS + '.forEach(e => e.remove()); __said.length = 0')

    def dialog(self, has):
        self.wait(f'(document.querySelector(".mdlg")?.innerText || "").toLowerCase().includes({json.dumps(has.lower())})', f'the dialog {has}', 15)
        return self.ev('document.querySelector(".mdlg").innerText')

    def press(self, label, where='.mdlg'):
        done = self.ev(f'(() => {{ const b = [...document.querySelectorAll("{where} button")].find(e => e.offsetParent && (e.querySelector("b")?.innerText || e.innerText).trim().toLowerCase() === {json.dumps(label.lower())} && !e.disabled); if (b) b.click(); return !!b; }})()')
        require(done, f"no button {label}: {self.ev(f'[...document.querySelectorAll(`{where} button`)].filter(e => e.offsetParent).map(e => [e.innerText, e.disabled])')}")

    def bar(self, label):
        self.press(label, '#hrTry')

    def playing(self, what, risen=True):
        self.wait('hrTry.state === "playing"' + (' && !hrTry.volume.rising' if risen else '') + ' && ' + QUIET, what, 60)

    def off(self, what):
        self.wait('hrTry.state === "off" && document.getElementById("hrTry").hidden && ' + QUIET, what, 40)

    def told(self, text):
        self.wait(f'__said.some(e => e.toLowerCase().includes({json.dumps(text.lower())}))', f'it is said: {text}', 15)

    def idle(self, what='a quiet page'):
        self.wait(QUIET, what, 30)

    def mark(self):
        """What is kept and what is heard, and the writes forgotten."""
        self.idle()
        self.clear()
        self.ev('__pedal.writes = []; __pedal.log = []')
        return self.ev('__pedal.kept()'), self.ev('__pedal.heard()')

    def same(self, mark, what, heard=True):
        kept, played = self.ev('__pedal.kept()'), self.ev('__pedal.heard()')
        require(kept == mark[0] and not self.ev('__pedal.writes'), f"{what}: the pedal was written: {self.ev('__pedal.writes')}")
        if heard and played != mark[1]:
            a, b = json.loads(mark[1]), json.loads(played)
            raise ValueError(f'{what}: not as it was: ' + json.dumps({k: [a[k], b[k]] for k in a if a[k] != b[k]}) + '; last sent: ' + json.dumps(self.ev('__pedal.sent.slice(-40)')))

    def ready(self):
        """A preset with a gate and a boost, two scenes, a tone, a volume, and the cab IR and the capture of its own slots."""
        self.ev(f'''void (async () => {{
          const say = (l, pre) => Pedal.cmd(l, pre || l.split(" ")[0], 8000);
          await uploadIrs([{wav(11)}], 0); await uploadIrs([{wav(12)}], 4); closeLib();
          for (const name of ["Home", "Other"]) {{
            await say("PNEW"); curPreset = -1; S.curPre = -1; await loadChain(); await loadSnaps(); await loadPresets(); await say("GAIN"); await say("GAIN 1 -3");
            for (const t of ["gate", "boost"]) await say("FXA Q 99 " + t); await say("FXA Q 99 ir"); await loadChain();
            await say("AMPEQ 1 60", "AMPEQ "); await say("CLOAD 9"); await say(name === "Home" ? "ILOAD 4" : "ILOAD 0"); await loadModelName(); await edFresh(); await new Promise(r => setTimeout(r, 1200));
            S.pendName = name; await savePreset(name === "Home" ? 2 : 5); }}
          await loadPreset(2); await saveSnap(1); await goSnap(0); await loadPresets(); window.__ready = true; }})()''')
        self.wait('window.__ready === true && curPreset === 2 && __pedal.current === 2 && S.snap === 0 && __pedal.ir_slot === 4 && ' + QUIET, 'the presets of this check', 60)
        require(self.ev('edCount()') == 0 and self.ev('__pedal.presets') == {'2': 'Home', '5': 'Other'}, f"the start: {self.ev('__pedal.presets')}, {self.toasts()}")


def presets(s):
    """A file of presets: heard one after the other, back exactly, kept."""
    text, cap, ir = document()
    out = {}
    s.ev(f'window.__doc = {json.dumps(text)}; window.__file = () => new File([__doc], "Stranger.hyperrig.json")')
    # a change that is not saved: a knob of the gate, a block off, the volume, the tempo
    s.ev('''void (async () => { const g = S.chain.Q.find(x => x.type === "gate"), b = S.chain.Q.find(x => x.type === "boost"); await Pedal.cmd(`FXP ${g.id} 0 -33`, "FXP"); edMark("p", {id: g.id, idx: 0, v: -33});
      await toggle(b.id); await Pedal.cmd("GAIN 1 -6", "GAIN"); edMark("on"); await Pedal.cmd("BPM 987", "BPM"); await loadChain(); window.__edited = true; })()''')
    s.wait('window.__edited === true && edCount() > 0 && ' + QUIET, 'a change that is not saved')
    mark = s.mark()
    changes = s.ev('edCount()')
    s.ev('void hrTry.files("preset", [__file()])')
    shown = s.dialog('Try 3 presets')
    require(all(x in shown for x in ('Loud one', 'With its files', 'Lacking', 'by A stranger', 'wonderfx', 'No such amp', 'Nowhere')) and 'Stranger amp' not in shown, f'the list: {shown}')
    s.cdp.screenshot(s.output / 'try-list.png')
    s.same(mark, 'the list')
    s.press('Cancel')
    s.off('Cancel')
    s.same(mark, 'Cancel')
    s.ev('void hrTry.files("preset", [__file()])')
    s.dialog('Try 3 presets')
    s.press('Try')
    s.playing('the first preset', risen=False)
    s.told('come back with Back')
    first = s.ev('[__pedal.log[0], Math.max(...__pedal.log.slice(0, 2)), hrTry.volume.rising]')
    s.playing('the first preset, risen')
    out['volume'] = s.ev('__pedal.log')
    require(-30 in out['volume'] and max(out['volume']) <= 0 and out['volume'][-1] == 0 and s.ev('__pedal.gain') == [2, 0] and any('12 dB louder' in n for n in s.ev('hrTry.notes')), f"the volume: {out['volume']}, {s.ev('hrTry.notes')}")
    after = out['volume'][len(out['volume']) - 1 - out['volume'][::-1].index(-30):]
    require(after == list(range(-30, 1, 2)), f'it does not rise step by step: {after}, {first}')
    require(s.ev('[__pedal.chain.P.map(x => x.type), __pedal.chain.Q.map(x => x.type), __pedal.current, __pedal.scenes, __pedal.bpm, __pedal.tuner[0]]') == [['gate'], ['comp'], -1, '11000000', 1400, 0], 'the first preset is not what plays')
    sent = s.ev('__pedal.sent')
    k = len(sent) - 1 - sent[::-1].index('PNEW')
    require('TUNER 1 1 440' in sent[k - 12:k], f'it is not muted while it loads: {sent[k - 12:k]}')
    s.same(mark, 'the first preset', heard=False)
    require(s.ev('[S.snapNames.slice(0, 2), __pedal.names.slice(0, 2)]') == [['Part 1', 'Part 2'], ['', '']] and not [c for c in sent[k:] if c.startswith(('SNAPNAME 0', 'SNAPNAME 1', 'PCOLOR f'))], 'the names of the scenes were sent')
    require(s.ev('document.getElementById("saveBar").hidden') and 'Loud one' in s.ev('document.getElementById("hrTry").innerText') and 'not saved on the pedal' in s.ev('document.getElementById("hrTry").innerText'), 'the bar')
    s.cdp.screenshot(s.output / 'try-preset.png')
    tall = s.ev('[...document.querySelectorAll("#hrTry button")].filter(e => e.offsetParent).map(e => [e.innerText, Math.round(e.getBoundingClientRect().height)])')
    require([t[0] for t in tall] == ['Previous', 'Next', 'Quieter', 'Louder', 'Back to 1C', 'Keep…'] and all(38 <= t[1] <= 46 for t in tall), f'the buttons: {tall}')
    out['buttons'] = tall
    # a scene of it is at its own level, no louder than the limit
    s.ev('void goSnap(1)')
    s.wait('__pedal.scene === 1 && ' + QUIET, 'its second scene')
    require(s.ev('__pedal.gain')[1] == -9, f"the second scene plays at {s.ev('__pedal.gain')}")          # 3 dB in the file, less the 12
    # what would write or change what plays is refused
    n = s.ev('__pedal.sent.length')
    s.clear()
    refused = s.ev('(async () => { const out = []; for (const c of ["PSAVE 2 X", "SNAPSAVE 0", "CSAVE 0 X", "ISAVE 0 X", "PDEL 2", "PNAME 2 X", "SNAPDEL 0", "CDEL 9", "IDEL 0", "PCOLOR ff0000"]) out.push((await Pedal.cmd(c, c.split(" ")[0]))[0]); return out; })()')
    require(all(r.startswith('ERR') and 'being tried' in r for r in refused), f'not refused: {refused}')
    for call in ('newPedalboard()', 'pioExport(true)', 'pioImport(__doc)', 'uploadCaptures([new File(["x"], "a.nam")], 1)', 'uploadIrs([new File(["x"], "a.wav")], 1)', 'useSlot(true, 9, "A2")', 'hrTry.files("preset", [__file()])'):
        s.ev(f'void {call}')
        time.sleep(0.15)
        require(not s.ev('!!document.querySelector(".mdlg")'), f'{call} asks something')
    s.told('Keep it or go back first')
    went = [c for c in s.ev(f'__pedal.sent.slice({n})') if c.split()[0] not in ('LVL', 'EVT', 'MEM', 'FXS', 'CLIST', 'FXMIX', 'STW', 'TUNE', 'LVLSUB') and not c.startswith('AMPEQ')]
    require(not went, f'sent meanwhile: {went}')
    s.same(mark, 'what is refused', heard=False)
    leave = s.ev('(() => { const e = new Event("beforeunload", {cancelable: true}); dispatchEvent(e); return [e.defaultPrevented, S.connected, Pedal.tr.isOpen()]; })()')
    require(leave == [True, True, True], f'leaving the page: {leave}')
    # the next, without anything in between; its capture and cab IR are heard without a slot
    s.clear()
    s.bar('Next')
    s.playing('the second preset')
    out['second'] = s.ev('[__pedal.chain.P.map(x => x.type), __pedal.chain.Q.map(x => x.type), __pedal.cap_slot, __pedal.ir_slot, __pedal.cap.data.length, __pedal.cap.trim, __pedal.ir.data.length, __pedal.gain, S.model, __pedal.scenes]')
    require(out['second'] == [['boost'], ['ir'], -1, -1, 600, 1.5, 1200, [2, -4], 'Stranger amp', '00000000'], f"the second preset: {out['second']}")
    s.same(mark, 'the second preset', heard=False)
    s.bar('Next')
    s.playing('the third preset')
    notes = ' '.join(s.ev('hrTry.notes'))
    require(s.ev('[__pedal.chain.P.map(x => x.type), __pedal.chain.Q.map(x => x.type)]') == [['gate'], ['ir']] and all(x in notes for x in ('wonderfx', 'No such amp', 'Nowhere')), f'the third preset: {notes}')
    require(s.ev('[...document.querySelectorAll("#hrTry button")].find(e => e.innerText === "Next").disabled'), 'there is a next after the last')
    s.cdp.screenshot(s.output / 'try-lacking.png')
    s.bar('Previous')
    s.playing('the second again')
    require(s.ev('__pedal.cap.data.length') == 600 and s.ev('hrTry.at') == 1, 'the second again')
    # quieter, louder, and not above the limit
    s.bar('Quieter')
    s.wait('__pedal.gain[1] === -7', 'quieter')
    for _ in range(5):
        s.wait('![...document.querySelectorAll("#hrTry button")].find(e => e.innerText === "Louder").disabled || hrTry.volume.now === hrTry.volume.limit', 'louder')
        s.ev('[...document.querySelectorAll("#hrTry button")].find(e => e.innerText === "Louder").click()')
        time.sleep(0.3)
    require(s.ev('__pedal.gain')[1] == 0 and max(s.ev('__pedal.log')) <= 0, f"louder than the limit: {s.ev('__pedal.gain')}")
    # back: exactly what played, with the changes that were not saved
    s.bar('Back to 1C')
    s.off('back')
    s.told('as it was')
    s.same(mark, 'back')
    require(s.ev('curPreset') == 2 and s.ev('edCount()') >= 1 and changes >= 1 and not s.ev('document.getElementById("saveBar").hidden') and 'Not saved' in s.ev('document.getElementById("saveTxt").innerText'), 'the changes that were not saved are not shown')
    out['back'] = s.ev('document.getElementById("saveTxt").innerText')
    # and they can still be saved: what is stored then is what was heard
    s.ev('void hrSave()')
    s.dialog('Save changes')
    s.press('Only scene 1')
    s.wait('edCount() === 0 && ' + QUIET, 'the changes saved after a try')
    require(s.ev('__pedal.store[2].chain.Q.find(x => x.type === "gate").p[0]') == -33 and s.ev('__pedal.store[2].gain') == [1, -6], 'what is saved after a try')
    return out


def keep_preset(s):
    """Keep: the slot and the name, the capture and the cab IR it brings, the volume as it is heard; and nothing else is written."""
    before = json.loads(s.mark()[0])
    s.ev('void hrTry.files("preset", [__file()])')
    s.dialog('Try 3 presets')
    s.ev('document.querySelectorAll(".mdlg input[type=radio]")[1].click()')
    s.press('Try')
    s.playing('the preset with its files')
    s.bar('Quieter')
    s.wait('__pedal.gain[1] === -7', 'quieter')
    s.ev('document.dispatchEvent(new KeyboardEvent("keydown", {key: "s", ctrlKey: true, bubbles: true, cancelable: true}))')
    s.dialog('Save this preset')
    s.press('Cancel')
    s.wait('hrTry.state === "playing" && ' + QUIET, 'still trying')
    s.bar('Keep…')
    s.dialog('Save this preset')
    require(s.ev('document.querySelector(".mdlg input").value') == 'With its files', 'the name that is offered')
    slot = s.ev('+document.querySelector(".mdlg select").value')
    require(not s.ev(f'!!__pedal.store[{slot}]'), 'the slot that is offered is not free')
    s.ev('document.querySelector(".mdlg input").value = "Kept \'one\' è"')
    s.press('Save')
    s.dialog('Keep the cab IR too')
    s.press('Save in free slots')
    s.dialog('Keep the capture too')
    s.ev('document.querySelector(".mdlg .mdlg-ok").click()')
    s.off('kept')
    s.wait(f'curPreset === {slot} && ' + QUIET, 'the preset that is kept')
    after = json.loads(s.ev('__pedal.kept()'))
    new = [k for k in after[0] if k not in before[0]]
    caps, irs = [x for x in after[2] if x not in before[2]], [x for x in after[3] if x not in before[3]]
    stored = s.ev(f'[__pedal.presets[{slot}], __pedal.store[{slot}].c_slot, __pedal.store[{slot}].i_slot, __pedal.store[{slot}].gain, __pedal.store[{slot}].chain.Q.map(x => x.type), __pedal.store[{slot}].scenes[0]]')
    require(new == [str(slot)] and len(caps) == 1 and len(irs) == 1 and [int(caps[0][0]), int(irs[0][0])] == stored[1:3] and [caps[0][1], irs[0][1]] == ['Stranger amp', 'Stranger cab'], f'what is kept: {new}, {caps}, {irs}, {stored}')
    require(stored[3] == [2, -7] and stored[4] == ['ir'] and stored[5] == '1' and stored[0] == 'Kept one e', f'the preset that is kept: {stored}')
    require({k: v for k, v in after[1].items() if k != str(slot)} == before[1], 'another preset was changed')
    words = {c.split()[0] for c in s.ev('__pedal.writes')}
    require(words == {'PSAVE', 'SNAPSAVE', 'CSAVE', 'ISAVE'}, f'what was written: {words}')
    require(s.ev('[...document.querySelectorAll("#saveBar .btn")].some(e => e.offsetParent)') and s.ev('S.capSlot') == stored[1], 'the line of the saving is not back')
    s.ev('void (async () => { await loadPreset(2); for (const c of ["PDEL ' + str(slot) + '", "CDEL ' + str(stored[1]) + '", "IDEL ' + str(stored[2]) + '"]) await Pedal.cmd(c, c.split(" ")[0], 5000); await loadPresets(); window.__k = true; })()')
    s.wait('window.__k === true && curPreset === 2 && __pedal.cap_slot === 9 && ' + QUIET, 'home again')
    return {'slot': slot, 'stored': stored}


def losses(s):
    """What could not come back is asked first: changed blocks, the scenes of a preset without a slot, a capture and a cab IR in no slot."""
    out = {}
    s.ev('void addFx("boost")')
    s.wait('S.chain.Q.length === 4 && edCount() > 0 && ' + QUIET, 'a block more')
    mark = s.mark()
    def start():
        s.ev('void hrTry.files("preset", [__file()])')
        s.dialog('Try 3 presets')
        s.press('Try')
        return s.dialog('without losing anything')
    out['blocks'] = start()
    require('The blocks of 1C were changed and are not saved' in out['blocks'], out['blocks'])
    s.cdp.screenshot(s.output / 'try-losses.png')
    s.press('Cancel')
    s.off('no')
    s.same(mark, 'a try that was refused')
    start()
    s.press('Save it first')
    s.playing('after saving')
    require(s.ev('__pedal.store[2].chain.Q.length') == 4, 'it was not saved first')
    mark2 = s.ev('__pedal.kept()')
    s.bar('Back to 1C')
    s.off('back')
    s.told('as it was')
    require(s.ev('__pedal.kept()') == mark2 and s.ev('__pedal.chain.Q.length') == 4 and s.ev('edCount()') == 0, 'back after saving first')
    # a capture and a cab IR that were only loaded
    s.ev('__pedal.cap = {data: new Uint8Array(4892).fill(3), trim: 0}; __pedal.cap_slot = -1; __pedal.ir = {...__pedal.irs[0], data: __pedal.irs[0].data.slice(0, 900)}; __pedal.ir_slot = -1; void loadModelName().then(() => setModel("Only loaded"))')
    s.idle()
    time.sleep(0.5)
    mark = s.mark()
    s.ev('void hrTry.files("preset", [__file()])')
    s.dialog('Try 3 presets')
    s.press('Try')
    out['files'] = s.dialog('without losing anything')
    require('"Only loaded"' in out['files'] and 'The cab IR that plays is in no slot' in out['files'], out['files'])
    s.press('Cancel')
    s.off('no')
    s.same(mark, 'a try that was refused')
    s.ev(f'void hrTry.files("ir", [{wav(21)}])')
    require('cab IR that plays is in no slot' in s.dialog('without losing anything'), 'the cab IR is not asked for')
    s.press('Save it first')
    s.playing('a cab IR after saving the one before')
    saved = s.ev('Object.keys(__pedal.irs).map(Number)')
    s.bar('Back to 1C')
    s.off('back')
    s.told('as it was')
    require(len(saved) == 3 and s.ev('__pedal.ir.data.length') == 900 and s.ev('__pedal.ir_slot') == next(k for k in saved if k not in (0, 4)), f"the cab IR before: {saved}, {s.ev('[__pedal.ir_slot, __pedal.ir.data.length]')}")
    # tried anyway: what does not come back is said
    s.ev(f'void hrTry.files("capture", [{NAM.replace("__NAME__", "Try amp")}])')
    s.dialog('without losing anything')
    s.press('Try anyway')
    s.playing('a capture anyway')
    s.clear()
    s.bar('Back to 1C')
    s.off('back')
    s.told('Not as before: the capture')
    s.ev('void (async () => { await Pedal.cmd("IDEL ' + str(next(k for k in saved if k not in (0, 4))) + '", "IDEL", 5000); await loadPreset(2); window.__l = true; })()')
    s.wait('window.__l === true && __pedal.cap_slot === 9 && __pedal.ir_slot === 4 && edCount() === 0 && ' + QUIET, 'home again')
    # another capture and cab than the preset's own, not saved: they come back, and are still a change
    s.ev('void (async () => { await uploadIrs([' + wav(13) + '], 5); closeLib(); await useSlot(false, 5, "Cab 13"); window.__u = true; })()')
    s.wait('window.__u === true && __pedal.ir_slot === 5 && edCount() > 0 && ' + QUIET, 'another cab, not saved')
    mark = s.mark()
    s.ev('void hrTry.files("preset", [__file()])')
    s.dialog('Try 3 presets')
    s.press('Try')
    s.playing('a try over another cab')
    s.bar('Back to 1C')
    s.off('back')
    s.told('as it was')
    s.same(mark, 'another cab, not saved')
    require(s.ev('edCount()') > 0 and 'Not saved' in s.ev('document.getElementById("saveTxt").innerText'), 'another cab is not a change any more')
    s.ev('void (async () => { await loadPreset(2); await Pedal.cmd("IDEL 5", "IDEL", 5000); window.__u2 = true; })()')
    s.wait('window.__u2 === true && __pedal.ir_slot === 4 && ' + QUIET, 'home again')
    # a preset without a slot and without scenes comes back too: it is made again
    s.ev('void (async () => { await Pedal.cmd("PNEW", "PNEW"); await loadChain(); await loadSnaps(); await loadPresets(); await Pedal.cmd("GAIN", "GAIN"); await Pedal.cmd("GAIN 3 -8", "GAIN"); await addFx("comp"); await addFx("gate"); '
         'const c = S.chain.Q[0]; await Pedal.cmd(`FXP ${c.id} 1 55`, "FXP"); await loadChain(); window.__n = true; })()')
    s.wait('window.__n === true && curPreset === -1 && S.chain.Q.length === 2 && ' + QUIET, 'a preset without a slot')
    mark = s.mark()
    s.ev('void hrTry.files("preset", [__file()])')
    s.dialog('Try 3 presets')
    s.press('Try')
    s.playing('a try from a preset without a slot')
    s.bar('Back')
    s.off('back')
    s.told('as it was')
    s.same(mark, 'a preset without a slot')
    s.ev('void (async () => { await Pedal.cmd("SNAPSAVE 0", "SNAPSAVE"); await loadSnaps(); window.__n2 = true; })()')
    s.wait('window.__n2 === true && ' + QUIET, 'a scene of it')
    out['scenes'] = start()
    require('its scenes are not saved' in out['scenes'], out['scenes'])
    s.press('Cancel')
    s.off('no')
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home again')
    return out


# A NAM A2-Lite capture of the right shape with made-up weights, as a file a person downloads; the seed is in its name.
NAM = '''((name, first) => { const k = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], d = [1, 2, 4, 8, 16, 32, 64, 128, 1, 2]; let seed = first; const C = 3, hk = 16;
  let n = C; for (const x of k) n += C * C * x + C + C + C * C + C; n += C * hk + 1 + 1;
  const weights = Array.from({length: n}, () => { seed = seed * 16807 % 2147483647; return (seed / 2147483647 - .5) * .3; });
  const model = {version: "0.7.0", architecture: "WaveNet", sample_rate: 48000, metadata: {name, input_level_dbu: 12.5}, config: {head: null, head_scale: .5, layers: [{
    input_size: 1, condition_size: 1, channels: C, kernel_sizes: k, dilations: d, activation: {type: "LeakyReLU", negative_slope: .01},
    layer1x1: {active: true, groups: 1}, head: {out_channels: 1, kernel_size: hk, bias: true}}]}, weights};
  return new File([JSON.stringify(model)], name + ".nam", {type: "application/json"}); })("__NAME__", "__NAME__".length * 7)'''


def captures(s):
    """Captures from files: heard without a slot, one after the other; back; a file that is wrong; kept in a free slot and over another."""
    out = {}
    nam = lambda n: NAM.replace('__NAME__', n)
    s.ev(f'window.__nams = [{nam("First amp")}, new File(["{{}}"], "Wrong.nam"), {nam("Second amp x")}]')
    mark = s.mark()
    s.ev('void hrTry.files("capture", __nams)')
    s.playing('the first capture')
    out['first'] = s.ev('[__pedal.cap_slot, __pedal.current, S.model, __pedal.gain, __pedal.sent.filter(c => /^CTRIM live/.test(c)).length > 0]')
    require(out['first'][:4] == [-1, 2, 'First amp', [1, -6]], f"the first capture: {out['first']}")
    require(s.ev('__pedal.log')[0] == -30 and max(s.ev('__pedal.log')) == -6, f"its volume: {s.ev('__pedal.log')}")
    s.same(mark, 'a capture', heard=False)
    s.cdp.screenshot(s.output / 'try-capture.png')
    s.clear()
    s.bar('Next')
    s.wait('hrTry.state === "failed" && ' + QUIET, 'a file that is wrong', 60)
    require('Wrong' in s.ev('document.getElementById("hrTry").innerText'), 'the bar of a failed one')
    s.same(mark, 'after a file that is wrong')
    s.bar('Next')
    s.playing('the one after it')
    require(s.ev('S.model') == 'Second amp x', 'the capture after a wrong one')
    # a knob that is turned meanwhile is as it was, and is no change that is not saved
    s.ev('void (async () => { const g = S.chain.Q.find(x => x.type === "gate"); await Pedal.cmd(`FXP ${g.id} 0 -44`, "FXP"); edMark("p", {id: g.id, idx: 0, v: -44}); await toggle(g.id); window.__g = true; })()')
    s.wait('window.__g === true && edCount() > 0 && ' + QUIET, 'a knob turned while trying')
    s.bar('Back to 1C')
    s.off('back')
    s.same(mark, 'back from captures')
    require(s.ev('S.capSlot') == 9, 'the page shows another capture')
    require(s.ev('edCount()') == 0 and 'Not saved' not in s.ev('document.getElementById("saveTxt").innerText'), 'what was turned while trying counts as a change')
    # the pedal refuses it at the end of the upload
    s.ev('__pedal.fail = line => line.startsWith("LDEND") ? ["LOAD rc=-100 name=\'\' audio=0"] : null; void hrTry.files("capture", [__nams[0]])')
    s.wait('hrTry.state === "failed" && ' + QUIET, 'a capture the pedal refuses', 60)
    s.ev('__pedal.fail = null')
    s.bar('Close')
    s.off('closed')
    s.same(mark, 'after a capture the pedal refuses')
    require(s.ev('__pedal.audio') == 2, 'the audio stays off')
    # a byte lost on the way is sent again (page's own), and stop in the middle
    s.ev('window.__slow = true; __pedal.fail = null; void hrTry.files("capture", [__nams[2]])')
    s.wait('hrTry.state === "loading"', 'loading')
    s.ev('void hrTry.back()')
    s.off('stopped')
    s.same(mark, 'stopped in the middle')
    # an amp that is off, and none at all: on while it is tried, and off again
    for words, what in ((['AMP 0'], 'off'), (['AMPX 0'], 'none')):
        s.ev(f'void (async () => {{ for (const c of {json.dumps(words)}) await Pedal.cmd(c, c.split(" ")[0] + " "); await loadChain(); window.__amp = "{what}"; }})()')
        s.wait(f'window.__amp === "{what}" && ' + QUIET, what)
        m = s.mark()
        s.ev('void hrTry.files("capture", [__nams[0]])')
        s.playing('with the amp ' + what)
        require(s.ev('[__pedal.amp, __pedal.ampx ?? 1]') == [1, 1], 'the amp does not play')
        s.bar('Back to 1C')
        s.off('back')
        s.same(m, 'the amp ' + what)
        s.ev('void (async () => { await Pedal.cmd("AMPX 1", "AMPX "); await Pedal.cmd("AMP 1", "AMP "); await loadChain(); window.__amp = 0; })()')
        s.wait('window.__amp === 0 && ' + QUIET, 'the amp again')
    # kept: a free slot, then over another after the question
    s.ev('void hrTry.files("capture", [__nams[0]])')
    s.playing('a capture to keep')
    s.bar('Keep…')
    s.dialog('Keep this capture')
    out['slot'] = s.ev('+document.querySelector(".mdlg select").value')
    require(out['slot'] == 0 and s.ev('document.querySelector(".mdlg input").value') == 'First amp', 'what is offered')
    s.cdp.screenshot(s.output / 'try-keep.png')
    s.ev('(() => { const e = document.querySelector(".mdlg select"); e.value = "9"; e.onchange(); })()')
    require('Replaces "A2"' in s.ev('document.querySelector(".mdlg").innerText'), 'it does not say what is replaced')
    s.press('Keep')
    s.dialog('Replace it?')
    s.press('Cancel')
    s.wait('hrTry.state === "playing" && ' + QUIET, 'not replaced')
    s.same(mark, 'not replaced', heard=False)
    s.bar('Keep…')
    s.dialog('Keep this capture')
    s.press('Keep')
    s.off('kept')
    s.told('is kept in slot 1')
    require(s.ev('[__pedal.caps[0].name, __pedal.cap_slot, __pedal.gain, __pedal.writes, edCount() > 0]') == ['First amp', 0, [1, -6], ['CSAVE 0 First amp'], True], f"kept: {s.ev('[__pedal.caps[0], __pedal.cap_slot, __pedal.gain, __pedal.writes]')}")
    s.ev('void (async () => { await Pedal.cmd("CLOAD 9", "CLOAD", 8000); await Pedal.cmd("CDEL 0", "CDEL", 8000); await loadPreset(2); window.__c = true; })()')
    s.wait('window.__c === true && __pedal.cap_slot === 9 && ' + QUIET, 'home again')
    return out


def irs(s):
    """Cab IRs from files: in the cab blocks that are there, in one that is added, over a block's own; back; kept."""
    out = {}
    s.ev(f'window.__wavs = [{wav(31)}, {wav(32, 5000)}, new File(["RIFFxxxxWAVE"], "Broken.wav")]')
    mark = s.mark()
    s.ev('void hrTry.files("ir", __wavs)')
    s.playing('the first cab IR')
    out['first'] = s.ev('[__pedal.ir_slot, __pedal.ir.n, __pedal.chain.Q.filter(x => x.type === "ir").length]')
    require(out['first'][0] == -1 and out['first'][2] == 1 and s.ev('__pedal.log')[0] == -30, f"the first cab IR: {out['first']}")
    s.same(mark, 'a cab IR', heard=False)
    s.bar('Next')
    s.playing('the second cab IR')
    require('shortened' in ' '.join(s.ev('hrTry.notes')), f"a long one: {s.ev('hrTry.notes')}")
    s.bar('Next')
    s.wait('hrTry.state === "failed" && ' + QUIET, 'a broken one', 40)
    s.same(mark, 'after a broken one')
    s.bar('Close')
    s.off('closed')
    # a block with its own IR plays the one that is tried, and gets its own back
    s.ev('void setBlockIr(S.chain.Q.find(x => x.type === "ir").id, 0, "Cab 11")')
    s.wait('__pedal.chain.Q.find(x => x.type === "ir").p[2] === 1 && ' + QUIET, "a block's own IR")
    m = s.mark()
    s.ev('void hrTry.files("ir", [__wavs[0]])')
    s.playing('over a block\'s own')
    require(s.ev('__pedal.chain.Q.find(x => x.type === "ir").p[2]') == 0, 'the block still plays its own')
    s.bar('Back to 1C')
    s.off('back')
    s.same(m, "a block's own IR again")
    # no cab block: one is added and taken away
    s.ev('void (async () => { await Pedal.cmd(`FXR ${S.chain.Q.find(x => x.type === "ir").id}`, "FXR"); await loadChain(); window.__r = true; })()')
    s.wait('window.__r === true && ' + QUIET, 'no cab block')
    m = s.mark()
    s.ev('void hrTry.files("ir", [__wavs[0], __wavs[1]])')
    s.playing('without a cab block')
    require(s.ev('__pedal.chain.Q.filter(x => x.type === "ir").length') == 1 and 'one is added while you try' in ' '.join(s.ev('hrTry.notes')), 'the cab block that is added')
    s.bar('Next')
    s.playing('the second, in the same block')
    require(s.ev('__pedal.chain.Q.filter(x => x.type === "ir").length') == 1, 'a second block was added')
    s.bar('Back to 1C')
    s.off('back')
    s.same(m, 'the block that was added')
    # kept, not in the small slot when it is long
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && edCount() === 0 && S.chain.Q.some(x => x.type === "ir") && ' + QUIET, 'home again')
    s.mark()
    s.ev('void hrTry.files("ir", [__wavs[0]])')
    s.playing('a cab IR to keep')
    s.bar('Keep…')
    s.dialog('Keep this cab IR')
    out['slots'] = s.ev('[...document.querySelectorAll(".mdlg option")].map(o => o.textContent)')
    require(len(out['slots']) == 7 and out['slots'][1] == '2 · free', f"the slots of a long one: {out['slots']}")
    s.press('Keep')
    s.off('kept')
    require(s.ev('[__pedal.irs[1].name, __pedal.ir_slot, __pedal.writes]') == ['Cab 31', 1, ['ISAVE 1 Cab 31']], f"kept: {s.ev('__pedal.writes')}")
    s.ev('void (async () => { await Pedal.cmd("IDEL 1", "IDEL", 8000); await loadPreset(2); window.__i = true; })()')
    s.wait('window.__i === true && __pedal.ir_slot === 4 && ' + QUIET, 'home again')
    return out


def trouble(s):
    """A footswitch, a disconnection, a restart, errors and a loud preset in the middle; a preset of the list; a file made to do harm."""
    out = {}
    def begin(at=1):
        s.ev('void hrTry.files("preset", [__file()])')
        s.dialog('Try 3 presets')
        s.ev(f'document.querySelectorAll(".mdlg input[type=radio]")[{at}].click()')
        s.press('Try')
    mark = s.mark()
    begin()
    s.playing('a preset')
    s.clear()
    s.ev('__pedal.press(5)')
    s.off('a footswitch')
    s.told('Another preset was chosen on the pedal')
    s.same(mark, 'a footswitch', heard=False)
    require(s.ev('[curPreset, __pedal.current, __pedal.cap_slot, __pedal.ir_slot, __pedal.gain]') == [5, 5, 9, 0, [1, -3]], f"after a footswitch: {s.ev('[curPreset, __pedal.current, __pedal.cap_slot, __pedal.ir_slot, __pedal.gain]')}")
    # a switch that is held saves what is tried: that is the person's, and it is said
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    begin(0)
    s.playing('a preset to hold a switch for')
    s.clear()
    s.ev('__pedal.presets[7] = "Preset 3B"; __pedal.current = 7; __pedal.store[7] = __pedal.keep(); __pedal.changes++')
    s.off('a switch that is held')
    s.told('The pedal saved it in 3B')
    require(s.ev('[curPreset, __pedal.gain, __pedal.chain.Q.map(x => x.type)]') == [7, [2, 0], ['comp']] and not any('nothing of it was saved' in x for x in s.toasts()), 'after a switch that was held')
    s.ev('void (async () => { await loadPreset(2); await Pedal.cmd("PDEL 7", "PDEL", 5000); await loadPresets(); window.__h = true; })()')
    s.wait('window.__h === true && curPreset === 2 && ' + QUIET, 'home')
    # in the middle of the loading, at a scene: nothing of it is written to the preset that was chosen
    for word in ('FXA', 'SNAPSAVE'):
        s.ev('void loadPreset(2)')
        s.wait('curPreset === 2 && ' + QUIET, 'home')
        mark = s.mark()
        s.ev(f'(() => {{ let n = 0; __pedal.hook = line => {{ if (line.startsWith("{word}") && ++n === 1) {{ __pedal.hook = null; setTimeout(() => {{ __pedal.press(5); __pedal.press(5); }}, 0); }} }}; }})()')
        begin(0)
        s.wait('__pedal.hook === null && (hrTry.state === "failed" || hrTry.state === "off") && ' + QUIET, f'a footswitch at {word}', 60)
        if s.ev('hrTry.state') == 'failed':
            s.bar('Close')
            s.off('closed')
        s.same(mark, f'a footswitch at {word}', heard=False)
    # one press in the middle only closes the tuner: the loading stops before a scene is made
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    mark = s.mark()
    s.ev('__pedal.hook = line => { if (line.startsWith("FXA")) { __pedal.hook = null; __pedal.press(5); } }')
    begin(0)
    s.wait('hrTry.state === "failed" && ' + QUIET, 'one press in the middle', 60)
    require('a switch was pressed on the pedal' in s.ev('document.getElementById("hrTry").innerText'), 'what is said of one press')
    s.bar('Close')
    s.off('closed')
    s.same(mark, 'one press in the middle')
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    # with a capture, the preset that is chosen has none of its own: it plays with the one of before
    s.ev('__pedal.store[5].c_slot = -1; void hrTry.files("capture", [__nams[0]])')
    s.playing('a capture')
    s.ev('__pedal.press(5)')
    s.off('a footswitch, with a capture')
    require(s.ev('[curPreset, __pedal.cap_slot]') == [5, 9], 'the capture before is not back')
    s.ev('__pedal.store[5].c_slot = 9; void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    # the cable: what is tried goes on, and can still go back; a restart ends it
    mark = s.mark()
    begin()
    s.playing('a preset')
    s.ev('onDisconnected(new Error("check"))')
    s.wait('hrTry.state === "lost" && !document.getElementById("hrTry").hidden', 'no pedal')
    require('not saved on it' in s.ev('document.getElementById("hrTry").innerText'), 'what the bar says without a pedal')
    time.sleep(0.5)
    require(s.ev('(() => { const r = document.querySelector("#hrTry .tabout").getBoundingClientRect(); return !!document.elementFromPoint(r.left + 20, r.top + r.height / 2)?.closest("#hrTry"); })()'), 'the bar is under the veil')
    s.cdp.screenshot(s.output / 'try-lost.png')
    def again():
        s.ev('void connect()')
        s.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer && ' + QUIET, 'connected again', 60)
    again()
    s.playing('the try goes on')
    s.bar('Back to 1C')
    s.off('back')
    s.same(mark, 'back after a disconnection')
    begin()
    s.playing('a preset')
    s.ev('onDisconnected(new Error("check")); __pedal.restart()')
    s.wait('hrTry.state === "lost"', 'no pedal')
    again()
    s.off('a restart')
    s.told('started again with its own presets')
    s.same(mark, 'a restart', heard=False)
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    # the cable in the middle of the loading: the pedal is put back when it returns
    mark = s.mark()
    s.ev('__pedal.hook = line => { if (line.startsWith("FXA")) { __pedal.hook = null; setTimeout(() => onDisconnected(new Error("check")), 0); } }')
    begin()
    s.wait('hrTry.state === "lost" && !S.connected', 'no pedal in the middle', 60)
    again()
    s.wait('hrTry.state === "failed" && ' + QUIET, 'put back', 60)
    s.same(mark, 'the cable in the middle')
    s.bar('Close')
    s.off('closed')
    # no answer in the middle, and while going back
    s.ev('__pedal.fail = line => line === "PNEW" ? [] : null')
    begin()
    s.wait('hrTry.state === "failed" && ' + QUIET, 'no answer', 60)
    s.ev('__pedal.fail = null')
    s.same(mark, 'no answer')
    s.bar('Next')
    s.playing('the next after no answer')
    s.ev('__pedal.fail = line => line.startsWith("PLOAD") ? ["ERR PLOAD flash"] : null')
    s.clear()
    s.bar('Back to 1C')
    s.told('It could not go back')
    s.ev('__pedal.fail = null')
    s.wait('hrTry.state === "playing" && ' + QUIET, 'still there')
    s.bar('Back to 1C')
    s.off('back at the second time')
    s.same(mark, 'back at the second time')
    # a loud one: it stops rising
    s.ev('__pedal.loud_at = -14')
    begin(0)
    s.playing('a loud preset')
    out['loud'] = s.ev('[__pedal.gain[1], Math.max(...__pedal.log.slice(__pedal.log.lastIndexOf(-30))), hrTry.volume.held, document.querySelector("#hrTry .tvol").innerText]')
    require(out['loud'][:2] == [-16, -14] and 'loud' in out['loud'][3], f"a loud preset: {out['loud']}")
    s.ev('__pedal.loud_at = null')
    # a preset of the list: back first, then that one
    s.ev('void loadPreset(5)')
    s.wait('hrTry.state === "off" && curPreset === 5 && __pedal.current === 5 && ' + QUIET, 'a preset of the list')
    s.same(mark, 'a preset of the list', heard=False)
    require(s.ev('__pedal.gain') == [1, -3], 'the preset of the list is not as it is')
    s.ev('void loadPreset(2)')
    s.wait('curPreset === 2 && ' + QUIET, 'home')
    # files that are no presets, or made to do harm
    mark = s.mark()
    s.ev('void hrTry.files("preset", [new File(["{}"], "a.json"), new File(["x"], "b.json"), new File(["x"], "c.exe")])')
    s.told('is not a HyperRig preset')
    require(not s.ev('!!document.querySelector(".mdlg")') and s.ev('hrTry.state') == 'off', 'a file that is no preset')
    bad = {'format': 'hyperrig-preset', 'version': 1, 'presets': [{'meta': {'name': 'x\r\nPDEL 2\r\n<img src=x onerror="__errors.push(1)">'}, 'sound': {'chain': [
        {'type': 'gate', 'id': 'a', 'params': {'umbral_db': 1e9, 'release_ms': -5}}, {'type': 'gate\nPDEL 2', 'id': 'b'}, {'type': 'constructor', 'id': 'c'}, {'amp': True}] + [{'type': 'boost'}] * 30,
        'gain_db': {'in': 500, 'out': 900}, 'scenes': [{'index': 0, 'name': 'a\r\nPSAVE 2 x', 'gain_db': {'in': 0, 'out': 900}, 'blocks': {}}], 'tempo_bpm_x10': 99999}}]}
    s.ev(f'void hrTry.files("preset", [new File([{json.dumps(json.dumps(bad))}], "bad.json")])')
    s.dialog('Try "x PDEL 2')
    require(not s.ev('!!document.querySelector(".mdlg img")'), 'a name became part of the page')
    s.press('Try')
    s.playing('a file made to do harm')
    lines = s.ev('__pedal.sent.slice(-260)')
    require(not [c for c in lines if c.startswith(('PDEL', 'PSAVE'))] and s.ev('__pedal.gain') == [12, 0] and s.ev('__pedal.bpm') == 3000 and s.ev('__pedal.chain.Q.length') <= 10, f"a file made to do harm: {s.ev('[__pedal.gain, __pedal.bpm]')}")
    s.same(mark, 'a file made to do harm', heard=False)
    s.bar('Back to 1C')
    s.off('back')
    s.same(mark, 'back from it')
    return out


def ways_in(s):
    """The buttons: beside the files of presets, and in the libraries."""
    s.idle()
    seen = s.ev('(() => { const b = document.getElementById("hrTryPreset").getBoundingClientRect(), p = document.querySelector(".side-card").getBoundingClientRect(); return [document.getElementById("hrTryPreset").innerText, Math.round(b.height), b.left >= p.left && b.right <= p.right]; })()')
    require(seen[0] == 'Try from files…' and 38 <= seen[1] <= 46 and seen[2], f'the button of presets: {seen}')
    s.cdp.screenshot(s.output / 'try-way-in.png')
    for kind in ('cap', 'ir'):
        s.ev(f'void openLib("{kind}")')
        s.wait('document.getElementById("lib").classList.contains("on") && ' + QUIET, 'the library')
        h = s.ev('[document.getElementById("hrTryFile").innerText, Math.round(document.getElementById("hrTryFile").getBoundingClientRect().height)]')
        require(h[0] == 'Try a file…' and 38 <= h[1] <= 46, f'the button of the library: {h}')
        s.cdp.screenshot(s.output / f'try-library-{kind}.png')
        s.ev('closeLib()')
    return seen


def run(bundle, output, page_class, steps=None):
    product = json.loads((Path(bundle) / 'editor/profile.json').read_bytes())['development']['product']
    page = page_class(bundle, output, f"HRID 1 {product['version']} {product['build_id']} banks=3")
    s, out = Steps(page, output), {}
    try:
        page.wait('window.__urOk === true && typeof hrTry === "object"', 'the page', 40)
        s.ev('document.querySelector(".ccall .tskip")?.click()')
        s.ev(MORE)
        s.ev('window.__said = []; { const f = toast; toast = (m, ...more) => { __said.push(String(m)); return f(m, ...more); }; }')
        s.ev('void connect()')
        page.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
        time.sleep(1.5)
        s.ev('document.querySelector(".ccall .tskip")?.click()')
        s.ready()
        for step in (ways_in, presets, keep_preset, losses, captures, irs, trouble):
            if steps is None or step.__name__ in steps or step is presets:
                out[step.__name__] = step(s)
        errors = s.ev('__errors')
        require(not errors, f'page errors: {errors}')
        return out
    except Exception:
        try:
            page.cdp.screenshot(output / 'try-failure.png')
        except Exception:
            pass
        raise
    finally:
        page.close()


def main(argv=None):
    from tools import check_mini_dev_editor as page_check
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args(argv)
    editor.check(args.bundle)
    output = args.output.resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    output.mkdir(parents=True)
    print(json.dumps({'kind': 'hyperrig-try-check', 'device_io': False, 'steps': run(args.bundle, output, page_check.Page, args.only), 'result': 'pass'}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
