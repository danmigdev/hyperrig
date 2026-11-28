/* HyperRig MINI development rules: what the development editor permits on a build from source, and what it learns
 * from the pedal's answers. mini-profile.js asks it on such a build only (tools/build_mini_dev_editor.py adds the
 * hooks); on any other profile it is not asked. This script performs no I/O.
 *
 * The forms are those the page sends; the firmware checks and limits the values itself. A command that names a block,
 * a preset or a scene is permitted only for one the pedal has reported. */
(function (root) {
  "use strict";
  const integer = (n, lo, hi) => Number.isInteger(n) && n >= lo && n <= hi;
  const need = value => { if (!value) throw new Error("incomplete protocol context"); };
  const ID = "(0|[1-9]\\d?)", NUMBER = "(-?(?:0|[1-9]\\d{0,4}))";
  const form = text => new RegExp("^" + text.replace(/ID/g, ID).replace(/NUMBER/g, NUMBER) + "$");
  const block = (state, id) => state.blocks && Object.hasOwn(state.blocks, id) ? state.blocks[id] : null;
  const inBank = (state, bank) => Object.values(state.blocks).filter(b => b.bank === bank).length;
  const open = (state, word) => !!state.upload && state.upload.word === word && integer(state.upload.bytes, 1, 8192);
  const name = text => /^[^\x00-\x1f\x7f]{1,23}$/.test(text);
  /* The settings for every preset, as the firmware says them; what does not fit is not known any more. */
  const globals = {GEQ: /^GEQ (-?\d+) (-?\d+) (-?\d+) (-?\d+) (-?\d+)$/, HPF: /^HPF hz=(\d+)$/, LIM: /^LIM on=([01]) thr=(-?\d+) rel=(\d+) lat=\d+ samples=\d+$/,
    SPILL: /^SPILL ([01]) tails=\d+$/, GLIDE: /^GLIDE ms=(\d+) blocks=\d+ snap=([01])$/, SPUR: /^SPUR ([01]) learned=\d+ blocks slow=\d+ pattern_rms=\d+ \(Q30\)$/};
  const told = (state, word) => !!state.globals && Object.hasOwn(state.globals, word);
  const rules = [
    // Chain. Sixteen blocks, ten in a section; the firmware refuses what does not fit its processor and memory.
    [form("FXA ([PQ]) 99 ([a-z0-9_]+)"), (m, s) => !!(s.blocks && s.types && Object.hasOwn(s.types, m[2])) &&
      Object.keys(s.blocks).length < 16 && inBank(s, m[1]) < 10],
    [form("FXR ID"), (m, s) => !!block(s, m[1])],
    [form("FXM ID ([PQ]) ID"), (m, s) => !!block(s, m[1]) && integer(+m[3], 0, 15) &&
      (block(s, m[1]).bank === m[2] || inBank(s, m[2]) < 10)],
    [form("FXL ID [0-2]"), (m, s) => !!block(s, m[1])],
    [form("FXOS ID [0-4]"), (m, s) => !!block(s, m[1])],
    // Another block in the place of one, on a product build: for the preset and the block that the pedal reported. The firmware compares both
    // with what is there.
    [/^FXC (-1|0|[1-9]|[12]\d|3[01]) (0|[1-9]|1[0-5]) ([a-z0-9_]+) ([a-z0-9_]+)$/, (m, s, p) => !!p && s.current === +m[1] && !!block(s, m[2]) &&
      block(s, m[2]).type === m[3] && m[4] !== m[3] && !!s.types && Object.hasOwn(s.types, m[4])],
    [form("FXMIX [PQ] [0-3] NUMBER NUMBER"), m => integer(+m[1], -32768, 32767) && integer(+m[2], -32768, 32767)],
    [form("FXXO [PQ] [0-3] NUMBER(?: [01])?"), m => integer(+m[1], 0, 20000)],
    // Amp and stereo.
    [form("AMP [01]"), () => true],
    [form("AMPX [01](?: ID)?"), m => m[1] === undefined || integer(+m[1], 0, 15)],
    [/^AMPEQ ((?:-?(?:0|[1-9]\d{0,4}) ?){2,6})$/, m => { const n = m[1].trim().split(" ").map(Number);
      return n.every(v => integer(v, -32768, 32767)) && (n.length >= 5 || n.length === 2 && integer(n[0], 0, 5)); }],
    [form("STW (?:0|100)"), () => true],
    // Tempo and tuner: the firmware's limits, 40 to 300 BPM in tenths and a reference of 415 to 466 Hz.
    [/^BPM ([1-9]\d{2,3})$/, m => integer(+m[1], 400, 3000)],
    [/^TUNER 0$/, () => true],
    [/^TUNER [01] [01] (\d{3})$/, m => integer(+m[1], 415, 466)],
    // Presets and scenes.
    [/^PNEW$/, () => true],
    [form("PNAME ID (.+)"), (m, s) => !!s.presets && Object.hasOwn(s.presets, m[1]) && name(m[2])],
    [form("PDEL ID"), (m, s) => !!s.presets && Object.hasOwn(s.presets, m[1])],
    [/^PCOLOR (?:[0-9a-f]{6}|none)( save)?$/, (m, s) => !m[1] || !!s.presets && integer(s.current, 0, 31) && Object.hasOwn(s.presets, s.current)],
    [/^SNAPCAP ([0-7]) (?:-1|[0-9]|1[0-4])$/, (m, s, p) => !!p && !!s.snaps && s.snaps.present[+m[1]] === "1"],
    [/^SNAPNAME ([0-7])(?: (.*))?$/, (m, s) => !!s.snaps && s.snaps.present[+m[1]] === "1" && (!m[2] || name(m[2]))],
    [/^SNAPDEL ([0-7])$/, (m, s) => !!s.snaps && s.snaps.present[+m[1]] === "1"],
    // A scene of a preset that is loaded goes to the pedal's storage. With none loaded (an import, before it is saved) the firmware keeps
    // it in its memory and answers preset=-1; PSAVE then writes it with the preset.
    [/^SNAPSAVE [0-7]$/, (m, s) => !!s.snaps && (s.current === -1 || !!s.presets && integer(s.current, 0, 31) && Object.hasOwn(s.presets, s.current))],
    // Footswitch actions and lights, kept by GSAVE in the firmware's own settings record.
    // 11 is a ramp while the switch is held, 12 the same ramp on and off (mini/product/ramp.c): a product build's, for the long press and for the tap only.
    [/^FSA [0-3] ([0-2]) (\d{1,2}) (\d{1,3}) (\d{1,3})$/, (m, s, p) => (+m[2] <= 10 || (+m[2] === 11 && m[1] === "1" || +m[2] === 12 && m[1] === "0") && !!p)
      && integer(+m[3], 0, 255) && integer(+m[4], 0, 255)],
    // The ramps of the three switches: kind, knob, target, rise and fall, six bytes each.
    [/^RAMP =([0-9a-f]{36})$/, (m, s, p) => !!p],
    [/^FSMODE (?:layout=(?:factory|scenes|custom)|mode=[a-z]{2,12}|bank=[0-9]|bypass=[01])$/, () => true],
    [/^KNOB (?:on|off)$/, (m, s, p) => !!p],
    [/^FSPRESS [0-3] [01]$/, () => true],
    [/^FSLED [0-3] (?:auto|custom|[0-9a-f]{6} [0-9a-f]{6})$/, () => true],
    [/^LEDCFG (?:(?:bright|tuner|tap|meter|hold|anim|idle)=[a-z0-9]{1,12}|default)$/, () => true],
    [/^FSDO [a-d]{1,2}(?: hold)?$/, () => true],
    [/^GSAVE$/, () => true],
    // Cab IRs and captures, on a product build (tools/check_mini_library.py): one upload at a time, its pieces within what it
    // announced; eight slots of IRs and fifteen of captures. The firmware keeps the limits of size, gain and slot itself,
    // and checks and prepares a capture before it plays. AUDIO stops and starts the engine around that.
    [/^IRBEGIN (0|[1-9]\d{0,3}) (-?(?:0|[1-9]\d{0,4})) (24|48)$/, (m, s, p) => !!p && integer(+m[1], 0, 4096) && integer(+m[2], -60000, 20000)],
    [/^(IRB|LDB) (0|[1-9]\d{0,3}) ((?:[0-9a-f]{2}){1,95})$/, (m, s, p) => !!p && open(s, m[1]) && +m[2] + m[3].length / 2 <= s.upload.bytes],
    [/^IREND [0-9a-f]{8}$/, (m, s, p) => !!p && open(s, "IRB")],
    [/^ISAVE [0-7] (.+)$/, (m, s, p) => !!p && name(m[1])],
    [/^(?:ILOAD|IDEL) [0-7]$/, (m, s, p) => !!p],
    [/^IREAD [0-7](?: (?:0|[1-9]\d{0,3}))?$/, (m, s, p) => !!p],
    [form("FXIR ID (?:-1|[0-7])"), (m, s, p) => !!p && !!block(s, m[1]) && block(s, m[1]).type === "ir"],
    [/^LDBEGIN (0|[1-9]\d{0,3})$/, (m, s, p) => !!p && integer(+m[1], 0, 8192)],
    [/^LDEND [0-9a-f]{8}$/, (m, s, p) => !!p && open(s, "LDB")],
    [/^CSAVE (?:[0-9]|1[0-4]) (.+)$/, (m, s, p) => !!p && name(m[1])],
    [/^(?:CLOAD|CDEL) (?:[0-9]|1[0-4])$/, (m, s, p) => !!p],
    [/^CREAD (?:[0-9]|1[0-4])(?: (?:0|[1-9]\d{0,3}))?$/, (m, s, p) => !!p],
    [/^CTRIM (?:live|[0-9]|1[0-4]) (-?(?:0|[1-9]\d?)(?:\.[05])?)(?: (-|-?(?:0|[1-9]\d{0,2})))?$/, (m, s, p) => !!p && Math.abs(+m[1]) <= 12 &&
      (m[2] === undefined || m[2] === "-" || integer(+m[2], -200, 400))],
    [/^AUDIO (?:OFF|A2L)$/, (m, s, p) => !!p],
    // The settings for every preset, on a product build that has said them, within the firmware's limits (tools/check_mini_globals.py); GSAVE keeps
    // them. Five bands of an EQ, the input's high-pass, the limiter, tails, the glide of a scene, the pedal's own whine. CALIB only listens; its sens,
    // a number about the input of another pedal, stays blocked.
    [/^GEQ [0-4] (0|-?[1-9]\d?)$/, (m, s, p) => !!p && told(s, "GEQ") && integer(+m[1], -12, 12)],
    [/^HPF (0|[1-9]\d{1,2})$/, (m, s, p) => !!p && told(s, "HPF") && (m[1] === "0" || integer(+m[1], 20, 120) && +m[1] % 5 === 0)],
    [/^LIM [01] (0|-[1-9]\d{0,2}) ([1-9]\d{1,3})$/, (m, s, p) => !!p && told(s, "LIM") && integer(+m[1], -200, 0) && integer(+m[2], 10, 2000)],
    [/^(SPILL|SPUR) [01]$/, (m, s, p) => !!p && told(s, m[1])],
    [/^GLIDE (0|[1-9]\d{0,2}) [01]$/, (m, s, p) => !!p && told(s, "GLIDE") && integer(+m[1], 0, 170)],
    [/^CALIB (?:start|stop)$/, (m, s, p) => !!p],
    // MIDI: the port, and its settings as thirty bytes (mini/product/midi.c), each within what the firmware knows.
    [/^MIDI (?:on|off)$/, (m, s, p) => !!p],
    [/^MIDI =([0-9a-f]{60})$/, (m, s, p) => !!p && midi(m[1].match(/../g).map(x => parseInt(x, 16)))],
    // The measure of loudness (docs/MINI_LOUDNESS.md): the firmware's own memory for it in the two sizes it needs, a stroke within its place,
    // runs of a few seconds, and output gains into a preset that the pedal reported. The firmware ends a measure by itself, and gives back
    // what played before.
    [/^HRLV(?: 0[15])?$/, (m, s, p) => !!p],
    [/^HRLV 06([0-9a-f]{2})0([1-8])([0-9a-f]{2})([0-9a-f]{2})$/, (m, s, p) => !!p && integer(parseInt(m[1], 16), 1, 176) && integer(parseInt(m[4], 16), 1, 152)],
    [/^HRLV 02([0-9a-f]{2})((?:[0-9a-f]{2}){9})$/, (m, s, p) => !!p && !!s.presets && Object.hasOwn(s.presets, String(parseInt(m[1], 16))) &&
      m[2].match(/../g).every(v => v === "7f" || integer(parseInt(v, 16) << 24 >> 24, -30, 12))],
    [/^(?:REC 4 (?:184|1142)|INJBEGIN 1408)$/, (m, s, p) => !!p],
    [/^RECD (?:0|[1-9]\d{0,3})$/, (m, s, p) => !!p],
    [/^INJB (0|[1-9]\d{0,3}) ((?:[0-9a-f]{2}){1,90})$/, (m, s, p) => !!p && +m[1] + m[2].length / 2 <= 2816],
  ];
  function midi(b) {
    const off = 255, within = (v, lo, hi) => v === off || integer(v, lo, hi);
    return b[0] <= 1 && within(b[1], 0, 16) && within(b[2], 1, 16) && b.slice(3, 9).every(v => within(v, 0, 119)) && within(b[9], 0, 104) &&
      [10, 15, 20, 25].every(k => within(b[k], 0, 119) && b[k + 1] < 16 && b[k + 2] < 7 && b[k + 3] <= 100 && b[k + 4] <= 100);
  }
  const families = Object.freeze(["BPM", "TUNER", "AMP", "AMPX", "AMPEQ", "STW", "FXM", "FXL", "FXOS", "FXMIX", "FXXO", "PNEW", "PNAME",
    "PDEL", "PCOLOR", "SNAPNAME", "SNAPDEL", "FSA", "FSMODE", "FSPRESS", "FSLED", "LEDCFG", "FSDO", "GSAVE"]);
  const productFamilies = Object.freeze(["KNOB", "IRBEGIN", "IRB", "IREND", "ISAVE", "ILOAD", "IDEL", "IREAD", "FXIR",
    "LDBEGIN", "LDB", "LDEND", "CSAVE", "CLOAD", "CDEL", "CREAD", "CTRIM", "AUDIO", "GEQ", "HPF", "LIM", "SPILL", "GLIDE", "SPUR", "CALIB", "FXC", "MIDI", "SNAPCAP", "HRLV", "REC", "RECD", "INJBEGIN", "INJB", "RAMP"]);
  // PNAME by itself only says how it is used: the page asks it whether the firmware can rename.
  const queries = Object.freeze(["PNAME", "TUNER", "FSA", "FSMODE", "FSPRESS", "FSLED", "LEDCFG", "KNOB", "HRID", "HRST", "AMPK", "MIDI", "SNAPCAP", "RAMP"]);
  // Over Bluetooth a product build takes what it takes over USB, less these, which its firmware keeps to the cable.
  const cable = Object.freeze(["REC", "RECD", "INJBEGIN", "INJB"]);

  /* A product build (docs/MINI_PRODUCT.md) says which build it is. An editor made for one permits changes only to the
   * build it was made for: product is its {version, build_id}, or null for an editor of another build from source. */
  let answered = null;
  function build(lines, product) {
    const m = Array.isArray(lines) && lines.length >= 1 && /^HRID 1 (\S+) ([0-9a-f]{16}) banks=3$/.exec(lines[0]);
    answered = m ? {version: m[1], build_id: m[2]} : null;
    return {known: !!m, same: same(product), version: m ? m[1] : null, build_id: m ? m[2] : null};
  }
  const same = product => !!(product && answered && answered.version === product.version && answered.build_id === product.build_id);
  const forget = () => { answered = null; };

  /* The link itself, on the build this editor was made for. The page asks the pedal for the key that this computer keeps:
   * over USB the pedal gives it, over Bluetooth only for a minute after A and B were held on it for three seconds. Over
   * Bluetooth the page then shows that it has the key: the pedal's question, then the key's number and the answer to the
   * question, after which the pedal takes changes from it; and it says when it is about to disconnect, so that the pedal ends
   * the link itself. Over either link it may open the pedal's minute for letting another device in (BLE pair), and make the
   * pedal forget every phone and computer (BLE forget): over Bluetooth the pedal takes both only from one that is in. None of
   * these changes a preset or a setting. */
  function link(value, transport, product) {
    if (!product || !same(product) || transport !== "usb-cdc" && transport !== "ble-nus") return false;
    if (/^BLE (?:key|pair|forget)$/.test(value)) return true;
    return transport === "ble-nus" && /^(?:AUTH \?|AUTH (?:0|[1-9]\d?) [0-9a-f]{32}|HRBYE)$/.test(value);
  }

  /* true or false for a form above, null for any other command: the tested rules then decide. */
  function rule(value, state, product = null) {
    if (product && !same(product)) return false;
    for (const [pattern, permitted] of rules) {
      const m = pattern.exec(value);
      if (m) return permitted(m, state, product) === true;
    }
    return null;
  }

  /* What a planned command changes in the state the next one of the plan is judged by. */
  function plan(command, state) {
    const w = command.split(" ");
    if (w[0] === "FXM" && block(state, w[1])) state.blocks[w[1]].bank = w[2];
    if (w[0] === "FXR" && state.blocks) delete state.blocks[w[1]];
    if (w[0] === "FXC" && state.blocks) delete state.blocks[w[2]];     // the id of the new one is not known before the answer
  }

  /* The pedal refused a command on the chain: the blocks, their sections and lanes are what they were. Forgetting them
   * refused the next command too, such as the IR block that waits for its IR to be uploaded. But FXC says when they are
   * the blocks of another preset. */
  function refused(request, lines) {
    const m = /^(FX(?:A|R|C|M|E|P|L|OS|IR)) /.exec(request);
    return !!m && Array.isArray(lines) && lines.length === 1 && typeof lines[0] === "string" &&
      (lines[0].startsWith("ERR " + m[1] + " ") || lines[0] === "ERR " + m[1]) && !lines[0].startsWith("ERR FXC another ");
  }

  /* Learn from an answer; true when it is done here, false when the tested code must look at it. */
  function observe(request, lines, observed) {
    const w = request.split(" "), first = lines[0] || "";
    if (w[0] === "FXM" || w[0] === "FXL") {
      need(w.length > 2 && new RegExp("^" + w[0] + " ok").test(first) && block(observed, w[1]));
      if (w[0] === "FXM") observed.blocks[w[1]].bank = w[2]; else observed.blocks[w[1]].lane = +w[2];
      return true;
    }
    if (w[0] === "FXA") {
      const m = /^FXA id=(\d+) (\S+)$/.exec(first);
      need(m && m[2] === w[3] && observed.blocks && !Object.hasOwn(observed.blocks, m[1]));
      observed.blocks[m[1]] = {type: m[2], bank: w[1], lane: 0};
      return true;
    }
    if (w[0] === "FXC") {        // the new block has the section and the lane of the old one
      const m = /^FXC id=(\d+) (\S+)$/.exec(first), old = block(observed, w[2]);
      need(m && m[2] === w[4] && old && (m[1] === w[2] || !Object.hasOwn(observed.blocks, m[1])));
      delete observed.blocks[w[2]];
      observed.blocks[m[1]] = {type: m[2], bank: old.bank, lane: old.lane};
      return true;
    }
    if (w[0] === "FXR") {
      need(/^FXR ok/.test(first) && block(observed, w[1]));
      delete observed.blocks[w[1]];
      return true;
    }
    if (request === "PNEW") {
      need(first === "PNEW ok");
      observed.blocks = null; observed.snaps = null; observed.gain = null; observed.current = -1;
      return true;
    }
    if (w[0] === "SNAP") {       // a scene changes switches and knobs, not which blocks there are
      need(new RegExp("^SNAP ok " + w[1] + " ").test(first));
      if (observed.snaps) observed.snaps.current = +w[1];
      observed.gain = null;
      return true;
    }
    if (w[0] === "SNAPDEL") {    // the others are what they were
      need(new RegExp("^SNAPDEL ok " + w[1] + " preset=-?[0-9]+$").test(first));
      if (observed.snaps) observed.snaps = {present: [...observed.snaps.present].map((v, k) => k === +w[1] ? "0" : v).join(""), current: observed.snaps.current === +w[1] ? -1 : observed.snaps.current};
      return true;
    }
    if (w[0] === "IRBEGIN" || w[0] === "LDBEGIN") {    // the upload that is open
      observed.upload = null;
      need(first === "OK " + w[0] + " " + w[1]);
      if (+w[1]) observed.upload = w[0] === "IRBEGIN" ? {word: "IRB", bytes: 2 * +w[1]} : {word: "LDB", bytes: +w[1]};
      return true;
    }
    if (w[0] === "IREND" || w[0] === "LDEND") { observed.upload = null; return true; }
    if (w[0] === "PDEL") { observed.presets = null; return true; }   // PLIST follows
    if (w[0] === "PNAME") {                                          // the list is what it was, with another name; the page does not read it again
      const m = /^PNAME ok (\d+) '(.*)'$/.exec(first);
      need(m && m[1] === w[1] && observed.presets && Object.hasOwn(observed.presets, m[1]));
      observed.presets[m[1]] = m[2];
      return true;
    }
    if (Object.hasOwn(globals, w[0])) {                              // asked or changed, the answer is what the pedal has
      const m = lines.length === 1 && globals[w[0]].exec(first), known = {...observed.globals};
      delete known[w[0]]; observed.globals = known;
      need(m);
      known[w[0]] = m.slice(1).map(Number);
      return true;
    }
    if (request === "LVL") {
      // A preset change of the pedal itself (a footswitch) shows here first; the page then reads the chain, the scenes
      // and the list. Noticed here, it clears what is old. Noticed only in the list, it cleared what was just read.
      const p = / p=(-?\d+)(?: |$)/.exec(first);
      if (p && observed.current !== null && +p[1] !== observed.current) {
        observed.blocks = null; observed.snaps = null; observed.current = +p[1];
      }
      return false;
    }
    return false;
  }
  root.HyperRigDevRules = Object.freeze({rule, plan, observe, refused, build, forget, link, families, productFamilies, queries, cable});
})(globalThis);
