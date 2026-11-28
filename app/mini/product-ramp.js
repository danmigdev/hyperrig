/* HyperRig for TANK-MINI, product builds: a ramp of a switch (firmware: mini/product/ramp.c). In Footswitches, the long press of A, B or C can be
 * "Ramp while held": a knob of a block goes to a target while the switch is held, in a rise time, and back when it is let go, in a fall time. A
 * tap of that switch is its short press as before. The tap can be "Ramp on/off" instead: one press goes to the target, where it stays, the next
 * goes back; the switch is the ramp's then. Both use the switch's one ramp. The block is named by its kind, the first of it in the chain, so the
 * ramp serves every preset that has one. Changes apply at once; Save to pedal keeps them, as with every setting of the footswitches. */
const HR_RAMP = 11, HR_RAMP_LATCH = 12, HR_RAMP_STEP = 50, HR_RAMP_MOST = 255 * HR_RAMP_STEP;
const hrRamp = { set: null, asked: false, busy: false };

/* What the pedal says of its ramps: one for each switch, kind, knob, target, rise and fall (ms). null when it does not say them. */
function hrRampParse(lines) {
  const m = Array.isArray(lines) && lines.length === 1 && /^RAMP ([0-9a-f]{36}) [0-7]$/.exec(lines[0]);
  if (!m) return null;
  const b = m[1].match(/../g).map(x => parseInt(x, 16));
  return [0, 1, 2].map(f => { const r = b.slice(6 * f, 6 * f + 6), t = r[2] | r[3] << 8; return { kind: r[0], knob: r[1], target: t > 32767 ? t - 65536 : t, rise: r[4] * HR_RAMP_STEP, fall: r[5] * HR_RAMP_STEP }; });
}
function hrRampHex(set) {
  const b = [];
  for (const r of set) { const t = r.target & 0xffff; b.push(r.kind, r.knob, t & 255, t >> 8, Math.round(r.rise / HR_RAMP_STEP), Math.round(r.fall / HR_RAMP_STEP)); }
  return b.map(v => v.toString(16).padStart(2, "0")).join("");
}
async function hrRampSay(word) {
  const set = hrRampParse(await Pedal.cmd("RAMP" + (word ? " " + word : ""), "RAMP", 2000));
  if (set) hrRamp.set = set;
  if (word && (!set || word !== "=" + hrRampHex(set))) toast("The pedal did not take this ramp.", "err");
  return set;
}
/* The ramps as a line, for a backup of the pedal's settings. */
const hrRampLines = () => hrRamp.set ? ["RAMP =" + hrRampHex(hrRamp.set)] : [];

/* The kinds of block that have knobs, by their names in the editor; a knob's words and how its value is written. */
const hrRampKinds = () => Object.values(S.types || {}).filter(t => t.params && t.params.length && Number.isInteger(t.id) && t.id > 0 && t.id < 256)
  .map(t => ({ id: t.id, name: t.name, label: lookOf(t.name).name, params: t.params })).sort((a, b) => a.label.localeCompare(b.label));
const hrRampKind = id => hrRampKinds().find(k => k.id === id) || null;
const hrRampKnob = (kind, knob) => kind && kind.params.find(p => p.idx === knob) || null;
function hrRampValue(p, v) { const l = plabel(p.name), s = fmtVal(v, l.unit); return typeof s === "string" ? s : String(v); }

/* A ramp in words, for the summary of a switch. */
function hrRampName(f, latch) {
  const r = hrRamp.set && hrRamp.set[f], kind = r && hrRampKind(r.kind), knob = hrRampKnob(kind, r && r.knob);
  if (!kind || !knob) return latch ? "Ramp on/off" : "Ramp while held";
  return `${latch ? "Ramp on/off" : "Ramp"}: ${kind.label} ${plabel(knob.name).lab} to ${hrRampValue(knob, Math.max(knob.min, Math.min(knob.max, r.target)))}`;
}

/* The knob a ramp of a block takes first: a bend where the block has one (the pitch glide), else its first. */
const hrRampFirst = k => k.params.find(p => /^bend/.test(p.name)) || k.params[0];

async function hrRampLoad() {
  if (hrRamp.asked || !S.connected || typeof hrOther !== "undefined" && hrOther.kind) return;
  hrRamp.asked = true;
  try { await hrRampSay(""); } catch (e) { hrRamp.asked = false; }
  if (typeof fsActRender === "function") fsActRender();
}

async function hrRampSet(f, change) {
  if (!hrRamp.set || hrRamp.busy || !S.connected) return;
  const set = hrRamp.set.map((r, i) => i === f ? { ...r, ...change } : r);
  hrRamp.busy = true;
  try { await hrRampSay("=" + hrRampHex(set)); } catch (e) { toast("The pedal did not take this ramp.", "err"); }
  hrRamp.busy = false;
  if (typeof fsActRender === "function") fsActRender();
}

/* What a ramp needs, beside its choice in Footswitches (the hold's, or the tap's on and off): the block, the knob, where it goes, and the two
 * times. */
function hrRampArgs(box, f, g) {
  if (g !== 0 && g !== 1) return;
  if (g === 1 && typeof fsTab !== "undefined" && fsTab && fsTab[f] && fsTab[f][0] && fsTab[f][0][0] === HR_RAMP_LATCH) return;     // the tap's on and off takes the switch
  if (!hrRamp.set) { void hrRampLoad(); return; }
  const r = hrRamp.set[f], kinds = hrRampKinds(), kind = hrRampKind(r.kind), knob = hrRampKnob(kind, r.knob);
  const add = (tag, attrs, label) => {
    const x = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) x.setAttribute(k, v);
    x.classList.add("arg", "hrramp");
    x.setAttribute("aria-label", `Footswitch ${"ABC"[f]}, ramp: ${label}`);
    box.appendChild(x);
    return x;
  };
  const block = add("select", { id: `hrRampK${f}` }, "block");
  if (!kind) { const o = document.createElement("option"); o.value = ""; o.textContent = "Choose a block"; block.appendChild(o); }
  for (const k of kinds) { const o = document.createElement("option"); o.value = k.id; o.textContent = k.label; block.appendChild(o); }
  block.value = kind ? String(kind.id) : "";
  block.onchange = () => { const k = hrRampKind(+block.value), p = k && hrRampFirst(k); if (k) void hrRampSet(f, { kind: k.id, knob: p.idx, target: p.max }); };
  if (!kind) return;
  const which = add("select", { id: `hrRampN${f}` }, "knob");
  for (const p of kind.params) { const o = document.createElement("option"); o.value = p.idx; o.textContent = plabel(p.name).lab; which.appendChild(o); }
  which.value = knob ? String(knob.idx) : "";
  which.onchange = () => { const p = hrRampKnob(kind, +which.value); if (p) void hrRampSet(f, { knob: p.idx, target: p.max }); };
  if (!knob) return;
  /* Where it goes, on a slider along the knob's way, with its value in words; then the two times, in seconds. */
  const part = (tag, attrs, cls) => { const x = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) x.setAttribute(k, v); if (cls) x.className = cls; return x; };
  const words = text => part("span", {}, "hrrampw").appendChild(document.createTextNode(text)).parentNode;
  const where = part("div", {}, "hrramp hrrampr"), times = part("div", {}, "hrramp hrrampr");
  const to = part("input", { id: `hrRampT${f}`, type: "range", min: knob.min, max: knob.max, step: 1, "aria-label": `Footswitch ${"ABC"[f]}, ramp: to` });
  to.value = Math.max(knob.min, Math.min(knob.max, r.target));
  const shown = part("output", { for: to.id }, "hrrampv");
  shown.textContent = hrRampValue(knob, +to.value);
  to.oninput = () => { shown.textContent = hrRampValue(knob, +to.value); };
  to.onchange = () => { void hrRampSet(f, { target: Math.max(knob.min, Math.min(knob.max, Math.round(+to.value))) }); };
  where.append(words("To"), to, shown);
  for (const [key, label] of [["rise", "Up in"], ["fall", "back in"]]) {
    const time = part("input", { id: `hrRamp${key === "rise" ? "R" : "F"}${f}`, type: "number", min: 0, max: HR_RAMP_MOST / 1000, step: HR_RAMP_STEP / 1000,
      "aria-label": `Footswitch ${"ABC"[f]}, ramp: ${label.toLowerCase()} seconds` }, "hrrampn");
    time.value = (r[key] / 1000).toFixed(2);
    time.onchange = () => { const ms = Math.max(0, Math.min(HR_RAMP_MOST, Math.round(+time.value * 1000 / HR_RAMP_STEP) * HR_RAMP_STEP || 0)); void hrRampSet(f, { [key]: ms }); };
    times.append(words(label), time, words(key === "rise" ? "s," : "s"));
  }
  box.append(where, times);
}

/* Read again after the pedal was away: another pedal, or the same one with other ramps. */
(() => {
  let was = false;
  setInterval(() => {
    const on = !!S.connected;
    if (on === was) return;
    was = on;
    if (!on) { hrRamp.set = null; hrRamp.asked = false; }
  }, 500);
})();
