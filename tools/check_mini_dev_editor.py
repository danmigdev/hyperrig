"""Use the development editor's page in an isolated headless browser with a simulated pedal. No device is opened.

The page of tools/build_mini_dev_editor.py runs unmodified. navigator.serial is replaced, before any page script, by a
simulated port whose pedal answers with the lines recorded from MINI v4 (tests/data/pedal_answers.json), an empty preset
store, and a chain, presets, scenes, stereo and footswitch settings that follow the commands. The check connects, taps the tempo,
types one, uses the tuner and the amp switch, makes presets, adds and moves blocks, follows a footswitch, uses scenes,
stereo, the footswitch panel and the stage view, as a person would, and reads back what the page sent and shows.
For the editor of a product build the pedal answers HRID and keeps captures and IRs; the check also looks at the three switches and at
banks above nine, measures every control of every view, uploads a .nam and a .wav, adds the block that was waiting for it, reads an IR back and deletes it, and connects a
second, a third and a fourth time, to a pedal with another build, to one without HRID and to a newer one: the page says so in plain words, and nothing that changes the pedal may be sent.

This says that the page and its policy do what they should with the firmware's documented answers. It is no test of a
pedal, its audio or its switches.

Usage, from the repository root:
    python -B tools/check_mini_dev_editor.py --bundle build/hyperrig-mini-dev-editor-NN --output build/CHECK-NN
"""
from __future__ import annotations

import argparse
from functools import partial
import http.server
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_mini_dev_editor as editor  # noqa: E402
from tools import page_driver as browser  # noqa: E402
from tools import simulated_globals  # noqa: E402
from tools import effects_reference  # noqa: E402

RECORDED = ROOT / 'tests/data/pedal_answers.json'          # {query: lines}, as a TANK-MINI with MINI v4 answered
require = editor.require
PEDAL = r'''
(() => {
  const recorded = __RECORDED__;
__GLOBALS__  const pedal = {amp: 1, ampeq: [0, 0, 0, 0, 0, 0], gain: [0, 0], bpm: 1200, tuner: [0, 1, 440], presets: {}, current: -1,
    scenes: "0".repeat(__SCENES__), scene: -1, names: Array(__SCENES__).fill(""), stereo: 0, chain: {P: [], Q: []}, store: {}, changes: 5, sent: [], opened: 0,
    layout: "factory", mode: "preset", fsa: [0, 1, 2, 3].map(f => [[1, f, 255], [[4, 9, 7, 3][f], 0, 255], [0, 0, 255]]), press_bits: [1, 1, 1, 1], saved_settings: 0,
    /* A footswitch selects a stored preset: the pedal changes by itself. */
    press(n) { if (!this.store[n]) return; this.load(n); this.changes++; this.events.push(n); },
    events: [],
    keep() { return JSON.parse(JSON.stringify({amp: this.amp, ampeq: this.ampeq, gain: this.gain, bpm: this.bpm, scenes: this.scenes,
      scene: this.scene, names: this.names, stereo: this.stereo, chain: this.chain, ampx: this.ampx ?? 1, mix: this.mix, xo: this.xo, outs: this.outs})); },
    outs: {}, at: "start",          // the output gains of scenes, where a check gave them some; what plays: a scene, or what a preset starts with
    load(n) { Object.assign(this, JSON.parse(JSON.stringify(this.store[n]))); this.current = n; this.outs = this.outs || {}; this.at = "start"; }};
  const types = {}; { let cur = null; for (const line of recorded["FXT"] || []) {
    let m = /^FXT (\d+) (\S+) cost=(\d+)(?:.* mem=(\d+))?/.exec(line); if (m) { cur = types[m[2]] = {id: +m[1], cost: +m[3], mem: +(m[4] || 0), p: [0, 0, 0, 0, 0, 0, 0]}; continue; }
    m = /^FXT\s+(\d+) \S+ -?\d+\.\.-?\d+ \((-?\d+)\)$/.exec(line); if (m && cur) cur.p[+m[1]] = +m[2]; } }
  const find = id => { for (const b of ["P", "Q"]) { const i = pedal.chain[b].findIndex(x => x.id === id); if (i >= 0) return [b, i, pedal.chain[b][i]]; } return null; };
  pedal.bank = 1;
  pedal.budget = pedal.room = Infinity; pedal.shown = "0/22718";      // what FXC finds room in, and what LVL says
  // the settings for every preset: the answers of tools/simulated_globals.py; a wrong answer instead of one, the load of the pedal beside the EQ
  pedal.globals = makeGlobals(); pedal.kept = ""; pedal.wrong = null; pedal.ticks = 0; pedal.refused_globals = 0;
  pedal.live = () => ({gain: pedal.gain[0], trim: Math.round(2 * (pedal.cap ? pedal.cap.trim : 0)), level: null, slot: pedal.cap_slot, audio: pedal.audio});
  pedal.reading = (peak, rms) => calibWindow(pedal.globals, pedal.live(), peak, rms);
  pedal.midi = {wanted: 0, port: 0, takes: 2, set: "010001141516171807" + "66" + "ff00000064".repeat(4),
    get(i) { return parseInt(this.set.slice(2 * i, 2 * i + 2), 16); }, knob(k) { return [0, 1, 2, 3, 4].map(i => this.get(10 + 5 * k + i)).join(); }};
  /* MIDI as the firmware answers it (mini/product/midi.c); takes: what becomes of the port when it is turned on. */
  function midiAnswer(a) {
    const m = pedal.midi, word = a[0] || "";
    if (word === "on" || word === "off") { m.port = word === "off" ? 0 : m.takes; m.wanted = m.port === 2 ? 1 : 0; }
    else if (/^=[0-9a-f]{60}$/.test(word)) m.set = word.slice(1);
    return [`MIDI ${m.port} ${m.wanted} ${m.set} 0 0`];
  }
  const settings = () => `FSMODE layout=${pedal.layout} mode=${pedal.mode} bank=${pedal.bank} bypass=0`;
  function panelAnswer(word, a) {
    if (word === "FSA") {
      if (a.length) { const [f, g, ...r] = a.map(Number); pedal.fsa[f][g] = r; return [`FSA end ok ${a.join(" ")}`]; }
      return [...pedal.fsa.flatMap((x, f) => x.map((r, g) => `FSA ${f} ${g} ${r.join(" ")}`)), "FSA end"];
    }
    if (word === "FSMODE") { const m = /^layout=(\w+)$/.exec(a[0] || ""); if (m) { if (pedal.layout !== m[1]) pedal.mode = "preset"; pedal.layout = m[1]; }
      const k = /^mode=(\w+)$/.exec(a[0] || ""); if (k) pedal.mode = k[1]; return [settings()]; }
    if (word === "FSPRESS") { if (a.length) pedal.press_bits[+a[0]] = +a[1]; return [`FSPRESS ${pedal.press_bits.join(" ")}`]; }
    if (word === "FSLED") return a.length ? [`FSLED ${a[0]} auto on=ffffff off=202020`] :
      [...[0, 1, 2, 3].map(f => `FSLED ${f} auto on=ffffff off=202020`), "FSLED end"];
    if (word === "LEDCFG") return ["LEDCFG bright=100 tuner=needle tap=1 meter=edit hold=1 anim=1 idle=0"];
    if (word === "FSDO") { const n = "abcd".indexOf(a[0]); if (n >= 0 && pedal.store[n]) pedal.press(n); return [settings()]; }
    if (word === "GSAVE") { pedal.saved_settings++; pedal.kept = JSON.stringify({...pedal.globals, pages: 0, cal: 0}); return globalAnswer(pedal.globals, pedal.live(), word, a); }
  }
  pedal.irs = {}; pedal.ir = null; pedal.ir_slot = -1; pedal.up = null;
  // a byte of a line lost on the way, as the pedal did on 2026-11-24: once at these places, or every time at one
  pedal.lose = []; pedal.loseAlways = -1;
  const lost = at => { if (at === pedal.loseAlways) return 1; const i = pedal.lose.indexOf(at); if (i < 0) return 0; pedal.lose.splice(i, 1); return 1; };
  const crc = data => { let c = -1; for (const b of data) { c ^= b; for (let k = 0; k < 8; k++) c = c & 1 ? c >>> 1 ^ 0xedb88320 : c >>> 1; } return ((c ^ -1) >>> 0).toString(16).padStart(8, "0"); };
  function irAnswer(word, a) {
    if (word === "IRBEGIN") { const n = +a[0]; pedal.up = n ? {n, gain: +a[1], fs: +a[2], data: new Uint8Array(2 * n)} : null; return [`OK IRBEGIN ${n}`]; }
    if (word === "IRB") { let k = 0; const at = +a[0], all = a[1].match(/../g).map(x => parseInt(x, 16)), part = all.slice(0, all.length - lost(at));
      if (pedal.up) for (; k < part.length && at + k < pedal.up.data.length; k++) pedal.up.data[at + k] = part[k]; return [`OK IRB ${at} ${k}`]; }
    if (word === "IREND") { const has = crc(pedal.up.data); if (has !== a[0]) return [`ERR IREND crc ${has} != ${a[0]}`];
      pedal.ir = pedal.up; pedal.ir_slot = -1; pedal.up = null; return [`IR ok ${pedal.ir.n} samples gain ${pedal.ir.gain} mdB fs ${pedal.ir.fs}`]; }
    if (word === "ILIST") return [...Object.entries(pedal.irs).map(([k, x]) => `IRS ${k} ${x.data.length} '${x.name}' fs=${x.fs}`), `ILIST end current=${pedal.ir_slot} slots=8`];
    if (word === "ISAVE") { if (!pedal.ir) return ["ERR ISAVE IR missing"]; const name = a.slice(1).join(" "); pedal.irs[a[0]] = {...pedal.ir, name}; pedal.ir_slot = +a[0];
      return [`ISAVE ok ${a[0]} '${name}' ${pedal.ir.n} samples fs=${pedal.ir.fs}`]; }
    const x = pedal.irs[word === "FXIR" ? a[1] : a[0]];
    if (!x) return [`ERR ${word} empty or invalid slot`];
    if (word === "ILOAD") { pedal.ir = x; pedal.ir_slot = +a[0]; return [`ILOAD ok ${a[0]}`]; }
    if (word === "IDEL") { delete pedal.irs[a[0]]; if (pedal.ir_slot === +a[0]) pedal.ir_slot = -1; return [`IDEL ok ${a[0]}`]; }
    if (word === "FXIR") { find(+a[0])[2].p[2] = +a[1] + 1; return [`FXIR ok ${a[0]} ${a[1]}`]; }
    if (word === "IREAD" && a.length === 1) return [`IREAD ${a[0]} len=${x.data.length} crc=${crc(x.data)} id=00000000 aux=${x.gain} fs=${x.fs} name='${x.name}'`];
    if (word === "IREAD") { const part = x.data.subarray(+a[1], +a[1] + 96); return [`IREAD ${a[0]} ${a[1]} ${part.length} ${crc(part)} ${btoa(String.fromCharCode(...part))}`]; }
  }
  // the pedal's own capture, kept in the library: what the sounds of the page are made of
  pedal.cap = {data: new Uint8Array(4892), trim: 0, name: "A2"}; pedal.caps = {9: pedal.cap}; pedal.cap_slot = 9; pedal.audio = 2; pedal.stops = 0;
  function captureAnswer(word, a) {
    if (word === "AUDIO") { if (a[0] === "OFF") { pedal.audio = 0; pedal.stops++; } if (a[0] === "A2L") pedal.audio = 2; return [`AUDIO ${pedal.audio} rc=0 ms=40`]; }
    if (word === "LDBEGIN") { const n = +a[0]; if (!n || n > 8192) return [`ERR LDBEGIN length ${n} (max 8192)`]; pedal.up = {n, data: new Uint8Array(n)}; return [`OK LDBEGIN ${n}`]; }
    if (word === "LDB") { let k = 0; const at = +a[0], part = a[1].match(/../g).map(x => parseInt(x, 16));
      if (pedal.up) for (; k < part.length && at + k < pedal.up.data.length; k++) pedal.up.data[at + k] = part[k]; return [`OK LDB ${at} ${k}`]; }
    if (word === "LDEND") { const has = crc(pedal.up.data); if (has !== a[0]) return [`ERR LDEND crc ${has} != ${a[0]}`];
      if (String.fromCharCode(...pedal.up.data.slice(0, 4)) !== "A2L1") return [`LOAD rc=-2 name='' audio=${pedal.audio}`];
      pedal.cap = {data: pedal.up.data, trim: 0}; pedal.cap_slot = -1; pedal.up = null; return [`LOAD rc=0 name='A2' layers=23 channels=3 audio=${pedal.audio} engine=A2L ms=30`]; }
    if (word === "CLIST") return [...Object.entries(pedal.caps).map(([k, x]) => `CAP ${k} ${x.data.length} '${x.name}' trim=${x.trim.toFixed(1)}`), `CLIST end current=${pedal.cap_slot} slots=15`];
    if (word === "CSAVE") { const live = pedal.cap || {data: new Uint8Array(4892), trim: 0}; const name = a.slice(1).join(" "); pedal.caps[a[0]] = {...live, name}; pedal.cap = pedal.caps[a[0]]; pedal.cap_slot = +a[0];
      return [`CSAVE ok ${a[0]} '${name}' ${live.data.length} B`]; }
    if (word === "CTRIM") { const k = a[0] === "live" ? pedal.cap_slot : +a[0], x = a[0] === "live" ? pedal.cap : pedal.caps[k]; if (!x) return ["ERR CTRIM"]; x.trim = +a[1];
      return [`CTRIM ok slot=${k} trim=${x.trim.toFixed(1)} saved=${a[0] === "live" ? 0 : 1}`]; }
    const x = pedal.caps[a[0]];
    if (!x) return [`ERR ${word} empty or invalid slot (-1)`];
    if (word === "CLOAD") { pedal.cap = x; pedal.cap_slot = +a[0]; return [`CLOAD ok ${a[0]} audio=${pedal.audio}`]; }
    if (word === "CDEL") { delete pedal.caps[a[0]]; if (pedal.cap_slot === +a[0]) pedal.cap_slot = -1; return [`CDEL ok ${a[0]}`]; }
    if (word === "CREAD" && a.length === 1) return [`CREAD ${a[0]} len=${x.data.length} crc=${crc(x.data)} id=00000000 aux=0 fs=0 name='${x.name}'`];
    if (word === "CREAD") { const part = x.data.subarray(+a[1], +a[1] + 96); return [`CREAD ${a[0]} ${a[1]} ${part.length} ${crc(part)} ${btoa(String.fromCharCode(...part))}`]; }
  }
  // The chain as the firmware keeps it (tools/check_mini_places.py): ten blocks in a section and sixteen in all, three splits in a section, a level and a
  // crossover for each place of a split. What it refuses is kept in "refusals".
  const none = () => ({P: [[0, 0], [0, 0], [0, 0]], Q: [[0, 0], [0, 0], [0, 0]]});
  pedal.mix = none(); pedal.xo = none(); pedal.refusals = [];
  const refused = text => { pedal.refusals.push(text); return [text]; };
  const splits = b => { let n = -1, before = false; return pedal.chain[b].map(x => { const on = x.lane > 0; if (on && !before) n++; before = on; return on ? n : -1; }); };
  // the knobs of the capture that plays, from what is behind it (docs/PARAMETRIC_NAM.md)
  function ampKnobs() {
    const d = pedal.cap && pedal.cap.data, out = [], v = d && new DataView(d.buffer, d.byteOffset, d.length), n = d ? d.length : 0;
    if (n > 60 && v.getUint16(n - 6, true) === 0x5041) {
      const at = n - v.getUint16(n - 8, true);
      for (let k = 0; k < d[at + 5]; k++) out.push("AMPK " + [...d.slice(at + 12 + 26 * k, at + 38 + 26 * k)].map(x => x.toString(16).padStart(2, "0")).join(""));
    }
    return [...out, "AMPK end"];
  }
  // the measure of loudness (mini/product/loudness.c) in the memory of REC and INJ: how loud each preset and scene is stands in pedal.loud, "preset,scene" or "preset,start"
  pedal.loud = {}; pedal.level = null; pedal.rec = null; pedal.inj = null; pedal.guitar = null; pedal.played = 0; pedal.strokes = 0; pedal.late = null; pedal.full = false; pedal.busy = 0;
  const endLevel = () => {
    const l = pedal.level; if (!l) return;
    pedal.level = pedal.rec = pedal.inj = null;
    if (l.preset !== pedal.current && pedal.store[l.preset]) { pedal.load(l.preset); pedal.changes++; }
    if (l.scene >= 0 && l.preset === pedal.current && l.scene !== pedal.scene) { pedal.scene = pedal.at = l.scene; if (pedal.outs[l.scene] !== undefined) pedal.gain = [pedal.gain[0], pedal.outs[l.scene]]; }
  };
  pedal.stopLevel = endLevel;                                  // a footswitch, or the pedal by itself
  function levelAnswer(word, a) {
    const r = pedal.rec, floatOf = v => new Uint32Array(Float32Array.of(v).buffer)[0];
    if (word === "REC") { if (pedal.full) return ["ERR REC out of memory"]; pedal.rec = {words: new Array(+a[1]).fill(0xdeadbeef)}; return [`REC tap=4 n=${a[1]} pos=0 scale=26 fs=48077`]; }
    if (word === "RECD") { if (!r || +a[0] >= r.words.length) return [`ERR RECD nothing at ${a[0]} (recorded 0)`];
      return [`RECD ${a[0]} ` + r.words.slice(+a[0], +a[0] + 24).map(w => (w >>> 0).toString(16).padStart(8, "0")).join("")]; }
    if (word === "INJBEGIN") { pedal.inj = new Uint8Array(2 * a[0]); return [`OK INJBEGIN ${a[0]}`]; }
    if (word === "INJB") { let k = 0; const at = +a[0], all = a[1].match(/../g), part = all.slice(0, all.length - lost(at)); if (!at) pedal.strokes++;
      if (pedal.inj) for (; k < part.length && at + k < pedal.inj.length; k++) pedal.inj[at + k] = parseInt(part[k], 16); return [`OK INJB ${at} ${k}`]; }
    const b = (a[0] || "").match(/../g)?.map(x => parseInt(x, 16)) || [], signed = v => v << 24 >> 24;
    if (b[0] === 1) { endLevel(); return ["HRLV 0 -1"]; }
    if (b[0] === 2) {
      const s = pedal.store[b[1]]; if (b.length !== 11 || !s) return [`HRLV ${s ? 2 : -4} -1`];
      if (b[2] !== 127) s.gain[1] = signed(b[2]);
      for (let k = 0; k < 8; k++) if (b[3 + k] !== 127) s.outs = {...s.outs, [k]: signed(b[3 + k])};
      return ["HRLV 0 -1"];
    }
    if (!pedal.level) pedal.level = {preset: pedal.current, scene: pedal.scene};
    if (b[0] >= 5 && (!r || r.words.length < (b[0] === 5 ? 1142 : 32 + b[4]))) return [`HRLV ${b[0]} ${r ? r.words[0] : -1}`];
    if (b[0] === 5) { r.mode = 5; r.words[0] = 0; return ["HRLV 0 0"]; }
    if (b[0] === 6) {
      const [, length, plays, before, total] = b, what = `${pedal.current},${pedal.at}`, base = pedal.loud[what] ?? -20, unsettled = pedal.unsettled === what && plays < 3;
      const part = v => floatOf(10 ** ((v + 0.691) / 10)), level = base + [0, 1.5, -1.5][(pedal.strokes - 1) % 3];
      r.mode = 6; r.heard = pedal.inj;
      if (pedal.late === what) pedal.und = (pedal.und || 0) + 1;
      r.words.splice(0, 3, total, Math.round(2 ** 26 * 10 ** (((pedal.peaks || {})[what] ?? base + 10) / 20)), 0);
      const echo = pedal.echo > 0 && pedal.echo--;
      for (let i = 0; i < total; i++) r.words[32 + i] = i < before / 4 ? echo ? part(level - 9) : 0 : part(echo ? level + 3 : i < (before + length) / 4 && unsettled ? level - 3 : level);
      return ["HRLV 0 0"];
    }
    if (r && r.mode === 5) {                                   // time goes by: a third of a second, or more than the ring holds
      const count = pedal.busy && pedal.played > 60000 ? (pedal.busy--, 9600) : 3840;
      for (let i = 0; i < count; i += 8, r.words[0] += 8, pedal.played += 8) { let w = 0; for (let k = 7; k >= 0; k--) w = w << 4 | parseInt(pedal.guitar[pedal.played + k] || "0", 16); r.words[32 + r.words[0] / 8 % 1024] = w >>> 0; }
    }
    return [`HRLV 0 ${r ? r.words[0] : -1}`];
  }
  function chainAnswer(word, a) {
    if (word === "FXA") {
      if (!types[a[2]]) return ["ERR FXA unknown effect"];
      if (a[2] === "ir" && !pedal.ir) return ["ERR FXA ir: no IR loaded (tankg_load_ir.py)"];
      if (pedal.chain[a[0]].length >= 10 || pedal.chain.P.length + pedal.chain.Q.length >= 16) return refused("ERR FXA bank full");
      const used = new Set([...pedal.chain.P, ...pedal.chain.Q].map(x => x.id)); let id = 0; while (used.has(id)) id++;
      pedal.chain[a[0]].splice(Math.min(+a[1], pedal.chain[a[0]].length), 0, {id, type: a[2], on: 1, p: types[a[2]].p.slice()});
      return [`FXA id=${id} ${a[2]}`, "FX cpu=490/21418 ticks (2%) mem_fx=0 B"];
    }
    if (word === "FXMIX" || word === "FXXO") {
      const of = word === "FXMIX" ? pedal.mix : pedal.xo, say = (b, g) => `${word} ${b} ${g} ${of[b][g].join(" ")}`;
      if (!a.length) return [...["P", "Q"].flatMap(b => [...Array(Math.max(...splits(b), -1) + 1).keys()].map(g => say(b, g))), word + " end"];
      if (+a[1] > 2) return [`ERR ${word} usage`];
      of[a[0]][+a[1]] = [+a[2], a[3] === undefined ? of[a[0]][+a[1]][1] : +a[3]];
      return [say(a[0], +a[1])];
    }
    if (word === "FXS") return [...["P", "Q"].flatMap(b => pedal.chain[b].map((x, i) =>
      `FX ${b}${i} id=${x.id} ${x.type} on=${x.on} p=${x.p.join(",")} ticks=${x.on ? 695 : 1857} l=${x.lane || 0} g=${splits(b)[i]} fu=0 mem=0`)),
      ...chainAnswer("FXMIX", []).slice(0, -1), ...chainAnswer("FXXO", []).slice(0, -1),
      `FXS amp=${pedal.ampx ?? 1} on=${pedal.amp}`, "FXS cpu=738/21418 ticks (3%) mem_fx=0 B", "FXS c1=0 a=0 wait=0/0 jobs=0 to=0 seq=0 skip=0 laneB par=0",
      "FXS eng=0 posts=0 takes=0 canc=0 lat=0/0 run=0",
      "FXS lockq=0 locks=1 spinfull=0 spinmax_us=2443 heavy=0 hspinfull=0 hspinmax_us=0 hsettle=0", "FXS peak=4406 ticks skipped=0"];
    if (word === "PNEW") { Object.assign(pedal, {chain: {P: [], Q: []}, current: -1, scenes: "0".repeat(__SCENES__), scene: -1, names: Array(__SCENES__).fill(""), amp: 1, ampx: 1, ampeq: [0, 0, 0, 0, 0, 0]}); return ["PNEW ok"]; }
    if (word === "FXC") {              // as mini/product/replace.c: the preset and the block are compared first, and what does not fit changes nothing
      const at = find(+a[1]), all = [...pedal.chain.P, ...pedal.chain.Q], sum = k => all.reduce((n, x) => n + (x !== at[2] && (x.on || k === "mem") ? types[x.type][k] : 0), 0);
      if (a.length !== 4) return ["ERR FXC <preset> <id> <type> <new type>"];
      if (+a[0] !== pedal.current) return ["ERR FXC another preset"];
      if (!at || at[2].type !== a[2]) return ["ERR FXC another block"];
      if (!types[a[3]]) return ["ERR FXC unknown effect"];
      if (a[3] === "ir" && !pedal.ir) return ["ERR FXC no IR loaded"];
      if (at[2].on && sum("cost") + types[a[3]].cost > pedal.budget) return ["ERR FXC not enough CPU"];
      if (at[2].on && sum("mem") + types[a[3]].mem > pedal.room) return [`ERR FXC out of memory (needs ${Math.ceil(types[a[3]].mem / 1024)} kB)`];
      const used = new Set(all.map(x => x.id)); let id = 0; while (used.has(id)) id++;
      if (id > 15) id = at[2].id;
      pedal.chain[at[0]][at[1]] = {id, type: a[3], on: at[2].on, lane: at[2].lane, p: types[a[3]].p.slice()};
      return [`FXC id=${id} ${a[3]}`, "FX cpu=490/21418 ticks (2%) mem_fx=0 B"];
    }
    const at = find(+a[0]);
    if (!at) return [`ERR ${word} no such block`];
    const [bank, index, block] = at;
    if (word === "FXP") { block.p[+a[1]] = +a[2]; return [`FXP ok ${a[2]}`]; }
    const many = () => ["P", "Q"].some(b => Math.max(...splits(b), -1) > 2);
    if (word === "FXL") { const was = block.lane; block.lane = +a[1]; if (many()) { block.lane = was; return refused("ERR FXL too many parallel groups (max 3 per bank)"); } return [`FXL ok ${a[0]} ${a[1]}`]; }
    if (word === "FXE") { block.on = +a[1]; return ["FXE ok cpu=0/20903 ticks (0%) mem_fx=0 B"]; }
    if (word === "FXR") { pedal.chain[bank].splice(index, 1); return ["FXR ok cpu=0/20762 ticks (0%) mem_fx=0 B"]; }
    if (word === "FXM") {
      if (bank !== a[1] && pedal.chain[a[1]].length >= 10) return refused("ERR FXM bank full");
      const was = JSON.stringify(pedal.chain);
      pedal.chain[bank].splice(index, 1); pedal.chain[a[1]].splice(Math.min(+a[2], pedal.chain[a[1]].length), 0, block);
      if (many()) { pedal.chain = JSON.parse(was); return refused("ERR FXM too many parallel groups (max 3 per bank)"); }
      return ["FXM ok"];
    }
  }
  function answer(line) {
    const word = line.split(" ")[0], a = line.split(" ").slice(1);
    if (pedal.hook) pedal.hook(line);
    { const own = pedal.before && pedal.before(line); if (own) return own; }
    if (line === "PING") return ["PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11"];
    if (line === "HRID") { const identity = __IDENTITY__; return [identity || "ERR unknown command"]; }
    if (word === "BPM") {
      if (a.length) pedal.bpm = +a[0];
      return [`BPM ${Math.floor(pedal.bpm / 10)}.${pedal.bpm % 10}`];
    }
    if (word === "TUNER") {
      a.forEach((v, i) => { pedal.tuner[i] = +v; });
      return [`TUNER ${pedal.tuner[0]} mute=${pedal.tuner[1]} ref=${pedal.tuner[2]}`];
    }
    if (line === "AMP" || word === "AMP") { if (a.length) pedal.amp = +a[0]; return [`AMP ${pedal.amp}`]; }
    if (word === "AMPX") { if (a.length) pedal.ampx = +a[0]; return [`AMPX ${pedal.ampx ?? 1} 0`]; }
    if (line === "AMPK") return ampKnobs();
    if (line === "AMPEQ info") return ["AMPEQ info volume=-2400..1200 bass=-1200..1200@100 mid=-1200..1200@650 treble=-1200..1200@2000 " +
      "presence=-1200..1200@4500 drive=-2400..2400"];
    if (word === "AMPEQ") {
      if (a.length === 2) pedal.ampeq[+a[0]] = +a[1]; else a.forEach((v, i) => { pedal.ampeq[i] = +v; });
      const [volume, bass, mid, treble, presence, drive] = pedal.ampeq;
      return [`AMPEQ volume=${volume} bass=${bass} mid=${mid} treble=${treble} presence=${presence} drive=${drive}`];
    }
    if (line === "TUNE") return pedal.tuner[0] ? ["TUNE A4 hz=440.00 cents=+0.0 conf=98 n=5 level=-200 ons=1"] : ["TUNE off"];
    if (["FSA", "FSMODE", "FSPRESS", "FSLED", "LEDCFG", "FSDO", "GSAVE"].includes(word)) return panelAnswer(word, a);
    if (["GEQ", "HPF", "LIM", "SPILL", "GLIDE", "SPUR", "CALIB"].includes(word)) {
      if (pedal.wrong && a.length) return [pedal.wrong];
      const lines = globalAnswer(pedal.globals, pedal.live(), word, a); if (lines[0].startsWith("ERR")) pedal.refused_globals++; return lines;
    }
    if (word === "MIDI") return midiAnswer(a);
    if (word === "STW") { if (a.length) pedal.stereo = +a[0]; return [`STW w=${pedal.stereo} cur=${pedal.stereo} live=0 cpu=0/21391 deg=0`]; }
    if (word === "SNAPNAME" && a.length) { pedal.names[+a[0]] = a.slice(1).join(" "); if (pedal.current >= 0 && pedal.store[pedal.current]) pedal.store[pedal.current].names = pedal.names.slice(); return [`SNAPNAME ok ${a[0]} '${pedal.names[+a[0]]}' preset=${pedal.current}`]; }
    if (word === "SNAPNAME") return [...pedal.names.map((x, k) => `SNAPNAME ${k} '${x}'`), "SNAPNAME end"];
    if (word === "SNAPDEL") { const s = pedal.scenes.split(""); s[+a[0]] = "0"; pedal.scenes = s.join(""); return [`SNAPDEL ok ${a[0]} preset=${pedal.current}`]; }
    if (line === "PNAME") return ["ERR PNAME 0..31 <name>"];
    if (word === "PNAME") { pedal.presets[a[0]] = a.slice(1).join(" "); return [`PNAME ok ${a[0]} '${pedal.presets[a[0]]}'`]; }
    if (word === "PDEL") { delete pedal.presets[a[0]]; delete pedal.store[a[0]]; return [`PDEL ok ${a[0]}`]; }
    if (word === "PCOLOR") return [`PCOLOR ${a[0] || "none"} preset=${pedal.current}`];
    if (["FXA", "FXR", "FXC", "FXP", "FXE", "FXM", "FXL", "FXS", "FXMIX", "FXXO", "PNEW"].includes(word) && (a.length || ["FXS", "FXMIX", "FXXO", "PNEW"].includes(word)))
      return chainAnswer(word, a);
    if (line === "PLIST") return [...Object.entries(pedal.presets).map(([n, name]) => { const s = pedal.store[n], fx =
        ["P", "Q"].flatMap(b => s.chain[b].map(x => b.toLowerCase() + types[x.type].id + ["", "a", "b"][x.lane || 0])).join(",");
      return `PRE ${n} ${s.chain.P.length + s.chain.Q.length} ${s.c_slot ?? -1} ${s.i_slot ?? -1} '${name}' t=${fx || "-"} s=${parseInt(s.scenes.split("").reverse().join(""), 2)}${s.ampx === 0 ? " amp=0" : ""}`; }),
                                  `PLIST end current=${pedal.current}`];
    if (word === "PSAVE") {
      pedal.presets[a[0]] = a.slice(1).join(" "); pedal.current = +a[0]; pedal.store[a[0]] = pedal.keep();
      return [`PSAVE ok ${a[0]} '${pedal.presets[a[0]]}' ${pedal.chain.P.length + pedal.chain.Q.length} blocks capture=${pedal.cap_slot} ir=-1`];
    }
    if (word === "PLOAD") {
      if (!pedal.store[a[0]]) return ["ERR PLOAD empty"];
      pedal.load(+a[0]); pedal.changes++;
      return [`PLOAD ok ${a[0]} '${pedal.presets[a[0]]}' missing=0 capture=-1 ir=-1 ms=0`];
    }
    if (/^SNAP \d$/.test(line)) { if (pedal.scenes[+a[0]] !== "1") return ["ERR SNAP empty"]; pedal.scene = +a[0]; pedal.at = +a[0];
      if (pedal.outs[a[0]] !== undefined) pedal.gain = [pedal.gain[0], pedal.outs[a[0]]]; return [`SNAP ok ${a[0]} missing=0 ms=0`]; }
    if (["HRLV", "REC", "RECD", "INJBEGIN", "INJB"].includes(word)) return levelAnswer(word, a);
    if (line === "SNAPS") return [`SNAPS ${pedal.scenes} current=${pedal.scene}`];
    if (word === "SNAPSAVE" && pedal.noRoom) return ["ERR SNAPSAVE no room for these scenes: take a block or a scene away"];
    if (word === "SNAPSAVE") {
      const s = pedal.scenes.split(""); s[+a[0]] = "1"; pedal.scenes = s.join(""); pedal.scene = +a[0];
      if (pedal.current >= 0) pedal.store[pedal.current] = pedal.keep();
      return [`SNAPSAVE ok ${a[0]} preset=${pedal.current}`];
    }
    if (word === "GAIN") { if (a.length) pedal.gain = a.map(Number); return [`GAIN in=${pedal.gain[0]} out=${pedal.gain[1]} dB`]; }
    if (["CLIST", "LDBEGIN", "LDB", "LDEND", "CSAVE", "CLOAD", "CDEL", "CREAD", "CTRIM", "AUDIO"].includes(word)) return captureAnswer(word, a);
    if (["ILIST", "IRBEGIN", "IRB", "IREND", "ISAVE", "ILOAD", "IDEL", "IREAD", "FXIR"].includes(word)) return irAnswer(word, a);
    if (line === "LVL") return [`LVL in=-240 out=-253 ci=0 co=0 fx=${pedal.shown !== "0/22718" ? pedal.shown : pedal.ticks + pedal.globals.geq.reduce((x, v, b) => x + (v ? b ? 580 : 635 : 0), 0) + "/22718"} mem=0 sk=0 m=${pedal.engine ?? 2} g=${pedal.gain.join("/")} b=${pedal.bpm} s=${pedal.scene} a=${pedal.amp} ` +
      `e=131732/154950 am=118688 c=${pedal.changes} p=${pedal.current} tu=${pedal.tuner[0]} lim=0 ce=0 und=${pedal.und || 0} ovl=0 cin=-241 ctg=-180 fm=${["factory", "scenes", "custom"].indexOf(pedal.layout)},${pedal.mode === "live" ? 1 : 0},${pedal.bank},${pedal.bypass || 0} stuck=0 bat=-1,0,1`];
    if (recorded[line]) return recorded[line];
    return ["ERR unknown command"];
  }
  class SerialPort extends EventTarget {
    getInfo() { return {usbVendorId: __VENDOR__, usbProductId: 0x5155}; }
    async open() {
      pedal.opened++;
      let push; const decoder = new TextDecoder(), encoder = new TextEncoder(); let partial = "";
      pedal.tell = line => push.enqueue(encoder.encode(line + "\n"));          // what the pedal says by itself
      this.readable = new ReadableStream({start: c => { push = c; }});
      pedal.unplug = () => { try { push.error(new Error("The device has been lost.")); } catch (e) {} };
      this.writable = new WritableStream({write: chunk => {
        partial += decoder.decode(chunk);
        for (let i; (i = partial.search(/[\r\n]/)) >= 0; partial = partial.slice(i + 1)) {
          const line = partial.slice(0, i).trim(); if (!line) continue;
          pedal.sent.push(line);
          setTimeout(() => { try { const said = answer(line); if (!(pedal.silent && pedal.silent.test(line))) push.enqueue(encoder.encode(said.join("\n") + "\n")); } catch (e) {} }, 5);
        }
      }});
    }
    async close() {} async forget() {} async setSignals() {} async getSignals() { return {}; }
  }
  globalThis.SerialPort = SerialPort;
  const port = new SerialPort(), serial = new EventTarget();
  serial.requestPort = async o => { pedal.asked = o; return port; }; serial.getPorts = async () => [];
  Object.defineProperty(navigator, "serial", {configurable: true, value: serial});
  for (const name of ["usb", "hid", "bluetooth"])
    Object.defineProperty(navigator, name, {configurable: true, value: undefined});
  globalThis.__pedal = pedal;
  globalThis.__errors = []; addEventListener("error", e => __errors.push(String(e.message)));
  addEventListener("unhandledrejection", e => __errors.push(String(e.reason)));
  window.open = () => null;
})();
'''


def recorded():
    """{query: lines} of the recorded v4 answers."""
    return json.loads(RECORDED.read_bytes())


# What a product build lists and MINI v4 does not: the lines the firmware sends for the acoustic block (tools/check_mini_effect_block.py) and for the
# harmonizer (tools/check_mini_harmonizer.py).
ACOUSTIC = ['FXT 6 acoustic cost=12500 cat=other mem=8896', 'FXT  0 strings 0..1 (0)', 'FXT  1 body_pct 0..100 (70)', 'FXT  2 top_db -12..12 (0)', 'FXT  3 decay_pct 0..100 (60)',
            'FXT  4 air_pct 0..100 (25)', 'FXT  5 doubles_pct 0..100 (60)', 'FXT  6 nivel_db -12..12 (0)']
HARMONIZER = ['FXT 24 harmonizer cost=11000 cat=mod mem=12632', 'FXT  0 key 0..11 (0)', 'FXT  1 scale 0..10 (0)', 'FXT  2 voice1 -7..7 (2)', 'FXT  3 voice2 -7..7 (0)',
              'FXT  4 balance_pct 0..100 (50)', 'FXT  5 mezcla_pct 0..100 (50)', 'FXT  6 nivel_db -12..12 (0)']


# The lines for the effects from the id 40 on (tools/check_mini_effects.py has them from the firmware), and how the page has to show each: its name, its group, its knobs.
OWN_EFFECTS = {'octaver': (40, 8000, 'drive', 772, 'Octaver', 'Pitch', ['Octave -1', 'Octave -2', 'Octave +1', 'Fuzz', 'Tone', 'Clean', 'Level']),
               'swell': (41, 4000, 'dynamics', 1364, 'Swell', 'Dynamics', ['Attack', 'Sensitivity', 'Depth', 'Level']),
               'reverse': (42, 6500, 'delay', 33384, 'Reverse Delay', 'Delay', ['Time', 'Feedback', 'Mix', 'Damping', 'Level'])}
OWN_LINES = [line for name, (ident, cost, group, memory, *_) in OWN_EFFECTS.items()
             for line in [f'FXT {ident} {name} cost={cost} cat={group} mem={memory}'] + [f'FXT  {k} {n} {a}..{b} ({d})' for k, (a, b, d, n) in enumerate(effects_reference.EFFECTS[name].ROWS)]]


def answers(identity):
    """The recorded answers, with what a product build has more."""
    out = recorded()
    if identity:
        for before, lines in (('FXT 7 ', ACOUSTIC), ('FXT 25 ', HARMONIZER)):
            i = next(k for k, line in enumerate(out['FXT']) if line.startswith(before))
            out['FXT'] = out['FXT'][:i] + lines + out['FXT'][i:]
        out['FXT'] = out['FXT'][:-1] + OWN_LINES + out['FXT'][-1:]
    return out


def pedal_source(identity):
    """The simulated pedal, with the answers and the USB numbers of the build it stands for."""
    return PEDAL.replace('__GLOBALS__', simulated_globals.GLOBALS).replace('__RECORDED__', json.dumps(answers(identity))).replace('__IDENTITY__', json.dumps(identity)).replace('__VENDOR__', '0x4c4a' if identity else '0x3654').replace('__SCENES__', '8' if identity else '4')


def acoustic(page, output):
    """The acoustic block: offered by its name, added, 6 and 12 strings as two buttons, a knob, its removal."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
    sent = lambda: cdp.evaluate('__pedal.sent')
    offered = cdp.evaluate('(() => { const t = S.types.acoustic, k = catKey("acoustic", t.cat); return [CATS.find(c => c.key === k).name, t.params.map(p => p.name).join()]; })()')
    require(offered == ['Acoustic', 'strings,body_pct,top_db,decay_pct,air_pct,doubles_pct,nivel_db'], f'how the block is offered: {offered}')
    n = len(sent())
    cdp.evaluate('void addFx("acoustic")')
    page.wait('[...document.querySelectorAll("#edOs .segsel")].some(e => /strings/i.test(e.innerText))', 'the choice of the strings', 20)
    page.wait(quiet, 'the block added', 20)
    require('FXA Q 99 acoustic' in sent()[n:] or 'FXA P 99 acoustic' in sent()[n:], f'what was sent: {sent()[n:]}')
    choice = '[...document.querySelectorAll("#edOs .segsel")].find(e => /strings/i.test(e.innerText))'
    labels = cdp.evaluate(choice + '.innerText.replace(/\\s+/g, " ").trim().toUpperCase()')
    require(labels == 'STRINGS 6 12', f'the choice of the strings: {labels}')
    cdp.screenshot(output / 'acoustic-6.png')
    n = len(sent())
    cdp.evaluate(choice + '.querySelectorAll("button")[1].click()')
    page.wait(choice + '.querySelectorAll("button")[1].classList.contains("on") && ' + quiet, '12 strings', 20)
    put = [c for c in sent()[n:] if c.startswith('FXP ')]
    require(len(put) == 1 and re.fullmatch(r'FXP [0-9]+ 0 1', put[0]), f'12 strings: {put}')
    cdp.screenshot(output / 'acoustic-12.png')
    knobs = cdp.evaluate('[...document.querySelectorAll("#editor .knob, #editor .kn, #editor [role=slider]")].map(e => (e.closest("[title]") || e).getAttribute("title") || e.getAttribute("aria-label") || "").filter(Boolean)')
    cdp.evaluate(choice + '.querySelectorAll("button")[0].click()')
    page.wait(choice + '.querySelectorAll("button")[0].classList.contains("on") && ' + quiet, '6 strings again', 20)
    n = len(sent())
    ident = put[0].split()[1]
    cdp.evaluate(f'void Pedal.cmd("FXR {ident}", "FXR").then(() => syncGen && loadChain())')
    page.wait(quiet, 'the block taken away', 20)
    return {'offered': offered, 'labels': labels, 'sent': put, 'tips': knobs[:8]}


def harmonizer(page, output):
    """The harmonizer: offered in the group of the pitch, added, its key, scale and intervals chosen by their names, its three knobs, its removal."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
    sent = lambda: cdp.evaluate('__pedal.sent')
    offered = cdp.evaluate('(() => { const t = S.types.harmonizer, k = catKey("harmonizer", t.cat); return [CATS.find(c => c.key === k).name, lookOf("harmonizer").name, t.params.map(p => p.name).join()]; })()')
    require(offered == ['Pitch', 'Harmonizer', 'key,scale,voice1,voice2,balance_pct,mezcla_pct,nivel_db'], f'how the block is offered: {offered}')
    n = len(sent())
    cdp.evaluate('void addFx("harmonizer")')
    page.wait('document.querySelectorAll("#edOs .hrlist").length === 4', 'the choices of the harmonizer', 20)
    page.wait(quiet, 'the block added', 20)
    require('FXA Q 99 harmonizer' in sent()[n:] or 'FXA P 99 harmonizer' in sent()[n:], f'what was sent: {sent()[n:]}')
    lists = cdp.evaluate('[...document.querySelectorAll("#edOs .hrlist")].map(e => { const s = e.querySelector("select"), r = s.getBoundingClientRect(); return [e.querySelector(".lbl").textContent, s.options.length, '
                         's.selectedOptions[0].textContent, Math.round(r.height) >= 40 && r.width > 80]; })')
    require(lists == [['Key', 12, 'C', True], ['Scale', 11, 'Major', True], ['Voice 1', 15, '3rd above', True], ['Voice 2', 15, 'Off', True]], f'the choices: {lists}')
    cdp.screenshot(output / 'harmonizer.png')
    put = []
    for k, name, wanted in ((0, 'A', '0 9'), (1, 'Harmonic minor', '1 7'), (2, '6th above', '2 5'), (3, '4th below', '3 -3'), (3, 'Off', '3 0'), (3, 'Octave below', '3 -7')):
        n = len(sent())
        cdp.evaluate(f'(() => {{ const s = document.querySelectorAll("#edOs .hrlist select")[{k}]; s.value = [...s.options].find(o => o.textContent === "{name}").value; s.dispatchEvent(new Event("change")); }})()')
        page.wait(quiet + f' && !document.querySelectorAll("#edOs .hrlist select")[{k}].disabled', name, 20)
        new = [c for c in sent()[n:] if c.startswith('FXP ')]
        require(len(new) == 1 and re.fullmatch(r'FXP [0-9]+ ' + re.escape(wanted), new[0]), f'{name}: {new}')
        require(cdp.evaluate(f'document.querySelectorAll("#edOs .hrlist select")[{k}].selectedOptions[0].textContent') == name, f'{name} is not shown')
        put.append(new[0])
    words = cdp.evaluate('[fmtVal(9, "hrkey"), fmtVal(7, "hrscale"), fmtVal(-7, "hrvoice"), fmtVal(0, "hrvoice"), plabel("voice2").lab]')
    require(words == ['A', 'Harmonic minor', 'Octave below', 'Off', 'Voice 2'], f'the values in words: {words}')
    knobs = cdp.evaluate('[...document.querySelectorAll("#edKnobs > *")].map(e => e.innerText.replace(/\\s+/g, " ").trim().toUpperCase())')
    require(len(knobs) == 3 and all(a in b for a, b in zip(('BALANCE', 'MIX', 'LEVEL'), knobs)), f'the knobs: {knobs}')
    cdp.screenshot(output / 'harmonizer-set.png')
    ident = put[0].split()[1]
    cdp.evaluate(f'void Pedal.cmd("FXR {ident}", "FXR").then(() => syncGen && loadChain())')
    page.wait(quiet, 'the block taken away', 20)
    return {'offered': offered, 'choices': lists, 'sent': put, 'knobs': knobs}


def own_effects(page, output):
    """The effects from the id 40 on: offered in their groups with a picture, added, their knobs with their words, formats and tips, one turned, and taken away."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
    sent = lambda: cdp.evaluate('__pedal.sent')
    seen = {}
    for name, (_, _, _, _, title, group, knobs) in OWN_EFFECTS.items():
        offered = cdp.evaluate(f'(() => {{ const t = S.types.{name}, k = catKey("{name}", t.cat), l = LOOK.{name}; return [CATS.find(c => c.key === k).name, l.name, /^<path /.test(l.ico), /^#[0-9a-f]{{6}}$/.test(l.c), '
                               't.params.map(p => plabel(p.name).lab)]; })()')
        require(offered == [group, title, True, True, knobs], f'how {name} is offered: {offered}')
        n = len(sent())
        cdp.evaluate(f'void addFx("{name}")')
        page.wait(f'[...S.chain.P, ...S.chain.Q].some(x => x.type === "{name}") && ' + quiet, f'{name} added', 20)
        require(f'FXA Q 99 {name}' in sent()[n:] or f'FXA P 99 {name}' in sent()[n:], f'what was sent: {sent()[n:]}')
        ident = cdp.evaluate(f'[...S.chain.P, ...S.chain.Q].find(x => x.type === "{name}").id')
        page.wait('document.getElementById("editor").innerText.length > 10', 'the editor of the block', 20)
        words = ' '.join(cdp.evaluate('document.getElementById("editor").innerText').split()).upper()
        require(all(k.upper() in words for k in knobs), f'{name}: the words of its knobs: {words[:400]}')
        faces = cdp.evaluate(f'(() => {{ const it = [...S.chain.P, ...S.chain.Q].find(x => x.type === "{name}"); return pedalValues(it); }})()')
        tips = cdp.evaluate(f'S.types.{name}.params.map(p => KNOB_TIP["{name}." + p.name] || "")')
        require(all(t.startswith(k + ':') for t, k in zip(tips, knobs) if t) and sum(bool(t) for t in tips) >= len(knobs) - 1, f'{name}: its tips: {tips}')
        n = len(sent())
        low, high = cdp.evaluate(f'[S.types.{name}.params[0].min, S.types.{name}.params[0].max]')
        answer = cdp.evaluate(f'Pedal.cmd("FXP {ident} 0 {high}", "FXP").then(r => r.join(" "))')
        require(answer == f'FXP ok {high}' and f'FXP {ident} 0 {high}' in sent()[n:], f'{name}: a knob turned to {high}: {answer}')
        refused = cdp.evaluate(f'Pedal.cmd("FXP {ident} {len(knobs)} 1", "FXP").then(r => r.join(" "))') if len(knobs) < 7 else 'ERR'
        require(refused.startswith('ERR'), f'{name}: a knob that it does not have: {refused}')
        cdp.screenshot(output / f'effect-{name}.png')
        cdp.evaluate(f'void Pedal.cmd("FXR {ident}", "FXR").then(() => syncGen && loadChain())')
        page.wait(quiet + f' && ![...S.chain.P, ...S.chain.Q].some(x => x.type === "{name}")', f'{name} taken away', 20)
        seen[name] = {'offered': offered[:2], 'faces': faces, 'range': [low, high]}
    return seen


# Random changes of a chain, with a capture and without, by the page's own functions and by the rules of the firmware: no section overflows on the way, the
# result is what was asked for, in the order that was asked for, and without a capture the sections meet where they should.
CHANGES_OF_A_CHAIN = r'''((seed, turns, splits) => {
  const was = [S.chain, S.mix, S.xo, S.xeq, S.ampPresent, S.xoOk, hrNew], quietly = hrNoPlace, saidBefore = toast, out = {turns: 0, refused: 0, moved: 0, long: 0, amp: 0, splits: 0, wrong: []};
  hrNoPlace = () => { out.refused++; }; toast = () => {};
  const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return Math.floor(seed / 2147483648 * n); };
  const kinds = ["boost", "ts9", "ds1", "chorus", "klon", "muff", "eq"], block = (id, lane) => { const type = kinds[rnd(kinds.length)], t = S.types[type], p = [0, 0, 0, 0, 0, 0, 0];
    for (const q of t.params) p[q.idx] = q.def; return {id, type, on: 1, p, lane: lane || 0, ticks: 0}; };
  const groups = l => { let n = 0, b = 0; for (const x of l) { if (x.lane > 0 && !b) n++; b = x.lane > 0; } return n; };
  const bare = segs => JSON.stringify(segs.filter(s => s.k !== "amp").map(s => s.k === "fx" ? s.id : [s.A, s.B]));
  const count = () => S.chain.P.length + S.chain.Q.length;
  try {
    S.chain = {P: [], Q: []}; S.mix = {P: [], Q: []}; S.xo = {P: [], Q: []}; S.xeq = {P: [], Q: []}; S.ampPresent = 0; let next = 0;
    for (let turn = 0; turn < turns; turn++) {
      const cur = flatCurrent(S.chain), segs = cloneSegs(curSegs()), n = count(), ids = [...S.chain.P, ...S.chain.Q].map(x => x.id), any = ids[rnd(ids.length)];
      const at = () => { const si = rnd(segs.length + 1), g = segs.findIndex(s => s.k === "grp"); return g >= 0 && rnd(3) === 0 ? {t: "lane", si: g, lane: "AB"[rnd(2)], idx: rnd(3)} : {t: "serial", si: segs[si] && segs[si].k === "amp" && !S.ampPresent ? si + 1 : si}; };
      let op = rnd(10), added = null;
      if (n < 4) op = 0;
      if (op < 4) {                                                             // a block is added
        if (n >= 16) continue;
        const loc = splits && rnd(6) === 0 ? {...at(), t: "newgrp"} : at();
        if (loc.t === "newgrp" && loc.lane) continue;
        if (!hrFits(loc)) continue;
        const b = hrBank(curSegs(), loc);
        if (S.chain[b].length >= 10) { if (S.ampPresent) continue; out.wrong.push(["no section", turn]); break; }
        added = block(next++); hrNew = added; cur[b].push({id: added.id, lane: 0});
        if (!placeNode(segs, added.id, loc)) continue;
        const ns0 = hrArrange(segs);
        if (!ns0 || (S.ampPresent && (grpCount(ns0).P > 3 || grpCount(ns0).Q > 3))) { if (!S.ampPresent) { out.wrong.push(["fits, and does not", turn]); break; } hrNew = null; continue; }
        S.chain[b].push(added);
      } else if (op < 7) {                                                      // moved
        const loc = at();
        if (joinsSplits(segs, any, loc) || !moveId(segs, any, loc)) continue;
      } else if (op === 7) {                                                    // into a split, or out of it
        if (!splits) continue;
        if (!setLane(segs, any, ["S", "A", "B"][rnd(3)])) continue;
      } else if (op === 8) {                                                    // taken away
        for (const b of PQ) { S.chain[b] = S.chain[b].filter(x => x.id !== any); cur[b] = cur[b].filter(x => x.id !== any); }
        if (S.ampPresent || !S.chain.P.length) { turn++; continue; }
        segs.splice(0, segs.length, ...cloneSegs(curSegs()));
      } else {                                                                  // the capture is taken out, or put in
        if (S.ampPresent) { S.ampPresent = 0; out.amp++; continue; }
        const loc = {t: "serial", si: 1 + rnd(segs.length)}, k = hrAmpPlace(loc);
        if (k == null) continue;
        const shown = bare(curSegs());
        S.ampPresent = 1; out.amp++;
        segs.splice(0, segs.length, ...cloneSegs(curSegs())); moveId(segs, "amp", hrAmpLoc(k));
        if (bare(segs) !== shown || segs.findIndex(s => s.k === "amp") !== k) { out.wrong.push(["the capture's place", turn]); break; }
      }
      const ns = hrArrange(segs);
      if (!ns) { if (S.ampPresent) out.wrong.push(["no place with a capture", turn]); out.refused++; continue; }
      const tgt = flatten(ns, cur), g = grpCount(ns), want = bare(normalize(segs));
      if (tgt.P.length > 10 || tgt.Q.length > 10 || g.P > 3 || g.Q > 3) { if (S.ampPresent) { out.refused++; continue; } out.wrong.push(["too many", turn, tgt]); break; }
      if (bare(ns) !== want) { out.wrong.push(["another chain", turn, want, bare(ns)]); break; }
      const pedal = {P: cur.P.map(x => ({...x})), Q: cur.Q.map(x => ({...x}))}, cmds = planCommands(cur, tgt);
      let bad = null;
      for (const c of cmds) {                                                   // the firmware, command by command
        const w = c.split(" "), b = PQ.find(x => pedal[x].some(y => y.id === +w[1])), x = pedal[b].find(y => y.id === +w[1]);
        if (w[0] === "FXL") x.lane = +w[2];
        else { if (b !== w[2] && pedal[w[2]].length >= 10) { bad = c; break; } pedal[b].splice(pedal[b].indexOf(x), 1); pedal[w[2]].splice(+w[3], 0, x); }
        if (groups(pedal.P) > 3 || groups(pedal.Q) > 3) { out.splits++; break; }        // a fourth on the way, where a section has three: refused by the firmware, as ever
      }
      if (bad) { out.wrong.push(["refused", turn, bad, cmds]); break; }
      out.moved += cmds.filter(c => c.startsWith("FXM")).length; out.turns++; if (tgt.P.length + tgt.Q.length > 10) out.long++;
      const flat = JSON.stringify(tgt);
      if (groups(pedal.P) <= 3 && groups(pedal.Q) <= 3 && JSON.stringify(pedal) !== flat && cmds.length) { out.wrong.push(["not what was asked", turn, pedal, tgt, cmds]); break; }
      S.chain = applyFlat(S.chain, tgt);
      const all = [...S.chain.P, ...S.chain.Q], least = Math.max(0, all.length - 10);
      if (!S.ampPresent && all.every(x => !x.lane)) {                           // the first place from the start that is allowed, and does not part drives if there is one
        const places = [...Array(all.length + 1).keys()].filter(k => k >= least && k <= 10), good = places.filter(k => !k || k === all.length || !hrTogether(hrDrive(all[k - 1].id), hrDrive(all[k].id)));
        if (S.chain.P.length !== (good.length ? good : places)[0]) { out.wrong.push(["the place", turn, S.chain.P.length, good, places]); break; }
        out.serial = (out.serial || 0) + 1;
      }
    }
  } finally { [S.chain, S.mix, S.xo, S.xeq, S.ampPresent, S.xoOk, hrNew] = was; hrNoPlace = quietly; toast = saidBefore; }
  return out;
})'''


def one_chain(page, output, types):
    """A chain without a capture, up to sixteen blocks: added, moved, split, taken away, saved, loaded, to a file and back; with a capture put in and taken out. The
    simulated pedal refuses what the firmware refuses, and nothing may be refused; the order that is shown is the order that was made."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !Pedal.busy'
    out = {}

    def edit(call, refused=False):
        cdp.evaluate(TOASTS + '.forEach(e => e.remove()); __pedal.refusals = []; window.__said = []')
        n = cdp.evaluate('__pedal.sent.length')
        cdp.evaluate(f'window.__ended = false; void (async () => {{ try {{ window.__answer = await ({call}); }} finally {{ window.__ended = true; }} }})()')
        page.wait('window.__ended && ' + quiet, call, 30)
        time.sleep(0.15)
        page.wait(quiet, call, 20)
        sent = [c for c in cdp.evaluate(f'__pedal.sent.slice({n})') if c.split()[0] in ('FXA', 'FXM', 'FXL', 'FXR', 'AMPX', 'FXMIX', 'FXXO') and len(c.split()) > 1]
        said = cdp.evaluate(TOASTS + '.map(e => [e.querySelector(".tst-ttl")?.textContent || "", e.querySelector(".tst-msg")?.textContent || ""])')
        require(not cdp.evaluate('__pedal.refusals') and not any('Couldn' in x[0] + x[1] for x in said), f"{call}: {sent}, the pedal refuses {cdp.evaluate('__pedal.refusals')}, {said}")
        require(not refused or (not sent and len(said) == 1), f'{call}: sent {sent}, said {said}')
        chain = cdp.evaluate('["P", "Q"].map(b => __pedal.chain[b].map(x => [x.id, x.lane || 0]))')
        require(cdp.evaluate('["P", "Q"].map(b => S.chain[b].map(x => [x.id, x.lane || 0]))') == chain and max(len(x) for x in chain) <= 10, f'{call}: the page and the pedal {chain}')
        return sent, (said[0] if said else None)

    def order():
        shown = cdp.evaluate('[...document.querySelectorAll("#chain .blk[data-id]")].map(e => +e.dataset.id)')
        segs = cdp.evaluate('curSegs().flatMap(s => s.k === "fx" ? [s.id] : s.k === "grp" ? [...s.A, ...s.B] : [])')
        require(shown == segs, f'shown {shown}, kept {segs}')
        return shown

    def sizes():
        return cdp.evaluate('["P", "Q"].map(b => __pedal.chain[b].length)')

    def state(p, q, amp=0):
        """A chain by the pedal itself: types, or (type, lane)."""
        ids = iter(range(16))
        one = lambda x: {'id': next(ids), 'type': x if isinstance(x, str) else x[0], 'on': 1, 'p': types[x if isinstance(x, str) else x[0]], **({} if isinstance(x, str) else {'lane': x[1]})}
        chain = {'P': [one(x) for x in p], 'Q': [one(x) for x in q]}
        edit(f'(() => {{ __pedal.chain = {json.dumps(chain)}; __pedal.ampx = {amp}; __pedal.changes++; __pedal.mix = {{P: [[0, 0], [0, 0], [0, 0]], Q: [[0, 0], [0, 0], [0, 0]]}}; '
             f'__pedal.xo = JSON.parse(JSON.stringify(__pedal.mix)); return loadChain(); }})()')
        require(cdp.evaluate('S.ampPresent') == amp and sizes() == [len(p), len(q)], f'the chain of {p} and {q}')

    end = '{t: "serial", si: curSegs().length}'
    names = ['gate', 'comp', 'boost', 'eq', 'chorus', 'phaser', 'tremolo', 'delay', 'geq', 'hum', 'vibrato', 'flanger', 'basseq', 'envfilter', 'doubler', 'rotary']
    # ten blocks: sent and stored as before there were more
    state([], [])
    for name in names[:10]:
        sent, said = edit(f'addFx("{name}")')
        require(sent == [f'FXA Q 99 {name}'] and said is None, f'a chain of ten: {sent}, {said}')
    require(order() == list(range(10)) and sizes() == [0, 10], f'a chain of ten: {order()}, {sizes()}')
    edit('loadPresets()')
    edit('Pedal.cmd("PSAVE 30 Ten", "PSAVE", 4000)')
    out['ten'] = cdp.evaluate('__pedal.store[30]')
    want = [{'id': i, 'type': n, 'on': 1, 'p': types[n]} for i, n in enumerate(names[:10])]
    require(out['ten']['chain'] == {'P': [], 'Q': want} and out['ten']['ampx'] == 0 and out['ten']['mix'] == out['ten']['xo'] == {b: [[0, 0]] * 3 for b in 'PQ'}, f"a chain of ten is stored as {out['ten']}")
    out['ten'] = [f'{len(want)} blocks after', out['ten']['ampx']]
    # up to sixteen, each at the end; the seventeenth is refused
    room = cdp.evaluate('document.getElementById("cpuFree").textContent')
    for k, name in enumerate(names[10:], 11):
        sent, said = edit(f'addFx("{name}")')
        require(order() == list(range(k)) and sizes() == [k - 10, 10] and sent[0] == f'FXA P 99 {name}' and len(sent) == 3, f'a chain of {k}: {order()}, {sizes()}, {sent}')
    out['eleventh'] = sent
    require(edit('addFx("boost")', True)[1] == ['This preset is full', '16 blocks are the most the pedal can hold. Remove one to add another.'], 'a seventeenth')
    require([room, cdp.evaluate('document.getElementById("cpuFree").textContent')] == ['~6 more', 'full'], f'the places that are left: {room}')
    cdp.screenshot(output / 'one-chain.png')
    edit('Pedal.cmd("PSAVE 31 Sixteen", "PSAVE", 4000)')
    kept = cdp.evaluate('JSON.stringify(__pedal.store[31].chain)')
    # moved: the order is the one that is asked for, whatever section a block is in
    now = list(range(16))
    for what, change in (('moveBlock(15, {t: "serial", si: 1})', lambda x: [15, *x[:15]]), (f'moveBlock(15, {end})', lambda x: [*x[1:], 15]), ('moveBlock(3, {t: "serial", si: 12})', lambda x: [*x[:3], *x[4:11], 3, *x[11:]]),
                         ('moveBlock(9, {t: "serial", si: 3})', lambda x: [*x[:2], 9, *[y for y in x[2:] if y != 9]])):
        edit(what)
        now = change(now)
        require(order() == now and sizes() == [6, 10], f'{what}: {order()}, {now}, {sizes()}')
    for ident, before in ((now[8], now[3]), (now[10], now[1])):     # by the hand: a block of the first row is taken at its grip and left before another of it
        n = cdp.evaluate('__pedal.sent.length')
        mouse = lambda kind, x, y: cdp.call('Input.dispatchMouseEvent', {'type': kind, 'x': x, 'y': y, 'button': 'left', 'buttons': 1, 'clickCount': 1})
        there = f'''(() => {{ const of = id => document.querySelector('#chain .blk[data-id="' + id + '"]').getBoundingClientRect(), g = document.querySelector('#chain .blk[data-id="{ident}"] .grip').getBoundingClientRect(),
            b = of({ident}), r = of({before}), y = g.y + g.height / 2; return [g.x + g.width / 2, y, r.x + r.width * .1, r.y + y - b.y]; }})()'''
        x0, y0, x1, y1 = cdp.evaluate(there)
        mouse('mousePressed', x0, y0)
        for k in range(1, 9):
            mouse('mouseMoved', x0 + (x1 - x0) * k / 8, y0 + (y1 - y0) * k / 8)
            time.sleep(0.04)
        time.sleep(0.4)
        mouse('mouseMoved', x1, y1)
        time.sleep(0.2)
        mouse('mouseReleased', x1, y1)
        cdp.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': 2, 'y': 2})      # away from what shows under the hand only
        time.sleep(0.5)
        page.wait(quiet, f'{ident} dragged before {before}', 20)
        now.remove(ident)
        now.insert(now.index(before), ident)
        require(order() == now and sizes() == [6, 10] and not cdp.evaluate('__pedal.refusals'), f"{ident} dragged before {before}: {order()}, {now}, {sizes()}, {cdp.evaluate(f'__pedal.sent.slice({n})')}")
    require(cdp.evaluate('[...document.querySelectorAll("#chain .cell")].filter(c => c.querySelector(".blk")).map(c => +c.querySelector(".gap").dataset.si)') == list(range(1, 17)), 'the places between the blocks')
    for step in (-1, 1):                                        # one step at a time, over the place where the sections meet
        for ident in ([now[6], now[7]] if step < 0 else [now[5], now[4]]):
            edit(f'(moveStep({ident}, {step}), new Promise(r => setTimeout(r, 400)))')
            i = now.index(ident)
            now.insert(i + step, now.pop(i))
            require(order() == now and sizes() == [6, 10], f'a step of {ident}: {order()}, {now}, {sizes()}')
    for ident, step, text in ((now[0], -1, 'first'), (now[-1], 1, 'last')):
        sent, said = edit(f'(window.__t = toast, toast = m => {{ __said.push(m); }}, moveStep({ident}, {step}), toast = __t, 0)')
        require(not sent and cdp.evaluate('__said') == [f'Already the {text} block.'], f"a step beyond the {text} block: {sent}, {cdp.evaluate('__said')}")
    # taken away, from either part, down to ten and less: as if there had never been more
    for ident in (now[8], now[0], now[15], now[3], now[9], now[5], now[12]):
        edit(f'removeFx({ident})')
        now.remove(ident)
        require(order() == now and sizes() == [max(0, len(now) - 10), min(10, len(now))], f'{ident} taken away: {order()}, {now}, {sizes()}')
    # added at the start, in the middle and at the end again
    for name, si in (('boost', 1), ('eq', 6), ('gate', 12), ('comp', 3), ('hum', 99)):
        edit(f'addFx("{name}", {{t: "serial", si: Math.min({si}, curSegs().length)}})')
        new = next(i for i in order() if i not in now)
        now.insert(min(si - 1, len(now)), new)
        require(order() == now and sizes() == [max(0, len(now) - 10), min(10, len(now))], f'{name} at {si}: {order()}, {now}, {sizes()}')
    # loaded again, the stored ones are what they were
    for n, size in ((30, [0, 10]), (31, [6, 10])):
        edit(f'(edClear(), loadPreset({n}))')
        require(sizes() == size and order() == list(range(sum(size))) and cdp.evaluate('S.ampPresent') == 0, f'preset {n}: {sizes()}, {order()}')
    require(cdp.evaluate('JSON.stringify(__pedal.chain)') == kept, 'a preset of sixteen comes back changed')
    # splits: made where the sections meet, with levels and a crossover that go with it from one to the other; never divided
    state(['gate'], names[1:11])
    edit('dropParallel(0, 1, "A")')
    require(sizes() == [2, 9] and cdp.evaluate('__pedal.chain.P.map(x => x.lane)') == [1, 2], f"a split where they meet: {sizes()}, {cdp.evaluate('__pedal.chain')}")
    edit('(setGroupMix("P", 0, 0, -3), setGroupXo("P", 0, 200), new Promise(r => setTimeout(r, 500)))')
    edit('removeFx(10)')
    require(sizes() == [0, 10] and cdp.evaluate('[__pedal.mix.Q[0], __pedal.xo.Q[0][0], __pedal.chain.Q.slice(0, 3).map(x => x.lane || 0)]') == [[-3, 0], 200, [1, 2, 0]], f"a split goes with its levels: {cdp.evaluate('[__pedal.chain, __pedal.mix, __pedal.xo]')}")
    edit('addFx("boost")')
    require(sizes() == [2, 9] and cdp.evaluate('[__pedal.mix.P[0], __pedal.xo.P[0][0]]') == [[-3, 0], 200] and order()[:2] == [0, 1], f"and back: {sizes()}, {cdp.evaluate('[__pedal.mix, __pedal.xo]')}")
    state([('gate', 1)] * 4 + [('eq', 2)] * 4, ['boost'] * 8)
    for k in (15, 14):
        edit(f'moveBlock({k}, {{t: "serial", si: 1}})')
    out['too large'] = edit('moveBlock(13, {t: "serial", si: 1})', True)[1]
    require(out['too large'] == ['No room here', 'A split cannot be divided, and this one is too large for this place. Choose another place, or take a block out of the split.'] and sizes() == [10, 6],
            f"a split that is too large: {out['too large']}, {sizes()}")
    state(['boost'] * 4, ['boost'] * 10)
    for k in (0, 2, 4, 6, 8, 10):
        edit(f'splitBlock({k})')
        require(order() == list(range(14)), f'a split at {k}: {order()}')
    out['splits'] = [sizes(), cdp.evaluate('["P", "Q"].map(b => curSegs().filter(s => s.k === "grp" && s.bank === b).length)')]
    require(out['splits'][1] == [3, 3], f"six splits: {out['splits']}")
    out['seventh'] = edit('splitBlock(12)', True)[1]
    require(out['seventh'] == ['Too many splits', 'A chain holds 6 splits at most. Merge one first.'], f"a seventh split: {out['seventh']}")
    # drives with oversampling side by side stay together
    state([], ['gate', 'ts9', 'ds1', 'comp', *['boost'] * 6])
    edit('addFx("eq")')
    require(sizes() == [1, 10], f'a chain of eleven with two drives: {sizes()}')
    edit('addFx("eq")')
    require(sizes() == [3, 9] and cdp.evaluate('__pedal.chain.P.map(x => x.type)') == ['gate', 'ts9', 'ds1'], f'two drives where the sections meet: {sizes()}')
    # a capture: put in where the sections hold it, refused where not; taken out again
    state(['gate', 'comp'], names[2:12])
    before = order()
    out['capture'] = [edit(f'addAmp({end})', True)[1], edit('addAmp({t: "serial", si: 1})', True)[1]]
    require(out['capture'] == [['No room before the AMP block', 'At most 10 blocks fit before it, and here there would be 12. Add it nearer the start of the chain.'],
                               ['No room after the AMP block', 'At most 10 blocks fit after it, and here there would be 12. Add it nearer the end of the chain.']], f"a capture without room: {out['capture']}")
    for at, size in ((7, [6, 6]), (3, [2, 10]), (11, [10, 2])):
        sent, _ = edit(f'addAmp({{t: "serial", si: {at}}})')
        require(sizes() == size and order() == before and cdp.evaluate('S.ampPresent') == 1 and sent[0] == 'AMPX 1' and cdp.evaluate('ampIdx(curSegs())') == size[0], f'a capture at {at}: {sizes()}, {order()}, {sent}')
        edit('removeAmp()')
        require(sizes() == [2, 10] and order() == before and cdp.evaluate('S.ampPresent') == 0, f'the capture at {at} taken out: {sizes()}, {order()}')
    edit(f'moveBlock({before[0]}, {end})')
    require(sizes() == [2, 10] and order() == [*before[1:], before[0]], f'moved afterwards: {sizes()}, {order()}')
    # a short chain: all of it in the second section, when its capture is taken out, or with the next change when it was so before
    state(names[:4], names[4:8], 1)
    sent, _ = edit('removeAmp()')
    require(sizes() == [0, 8] and order() == list(range(8)) and sent[0] == 'AMPX 0' and len(sent) == 5, f'a capture taken out of a short chain: {sizes()}, {sent}')
    state(names[:4], names[4:8])
    edit('addFx("eq")')
    require(sizes() == [0, 9] and order() == list(range(9)), f'a short chain with a capture taken out before: {sizes()}')
    # in stereo the first blocks of a long chain are mono: it is said
    state([], ['chorus', *['eq'] * 9])
    edit('(S.stw = {...(S.stw || {}), w: 100, deg: 0}, render(true), 0)')
    said = edit('addFx("eq")')[1]
    out['mono'] = said
    require(said == ['Mono at the start of the chain', 'In a chain of more than 10 blocks only the last ten are in stereo. Now in mono: Chorus.'], f'a block that is mono now: {said}')
    edit('(S.sel = 0, render(true), 0)')
    require('Mono here: without a capture, the last ten blocks of a chain are in stereo.' in cdp.evaluate('document.getElementById("edStHint")?.textContent || ""'), 'the block does not say that it is mono')
    edit('(S.stw = {...S.stw, w: 0}, S.sel = null, render(true), 0)')
    # to a file and back, with scenes; and files that say nothing of sections
    edit('(edClear(), loadPreset(31))')
    cdp.evaluate('window.__files = []; window.__save = pioSaveFile; pioSaveFile = async (name, text) => { __files.push([name, text]); return "file"; };')
    cdp.evaluate('void pioExport(false)')
    deadline = time.monotonic() + 40
    while not cdp.evaluate('__files.length'):
        require(time.monotonic() < deadline, 'the export of sixteen blocks does not end')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    page.wait(quiet, 'the end of the export', 20)
    edit('(async () => { await Pedal.cmd("PNEW", "PNEW", 4000); await loadChain(); await loadSnaps(); })()')
    cdp.evaluate('window.__imported = undefined; void pioImport(__files[0][1]).then(v => { window.__imported = v; })')
    deadline = time.monotonic() + 60
    while cdp.evaluate('window.__imported === undefined || !!document.querySelector(".mdlg")'):
        require(time.monotonic() < deadline, 'the import of sixteen blocks does not end')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    page.wait(quiet, 'the end of the import', 20)
    require(sizes() == [6, 10] and cdp.evaluate('[...__pedal.chain.P, ...__pedal.chain.Q].map(x => x.type)') == names and cdp.evaluate('__pedal.ampx') == 0, f"from a file: {sizes()}, {cdp.evaluate('__pedal.chain')}")
    cdp.evaluate('pioSaveFile = window.__save')
    plan = lambda chain, amp: cdp.evaluate(f'(() => {{ const p = pioPlan({{meta: {{name: "x"}}, sound: {{chain: {json.dumps(chain)}, amp: {{present: {amp}}}}}}}, pioCtxOf({{list: []}}, {{list: []}})); '
                                           'return [p.cmds.filter(c => /^FXA/.test(c.line)).map(c => c.line.split(" ").filter((x, i) => i !== 2).slice(1).join(" ")), p.warn.map(w => w.k).filter(x => /left out|joined/.test(x)), p.cmds.some(c => c.line === "AMPX 0")]; })()')
    many = [{'type': n} for n in names]
    for chain in (many, [{'amp': True}, *many], [*many, {'amp': True}]):
        got = plan(chain, 'false')
        require(got == [[f'P {n}' for n in names[:6]] + [f'Q {n}' for n in names[6:]], [], True], f'sixteen blocks of a file without a capture: {got}')
    require(plan([*many[:3], {'amp': True}, *many[3:8]], 'false')[0] == [f'P {n}' for n in names[:3]] + [f'Q {n}' for n in names[3:8]], 'a file of eight blocks is taken as it is')
    got = plan([{'amp': True}, *many], 'true')
    require(len(got[0]) == 10 and got[1] and not got[2], f'a file with a capture and sixteen blocks after it: {got}')
    out['changes'] = [cdp.evaluate(f'{CHANGES_OF_A_CHAIN}({seed}, 6000, {splits})') for seed, splits in ((11, 0), (12, 0), (2026, 1), (2027, 1))]
    require(all(not x['wrong'] and x['turns'] > 1000 and x['long'] > 300 and x['amp'] > 100 and x['splits'] <= x['turns'] / 20 for x in out['changes']) and
            all(x['splits'] == 0 and x['serial'] > 300 for x in out['changes'][:2]), f"random changes of a chain: {json.dumps(out['changes'])[:1500]}")
    return out


def full_chain(page, output):
    """A chain without room: what it says, with a capture in the chain, for a block that is added and for one that is moved; and nothing is sent. And a chain without a
    capture, which uses all the places (one_chain)."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
    cdp.evaluate('''__pedal.kept = JSON.stringify(Object.fromEntries(["chain", "ampx", "mix", "xo", "presets", "store", "current", "scenes", "scene", "names", "stereo", "amp", "ampeq", "gain", "bpm"].map(k => [k, __pedal[k]])));
                    window.__stw = JSON.stringify(S.stw)''')

    def chain(p, q, amp):
        cdp.evaluate(f"""(() => {{ const one = id => ({{id, type: "boost", on: 1, p: Array.from({{length: 7}}, (_, i) => (S.types.boost.params[i] || {{def: 0}}).def)}});
            __pedal.chain = {{P: [...Array({p}).keys()].map(one), Q: [...Array({q}).keys()].map(k => one({p} + k))}}; __pedal.ampx = {amp}; void loadChain(); }})()""")
        page.wait(f'S.chain.P.length === {p} && S.chain.Q.length === {q} && S.ampPresent === {amp} && ' + quiet, f'a chain of {p} and {q}', 20)
        time.sleep(0.3)
        require(cdp.evaluate('HyperRigMini.commandPolicy("FXE 0 1", "usb-cdc").allowed'), f'the rules do not know the chain of {p} and {q}')
        room[f'{p}+{q}' + (' amp' if amp else '')] = cdp.evaluate('document.getElementById("cpuFree").textContent')

    def said(what):
        cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
        n = cdp.evaluate('__pedal.sent.length')
        cdp.evaluate(f'void {what}')
        page.wait(TOASTS + '.length > 0', f'what is said of {what}', 10)
        time.sleep(0.4)
        page.wait(quiet, what, 10)
        sent = [c for c in cdp.evaluate(f'__pedal.sent.slice({n})') if c.split()[0] in ('FXA', 'FXM', 'FXL', 'FXR')]
        text = cdp.evaluate(TOASTS + '.map(e => [e.querySelector(".tst-ttl").textContent, e.querySelector(".tst-msg").textContent])')
        require(not sent and len(text) == 1, f'{what}: sent {sent}, said {text}')
        return text[0]

    out, room = {}, {}
    chain(2, 10, 1)
    out['two and ten'] = said('addFx("boost", {t: "serial", si: 13})')
    cdp.screenshot(output / 'full-chain.png')
    out['one moved after'] = said('moveBlock(0, {t: "serial", si: 13})')
    chain(10, 2, 1)
    out['ten and two'] = said('addFx("boost", {t: "serial", si: 0})')
    chain(6, 10, 1)
    out['sixteen'] = said('addFx("boost", {t: "serial", si: 0})')
    out['anything else'] = said('toast("Couldn\'t add the block: ERR MINI_APP command is outside the current FXT/FXS/PLIST/SNAPS data", "err")')
    chain(8, 8, 0)
    out['sixteen, no capture'] = said('addFx("boost")')
    want = {'sixteen, no capture': ['This preset is full', '16 blocks are the most the pedal can hold. Remove one to add another.'],
            'two and ten': ['No room after the AMP block', 'At most 10 blocks fit after it. Remove one, or add this one before it.'],
            'one moved after': ['No room after the AMP block', 'At most 10 blocks fit after it. Remove one there first.'],
            'ten and two': ['No room before the AMP block', 'At most 10 blocks fit before it. Remove one, or add this one after it.'],
            'sixteen': ['This preset is full', '16 blocks are the most the pedal can hold. Remove one to add another.'],
            'anything else': ['Nothing was changed', 'The editor and the pedal are out of step. Disconnect, connect again and retry.']}
    require(out == want, f'what is said: {json.dumps({k: v for k, v in out.items() if v != want[k]})}')
    # there is room again: the block is added
    chain(0, 9, 0)
    cdp.evaluate('void addFx("boost", {t: "serial", si: 10})')
    page.wait('S.chain.Q.length === 10 && ' + quiet, 'the tenth block', 15)
    chain(2, 10, 0)
    require(room == {'2+10': '~4 more', '2+10 amp': '~4 more', '10+2 amp': '~4 more', '6+10 amp': 'full', '8+8': 'full', '0+9': '~7 more'}, f'the places that are left: {room}')
    cdp.evaluate('void blockMenu({clientX: 500, clientY: 320}, S.chain.Q[0])')
    page.wait('!!document.getElementById("menu")', 'the menu of a block', 10)
    menu = cdp.evaluate('document.getElementById("menu").innerText')
    cdp.evaluate('closeMenu()')
    require(all(x in menu for x in ('Move left', 'Move right', 'Remove Boost', 'Split here')), f'the menu of a block: {menu!r}')
    types = cdp.evaluate('Object.fromEntries(Object.entries(S.types).map(([n, t]) => [n, Array.from({length: 7}, (_, i) => (t.params.find(q => q.idx === i) || {def: 0}).def)]))')
    one = one_chain(page, output, types)
    cdp.evaluate('window.__back = false; void (async () => { Object.assign(__pedal, JSON.parse(__pedal.kept)); __pedal.ampx ??= 1; __pedal.changes++; S.stw = JSON.parse(__stw); edClear(); S.pendName = ""; '
                 'await loadPresets(); await loadChain(); await loadSnaps(); await Pedal.cmd("GAIN", "GAIN"); render(true); window.__back = true; })()')
    page.wait('window.__back && S.chain.P.length === __pedal.chain.P.length && S.chain.Q.length === __pedal.chain.Q.length && S.ampPresent === __pedal.ampx && curPreset === __pedal.current && ' + quiet,
              'the chain as it was', 20)
    asked = -1                                          # the page reads the pedal again when it notices the change itself: until it asks no more than its levels
    while asked != (asked := cdp.evaluate('__pedal.sent.filter(c => !/^(LVL|EVT)/.test(c)).length')):
        time.sleep(3)
        page.wait(quiet, 'the page at rest', 20)
    cdp.evaluate('edClear(); ' + TOASTS + '.forEach(e => e.remove())')
    return {'said': out, 'room': room, 'menu': menu, 'one_chain': one}


REPLACE = r'''
  window.__one = (id, t, lane, on) => ({id, type: t, on: on ?? 1, lane: lane || 0, p: Array.from({length: 7}, (_, i) => ((S.types[t].params || []).find(q => q.idx === i) || {def: 0}).def)});
  window.__make = (n, name, p, q) => { const k = __pedal, was = JSON.parse(JSON.stringify([k.chain, k.scenes, k.scene, k.names, k.amp])); let id = 0;
    k.chain = {P: p.map(x => __one(id++, ...x)), Q: q.map(x => __one(id++, ...x))}; k.scenes = "11000000"; k.scene = 0; k.names = Array(8).fill(""); k.amp = 1; k.presets[n] = name; k.store[n] = k.keep();
    [k.chain, k.scenes, k.scene, k.names, k.amp] = was; };
  window.__view = c => ["P", "Q"].map(b => c[b].map(x => [x.id, x.type, x.on ? 1 : 0, x.lane || 0]));
  __pedal.ampx = 1;'''


def replace(page, output):
    """A block in the place of another, from its menu: by mouse and by keys, in series, on a branch, first, last, off, in a full section; what does not fit, with the words that
    say why; a footswitch, a scene and a disconnection in the middle; then moved, saved, and given back by Discard."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !hrSaving && !Pedal.busy'
    start, (one, two) = cdp.evaluate('curPreset'), [k for k in range(31, 0, -1) if not cdp.evaluate(f'!!__pedal.store[{k}]')][:2]
    count = lambda: cdp.evaluate('__pedal.sent.length')
    sent = lambda since: [c for c in cdp.evaluate(f'__pedal.sent.slice({since})') if ' ' in c and re.match(r'FX|PNEW|PLOAD|PSAVE|SNAP|AMPX', c)]
    pedal, shown = (lambda: cdp.evaluate('__view(__pedal.chain)')), (lambda: cdp.evaluate('__view(S.chain)'))
    clear = lambda: cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    said = lambda: (time.sleep(0.2), cdp.evaluate(TOASTS + '.map(e => [e.querySelector(".tst-ttl")?.textContent || "", e.querySelector(".tst-msg")?.textContent || ""])'))[1]      # a message has its text 30 ms after it is there
    state = lambda: cdp.evaluate('[hrState().kind, document.getElementById("saveTxt").innerText.replace(/\\s+/g, " ")]')
    out = {'sent': [], 'said': {}}

    def load(n, dirty=False):
        cdp.evaluate('closeMenu(); ' + ('' if dirty else 'edClear(); ') + f'window.__ready = false; void (async () => {{ await loadPresets(); await loadPreset({n}); window.__ready = true; }})()')
        page.wait(f'window.__ready === true && curPreset === {n} && JSON.stringify(__view(S.chain)) === JSON.stringify(__view(__pedal.store[{n}].chain)) && ' + quiet, f'preset {n}', 20)
        time.sleep(0.3)
        clear()

    def fresh(p, q):
        cdp.evaluate(f'__make({one}, "Replace", {json.dumps(p)}, {json.dumps(q)})')
        load(one)

    def settle(what):
        time.sleep(0.2)
        page.wait(quiet, what, 20)
        page.wait('JSON.stringify(__view(S.chain)) === JSON.stringify(__view(__pedal.chain))', f'{what}: the page shows what is on the pedal', 10)

    def swap(what, bank, k, name, do=None, fits=True):
        """Replace the block; (its id, the new one's). Nothing else is sent, and nothing else changes."""
        before, n = pedal(), count()
        row = 'PQ'.index(bank)
        ident, old = before[row][k][:2]
        clear()
        cdp.evaluate(do(ident) if do else f'window.__new = undefined; void replaceFx({ident}, "{name}").then(v => {{ window.__new = v; }})')
        page.wait(f'__pedal.sent.slice({n}).some(c => /^FXC /.test(c))', f'{what}: the command', 10)
        settle(what)
        now, commands = pedal(), sent(n)
        require(commands == [f'FXC {cdp.evaluate("curPreset")} {ident} {old} {name}'], f'{what}: sent {commands}')
        out['sent'] += commands
        want = json.loads(json.dumps(before))
        if fits:
            want[row][k][:2] = [now[row][k][0], name]
            require(now == want and cdp.evaluate('S.sel') == now[row][k][0] and not said(), f'{what}: {now}, not {want}; {said()}')
            require(state()[0] == 'changed' and state()[1].endswith(', for all its scenes'), f'{what}: the line says {state()}')
        else:
            require(now == before, f'{what}: {now}, not {before}')
            out['said'][what] = said()
        return ident, now[row][k][0]

    cdp.evaluate(REPLACE)
    # the menu: the category of the block first, what fits, sizes; by mouse
    series = ([['boost'], ['ts9'], ['eq']], [['gate'], ['delay'], ['rat']])
    fresh(*series)
    cdp.evaluate('__pedal.shown = "22000/22718"')
    page.wait('S.cpu[0] === 22000', 'what the pedal has left', 10)
    cdp.evaluate('(() => { const d = document.querySelector("#chain .blk[data-id=\'1\']"), r = d.getBoundingClientRect(); '
                 'd.dispatchEvent(new MouseEvent("contextmenu", {bubbles: true, cancelable: true, clientX: r.left + 20, clientY: r.top + 20})); })()')
    page.wait('!!document.querySelector("#menu .mcr")', 'the menu of a block', 10)
    menu = cdp.evaluate('(() => { const cat = t => catKey(t, S.types[t].cat), m = document.getElementById("menu").getBoundingClientRect(); return {'
                        'head: [...document.querySelectorAll("#menu .mhd")].map(e => e.innerText).join(" | "), cats: [...document.querySelectorAll("#menu .mcr")].map(e => [e.dataset.cat, e.classList.contains("here")]), '
                        'own: cat("ts9"), all: CATS.map(c => c.key).filter(k => Object.keys(S.types).some(t => t !== "ts9" && cat(t) === k)), '
                        'least: Math.min(...[...document.querySelectorAll("#menu button")].map(e => e.getBoundingClientRect().height)), inside: m.top >= 0 && m.bottom <= innerHeight}; })()')
    require('REPLACE WITH' in menu['head'].upper() and menu['cats'] == [[menu['own'], True]] + [[k, False] for k in menu['all'] if k != menu['own']] and menu['least'] >= 40 and menu['inside'], f'the menu: {menu}')
    cdp.click('#menu .mcr[data-cat="dynamics"]')
    page.wait('!!document.getElementById("menuSub")', 'the blocks of a category', 10)
    cdp.screenshot(output / 'replace-menu.png')
    cdp.click('#menu .mcr')
    page.wait('document.getElementById("menuSub")?.getAttribute("aria-label") === CATS.find(c => c.key === "drive").name', 'the blocks of the same category', 10)
    listed = ('(() => { const c = fitCtx(findInst(1).inst), by = Object.fromEntries(Object.keys(S.types).map(t => [lookOf(t).name, t])); '
                        'return [...document.querySelectorAll("#menuSub button:not(.mcat)")].map(e => { const t = by[(e.querySelector(".mnm") || e).innerText.replace(e.querySelector("small")?.innerText || "~", "").trim()], f = t && fitOf(S.types[t], c); '
                        'return [t, e.className, e.querySelector(".mwhy")?.innerText || "", f ? f.why || f.note || "" : null, e.getBoundingClientRect().height, e.disabled]; }); })()')
    fits = cdp.evaluate(listed)
    cdp.click('#menu .mcr[data-cat="delay"]')
    page.wait('document.getElementById("menuSub")?.getAttribute("aria-label") === CATS.find(c => c.key === "delay").name', 'the blocks of another category', 10)
    fits += cdp.evaluate(listed)
    require(len(fits) > 4 and 'ts9' not in [x[0] for x in fits] and all(x[0] and x[2] == x[3] and x[4] >= 40 and not x[5] for x in fits) and any('fit-no' in x[1] and 'needs' in x[2] for x in fits) and
            any(x[1] == '' for x in fits), f'what fits: {fits}')
    out['fits'] = [[x[0], x[2]] for x in fits]
    cdp.evaluate('closeMenu(); __pedal.shown = "0/22718"')
    page.wait('S.cpu[0] === 0', 'what the pedal has left', 10)
    open_menu = '(() => {{ document.querySelector("#chain .blk[data-id=\'{0}\']").focus(); }})()'

    def by_mouse(ident):
        cdp.evaluate(f'(() => {{ const d = document.querySelector("#chain .blk[data-id=\'{ident}\']"), r = d.getBoundingClientRect(); '
                     'd.dispatchEvent(new MouseEvent("contextmenu", {bubbles: true, cancelable: true, clientX: r.left + 20, clientY: r.top + 20})); })()')
        page.wait('!!document.querySelector("#menu .mcr")', 'the menu', 10)
        cdp.click('#menu .mcr')
        page.wait('!!document.getElementById("menuSub")', 'the blocks of the same category', 10)
        cdp.evaluate('[...document.querySelectorAll("#menuSub button")].find(e => e.innerText.includes(lookOf("klon").name)).id = "pick"')
        cdp.click('#pick')
        return '0'

    def by_keys(ident):
        cdp.evaluate(open_menu.format(ident))
        for key, code, number, modifiers in (('F10', 'F10', 121, 8), *[('ArrowDown', 'ArrowDown', 40, 0)] * 5, ('ArrowRight', 'ArrowRight', 39, 0), ('Enter', 'Enter', 13, 0)):
            for kind in ('rawKeyDown', 'keyUp'):
                cdp.call('Input.dispatchKeyEvent', {'type': kind, 'key': key, 'code': code, 'windowsVirtualKeyCode': number, 'modifiers': modifiers})
            time.sleep(0.4 if key == 'F10' else 0.1)
        return '0'

    ident, new = swap('by mouse, between two', 'P', 1, 'klon', by_mouse)
    require(ident == 1 and new == 6, f'the ids: {ident}, {new}')
    page.wait(f'document.activeElement && document.activeElement.dataset.id === "{new}"', 'the new block has the focus', 5)
    cdp.screenshot(output / 'replaced.png')
    first = cdp.evaluate('(() => { const cat = t => catKey(t, S.types[t].cat); return Object.keys(S.types).find(t => t !== "gate" && cat(t) === cat("gate")); })()')
    ident, new = swap('by keys, first after the amp', 'Q', 0, first, by_keys)
    page.wait(f'document.activeElement && document.activeElement.dataset.id === "{new}"', 'the new block has the focus after the keys', 5)
    swap('first', 'P', 0, 'comp')
    swap('last before the amp', 'P', 2, 'chorus')
    swap('last', 'Q', 2, 'reverb2')
    cdp.evaluate(f'void toggle({pedal()[1][1][0]})')
    page.wait('__pedal.chain.Q[1].on === 0 && ' + quiet, 'a block off', 10)
    settle('a block off')
    swap('off', 'Q', 1, 'phaser')
    require(pedal()[1][1][2] == 0, 'a block that was off plays')
    # branches
    fresh([['boost', 1], ['ts9', 2], ['eq'], ['rat', 2]], [['gate', 1], ['delay', 1], ['rat', 2], ['comp']])
    segs = 'curSegs().map(s => s.k === "grp" ? [s.bank, s.ord, s.A.length, s.B.length] : s.k)'
    groups = cdp.evaluate(segs)
    for what, bank, k, name in (('on branch A, alone on it', 'P', 0, 'comp'), ('on branch B', 'P', 1, 'klon'), ('between two splits', 'P', 2, 'geq'), ('alone in a split', 'P', 3, 'muff'), ('first of two on branch A', 'Q', 0, 'chorus'),
                                ('second of two on branch A', 'Q', 1, 'hum'), ('behind a split', 'Q', 3, 'reverb2')):
        swap(what, bank, k, name)
        require(cdp.evaluate(segs) == groups, f'{what}: the splits are {cdp.evaluate(segs)}, not {groups}')
    # full: ten in a section, sixteen
    fresh([], [['boost']] * 10)
    swap('ten in a section', 'Q', 9, 'eq')
    fresh([['gate']] * 6, [['boost']] * 10)
    _, new = swap('sixteen', 'Q', 4, 'ts9')
    require(new == 10, f'the id in a chain of sixteen: {new}')
    # what does not fit: nothing is marked, and a knob that was turned stays turned
    fresh(*series)
    cdp.evaluate('__pedal.budget = 9000')
    ident, _ = swap('not enough CPU', 'P', 1, 'amp_hi', fits=False)
    require(state()[0] == 'saved', f'refused, and the line says {state()}')
    cdp.evaluate(f'void (async () => {{ await Pedal.cmd("FXP {ident} 0 77", "FXP"); edMark("p", {{id: {ident}, idx: 0, v: 77}}); await loadChain(); }})()')
    page.wait('ED.p.size === 1 && findInst(1).inst.p[0] === 77 && ' + quiet, 'a knob', 10)
    cdp.evaluate('__pedal.budget = Infinity; __pedal.room = 40000')
    swap('not enough memory', 'P', 1, 'reverb2', fits=False)
    require(cdp.evaluate(f'[ED.p.size, ED.other, __pedal.chain.P[1].p[0], findInst({ident}).inst.p[0]]') == [1, False, 77, 77], 'refused, and the knob is not as it was')
    cdp.evaluate('__pedal.room = Infinity')
    swap('then it fits', 'P', 1, 'reverb2')
    require(cdp.evaluate('[ED.p.size, ED.other]') == [0, True], 'the knob of a block that is gone is still to be saved')
    cdp.evaluate('__pedal.ir = null; __pedal.ir_slot = -1; if (!Object.keys(__pedal.irs).length) __pedal.irs[0] = {n: 256, gain: 0, fs: 48, data: new Uint8Array(512), name: "Cab"}')
    fresh(*series)
    swap('no IR', 'Q', 1, 'ir', fits=False)
    page.wait('document.getElementById("lib").classList.contains("on")', 'the library of IRs', 10)
    require(state()[0] == 'saved', f'without an IR the line says {state()}')
    page.wait('!!document.querySelector(\'#libL [data-a="l"]\') && ' + quiet, 'an IR to pick', 10)
    cdp.click('#libL [data-a="l"]')
    page.wait('__pedal.chain.Q[1].type === "ir" && ' + quiet, 'the block that was waiting for the IR', 15)
    settle('the IR')
    cdp.evaluate('if (document.getElementById("lib").classList.contains("on")) closeLib()')
    require([x[1] for x in pedal()[1]] == ['gate', 'ir', 'rat'], f'with the IR: {pedal()}')
    # a footswitch in the middle: when the command arrives; seen by the rules before the page; and a scene
    cdp.evaluate(f'__make({two}, "Other", [["eq"], ["ts9"]], [["gate"]])')
    fresh(*series)
    stores = lambda: cdp.evaluate(f'JSON.stringify([{one}, {two}].map(n => __pedal.store[n].chain))')
    kept = stores()
    for what, do in (('a footswitch before the command arrives', f'__pedal.hook = line => {{ if (/^FXC /.test(line)) {{ __pedal.hook = null; __pedal.press({two}); }} }}; void replaceFx(1, "muff")'),
                     ('a footswitch that the rules have seen', f'void (async () => {{ __pedal.press({two}); await edFresh(); await replaceFx(1, "muff"); }})()')):
        n = count()
        cdp.evaluate(do)
        page.wait(f'curPreset === {two} && {TOASTS}.length > 0 && ' + quiet, what, 20)
        settle(what)
        page.wait('hrState().kind === "saved"', f'{what}: nothing to save', 10)
        out['said'][what] = said()
        commands = [c for c in sent(n) if not c.startswith(('FXC', 'SNAPNAME'))]
        require(not commands and stores() == kept and pedal() == [[[0, 'eq', 1, 0], [1, 'ts9', 1, 0]], [[2, 'gate', 1, 0]]], f'{what}: {commands}, {pedal()}')
        require(len([c for c in sent(n) if c.startswith('FXC')]) == (1 if 'arrives' in what else 0), f'{what}: {sent(n)}')
        swap('the next one', 'P', 1, 'klon')
        load(one)
    cdp.evaluate('__pedal.hook = line => { if (/^FXC /.test(line)) { __pedal.hook = null; __pedal.scene = 1; __pedal.changes++; } }')
    swap('a scene in the middle', 'P', 1, 'muff')
    page.wait('S.snap === 1 && ' + quiet, 'the scene that was chosen', 10)
    require(cdp.evaluate(f'curPreset === {one} && hrState().kind') == 'changed', 'after a scene in the middle there is nothing to save')
    # no answer, and a disconnection: the page shows what is on the pedal, and that it may not be saved
    for what, do, changed in (('no answer', '__pedal.silent = /^FXC /; void replaceFx(1, "muff")', True),
                              ('a disconnection before it arrives', '__pedal.hook = line => { if (/^FXC /.test(line)) { __pedal.hook = null; __pedal.unplug(); throw new Error("gone"); } }; void replaceFx(1, "muff")', False),
                              ('a disconnection after it', '__pedal.silent = /^FXC /; __pedal.hook = line => { if (/^FXC /.test(line)) { __pedal.hook = null; setTimeout(() => __pedal.unplug(), 10); } }; void replaceFx(1, "muff")', True)):
        fresh(*series)
        cdp.evaluate('window.__marked = null; { const was = onDisconnected; onDisconnected = e => { window.__marked = ED.other; onDisconnected = was; was(e); }; }' if 'disconnection' in what else 'window.__marked = null')
        cdp.evaluate(do)
        page.wait(f'JSON.stringify(__view(__pedal.chain)).includes("muff") === {str(changed).lower()} && ' + ('!S.connected' if 'disconnection' in what else TOASTS + '.length > 0 && ' + quiet), what, 20)
        cdp.evaluate('__pedal.silent = null')
        if 'disconnection' in what:
            require(cdp.evaluate('window.__marked') is True, f'{what}: it was not marked before it was sent')
            time.sleep(0.5)
            cdp.evaluate('void connect()')
            page.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer && ' + quiet, 'connected again', 60)
            cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        else:
            require(state()[0] == 'changed', f'{what}: the line says {state()}')
            out['said'][what] = said()
        settle(what)
        require([x[1] for x in pedal()[0]] == ['boost', 'muff' if changed else 'ts9', 'eq'] and [x[1] for x in pedal()[1]] == ['gate', 'delay', 'rat'], f'{what}: {pedal()}')
        load(one)
    # moved, saved, given back
    fresh(*series)
    _, new = swap('to move', 'P', 1, 'muff')
    cdp.evaluate(f'void moveBlock({new}, {{t: "serial", si: 0}})')
    page.wait('__pedal.chain.P[0].type === "muff" && ' + quiet, 'the new block moved', 10)
    cdp.evaluate(f'void moveBlock({new}, {{t: "newgrp", si: 5}})')
    page.wait('__pedal.chain.Q.some(x => x.type === "muff" && x.lane === 1) && ' + quiet, 'and on a branch', 10)
    settle('moved')
    swap('on its new branch', 'Q', next(k for k, x in enumerate(pedal()[1]) if x[1] == 'muff'), 'phaser')
    cdp.click('#saveDiscard')
    page.wait('/Discard changes/i.test(document.querySelector(".mdlg")?.innerText || "")', 'the question', 10)
    cdp.evaluate('document.querySelector(".mdlg .mdlg-ok").click()')
    page.wait(f'edCount() === 0 && JSON.stringify(__view(__pedal.chain)) === JSON.stringify(__view(__pedal.store[{one}].chain)) && ' + quiet, 'Discard brings the old blocks back', 15)
    require([x[1] for x in pedal()[0]] == ['boost', 'ts9', 'eq'], f'after Discard: {pedal()}')
    settle('given back')
    swap('to save', 'P', 1, 'muff')
    cdp.click('#saveGo')
    page.wait(f'edCount() === 0 && __pedal.store[{one}].chain.P[1].type === "muff" && ' + quiet, 'saved', 15)
    # a chain that has no preset yet
    free = next(k for k in range(31, 0, -1) if k not in (one, two) and not cdp.evaluate(f'!!__pedal.store[{k}]'))
    cdp.evaluate(f'void (async () => {{ const p = newPedalboard({free}); await new Promise(r => setTimeout(r, 400)); '
                 'const b = [...document.querySelectorAll("button")].find(e => e.offsetParent && e.innerText.trim() === "Start new"); if (b) b.click(); await p; await addFx("boost"); })()')
    page.wait('curPreset === -1 && [...__pedal.chain.P, ...__pedal.chain.Q].length === 1 && ' + quiet, 'a new preset', 20)
    swap_new = count()
    cdp.evaluate('void replaceFx([...S.chain.P, ...S.chain.Q][0].id, "comp")')
    page.wait('[...__pedal.chain.P, ...__pedal.chain.Q][0].type === "comp" && ' + quiet, 'in a preset without a slot', 10)
    require(state()[0] == 'new', f'a preset without a slot: the line says {state()}')
    require([c for c in sent(swap_new) if c.startswith('FXC')] == ['FXC -1 0 boost comp'], f'without a preset: {sent(swap_new)}')
    want = {'not enough CPU': ['Not enough CPU', 'Not enough CPU for'], 'not enough memory': ['Not enough memory', 'Not enough memory for'], 'no IR': ['No cab IR yet', 'Pick one from the library, or load a .wav.'],
            'a footswitch before the command arrives': ['Not replaced', 'The pedal has another preset now. Nothing was replaced.'], 'a footswitch that the rules have seen': ['Not replaced', 'The pedal has another preset now. Nothing was replaced.'],
            'no answer': ['The pedal did not answer', 'The chain shows what is on it.']}
    for what, (title, text) in want.items():
        got = out['said'].get(what) or [['', '']]
        require(len(got) == 1 and got[0][0] == title and got[0][1].startswith(text) and 'ERR' not in got[0][1], f'{what}: said {got}')
    require(all(out['said'][k][0][1].count('stays as it was.') == 1 for k in ('not enough CPU', 'not enough memory', 'no IR')), f"it is not said that the old block stays: {out['said']}")
    cdp.evaluate(f'edClear(); __pedal.hook = __pedal.silent = null; void (async () => {{ for (const n of [{one}, {two}]) await Pedal.cmd("PDEL " + n, "PDEL"); await loadPresets(); window.__gone = true; }})()')
    page.wait('window.__gone === true && ' + quiet, 'the presets of this step taken away', 20)
    if start >= 0:
        load(start)
    clear()
    return out


def preset_files(page):
    """A preset and all of them go to a file and come back: what is sent, what the files hold, and the pedal as it was afterwards."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !Pedal.busy'
    cdp.evaluate('void (async () => { if (edCount()) { const n = curPreset >= 0 ? curPreset : 0; await loadPreset(n); } })()')
    page.wait(quiet, 'a quiet page', 20)
    cdp.evaluate('window.__files = []; pioSaveFile = async (name, text) => { __files.push([name, text]); return "file"; };')
    before = cdp.evaluate('JSON.stringify([__pedal.store, __pedal.presets, curPreset, S.snap])')
    out = {}
    # another scene than the first is on: the export reads them all, and must leave the pedal on this one
    two = [int(k) for k in cdp.evaluate('Object.keys(__pedal.store).filter(k => __pedal.store[k] && /^11/.test(__pedal.store[k].scenes))')]
    require(two, 'no preset has two scenes')
    cdp.evaluate(f'void (async () => {{ await loadPreset({two[0]}); await goSnap(1); window.__on = true; }})()')
    page.wait(f'window.__on === true && curPreset === {two[0]} && S.snap === 1 && __pedal.scene === 1 && ' + quiet, 'the second scene', 20)
    before = cdp.evaluate('JSON.stringify([__pedal.store, __pedal.presets, curPreset, S.snap])')
    out = {}
    for name, call in (('one', 'pioExport(false)'), ('all', 'pioExport(true)')):
        n = len(cdp.evaluate('__pedal.sent'))
        cdp.evaluate('void ' + call)
        done = 'window.__files.length === ' + str(1 if name == 'one' else 2)
        deadline = time.monotonic() + 60
        while not cdp.evaluate(done):                                       # its questions are answered as they come: the name, what to include
            require(time.monotonic() < deadline, 'the export of ' + name + ' does not end: ' + str(cdp.evaluate(TOASTS)))
            cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
            time.sleep(0.4)
        page.wait(quiet, 'the end of the export', 20)
        sent = cdp.evaluate('__pedal.sent')[n:]
        words = {c.split(' ')[0] for c in sent}
        require(not words & {'PSAVE', 'SNAPSAVE', 'PDEL', 'PNEW', 'FXA', 'FXR', 'FXP', 'FXM', 'CSAVE', 'ISAVE', 'GSAVE', 'PCOLOR ', 'PNAME'}, f'an export changes the pedal: {sent}')
        file, text = cdp.evaluate('__files[__files.length - 1]')
        doc = json.loads(text)
        out[name] = {'file': file, 'presets': len(doc['presets']), 'kinds': sorted(words)}
        require('ERR' not in text and file.endswith('.json'), 'the file of ' + name)
    kept = cdp.evaluate('Object.keys(__pedal.store).filter(k => __pedal.store[k]).length')
    require(out['one']['presets'] == 1 and out['all']['presets'] == kept, f'the presets of the files: {out}, of the pedal: {kept}')
    require(cdp.evaluate('JSON.stringify([__pedal.store, __pedal.presets, curPreset, S.snap])') == before, 'the pedal is not as it was')
    require(cdp.evaluate('__pedal.scene') == 1, f"after the export the pedal is on scene {cdp.evaluate('__pedal.scene')}")
    require(not cdp.evaluate('[...document.querySelectorAll("#toasts > *")].some(e => /Couldn/.test(e.innerText))'), 'an export complained: ' + str(cdp.evaluate(TOASTS)))
    # the chain of the file is the chain of the pedal, block by block
    doc = json.loads(cdp.evaluate('__files[1][1]'))
    stored = cdp.evaluate('Object.entries(__pedal.store).filter(([k, v]) => v).map(([k, v]) => [...v.chain.P, ...v.chain.Q].map(x => x.type))')
    def blocks(preset):
        found = []
        for part in preset['sound']['chain']:
            found += [b['type'] for b in ([part] if 'type' in part else [*part['split']['a'], *part['split']['b']] if 'split' in part else [])]
        return found
    in_file = [blocks(p) for p in doc['presets']]
    require(in_file == stored, f'the blocks of the file {in_file}, of the pedal {stored}')
    # and back: the file of one preset, over an empty chain
    one = blocks(json.loads(cdp.evaluate('__files[0][1]'))['presets'][0])
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('void (async () => { await Pedal.cmd("PNEW", "PNEW", 4000); await loadChain(); await loadSnaps(); window.__cleared = true; })()')
    page.wait('window.__cleared === true && __pedal.chain.P.length + __pedal.chain.Q.length === 0 && __pedal.scenes === "00000000" && ' + quiet, 'an empty chain before the import', 20)
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('window.__imported = undefined; void pioImport(__files[0][1]).then(v => { window.__imported = v; })')
    deadline = time.monotonic() + 60
    while cdp.evaluate('[...__pedal.chain.P, ...__pedal.chain.Q].map(x => x.type)') != one:
        require(time.monotonic() < deadline, f"the import does not bring {one}: {cdp.evaluate('[...__pedal.chain.P, ...__pedal.chain.Q].map(x => x.type)')}, {cdp.evaluate(TOASTS + '.map(e => e.innerText)')}")
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.4)
    page.wait('!document.querySelector(".mdlg") && window.__imported !== undefined && ' + quiet, 'the end of the import', 30)
    time.sleep(1.0)
    require(not [c for c in cdp.evaluate('__pedal.sent')[n:] if c.split(' ')[0] in ('PSAVE', 'PDEL', 'CSAVE', 'GSAVE')], 'an import of one preset writes to the pedal')
    out['imported'] = one
    # with its scenes, all of them, in the pedal's memory, and nothing left out; they go to the slot with the preset
    sound = json.loads(cdp.evaluate('__files[0][1]'))['presets'][0]['sound']
    scenes = ''.join('1' if k in [x['index'] for x in sound['scenes']] else '0' for k in range(8))
    said = [' '.join(x.split()) for x in cdp.evaluate(TOASTS + '.map(e => e.innerText)')] + [cdp.evaluate('document.querySelector(".mdlg")?.innerText || ""')]
    require(scenes.count('1') > 1 and cdp.evaluate('__pedal.scenes') == scenes, f"the scenes of the file {scenes}, of the pedal {cdp.evaluate('__pedal.scenes')}: {said}")
    require(not any('apply' in x or 'with some changes' in x for x in said), f'the import was changed: {said}')
    # it has no slot yet: the pencil names it, and it is saved with that name
    page.wait('!document.getElementById("hrNameP").hidden && document.getElementById("hrNameP").title === "Name this preset"', 'the pencil of a preset without a slot', 10)
    cdp.evaluate('document.getElementById("hrNameP").click()')
    page.wait('!!document.querySelector("input.ied")', 'the field of the name', 10)
    cdp.evaluate('(() => { const i = document.querySelector("input.ied"); i.value = "L\u00e0 mia"; i.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true})); })()')
    page.wait('S.pendName === "La mia" && /LA MIA/i.test(document.getElementById("presetLbl").innerText)', 'the name, in plain letters', 10)
    kept_before = cdp.evaluate('Object.keys(__pedal.store).filter(k => __pedal.store[k]).length')
    free = next(k for k in range(20, 32) if not cdp.evaluate(f'!!__pedal.store[{k}]'))
    cdp.evaluate(f'void savePreset({free})')
    deadline = time.monotonic() + 40
    while not cdp.evaluate(f'!!__pedal.store[{free}] && {quiet}'):                 # its questions: the name, and whether to keep the capture
        require(time.monotonic() < deadline, f"the imported preset is not saved: {cdp.evaluate(TOASTS + '.map(e => e.innerText)')}")
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.4)
    stored = cdp.evaluate(f'[__pedal.store[{free}].scenes, Object.keys(__pedal.store).filter(k => __pedal.store[k]).length]')
    require(stored == [scenes, kept_before + 1], f'the saved preset has the scenes {stored}, the file {scenes}')
    require(cdp.evaluate(f'__pedal.presets[{free}]') == 'La mia', f"the preset is saved as {cdp.evaluate(f'__pedal.presets[{free}]')}")
    out['scenes'] = scenes
    out['blocks'] = in_file
    return out


def names(page, output):
    """A preset and a scene are renamed with the pencils, and other presets can be loaded afterwards; the names come back with the preset."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !Pedal.busy'
    slots = [int(k) for k in cdp.evaluate('Object.keys(__pedal.store).filter(k => __pedal.store[k])')]
    first, second = slots[0], slots[1]
    cdp.evaluate(f'void (async () => {{ await loadPreset({second}); await loadPreset({first}); }})()')
    page.wait(f'curPreset === {first} && __pedal.current === {first} && ' + quiet, 'a preset with a scene', 30)
    page.wait('!document.getElementById("hrNameP").hidden && !document.getElementById("hrNameS").hidden', 'the pencils', 10)
    seen = cdp.evaluate('["hrNameP", "hrNameS"].map(id => document.getElementById(id).title)')
    require(re.fullmatch(r'Rename preset [0-9]+[ABC]', seen[0]) and re.fullmatch(r'Rename scene [1-4]', seen[1]), f'the pencils: {seen}')

    def put(pencil, text, done):
        cdp.evaluate(f'document.getElementById("{pencil}").click()')
        page.wait('!!document.querySelector("input.ied")', 'the field of a name', 15)
        cdp.evaluate('(() => { const i = document.querySelector("input.ied"); i.value = ' + json.dumps(text) + '; i.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true})); })()')
        page.wait(done + ' && ' + quiet, text, 15)

    put('hrNameP', 'Clean verse', f'__pedal.presets[{first}] === "Clean verse"')
    k = cdp.evaluate('S.snap')
    put('hrNameS', 'Intro', f'__pedal.names[{k}] === "Intro"')
    cdp.screenshot(output / 'names.png')
    shown = cdp.evaluate('[document.getElementById("presetLbl").innerText, document.querySelector("#snaps .snap.on").innerText]')
    require('CLEAN VERSE' in shown[0].upper() and 'INTRO' in shown[1].upper(), f'the names are not shown: {shown}')
    said = cdp.evaluate(TOASTS + '.map(e => e.innerText)')
    require(not any('rename' in x.lower() or 'update' in x.lower() for x in said), f'a name was refused: {said}')
    cdp.evaluate(f'void loadPreset({second})')
    page.wait(f'curPreset === {second} && __pedal.current === {second} && ' + quiet, 'another preset after a name', 20)
    cdp.evaluate(f'void loadPreset({first})')
    page.wait(f'curPreset === {first} && S.snapNames[{k}] === "Intro" && presetName() === "Clean verse" && ' + quiet, 'the names, come back with the preset', 20)
    # Esc leaves the name
    cdp.evaluate('document.getElementById("hrNameP").click()')
    page.wait('!!document.querySelector("input.ied")', 'the field', 10)
    cdp.evaluate('(() => { const i = document.querySelector("input.ied"); i.value = "Other"; i.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true})); })()')
    time.sleep(0.6)
    require(cdp.evaluate(f'__pedal.presets[{first}]') == 'Clean verse', 'Esc changed a name')
    return {'pencils': seen, 'shown': shown}


def setups(page, output):
    """What A, B and C do: Presets, Stomp and Scenes chosen in their window, what the pedal is told, and what is kept; own actions; live mode."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !fsQuickBusy && !Pedal.busy'
    none = '[[0,0,255],[0,0,255],[0,0,255]]'
    first = cdp.evaluate('[0, 1, 2].map(f => { const b = fsBlks()[f]; return b ? JSON.stringify([8, ...fsIdent(b)]) : "[8,0,0]"; })')        # the first three blocks, by their kind
    require(first[0] != '[8,0,0]' and len(set(first)) > 1, f'the blocks of the preset: {first}')
    stomp = lambda a=first[0]: f'[[{a},[0,0,255],[0,0,255]],[{first[1]},[0,0,255],[0,0,255]],[{first[2]},[0,0,255],[0,0,255]],{none}]'
    scenes = f'[[[1,0,255],[4,0,255],[0,0,255]],[[1,1,255],[0,0,255],[0,0,255]],[[1,2,255],[3,0,255],[0,0,255]],{none}]'
    out = {'seen': {}}
    cdp.evaluate('localStorage.removeItem("hyperrig.footswitches"); void fsOpen()')
    page.wait('document.getElementById("fsm").classList.contains("on") && !!document.querySelector("#fsQuick .fseg button")', 'the footswitches\' window', 15)

    def seen(name, choices, on, mark):
        page.wait(quiet, name, 20)
        want = [choices, on, mark]
        look = ('[[...document.querySelectorAll("#fsQuick .fseg button")].map(e => e.innerText), document.querySelector("#fsQuick .fseg button.on")?.innerText || "", '
                'document.getElementById("fmChip").hidden ? "" : document.getElementById("fmChip").textContent]')
        end = time.monotonic() + 10
        while cdp.evaluate(look) != want:
            require(time.monotonic() < end, f'{name}: {cdp.evaluate(look)}, not {want}')
            time.sleep(0.2)
        out['seen'][name] = want

    def choose(label):
        require(cdp.evaluate(f'(() => {{ const b = [...document.querySelectorAll("#fsQuick .fseg button")].find(e => e.innerText === {json.dumps(label)}); if (b) b.click(); return !!b; }})()'), f'no choice {label}')

    def answer(title, yes):
        page.wait(f'/{title}/i.test(document.querySelector(".mdlg")?.innerText || "")', title, 10)
        cdp.evaluate(f'[...document.querySelectorAll(".mdlg button")].find(e => e.innerText.trim() === {json.dumps(yes)}).click()')

    three = ['Presets', 'Stomp', 'Scenes']
    seen('as it comes', three, 'Presets', '')
    text = cdp.evaluate('document.getElementById("fsm").innerText').upper()
    require(all(x in text for x in ('WHAT DO A, B AND C DO?', 'A+B AND B+C: THE BANK')) and not any(x in text for x in ('QUICK SETUP', 'STOMPBOX', 'FACTORY', 'LIVE MODE', '1-4', 'UNASSIGNED')), f'the window: {text}')
    cdp.screenshot(output / 'setup-presets.png')
    n = len(cdp.evaluate('__pedal.sent'))
    choose('Stomp')
    page.wait(f'__pedal.layout === "custom" && JSON.stringify(__pedal.fsa) === "{stomp()}"', 'Stomp on the pedal', 15)
    seen('stomp', three, 'Stomp', 'Stomp')
    require(not cdp.evaluate('!!document.querySelector(".mdlg")') and 'A+B and B+C: the preset before and the next' in cdp.evaluate('document.getElementById("fsQuick").innerText'), 'what Stomp says')
    require(not [c for c in cdp.evaluate('__pedal.sent')[n:] if c.split(' ')[0] in ('GSAVE', 'PSAVE', 'SNAPSAVE')], 'a choice was kept without being asked')
    tall = cdp.evaluate('[...document.querySelectorAll("#fsCols select")].map(e => Math.round(e.getBoundingClientRect().height))')
    require(tall and max(tall) <= 48, f'the menus of the switches are {tall} high')
    cdp.screenshot(output / 'setup-stomp.png')
    # the block of a switch, by its kind; it is still Stomp, and comes back after another choice
    other = cdp.evaluate('(() => { const b = fsBlks()[1], s = document.getElementById("fsA00x1"); s.value = String(b.id); s.onchange(); return JSON.stringify([8, ...fsIdent(b)]); })()')
    require(other != first[0], 'another block for A')
    page.wait(f'JSON.stringify(__pedal.fsa) === "{stomp(other)}"', 'a block chosen for A', 10)
    seen('stomp with a block', three, 'Stomp', 'Stomp')
    choose('Scenes')
    page.wait(f'JSON.stringify(__pedal.fsa) === "{scenes}"', 'Scenes on the pedal', 15)
    seen('scenes', three, 'Scenes', 'Scenes')
    choose('Stomp')
    page.wait(f'JSON.stringify(__pedal.fsa) === "{stomp(other)}"', 'the chosen block is back', 15)
    seen('stomp again', three, 'Stomp', 'Stomp')
    # a switch without a block, in a preset with fewer of them, takes the block of its place when there is one
    empty = [f for f in range(3) if cdp.evaluate(f'String(__pedal.fsa[{f}][0])') == '8,0,0']
    if empty:
        count = cdp.evaluate('fsBlks().length')
        for _ in range(3 - count):
            cdp.evaluate('void addFx("boost")')
            page.wait(f'fsBlks().length > {count} && ' + quiet, 'a block more', 15)
            count += 1
        choose('Scenes')
        seen('scenes, before a third block', three, 'Scenes', 'Scenes')
        choose('Stomp')
        third = cdp.evaluate(f'JSON.stringify([8, ...fsIdent(fsBlks()[{empty[0]}])])')
        page.wait(f'JSON.stringify(__pedal.fsa[{empty[0]}][0]) === "{third}"', 'the block of its place', 15)
        cdp.evaluate('void loadPreset(curPreset)')
        page.wait('edCount() === 0 && ' + quiet, 'the preset as it was', 15)
    out['empty'] = empty
    choose('Presets')
    page.wait('__pedal.layout === "factory"', 'Presets on the pedal', 15)
    seen('presets', three, 'Presets', '')
    # an action of one's own: Custom; it is asked before it is replaced, and it comes back from Presets
    choose('Scenes')
    seen('scenes again', three, 'Scenes', 'Scenes')
    cdp.evaluate('fsSetAct(2, 0, 7)')
    seen('custom', three + ['Custom'], 'Custom', 'Custom')
    choose('Stomp')
    answer('Use Stomp', 'Cancel')
    seen('custom, kept', three + ['Custom'], 'Custom', 'Custom')
    choose('Presets')
    seen('presets with own actions left', three + ['Custom'], 'Presets', '')
    choose('Custom')
    page.wait('__pedal.layout === "custom" && __pedal.fsa[2][0][0] === 7', 'the own actions are back', 15)
    seen('custom again', three + ['Custom'], 'Custom', 'Custom')
    choose('Scenes')
    answer('Use Scenes', 'Use it')
    seen('scenes, own actions replaced', three, 'Scenes', 'Scenes')
    choose('Presets')
    seen('presets again', three, 'Presets', '')
    # a pedal that is in live mode: the window says so, and Presets leaves it
    cdp.evaluate('__pedal.mode = "live"; void Pedal.cmd("FSMODE", "FSMODE").then(r => { fmApply(parseFsMode(r[0])); fsRender(); })')
    seen('live', three, '', 'Live')
    require('live mode' in cdp.evaluate('document.getElementById("fsQuick").innerText') and 'First reverb' in cdp.evaluate('document.getElementById("fsCols").innerText'), 'what the window says in live mode')
    choose('Presets')
    page.wait('__pedal.mode === "preset"', 'live mode left', 15)
    seen('live left', three, 'Presets', '')
    cdp.evaluate('fsClose()')
    # the mark says the setup after the page connects again, without the window
    cdp.evaluate('__pedal.layout = "custom"; stFsReady = false; void Pedal.cmd("FSMODE", "FSMODE").then(r => fmApply(parseFsMode(r[0])))')
    page.wait('!document.getElementById("fmChip").hidden && document.getElementById("fmChip").textContent === "Scenes"', 'the mark of a pedal that comes with Scenes', 15)
    cdp.evaluate('document.getElementById("fmChip").click()')
    page.wait('document.getElementById("fsm").classList.contains("on")', 'the mark opens the window', 15)
    choose('Presets')
    seen('the end', three, 'Presets', '')
    cdp.evaluate('fsClose()')
    said = cdp.evaluate(TOASTS + '.map(e => e.innerText)')
    require(not any('Couldn' in x or 'outside' in x for x in said), f'the choice complained: {said}')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    return out


def save_line(page, output):
    """The line of the saving, in each state: what it says, its buttons, and what each of them writes."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !hrSaving && !Pedal.busy'
    line = ('(() => { const t = document.getElementById("saveTxt").innerText.replace(/\\s+/g, " "), b = [...document.querySelectorAll("#saveBar .btn")].filter(e => e.offsetParent).map(e => e.innerText.trim()); '
            'return [document.getElementById("saveBar").hidden ? "" : t, b]; })()')
    out = {'states': {}}

    def state(name, text, buttons):
        page.wait(quiet, name, 20)
        deadline = time.monotonic() + 8
        while cdp.evaluate(line) != [text, buttons]:
            require(time.monotonic() < deadline, f'{name}: the line says {cdp.evaluate(line)}, not {[text, buttons]}')
            time.sleep(0.2)
        out['states'][name] = [text, buttons]

    def sent(since):
        return [c for c in cdp.evaluate('__pedal.sent')[since:] if c.split(' ')[0] in ('PSAVE', 'SNAPSAVE', 'PNAME', 'PDEL', 'CSAVE', 'GSAVE')]

    def dialog(title):
        page.wait(f'/{title}/i.test(document.querySelector(".mdlg")?.innerText || "")', title, 15)

    def button(label):
        require(cdp.evaluate(f'(() => {{ const b = [...document.querySelectorAll(".mdlg button")].find(e => e.offsetParent && e.innerText.trim() === {json.dumps(label)}); if (b) b.click(); return !!b; }})()'),
                f"no button {label}: {cdp.evaluate('document.querySelector(`.mdlg`)?.innerText')}")

    def slot(n):
        return f'{n // 3 + 1}{"ABC"[n % 3]}'

    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('if (document.getElementById("fsm").classList.contains("on")) fsClose()')          # left open by a step before
    home = next(int(k) for k in cdp.evaluate('Object.keys(__pedal.store)') if cdp.evaluate(f'__pedal.store[{k}].scenes') == '10000000')
    cdp.evaluate(f'void loadPreset({home})')
    page.wait(f'curPreset === {home} && S.snap === 0 && ' + quiet, 'a preset with one scene', 20)
    state('saved', f'Saved in {slot(home)}', ['Save as…'])
    disks = cdp.evaluate('[...document.querySelectorAll("#snapSave, #pList [data-a=s]")].filter(e => e.offsetParent).length')
    require(disks == 0, f'{disks} disks are still shown')
    # a change, and back
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('void addFx("boost")')
    page.wait('edCount() > 0 && ' + quiet, 'a change')
    state('a block added', f'Not saved · changes in {slot(home)}, for all its scenes', ['Discard', 'Save as…', f'Save to {slot(home)}'])
    require(cdp.evaluate('!!document.querySelector("#pList .pslot.cur.hrchg")') or cdp.evaluate(f'bank !== {home // 3}'), 'the row does not show it')
    cdp.screenshot(output / 'save-changed.png')
    cdp.click('#saveDiscard')
    dialog('Discard changes')
    button('Discard')
    state('discarded', f'Saved in {slot(home)}', ['Save as…'])
    require(not sent(n), f'a discarded change wrote {sent(n)}')
    # a knob is of the scene
    cdp.evaluate('void toggle(fsBlks()[0].id)')
    page.wait('edCount() > 0 && ' + quiet, 'a block switched')
    state('a block switched', f'Not saved · changes in scene 1 of {slot(home)}', ['Discard', 'Save as…', f'Save to {slot(home)}'])
    cdp.click('#saveDiscard')
    dialog('Discard changes')
    button('Discard')
    state('switched back', f'Saved in {slot(home)}', ['Save as…'])
    # a change saved with the keyboard
    blocks = cdp.evaluate(f'__pedal.store[{home}].chain.Q.length')
    cdp.evaluate('void addFx("boost")')
    page.wait('edCount() > 0 && ' + quiet, 'a change')
    n = len(cdp.evaluate('__pedal.sent'))
    # not under a panel that covers the line
    cdp.evaluate('document.getElementById("fsm").classList.add("on"); document.dispatchEvent(new KeyboardEvent("keydown", {key: "s", ctrlKey: true, bubbles: true, cancelable: true}))')
    time.sleep(0.8)
    require(not sent(n) and cdp.evaluate('edCount()') > 0, 'Ctrl+S saved under a panel')
    cdp.evaluate('document.getElementById("fsm").classList.remove("on")')
    cdp.evaluate('document.dispatchEvent(new KeyboardEvent("keydown", {key: "s", ctrlKey: true, bubbles: true, cancelable: true}))')
    page.wait(f'__pedal.store[{home}].chain.Q.length === {blocks + 1} && edCount() === 0', 'Ctrl+S', 15)
    state('saved again', f'Saved in {slot(home)}', ['Save as…'])
    require(sent(n) == ['SNAPSAVE 0'], f'Ctrl+S wrote {sent(n)}')
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('document.dispatchEvent(new KeyboardEvent("keydown", {key: "s", ctrlKey: true, bubbles: true, cancelable: true}))')
    time.sleep(0.8)
    require(not sent(n) and not cdp.evaluate('!!document.querySelector(".mdlg")'), 'Ctrl+S with nothing to save did something')
    # a copy, with a name, in the first empty slot; then over a preset, answered no
    other = cdp.evaluate(f'JSON.stringify(__pedal.store[{home}])')
    free = next(k for k in [*range(home, 32), *range(home)] if not cdp.evaluate(f'!!__pedal.store[{k}]'))
    cdp.click('#hrSaveAs')
    dialog('Save this preset')
    require(cdp.evaluate('+document.querySelector(".mdlg select").value') == free, f"the slot offered is {cdp.evaluate('document.querySelector(`.mdlg select`).value')}, not {free}")
    cdp.screenshot(output / 'save-as.png')
    cdp.evaluate('document.querySelector(".mdlg input").value = "Copia \u00e8 mia"')
    button('Save')
    page.wait(f'!!__pedal.store[{free}] && curPreset === {free} && ' + quiet, 'the copy', 20)
    require(cdp.evaluate(f'__pedal.presets[{free}]') == 'Copia e mia' and cdp.evaluate(f'JSON.stringify(__pedal.store[{home}])') == other, 'the copy, or the original')
    state('copied', f'Saved in {slot(free)}', ['Save as…'])
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.click('#hrSaveAs')
    dialog('Save this preset')
    cdp.evaluate(f'(() => {{ const s = document.querySelector(".mdlg select"); s.value = "{home}"; s.onchange(); }})()')
    require('Replaces' in cdp.evaluate('document.querySelector(".mdlg").innerText'), 'it does not say what is replaced')
    button('Save')
    dialog('Overwrite preset')
    button('Cancel')
    state('not overwritten', f'Saved in {slot(free)}', ['Save as…'])
    require(not sent(n) and not cdp.evaluate('S.pendName') and 'COPIA E MIA' in cdp.evaluate('document.getElementById("presetLbl").innerText').upper(), 'a save answered no')
    # a new preset without a slot: Save asks for the name and the slot
    cdp.evaluate('void newPedalboard()')
    dialog('Start a new preset')
    button('Start new')
    page.wait('curPreset === -1 && ' + quiet, 'a new preset', 20)
    state('new', 'Not saved · new preset, without a slot yet', ['Save to…'])
    require('NEW PRESET' in cdp.evaluate('document.getElementById("presetLbl").innerText').upper(), 'the title of a new preset')
    cdp.evaluate('void addFx("gate")')
    page.wait('__pedal.chain.Q.length === 1 && ' + quiet, 'a block')
    cdp.click('#saveGo')
    dialog('Save this preset')
    button('Cancel')
    state('new, not saved', 'Not saved · new preset, without a slot yet', ['Save to…'])
    require(cdp.evaluate('curPreset') == -1, 'a cancelled save chose a preset')
    cdp.click('#saveGo')
    dialog('Save this preset')
    second = int(cdp.evaluate('document.querySelector(".mdlg select").value'))
    require(not cdp.evaluate(f'!!__pedal.store[{second}]'), 'the slot offered is not empty')
    button('Save')
    answer = time.monotonic() + 20
    while not cdp.evaluate(f'!!__pedal.store[{second}] && {quiet}'):                         # the question of the capture that plays, if it is asked
        require(time.monotonic() < answer, 'a new preset is not saved')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    require(cdp.evaluate(f'__pedal.presets[{second}]') == f'Preset {slot(second)}', f"the name of a preset without one: {cdp.evaluate(f'__pedal.presets[{second}]')}")
    state('new, saved', f'Saved in {slot(second)}', ['Save as…'])
    # a new preset for a slot: its row shows it, Save writes there
    third = next(k for k in range(31, 0, -1) if not cdp.evaluate(f'!!__pedal.store[{k}]'))
    cdp.evaluate(f'bank = {third // 3}; void newPedalboard({third})')
    dialog('Start a new preset')
    button('Start new')
    page.wait(f'curPreset === -1 && hrSlot === {third} && ' + quiet, 'a new preset for a slot', 20)
    state('new for a slot', f'Not saved · new preset for {slot(third)}', ['Other slot…', f'Save to {slot(third)}'])
    require(cdp.evaluate(f'/New preset/.test(document.querySelector("#pList [data-preset=\'{third}\']").innerText)'), 'the row of the new preset')
    cdp.screenshot(output / 'save-new.png')
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate(f'document.querySelector("#pList [data-preset=\'{third}\'] .n").click()')
    time.sleep(0.8)
    require(not cdp.evaluate('!!document.querySelector(".mdlg")') and not sent(n), 'a click on the row of the new preset starts it again')
    cdp.click('#saveGo')
    answer = time.monotonic() + 20
    while not cdp.evaluate(f'!!__pedal.store[{third}] && {quiet}'):
        require(time.monotonic() < answer, 'a new preset for a slot is not saved')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    state('saved in its slot', f'Saved in {slot(third)}', ['Save as…'])
    # a footswitch that loads another preset: the line follows
    cdp.evaluate(f'__pedal.press({home})')
    page.wait(f'curPreset === {home}', 'the footswitch', 20)
    state('after a footswitch', f'Saved in {slot(home)}', ['Save as…'])
    cdp.evaluate(f'void (async () => {{ for (const k of [{free}, {second}, {third}]) await Pedal.cmd("PDEL " + k, "PDEL"); await loadPresets(); window.__cleaned = true; }})()')
    page.wait('window.__cleaned === true && ' + quiet, 'the presets of this step taken away', 20)
    said = cdp.evaluate(TOASTS + '.map(e => e.innerText)')
    require(not any('Couldn' in x or 'outside' in x or 'unavailable' in x for x in said), f'the saving complained: {said}')
    return out


def eight_scenes(page, output):
    """Eight scenes: the tabs that are shown, one to add until there are eight, their names, a scene taken away in the middle, a file with eight and back, the groups of
    the switches, and a preset without room for another."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !hrSaving && !Pedal.busy'
    tabs = '[...document.querySelectorAll("#snaps .snap")].map(e => [e.dataset.snap, e.classList.contains("vacio") ? "add" : "scene", Math.round(e.getBoundingClientRect().width)])'
    free = next(k for k in range(31, 0, -1) if not cdp.evaluate(f'!!__pedal.store[{k}]'))
    home = next(int(k) for k in cdp.evaluate('Object.keys(__pedal.store)') if cdp.evaluate(f'__pedal.store[{k}].scenes') == '10000000')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate(f'void loadPreset({home})')
    page.wait(f'curPreset === {home} && ' + quiet, 'a preset with one scene', 20)
    cdp.evaluate(f'S.pendName = "Eight"; void savePreset({free})')
    page.wait(f'!!__pedal.store[{free}] && curPreset === {free} && ' + quiet, 'its copy', 20)
    out = {'tabs': [[t[:2] for t in cdp.evaluate(tabs)]]}
    for k in range(1, 8):
        cdp.click(f'#snaps .snap[data-snap="{k}"]')
        page.wait(f'__pedal.scenes === "{("1" * (k + 1)).ljust(8, "0")}" && S.snap === {k} && ' + quiet, f'scene {k + 1}', 15)
        time.sleep(0.3)
        out['tabs'].append([t[:2] for t in cdp.evaluate(tabs)])
    want = [[[str(i), 'scene'] for i in range(n)] + ([[str(n), 'add']] if n < 8 else []) for n in range(1, 9)]
    require(out['tabs'] == want, f"the tabs: {out['tabs']}")
    for k, name in ((0, 'Clean'), (4, 'Crunch'), (7, 'Solo lead')):
        cdp.evaluate(f'void renameSnap({k}, "{name}")')
        page.wait(f'__pedal.names[{k}] === "{name}" && S.snapNames[{k}] === "{name}" && ' + quiet, name, 15)
    shown = cdp.evaluate(tabs)
    wide = cdp.evaluate('(() => { const a = document.getElementById("snaps").getBoundingClientRect(), b = document.getElementById("hrNameS").getBoundingClientRect(); return [a.right, b.right, innerWidth, document.documentElement.scrollWidth]; })()')
    require(len(shown) == 8 and min(t[2] for t in shown) >= 44 and wide[1] <= wide[2] and wide[3] <= wide[2] + 1, f'eight tabs do not fit: {shown}, {wide}')
    name = cdp.evaluate('(() => { const e = document.getElementById("presetLbl"), s = e.querySelector("span"); return [e.innerText, s.scrollWidth, s.clientWidth]; })()')
    require('EIGHT' in name[0].upper() and name[1] <= name[2] + 1, f'the name of the preset has no room: {name}')
    cut = cdp.evaluate('[...document.querySelectorAll("#snaps .snap")].map(e => { const n = e.querySelector(".snn").getBoundingClientRect(), t = e.getBoundingClientRect(); return [e.querySelector(".snn").textContent, n.width > 4 && n.left >= t.left && n.right <= t.right, e.querySelector(".snl").scrollWidth <= e.querySelector(".snl").clientWidth + 1]; })')
    require([c[0] for c in cut] == [str(k) for k in range(1, 9)] and all(c[1] and c[2] for c in cut), f'the number of a scene is hidden: {cut}')
    cdp.screenshot(output / 'eight-scenes.png')
    require('8 scenes' in cdp.evaluate(f'(() => {{ bank = {free // 3}; renderPresets(); return document.querySelector("#pList [data-preset=\'{free}\']").innerText; }})()'), 'the list does not say how many')
    cdp.click('#snaps .snap[data-snap="5"]')
    page.wait('__pedal.scene === 5 && S.snap === 5 && ' + quiet, 'the sixth scene', 15)
    # the switches: in Scenes the taps of the stage are the group that the pedal says
    for f in range(3):
        cdp.evaluate(f'void Pedal.cmd("FSA {f} 0 1 {f} 255", "FSA end")')
    cdp.evaluate('__pedal.layout = "custom"; __pedal.bank = 2; void (async () => { for (const c of ["FSA 0 1 4 0 255", "FSA 1 1 0 0 255", "FSA 2 1 3 0 255", "FSA 3 0 0 0 255", "FSA 3 1 0 0 255"]) await Pedal.cmd(c, "FSA end"); '
                 'fmApply(parseFsMode((await Pedal.cmd("FSMODE", "FSMODE"))[0])); await fsLoad(); window.__fs = true; })()')
    page.wait('window.__fs === true && hrSetup() === "snaps" && ' + quiet, 'Scenes on the switches', 20)
    out['group'] = cdp.evaluate('[0, 1, 2].map(f => hrScene(f))')
    out['stage'] = cdp.evaluate('[0, 1, 2].map(f => stAct(fsTab[f][0]).big)')
    require(out['group'] == [3, 4, 5] and out['stage'] == ['Scene 4', 'Crunch', 'Scene 6'], f"the group of the switches: {out['group']}, {out['stage']}")
    cdp.evaluate('__pedal.layout = "factory"; __pedal.bank = 1; void Pedal.cmd("FSMODE", "FSMODE").then(r => fmApply(parseFsMode(r[0])))')
    page.wait('S.fm.layout === 0 && hrScene(1) === 1', 'the factory layout', 10)
    # one in the middle is taken away: its tab is the one to add
    cdp.evaluate('void delSnap(2)')
    page.wait('/Delete/i.test(document.querySelector(".mdlg")?.innerText || "")', 'the question', 10)
    cdp.evaluate('document.querySelector(".mdlg .mdlg-ok").click()')
    page.wait('__pedal.scenes === "11011111" && ' + quiet, 'a scene taken away', 15)
    time.sleep(0.4)
    require([t[:2] for t in cdp.evaluate(tabs)][2] == ['2', 'add'] and len(cdp.evaluate(tabs)) == 8, f'the tabs after it: {cdp.evaluate(tabs)}')
    cdp.click('#snaps .snap[data-snap="2"]')
    page.wait('__pedal.scenes === "11111111" && S.snap === 2 && ' + quiet, 'and made again', 15)
    # a file with eight, and back
    cdp.evaluate('window.__files = []; pioSaveFile = async (name, text) => { __files.push([name, text]); return "file"; }; void pioExport(false)')
    end = time.monotonic() + 60
    while not cdp.evaluate('__files.length === 1'):
        require(time.monotonic() < end, 'the export with eight scenes does not end')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    page.wait(quiet, 'the end of the export', 20)
    sound = json.loads(cdp.evaluate('__files[0][1]'))['presets'][0]['sound']
    require([s['index'] for s in sound['scenes']] == list(range(8)) and [s['name'] for s in sound['scenes']][4] == 'Crunch', f"the scenes of the file: {[s['index'] for s in sound['scenes']]}")
    require(cdp.evaluate('__pedal.scene') == 2, 'the scene after the export')
    cdp.evaluate('window.__back = undefined; void pioImport(__files[0][1]).then(v => { window.__back = v; })')
    end = time.monotonic() + 60
    while cdp.evaluate('window.__back === undefined'):
        require(time.monotonic() < end, 'the import with eight scenes does not end')
        cdp.evaluate('document.querySelector(".mdlg .mdlg-ok")?.click()')
        time.sleep(0.3)
    page.wait('!document.querySelector(".mdlg") && ' + quiet, 'the end of the import', 20)
    require(cdp.evaluate('__pedal.scenes') == '11111111' and cdp.evaluate('__pedal.names[7]') == 'Solo lead', f"the import: {cdp.evaluate('__pedal.scenes')}, {cdp.evaluate('__pedal.names')}")
    # no room for another: said in words, and nothing changes
    cdp.evaluate(f'void loadPreset({home})')
    page.wait(f'curPreset === {home} && ' + quiet, 'the first preset', 20)
    cdp.evaluate(TOASTS + '.forEach(e => e.remove()); __pedal.noRoom = true')
    cdp.click('#snaps .snap[data-snap="1"]')
    page.wait(TOASTS + '.some(e => /no room for this scene/i.test(e.innerText))', 'what is said without room', 10)
    require(cdp.evaluate('__pedal.scenes') == '10000000' and not cdp.evaluate(TOASTS + '.some(e => /ERR/.test(e.innerText))'), 'a scene without room')
    cdp.evaluate(f'__pedal.noRoom = false; void (async () => {{ await Pedal.cmd("PDEL {free}", "PDEL"); await loadPresets(); window.__cleared8 = true; }})()')
    page.wait('window.__cleared8 === true && ' + quiet, 'the preset of this step taken away', 20)
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    return out


def import_all(page, output):
    """The file of all presets comes back at once, each in its slot: one that was deleted, one that was changed, one that is in the way. A footswitch
    pressed in the middle stops it, and nothing is saved over a slot by mistake."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !Pedal.busy'
    text = 'window.__files[1][1]'
    doc = json.loads(cdp.evaluate(text))
    slots = [(int(p['meta']['slot'][:-1]) - 1) * 3 + 'ABC'.index(p['meta']['slot'][-1]) for p in doc['presets']]
    require(len(slots) > 1 and len(set(slots)) == len(slots), f'the slots of the file: {slots}')
    state = '(ks => JSON.stringify(ks.map(k => { const s = __pedal.store[k]; return s && [__pedal.presets[k], s.scenes, s.names, s.ampeq, [...s.chain.P, ...s.chain.Q].map(x => [x.type, x.on, x.p])]; })))'
    want = cdp.evaluate(f'{state}({json.dumps(slots)})')
    others = [int(k) for k in cdp.evaluate('Object.keys(__pedal.store)') if int(k) not in slots]
    require(others, 'no preset beside those of the file')
    before = cdp.evaluate(f'{state}({json.dumps(others)})')
    out = {'slots': slots, 'others': others}

    def run():
        """Import all, with yes to each question."""
        cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
        cdp.evaluate('window.__said = []; if (!window.__toast) { window.__toast = toast; toast = (m, ...more) => { __said.push(String(m)); return __toast(m, ...more); }; }')
        cdp.evaluate('window.__all = undefined; void pioImport(' + text + ').then(v => { window.__all = v; })')
        deadline = time.monotonic() + 90
        while cdp.evaluate('window.__all === undefined'):
            require(time.monotonic() < deadline, f"the import of all does not end: {cdp.evaluate(TOASTS + '.map(e => e.innerText)')}, {cdp.evaluate('document.querySelector(`.mdlg`)?.innerText')}")
            shown = cdp.evaluate('document.querySelector(".mdlg")?.innerText || ""')
            if shown:
                if 'REPLACED' in shown.upper() and not out.get('picture'):
                    out['picture'] = cdp.screenshot(output / 'import-all.png')['path']
                if not out.get('asked') or shown not in out['asked']:
                    out.setdefault('asked', []).append(shown)
                cdp.evaluate('(document.querySelector(".mdlg .mdlg-ok") || [...document.querySelectorAll(".mdlg button")].find(b => /All of them/.test(b.innerText)))?.click()')
            time.sleep(0.15)
        page.wait('!document.querySelector(".mdlg") && ' + quiet, 'the end of the import of all', 30)
        return cdp.evaluate('__said')

    # one is gone, one is something else
    cdp.evaluate(f'void (async () => {{ await Pedal.cmd("PDEL {slots[0]}", "PDEL"); const s = __pedal.store[{slots[1]}]; s.chain.Q = []; s.scenes = "10000000"; __pedal.presets[{slots[1]}] = "Other"; '
                 f'await loadPresets(); window.__gone = true; }})()')
    page.wait('window.__gone === true && ' + quiet, 'a deleted preset', 20)
    said = run()
    asked = ' | '.join(out['asked']).upper()
    require('PRESETS IN THIS FILE' in asked and f'IMPORT {len(slots)} PRESETS?' in asked and '"OTHER"' in asked, f'the questions: {asked}')
    have = cdp.evaluate(f'{state}({json.dumps(slots)})')
    require(have == want, f'the presets are not what the file has: {have}, {want}')
    require(cdp.evaluate(f'{state}({json.dumps(others)})') == before, 'another preset was changed')
    require(any(f'{len(slots)} presets imported' in x for x in said) and not any('outside' in x or 'Couldn' in x or 'stopped' in x for x in said), f'the import of all: {said}')
    require(cdp.evaluate('curPreset') == slots[0] and not cdp.evaluate('S.pendName'), 'the first of them is not the one that plays')
    # with a footswitch in the middle: the first is there, the second is not saved over
    saved = cdp.evaluate('__pedal.sent.filter(c => c.startsWith("PSAVE")).length')
    cdp.evaluate('(() => { let saves = 0; __pedal.hook = line => { if (line.startsWith("PSAVE")) saves++; '
                 f'if (saves === 1 && line.startsWith("FXA")) {{ __pedal.hook = null; __pedal.press({others[0]}); }} }}; }})()')
    said = run()
    require(cdp.evaluate('__pedal.hook === null'), 'the footswitch was not pressed')
    require(any('1 of' in x and 'another preset was chosen' in x for x in said), f'a footswitch in the middle: {said}')
    require(cdp.evaluate(f'{state}({json.dumps(slots)})') == want and cdp.evaluate(f'{state}({json.dumps(others)})') == before, 'a preset was saved over by mistake')
    require(cdp.evaluate('__pedal.sent.filter(c => c.startsWith("PSAVE")).length') == saved + 1, 'a preset was saved after the footswitch')
    return out


def same_volume(page, output):
    """The same volume for scenes and presets: the guitar that is recorded, what is measured, the gains that are shown, corrected and written, and nothing else; the
    single scene, whose gain is a change like any other; what stops it, from the page and from the pedal, and what cannot be measured."""
    cdp, quiet = page.cdp, 'S.connected && !refreshing && !txn && !saveRun && !pioBusy && !hrSaving && !Pedal.busy'
    text = '(document.querySelector("dialog.hrvol")?.innerText || "").replace(/\\s+/g, " ")'
    out, limiter = {}, cdp.evaluate('JSON.stringify(__pedal.globals.lim)')
    cdp.evaluate('__pedal.globals.lim = {on: 0, thr: -3, rel: 100}')          # without the limiter what is too loud clips

    def press(label):
        page.wait(f'!!([...document.querySelectorAll("dialog.hrvol button")].find(e => !e.disabled && e.innerText.trim() === {json.dumps(label)}))', f'the button {label}', 15)
        cdp.evaluate(f'[...document.querySelectorAll("dialog.hrvol button")].find(e => e.innerText.trim() === {json.dumps(label)}).click()')

    def opened():
        page.wait(quiet, 'a quiet page', 30)
        cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
        cdp.evaluate('document.getElementById("hrVolume").click()')
        page.wait('document.querySelector("dialog.hrvol")?.open === true', 'the window', 10)

    def pick(value):
        cdp.evaluate(f'document.querySelector("dialog.hrvol input[value={value}]").click()')

    def choose(scene):
        cdp.evaluate(f'window.__snapped = false; void Pedal.cmd("SNAP {scene}", "SNAP ").then(() => {{ window.__snapped = true; }})')
        page.wait('window.__snapped && ' + quiet, 'a scene', 20)

    def sent(since, *words):
        return [c for c in cdp.evaluate('__pedal.sent')[since:] if c.startswith(words)]

    # three presets: one with three scenes that starts with its second, one whose start is none of its scenes, one without scenes
    slots = sorted(int(k) for k in cdp.evaluate('Object.keys(__pedal.store)'))[:3]
    require(len(slots) == 3, f'the presets: {slots}')
    a, b, c = slots
    cdp.evaluate(f'''(() => {{ const s = __pedal.store, put = (n, o) => Object.assign(s[n], JSON.parse(JSON.stringify(o)));
        put({a}, {{scenes: "11100000", scene: 1, gain: [0, 0], outs: {{0: 4, 1: 0, 2: -6}}}});
        put({b}, {{scenes: "10000000", scene: 0, gain: [0, 2], outs: {{0: -3}}}});
        put({c}, {{scenes: "00000000", scene: -1, gain: [0, 0], outs: {{}}}});
        __pedal.loud = {{"{a},start": -18, "{a},0": -24, "{a},1": -18, "{a},2": -13, "{b},start": -22, "{b},0": -16, "{c},start": -30}};
        __pedal.peaks = {{"{a},0": -5, "{a},1": -9, "{a},2": -10}}; void loadPreset({a}); }})()''')
    page.wait(f'curPreset === {a} && S.snaps.filter(Boolean).length === 3 && ' + quiet, 'a preset with three scenes', 20)
    # the rest of the presets are put aside: not to be measured here
    cdp.evaluate(f'''(() => {{ window.__aside = [{{}}, {{}}]; for (const k of Object.keys(__pedal.store)) if (![{a}, {b}, {c}].includes(+k)) {{ __aside[0][k] = __pedal.store[k]; __aside[1][k] = __pedal.presets[k]; delete __pedal.store[k]; delete __pedal.presets[k]; }}
        void loadPresets().then(() => {{ window.__put = true; }}); }})()''')
    page.wait('window.__put === true && plist.length === 3 && ' + quiet, 'three presets', 15)
    cdp.evaluate('localStorage.removeItem("hyperrig.loudness"); window.__said = []; if (!window.__toast) { window.__toast = toast; toast = (m, ...more) => { __said.push(String(m)); return __toast(m, ...more); }; }')
    # the window: nothing is sent before the guitar is known
    opened()
    out['window'] = cdp.evaluate(text)
    require(cdp.evaluate('document.getElementById("hrVolGo").disabled') and 'listens to your guitar once' in out['window'], f"the window: {out['window']}")
    cdp.screenshot(output / 'same-volume.png')
    # a guitar that is hardly heard, then one with too few strokes, then the guitar
    for hertz, count, loud, said in ((110, 8, 0.0004, 'hardly heard'), (110, 2, 0.2, 'Only 2 strokes were heard'), (110, 12, 0.2, 'Recorded on')):
        cdp.evaluate(f'''(() => {{ const L = HyperRigLoudness, x = new Float32Array(Math.round(14.5 * L.LOW)); let seed = 5; const random = () => (seed = seed * 16807 % 2147483647) / 2147483647;
            for (let n = 0; n < {count}; n++) for (let i = 0, at = Math.round((0.4 + n * 1.1) * L.LOW); i < 0.9 * L.LOW && at + i < x.length; i++) x[at + i] += {loud} * (0.4 + 0.05 * n) * (Math.exp(-3 * i / L.LOW) * (Math.sin(2 * Math.PI * {hertz} * i / L.LOW) +
              0.6 * Math.sin(4 * Math.PI * {hertz} * i / L.LOW)) + Math.exp(-i / 40) * (random() - .5));
            __pedal.guitar = L.hexOf(L.encode(x)); __pedal.played = 0; __pedal.busy = {1 if count > 10 else 0}; }})()''')
        press('Record my guitar')
        page.wait('/Play now/.test(' + text + ')', 'the recording', 10)
        page.wait('!/Play now/.test(' + text + ')', 'the end of the recording', 40)
        require(said in cdp.evaluate(text), f'the guitar: {cdp.evaluate(text)}')
    guitar = cdp.evaluate('JSON.parse(localStorage.getItem("hyperrig.loudness")).guitar')
    require(len(guitar['strokes']) == 3 and all(len(s) == 5632 for s in guitar['strokes']) and guitar['heard'] >= 9, f"what is kept of the guitar: {guitar['heard']}, {[len(s) for s in guitar['strokes']]}")
    require(cdp.evaluate('__pedal.level === null && __pedal.rec === null && __pedal.busy === 0') and cdp.evaluate('__pedal.current') == a, 'the recording did not end')
    require(cdp.evaluate('__pedal.sent.filter(c => c === "HRLV 05").length') == 4, 'a recording that went too fast was not begun anew')
    out['guitar'] = [guitar['heard'], round(guitar['level'], 1)]
    # all presets
    before = cdp.evaluate('JSON.stringify(__pedal.store)')
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('__pedal.lose = [88]')                         # a byte of a piece is lost on the way, once
    pick('all')
    press('Measure')
    page.wait('/Measuring/.test(' + text + ')', 'the measure', 10)
    time.sleep(1.5)
    cdp.screenshot(output / 'same-volume-measuring.png')
    page.wait('!!document.getElementById("hrVolSave")', 'the result', 120)
    require(cdp.evaluate('JSON.stringify(__pedal.store)') == before, 'measuring changed a preset')
    require(cdp.evaluate('[__pedal.current, __pedal.scene, __pedal.level === null]') == [a, 1, True], 'what played did not come back')
    wrote = [x for x in sent(n, 'GAIN', 'SNAPSAVE', 'PSAVE', 'HRLV 02', 'GSAVE', 'FXP', 'FXE') if x != 'GAIN']
    require(not wrote, f'measuring wrote {wrote}')
    pieces = sent(n, 'INJB ')
    require(cdp.evaluate('__pedal.strokes') == 3 and pieces[1] == pieces[2] and len(pieces) == 3 * 32 + 1 and cdp.evaluate('__pedal.inj === null'), f'the pieces: {len(pieces)}')
    rows = '[...document.querySelectorAll("#hrVolList .vitem")].map(e => [e.dataset.item, e.querySelector(".vname").textContent, e.querySelector(".vgain")?.textContent.replace(/\\u2212/g, "-"), e.querySelector(".vwhy").textContent])'
    out['rows'] = cdp.evaluate(rows)
    out['all'] = cdp.evaluate('document.getElementById("hrVolAll").textContent')
    # what they have now is -20, -18, -19, -20, -19 and -30: the middle of it, and less than the first may have before the limiter
    volume = int(out['all'].replace('−', '-').split()[0])
    loud = {f'{a},0': (-24, 4), f'{a},1': (-18, 0), f'{a},2': (-13, -6), f'{b},-1': (-22, 2), f'{b},0': (-16, -3), f'{c},-1': (-30, 0)}
    require([r[0] for r in out['rows']] == list(loud), f"what was measured: {out['rows']}")
    want = {k: max(-30, min(12, round(volume - level))) for k, (level, gain) in loud.items()}
    sign = lambda v: f'{v:+d}' if v else '0'
    require(all(r[2] == f'{sign(loud[r[0]][1])} → {sign(want[r[0]])} dB' for r in out['rows']), f"the gains: {out['rows']} for {volume}")
    require([r[1].split(' · ')[0] for r in out['rows']] == ['Scene 1', 'Scene 2', 'Scene 3', 'As it starts', 'Scene 1', 'Preset'], f"the names: {out['rows']}")
    # louder for all: what would clip is said (this pedal has no limiter), and where a gain ends; and back; one by hand
    for _ in range(3):
        cdp.evaluate('document.getElementById("hrVolMore").click()')
    louder = cdp.evaluate(rows)
    require(any('clip' in r[3] for r in louder) and any('gain ends' in r[3] for r in louder), f'louder: {louder}')
    for _ in range(3):
        cdp.evaluate('document.getElementById("hrVolLess").click()')
    require(cdp.evaluate(rows) == out['rows'], 'louder and softer is not what it was')
    cdp.evaluate(f'document.querySelector("#hrVolList [data-item=\'{a},2\'] .vstep:last-of-type").click()')
    want[f'{a},2'] += 1
    cdp.screenshot(output / 'same-volume-result.png')
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('document.getElementById("hrVolSave").click()')
    page.wait('!document.querySelector("dialog.hrvol") && ' + quiet, 'the gains saved', 30)
    field = lambda p, *keys: 'HRLV 02' + bytes([p] + [want[f'{p},{k}'] & 255 if want[f'{p},{k}'] != loud[f'{p},{k}'][1] else 127 for k in keys] + [127] * (9 - len(keys))).hex()
    sets = sent(n, 'HRLV 02')
    expected = [field(a, 1, 0, 1, 2), field(b, -1, 0), field(c, -1)]
    require(sets == expected, f'what was written: {sets}, not {expected}')
    after, old = json.loads(cdp.evaluate('JSON.stringify(__pedal.store)')), json.loads(before)
    for k in after:
        for s in (after[k], old[k]):
            s.pop('outs'), s.pop('gain')
    require(after == old, 'something else of a preset was changed')
    require(cdp.evaluate(f'[__pedal.store[{a}].gain[1], __pedal.store[{a}].outs, __pedal.store[{b}].gain[1], __pedal.store[{b}].outs, __pedal.store[{c}].gain[1]]') ==
            [want[f'{a},1'], {'0': want[f'{a},0'], '1': want[f'{a},1'], '2': want[f'{a},2']}, want[f'{b},-1'], {'0': want[f'{b},0']}, want[f'{c},-1']], 'the gains that are stored')
    require(cdp.evaluate('[__pedal.current, __pedal.scene, __pedal.gain[1], S.gain[1]]') == [a, 1, want[f'{a},1'], want[f'{a},1']] and cdp.evaluate('edCount()') == 0, 'what plays has not its new gain')
    out['said'] = cdp.evaluate('__said')
    require(any('3 presets have their new volume' in x for x in out['said']), f"what is said: {out['said']}")
    # this preset, stopped from the page; then a footswitch; then a pedal that does not answer any more: nothing is changed, and what played is back
    stored = cdp.evaluate('JSON.stringify(__pedal.store)')
    for how, act, said in (('another preset', f'__pedal.load({b})', 'Another preset or scene was chosen on the pedal.'), ('Stop', None, 'Stopped. Nothing was changed.'), ('footswitch', '__pedal.stopLevel()', 'It was stopped from the pedal.'), ('silence', '__pedal.hook = line => { if (line.startsWith("RECD")) throw new Error("silent"); }', 'did not answer')):
        opened()
        pick('preset')
        press('Measure')
        page.wait('__pedal.rec && __pedal.rec.mode === 6', how, 30)
        time.sleep(0.5)
        cdp.evaluate(act) if act else press('Stop')
        page.wait('!/Measuring/.test(' + text + ')', f'the end after {how}', 30)
        cdp.evaluate('__pedal.hook = null')
        page.wait('__pedal.level === null && __pedal.rec === null && __pedal.inj === null', f'the pedal after {how}', 15)
        require(said in cdp.evaluate(text), f'{how}: {cdp.evaluate(text)}')
        require(cdp.evaluate('[__pedal.current, __pedal.scene]') == [a, 1] and cdp.evaluate('JSON.stringify(__pedal.store)') == stored, f'{how}: something was changed')
        press('Cancel')
        page.wait('!document.querySelector("dialog.hrvol") && ' + quiet, f'the window closed after {how}', 30)
    cdp.evaluate('__errors.splice(0)')                          # the answer that was held back on purpose
    # a preset that starts with another sound than its scene: the one that played comes back, be it the scene or the start
    gains = []
    for scene in (None, 0):
        cdp.evaluate(f'void loadPreset({b})')
        page.wait(f'curPreset === {b} && ' + quiet, 'the preset with another start', 20)
        if scene is not None:
            choose(scene)
        playing = cdp.evaluate('[__pedal.current, __pedal.scene, __pedal.at, __pedal.gain[1]]')
        gains.append(playing[3])
        opened()
        pick('preset')
        press('Measure')
        page.wait('!!document.getElementById("hrVolSave")', 'the preset measured', 60)
        require(cdp.evaluate('[__pedal.current, __pedal.scene, __pedal.at, __pedal.gain[1]]') == playing == [b, 0, 'start' if scene is None else scene, playing[3]], f'what played did not come back: {playing}')
        press('Cancel')
        page.wait('!document.querySelector("dialog.hrvol") && ' + quiet, 'the window closed', 30)
    require(gains[0] != gains[1], f'the start and the scene are the same: {gains}')
    cdp.evaluate(f'void loadPreset({a})')
    page.wait(f'curPreset === {a} && ' + quiet, 'the first preset again', 20)
    choose(1)
    # with a change that is not saved only the scene can be measured; its gain is a change, too
    cdp.evaluate('void toggle(fsBlks()[0].id)')
    page.wait('edCount() > 0 && ' + quiet, 'a change', 15)
    opened()
    require(cdp.evaluate('[...document.querySelectorAll("dialog.hrvol input[type=radio]")].map(e => [e.value, e.disabled])') == [['scene', False], ['preset', True], ['all', True]], 'a change that is not saved')
    n = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate(f'__pedal.loud["{a},1"] = -11; __pedal.unsettled = "{a},1"; __pedal.echo = 2')
    press('Measure')
    page.wait('!!document.getElementById("hrVolSave")', 'the scene', 60)
    require(not sent(n, 'PLOAD', 'SNAP '), 'a scene alone loaded something')
    runs = sent(n, 'HRLV 06')
    require(runs == ['HRLV 06b002406c'] * 3 + ['HRLV 06b0034098'] + ['HRLV 06b002406c', 'HRLV 06b0034098'] * 2, f'a sound with echoes of another, or that was not settled, was not played again: {runs}')
    require(cdp.evaluate('document.getElementById("hrVolAll").textContent') == out['all'], 'the volume of the last time is not offered')
    cdp.evaluate('__pedal.unsettled = null; document.getElementById("hrVolSave").click()')
    page.wait('!document.querySelector("dialog.hrvol") && ' + quiet, 'the gain set', 20)
    require(cdp.evaluate('__pedal.gain[1]') == round(volume + 11) and cdp.evaluate('S.gain[1]') == round(volume + 11) and cdp.evaluate('edCount()') > 0 and not sent(n, 'HRLV 02', 'SNAPSAVE', 'PSAVE'), 'the gain of a scene')
    cdp.evaluate('document.getElementById("saveDiscard").click()')
    page.wait('/Discard changes/i.test(document.querySelector(".mdlg")?.innerText || "")', 'the question', 10)
    cdp.evaluate('document.querySelector(".mdlg .mdlg-ok").click()')
    page.wait('edCount() === 0 && ' + quiet, 'the change discarded', 20)
    # what cannot be measured is said, and the rest goes on; a pedal without memory says why
    opened()
    cdp.evaluate('const s = document.querySelector("dialog.hrvol select"); s.value = "medium"; s.dispatchEvent(new Event("change"))')
    pick('preset')
    cdp.evaluate(f'__pedal.late = "{a},2"; __pedal.loud["{a},1"] = -18; void 0')
    press('Measure')
    page.wait('!!document.getElementById("hrVolSave")', 'the preset with built-in strokes', 90)
    out['late'] = [r for r in cdp.evaluate(rows) if 'no time' in r[3]]
    require(len(out['late']) == 1, f'what could not be measured: {cdp.evaluate(rows)}')
    cdp.evaluate('__pedal.late = null')
    press('Cancel')
    page.wait('!document.querySelector("dialog.hrvol") && ' + quiet, 'the window closed', 20)
    for why, back, said in (('full = true', 'full = false', 'no free memory'), ('bypass = 1', 'bypass = 0', 'in bypass'), ('engine = 0', 'engine = 2', 'engine is not running')):
        opened()
        cdp.evaluate(f'__pedal.{why}')
        press('Measure')
        page.wait('/' + said + '/.test(' + text + ')', why, 20)
        cdp.evaluate(f'__pedal.{back}')
        press('Cancel')
        require(cdp.evaluate('__pedal.level === null'), f'{why}: it was not ended')
    # the window from the gain, and its size
    cdp.evaluate('document.getElementById("hrVolGain").click()')
    page.wait('document.querySelector("dialog.hrvol")?.open === true', 'the window from the gain', 10)
    sizes = cdp.evaluate('[...document.querySelectorAll("dialog.hrvol button, dialog.hrvol select")].map(e => [e.innerText.slice(0, 20), Math.round(e.getBoundingClientRect().height)])')
    require(all(38 <= h <= 46 for _, h in sizes), f'controls of another size: {sizes}')
    press('Cancel')
    cdp.evaluate('''(() => { Object.assign(__pedal.store, __aside[0]); Object.assign(__pedal.presets, __aside[1]); void loadPresets(); })()''')
    page.wait(quiet, 'a quiet page', 20)
    cdp.evaluate(f'__pedal.globals.lim = {limiter}')
    return out


class Page:
    def __init__(self, bundle, output, identity=None):
        self.profile = output / ('isolated-profile-' + str(len(list(output.glob('isolated-profile-*')))))
        web = Path(bundle).resolve() / 'editor/web'

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.rfile.read(int(self.headers.get('Content-Length', '0')))
                self.send_response(204)
                self.end_headers()

        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(web)))
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.process = subprocess.Popen(
            [str(browser.browser_path()), '--headless=new', '--no-first-run', '--no-default-browser-check',
             '--disable-background-networking', '--disable-sync', '--disable-extensions', '--disable-component-update',
             '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0', '--window-size=1440,1000',
             '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
             '--user-data-dir=' + str(self.profile), 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        endpoint = self.profile / 'DevToolsActivePort'
        for _ in range(150):
            try:
                if endpoint.is_file() and endpoint.read_text().strip():
                    break
            except PermissionError:         # the browser is writing it
                pass
            require(self.process.poll() is None, 'The browser exited')
            time.sleep(0.1)
        port = int(endpoint.read_text().splitlines()[0])
        with urlopen(f'http://127.0.0.1:{port}/json/list', timeout=5) as response:
            page = next(p for p in json.load(response) if p['type'] == 'page')
        self.cdp = browser.CDP(page['webSocketDebuggerUrl'])
        for domain in ('Page', 'Runtime'):
            self.cdp.call(domain + '.enable')
        self.cdp.call('Page.addScriptToEvaluateOnNewDocument',
                      {'source': pedal_source(identity)})
        self.cdp.call('Page.navigate', {'url': f'http://127.0.0.1:{self.server.server_port}/{editor.PAGE_FILE}'})

    def wait(self, expression, what, seconds=20):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.cdp.evaluate(expression):
                return
            time.sleep(0.1)
        raise ValueError(f'timeout: {what}')

    def close(self):
        try:
            self.cdp.call('Browser.close')
        except Exception:
            pass
        try:
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.server.shutdown()
        self.server.server_close()


CHANGES = ['GAIN 0 0', 'PLOAD 0', 'PSAVE 0 X', 'SNAPSAVE 0', 'FXA Q 99 gate', 'FXP 0 0 1', 'FXE 0 1', 'FXR 0', 'SNAP 0', 'BPM 1200',
           'TUNER 1 1 440', 'AMP 0', 'AMPEQ 1 600', 'STW 100', 'PNEW', 'PDEL 0', 'FSMODE mode=live', 'FSDO a', 'GSAVE', 'KNOB off',
           'IRBEGIN 4 0 48', 'ISAVE 0 X', 'ILOAD 0', 'IDEL 0', 'LDBEGIN 4', 'CSAVE 0 X', 'CLOAD 0', 'CDEL 0', 'CTRIM live 0', 'AUDIO OFF',
           'GEQ 0 3', 'HPF 80', 'LIM 1 -3 100', 'SPILL 0', 'GLIDE 42 0', 'SPUR 0', 'CALIB start']


def only_reads(page, picture, newer=False):
    """Connect to a pedal with another build: the page says so in plain words, reads, and sends nothing that changes it."""
    cdp = page.cdp
    page.wait('window.__urOk === true && !!document.getElementById("miniPortStatus")', 'the page')
    cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
    cdp.evaluate('void connect()')
    page.wait('/HyperRig/.test(document.querySelector(".mdlg")?.innerText || "")', 'the notice', 60)
    notice = cdp.evaluate('(() => { const t = document.querySelector(".mdlg"); return {text: t.innerText, buttons: [...t.querySelectorAll("button")].map(b => b.textContent)}; })()')
    require(not re.search(r'[0-9a-f]{16}|HRID|dev[.]|[0-9]+[.][0-9]+', notice['text']), f'the notice has codes in it: {notice}')
    require(('ahead of this program' if newer else 'update') in notice['text'].lower(), f'the notice: {notice}')
    page.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
    page.wait('!!document.getElementById("hrOther") && !document.getElementById("hrOther").hidden', 'the bar', 5)
    cdp.screenshot(picture)
    cdp.evaluate('(document.querySelector(".mdlg-cancel") || document.querySelector(".mdlg-ok")).click()')
    time.sleep(1.5)
    require(not cdp.evaluate('!!document.querySelector(".mdlg")'), 'the notice does not go away')
    bar = cdp.evaluate('document.getElementById("hrOther").innerText')
    require(('newer HyperRig' if newer else 'needs an update') in bar and 'not change anything' in bar, f'the bar of another build: {bar!r}')
    cdp.evaluate('toast("Parameter: ERR MINI_APP command is outside the current FXT/FXS/PLIST/SNAPS data", "err")')
    page.wait('[...document.querySelectorAll("#toasts > *")].some(e => /Not changed/.test(e.innerText) && !/MINI_APP/.test(e.innerText))', 'the refusal in plain words', 10)
    refused = cdp.evaluate('(async () => { const out = {}; for (const c of ' + json.dumps(CHANGES) + ') '
                           'out[c] = (await Pedal.cmd(c, c.split(" ")[0])).join(" "); return out; })()')
    require(all(v.startswith('ERR MINI_APP') for v in refused.values()), f'a change was sent to another build: {refused}')
    sent = cdp.evaluate('__pedal.sent')
    require('HRID' in sent and 'FXT' in sent and 'PLIST' in sent, 'the page did not read')
    require(not [c for c in sent if c in CHANGES], 'a change was sent to another build')
    return {'refused': len(refused), 'sent': len(sent), 'notice': notice, 'bar': bar}


# A .wav as a person has one: 16 bits, 44.1 kHz, two channels, longer than a slot.
WAV = '''(() => { const n = 9000, b = new DataView(new ArrayBuffer(44 + 4 * n)), s = (o, t) => [...t].forEach((c, i) => b.setUint8(o + i, c.charCodeAt(0)));
  s(0, "RIFF"); b.setUint32(4, 36 + 4 * n, true); s(8, "WAVEfmt "); b.setUint32(16, 16, true); b.setUint16(20, 1, true); b.setUint16(22, 2, true);
  b.setUint32(24, 44100, true); b.setUint32(28, 176400, true); b.setUint16(32, 4, true); b.setUint16(34, 16, true); s(36, "data"); b.setUint32(40, 4 * n, true);
  let seed = 1; for (let i = 0; i < n; i++) { seed = seed * 16807 % 2147483647; const v = Math.round((seed / 2147483647 - .5) * 50000 * Math.exp(-i / 900));
    b.setInt16(44 + 4 * i, v, true); b.setInt16(46 + 4 * i, v, true); } return new File([b.buffer], "__NAME__.wav", {type: "audio/wav"}); })()'''
TOASTS = '[...document.querySelectorAll(".toast, .toasts > *, #toasts > *")]'


def cab_irs(page, quiet, output):
    '''The library of cab IRs as a person uses it: no IR yet, an upload, a block, the block's own IR, read back, delete.'''
    cdp = page.cdp
    page.wait(quiet, 'a quiet page')
    blocks = cdp.evaluate('__pedal.chain.Q.length')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('void addFx("ir", {t: "serial", si: 2})')
    page.wait(TOASTS + '.some(e => /Pick a cab IR/.test(e.innerText))', 'the library asked for')
    page.wait(quiet, 'a quiet page')
    cdp.evaluate('__pedal.lose = [900, 1620]')          # bytes lost on the way, as on the pedal
    cdp.evaluate('void uploadIrs([' + WAV.replace('__NAME__', 'My cáb · V30') + '], null)')
    page.wait('!!__pedal.irs[0] && capJobs === null && ' + quiet, 'the upload', 60)
    again = cdp.evaluate('[900, 1620].map(at => __pedal.sent.filter(c => c.startsWith("IRB " + at + " ")).length)')
    require(again == [2, 2], f'a piece that came back short is not sent again: {again}')
    out = cdp.evaluate('({name: __pedal.irs[0].name, samples: __pedal.irs[0].n, gain: __pedal.irs[0].gain, pieces: __pedal.sent.filter(c => /^IRB /.test(c)).length, '
                       'longest: Math.max(...__pedal.sent.map(c => new TextEncoder().encode(c).length))})')
    require(out['name'] == 'My cab V30' and 3000 < out['samples'] <= 4076 and out['longest'] <= 190, f'the upload: {out}')
    page.wait(f'__pedal.chain.Q.length === {blocks + 1} && __pedal.chain.Q.some(x => x.type === "ir")', 'the block that was waiting for it', 30)
    # a place that always loses: told with what the pedal said, and nothing is kept
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('__pedal.loseAlways = 1800; void uploadIrs([' + WAV.replace('__NAME__', 'Lossy') + '], 3)')
    page.wait(TOASTS + '.some(e => /0 of 1 saved/.test(e.innerText))', 'the lost upload is told', 60)
    require(not cdp.evaluate('!!__pedal.irs[3]'), 'an IR that was not whole was kept')
    cdp.evaluate('__pedal.loseAlways = -1')
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    page.wait(quiet, 'a quiet page')
    close = 'if (document.getElementById("lib").classList.contains("on")) closeLib()'
    cdp.evaluate(close)
    cdp.evaluate('void uploadIrs([' + WAV.replace('__NAME__', 'Second') + '], 5)')
    page.wait('!!__pedal.irs[5] && capJobs === null && ' + quiet, 'a second one, in a chosen slot', 60)
    cdp.evaluate(close)
    cdp.evaluate('void setBlockIr(__pedal.chain.Q.find(x => x.type === "ir").id, 0, "My cab V30")')
    page.wait('__pedal.chain.Q.find(x => x.type === "ir").p[2] === 1 && ' + quiet, "the block's own IR")
    cdp.evaluate('void useSlot(false, 0, "My cab V30")')
    page.wait('__pedal.ir_slot === 0 && ' + quiet, 'an IR chosen from the list')
    out['read_back'] = cdp.evaluate('pioSlotRead(async (line, pre, tmo) => await Pedal.cmd(line, pre, tmo), "ir", 5).then(r => [r.head.name, r.data.length, '
                                    'r.data.every((b, i) => b === __pedal.irs[5].data[i])])')
    require(out['read_back'][0] == 'Second' and out['read_back'][2] is True, f"read back: {out['read_back']}")
    out['deleted'] = cdp.evaluate('Pedal.cmd("IDEL 5", "IDEL")')
    require(out['deleted'] == ['IDEL ok 5'] and cdp.evaluate('Object.keys(__pedal.irs).join()') == '0', f"delete: {out['deleted']}")
    cdp.evaluate('void openLib("ir")')
    page.wait('document.getElementById("lib").classList.contains("on")', 'the library')
    time.sleep(1.0)
    out['picture'] = cdp.screenshot(output / 'cab-irs.png')['path']
    cdp.evaluate(close)
    out['toasts'] = cdp.evaluate(TOASTS + '.map(e => e.innerText.trim()).filter(Boolean)')
    require(not [t for t in out['toasts'] if 'failed' in t or 'Couldn' in t], f"a message says it failed: {out['toasts']}")
    return out


CONTROLS = '''(() => { const out = []; for (const e of document.querySelectorAll("button, select, input[type=text], input[type=number], input:not([type])")) {
  const r = e.getBoundingClientRect(); if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) continue;
  let gone = false; for (let p = e; p; p = p.parentElement) { const s = getComputedStyle(p); if (s.display === "none" || s.visibility === "hidden") gone = true; } if (gone) continue;
  const f = parseFloat(getComputedStyle(e).fontSize), name = e.tagName.toLowerCase() + (e.id ? "#" + e.id : "") + (typeof e.className === "string" && e.className ? "." + e.className.trim().split(/\\s+/).join(".") : "");
  out.push([name, Math.round(r.width), Math.round(r.height), f, (e.innerText || "").trim().slice(0, 20)]); } return out; })()'''
# What is not a control of the two sizes: pedals on the board and tiles of the stage, chips that show the load, the + of the chain, colours.
OWN_SIZE = re.compile(r'\.(?:rchipb|add|mergebtn|sttile|seg|blk|amp|swatch|sw)\b|#(?:tap|meters)\b')


def controls(page, quiet, output):
    '''Every button, list and field of every view has one of two sizes, and text that can be read.'''
    cdp = page.cdp
    cdp.call('Emulation.setDeviceMetricsOverride', {'width': 1360, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})
    if cdp.evaluate('location.protocol === "hyperrig:"'):
        cdp.evaluate('fetch("zoom?by=auto", {method: "POST"})')
    seen, wrong = {}, []

    def view(name):
        time.sleep(0.7)
        rows = cdp.evaluate(CONTROLS)
        seen[name] = len(rows)
        for control, width, height, font, text in rows:
            if OWN_SIZE.search(control):
                continue
            if not 38 <= height <= 46 or width < 38 or font < 13:
                wrong.append([name, control[:60], width, height, font, text])
        cdp.screenshot(output / f'view-{name}.png')
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    view('board')
    cdp.click('[data-id="amp"]')
    view('amp')
    cdp.evaluate('document.querySelector("#chain .blk")?.click()')
    view('block')
    for kind in ('cap', 'ir'):
        cdp.evaluate(f'void openLib("{kind}")')
        page.wait('document.getElementById("lib").classList.contains("on")', 'the library')
        view('library-' + kind)
        cdp.evaluate('closeLib()')
        page.wait('!document.getElementById("lib").classList.contains("on")', 'the library closed')
    for name, opened, closed in (
            ('settings', 'document.getElementById("setBtn").click()', 'document.getElementById("setX").click()'),
            ('calibrate', 'void openCalib(S.capSlot)', 'void closeCalib()'),
            ('tuner', 'document.getElementById("tunerBtn").click()', 'document.getElementById("tuClose").click()'),
            ('footswitches', 'void fsOpen()', 'fsClose()'),
            ('lights', 'void fsOpen(); setTimeout(() => document.getElementById("fsAdvBtn").click(), 300)', 'fsClose()'),
            ('add', 'document.querySelector("#chain .add").click()', 'document.dispatchEvent(new KeyboardEvent("keydown", {key: "Escape", bubbles: true}))')):
        cdp.evaluate(opened)
        view(name)
        cdp.evaluate(closed)
        time.sleep(0.5)
    require(not wrong, 'controls of another size: ' + json.dumps(wrong[:12]))
    cdp.call('Emulation.clearDeviceMetricsOverride')
    return {'views': seen, 'own_size': OWN_SIZE.pattern}


# A NAM A2-Lite capture of the right shape with made-up weights, as a file a person downloads.
NAM = '''(() => { const k = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3], d = [1, 2, 4, 8, 16, 32, 64, 128, 1, 2]; let seed = 7; const C = 3, hk = 16;
  let n = C; for (const x of k) n += C * C * x + C + C + C * C + C; n += C * hk + 1 + 1;
  const weights = Array.from({length: n}, () => { seed = seed * 16807 % 2147483647; return (seed / 2147483647 - .5) * .3; });
  const model = {version: "0.7.0", architecture: "WaveNet", sample_rate: 48000, metadata: {name: "__NAME__", input_level_dbu: 12.5}, config: {head: null, head_scale: .5, layers: [{
    input_size: 1, condition_size: 1, channels: C, kernel_sizes: k, dilations: d, activation: {type: "LeakyReLU", negative_slope: .01},
    layer1x1: {active: true, groups: 1}, head: {out_channels: 1, kernel_size: hk, bias: true}}]}, weights};
  return new File([JSON.stringify(model)], "__NAME__.nam", {type: "application/json"}); })()'''


# A capture that keeps two knobs: a network of the published form (HyperA2) with made-up weights, as a file a person downloads.
NAM_KNOBS = '''(() => { const K = [...Array(14).fill(6), 15, 15, ...Array(7).fill(6)], D = [1, 3, 7, 17, 41, 101, 239, 1, 3, 7, 17, 41, 101, 239, 1, 13, 1, 3, 7, 17, 41, 101, 239]; let seed = 11;
  const g = (n, s) => Array.from({length: n}, () => { seed = seed * 16807 % 2147483647; return (seed / 2147483647 - .5) * 2 * s; }), base = g(3, 1), map = [{name: "rech", mode: "full", numel: 3, export_offset: 0}];
  K.forEach((k, i) => { const o = base.length; base.push(...g(9 * k, .25), ...g(3, .1), ...g(3, .3), ...g(9, .3), ...g(3, .05));
    map.push({name: "cb", mode: "full", numel: 3, export_offset: o + 9 * k}, {name: "mix", mode: "full", numel: 3, export_offset: o + 9 * k + 3},
      {name: "l1", mode: "low_rank", numel: 9, export_offset: o + 9 * k + 6, rank: 2, out_features: 3, rest_features: 3}, {name: "lb", mode: "full", numel: 3, export_offset: o + 9 * k + 15}); });
  const h = base.length; base.push(...g(48, .3), .01, .05); map.push({name: "head", mode: "full", numel: 48, export_offset: h}, {name: "hb", mode: "full", numel: 1, export_offset: h + 48});
  const outs = map.reduce((n, t) => n + (t.mode === "full" ? t.numel : 12), 0), state = [...g(32, .6), ...g(16, .5), ...g(outs * 16, .04), ...g(outs, .03), ...g(outs, .03)];
  const params = [{name: "Gain", min: 0, max: 10, default: 5, type: "continuous"}, {name: "Tone", min: 0, max: 10, default: 5, type: "continuous"}];
  const sub = {head: null, head_scale: .05, params, hypernet: {hidden_sizes: [16], activation: "LeakyReLU", mode: "low_rank", rank: 2, delta_map: map}, layers: [{
    input_size: 1, condition_size: 1, channels: 3, kernel_sizes: K, dilations: D, activation: {type: "LeakyReLU", negative_slope: .01}, layer1x1: {active: true, groups: 1}, head: {out_channels: 1, kernel_size: 16, bias: true}}]};
  const weights = [...base, ...state], model = {version: "1.0.0", architecture: "HyperA2", sample_rate: 48000, metadata: {name: "Two Knobs"}, weights,
    config: {params, size: "full", submodels: [{name: "lite", max_value: .5, architecture: "HyperWaveNet", config: sub, weight_offset: 0, weight_count: weights.length, base_weight_count: base.length}]}};
  return new File([JSON.stringify(model)], "Two Knobs.nam", {type: "application/json"}); })()'''


def knobs(page, quiet, output):
    """A capture that keeps knobs: converted in the page's own worker, loaded and saved; the amp's controls have the names and numbers of its knobs, and
    a turn of one sends the control it is; a capture without knobs gives the controls back."""
    cdp = page.cdp
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('void uploadCaptures([' + NAM_KNOBS + '], 5)')
    page.wait('!!__pedal.caps[5] && capJobs === null && ' + quiet, 'the capture with knobs', 300)
    close = 'if (document.getElementById("lib").classList.contains("on")) closeLib()'
    cdp.evaluate(close)
    out = cdp.evaluate('({name: __pedal.caps[5].name, bytes: __pedal.caps[5].data.length, asked: __pedal.sent.includes("AMPK")})')
    require(out['name'] == 'Two Knobs' and 4892 < out['bytes'] <= 8152, f'the capture with knobs: {out}')
    names = '[...document.querySelectorAll("#ampEqKnobs .knob")].map(e => e.dataset.k).join()'
    page.wait('S.sel = "amp", render(true), ' + names + ' === "Gain,Bass,Mid,Tone,Presence,Volume"', 'the names of its knobs')
    values = '[...document.querySelectorAll("#ampEqKnobs .knob .v")].map(e => e.textContent).join("|")'
    out['values'] = cdp.evaluate(values)
    before = len(cdp.evaluate('__pedal.sent'))
    cdp.evaluate('(() => { const e = document.querySelector("#ampEqKnobs .knob"); e.focus(); e.dispatchEvent(new KeyboardEvent("keydown", {key: "End", bubbles: true})); })()')
    page.wait('__pedal.ampeq[5] === 120 && ' + quiet, 'the knob turned up')
    out['sent'] = [c for c in cdp.evaluate('__pedal.sent')[before:] if c.startswith('AMPEQ ')]
    out['full'] = cdp.evaluate(values)
    out['note'] = cdp.evaluate('document.querySelector("#editor .anote").textContent')
    out['picture'] = cdp.screenshot(output / 'knobs.png')['path']
    require(out['values'].split('|')[0] == '5.0' and out['full'].split('|')[0] == '10.0' and out['full'].split('|')[1].endswith('dB') and out['sent'] == ['AMPEQ 5 120'] and
            'knobs of its own: Gain, Tone.' in out['note'], f'the knobs of the capture: {out}')
    cdp.evaluate('(() => { const e = document.querySelector("#ampEqKnobs .knob"); e.dispatchEvent(new KeyboardEvent("keydown", {key: "Delete", bubbles: true})); })()')
    page.wait('__pedal.ampeq[5] === 0 && ' + quiet, 'the knob back at its usual place')
    cdp.evaluate('void useSlot(true, 9, "A2")')
    page.wait('__pedal.cap_slot === 9 && ' + quiet, 'a capture without knobs')
    page.wait(names + ' === "Gain,Bass,Mid,Treble,Presence,Volume" && /dB/.test(' + values + '.split("|")[0])', 'the controls given back')
    cdp.evaluate('Pedal.cmd("CDEL 5", "CDEL")')
    cdp.evaluate(close)
    cdp.evaluate('S.sel = null; render(true)')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    return out


def long_delay(page):
    """A delay that is too long for the memory: the longest that fits is found, kept and said once; a new turn of the knob ends the search; and what a
    footswitch pressed during an import would change is not sent."""
    cdp = page.cdp
    out = cdp.evaluate("""(async () => {
      const real = Pedal.cmd, sent = [], said = []; let limit = 1230, held = 350, turnAt = -1;
      const was = memToast;
      Pedal.cmd = async line => { const v = +line.split(" ")[3]; sent.push(line);
        await new Promise(r => setTimeout(r, 5));
        if (sent.length === turnAt) hrTimeTurned();
        if (v <= limit) { held = v; return [`FXP ok ${v}`]; }
        return [`ERR FXP out of memory; kept ${held}`]; };
      memToast = m => said.push(m);
      const ask = want => hrLongest(7, want, `ERR FXP out of memory; kept ${held}`, hrTimeTurned());
      const r = {};
      r.first = [await ask(2000), held, sent.slice(), said.slice()];
      sent.length = said.length = 0;
      r.again = [await ask(2000), sent.slice(), said.slice()];
      hrTime.last = null; sent.length = said.length = 0; turnAt = 2;
      r.stopped = [await ask(1990), sent.length, said.slice()];
      sent.length = said.length = 0; turnAt = -1;
      r.none = [await hrLongest(7, 2000, "ERR FXP out of memory", hrTimeTurned()), sent.length];
      Pedal.cmd = real; memToast = was; hrTime.last = null;
      return r; })()""")
    answer, held, sent, said = out['first']
    require(1220 <= int(answer.split()[-1]) <= 1230 and held == int(answer.split()[-1]), f'the longest delay: {out["first"]}')
    require(all(c.startswith('FXP 7 0 ') for c in sent) and len(sent) <= 9, f'the search: {sent}')
    require(len(said) == 1 and 'longest delay that fits here is 1.2' in said[0], f'what is said: {said}')
    require(out['again'][0] == answer and out['again'][1] == [] and out['again'][2] == [], f'asked again at once: {out["again"]}')
    require(out['stopped'][1] == 2 and out['stopped'][2] == [], f'a new turn of the knob: {out["stopped"]}')
    require(out['none'] == ['ERR FXP out of memory', 0], f'what the pedal does not keep: {out["none"]}')
    guard = cdp.evaluate("""(async () => { const out = [];
      for (const p of [5, -1]) for (const line of ["SNAPSAVE 0", "SNAPNAME 0 A", "PCOLOR ff0000", "FXE 0 1"]) { const sent = []; let why = "";
        const send = async x => { sent.push(x); return x === "LVL" ? [`LVL in=-240 out=-253 m=2 g=0/0 b=1200 s=0 a=1 c=5 p=${p} tu=0 lim=0`] : [x.split(" ")[0] + " ok"]; };
        try { await pioRun({cmds: [{line, pre: line.split(" ")[0]}], blocks: []}, send); } catch (e) { why = e.message; }
        out.push([p, line, sent, why]); }
      return out; })()""")
    for p, line, sent, why in guard:
        stops = p == 5 and not line.startswith('FXE')
        require(line in sent and not why if not stops else sent == ['LVL'] and 'another preset was chosen' in why, f'an import with another preset: {[p, line, sent, why]}')
    return {'longest': out, 'import_guard': len(guard)}


def button(page, text):
    """Press the button that shows this text."""
    page.wait(f'!!([...document.querySelectorAll("button")].find(e => e.offsetParent && e.innerText.trim() === {json.dumps(text)}))', f'the button {text}')
    page.cdp.evaluate(f'[...document.querySelectorAll("button")].find(e => e.offsetParent && e.innerText.trim() === {json.dumps(text)}).click()')


def midi(page, quiet, output):
    """MIDI in the settings: what the pedal says, the channels, the map and its mistakes, kept and not kept, and the port turned on, taken and not taken."""
    cdp = page.cdp
    cdp.call('Emulation.setDeviceMetricsOverride', {'width': 1360, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})
    sent = lambda since: [c for c in cdp.evaluate('__pedal.sent')[since:] if c.startswith('MIDI ') or c == 'GSAVE']
    here = lambda: len(cdp.evaluate('__pedal.sent'))
    value = lambda name: cdp.evaluate(f'document.getElementById("{name}").value')
    choose = lambda name, v: cdp.evaluate(f'(() => {{ const e = document.getElementById("{name}"); e.value = {json.dumps(v)}; e.onchange({{target: e}}); }})()')
    toast_of = lambda text: f'{TOASTS}.some(e => e.textContent.includes({json.dumps(text)}))'
    wrong_size = lambda: [r for r in cdp.evaluate(CONTROLS) if not OWN_SIZE.search(r[0]) and (not 38 <= r[2] <= 46 or r[1] < 38 or r[3] < 13)]
    kept = cdp.evaluate('__pedal.saved_settings')

    def opened():
        page.wait(quiet, 'a quiet page')
        cdp.evaluate('document.getElementById("setBtn").click()')
        page.wait('document.getElementById("settings").classList.contains("on") && !!hrMidi.is && !document.getElementById("hrMidiMap").disabled', 'the MIDI settings', 15)
        cdp.evaluate('document.getElementById("hrMidi").scrollIntoView()')

    def dialog(title):
        page.wait(f'/{title}/i.test(document.querySelector(".mdlg h2")?.textContent || "")', title, 10)

    def press(text):
        cdp.evaluate(f'[...document.querySelectorAll(".mdlg button")].find(e => e.innerText.trim().toLowerCase() === {json.dumps(text.lower())}).click()')

    out = {}
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    opened()
    out['as_it_comes'] = {'port': cdp.evaluate('document.querySelector("#hrMidi [data-hrport].on").innerText'), 'says': cdp.evaluate('document.getElementById("hrMidiSay").textContent'),
                          'in': value('hrMidiIn'), 'out': value('hrMidiOut'), 'clock': cdp.evaluate('document.getElementById("hrMidiClock").checked')}
    require(out['as_it_comes']['port'] == 'Off' and out['as_it_comes']['says'].startswith('Off.') and [out['as_it_comes'][k] for k in ('in', 'out', 'clock')] == ['all', '1', True], f"as it comes: {out['as_it_comes']}")
    time.sleep(0.6)
    cdp.screenshot(output / 'midi-settings.png')
    require(not wrong_size(), f'controls of another size: {wrong_size()}')
    # the channels, at once, and unsaved until they are kept
    n = here()
    choose('hrMidiIn', '5')
    page.wait('__pedal.midi.get(1) === 5 && !document.querySelector("#settings .gdnote").hidden && ' + quiet, 'the channel received on')
    choose('hrMidiOut', 'off')
    page.wait('__pedal.midi.get(2) === 255 && ' + quiet, 'nothing sent')
    cdp.evaluate('(() => { const e = document.getElementById("hrMidiClock"); e.checked = false; e.onchange({target: e}); })()')
    page.wait('__pedal.midi.get(0) === 0 && ' + quiet, 'the clock')
    require([c[:12] for c in sent(n)] == ['MIDI =010501', 'MIDI =0105ff', 'MIDI =0005ff'], f'the channels: {sent(n)}')
    # the map: shown with the blocks of the chain, changed, and only what is changed is sent
    n = here()
    cdp.evaluate('document.getElementById("hrMidiMap").click()')
    dialog('What the messages do')
    out['map'] = cdp.evaluate('document.querySelector(".mdlg").innerText')
    first = cdp.evaluate('lookOf([...S.chain.P, ...S.chain.Q][0].type).name')
    require(all(x in out['map'].upper() for x in ('PRESETS 1A TO 11B', 'SCENE', 'BYPASS', 'TAP TEMPO', 'VOLUME', 'BLOCKS', 'KNOBS OF BLOCKS')), f"the map: {out['map'][:600]}")
    names = cdp.evaluate('[...document.querySelector(".mdlg .hrmknobs select").options].map(o => o.text)')
    require(len(names) == 16 and names[0] == f'1 · {first}', f'the blocks of the chain by name: {names}')
    fields = '[...document.querySelectorAll(".mdlg .hrmrows input")]'
    require(cdp.evaluate(fields + '.map(e => e.value).join()') == '20,21,24,22,23,7,102', cdp.evaluate(fields + '.map(e => e.value).join()'))
    time.sleep(0.4)
    cdp.screenshot(output / 'midi-map.png')
    require(not wrong_size(), f'controls of another size in the map: {wrong_size()}')
    wide = cdp.evaluate('(() => { const b = document.querySelector(".mdlg"); return [b.scrollWidth <= b.clientWidth + 1, '
                        '[...b.querySelectorAll("input, select, small, b")].every(e => e.getBoundingClientRect().right <= b.getBoundingClientRect().right)]; })()')
    require(wide == [True, True], f'the map is cut off at the side: {wide}')
    for change, text in ((fields + '[0].value = "120"', 'Controllers are 0 to 119'), (fields + '[0].value = "21"', 'same controller'), (fields + '[0].value = "110"', 'same controller')):
        cdp.evaluate(change)
        press('Use it')
        page.wait(f'(document.querySelector(".mdlg .hrnote")?.textContent || "").includes({json.dumps(text)})', text)
    require(not sent(n), f'a mistake was sent: {sent(n)}')
    cdp.evaluate(fields + '[0].value = "30"; ' + fields + '[4].value = ""; (() => { const k = document.querySelector(".mdlg .hrmknobs"), i = k.querySelectorAll("input"), s = k.querySelectorAll("select"); '
                 'i[0].value = "11"; s[0].value = "2"; s[0].onchange(); k.querySelectorAll("select")[1].value = "3"; i[1].value = "10"; i[2].value = "90"; })()')
    press('Use it')
    page.wait('!document.querySelector(".mdlg") && __pedal.midi.get(3) === 30 && __pedal.midi.knob(0) === "11,1,2,10,90" && ' + quiet, 'the map on the pedal', 15)
    require(sent(n) == ['MIDI =0005ff1e1516ff1807660b01020a5a' + 'ff00000064' * 3], f'the map: {sent(n)}')
    # kept
    cdp.evaluate('document.getElementById("gsave").click()')
    page.wait(f'__pedal.saved_settings === {kept + 1} && document.querySelector("#settings .gdnote").hidden && ' + quiet, 'the settings kept', 15)
    # and not kept: back to what was saved
    choose('hrMidiIn', '9')
    page.wait('__pedal.midi.get(1) === 9 && ' + quiet, 'another channel')
    cdp.evaluate('document.getElementById("setX").click()')
    dialog('Save your changes')
    cdp.evaluate('[...document.querySelectorAll(".mdlg button")].find(e => /don.t save/i.test(e.innerText)).click()')
    page.wait('!document.querySelector(".mdlg") && __pedal.midi.get(1) === 5 && !document.getElementById("settings").classList.contains("on") && ' + quiet, 'back to what was saved', 20)
    require(cdp.evaluate('[__pedal.midi.get(3), __pedal.midi.get(2), __pedal.midi.knob(0)].join()') == '30,255,11,1,2,10,90', 'what was saved is another')
    # the port: asked first, then the pedal comes back with it
    opened()
    n = here()
    cdp.evaluate('document.querySelector("#hrMidi [data-hrport=on]").click()')
    dialog('Turn on MIDI over USB')
    cdp.screenshot(output / 'midi-port.png')
    press('Cancel')
    page.wait('!document.querySelector(".mdlg")', 'the question closed')
    require(not sent(n) and cdp.evaluate('__pedal.midi.port') == 0, 'the port was turned on without a yes')
    for takes, becomes, says, state in (('on', 2, 'MIDI over USB is on', 'On.'), ('refused', 3, 'MIDI is off again', 'The computer did not take it')):
        cdp.evaluate(TOASTS + f'.forEach(e => e.remove()); __pedal.midi.wanted = __pedal.midi.port = 0; __pedal.midi.takes = {becomes}; void hrMidiSay("")')
        page.wait('hrMidi.is && hrMidi.is.port === "off" && ' + quiet, 'the port off')
        n = here()
        cdp.evaluate('document.querySelector("#hrMidi [data-hrport=on]").click()')
        dialog('Turn on MIDI over USB')
        press('Turn on')
        page.wait('__pedal.sent.includes("MIDI on") && !document.querySelector(".mdlg") && ' + quiet, 'the port asked for')
        require(sent(n)[:1] == ['MIDI on'], f'the port: {sent(n)}')
        cdp.evaluate('void (async () => { await Pedal.disconnect(); onDisconnected(); await new Promise(r => setTimeout(r, 900)); await connect(); })()')      # the pedal leaves and comes back
        page.wait('S.connected && hrMidi.asked === "" && ' + quiet, 'connected again', 60)
        page.wait(toast_of(says), says, 20)
        out[takes] = cdp.evaluate(TOASTS + '.map(e => e.innerText.trim())')
        if not cdp.evaluate('document.getElementById("settings").classList.contains("on")'):
            opened()
        page.wait(f'document.getElementById("hrMidiSay").textContent.startsWith({json.dumps(state)})', state, 10)
        require(cdp.evaluate('document.querySelector("#settings .gdnote").hidden') == (takes != 'on'), 'the port that is on is not said to be unsaved, or one that is off is')
        if takes == 'on':
            n = here()
            cdp.evaluate('document.getElementById("gsave").click()')
            page.wait('document.querySelector("#settings .gdnote").hidden && ' + quiet, 'the port kept', 15)
            require('GSAVE' in sent(n), 'the port is not kept')
            cdp.evaluate('document.querySelector("#hrMidi [data-hrport=off]").click()')                     # and off again: not asked, the connection restarts as well
            page.wait('__pedal.midi.port === 0 && ' + quiet, 'the port turned off')
            cdp.evaluate('void (async () => { await Pedal.disconnect(); onDisconnected(); await new Promise(r => setTimeout(r, 900)); await connect(); })()')
            page.wait('S.connected && hrMidi.asked === "" && ' + quiet, 'connected again', 60)
            page.wait(toast_of('MIDI over USB is off'), 'said to be off', 20)
    cdp.evaluate('gdClear(); document.getElementById("setX").click()')
    page.wait('!document.getElementById("settings").classList.contains("on")', 'the settings closed')
    out['blocked'] = {c: cdp.evaluate(f'Pedal.cmd({json.dumps(c)}, "MIDI")')[0] for c in ('MIDI >c005', 'MIDI =00', 'MIDI =' + '7f' * 30, 'MIDI maybe')}
    require(all(v.startswith('ERR MINI_APP') for v in out['blocked'].values()), f"not blocked: {out['blocked']}")
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.call('Emulation.clearDeviceMetricsOverride')
    return out


def saving(page, quiet):
    """A preset whose capture is not in the library: asked by name, kept in a free slot or not; and a scene of a new preset."""
    cdp = page.cdp
    dialog = 'document.querySelector(".mdlg-body")'
    live = 'S.capSlot = -1; S.model = "A2"; __pedal.cap_slot = -1; __pedal.cap = {data: new Uint8Array(4892), trim: 0}'
    cdp.evaluate(live)
    free = cdp.evaluate('[...Array(15).keys()].find(i => !(i in __pedal.caps))')
    kept = cdp.evaluate('Object.keys(__pedal.caps).length')
    cdp.evaluate('void savePreset(6)')
    page.wait('!!' + dialog + ' && /"A2"/.test(' + dialog + '.textContent) && /not in your library/.test(' + dialog + '.textContent)', 'the capture is named')
    button(page, f'Save it in slot {free + 1}')
    page.wait(f'__pedal.presets[6] && !!__pedal.caps[{free}] && __pedal.caps[{free}].name === "A2" && __pedal.cap_slot === {free} && ' + quiet, 'the capture kept, then the preset')
    out = {'kept': cdp.evaluate(f'[__pedal.caps[{free}].name, S.capSlot, Object.keys(__pedal.caps).length]')}
    require(out['kept'] == ['A2', free, kept + 1], f"the capture: {out['kept']}")
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate(live)
    cdp.evaluate('void savePreset(7)')
    page.wait('!!' + dialog, 'asked again')
    button(page, 'Only the preset')
    page.wait('__pedal.presets[7] && ' + quiet, 'the preset alone')
    require(cdp.evaluate('Object.keys(__pedal.caps).length') == kept + 1, 'a capture was kept that the person had refused')
    page.wait(TOASTS + '.some(e => /"A2" is not in your library/.test(e.innerText))', 'the capture that is not kept is named', 20)
    cdp.evaluate('__pedal.cap = __pedal.caps[9]; __pedal.cap_slot = 9; S.capSlot = 9')
    # a scene of a new preset: the preset is saved with it, and both are said
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('void (async () => { const p = newPedalboard(4); await new Promise(r => setTimeout(r, 400)); '
                 'const b = [...document.querySelectorAll("button")].find(e => e.offsetParent && e.innerText.trim() === "Start new"); if (b) b.click(); await p; })()')
    page.wait('hrSlot === 4 && curPreset < 0 && ' + quiet, 'a new preset in a chosen slot')
    cdp.evaluate('void addFx("gate")')
    page.wait('__pedal.chain.P.length + __pedal.chain.Q.length === 1 && ' + quiet, 'a block')
    require(not cdp.evaluate('!!__pedal.presets[4]'), 'the new preset is on the pedal before it is saved')
    cdp.evaluate('void saveSnap(1)')
    page.wait('__pedal.presets[4] && curPreset === 4 && __pedal.store[4] && __pedal.store[4].scenes[1] === "1" && ' + quiet, 'the scene and its new preset', 40)
    time.sleep(1.0)
    said = [' '.join(x.split()) for x in cdp.evaluate(TOASTS + '.map(e => e.innerText)')]
    require(any('SCENE 2 AND PRESET' in x.upper() and 'ARE SAVED' in x.upper() for x in said), f'both are said: {said}')
    out['scene'] = cdp.evaluate('[__pedal.presets[4], __pedal.store[4].scenes]')
    # a preset from a file: the chain is cleared and its blocks are added, one after the other
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    doc = {'format': 'hyperrig-preset', 'version': 1, 'min_reader': 1, 'kind': 'presets', 'exported': '', 'app': 'check', 'presets': [{
        'meta': {'name': 'Imported', 'description': '', 'tags': [], 'genre': '', 'author': '', 'created': '', 'modified': '', 'id': 'urp-0123456789abcdef'},
        'compat': {'source': {}, 'needs': {'effects': ['comp', 'gate'], 'captures': [], 'irs': []}},
        'sound': {'chain': [{'id': 'b1', 'type': 'gate', 'on': True, 'params': {'umbral_db': -60, 'release_ms': 90}}, {'amp': True},
                            {'id': 'b2', 'type': 'comp', 'on': True, 'params': {'umbral_db': -30, 'ratio_x10': 30, 'ataque_ms': 9, 'release_ms': 110, 'nivel_db': 2, 'mezcla_pct': 70}}],
                  'amp': {'present': True, 'on': False, 'capture': None}, 'cab_ir': None, 'gain_db': {'in': 3, 'out': -2}, 'tempo_bpm_x10': 1300,
                  'color': None, 'scenes': [], 'active_scene': None}}]}
    cdp.evaluate('void pioImport(' + json.dumps(json.dumps(doc)) + ')')
    button(page, 'Import')
    page.wait('__pedal.chain.P.length === 1 && __pedal.chain.Q.length === 1 && __pedal.amp === 0 && ' + quiet, 'the blocks of an imported preset', 40)
    time.sleep(1.0)
    said = [' '.join(x.split()) for x in cdp.evaluate(TOASTS + '.map(e => e.innerText)')]
    out['imported'] = cdp.evaluate('[__pedal.chain.P.map(x => x.type), __pedal.chain.Q.map(x => x.type), __pedal.gain, __pedal.bpm]')
    require(not any('didn' in x or 'apply' in x for x in said), f'the import was changed: {said}')
    require(out['imported'] == [['gate'], ['comp'], [3, -2], 1300], f"the import: {out['imported']}")
    cdp.evaluate('void (async () => { await Pedal.cmd("AMPX 1", "AMPX"); await loadChain(); })()')       # for the steps that follow
    page.wait('S.ampPresent === 1 && ' + quiet, 'the amp put back')
    return out


def captures(page, quiet, output):
    '''The library of captures as a person uses it: a .nam converted, loaded and saved, trim, read back, another one, delete, a wrong file.'''
    cdp = page.cdp
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('void uploadCaptures([' + NAM.replace('__NAME__', 'My Amp') + '], null)')
    page.wait('!!__pedal.caps[0] && capJobs === null && ' + quiet, 'the capture', 180)
    out = cdp.evaluate('({name: __pedal.caps[0].name, bytes: __pedal.caps[0].data.length, pieces: __pedal.sent.filter(c => /^LDB /.test(c)).length, audio: __pedal.audio, '
                       'stopped: __pedal.stops, shown: S.model, slot: S.capSlot, level: __pedal.sent.filter(c => /^CTRIM live/.test(c))})')
    require(out['name'] == 'My Amp' and out['audio'] == 2 and out['stopped'] == 1 and out['slot'] == 0 and 400 < out['bytes'] <= 8192, f'the capture: {out}')
    close = 'if (document.getElementById("lib").classList.contains("on")) closeLib()'
    cdp.evaluate(close)
    cdp.evaluate('void applyTrim(0, -5)')
    page.wait('__pedal.caps[0].trim === -2.5 && ' + quiet, 'a trim')
    cdp.evaluate('void uploadCaptures([' + NAM.replace('__NAME__', 'Othér · 23') + '], 14)')
    page.wait('!!__pedal.caps[14] && capJobs === null && ' + quiet, 'a second one, in the last slot', 180)
    cdp.evaluate(close)
    cdp.evaluate('void useSlot(true, 0, "My Amp")')
    page.wait('__pedal.cap_slot === 0 && ' + quiet, 'a capture chosen from the list')
    out['read_back'] = cdp.evaluate('pioSlotRead(async (line, pre, tmo) => await Pedal.cmd(line, pre, tmo), "cap", 14).then(r => [r.head.name, '
                                    'r.data.every((b, i) => b === __pedal.caps[14].data[i])])')
    require(out['read_back'] == ['Other 23', True], f"read back: {out['read_back']}")
    out['deleted'] = cdp.evaluate('Pedal.cmd("CDEL 14", "CDEL")')
    require(out['deleted'] == ['CDEL ok 14'] and cdp.evaluate('Object.keys(__pedal.caps).join()') == '0,9', f"delete: {out['deleted']}")
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    cdp.evaluate('void uploadCaptures([new File([new Uint8Array(900).fill(7)], "wrong.a2l")], null)')
    page.wait('capJobs === null && ' + TOASTS + '.some(e => /failed|Couldn|0 of 1/.test(e.innerText))', 'the wrong file refused', 30)
    page.wait(quiet, 'a quiet page')
    out['after_wrong'] = cdp.evaluate('({audio: __pedal.audio, caps: Object.keys(__pedal.caps).join()})')
    require(out['after_wrong'] == {'audio': 2, 'caps': '0,9'}, f"after a wrong file: {out['after_wrong']}")
    cdp.evaluate('void openLib("cap")')
    page.wait('document.getElementById("lib").classList.contains("on")', 'the library')
    time.sleep(1.0)
    out['picture'] = cdp.screenshot(output / 'captures.png')['path']
    cdp.evaluate(close)
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    return out


def global_settings(page, quiet, output):
    """The settings for every preset: shown as the pedal has them, changed, kept, taken back; the EQ off, on and flat; what has no room and what is refused."""
    cdp, at = page.cdp, '__pedal.globals'
    el = lambda name: f'document.getElementById("{name}")'
    press = lambda band, key, times=1: cdp.evaluate(f'(() => {{ const k = document.querySelectorAll("#geq .knob")[{band}]; for (let i = 0; i < {times}; i++) '
                                                    f'k.dispatchEvent(new KeyboardEvent("keydown", {{key: "{key}", bubbles: true}})); }})()')
    choose = lambda what, value='': cdp.evaluate(f'(() => {{ const e = {el(what)}; if (e.type === "checkbox") e.click(); else {{ e.value = "{value}"; e.dispatchEvent(new Event("change", {{bubbles: true}})); }} }})()')
    shown = lambda: cdp.evaluate('({knobs: [...document.querySelectorAll("#geq .knob")].map(k => +k.getAttribute("aria-valuenow")), off: document.querySelectorAll("#geq .knob.hroff").length, '
                                 f'on: {el("hrEqOn")}.checked, can: !{el("hrEqOn")}.disabled, flat: !{el("hrEqFlat")}.disabled, say: {el("hrEqSay")}.textContent, '
                                 f'note: !document.querySelector("#settings .gdnote").hidden, hot: {el("gsave")}.classList.contains("gdhot")}})')
    values = lambda: cdp.evaluate('[' + ', '.join([el('hpf') + '.value', el('limOn') + '.checked', el('limThr') + '.value', el('limRel') + '.value', el('spill') + '.checked',
                                                   el('snapGlide') + '.checked', el('spur') + '.checked']) + ']')
    toasts = lambda: [' '.join(x.split()) for x in cdp.evaluate(TOASTS + '.map(e => e.innerText)')]
    top = lambda: cdp.evaluate('document.querySelector("#settings .dbox").scrollTo(0, 0)')
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove()); void loadGlobal()')
    page.wait('S.geq && S.lim && S.spur && ' + quiet, 'the settings read')
    cdp.evaluate(el('setBtn') + '.click()')
    page.wait(el('settings') + '.classList.contains("on") && ' + quiet, 'the settings')
    first = shown()
    require(first == {'knobs': [0] * 5, 'on': False, 'can': False, 'flat': False, 'off': 0, 'say': '', 'note': False, 'hot': False}, f'a flat EQ: {first}')
    seen = cdp.evaluate('({text: document.querySelector("#settings .hrall").innerText, sections: ["limSec", "spurRow", "snapGlideRow"].map(x => document.getElementById(x).style.display !== "none"), '
                        'hpf: document.getElementById("hpf").options.length})')
    require('every preset' in seen['text'] and 'Save to pedal' in seen['text'] and seen['sections'] == [True] * 3 and seen['hpf'] == 22 and values() == ['55', True, '-3', '100', True, True, True], f'the settings: {seen} {values()}')
    n = cdp.evaluate('__pedal.sent.length')
    press(0, 'ArrowUp', 3)
    page.wait(at + '.geq[0] === 3', 'a band')
    press(2, 'PageDown')
    page.wait(at + '.geq[2] === -2 && ' + quiet, 'another band')
    now = shown()
    require(now['knobs'] == [3, 0, -2, 0, 0] and now['on'] and now['can'] and now['flat'] and now['note'] and now['hot'], f'an EQ in use, not saved: {now}')
    top()
    cdp.screenshot(output / 'settings-eq.png')
    choose('hrEqOn')
    page.wait(at + '.geq.every(v => v === 0) && !HR_EQ.busy && ' + quiet, 'the EQ off')
    now = shown()
    require(now['knobs'] == [3, 0, -2, 0, 0] and now['off'] == 5 and not now['on'] and now['can'] and 'kept' in now['say'], f'the EQ off: {now}')
    cdp.screenshot(output / 'settings-eq-off.png')
    cdp.evaluate('void loadGlobal()')
    page.wait(quiet, 'read again')
    require(shown()['off'] == 5, 'the values of an EQ that is off are not kept')
    choose('hrEqOn')
    page.wait(at + '.geq.join() === "3,0,-2,0,0" && !HR_EQ.busy && ' + quiet, 'the EQ on again')
    saved = cdp.evaluate('__pedal.saved_settings')
    cdp.click('#gsave')
    page.wait(f'__pedal.saved_settings === {saved + 1} && !gdDirty', 'kept in the pedal')
    require(not shown()['note'], 'what is saved is called unsaved')
    # flat, and back
    cdp.evaluate(TOASTS + '.forEach(e => e.remove()); ' + el('hrEqFlat') + '.click()')
    page.wait(at + '.geq.every(v => v === 0) && ' + quiet, 'flat')
    require(shown()['knobs'] == [0] * 5 and not shown()['can'], f'flat: {shown()}')
    button(page, 'Undo')
    page.wait(at + '.geq.join() === "3,0,-2,0,0" && !HR_EQ.busy && ' + quiet, 'flat undone')
    # the others, each as its control has it
    for what, value, held in (('hpf', '80', 'hpf === 80'), ('limThr', '-30', 'lim.thr === -30'), ('limRel', '500', 'lim.rel === 500'), ('limOn', '', 'lim.on === 0'), ('spill', '', 'spill === 0'),
                              ('snapGlide', '', 'snap === 0'), ('spur', '', 'spur === 0')):
        choose(what, value)
        page.wait(f'{at}.{held} && ' + quiet, f'the setting {what}')
    require(cdp.evaluate(el('limThr') + '.disabled && ' + el('limRel') + '.disabled && gdDirty'), 'the limiter off')
    top()
    cdp.screenshot(output / 'settings-changed.png')
    # closed without saving: asked, and the pedal goes back to what was saved
    cdp.evaluate(el('setX') + '.click()')
    page.wait('!!document.querySelector(".mdlg")', 'the question')
    cdp.evaluate('[...document.querySelectorAll(".mdlg button")].find(b => /Don.t save/.test(b.innerText)).click()')
    page.wait(TOASTS + '.some(e => /back to what you had saved/i.test(e.innerText)) && ' + quiet, 'back to what was saved', 40)
    require(cdp.evaluate('JSON.stringify({...__pedal.globals, pages: 0, cal: 0}) === __pedal.kept') and values() == ['55', True, '-3', '100', True, True, True] and shown()['knobs'] == [3, 0, -2, 0, 0],
            f"after the way back: {cdp.evaluate('__pedal.globals')} {values()} {shown()}")
    lines = [c for c in cdp.evaluate('__pedal.sent')[n:] if re.match(r'(?:GEQ|HPF|LIM|SPILL|GLIDE|SPUR) ', c)]
    require(len(lines) >= 20 and cdp.evaluate('__pedal.refused_globals') == 0, f'a line the pedal refused: {lines}')
    # no room: a band that comes on is not sent, one that is on goes on
    page.wait(quiet, 'a quiet page')
    cdp.evaluate(TOASTS + '.forEach(e => e.remove()); __pedal.ticks = 21400; ' + el('setBtn') + '.click()')
    page.wait('S.cpu[0] >= 22500 && ' + quiet, 'a full pedal')
    n = cdp.evaluate('__pedal.sent.length')
    press(4, 'ArrowUp')
    page.wait(TOASTS + '.some(e => /room/i.test(e.innerText))', 'no room, said')
    press(0, 'ArrowUp')
    page.wait(at + '.geq[0] === 4 && ' + quiet, 'a band that is on already')
    require(shown()['knobs'] == [4, 0, -2, 0, 0] and not [c for c in cdp.evaluate('__pedal.sent')[n:] if c.startswith('GEQ 4')], 'a band without room was sent')
    cdp.evaluate('__pedal.ticks = 0')
    page.wait('S.cpu[0] < 5000 && ' + quiet, 'room again')
    # refused by the pedal, and an answer that is not one: the page shows what the pedal has
    for answer in ('ERR GEQ usage', 'GEQ 1 2'):
        cdp.evaluate(TOASTS + f'.forEach(e => e.remove()); __pedal.wrong = {json.dumps(answer)}')
        press(1, 'ArrowUp', 5)
        page.wait(TOASTS + '.some(e => /did not take/i.test(e.innerText)) && ' + quiet, 'a refusal, said')
        cdp.evaluate('__pedal.wrong = null')
        require(shown()['knobs'] == [4, 0, -2, 0, 0], f'after a refusal: {shown()}')
    press(1, 'ArrowUp')
    page.wait(at + '.geq[1] === 1 && ' + quiet, 'and then it is taken')
    # stereo is told
    cdp.evaluate('S.stw = {...(S.stw || {}), w: 100}; hrEqShow()')
    require('mono' in shown()['say'], 'stereo with an EQ in use')
    cdp.evaluate('S.stw.w = 0; hrEqShow()')
    # left as it was
    cdp.evaluate(el('hrEqFlat') + '.click()')
    page.wait(at + '.geq.every(v => v === 0) && ' + quiet, 'flat')
    cdp.click('#gsave')
    page.wait('!gdDirty', 'kept')
    out = {'sent': len(lines), 'kinds': sorted({c.split(' ')[0] for c in lines}), 'toasts': toasts()}
    cdp.evaluate(el('setX') + '.click(); ' + TOASTS + '.forEach(e => e.remove())')
    page.wait('!' + el('settings') + '.classList.contains("on")', 'the settings closed')
    return out


def calibration(page, quiet, output):
    """The calibration of the input: it listens, suggests, and sets the trim only when asked; another capture, no sound, the end by itself."""
    cdp, out = page.cdp, {}
    el = lambda name: f'document.getElementById("{name}")'
    listens = 'Cal.open && __pedal.globals.cal.running === 1 && ' + quiet
    closed = '!Cal.open && __pedal.globals.cal.running === 0 && ' + quiet
    reading = lambda peak, rms: cdp.evaluate(f'__pedal.tell(__pedal.reading({peak}, {rms}))')

    def begin():
        page.wait(quiet, 'a quiet page')
        cdp.evaluate(TOASTS + '.forEach(e => e.remove()); ' + el('ampCal') + '.click()')
        page.wait(listens, 'the calibration listens')

    page.wait(quiet, 'a quiet page')
    cdp.click('[data-id="amp"]')
    page.wait('S.audio === 2 && !!' + el('ampCal'), 'the amp panel')
    slot, gain = cdp.evaluate('__pedal.cap_slot'), cdp.evaluate('__pedal.gain')
    cdp.evaluate('__pedal.gain = [0, 0]')
    begin()
    page.wait('/[0-9]/.test(' + el('calNow') + '.textContent)', 'the level of the input')
    text = cdp.evaluate(el('calm') + '.innerText')
    require('listens' in text and 'dBFS' not in text and 'dBu' not in text and cdp.evaluate(el('calNext') + '.disabled'), f'the first step: {text!r}')
    for peak, rms in ((-200, -260), (-120, -190), (-300, -350)):
        reading(peak, rms)
    page.wait(el('calWin') + '.textContent === "3" && ' + el('calPk') + '.textContent.includes("12.0") && !' + el('calNext') + '.disabled', 'three readings, the loudest of them')
    cdp.screenshot(output / 'calibrate-listen.png')
    n = cdp.evaluate('__pedal.sent.length')
    cdp.click('#calNext')
    page.wait('Cal.phase === 2 && __pedal.globals.cal.running === 0 && ' + el('calApply') + '.style.display === ""', 'the suggestion')
    out['said'] = ' '.join(cdp.evaluate(el('calRes') + '.innerText').split())
    cdp.screenshot(output / 'calibrate-result.png')
    sent = cdp.evaluate('__pedal.sent')[n:]
    require('6.0 dB' in out['said'] and cdp.evaluate(f'__pedal.caps[{slot}].trim') == 0 and sent.count('CALIB stop') == 1 and not [c for c in sent if c.startswith('CTRIM')], f"the suggestion: {out['said']} {sent}")
    cdp.click('#calApply')
    page.wait(f'__pedal.caps[{slot}].trim === -6 && !Cal.open && ' + quiet, 'the trim')
    # right as it is, with the input gain of the preset: nothing to set
    cdp.evaluate('__pedal.gain = [4, 0]')
    begin()
    reading(-160, -190)
    page.wait('!' + el('calNext') + '.disabled', 'a reading')
    cdp.click('#calNext')
    page.wait('Cal.phase === 2 && /nothing to change/.test(' + el('calRes') + '.innerText) && /input gain of .?4/.test(' + el('calRes') + '.innerText)', 'the trim is right')
    require(cdp.evaluate(el('calApply') + '.style.display') == 'none', 'a trim that is right is offered')
    cdp.click('#calX')
    page.wait(closed, 'closed')
    # no sound at all
    begin()
    reading(-999, -999)
    page.wait('!' + el('calNext') + '.disabled && /Nothing is heard/.test(' + el('calRes') + '.innerText)', 'nothing heard')
    cdp.click('#calNext')
    page.wait('/No sound was heard/.test(' + el('calRes') + '.innerText)', 'no suggestion without sound')
    cdp.click('#calX')
    page.wait(closed, 'closed')
    # another capture plays: what was found is not for it
    begin()
    reading(-200, -260)
    page.wait('!' + el('calNext') + '.disabled', 'a reading')
    cdp.evaluate('__pedal.cap_slot = 14')
    reading(-150, -200)
    page.wait(closed + ' && ' + TOASTS + '.some(e => /another capture/i.test(e.innerText))', 'another capture')
    cdp.evaluate(f'__pedal.cap_slot = {slot}')
    # it ends by itself
    begin()
    cdp.evaluate('__pedal.globals.cal.running = 0; __pedal.tell("ERR CALIB stopped (timeout)")')
    page.wait('!Cal.open && ' + TOASTS + '.some(e => /3 minutes/i.test(e.innerText))', 'the end by itself')
    # given up, and a reading that comes late is passed over
    begin()
    cdp.click('#calX')
    page.wait(closed, 'given up')
    reading(-100, -150)
    page.wait(quiet, 'a quiet page')
    require(not cdp.evaluate('Cal.open'), 'a late reading opens it')
    cdp.evaluate(f'void applyTrim({slot}, 0)')
    cdp.evaluate(f'__pedal.gain = {gain}')
    page.wait(f'__pedal.caps[{slot}].trim === 0 && ' + quiet, 'the trim as it was')
    out['sent'] = sorted({c for c in cdp.evaluate('__pedal.sent') if c.startswith('CALIB')})
    require(out['sent'] == ['CALIB start', 'CALIB stop'], f"the words of the calibration: {out['sent']}")
    cdp.evaluate(TOASTS + '.forEach(e => e.remove())')
    return out


def run(bundle, output, page_class=Page):
    editor.check(bundle)
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT / 'build') and not output.exists(), 'use a fresh directory under build/')
    output.mkdir(parents=True)
    report = {'kind': 'hyperrig-mini-development-editor-page-check', 'bundle': str(bundle), 'device_io': False,
              'hardware_apis_replaced': True, 'steps': {}, 'result': 'fail'}
    product = json.loads((Path(bundle) / 'editor/profile.json').read_bytes())['development'].get('product')
    identity = f"HRID 1 {product['version']} {product['build_id']} banks=3" if product else None
    page = page_class(bundle, output, identity)
    cdp, steps = page.cdp, report['steps']
    try:
        page.wait('window.__urOk === true && !!document.getElementById("miniPortStatus")', 'the page')
        steps['note'] = cdp.evaluate('document.getElementById("miniPortStatus").textContent')
        test = bool(product) and '-' in product['version']                  # a release does not call itself a test version
        said = ('development build', 'not qualified') if not product else (f"HyperRig {product['version']}", *(('Test version', 'not everything has been tried') if test else ()))
        require(all(text in steps['note'] for text in said) and (not product or test or 'Test version' not in steps['note']), 'the page hides what it is')
        require(cdp.evaluate('__pedal.opened') == 0, 'the page connected by itself')
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        cdp.evaluate('void connect()')
        page.wait('S.connected && typeof lvlTimer !== "undefined" && !!lvlTimer', 'the connection', 60)
        time.sleep(1.5)
        if product:            # the port that is asked for: the pedal's numbers, and the ones before; the one that is known is found again
            asked = cdp.evaluate('(async () => { await navigator.serial.requestPort({filters: [{usbVendorId: 1}]}); return JSON.stringify(__pedal.asked); })()')
            require(json.loads(asked) == {'filters': [{'usbVendorId': 0x4C4A, 'usbProductId': 0x5155}, {'usbVendorId': 0x3654}]}, f'the port that is asked for: {asked}')
            known = cdp.evaluate('(async () => { const g = navigator.serial.getPorts, of = (v, p) => ({getInfo: () => ({usbVendorId: v, usbProductId: p}), of: [v, p]}), out = []; '
                                 'for (const list of [[of(0x4c4a, 0xc755), of(0x4c4a, 0x5155)], [of(0x4c4a, 0xc755), of(0x3654, 0x5155)], [of(0x4c4a, 0xc755), of(0x1209, 2)]]) { '
                                 'navigator.serial.getPorts = async () => list; const k = await SerialTransport.known(); out.push(k ? k.of : null); } navigator.serial.getPorts = g; return out; })()')
            require(known == [[0x4C4A, 0x5155], [0x3654, 0x5155], None], f'the port that is known: {known}')
        steps['connected'] = cdp.evaluate('({fw: S.fw, preset: curPreset, sent: __pedal.sent.length})')
        cdp.evaluate('document.querySelector(".ccall .tskip")?.click()')
        # Tap: five presses half a second apart, through the button.
        cdp.evaluate('''(async () => { for (let i = 0; i < 5; i++) { document.getElementById("tap").click();
                         await new Promise(r => setTimeout(r, 500)); } })()''')
        time.sleep(0.5)
        steps['tap'] = cdp.evaluate('({pedal: __pedal.bpm, shown: document.getElementById("bpm").value, '
                                    'sent: __pedal.sent.filter(c => /^BPM \\d/.test(c))})')
        require(1150 <= steps['tap']['pedal'] <= 1250 and steps['tap']['sent'], 'the taps did not reach the pedal')
        # A tempo typed in the field.
        cdp.evaluate('''(() => { const e = document.getElementById("bpm"); e.focus(); e.value = "95.5";
                         e.dispatchEvent(new KeyboardEvent("keydown", {key: "Enter", bubbles: true})); })()''')
        page.wait('__pedal.bpm === 955', 'the typed tempo')
        steps['typed'] = cdp.evaluate('({pedal: __pedal.bpm, shown: document.getElementById("bpm").value})')
        # The tuner.
        cdp.evaluate('document.getElementById("tunerBtn").click()')
        page.wait('__pedal.tuner[0] === 1 && __pedal.sent.includes("TUNE")', 'the tuner')
        page.wait('/A/.test(document.querySelector("#tuner .note")?.textContent || "")', 'the note shown')
        steps['tuner'] = cdp.evaluate('({pedal: __pedal.tuner.slice(), note: document.querySelector("#tuner .note").textContent})')
        steps['tuner_picture'] = cdp.screenshot(output / 'tuner.png')['path']
        cdp.evaluate('document.getElementById("tuClose").click()')
        page.wait('__pedal.tuner[0] === 0', 'the tuner closed')
        # The amp, as a person does it: select its block, then its Bypass button, then again.
        cdp.click('[data-id="amp"]')
        page.wait('!!document.getElementById("ampOn")', 'the amp panel')
        for wanted in (0, 1):
            page.wait('S.connected && !refreshing && !txn && !saveRun && !Pedal.busy', 'a quiet page')
            time.sleep(0.5)
            cdp.click('#ampOn')
            page.wait(f'__pedal.amp === {wanted} && S.amp === {wanted}', f'the amp at {wanted}')
            steps[f'amp_{wanted}'] = cdp.evaluate('document.getElementById("ampOn").innerText.trim()')
        cdp.evaluate('Pedal.cmd("AMPEQ 1 600", "AMPEQ ")')
        page.wait('__pedal.ampeq[1] === 600', 'an amp control')
        steps['amp_picture'] = cdp.screenshot(output / 'amp.png')['path']
        # A new preset on an empty slot: the slot is chosen, the chain is built, Save goes there.
        toasts = '[...document.querySelectorAll(".toast, .toasts > *, #toasts > *")].map(e => e.innerText.trim().replace(/\\n+/g, " | ")).filter(Boolean)'
        quiet = 'S.connected && !refreshing && !txn && !saveRun && !Pedal.busy'
        cdp.evaluate('document.querySelectorAll(".toast, .toasts > *, #toasts > *").forEach(e => e.remove())')
        cdp.evaluate('void (async () => { const p = newPedalboard(0); await new Promise(r => setTimeout(r, 400)); '
                     'const b = [...document.querySelectorAll("button")].find(e => e.offsetParent && e.innerText.trim() === "Start new"); '
                     'if (b) b.click(); await p; })()')
        page.wait('__pedal.sent.includes("PNEW") && hrSlot === 0', 'the new preset')
        page.wait('__pedal.ampx === 0 && S.ampPresent === 0 && ' + quiet, 'a new preset without the amp')
        require(cdp.evaluate('__pedal.chain.P.length + __pedal.chain.Q.length') == 0, 'a new preset is not empty')
        cdp.evaluate('void (async () => { await Pedal.cmd("AMPX 1", "AMPX"); await loadChain(); })()')       # put back for the steps below
        page.wait('__pedal.ampx === 1 && S.ampPresent === 1 && ' + quiet, 'the amp added like a block')
        steps['new_preset_label'] = cdp.evaluate('document.getElementById("presetLbl").innerText')
        page.wait(quiet, 'a quiet page')
        cdp.evaluate('void addFx("gate")')
        page.wait('__pedal.chain.Q.length === 1 && ' + quiet, 'a block added')
        cdp.click('#saveGo')
        page.wait('__pedal.store[0] && __pedal.store[0].chain.Q.length === 1 && curPreset === 0 && ' + quiet, 'Save into the chosen slot')
        time.sleep(2.0)
        steps['saved_new'] = cdp.evaluate('({name: __pedal.presets[0], scenes: __pedal.store[0].scenes, shown: presetName()})')
        require(steps['saved_new']['scenes'] == ('10000000' if product else '1000'), 'the first scene was not made')
        # A second block before the amp, added there at once, then moved behind the gate by its drop place.
        cdp.evaluate('void addFx("boost", {t: "serial", si: 0})')
        page.wait('__pedal.chain.P.length === 1 && ' + quiet, 'a block before the amp')
        cdp.evaluate('void moveBlock(__pedal.chain.P[0].id, {t: "serial", si: 3})')
        page.wait('__pedal.chain.P.length === 0 && __pedal.chain.Q.length === 2 && ' + quiet, 'a block moved over the amp')
        steps['moved'] = cdp.evaluate('__pedal.chain.Q.map(x => x.type)')
        require(steps['moved'] == ['gate', 'boost'], f"the order is {steps['moved']}")
        cdp.evaluate('void moveBlock(__pedal.chain.Q[1].id, {t: "serial", si: 1})')
        page.wait('__pedal.chain.Q.map(x => x.type).join() === "boost,gate" && ' + quiet, 'a block moved within its section')
        # In parallel with the other one, and back in series.
        cdp.evaluate('void moveBlock(__pedal.chain.Q[1].id, {t: "newgrp", si: 1})')
        time.sleep(1.5)
        steps['lanes'] = cdp.evaluate('__pedal.chain.Q.map(x => [x.type, x.lane || 0])')
        page.wait(quiet, 'a quiet page')
        cdp.click('#saveGo')
        page.wait('__pedal.store[0].chain.Q.length === 2 && edCount() === 0 && ' + quiet, 'Save of a loaded preset')
        time.sleep(1.0)
        cdp.evaluate('void savePreset(1)')
        page.wait('__pedal.presets[1] && curPreset === 1 && ' + quiet, 'a second preset')
        time.sleep(3.0)
        # The footswitch selects the first one, then a change and Save: refused before revision mini-dev-02.
        cdp.evaluate('document.querySelectorAll(".toast, .toasts > *, #toasts > *").forEach(e => e.remove())')
        cdp.evaluate('__pedal.press(0)')
        page.wait('curPreset === 0', 'the page following the footswitch')
        time.sleep(2.5)
        before = cdp.evaluate('__pedal.chain.Q.find(x => x.type === "gate").on')
        cdp.evaluate('void toggle(__pedal.chain.Q.find(x => x.type === "gate").id)')
        page.wait(f'__pedal.chain.Q.find(x => x.type === "gate").on !== {before} && ' + quiet, 'a block switched after the footswitch')
        cdp.click('#saveGo')
        page.wait(f'__pedal.store[0].chain.Q.find(x => x.type === "gate").on !== {before} && edCount() === 0', 'Save after the footswitch')
        steps['after_footswitch'] = cdp.evaluate(toasts)
        require(not [x for x in steps['after_footswitch'] if 'outside' in x or 'Couldn' in x], 'an edit was refused')
        time.sleep(1.5)
        # Scenes: the second tab is empty and makes one; the first goes back.
        cdp.click('#snaps .snap[data-snap="1"]')
        page.wait('/^110+$/.test(__pedal.scenes) && S.snap === 1', 'a scene made from its tab')
        cdp.click('#snaps .snap[data-snap="0"]')
        page.wait('__pedal.scene === 0 && S.snap === 0', 'a scene chosen from its tab')
        steps['scenes'] = cdp.evaluate('({pedal: __pedal.scenes, page: S.snaps})')
        time.sleep(1.0)
        # Stereo and mono.
        page.wait('!document.getElementById("stSw").hidden', 'the stereo switch')
        for wanted in (100, 0):
            cdp.evaluate('void stwToggle()')
            page.wait(f'__pedal.stereo === {wanted}', f'stereo at {wanted}')
        steps['stereo'] = cdp.evaluate('__pedal.sent.filter(c => /^STW \\d/.test(c))')
        # The tab with the pedal's mode and bank: preset mode, live mode and back.
        cdp.click('#saveGo')
        page.wait('edCount() === 0 && ' + quiet, 'the change saved')
        cdp.evaluate('Pedal.cmd("FSMODE", "FSMODE").then(r => fmApply(parseFsMode(r[0])))')
        if product:
            steps['setups'] = setups(page, output)
        else:
            page.wait('!document.getElementById("fmChip").hidden', 'the mode tab')
            for wanted in ('live', 'preset'):
                page.wait(quiet, 'a quiet page')
                cdp.evaluate('document.getElementById("fmChip").click()')
                page.wait(f'__pedal.sent.includes("FSMODE mode={wanted}") && S.fm.live === {str(wanted == "live").lower()}', f'{wanted} mode')
        steps['mode_tab'] = cdp.evaluate('document.getElementById("fmChip").textContent')
        # The footswitch panel: it opens, an action changes, and its Save keeps the settings.
        page.wait('!document.getElementById("fswBtn").disabled', 'the Footswitches button')
        cdp.evaluate('document.getElementById("fswBtn").click()')
        time.sleep(1.5)
        steps['footswitches_open'] = cdp.evaluate('document.getElementById("fsm").classList.contains("on")')
        cdp.screenshot(output / 'footswitches.png')
        if not steps['footswitches_open']:
            cdp.evaluate('void fsOpen()')
            page.wait('document.getElementById("fsm").classList.contains("on")', 'the footswitch panel')
            time.sleep(0.8)
            cdp.screenshot(output / 'footswitches.png')
        steps['switches_in_panel'] = cdp.evaluate('document.querySelectorAll("#fsCols .fsk").length')
        require(steps['switches_in_panel'] == (3 if product else 4), f"the panel shows {steps['switches_in_panel']} switches")
        cdp.evaluate('void fsSetPress(0, 0)')
        page.wait('__pedal.press_bits[0] === 0', 'a footswitch setting')
        cdp.evaluate('void fsSaveAll()')
        page.wait('__pedal.saved_settings === 1', 'the footswitch settings kept')
        cdp.evaluate('fsClose()')
        if product:
            steps['cab_irs'] = cab_irs(page, quiet, output)
            steps['captures'] = captures(page, quiet, output)
            steps['knobs'] = knobs(page, quiet, output)
            steps['acoustic'] = acoustic(page, output)
            steps['own_effects'] = own_effects(page, output)
            steps['harmonizer'] = harmonizer(page, output)
            steps['full_chain'] = full_chain(page, output)
            steps['replace'] = replace(page, output)
            steps['saving'] = saving(page, quiet)
            steps['global_settings'] = global_settings(page, quiet, output)
            steps['calibration'] = calibration(page, quiet, output)
            steps['controls'] = controls(page, quiet, output)
            steps['midi'] = midi(page, quiet, output)
        # Stage.
        cdp.evaluate('void stageOpen()')
        page.wait('document.body.classList.contains("staging")', 'the stage view')
        time.sleep(1.0)
        steps['stage_tiles'] = cdp.evaluate('[...document.querySelectorAll("#stFs .sttile")].map(e => e.querySelector(".num").textContent)')
        require(steps['stage_tiles'] == (['A', 'B', 'C'] if product else ['1', '2', '3', '4']), f"the stage shows {steps['stage_tiles']}")
        cdp.screenshot(output / 'stage.png')
        if product:
            # A bank above nine, and the presets of a bank of three.
            cdp.evaluate('__pedal.bank = 11; Pedal.cmd("FSMODE", "FSMODE").then(r => fmApply(parseFsMode(r[0])))')
            page.wait('S.fm && S.fm.bank === 11', 'bank 11 of the FSMODE answer')
            steps['banks'] = cdp.evaluate('({slots: [fmSlot(1, 0), fmSlot(1, 2), fmSlot(2, 0), fmSlot(11, 1)], '
                                          'level: parseLvlFm("LVL x fm=0,1,10,0 y"), chip: document.getElementById("fmChip").textContent})')
            require(steps['banks']['slots'] == [0, 2, 3, 31] and steps['banks']['level']['bank'] == 10, f"banks: {steps['banks']}")
            cdp.evaluate('__pedal.bank = 1')
        cdp.evaluate('typeof stageClose === "function" ? void stageClose() : document.body.classList.remove("staging")')
        time.sleep(0.5)
        # What stays blocked never reaches the wire.
        steps['blocked'] = cdp.evaluate('''(async () => { const out = {}; for (const c of ["CSAVE 15 A", "ISAVE 8 A", "UBOOT", "BLE key", "AUTH x", "CALIB 1", "CALIB sens 12.0", "GEQ 5 1", "LIM 1 -201 100", "HPF 81", "PDEL 9"])
                                           out[c] = (await Pedal.cmd(c, c.split(" ")[0])).join(" "); return out; })()''')
        require(all(v.startswith('ERR MINI_APP') for v in steps['blocked'].values()), 'a blocked command was sent')
        sent = cdp.evaluate('__pedal.sent')
        require(not [c for c in sent if c.split(' ')[0] in ('UBOOT', 'AUTH') + (() if product else ('ISAVE', 'CSAVE', 'CALIB')) or
                     c in ('BLE key', 'PDEL 9', 'ISAVE 8 A', 'CSAVE 15 A', 'CALIB 1', 'CALIB sens 12.0', 'GEQ 5 1', 'LIM 1 -201 100', 'HPF 81')], 'a blocked command was sent')
        if product:
            steps['names'] = names(page, output)
            steps['save_line'] = save_line(page, output)
            steps['eight_scenes'] = eight_scenes(page, output)
            steps['preset_files'] = preset_files(page)
            steps['import_all'] = import_all(page, output)
            steps['long_delay'] = long_delay(page)
            steps['same_volume'] = same_volume(page, output)
        steps['page_errors'] = cdp.evaluate('__errors')
        require(not steps['page_errors'], f"page errors: {steps['page_errors']}")
        steps['picture'] = cdp.screenshot(output / 'page.png')['path']
        report['sent'] = sent
        if product:
            page.close()
            from tools import check_mini_try
            steps['trying'] = check_mini_try.run(bundle, output, page_class)
            for name, other in (('another_build', f"HRID 1 {product['version']} 0123456789abcdef banks=3"), ('no_identity', None),
                                ('newer_build', 'HRID 1 99.0.0 0123456789abcdef banks=3')):
                page = page_class(bundle, output, other)
                cdp = page.cdp
                try:
                    steps[name] = only_reads(page, output / f'{name}.png', name == 'newer_build')
                finally:
                    page.close()
        report['result'] = 'pass'
    finally:
        if report['result'] != 'pass':
            try:
                report['sent'] = cdp.evaluate('__pedal.sent')
                report['page_errors'] = cdp.evaluate('__errors')
                cdp.screenshot(output / 'failure.png')
            except Exception:
                pass
        (output / 'report.json').write_bytes(editor.encoded(report))
        if page.process.poll() is None:
            page.close()
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.bundle, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != 'sent'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
