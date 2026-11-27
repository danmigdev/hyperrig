/* HyperRig for TANK-MINI, product builds: MIDI, in the settings (firmware: mini/product/midi.c, midi_usb.h). The port, the channels, what each message
 * does. Changes apply at once, and Save to pedal keeps them, as with every setting of the pedal.
 * The port is another thing: turning it on restarts the USB connection of the pedal, so the editor loses it for a moment; and the pedal turns it off
 * again by itself when the editor does not find it again. Nothing is kept before that. */
const HR_CC = { scene: ["Scene", "value 0 to 7 is the scene, 8 the next, 9 the one before"], bypass: ["Bypass", "on from 64, off below"], amp: ["Amp", "on from 64, off below"],
  tuner: ["Tuner", "on from 64, off below"], tap: ["Tap tempo", "a tap from 64"], volume: ["Volume", "0 to 127"], blocks: ["Blocks", "this one and the next fifteen: the places of the chain, on from 64"] };
const HR_LAST = { blocks: 104 };
const HR_PORT = {
  off: "Off. Turn it on to use the pedal with other MIDI devices and programs, over the USB cable.",
  waiting: "On, and waiting for a computer.",
  on: "On. Other programs call it Tank-M HyperRig. A computer needs no driver.",
  refused: "The computer did not take it, so the pedal goes on without. Unplug the cable for a few seconds and plug it in again to try once more.",
};
const HR_KEYS = ["clock", "in", "out", "scene", "bypass", "tuner", "tap", "amp", "volume", "blocks"], HR_PORTS = ["off", "waiting", "on", "refused"];
const hrMidi = { is: null, asked: "", was: false, busy: false };

/* What the pedal says of its settings, in words; null when it does not say them. Its bytes: the ten of HR_KEYS, 255 for off, and five for each knob, from 0. */
function hrMidiParse(lines) {
  const m = Array.isArray(lines) && lines.length === 1 && /^MIDI ([0-3]) ([01]) ([0-9a-f]{60}) \d+ \d+$/.exec(lines[0]);
  if (!m) return null;
  const b = m[3].match(/../g).map(x => parseInt(x, 16)), word = v => v === 255 ? "off" : String(v), is = { port: HR_PORTS[+m[1]], usb: m[2] === "1" ? "on" : "off", knobs: [] };
  HR_KEYS.forEach((k, i) => { is[k] = word(b[i]); });
  is.clock = b[0] ? "on" : "off";
  if (b[1] === 0) is.in = "all";
  for (let k = 0; k < 4; k++) { const [cc, place, knob, from, to] = b.slice(10 + 5 * k, 15 + 5 * k); is.knobs.push({ cc: word(cc), place: place + 1, knob: knob + 1, from, to }); }
  return is;
}
function hrMidiHex(is) {
  const byte = v => v === "off" ? 255 : v === "all" ? 0 : +v, b = [is.clock === "on" ? 1 : 0, ...HR_KEYS.slice(1).map(k => byte(is[k]))];
  for (const k of is.knobs) b.push(byte(k.cc), k.place - 1, k.knob - 1, k.from, k.to);
  return b.map(v => v.toString(16).padStart(2, "0")).join("");
}
async function hrMidiSay(word) {
  const line = "MIDI" + (word ? " " + word : ""), is = hrMidiParse(await Pedal.cmd(line, "MIDI", 2000));
  if (is) hrMidi.is = is;
  if (word && (!is || word[0] === "=" && word !== "=" + hrMidiHex(is))) toast("The pedal did not take this MIDI setting.", "err");
  hrMidiShow();
  return is;
}
const hrMidiSet = change => hrMidiSay("=" + hrMidiHex({ ...hrMidi.is, ...change }));
/* The settings as a line, to put them back when they are not to be saved. The port is not one of them. */
const hrMidiLines = () => hrMidi.is ? ["MIDI =" + hrMidiHex(hrMidi.is)] : [];

function hrMidiShow() {
  const box = document.getElementById("hrMidi"), is = hrMidi.is;
  if (!box) return;
  const on = !!S.connected && !hrOther.kind && !!is;
  for (const e of box.querySelectorAll("button, select, input")) e.disabled = !on || hrMidi.busy;
  const say = document.getElementById("hrMidiSay"), text = on ? HR_PORT[is.port] || "" : "Connect the pedal first.";
  if (say.textContent !== text) say.textContent = text;
  if (!on) return;
  const port = is.port !== "off" && is.port !== "refused" || is.usb === "on";
  for (const b of box.querySelectorAll("[data-hrport]")) { const me = (b.dataset.hrport === "on") === port; b.classList.toggle("on", me); b.setAttribute("aria-pressed", String(me)); }
  document.getElementById("hrMidiIn").value = is.in;
  document.getElementById("hrMidiOut").value = is.out;
  document.getElementById("hrMidiClock").checked = is.clock === "on";
}

async function hrMidiPort(on) {
  if (!S.connected || hrMidi.busy || !hrMidi.is) return;
  if (on && !await uiConfirm({ title: "Turn on MIDI over USB?", okLabel: "Turn on",
    body: "The pedal leaves the computer for a moment and comes back as a MIDI device too. If the editor does not find it again within 45 seconds, the pedal turns MIDI off by itself." })) return;
  Log.act("midi_port", { on });
  hrMidi.busy = true; hrMidiShow();
  try {
    hrMidi.asked = on ? "on" : "off";
    await hrMidiSay(hrMidi.asked);
  } finally { hrMidi.busy = false; hrMidiShow(); }
}

/* Once more connected after the port was turned on or off: is it so, and how to keep it. */
async function hrMidiBack() {
  const asked = hrMidi.asked;
  hrMidi.asked = "";
  for (let k = 0; k < 20 && S.connected && (Pedal.busy || txn || refreshing); k++) await new Promise(r => setTimeout(r, 250));
  if (!S.connected) return;
  const is = await hrMidiSay("").catch(() => null);
  if (!is) return;
  if (is.port === asked) {
    gdDirty = true; gdSeq++; gdRender();
    toast(`${asked === "on" ? "The pedal is a MIDI device now. " : ""}In the settings, Save to pedal keeps it so.`, "ok", { title: `MIDI over USB is ${asked}` });
  } else if (is.port === "refused") toast("The computer did not take it, or the editor did not come back in time. The pedal goes on without.", "err", { title: "MIDI is off again" });
}

const hrBlockName = k => { const it = [...S.chain.P, ...S.chain.Q][k]; return it ? lookOf(it.type).name : ""; };
const hrMidiKnobName = (place, k) => { const it = [...S.chain.P, ...S.chain.Q][place], p = it && ((S.types[it.type] || {}).params || []).find(x => x.idx === k); return p ? plabel(p.name).lab : ""; };

async function hrMidiMap() {
  const is = hrMidi.is;
  if (!is || hrMidi.busy) return;
  const mk = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  const number = (value, high, label) => { const e = mk("input"); e.type = "number"; e.min = "0"; e.max = String(high); e.step = "1"; e.placeholder = "off"; e.value = value === "off" ? "" : value; e.setAttribute("aria-label", label); return e; };
  const pick = (n, value, label, text) => { const e = mk("select"); for (let k = 1; k <= n; k++) { const o = mk("option", "", text(k)); o.value = String(k); e.append(o); } e.value = String(value); e.setAttribute("aria-label", label); return e; };
  const cc = {}, knobs = [];
  const note = mk("p", "hrnote");
  const right = (e, high) => e.value === "" || /^\d{1,3}$/.test(e.value) && +e.value <= high;
  const made = await uiForm({
    title: "What the messages do", okLabel: "Use it",
    body: "Received, they do this. When you change it on the pedal, the same messages are sent. An empty number is off.",
    build: box => {
      box.classList.add("hrmmap");
      const list = mk("div", "hrmrows");
      list.append(mk("b", "", "Presets 1A to 11B"), mk("span", "hrmfix", "Program change"), mk("small", "", "0 to 31, shown as 1 to 32 by many programs"));
      for (const [k, [name, what]] of Object.entries(HR_CC)) {
        cc[k] = number(is[k], HR_LAST[k] || 119, `Controller for ${name}`);
        const field = mk("span", "hrmfld"); field.append(mk("span", "", "Controller"), cc[k]);
        list.append(mk("b", "", name), field, mk("small", "", what));
      }
      box.append(list, mk("h3", "", "Knobs of blocks, as with an expression pedal"));
      const table = mk("div", "hrmknobs");
      for (const x of ["Controller", "Block", "Knob", "From %", "To %"]) table.append(mk("b", "", x));
      is.knobs.forEach((k, i) => {
        const at = `Knob ${i + 1}: `, e = { cc: number(k.cc, 119, at + "controller"), place: pick(16, k.place, at + "block", n => hrBlockName(n - 1) ? `${n} · ${hrBlockName(n - 1)}` : String(n)),
          knob: null, from: number(String(k.from), 100, at + "from"), to: number(String(k.to), 100, at + "to") };
        const names = () => { const was = e.knob ? e.knob.value : String(k.knob); const next = pick(7, was, at + "knob", n => hrMidiKnobName(+e.place.value - 1, n - 1) || String(n)); if (e.knob) e.knob.replaceWith(next); e.knob = next; };
        names(); e.place.onchange = names;
        e.from.placeholder = "0"; e.to.placeholder = "100";
        table.append(e.cc, e.place, e.knob, e.from, e.to);
        knobs.push(e);
      });
      box.append(table, note);
      return { first: cc.scene };
    },
    submit: async () => {
      const bad = [...Object.entries(cc).filter(([k, e]) => !right(e, HR_LAST[k] || 119)).map(([, e]) => e), ...knobs.flatMap(k => [k.cc, k.from, k.to].filter((e, i) => !right(e, i ? 100 : 119)))];
      if (bad.length) { note.textContent = "Controllers are 0 to 119, the first of the blocks 0 to 104, and the two ends of a knob 0 to 100."; bad[0].focus(); return undefined; }
      const twice = Object.entries(cc).filter(([, e]) => e.value !== "").map(([k, e]) => [k, +e.value]);
      for (const [a, n] of twice) for (const [b, m] of twice) if (a < b && (n === m || (a === "blocks" && m > n && m < n + 16) || (b === "blocks" && n > m && n < m + 16))) {
        note.textContent = `${HR_CC[a][0]} and ${HR_CC[b][0]} have the same controller.`; cc[a].focus(); return undefined;
      }
      const word = e => e.value === "" ? "off" : String(+e.value);
      return { ...Object.fromEntries(Object.keys(HR_CC).map(k => [k, word(cc[k])])),
        knobs: knobs.map(k => ({ cc: word(k.cc), place: +k.place.value, knob: +k.knob.value, from: +k.from.value || 0, to: k.to.value === "" ? 100 : +k.to.value })) };
    },
  });
  if (!made || !hrMidi.is || hrMidiHex({ ...hrMidi.is, ...made }) === hrMidiHex(hrMidi.is)) return;
  Log.act("midi_map", {});
  hrMidi.busy = true; hrMidiShow();
  try { await hrMidiSet(made); } finally { hrMidi.busy = false; hrMidiShow(); }
  toast("Save to pedal keeps it.", "ok", { title: "What the messages do is changed" });
}

(function () {
  "use strict";
  const drawer = document.getElementById("settings");
  if (!drawer) return;
  const section = document.createElement("section");
  section.id = "hrMidi";
  const channels = ["off", ...Array.from({ length: 16 }, (_, k) => String(k + 1))];
  const options = list => list.map(([v, t]) => `<option value="${v}">${t}</option>`).join("");
  section.innerHTML = '<h3>MIDI</h3><div class="row wrap hrmport"><span id="hrMidiPortL">Over USB</span><span class="fseg" role="group" aria-labelledby="hrMidiPortL">' +
    '<button type="button" data-hrport="off">Off</button><button type="button" data-hrport="on">On</button></span></div><p class="hrmsay" id="hrMidiSay" role="status"></p>' +
    `<label class="spill"><span>Receive on</span> <select id="hrMidiIn">${options([["all", "All channels"], ...channels.slice(1).map(c => [c, "Channel " + c]), ["off", "Off"]])}</select></label>` +
    `<label class="spill"><span>Send on</span> <select id="hrMidiOut">${options([...channels.slice(1).map(c => [c, "Channel " + c]), ["off", "Off"]])}</select></label>` +
    '<label class="spill"><input type="checkbox" id="hrMidiClock"> Take the tempo from MIDI clock</label>' +
    '<div class="row wrap"><button type="button" class="btn mini" id="hrMidiMap">What the messages do…</button></div>';
  const help = [...drawer.querySelectorAll(".dbox > section")].find(s => /^Help/.test((s.querySelector("h3") || {}).textContent || ""));
  if (help) help.before(section); else drawer.querySelector(".dbox").append(section);
  for (const b of section.querySelectorAll("[data-hrport]")) b.onclick = () => { if (b.getAttribute("aria-pressed") !== "true") void hrMidiPort(b.dataset.hrport === "on"); };
  section.querySelector("#hrMidiIn").onchange = e => void hrMidiSet({ in: e.target.value });
  section.querySelector("#hrMidiOut").onchange = e => void hrMidiSet({ out: e.target.value });
  section.querySelector("#hrMidiClock").onchange = e => void hrMidiSet({ clock: e.target.checked ? "on" : "off" });
  section.querySelector("#hrMidiMap").onclick = () => void hrMidiMap();
  hrMidiShow();
  // Read when the settings open, and shown as it changes: the port comes and goes with the cable.
  let reading = false;
  const read = async () => {
    if (reading || hrMidi.busy || !S.connected || hrOther.kind || pioBusy) return;
    reading = true;
    try { await hrMidiSay(""); } catch (e) { /* the next time */ } finally { reading = false; }
  };
  new MutationObserver(() => { if (drawer.classList.contains("on")) void read(); }).observe(drawer, { attributes: true, attributeFilter: ["class"] });
  setInterval(() => {
    const on = !!S.connected;
    if (on !== hrMidi.was) {
      hrMidi.was = on;
      if (!on) hrMidi.is = null;
      else if (hrMidi.asked) void hrMidiBack();
      hrMidiShow();
    }
    if (on && !hrMidi.is && drawer.classList.contains("on") && !Pedal.busy && !txn && !refreshing) void read();
  }, 500);
})();
