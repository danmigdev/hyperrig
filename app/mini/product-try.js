/* Trying without saving: a preset, a NAM capture or a cab IR is heard on the pedal, and nothing is stored there until Keep. Back gives what played before.
 *
 * One try at a time. It goes through these states: starting (what plays now is read, and the person is asked when something of it could not come back),
 * loading, playing, failed (what plays is what was there before, the next one can be tried), lost (no pedal), back. While it is on, the page's other ways of
 * changing what plays or of writing to the pedal are refused (GUARDED, STORES). A preset chosen on the pedal ends the try. It starts quietly and rises, up to a limit. */
(function () {
  "use strict";
  const START = -30, STEP = 2, EVERY = 160, NEAR = -30, TURN = 3;      // dB, dB, ms; tenths of dB under full scale at which it stops rising; dB of a press
  const FILES = { preset: { most: 4 * 1024 * 1024, ends: /\.json$/i, accept: ".json,application/json", say: "a HyperRig preset (.json)" },
    capture: { most: 8 * 1024 * 1024, ends: /\.(?:nam|a2l)$/i, accept: ".nam,.a2l", say: "a .nam or .a2l file" }, ir: { most: 24 * 1024 * 1024, ends: /\.wave?$/i, accept: ".wav", say: "a .wav file" } };
  const BUSY = "Wait until the pedal is free.", FIRST = "You are trying a sound. Keep it or go back first.";
  let trial = null, starting = false;
  class Stopped extends Error {}

  const el = (tag, attributes, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attributes || {})) if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
    e.append(...children.filter(c => c !== null && c !== undefined));
    return e;
  };
  const short = (s, n) => { const t = pioText(s, 80); return t.length > n ? t.slice(0, n - 1) + "…" : t; };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const dB = v => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v) + " dB";
  const line = async (send, text, pre, ms) => pioFind(await send(text, pre, ms || 1500), pre);
  const free = (lib, n) => { const used = new Set(lib.list.map(x => x.slot)); for (let k = 0; k < n; k++) if (!used.has(k)) return k; return -1; };
  const home = b => (b.p >= 0 ? slotTxt(b.p) : "");

  /* What plays now, all of it that a command can bring back. */
  async function read(send = pioSendLive) {
    const lvl = await line(send, "LVL", "LVL"), p = / c=(\d+) p=(-?\d+)(?: |$)/.exec(lvl);
    if (!p) throw new Error("no answer");
    const live = await pioReadLive(send, pioReadOpts());
    const caps = pioLib(await send("CLIST", PIO_LIBEND("CLIST"), 3000), true), irs = pioLib(await send("ILIST", PIO_LIBEND("ILIST"), 3000), false);
    if (!caps.full || !irs.full) throw new Error("the slots could not be read");
    const sn = /^SNAPS ([01]+) (?:current|actual)=(-?\d+)/.exec(await line(send, "SNAPS", "SNAPS"));
    const st = S.stw ? parseStw(await line(send, "STW", "STW")) : null;
    return { p: +p[2], gen: +p[1], live, caps, irs, scenes: sn ? sn[1] : "", scene: sn ? +sn[2] : -1, bpm: pioBpm(await line(send, "BPM", "BPM")), color: pioColor(await line(send, "PCOLOR", "PCOLOR")), stereo: st ? st.w : null };
  }
  const each = live => ["P", "Q"].flatMap(b => live.chain[b].map(x => ({ b, x })));
  const shape = live => each(live).map(({ b, x }) => b.toLowerCase() + (S.types[x.type] || {}).id + ["", "a", "b"][x.lane || 0]).join();
  const params = x => ((S.types[x.type] || {}).params || []).filter(q => q.name);
  const ownIr = x => { const q = x.type === "ir" ? params(x).find(y => y.name === "ir_slot") : null; return q ? x.p[q.idx] || 0 : 0; };

  /* What differs between two readings, in words. */
  function differs(a, b) {
    const out = [], x = each(a.live), y = each(b.live), eq = (p, q) => JSON.stringify(p) === JSON.stringify(q);
    if (a.p !== b.p) out.push("the preset");
    if (shape(a.live) !== shape(b.live) || a.live.amp.present !== b.live.amp.present) out.push("the blocks");
    else if (x.some((k, i) => k.x.on !== y[i].x.on || !eq(k.x.p, y[i].x.p)) || !eq(a.live.amp, b.live.amp)) out.push("a block or a knob");
    if (a.scene >= 0 && a.scene !== b.scene || a.scenes !== b.scenes) out.push("the scenes");
    if (!eq(a.live.gain, b.live.gain)) out.push("the volume");
    if (!eq(a.live.aeq, b.live.aeq)) out.push("the tone of the amp");
    for (const k of ["mix", "xo", "xeq"]) if (!eq(a.live[k], b.live[k])) { out.push("the parallel paths"); break; }
    if (a.bpm !== b.bpm) out.push("the tempo");
    if (a.stereo !== b.stereo) out.push("stereo");
    if (a.color !== b.color) out.push("the colour");
    if (a.live.amp.present && a.caps.cur !== b.caps.cur) out.push("the capture");
    if (a.irs.cur !== b.irs.cur && x.some(k => k.x.type === "ir" && !ownIr(k.x))) out.push("the cab IR");
    return out;
  }

  /* From what plays (now) to what played (b): the commands for what differs, with the same blocks in the same places. What was sent, as the page counts changes. */
  async function level(b, now) {
    const send = pioSendLive, done = [], cmd = async (text, pre, mark, ms) => { const r = await line(send, text, pre, ms); if (!/^ERR/.test(r)) done.push(mark); };
    if (b.live.amp.present !== now.live.amp.present) await cmd(`AMPX ${b.live.amp.present ? 1 : 0}`, "AMPX", { other: 1 }, 3000);
    if (b.live.amp.present && b.live.amp.on !== now.live.amp.on) await cmd(`AMP ${b.live.amp.on ? 1 : 0}`, "AMP ", { on: 1 });
    if (shape(b.live) === shape(now.live)) {
      const a = each(b.live), c = each(now.live);
      for (let i = 0; i < a.length; i++) {
        const x = a[i].x, y = c[i].x;
        if (ownIr(x) !== ownIr(y)) await cmd(`FXIR ${y.id} ${ownIr(x) - 1}`, "FXIR", { other: 1 }, 3000);
        for (const q of params(x)) if (!PIO_REF_P[q.name] && x.p[q.idx] !== y.p[q.idx])
          await (q.name === PIO_OS_P ? cmd(`FXOS ${y.id} ${x.p[q.idx]}`, "FXOS", { p: [y.id, q.idx, x.p[q.idx]] }) : cmd(`FXP ${y.id} ${q.idx} ${x.p[q.idx]}`, "FXP", { p: [y.id, q.idx, x.p[q.idx]] }));
        if (x.on !== y.on) await cmd(`FXE ${y.id} ${x.on ? 1 : 0}`, "FXE", { on: 1 }, 3000);
      }
      for (const k of ["P", "Q"]) for (let g = 0; g < Math.max(b.live.mix[k].length, b.live.xo[k].length); g++) {
        const m = b.live.mix[k][g], n = now.live.mix[k][g];
        if (m && String(m) !== String(n)) await cmd(`FXMIX ${k} ${g} ${m[0]} ${m[1]}`, "FXMIX", { other: 1 });
        if ((b.live.xo[k][g] || 0) !== (now.live.xo[k][g] || 0) || (b.live.xeq[k][g] || 0) !== (now.live.xeq[k][g] || 0)) await cmd(`FXXO ${k} ${g} ${b.live.xo[k][g] || 0} ${b.live.xeq[k][g] || 0}`, "FXXO", { other: 1 });
      }
    }
    if (String(b.live.gain) !== String(now.live.gain)) await cmd(`GAIN ${b.live.gain[0]} ${b.live.gain[1]}`, "GAIN", { on: 1 });
    if (b.live.aeq && String(b.live.aeq) !== String(now.live.aeq)) await cmd(`AMPEQ ${b.live.aeq.join(" ")}`, AEQ_PRE, { aeq: b.live.aeq.map((v, i) => (v === (now.live.aeq || [])[i] ? -1 : i)).filter(i => i >= 0) });
    if (b.bpm != null && b.bpm !== now.bpm) await cmd(`BPM ${b.bpm}`, "BPM", {});
    if (b.stereo != null && b.stereo !== now.stereo) await cmd(`STW ${b.stereo > 0 ? 100 : 0}`, "STW", { other: 1 });
    if (b.p < 0 && b.color !== now.color) await cmd(`PCOLOR ${b.color || "none"}`, "PCOLOR", {});
    return done;
  }
  /* A preset that was in no slot is made again from what was read. */
  async function rebuild(b) {
    const ctx = pioCtxOf(b.caps, b.irs), pre = pioPresetOut({ live: b.live, bpm10: b.bpm, color: b.color, caps: b.caps, irs: b.irs, scenes: [], names: [], active: -1, stereo: b.stereo == null ? null : b.stereo > 0 }, S.types, {});
    const plan = pioPlan(pre, ctx);
    plan.cmds = plan.cmds.filter(c => !/^PCOLOR /.test(c.line));
    await pioRun(plan, pioSendLive, ctx);
  }
  const changes = () => ({ p: new Map(ED.p), on: ED.on, other: ED.other, aeq: ED.aeq, aeqB: new Set(ED.aeqB), aeqV: ED.aeqV.slice(), aeqS: ED.aeqS.slice(), aeqT: ED.aeqT.slice() });
  /* Everything as it was. What could not be put back, in words; the page's count of changes follows. */
  async function putBack(b, undo, replaced) {
    let now = await read(), tun = null, marks = [];
    const moved = now.p !== b.p || !!replaced;
    try {
      if (moved) {
        tun = await pioMute();
        if (b.p >= 0) {
          await Pedal.cmd("PLIST", doneBy("PLIST end", "PLIST fin"), 4000);            // the rules load a preset the pedal has named
          const r = reply(await Pedal.cmd(`PLOAD ${b.p}`, "PLOAD", 8000), "PLOAD");
          if (!r.startsWith("PLOAD ok")) throw new Error(errText(r) || "no answer");
        } else await rebuild(b);
        now = await read();
      } else for (const c of undo.slice().reverse()) await line(pioSendLive, c, c.split(" ")[0] + (c.startsWith("AMP ") ? " " : ""), 3000);
      if (b.scene >= 0 && now.scene !== b.scene && now.scenes[b.scene] === "1") { await Pedal.cmd(`SNAP ${b.scene}`, "SNAP ", 3000); now = await read(); }
      const took = b.slots || [-1, -1];                                 // what the stored preset brings of its own: another one that played is a change that is not saved
      if (b.caps.cur >= 0 && now.caps.cur !== b.caps.cur) { await Pedal.cmd(`CLOAD ${b.caps.cur}`, "CLOAD", 8000); if (took[0] >= 0) marks.push({ other: 1 }); }
      if (b.irs.cur >= 0 && now.irs.cur !== b.irs.cur) { await Pedal.cmd(`ILOAD ${b.irs.cur}`, "ILOAD", 8000); if (took[1] >= 0) marks.push({ other: 1 }); }
      for (let turn = 0; turn < 2; turn++) {
        now = await read();
        const sent = await level(b, now);
        marks = marks.concat(sent);
        if (!sent.length) break;
      }
      now = await read();
    } finally { await pioUnmute(tun).catch(() => {}); }
    const left = differs(b, now);
    curPreset = b.p; S.curPre = b.p; S.sel = null; S.pendName = b.pend; hrSlot = b.slot;
    if (moved) edClear();
    if (now.caps.cur < 0) setModel(b.model);
    await again();
    if (!moved) { const e = b.edits; Object.assign(ED, { ...e, p: new Map(e.p), aeqB: new Set(e.aeqB), aeqV: e.aeqV.slice(), aeqS: e.aeqS.slice(), aeqT: e.aeqT.slice() }); renderSaveBar(); }       // also what was turned during the try is as it was
    if (moved && b.p >= 0) for (const m of marks) {             // what was not saved is not saved again
      if (m.p) edMark("p", { id: m.p[0], idx: m.p[1], v: m.p[2] });
      else if (m.on) edMark("on");
      else if (m.aeq) { if (m.aeq.length && edMark("aeq")) for (const k of m.aeq) { ED.aeqB.add(k); ED.aeqV[k] = b.live.aeq[k]; ED.aeqS[k] = ED.seq; ED.aeqT[k] = Date.now(); } }
      else if (m.other) edMark("other");
    }
    if (b.p < 0) edMark("other");
    return left;
  }
  /* The page reads what plays. */
  async function again() {
    await evPoll({ own: true });
    for (const f of [loadChain, stwLoad, () => loadAmpEq(true), loadMem, loadModelName, loadSnaps, loadPresets]) await Promise.resolve().then(f).catch(() => {});
    const g = / g=(-?\d+)\/(-?\d+)/.exec(reply(await Pedal.cmd("LVL", "LVL"), "LVL"));
    if (g) { S.gain = [+g[1], +g[2]]; buildGains(); }
  }
  async function inner(f) {
    txn++; pioBusy = true;
    if (trial) trial.inner++;
    try { return await f(); } finally { if (trial) trial.inner--; pioBusy = false; txn--; }
  }

  /* What would not come back: asked before, with the way to save it first. */
  function losses(b, item, stored) {
    const out = [], cabs = each(b.live).some(({ x }) => x.type === "ir" && !ownIr(x));
    if (item.kind === "preset") {
      if (b.p >= 0 && (!stored || stored[3].join() !== shape(b.live))) out.push({ key: "preset", text: `The blocks of ${home(b)} were changed and are not saved.` });
      if (b.p < 0 && /1/.test(b.scenes)) out.push({ key: "preset", text: "The preset that plays is in no slot: its scenes are not saved." });
    }
    const took = b.slots;
    if (b.caps.cur < 0 && b.live.amp.present && (item.kind === "capture" || item.kind === "preset" && (item.brings.capture || took && took[0] >= 0))) out.push({ key: "capture", text: `The amp capture that plays${S.model && S.model !== "—" ? ` ("${S.model}")` : ""} is in no slot.` });
    if (b.irs.cur < 0 && cabs && (item.kind === "ir" || item.kind === "preset" && (item.brings.ir || took && took[1] >= 0))) out.push({ key: "ir", text: "The cab IR that plays is in no slot." });
    return out;
  }
  /* The capture and the cab IR a stored preset brings, -1 for none. */
  async function slotsOf(n) {
    const m = (await Pedal.cmd("PLIST", doneBy("PLIST end", "PLIST fin"), 4000)).map(l => /^PRE (\d+) \d+ (-?\d+) (-?\d+) /.exec(l)).find(x => x && +x[1] === n);
    return m ? [+m[2], +m[3]] : null;
  }
  async function saveFirst(b, list) {
    for (const key of new Set(list.map(x => x.key))) {
      if (key === "preset") {
        if (b.p >= 0) await hrSave(); else await hrSaveTo();
        if (curPreset < 0 || edCount()) return false;
      } else {
        const cap = key === "capture", lib = cap ? b.caps : b.irs, slot = free(lib, lib.slots || (cap ? 15 : 8)), word = cap ? "CSAVE" : "ISAVE";
        if (slot < 0) { toast(`All the slots of ${cap ? "captures" : "cab IRs"} are in use: delete one first.`, "err"); return false; }
        const r = reply(await Pedal.cmd(`${word} ${slot} ${cap ? pioAscii(S.model, 23) || "Capture" : "Cab IR"}`, word, 8000), word);
        if (!r.startsWith(word + " ok")) { toast("It was not saved: " + errText(r || "ERR no answer"), "err"); return false; }
        if (cap) S.capSlot = slot;
        toast(`Saved in slot ${slot + 1}.`, "ok");
      }
    }
    return true;
  }
  async function base(item) {
    for (;;) {
      const list = await readPlist();
      if (!list.ok) throw new Error("the presets could not be read");
      const b = await inner(() => read()), entry = list.list.find(x => x[0] === b.p);
      Object.assign(b, { edits: changes(), pend: S.pendName, slot: hrSlot, model: S.model, list: list.list, slots: entry ? await slotsOf(b.p) : null });
      const lost = losses(b, item, entry);
      if (!lost.length) return b;
      const how = await uiChoice({ title: "Try it without losing anything?", body: lost.map(x => x.text).join("\n") + "\nIt cannot come back after the try.",
        choices: [{ label: "Save it first", value: "save", primary: true }, { label: "Try anyway", sub: "What is not saved is lost", value: "go" }] });
      if (how === "go") { b.lost = lost.map(x => x.key); return b; }
      if (how !== "save" || !await saveFirst(b, lost)) return null;
    }
  }

  /* The volume: from quiet to the preset's own, and never above the limit. It stops where the output is near full scale, or when the person says so. */
  async function gainTo(out) {
    const r = await line(pioSendLive, `GAIN ${trial.vol.in} ${out}`, "GAIN"), g = pioGain(r);
    if (g && trial) { trial.vol.now = g[1]; S.gain = g; if (S.gainK) S.gainK.forEach((k, i) => k.show(g[i])); draw(); }
  }
  async function rise() {
    const run = ++trial.vol.run, mine = () => trial && trial.vol.run === run && trial.state === "playing" && S.connected;
    trial.vol.rising = true; trial.vol.held = ""; draw();
    let clips = null;
    while (mine() && trial.vol.now < trial.vol.own) {
      await wait(EVERY);
      if (!mine()) return;
      if (Pedal.busy || drag || document.visibilityState === "hidden") continue;
      const l = await line(pioSendLive, "LVL", "LVL", 800), m = / out=(-?\d+) ci=\d+ co=(\d+) .* g=(-?\d+)\/(-?\d+)/.exec(l), s = / s=(-?\d+)/.exec(l), lim = / lim=(-?\d+)/.exec(l);
      if (!mine() || !m) continue;
      if (+m[4] !== trial.vol.now || s && +s[1] !== trial.scene) { trial.vol.now = +m[4]; trial.vol.in = +m[3]; trial.scene = s ? +s[1] : trial.scene; break; }       // a scene, or the knob of the volume: it is theirs now
      const loud = +m[1] > NEAR || clips !== null && +m[2] > clips || lim && +lim[1] < 0;
      clips = +m[2];
      if (loud) { trial.vol.held = "it is loud"; await gainTo(Math.max(START, trial.vol.now - STEP)); break; }
      await gainTo(Math.min(trial.vol.own, trial.vol.now + STEP));
    }
    if (trial && trial.vol.run === run) { trial.vol.rising = false; draw(); }
  }
  async function turn(by) {
    if (!trial || trial.state !== "playing" || trial.working) return;
    trial.vol.run++; trial.vol.rising = false; trial.vol.held = "";
    await line(pioSendLive, "GAIN", "GAIN");
    await gainTo(pioClamp(trial.vol.now + by, START, trial.vol.limit));
  }

  /* What is tried goes to the pedal. Each leaves trial.vol and trial.expect (the preset number the pedal says while it plays).
   * A scene of a preset that is loading is kept in the pedal's memory as long as no preset is chosen there. The pedal is muted by its tuner meanwhile, and
   * with the tuner on no switch chooses a preset, the first press closes it (tools/check_mini_panel.py, check_mini_scenes.py): a scene is sent only while the tuner is
   * on, right after the pedal said so. The names of
   * the scenes and the colour, which would go to a preset chosen in between, are sent when the preset is kept. */
  const careful = async (text, until, ms) => {
    if (!trial || trial.stop) throw new Stopped();
    if (/^SNAPSAVE /.test(text) && !trial.tuner) throw new Error("a switch was pressed on the pedal");
    const piece = /^(IRB|LDB) (\d+) ([0-9a-f]+)$/.exec(text);
    for (let k = 0; ; k++) {
      const lines = await pioSendLive(text, until, ms);
      if (piece && k < 3 && +pioFind(lines, `OK ${piece[1]} ${piece[2]} `).split(" ").pop() !== piece[3].length / 2) continue;      // a byte was lost on the way: the same piece again
      const wrote = /^SNAPSAVE /.test(text) ? /preset=(\d+)/.exec(pioFind(lines, "SNAPSAVE")) : null;
      if (wrote) throw new Error(`a preset was chosen on the pedal: look at the scenes of ${slotTxt(+wrote[1])}`);
      if (text === "LVL") trial.tuner = / tu=1/.test(pioFind(lines, "LVL"));
      return lines;
    }
  };
  const unsaved = (text, until, ms) => (/^(?:CSAVE|ISAVE) /.test(text) ? Promise.resolve([text.split(" ")[0] + " ok, not sent"]) : careful(text, until, ms));
  const progress = fr => { if (trial) { trial.fr = fr; draw(); } };
  const quiet = async (b = trial.base) => { trial.vol = { in: b.live.gain[0], now: START, own: b.live.gain[1], limit: b.live.gain[1], run: trial.vol.run + 1, rising: false, held: "", file: b.live.gain[1] }; await line(pioSendLive, "GAIN", "GAIN"); await gainTo(START); };

  function plain(pre, cap, irs) {
    const sound = { ...pre.sound, amp: { ...pre.sound.amp } }, ref = b => b.ir || pre.sound.cab_ir;
    const main = irs.find(x => pre.sound.cab_ir && x.key === pre.sound.cab_ir.attachment) || irs[0] || null;
    if (cap) sound.amp.capture = null;
    if (main) {
      const one = b => (b.type !== "ir" ? b : { ...b, ir: ref(b) && irs.some(x => x.key === ref(b).attachment) ? null : ref(b) });
      sound.chain = pre.sound.chain.map(b => (b.split ? { ...b, split: { a: b.split.a.map(one), b: b.split.b.map(one) } } : b.type ? one(b) : b));
      sound.cab_ir = null;
      sound.scenes = pre.sound.scenes.map(s => ({ ...s, blocks: Object.fromEntries(Object.entries(s.blocks).map(([id, b]) => {
        const came = b.ir && irs.find(x => x.key === b.ir.attachment), { ir, ...rest } = b;
        return [id, came ? came.key === main.key ? { ...rest, ir: null } : rest : b];
      })) }));
    }
    return { pre: { ...pre, sound }, main };
  }
  /* The mute of the loading is taken away; false when the pedal did not say so. Until it does the tuner that is on is the mute, not the pedal's own
   * (S.saveMute): the page would open its tuner for it when the cable comes back, and switch it on again. */
  let mutedUntil = 0;
  async function unmute(t) {
    let off = !t;
    if (t) try { off = /^TUNER /.test(reply(await Pedal.cmd(`TUNER ${t[1]} ${t[2]} ${t[3]}`, "TUNER"), "TUNER")); } catch (e) { /* the cable */ }
    S.saveMute = !off;
    if (off) mutedUntil = performance.now() + 2000;                  // a level that was asked before may still say that the tuner is on
    return off;
  }
  async function playPreset(item) {
    const caps = pioLib(await careful("CLIST", PIO_LIBEND("CLIST"), 3000), true), irs = pioLib(await careful("ILIST", PIO_LIBEND("ILIST"), 3000), false);
    if (!caps.full || !irs.full) throw new Error("the slots could not be read");
    const ctx = { ...pioCtxOf(caps, irs), scap: false }, brought = pioAttsOf(item.pre, item.doc).map(x => ({ ...x, check: pioAttCheck(x.a) })), good = brought.filter(x => x.check.ok).map(x => ({ key: x.key, role: x.role, a: x.a, data: x.check.data }));
    ctx.att = {};
    if (good.length) for (const s of (await pioAttPlace(good, careful, ctx)).same) ctx.att[s.key] = s.slot;       // the same file is on the pedal already
    const fresh = good.filter(x => !(x.key in ctx.att)), cap = fresh.find(x => x.role === "capture" && x.key === (item.pre.sound.amp.capture || {}).attachment) || null, made = plain(item.pre, cap, fresh.filter(x => x.role === "ir")), plan = pioPlan(made.pre, ctx);
    const limit = Math.max(0, trial.base.live.gain[1]), outs = plan.cmds.filter(c => /^GAIN /.test(c.line)).map(c => c.line.split(" ").map(Number)), cut = Math.max(0, ...outs.map(g => g[2] - limit));
    trial.after = plan.cmds.filter(c => /^(?:SNAPNAME|PCOLOR) /.test(c.line)).map(c => c.line);
    plan.cmds = plan.cmds.filter(c => !/^(?:SNAPNAME|PCOLOR) /.test(c.line));
    trial.names = plan.scenes;
    for (const c of plan.cmds) { const g = /^GAIN (-?\d+) (-?\d+)$/.exec(c.line); if (g) c.line = `GAIN ${g[1]} ${Math.max(START, +g[2] - cut)}`; }
    const last = outs.length ? outs[outs.length - 1] : [0, 0, 0], own = Math.max(START, last[2] - cut);
    const tun = await pioMute();
    let res;
    trial.expect = -1; trial.replaced = true; trial.muted = tun;
    try {
      await aeqSettle();
      if (!/^PNEW ok/.test(await line(careful, "PNEW", "PNEW", 3000))) throw new Error("no answer");
      await careful("FXS", PIO_FXS_END, 2500); await careful("SNAPS", "SNAPS");
      edClear();
      trial.vol.run++;
      if (cap) { await pioAttUpload(unsaved, cap, 0, { maxLine: Pedal.tr.maxLine, audioOn: S.audio === 2 }, fr => progress(fr * .4)); setModel(pioText(cap.a.name, 23) || "Capture"); S.capSlot = -1; }
      if (made.main) await pioAttUpload(unsaved, made.main, 0, { maxLine: Pedal.tr.maxLine, audioOn: S.audio === 2 }, fr => progress(.4 + fr * .2));
      res = await pioRun(plan, careful, ctx, (k, n) => progress(.6 + .4 * k / n));
      await careful("LVL", "LVL");
      trial.vol = { in: last[1], now: START, own, limit, run: trial.vol.run + 1, rising: false, held: "", file: own };
      await gainTo(START);
      await hrStillNew(careful);
    } finally { if (await unmute(tun) && trial) trial.muted = null; }
    curPreset = -1; S.curPre = -1; S.sel = null; hrSlot = -1; S.pendName = pioAscii(item.name, 23);
    trial.ir = made.main;
    trial.extra = fresh.filter(x => x.role === "ir" && x !== made.main);
    const said = w => T(w.k, { ...w, why: w.why ? T(w.why) : "" });
    trial.notes = [...(item.pre.left ? ["Parts of the file that this version does not understand are left out."] : []), ...(brought.length > good.length ? ["A file inside is damaged and is left out."] : []), ...(cut ? [`Its output is ${cut} dB louder than the limit and is lowered by that.`] : []),
      ...(item.pre.sound.scenes.some(s => s.capture) ? ["Scenes of it have captures of their own: while you try they play the preset's. Import the file to have them."] : []),
      ...(trial.extra.length ? ["It brings more than one cab IR: while you try, one of them plays in all the cab blocks."] : []), ...[...plan.warn, ...res.warn].map(said)];
  }
  async function playCapture(item, file) {
    const b = trial.base, now = await read(careful);
    await quiet();
    if (!now.live.amp.present) { await line(careful, "AMPX 1", "AMPX", 3000); trial.undo.push("AMPX 0"); }
    if (!now.live.amp.present || now.live.amp.on === 0) { await line(careful, "AMP 1", "AMP ", 3000); if (b.live.amp.present) trial.undo.push("AMP 0"); }
    await captureToSlot(file, null, (ph, fr) => progress(ph === "convert" ? fr * .5 : .5 + (fr || 0) * .5));
    trial.expect = b.p; trial.notes = [];
  }
  async function playIr(item, file) {
    const st = { q: null, cut: false, shortMem: false };
    await quiet();
    await irSend(file, null, fr => progress(fr * .9), st);
    const now = await read(careful), cabs = each(now.live).filter(k => k.x.type === "ir").map(k => k.x);
    if (!cabs.length) {
      const r = await line(careful, "FXA Q 99 ir", "FXA", 3000), m = /^FXA id=(\d+)/.exec(r);
      if (!m) throw new Error(isCpuErr(r) || isMemErr(r) ? "there is no room for a cab block in this preset" : errText(r || "ERR no answer"));
      trial.undo.push(`FXR ${m[1]}`);
    }
    for (const x of cabs) if (ownIr(x)) {
      const r = await line(careful, `FXIR ${x.id} -1`, "FXIR", 3000);
      if (!/^FXIR ok/.test(r)) throw new Error(errText(r || "ERR no answer"));
      trial.undo.push(`FXIR ${x.id} ${ownIr(x) - 1}`);
    }
    if (cabs.length && !cabs.some(x => x.on)) { await line(careful, `FXE ${cabs[0].id} 1`, "FXE", 3000); trial.undo.push(`FXE ${cabs[0].id} 0`); }
    trial.samples = st.q ? st.q.length : 0;
    trial.expect = trial.base.p;
    trial.notes = [...(cabs.length ? [] : ["This preset has no cab block: one is added while you try."]), ...(st.cut || st.shortMem ? ["It is longer than the pedal's memory for it and is shortened."] : [])];
  }

  async function load(at) {
    if (!trial || trial.working) return;
    const item = trial.items[at];
    trial.at = at; trial.state = "loading"; trial.working = true; trial.stop = false; trial.why = ""; trial.fr = 0; trial.notes = []; trial.vol.run++;
    draw();
    let why = null;
    trial.half = false;
    try {
      const got = await item.get();                                   // the file, when it is asked for: one at a time
      if (trial.stop) throw new Stopped();
      if (!S.connected) throw new Error("The pedal disconnected.");
      trial.half = true;
      await inner(async () => {
        if (trial.kind === "preset") await playPreset(item); else if (trial.kind === "capture") await playCapture(item, got); else await playIr(item, got);
        await again();
      });
    } catch (e) { why = e; }
    if (!trial) return;
    trial.working = false;
    if (!why) trial.half = false;
    if (why instanceof Stopped || trial.stop) return void back();
    if (why) return void fail(why);
    if (trial.kind === "preset" && trial.names.length) { for (const x of trial.names) S.snapNames[x.k] = x.name; renderPerf(); }      // shown here, and sent when it is kept
    trial.state = "playing"; trial.scene = S.snap; trial.gen = S.gen;
    Log.act("try_playing", { kind: trial.kind, at, of: trial.items.length, notes: trial.notes.length });
    draw();
    void rise().catch(() => {});
  }
  /* It could not be played: the pedal plays what it did before, and another one can be tried. */
  async function fail(e) {
    const text = String(e && e.message || e);
    Log.act("try_failed", { kind: trial.kind, at: trial.at, why: text.slice(0, 160) });
    if (!S.connected) { trial.state = "lost"; draw(); return; }
    trial.working = true; trial.state = "back"; draw();
    let left = null;
    try { left = await inner(() => putBack(trial.base, trial.undo, trial.replaced)); trial.undo = []; trial.replaced = false; } catch (x) { left = S.connected ? ["what plays"] : null; }
    if (trial && trial.muted && S.connected && await unmute(trial.muted) && trial) trial.muted = null;
    if (!trial) return;
    trial.working = false;
    if (!left) { trial.state = "lost"; draw(); return; }
    trial.state = "failed"; trial.why = errText(text).replace(/^Error: /, "") + (left.length ? `. Not as before: ${left.join(", ")}.` : "");
    draw();
  }
  async function back() {
    if (!trial) return;
    if (trial.working) { trial.stop = true; trial.leaving = true; draw(); return; }
    if (trial.state === "failed") return end();
    if (trial.state === "lost" && !S.connected) return end();
    const b = trial.base;
    trial.working = true; trial.state = "back"; trial.vol.run++;
    draw();
    let left = null, err = "";
    try { left = await inner(() => putBack(b, trial.undo, trial.replaced)); } catch (e) { err = String(e && e.message || e); }
    if (!trial) return;
    trial.working = false;
    Log.act("try_back", { kind: trial.kind, left: left || undefined, err: err || undefined });
    if (err) { if (!S.connected) { trial.state = "lost"; draw(); return; } trial.state = "playing"; draw(); toast(`It could not go back: ${errText(err)}. Try again, or choose a preset.`, "err"); return; }
    end();
    const not = left.concat((b.lost || []).includes("capture") && b.caps.cur < 0 && !left.includes("the capture") && b.live.amp.present ? ["the capture"] : [], (b.lost || []).includes("ir") && b.irs.cur < 0 && !left.includes("the cab IR") ? ["the cab IR"] : []);
    if (not.length) toast(`Back to ${home(b) || "what played before"}. Not as before: ${not.join(", ")}.`, "warn"); else toast(`Back to ${home(b) || "what played before"}, as it was.`, "ok");
  }
  function end() { const t = trial; trial = null; if (t) { t.vol.run++; if (t.muted) S.saveMute = false; } draw(); hrSaveBar(); renderPresets(); }

  /* Where to keep it: a name and a slot, the first that is free. */
  async function slotForm(title, name0, rows, n, first, skip) {
    const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
    const held = new Map(rows.map(x => [x.slot, x.name]));
    let name = null, slot = null;
    const pick = await uiForm({
      title, okLabel: "Keep", build: box => {
        name = mk("input"); name.type = "text"; name.maxLength = 23; name.autocomplete = "off"; name.value = name0;
        slot = mk("select", "mdlg-sel");
        for (let k = 0; k < n; k++) if (k !== skip) { const o = mk("option", "", `${k + 1} · ${held.get(k) || "free"}`); o.value = String(k); slot.append(o); }
        slot.value = String(first >= 0 ? first : 0);
        const note = mk("p", "hrnote"), say = () => { note.textContent = held.has(+slot.value) ? `Replaces "${held.get(+slot.value)}". Presets that use it will play this.` : ""; };
        slot.onchange = say; say();
        const field = (text, e) => { const w = mk("label", "mdlg-fld"); w.append(mk("span", "", text), e); return w; };
        box.append(field("Name", name), field("Slot", slot), note);
        return { first: name };
      },
      submit: async () => ({ slot: +slot.value, name: pioAscii(name.value, 23) || name0 || "Untitled" }),
    });
    if (!pick) return null;
    if (held.has(pick.slot) && !await uiConfirm({ title: "Replace it?", body: `"${held.get(pick.slot)}" in slot ${pick.slot + 1} is replaced with "${pick.name}".`, okLabel: "Replace", danger: true })) return null;
    return pick;
  }
  async function risen() { for (let k = 0; trial && trial.vol.rising && k < 100; k++) await wait(100); }
  async function keep() {
    if (!trial || trial.state !== "playing" || trial.working || trial.keeping) return;
    trial.keeping = true; draw();
    try { if (trial.kind === "preset") await keepPreset(); else await keepFile(trial.kind === "capture"); }
    catch (e) { toast("It was not kept: " + errText(String(e && e.message || e)), "err"); }
    finally { if (trial) { trial.keeping = false; trial.open = false; draw(); } }
  }
  async function keepPreset() {
    const t = trial, item = t.items[t.at];
    t.open = true;
    S.pendName = S.pendName || pioAscii(item.name, 23);
    await hrSaveTo();
    if (trial !== t || curPreset < 0) return;
    const n = curPreset;
    Log.act("try_kept", { kind: "preset", n });
    for (const c of t.after) if (S.curPre === n) await line(pioSendLive, c, c.split(" ")[0]);
    end();
    await loadSnaps().catch(() => {});
    await loadPresets().catch(() => {});
    if (item.kept && curPreset === n) try { item.kept(n, presetName()); } catch (e) { /* only a note */ }
  }
  /* Asked by the page's own save, before it writes the preset: the cab IR that has no slot, the ones that did not play, and the volume as it is heard. */
  async function beforeSave() {
    if (!trial || trial.kind !== "preset") return;
    await risen();
    if (trial.vol.now !== trial.vol.file) edMark("on");
    const put = async (name, samples) => {
      const lib = pioLib(await Pedal.cmd("ILIST", PIO_LIBEND("ILIST"), 3000), false), short7 = samples > IR_CAP_LAST, slot = free(lib, short7 ? 7 : lib.slots || 8);
      if (slot < 0) { toast(`The cab IR "${short(name, 30)}" was not kept: all the slots are in use.`, "warn"); return -1; }
      const r = reply(await Pedal.cmd(`ISAVE ${slot} ${pioAscii(name, 23) || "Cab IR"}`, "ISAVE", 8000), "ISAVE");
      if (!r.startsWith("ISAVE ok")) throw new Error(r || "no answer");
      return slot;
    };
    if (!trial.ir) return;
    const all = [trial.ir, ...trial.extra], names = all.map(x => `"${short(x.a.name, 30)}"`).join(", ");
    if (!await uiConfirm({ title: all.length > 1 ? "Keep the cab IRs too?" : "Keep the cab IR too?", body: `The preset plays with ${names}, which ${all.length > 1 ? "are" : "is"} not in your library. Without, the preset will not bring this sound back.`, okLabel: "Save in free slots", cancelLabel: "Only the preset" })) return;
    const main = await put(trial.ir.a.name, trial.ir.data.length / 2);
    for (const x of trial.extra) {
      const ids = irIds(trial.items[trial.at].pre, x.key);
      await pioAttUpload(unsaved, x, 0, { maxLine: Pedal.tr.maxLine });
      const slot = await put(x.a.name, x.data.length / 2);
      if (slot >= 0) for (const id of ids) await line(pioSendLive, `FXIR ${id} ${slot}`, "FXIR", 3000);
    }
    if (trial.extra.length && main >= 0) await Pedal.cmd(`ILOAD ${main}`, "ILOAD", 8000);
    await loadChain().catch(() => {});
    trial.ir = null;
  }
  /* The blocks of the pedal that a file's cab IR is for: the cab blocks in their order. */
  function irIds(pre, key) {
    const want = [], walk = list => { for (const b of list) if (b.split) { walk(b.split.a); walk(b.split.b); } else if (b.type === "ir") { const r = b.ir || pre.sound.cab_ir; want.push(!!r && r.attachment === key); } };
    walk(pre.sound.chain);
    const have = ["P", "Q"].flatMap(b => S.chain[b]).filter(x => x.type === "ir");
    return have.length === want.length ? have.filter((x, i) => want[i]).map(x => x.id) : [];
  }
  async function keepFile(cap) {
    const t = trial, item = t.items[t.at], word = cap ? "CSAVE" : "ISAVE", lib = pioLib(await Pedal.cmd(cap ? "CLIST" : "ILIST", PIO_LIBEND(cap ? "CLIST" : "ILIST"), 3000), cap);
    if (!lib.full) throw new Error("ERR the slots could not be read");
    const skip = !cap && t.samples > IR_CAP_LAST ? 7 : -1, n = lib.slots || (cap ? 15 : 8), pick = await slotForm(cap ? "Keep this capture" : "Keep this cab IR", pioAscii(item.name, 23), lib.list, n, free(lib, skip === 7 ? 7 : n), skip);
    if (!pick || trial !== t) return;
    if (t.state !== "playing" || S.curPre !== t.expect) { toast("It was not kept: another preset was chosen on the pedal.", "err"); return; }
    t.open = true;
    const r = reply(await Pedal.cmd(`${word} ${pick.slot} ${pick.name}`, word, 8000), word);
    if (!r.startsWith(word + " ok")) { toast("It was not kept: " + errText(r || "ERR no answer"), "err"); return; }
    if (cap) { S.capSlot = pick.slot; setModel(pick.name); await hrCapCame(); }
    Log.act("try_kept", { kind: t.kind, slot: pick.slot });
    await risen();
    await line(pioSendLive, `GAIN ${t.base.live.gain[0]} ${t.base.live.gain[1]}`, "GAIN");                                  // the volume of the preset is the preset's
    if (item.kept) try { item.kept(pick.slot, pick.name); } catch (e) { /* only a note */ }
    end();
    await inner(again);
    edMark("other");
    const where = home(t.base);
    toast(`"${pick.name}" is kept in slot ${pick.slot + 1}.` + (where ? ` Save the preset to use it in ${where}.` : ""), "ok");
  }

  /* The pedal does something by itself while a sound is tried: another preset, or it is gone and comes back. */
  async function gone() {
    const t = trial, b = t.base, cap = t.kind !== "ir", ir = t.kind !== "capture";
    let held = false;
    trial.working = true; trial.vol.run++;
    try {
      await inner(async () => {
        const now = await read(), has = await slotsOf(now.p), list = await readPlist(), entry = l => JSON.stringify(l.find(x => x[0] === now.p) || null);
        held = t.kind === "preset" && now.p >= 0 && list.ok && entry(list.list) !== entry(b.list);         // a switch that was held saved it there
        if (held) { S.pendName = ""; await again(); return; }
        // what the preset that was chosen has not of its own is as it was before the try
        if (cap && b.caps.cur >= 0 && now.caps.cur !== b.caps.cur && !(has && has[0] >= 0)) await Pedal.cmd(`CLOAD ${b.caps.cur}`, "CLOAD", 8000);
        if (ir && b.irs.cur >= 0 && now.irs.cur !== b.irs.cur && !(has && has[1] >= 0)) await Pedal.cmd(`ILOAD ${b.irs.cur}`, "ILOAD", 8000);
        S.pendName = ""; hrSlot = -1;
        await again();
      });
    } catch (e) { /* it is said below */ }
    if (trial !== t) return;
    Log.act("try_gone", { kind: t.kind, p: S.curPre, held });
    end();
    if (held) { toast(`The pedal saved it in ${slotTxt(S.curPre)}.` + (S.capSlot < 0 || t.ir ? " What it brings has no slot yet: Save as keeps that too." : ""), "ok"); return; }
    toast("Another preset was chosen on the pedal. The try has ended, and nothing of it was saved.", "info");
  }
  async function found() {
    const t = trial;
    trial.working = true;
    let there = false;
    try {
      const now = await inner(() => read());
      there = now.gen >= (t.gen || t.base.gen) && (t.half || now.p === t.expect && (t.kind === "preset" || (t.kind === "capture" ? now.caps : now.irs).cur < 0));
      if (there && trial === t && !t.half) { trial.vol.in = now.live.gain[0]; trial.vol.now = now.live.gain[1]; trial.gen = now.gen; S.pendName = t.kind === "preset" ? pioAscii(t.items[t.at].name, 23) : S.pendName; }
    } catch (e) { there = null; }
    if (trial !== t) return;
    if (there === null) { trial.working = false; return; }                // asked again at the next turn
    if (there && t.muted && await unmute(t.muted)) t.muted = null;         // still working: the turn that asks whether the pedal is back must not start this again
    if (trial !== t) return;
    trial.working = false;
    if (there && t.half) { await fail(new Error("the pedal was disconnected")); return; }
    if (there) { trial.state = "playing"; draw(); renderPresets(); return; }
    end();
    toast("The pedal started again with its own presets. Nothing of what you tried was saved.", "info");
  }
  setInterval(() => {
    if (!trial || trial.working) return;
    if (!S.connected) { if (trial.state !== "lost") { trial.state = "lost"; trial.vol.run++; trial.vol.rising = false; draw(); } return; }
    if (trial.state === "lost") { if (!S.connecting && !txn && !refreshing && typeof lvlTimer !== "undefined" && lvlTimer && S.gen != null && Object.keys(S.types).length) void found(); return; }
    if (trial.state === "playing" && !trial.keeping && !txn && S.curPre != null && S.curPre !== trial.expect) void gone();
  }, 250);

  /* The bar. */
  const bar = el("div", { id: "hrTry", role: "status", hidden: true });
  const name = el("b"), about = el("span", { class: "tabout" }), notes = el("span", { class: "tnotes" }), from = el("a", { target: "_blank", rel: "noopener noreferrer", hidden: true });
  const button = (text, cls, f) => el("button", { type: "button", class: "btn mini" + (cls ? " " + cls : ""), text, onclick: f });
  const prev = button("Previous", "", () => void step(-1)), next = button("Next", "", () => void step(1)), less = button("Quieter", "", () => void turn(-TURN)), more = button("Louder", "", () => void turn(TURN)), level_ = el("span", { class: "tvol" });
  const backB = button("Back", "", () => void back()), keepB = button("Keep…", "primary", () => void keep());
  bar.append(el("span", { class: "ttext" }, name, about, from, notes), el("span", { class: "tgroup", role: "group", "aria-label": "Which one" }, prev, next), el("span", { class: "tgroup", role: "group", "aria-label": "Volume" }, less, level_, more), el("span", { class: "tgroup" }, backB, keepB));
  document.querySelector(".top").after(bar);
  const set = (e, text) => { if (e.textContent !== text) e.textContent = text; };
  function draw() {
    bar.hidden = !trial;
    document.body.classList.toggle("hrtrying", !!trial);
    if (!trial) return;
    const item = trial.items[trial.at], many = trial.items.length > 1, b = trial.base, way = home(b), s = trial.state;
    bar.dataset.state = s;
    set(name, (s === "loading" ? "Loading " : s === "failed" ? "Not played: " : s === "back" ? "Going back" : "Trying ") + (s === "back" ? (way ? ` to ${way}…` : "…") : `“${short(item.name, 46)}”`));
    set(about, s === "back" ? "" : [many ? `${trial.at + 1} of ${trial.items.length}` : "", item.by ? `by ${short(item.by, 40)}` : "", item.license ? short(item.license, 40) : "",
      s === "loading" ? (trial.leaving ? "stopping…" : trial.fr ? Math.round(100 * trial.fr) + " %" : "") : s === "failed" ? trial.why : s === "lost" ? "The pedal is disconnected. What you tried is not saved on it." : "not saved on the pedal"].filter(Boolean).join(" · "));
    from.hidden = !(item.address && s !== "back");
    if (item.address) { from.href = item.address; set(from, "See it"); }
    set(notes, s === "playing" && trial.notes.length ? trial.notes.join(" ") : "");
    notes.title = notes.textContent;
    const ready = !trial.working && !trial.keeping && S.connected, playing = s === "playing";
    prev.hidden = next.hidden = !many;
    prev.disabled = !(ready && (playing || s === "failed") && trial.at > 0); next.disabled = !(ready && (playing || s === "failed") && trial.at < trial.items.length - 1);
    less.disabled = !(ready && playing && trial.vol.now > START); more.disabled = !(ready && playing && trial.vol.now < trial.vol.limit);
    set(level_, playing ? dB(trial.vol.now) + (trial.vol.rising ? ", rising" : trial.vol.held ? `, ${trial.vol.held}` : "") : "");
    set(backB, s === "failed" || s === "lost" ? "Close" : s === "loading" ? "Stop" : way ? `Back to ${way}` : "Back");
    backB.disabled = s === "back" || !!trial.leaving || !!trial.keeping || trial.working && s !== "loading";
    keepB.hidden = s === "failed" || s === "lost";
    keepB.disabled = !(ready && playing);
    prev.title = many && trial.at > 0 ? trial.items[trial.at - 1].name : ""; next.title = many && trial.at < trial.items.length - 1 ? trial.items[trial.at + 1].name : "";
  }
  async function step(by) {
    if (!trial || trial.working || trial.keeping || !["playing", "failed"].includes(trial.state) || !trial.items[trial.at + by]) return;
    await load(trial.at + by);
  }

  /* items: { kind, name, by, license, address, get(), kept(slot, name) }, and for a preset { pre, doc, brings: {capture, ir} }. */
  async function start(kind, items, at = 0) {
    if (trial) { toast(FIRST, "err"); return false; }
    if (DEMO || !S.connected) { toast("Connect the pedal first.", "err"); return false; }
    if (hrOther.kind) { toast("Update your pedal first.", "err"); return false; }
    if (starting || pioBusy || saveRun || hrSaving || capJobs) { toast(BUSY, "err"); return false; }
    starting = true;
    try {
      for (let k = 0; k < 40 && (txn || refreshing || Pedal.busy); k++) await wait(100);
      await aeqSettle();
      const all = items.reduce((o, i) => ({ capture: o.capture || !i.brings || i.brings.capture, ir: o.ir || !i.brings || i.brings.ir }), {}), b = await base({ ...items[at], brings: all });
      if (!b) return false;
      if ($("lib").classList.contains("on")) closeLib();
      trial = { kind, items, at, base: b, state: "starting", working: false, inner: 0, undo: [], notes: [], extra: [], expect: b.p, vol: { in: b.live.gain[0], now: b.live.gain[1], own: b.live.gain[1], limit: b.live.gain[1], run: 0, rising: false, held: "" } };
      Log.act("try_start", { kind, n: items.length, p: b.p, edits: edCount(), lost: b.lost });
      if (edCount() && kind === "preset" && b.p >= 0) toast(`Your changes in ${home(b)} that are not saved come back with Back.`, "info");
    } catch (e) { toast("What plays now could not be read: " + errText(String(e && e.message || e)), "err"); return false; }
    finally { starting = false; }
    draw(); hrSaveBar();
    await load(at);
    return true;
  }

  /* Files. A preset is read strictly, and what it lacks on this pedal is shown before it is tried. */
  const has = (lib, ref) => { const m = pioMatch(ref, lib); return !!m; };
  async function libraries() {
    const caps = pioLib(await pioSendLive("CLIST", PIO_LIBEND("CLIST"), 3000), true), irs = pioLib(await pioSendLive("ILIST", PIO_LIBEND("ILIST"), 3000), false);
    if (!caps.full || !irs.full) throw new Error("the slots could not be read");
    return { caps, irs };
  }
  function lacks(pre, doc, libs) {
    const in_ = ref => !!ref.attachment && Object.prototype.hasOwnProperty.call(doc.attachments, ref.attachment);
    const n = HyperRigPresetFile.needs(pre, { type: t => Object.prototype.hasOwnProperty.call(S.types, t), capture: r => in_(r) || has(libs.caps, r), ir: r => in_(r) || has(libs.irs, r) });
    return [n.effects.length ? `effects this HyperRig does not have: ${n.effects.map(x => short(x, 20)).join(", ")}` : "", n.captures.length ? `the capture "${n.captures.map(x => short(x, 30)).join('", "')}"` : "", n.irs.length ? `the cab IR "${n.irs.map(x => short(x, 30)).join('", "')}"` : ""].filter(Boolean);
  }
  /* Presets of a text, as items; null when it is none. more: { by, license, address, title, kept }. */
  function presetItems(raw, more = {}) {
    const r = HyperRigPresetFile.clean(raw);
    if (!r.ok) return { err: r.err };
    return { warn: r.warn, items: r.presets.map(pre => {
      const o = pre.meta.origin || {}, n = HyperRigPresetFile.needs(pre, { type: () => true, capture: () => false, ir: () => false });
      return { kind: "preset", name: pre.meta.name, by: more.by || o.creator || pre.meta.author, license: more.license || o.license || "", address: more.address || o.address || "", description: pre.meta.description, pre, doc: r.doc, kept: more.kept, get: async () => pre,
        brings: { capture: n.captures.length > 0, ir: n.irs.length > 0 } };
    }) };
  }
  /* The list, with what each one lacks; the one to begin with. */
  async function chooseOne(items, warn, title) {
    const libs = await libraries(), mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
    let at = 0;
    return uiForm({
      title: title || (items.length > 1 ? `Try ${items.length} presets` : `Try "${short(items[0].name, 40)}"?`), okLabel: "Try", body: "You hear it at once, quietly at first. Nothing is saved on the pedal until you keep it.",
      build: box => {
        const list = mk("div", "hrtlist"); list.setAttribute("role", "radiogroup"); list.setAttribute("aria-label", "Preset");
        items.forEach((item, i) => {
          const row = mk("label", "hrtrow"), input = mk("input"), words = mk("span", "hrtwords"), missing = lacks(item.pre, item.doc, libs);
          input.type = "radio"; input.name = "hrtry"; input.checked = i === 0; input.onchange = () => { at = i; };
          words.append(mk("b", "", short(item.name, 60)));
          const sub = [item.by ? "by " + short(item.by, 40) : "", short(item.license, 60)].filter(Boolean).join(" · ");
          if (sub) words.append(mk("span", "", sub));
          if (item.description && items.length === 1) words.append(mk("span", "hrtdesc", pioText(item.description, 400)));
          if (missing.length) words.append(mk("span", "hrtlack", "Plays without " + missing.join("; ") + "."));
          row.append(input, words); list.append(row);
        });
        if (items.length === 1) list.classList.add("one");
        for (const w of warn) box.append(mk("p", "hrnote", w));
        box.append(list);
        return { first: list.querySelector("input") };
      },
      submit: async () => ({ at }),
    });
  }
  async function tryPresets(items, warn = [], title) {
    if (trial) { toast(FIRST, "err"); return false; }
    if (DEMO || !S.connected) { toast("Connect the pedal first.", "err"); return false; }
    let pick;
    try { pick = await chooseOne(items, warn, title); } catch (e) { toast("The pedal could not be read. Try again.", "err"); return false; }
    return pick ? start("preset", items, pick.at) : false;
  }
  async function files(kind, list) {
    const f = FILES[kind], good = [...list].filter(x => f.ends.test(x.name) && x.size <= f.most), bad = [...list].filter(x => !good.includes(x));
    if (bad.length) toast(bad.some(x => x.size > f.most) ? `"${short(bad.find(x => x.size > f.most).name, 40)}" is too large.` : `Skipped ${bad.length === 1 ? `"${short(bad[0].name, 40)}"` : bad.length + " files"}: choose ${f.say}.`, "err");
    if (!good.length) return false;
    if (kind !== "preset") return start(kind, good.map(x => ({ kind, name: x.name.replace(/\.[^.]+$/, ""), get: async () => x })));
    const items = [], warn = [];
    for (const x of good) {
      let r;
      try { r = presetItems(await x.text()); } catch (e) { r = { err: "This file could not be read." }; }
      if (r.err) toast(`"${short(x.name, 40)}": ${r.err}`, "err"); else { items.push(...r.items); warn.push(...r.warn); }
    }
    return items.length ? tryPresets(items.slice(0, 64), warn) : false;
  }
  function pick(kind) {
    if (trial) { toast(FIRST, "err"); return; }
    if (!S.connected) { toast("Connect the pedal first.", "err"); return; }
    const input = el("input", { type: "file", accept: FILES[kind].accept, multiple: true, hidden: true });
    input.onchange = () => { const list = [...input.files]; input.remove(); if (list.length) void files(kind, list); };
    input.oncancel = () => input.remove();
    document.body.append(input);
    input.click();
  }
  // The ways in: beside the import of presets, and in the libraries.
  const head = document.querySelector(".side .phd");
  if (head) head.after(el("div", { class: "hrways", id: "hrWays" }, el("button", { type: "button", class: "btn mini", id: "hrTryPreset", text: "Try from files…", title: "Hear presets from files on the pedal, without saving them", onclick: () => pick("preset") })));
  const add = document.getElementById("libAdd");
  if (add) add.after(el("button", { type: "button", class: "btn", id: "hrTryFile", text: "Try a file…", title: "Hear it on the pedal, without using a slot", onclick: () => pick(libKind === "cap" ? "capture" : "ir") }));

  /* While a sound is tried: the page's other ways of changing what plays, and everything that writes to the pedal, are for afterwards. */
  const GUARDED = { newPedalboard, pioPick, pioImport, pioExport, hrImportAll, uploadCaptures, uploadIrs, irPicked, useSlot, openCalib, hrUpdate };
  const instead = { newPedalboard: f => { newPedalboard = f; }, pioPick: f => { pioPick = f; }, pioImport: f => { pioImport = f; }, pioExport: f => { pioExport = f; }, hrImportAll: f => { hrImportAll = f; }, uploadCaptures: f => { uploadCaptures = f; },
    uploadIrs: f => { uploadIrs = f; }, irPicked: f => { irPicked = f; }, useSlot: f => { useSlot = f; }, openCalib: f => { openCalib = f; }, hrUpdate: f => { hrUpdate = f; } };
  for (const [k, f] of Object.entries(GUARDED)) instead[k](async function (...a) { if (trial || starting) { toast(FIRST, "err"); return false; } return f.apply(this, a); });
  const loadOther = loadPreset;                                        // a preset of the list: back first, then that one
  loadPreset = async function (n) {
    if (starting) return;
    if (trial) { if (trial.working || trial.keeping) { toast(BUSY, "err"); return; } await back(); if (trial) return; }
    return loadOther(n);
  };
  const STORES = /^(?:PSAVE|SNAPSAVE|SNAPDEL|PDEL|CSAVE|CDEL|ISAVE|IDEL)(?: |$)|^(?:SNAPNAME|PNAME|CTRIM) \d|^PCOLOR \S/, send = Pedal.cmd;
  Pedal.cmd = function (text, ...rest) {
    if (trial && !trial.open && !trial.inner && STORES.test(text)) { toast(FIRST, "err"); return Promise.resolve(["ERR " + text.split(" ")[0] + " a sound is being tried"]); }
    return send.call(this, text, ...rest);
  };
  const converted = new WeakMap(), convert = namToBlob;                // a capture is converted once, also when it is tried again
  namToBlob = async function (f, onProg) { if (!converted.has(f)) converted.set(f, await convert(f, onProg)); return converted.get(f); };
  // Leaving the page: asked first, and the port stays open when the answer is no.
  removeEventListener("beforeunload", pageGone);
  addEventListener("beforeunload", e => { if (trial) { e.preventDefault(); e.returnValue = ""; return; } pageGone(); });

  globalThis.hrTry = Object.freeze({ get on() { return !!trial || starting; }, get muted() { return !!(trial && trial.muted) || performance.now() < mutedUntil; }, get state() { return trial ? trial.state : "off"; }, get at() { return trial ? trial.at : -1; }, get volume() { return trial ? { ...trial.vol } : null; }, get notes() { return trial ? trial.notes.slice() : []; },
    start, files, step, back, keep, beforeSave, presetItems, tryPresets });
})();
