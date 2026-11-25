/* The knobs a NAM capture keeps (docs/PARAMETRIC_NAM.md), on the amp's own controls: the pedal says which ones after AMPK, and a control that
 * moves a knob has the knob's name and numbers here. What is sent is AMPEQ, as ever: -120 and 120 are the ends of the knob, 0 its usual place. */
let hrKnobList = [], hrKnobTurn = 0, hrKnobTimer = 0;

/* AMPK <26 bytes in hexadecimal digits>: the control, the name, min and max as the knob has them, and what the network is given at the ends and the middle
 * of the control, 16384 is an end of the knob. */
function hrKnobParse(lines) {
  const out = [];
  for (const l of lines || []) {
    const m = /^AMPK ([0-9a-f]{52})$/.exec(l);
    if (!m) continue;
    const b = Uint8Array.from(m[1].match(/../g), x => parseInt(x, 16)), v = new DataView(b.buffer), name = String.fromCharCode(...b.slice(1, 12)).split("\0")[0].trim();
    const q = { control: b[0], min: v.getFloat32(12, true), max: v.getFloat32(16, true), lo: v.getInt16(20, true) / 16384, mid: v.getInt16(22, true) / 16384, hi: v.getInt16(24, true) / 16384, name: name || "Knob" };
    if (q.control >= 1 && q.control <= 5 && q.max > q.min) out.push(q);
  }
  return out;
}
const hrKnobOf = control => hrKnobList.find(k => k.control === control) || null;
/* The knob's own number for a value of the control, in tenths as AMPEQ has it. */
function hrKnobAt(k, v) {
  const x = k.mid + (v < 0 ? k.mid - k.lo : k.hi - k.mid) * Math.max(-120, Math.min(120, v)) / 120;
  return k.min + (x + 1) / 2 * (k.max - k.min);
}
function hrKnobText(control, v) {
  const k = hrKnobOf(control);
  if (!k) return fmtVal(v, "dB10");
  const n = hrKnobAt(k, v), span = k.max - k.min;
  return n.toFixed(span > 200 ? 0 : span > 2 ? 1 : 2).replace(/^-(0(?:\.0+)?)$/, "$1");
}
const hrKnobName = control => (hrKnobOf(control) || { name: AEQ_NAMES[control] }).name;
const hrKnobTitle = (control, hz) => { const k = hrKnobOf(control);
  return k ? `${k.name}: the capture's own knob, ${+k.min.toFixed(2)} to ${+k.max.toFixed(2)}. Double-click for its usual place.` : aeqTitle(control, hz); };
const hrKnobNote = () => hrKnobList.length ? ` This capture has knobs of its own: ${hrKnobList.map(k => k.name).join(", ")}.` : "";

/* Asked after the capture may have changed. */
function hrKnobsSoon() {
  clearTimeout(hrKnobTimer);
  if (DEMO) return;
  hrKnobTimer = setTimeout(() => void hrKnobsLoad(), 250);
}
async function hrKnobsLoad() {
  const turn = ++hrKnobTurn;
  let list = [];
  if (S.connected && S.ampPresent) {
    try { list = hrKnobParse(await Pedal.cmd("AMPK", l => /^AMPK end\b/.test(l) || /^ERR/.test(l), 1500)); } catch (e) { return; }
  }
  if (turn !== hrKnobTurn || JSON.stringify(list) === JSON.stringify(hrKnobList)) return;
  hrKnobList = list;
  Log.ev("amp_knobs", { names: list.map(k => k.name) });
  if (S.sel === "amp") syncAmpEditor();
}

/* A .nam to what the pedal loads: one that keeps knobs has its own converter. */
function hrNamConvert(text, opts) {
  return typeof HyperRigParametric === "object" && HyperRigParametric.handles(text) ? HyperRigParametric.convertAsync(text, opts) : Nam2Chip.convertAsync(text, opts);
}
/* What to say of a conversion: which knobs it has, which stay where they are, how near the pedal's copy is to the model. */
function hrNamInfo(res) {
  if (!res.knobs || !res.knobs.length) return "";
  const list = a => a.join(", "), worst = res.fit ? res.fit.worst : 0;
  return `; knobs: ${list(res.knobs.map(k => k.name))}` + (res.fixed && res.fixed.length ? `; fixed: ${list(res.fixed.map(k => `${k.name} at ${k.at}`))}` : "") +
    (worst < -24 ? "; a close copy over their whole range" : worst < -14 ? "; a fair copy, less so at the ends of their range" : "; only roughly like the original away from their usual place");
}
