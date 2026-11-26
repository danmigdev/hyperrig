/* The same volume for every preset and scene (docs/MINI_LOUDNESS.md): the window. It records some strokes of the player's guitar, once; plays them on
 * the pedal into the scene, the preset or all the presets while the output is silent; shows how loud each is and the gain it would get; and
 * writes the gains that the person agrees to. While it measures, nothing on the pedal changes, and what played before comes back: the
 * firmware sees to that, also when the cable is pulled or a footswitch pressed. The numbers are made in product-loudness.js. */
(function () {
  "use strict";
  const L = globalThis.HyperRigLoudness, presets = document.getElementById("pList");
  if (!L || !presets) return;
  const KEPT = "hyperrig.loudness", MAX_SECONDS = 14, PATIENCE = 40, ENOUGH = 10, LEAST = 3, HARDLY = -62, SETTLED = 0.7, ECHO = 15, SILENT = -90;
  const SET = 2, RECORD = 5, MEASURE = 6, HEAD = 32, RING = 1024, RECORDING = HEAD + RING + 86, MEASURING = HEAD + 152;      // of the firmware: operations, and words of memory
  const WHY = {
    memory: "The pedal has no free memory for it. Load a preset with fewer blocks and try again.", engine: "The pedal's sound engine is not running. Load a preset and try again.",
    tuner: "The tuner is open. Close it and try again.", bypass: "The pedal is in bypass. Press the footswitch of the preset and try again.",
    off: "It was stopped from the pedal.", other: "Another preset or scene was chosen on the pedal.", lost: "Part of the recording was lost on the way. Try again.",
  };
  const kept = () => { try { const v = JSON.parse(localStorage.getItem(KEPT)); return v && typeof v === "object" ? v : {}; } catch (e) { return {}; } };
  const keep = more => { try { localStorage.setItem(KEPT, JSON.stringify({ ...kept(), ...more })); } catch (e) { /* it is asked again the next time */ } };
  const right = t => typeof t === "string" && t.length === L.STROKE && /^[0-9a-f]+$/.test(t);
  const own = () => { const g = kept().guitar; return g && Array.isArray(g.strokes) && g.strokes.length >= LEAST && g.strokes.every(right) ? g : null; };
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const el = (tag, attributes, ...children) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attributes || {})) if (k === "text") e.textContent = v; else if (k.startsWith("on")) e[k] = v; else if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? "" : v);
    e.append(...children.filter(c => c !== null && c !== undefined));
    return e;
  };
  class Stopped extends Error {}

  // The pedal. The firmware's diagnostic words lend the memory (REC, INJBEGIN), fill it (INJB) and read it (RECD); HRLV does the rest.
  async function ask(line, word, ms = 1500) {
    const lines = await Pedal.cmd(line, l => l.startsWith(word) || l.startsWith("ERR"), ms), r = reply(lines, word);
    if (!r) throw new Error("The pedal did not answer. Try again.");
    if (r.startsWith("ERR RECD")) throw new Stopped(WHY.off);                    // its memory was given back
    if (/^ERR (?:REC|INJBEGIN)\b.*memory/.test(r)) throw new Error(WHY.memory);
    if (r.startsWith("ERR")) throw new Error(errText(r));
    return r;
  }
  /* An operation, as bytes; how many slices or codes there are. Refused: a footswitch ended it, or the pedal did by itself. */
  const bytes = list => list.map(v => (v & 255).toString(16).padStart(2, "0")).join("");
  async function operate(list, ms) {
    const m = /^HRLV (-?\d+) (-?\d+)$/.exec(await ask(("HRLV " + bytes(list)).trim(), "HRLV", ms));
    if (!m) throw new Error("The pedal could not do it. Try again.");
    if (m[1] !== "0") throw list[0] === SET ? new Error(`The pedal did not save it (${m[1]}).`) : new Stopped(WHY.off);
    return +m[2];
  }
  /* The editor is there; whether the measure still is. */
  const alive = async () => { if (await operate([]) < 0) throw new Stopped(WHY.off); };
  async function words(at, count) {
    const out = [];
    while (out.length < count) {
      const m = /^RECD (\d+) ((?:[0-9a-f]{8})+)$/.exec(await ask(`RECD ${at + out.length}`, "RECD"));
      if (!m || +m[1] !== at + out.length) throw new Error("The pedal did not say all it measured. Try again.");
      for (const w of m[2].match(/.{8}/g)) out.push(parseInt(w, 16));
    }
    return out.slice(0, count);
  }
  const lvl = async () => reply(await Pedal.cmd("LVL", "LVL"), "LVL");
  /* What is done while the pedal lends its memory for it; the page does not read the pedal meanwhile. From the first word on the pedal ends it by itself. */
  async function session(memory, work) {
    let on = false;
    pioBusy = true; txn++;
    try {
      const m = / m=(\d) .* tu=(\d) .* fm=\d+,\d+,\d+,(\d)/.exec(await lvl());
      if (!m) throw new Error("The pedal did not answer. Try again.");
      if (m[2] !== "0") throw new Error(WHY.tuner);
      if (m[3] !== "0") throw new Error(WHY.bypass);
      if (m[1] !== "2") throw new Error(WHY.engine);
      await operate([]);
      on = true;
      await ask(`REC 4 ${memory}`, "REC tap");
      if (memory === MEASURING) await ask(`INJBEGIN ${L.STROKE / 4}`, "OK INJBEGIN");
      await wait(60);                                     // REC fills it with what it is for, once
      return await work();
    } finally {
      if (on && S.connected) try { await Pedal.cmd("HRLV 01", "HRLV", 4000); } catch (e) { /* the pedal ends it by itself */ }
      txn--; pioBusy = false;
    }
  }
  async function readAgain() {
    if (!S.connected) return;
    S.sel = null;
    txn++;
    try {
      await evPoll({ own: true });
      for (const read of [loadPresets, loadSnaps, loadChain, stwLoad, () => loadAmpEq(true), loadMem, loadModelName]) await Promise.resolve().then(read).catch(() => {});
      const g = /g=(-?\d+)\/(-?\d+)/.exec(await lvl());
      if (g) { S.gain = [+g[1], +g[2]]; buildGains(); }
    } catch (e) { /* the page finds out by itself */ } finally { txn--; }
    renderPresets(); renderSaveBar();
  }

  async function record(say, run) {
    const x = [], gaps = [], began = performance.now();
    /* Whole strokes: none that a gap is in, and none that a gap only looks like. */
    const whole = list => list.filter(s => !gaps.some(g => s.at + L.STROKE > g && s.at < g + 0.2 * L.LOW));
    let seen = [];
    await session(RECORDING, async () => {
      let coder = L.coder(), next = 0, from = 0, had = 0;      // codes that were read; where the last of it began, in codes and in samples
      await operate([RECORD]);
      for (let turn = 0; !run.stop; turn++) {
        const there = await operate([]);
        if (there < 0) throw new Stopped(WHY.off);
        if (there - from > 8 * RING - 64) {               // the computer was busy, and the last of it may be gone: from here on anew
          x.length = had;
          gaps.push(had);
          await operate([RECORD]);
          coder = L.coder(); next = from = 0;
          continue;
        }
        const seconds = x.length / L.LOW, end = seconds >= MAX_SECONDS || performance.now() - began > PATIENCE * 1000;
        if (turn % 8 === 7 || end) seen = whole(L.strokes(Float32Array.from(x)));
        say(seen.length, seconds);
        if (end || seen.length >= ENOUGH) break;
        from = next; had = x.length;
        while (next < there) {
          const at = next / 8 % RING, count = Math.min(24, RING - at, (there - next) / 8);
          for (const w of await words(HEAD + at, count)) for (let k = 0; k < 8; k++) x.push(coder.sample(w >>> 4 * k & 15) / 32768);
          next += 8 * count;
        }
      }
    });
    const sound = Float32Array.from(x), list = whole(L.strokes(sound)), level = L.median(list.map(s => s.level));
    Log.act("loudness_record", { strokes: list.length, seconds: +(x.length / L.LOW).toFixed(1), gaps: gaps.length, level: +level.toFixed(1) });
    if (run.stop && list.length < LEAST) throw new Stopped("");
    if (gaps.length > 5 && list.length < LEAST) throw new Error(WHY.lost);
    if (!list.length || level < HARDLY) throw new Error("The guitar was hardly heard. Is it plugged in, with its volume up?");
    if (list.length < LEAST) throw new Error(`Only ${list.length === 1 ? "one stroke was" : list.length + " strokes were"} heard. Play about one each second.`);
    const chosen = L.choose(list);
    return { strokes: chosen.map(s => L.hexOf(L.cut(sound, s.at))), heard: list.length, level, when: new Date().toISOString().slice(0, 10), loud: list.some(s => s.peak > 0.91) };
  }

  const PIECE = 88;                                       // bytes
  async function put(stroke, run) {
    const data = L.bytesOf(stroke);
    for (let at = 0; at < data.length / 2; at += PIECE) {
      if (run.stop) throw new Stopped("");
      if (at % (8 * PIECE) === 0) await alive();
      const part = data.slice(2 * at, 2 * (at + PIECE));
      let there = 0;
      for (let turn = 0; turn < 4 && there !== part.length / 2; turn++)         // a byte of a line can be lost on the way
        there = +(await ask(`INJB ${at} ${part}`, "OK INJB")).split(" ")[3];
      if (there !== part.length / 2) { await alive(); throw new Error("The pedal did not take the stroke. Try again."); }
    }
  }
  async function once(plays, run) {
    const total = L.slices(plays);
    await operate([MEASURE, L.PLAYED * 4, plays, L.BEFORE * 4, total]);
    const until = performance.now() + total * 512 / L.RATE * 1000;
    for (;;) {
      if (run.stop) throw new Stopped("");
      const left = until - performance.now();
      if (left > 0) { await wait(Math.min(left, 250)); continue; }
      if (left < -3000) throw new Error("The pedal did not finish. Try again.");
      const [done, peak, running] = await words(0, 3);
      if (running) { await wait(40); continue; }
      if (done !== total) throw new Stopped(WHY.off);
      const view = new DataView(new ArrayBuffer(4));
      return { peak, energies: (await words(HEAD, total)).map(w => { view.setUint32(0, w); return view.getFloat32(0); }) };
    }
  }
  /* Blocks of effects that were let by, and blocks that came late; what plays. */
  const state = async () => { const now = await lvl(); return [/ sk=\d+| und=\d+ ovl=\d+/g, / s=-?\d+| p=-?\d+/g].map(re => String(now.match(re))); };
  async function level(item, run) {
    for (let turn = 0; ; turn++) {
      const [before, playing] = await state();
      let plays = 2, r = await once(plays, run), v = L.result(r.energies, plays);
      for (let k = 0; k < 3 && v.before > v.level - ECHO; k++) { r = await once(plays, run); v = L.result(r.energies, plays); }       // echoes of what was there before
      if (v.apart > SETTLED) { plays = 3; r = await once(plays, run); v = L.result(r.energies, plays); }       // it was not settled
      const [after, still] = await state();
      if (still !== playing) throw new Stopped(WHY.other);
      if (after !== before) {
        if (!turn) continue;
        item.note = "The pedal had no time left to measure it.";
        return;
      }
      if (v.level < SILENT) { item.note = "Nothing is heard from it."; return; }
      item.levels.push(v.level);
      item.peak = Math.max(item.peak, r.peak);
      return;
    }
  }

  const gainNow = async () => { const m = /^GAIN in=(-?\d+) out=(-?\d+) dB/.exec(await ask("GAIN", "GAIN")); if (!m) throw new Error("The pedal did not say its gain. Try again."); return +m[2]; };
  /* What plays, in the pedal's words, without what it costs: whether a preset starts with one of its scenes. */
  async function sound() {
    const lines = (await Pedal.cmd("FXS", FXS_DONE, 2500)).filter(l => /^FX [PQ]|^FXS amp=|^FXMIX|^FXXO/.test(l)).map(l => l.replace(/ ticks=\d+/, "").replace(/ fu=\d+/, ""));
    return JSON.stringify([lines, await Pedal.cmd("AMPEQ", "AMPEQ"), await gainNow()]);
  }
  const bits = mask => [0, 1, 2, 3, 4, 5, 6, 7].filter(k => mask >> k & 1);
  async function measure(scope, strokes, say, run) {
    const names = new Map(plist.map(p => [p[0], p[1]])), order = scope === "all" ? plist.map(p => p[0]) : scope === "preset" ? [curPreset] : [-1];
    const items = [], plans = new Map(), missing = new Set();
    const masks = new Map(plist.map(p => [p[0], p[4]]));
    const expected = () => order.reduce((n, p) => n + (p < 0 ? 1 : plans.has(p) ? plans.get(p).length : Math.max(1, bits(masks.get(p) || 0).length)), 0) * strokes.length;
    let done = 0, limit = 0, limiter = false;
    const tell = item => say(done, expected(), item.preset < 0 ? "" : `${slotTxt(item.preset)} ${names.get(item.preset) || ""}${item.scene >= 0 ? `, scene ${item.scene + 1}` : ""}`);
    const make = (preset, scene, out) => { const item = { preset, scene, out, levels: [], peak: 0, note: "", by: 0 }; items.push(item); return item; };
    /* A preset can name a scene and start with another sound than that. The firmware brings back both by their numbers; the sound is looked at here. */
    const was = order[0] >= 0 && curPreset >= 0 ? [(await state())[1], await sound(), curPreset, S.snap] : null;
    const back = async () => {
      if (!was || !S.connected || (await state())[1] !== was[0] || await sound() === was[1]) return;
      await Pedal.cmd(`PLOAD ${was[2]}`, "PLOAD", 8000);
      if (was[3] >= 0 && await sound() !== was[1]) await Pedal.cmd(`SNAP ${was[3]}`, "SNAP ");
    };
    await session(MEASURING, async () => {
      const lim = /^LIM on=(\d) thr=(-?\d+)/.exec(reply(await Pedal.cmd("LIM", "LIM"), "LIM"));
      limiter = !!lim && lim[1] === "1";
      limit = limiter ? +lim[2] : 0;
      for (const [turn, stroke] of strokes.entries()) {
        await put(stroke, run);
        for (const n of order) {
          if (missing.has(n)) continue;
          if (n < 0) {                                    // the sound that plays, with what was changed and not saved
            const item = turn ? items[0] : make(curPreset, S.snap, await gainNow());
            tell(item); await level(item, run); done++;
            continue;
          }
          const load = async () => {
            await alive();
            const r = reply(await Pedal.cmd(`PLOAD ${n}`, "PLOAD", 8000), "PLOAD");
            const s = r.startsWith("PLOAD ok") ? /^SNAPS ([01]{8}) current=(-?\d+)/.exec(reply(await Pedal.cmd("SNAPS", "SNAPS"), "SNAPS")) : null;
            return s ? { r, s } : null;
          };
          const scene = async k => { await alive(); const r = reply(await Pedal.cmd(`SNAP ${k}`, "SNAP "), "SNAP "); if (!r.startsWith("SNAP ok")) throw new Error(errText(r)); };
          const at = await load();
          if (!at) { missing.add(n); make(n, -1, 0).note = "It could not be loaded."; continue; }
          if (!plans.has(n)) {
            const there = [...at.s[1]].map((c, k) => c === "1" ? k : -1).filter(k => k >= 0), cur = +at.s[2], plan = [];
            let base = true;
            if (cur >= 0) {
              const loaded = await sound();
              await scene(cur);
              base = await sound() !== loaded;
              if (!await load()) throw new Error("The pedal did not answer. Try again.");
            }
            if (base) plan.push(make(n, -1, await gainNow()));
            for (const k of there) plan.push(Object.assign(make(n, k, 0), { first: !base && k === cur }));
            for (const line of there.length ? await Pedal.cmd("SNAPNAME", doneBy("SNAPNAME end", "SNAPNAME fin")) : []) {
              const m = /^SNAPNAME ([0-7]) '(.+)'$/.exec(line), item = m && plan.find(i => i.scene === +m[1]);
              if (item) item.name = m[2];
            }
            const miss = /(?:missing|faltan)=([1-9]\d*)/.exec(at.r);
            if (miss) for (const item of plan) item.note = "Not measured: a block of it does not fit on the pedal.";
            plans.set(n, plan);
          }
          for (const item of plans.get(n)) {
            tell(item);
            if (item.scene >= 0) { await scene(item.scene); if (!turn) item.out = await gainNow(); }
            if (!item.note) await level(item, run);
            done++;
          }
        }
      }
    }).finally(() => back().catch(() => {}));
    for (const item of items) item.level = L.mean(item.levels);
    const good = items.filter(i => !i.note && i.levels.length === strokes.length);
    Log.act("loudness_measured", { scope, items: items.length, good: good.length, levels: good.slice(0, 40).map(i => [i.preset, i.scene, +i.level.toFixed(1), i.out, Math.round(L.decibels(i.peak))]) });
    return { items, good, limit, limiter, names };
  }
  /* The gains into the stored presets, one command for each; nothing else of them changes. */
  async function store(changes, say) {
    const order = [...new Set(changes.map(c => c.preset))];
    let done = 0;
    pioBusy = true; txn++;
    try {
      for (const n of order) {
        say(done, order.length);
        const gains = Array(9).fill(127);                 // a gain that stays
        for (const c of changes.filter(x => x.preset === n)) { gains[c.scene + 1] = c.gain; if (c.first) gains[0] = c.gain; }
        await operate([SET, n, ...gains], 8000);
        done++;
      }
      if (order.includes(curPreset)) {                    // what plays takes its new gain
        const scene = S.snap;
        await Pedal.cmd(`PLOAD ${curPreset}`, "PLOAD", 8000);
        await Pedal.cmd("SNAPS", "SNAPS");
        if (scene >= 0) await Pedal.cmd(`SNAP ${scene}`, "SNAP ");
      }
    } catch (e) { e.done = done; throw e; } finally { txn--; pioBusy = false; }
    return done;
  }

  // The window.
  let dialog = null, running = null;
  const number = v => (v < 0 ? "−" : v > 0 ? "+" : "") + Math.abs(v);
  const plain = v => (v < 0 ? "−" : "") + Math.abs(Math.round(v));
  const button = (text, cls, onclick, more) => el("button", { type: "button", class: "btn " + cls, text, onclick, ...more });
  function open() {
    if (dialog || pioBusy || saveRun || DEMO) return;
    if (!S.connected) { toast("Connect the pedal first.", "err"); return; }
    if (hrOther.kind) { toast("ERR MINI_APP another build", "err"); return; }
    dialog = el("dialog", { class: "hrvol", "aria-labelledby": "hrVolT" });
    dialog.addEventListener("cancel", e => { e.preventDefault(); running ? running.stop = true : close(); });
    dialog.addEventListener("keydown", e => e.stopPropagation());
    document.body.append(dialog);
    begin();
    dialog.showModal();
  }
  function close() { if (!dialog) return; dialog.close(); dialog.remove(); dialog = null; }
  const show = (...children) => dialog.replaceChildren(el("h2", { id: "hrVolT", text: "Level volumes" }), ...children);
  const note = (text, cls = "vnote") => el("p", { class: cls, text });

  let scope = "scene", built = "";
  function begin(message = "") {
    const g = own(), changed = curPreset < 0 || edCount() > 0, has = { scene: true, preset: curPreset >= 0, all: plist.length > 0 };
    const scenes = (S.snaps || []).some(Boolean), last = Number.isInteger(kept().volume) ? "To the volume of the last time." : "To a volume you choose.";
    if (!has[scope]) scope = "scene";
    const guitar = el("section", {}, el("h3", { text: "Your guitar" }));
    const sounds = el("select", { "aria-label": "Built-in strokes", onchange: e => { built = e.target.value; begin(); } },
      ...[["", g ? "Your guitar" : "Choose…"], ["soft", "Built-in, soft pickups"], ["medium", "Built-in, medium pickups"], ["hot", "Built-in, hot pickups"]].map(([v, t]) => el("option", { value: v, text: t, selected: v === built })));
    guitar.append(note(built ? "The pedal plays strokes that nobody played. Your own guitar is more accurate." : g ? `Recorded on ${g.when}: ${g.strokes.length} of the ${g.heard} strokes that were heard.` :
      "The pedal listens to your guitar once, for some ten seconds, and plays the strokes itself from then on.", ""),
      el("div", { class: "vrow" }, button(g ? "Record again" : "Record my guitar", g || built ? "" : "primary", listen, { id: "hrVolRec" }), sounds));
    const pick = (value, title, text, why) => {
      const input = el("input", { type: "radio", name: "hrvol", value, onchange: () => { scope = value; begin(); } });
      input.checked = scope === value; input.disabled = !has[value] || !!why;
      return el("label", { class: input.disabled ? "off" : "" }, input, el("span", {}, el("b", { text: title }), el("small", { text: why || text })));
    };
    const unsaved = "Save or discard your changes first.";
    const which = el("section", { class: "vpick", role: "radiogroup", "aria-label": "What to level" }, el("h3", { text: "What to level" }),
      pick("scene", S.snap >= 0 ? "This scene" : "This sound", last),
      pick("preset", "This preset", scenes ? "All its scenes to one volume." : last, changed ? (curPreset < 0 ? "Save the preset first." : unsaved) : ""),
      pick("all", `All presets (${plist.length})`, "Every preset, with all its scenes, to one volume.", curPreset < 0 ? "Load or save a preset first." : edCount() > 0 ? unsaved : ""));
    const at = which.querySelector("input:checked");
    if (at && at.disabled) { scope = "scene"; which.querySelector("input[value=scene]").checked = true; }
    const ready = built || g;
    show(message ? note(message, "vwarn") : "", guitar, which, note("The pedal is silent while it measures, and nothing is changed until you save."),
      el("div", { class: "vacts" }, button("Cancel", "", close), button("Measure", "primary", go, { id: "hrVolGo", disabled: !ready, title: ready ? "" : "Record your guitar or choose built-in strokes first" })));
  }
  const failed = e => e instanceof Stopped ? e.message : String(e && e.message || e) === "not connected" ? "The pedal was disconnected. Nothing was changed." : String(e && e.message || e);
  function working(title, text, stop = "Stop") {
    const line = el("p", { class: "vsay", role: "status", text }), bar = el("i"), run = running = { stop: false };
    const end = button(stop, "", () => { run.stop = true; });
    show(el("p", { class: "vbig", text: title }), line, el("div", { class: "vbar" }, bar), el("div", { class: "vacts" }, end));
    return { run, end, say: (text, part) => { if (line.textContent !== text) line.textContent = text; bar.style.width = (100 * Math.min(1, part)).toFixed(1) + "%"; } };
  }
  async function listen() {
    const w = working("Play now", "Chords and single notes, about one each second, as you play on stage.", "That is enough");
    let message = "";
    try {
      const g = await record((n, seconds) => w.say(n ? `${n} ${n === 1 ? "stroke" : "strokes"} heard. ${n < ENOUGH ? "Go on." : "Thank you."}` : "Chords and single notes, about one each second, as you play on stage.", Math.max(n / ENOUGH, seconds / MAX_SECONDS)), w.run);
      keep({ guitar: g }); built = "";
      if (g.loud) message = "Recorded. The guitar is very loud for the pedal's input.";
    } catch (e) { message = failed(e); }
    running = null;
    if (dialog) begin(message);
  }
  async function go() {
    const g = own(), strokes = built ? L.built(L.LEVELS[built]).map(L.hexOf) : g ? g.strokes : null;
    if (!strokes) return;
    const w = working("Measuring", "The pedal is silent meanwhile.");
    let got = null, message = "";
    Log.act("loudness_start", { scope, built, presets: plist.length });
    try { got = await measure(scope, strokes, (n, of, what) => w.say((what ? what + ". " : "") + "The pedal is silent meanwhile; a footswitch stops it.", n / Math.max(1, of)), w.run); }
    catch (e) { message = failed(e) || "Stopped. Nothing was changed."; Log.act("loudness_stopped", { why: message.slice(0, 80) }); }
    if (scope !== "scene" || message) await readAgain();
    running = null;
    if (!dialog) return;
    if (!got) begin(message); else if (!got.good.length) begin(got.items[0] && got.items[0].note || "Nothing could be measured."); else results(got);
  }
  function results(got) {
    const last = kept().volume, range = [Math.min(...got.good.map(i => i.level + i.out)), Math.max(...got.good.map(i => i.level + i.out))];
    let volume = got.good.length === 1 && Number.isInteger(last) ? last : L.start(got.good, got.limit);
    const gainOf = i => Math.max(-30, Math.min(12, L.gainFor(i, volume) + i.by));
    const title = i => i.scene >= 0 ? `Scene ${i.scene + 1}${i.name ? " · " + i.name : ""}` : got.good.some(x => x.preset === i.preset && x.scene >= 0) ? "As it starts" : i.preset >= 0 ? "Preset" : "This sound";
    const shown = el("output", { id: "hrVolAll", class: "vval" }), say = el("p", { class: "vnote" }), list = el("div", { class: "vlist", id: "hrVolList" }), save = button("", "primary", keepThem, { id: "hrVolSave" }), rows = [];
    const step = (text, label, fn, id) => button(text, "ico vstep", fn, { "aria-label": label, title: label, id });
    for (const n of [...new Set(got.items.map(i => i.preset))]) {
      if (n >= 0) list.append(el("h4", { text: `${slotTxt(n)} ${got.names.get(n) || ""}` }));
      for (const i of got.items.filter(x => x.preset === n)) {
        if (!got.good.includes(i)) { list.append(el("div", { class: "vitem" }, el("span", { class: "vname", text: title(i) }), el("span", { class: "vwhy", text: i.note || "It could not be measured." }))); continue; }
        const gain = el("span", { class: "vgain" }), why = el("small", { class: "vwhy" });
        const by = d => () => { const g = gainOf(i) + d; if (g >= -30 && g <= 12) { i.by += d; draw(); } };
        list.append(el("div", { class: "vitem", "data-item": `${i.preset},${i.scene}` }, el("span", { class: "vname", text: title(i) }), el("span", { class: "vnow", text: `now ${plain(i.level + i.out)} dB` }),
          step("−", `${title(i)} softer`, by(-1)), gain, step("+", `${title(i)} louder`, by(1)), why));
        rows.push({ i, gain, why });
      }
    }
    const left = [...new Set(got.items.filter(i => !got.good.includes(i)).map(i => i.preset))].filter(n => n >= 0).map(slotTxt);
    const changes = () => got.good.map(i => ({ preset: i.preset, scene: i.scene, first: i.first, gain: gainOf(i), was: i.out })).filter(c => c.gain !== c.was);
    function draw() {
      shown.textContent = `${plain(volume)} dB`;
      let held = 0, ends = 0;
      for (const { i, gain, why } of rows) {
        const g = gainOf(i), want = Math.round(volume - i.level) + i.by, holds = g > L.roomOf(i, got.limit);
        gain.replaceChildren(el("s", { text: number(i.out) }), " → ", el("b", { class: g === i.out ? "" : "new", text: number(g) }), " dB");
        why.textContent = want !== g ? "The gain ends here." : holds ? (got.limiter ? "Loud notes reach the limiter." : "Loud notes clip.") : i.by ? `${number(i.by)} by hand` : "";
        why.classList.toggle("vwarn", want !== g || holds);
        held += holds; ends += want !== g;
      }
      const n = changes().length;
      say.textContent = held || ends ? (held ? "Softer for all keeps the sound as it is." : "The gain of some does not go that far.") : "";
      save.textContent = scope === "scene" ? "Set the gain" : n === 1 ? "Save 1 change" : `Save ${n} changes`;
      save.disabled = !n;
    }
    async function keepThem() {
      const them = changes();
      keep({ volume });
      Log.act("loudness_save", { scope, n: them.length, volume });
      if (scope === "scene") {                            // the gain knob, saved as any change is
        close();
        S.gain[1] = them[0].gain; S.gainT = Date.now();
        const r = reply(await Pedal.cmd(`GAIN ${S.gain[0]} ${S.gain[1]}`, "GAIN"), "GAIN");
        if (r.startsWith("ERR") || !r) { toast("The gain was not set: " + errText(r || "ERR no answer"), "err"); return; }
        edMark("on"); buildGains();
        toast(`Output gain ${number(S.gain[1])} dB. Save the preset to keep it.`, "ok");
        return;
      }
      const w = working("Saving", "", "Please wait"), of = new Set(them.map(c => c.preset)).size;
      w.end.disabled = true;
      let message = "", done = 0;
      try { done = await store(them, (n, of) => w.say(`Preset ${n + 1} of ${of}`, n / of)); }
      catch (e) { message = failed(e); done = e.done || 0; }
      running = null;
      hrKnown = true;
      await readAgain();
      close();
      if (message) toast(`${done} of ${of} presets have their new volume, then it stopped: ${message}`, "err");
      else toast((done === 1 ? "The preset has its new volume." : `${done} presets have their new volume.`) + (left.length ? ` Not measured, and as it was: ${left.join(", ")}.` : ""), left.length ? "warn" : "ok");
    }
    const all = d => () => { volume = Math.max(-60, Math.min(0, volume + d)); draw(); };
    show(el("div", { class: "vall" }, el("span", { text: got.good.length === 1 ? "Volume" : "Volume for all" }), step("−", "Softer", all(-1), "hrVolLess"), shown, step("+", "Louder", all(1), "hrVolMore")),
      got.good.length > 1 ? note(`Now they are between ${plain(range[0])} and ${plain(range[1])} dB. The numbers below are output gains.`) : "", left.length ? el("p", { class: "vnote vwarn", id: "hrVolLeft", text: `Not all could be measured: ${left.join(", ")}. What is in the list without a number stays as loud as it is.` }) : "", say, list,
      el("div", { class: "vacts" }, button("Cancel", "", close), save));
    draw();
  }

  presets.after(button("Level volumes…", "mini", () => open(), { id: "hrVolume", title: "Give scenes and presets the same volume" }));
  const pop = document.getElementById("gainPop");
  if (pop) pop.append(button("Level volumes…", "mini", () => open(), { id: "hrVolGain" }));
})();
