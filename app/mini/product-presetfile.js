/* A preset file from somebody else, read strictly: only what the format has, in its form and within its limits; anything else is dropped, or the file is
 * refused. What comes out is made new here, and no text of the file reaches a command but through pioAscii. No input and no output, so that node can test it. */
(function (root) {
  "use strict";
  const MAX = Object.freeze({ bytes: 4 * 1024 * 1024, presets: 64, chain: 40, blocks: 16, params: 16, scenes: 8, files: 24, data: 8152 });
  const TONE = ["volume", "bass", "mid", "treble", "presence", "drive"];
  const KEY = /^[A-Za-z0-9_-]{1,24}$/, TYPE = /^[a-z][a-z0-9_]{0,19}$/, HASH = /^[0-9a-f]{64}$/i;
  // Control characters, and those that hide or turn around what is written.
  const hides = (c, lines) => c < 32 && !(lines && c === 10) || c >= 127 && c <= 159 || c === 0xad || c >= 0x200b && c <= 0x200f || c >= 0x2028 && c <= 0x202e || c >= 0x2060 && c <= 0x2069 || c === 0xfeff;
  const plain = (s, lines) => Array.from(s, ch => (hides(ch.codePointAt(0), lines) ? " " : ch)).join("");
  const bare = () => Object.create(null);
  const obj = v => !!v && typeof v === "object" && !Array.isArray(v);
  const arr = v => (Array.isArray(v) ? v : []);
  const own = (o, k) => (obj(o) && Object.prototype.hasOwnProperty.call(o, k) ? o[k] : undefined);
  const int = (v, lo = -100000, hi = 100000) => (typeof v === "number" && Number.isFinite(v) && v >= lo && v <= hi ? Math.round(v) : null);
  const text = (v, most, lines) => (typeof v === "string" ? plain(v.slice(0, 8000).normalize("NFC"), lines).replace(/[ 	]+/g, " ").trim().slice(0, most).trim() : "");
  const word = (v, form) => (typeof v === "string" && form.test(v) ? v : null);
  const flag = v => (typeof v === "boolean" ? v : null);
  const put = (o, k, v) => { if (v !== undefined && v !== null) o[k] = v; return o; };

  /* Where a file came from, as the program noted it: only the places it can come from. */
  function originOf(raw) {
    const out = bare();
    put(out, "title", text(own(raw, "title"), 120) || null);
    put(out, "creator", text(own(raw, "creator"), 80) || null);
    put(out, "license", text(own(raw, "license"), 120) || null);
    put(out, "address", word(own(raw, "address"), /^https:\/\/(?:www\.)?(?:patchstorage|tone3000)\.com\/[A-Za-z0-9/_.~%-]{0,200}$/));
    return Object.keys(out).length ? out : null;
  }
  function refOf(raw) {
    const name = text(own(raw, "name"), 40);
    if (!name) return null;
    const out = put(put(bare(), "name", name), "bytes", int(own(raw, "bytes"), 1, MAX.data));
    put(out, "rate_khz", int(own(raw, "rate_khz"), 24, 48));
    put(out, "sha256", word(own(raw, "sha256"), HASH));
    return put(out, "attachment", word(own(raw, "attachment"), KEY));
  }
  function paramsOf(raw) {
    const out = bare();
    if (obj(raw)) for (const k of Object.keys(raw).slice(0, MAX.params)) { const v = int(raw[k]); if (/^[a-z0-9_]{1,24}$/.test(k) && v !== null) out[k] = v; }
    return out;
  }
  function toneOf(raw) {
    if (!obj(raw)) return null;
    const out = bare();
    for (const k of TONE) put(out, k, int(own(raw, k), -10000, 10000));
    return out;
  }
  function gainOf(raw) {
    const out = bare();
    for (const k of ["in", "out"]) put(out, k, int(own(raw, k), -1000, 1000));
    return out;
  }

  function soundOf(raw, count) {
    const out = bare(), ids = new Set();
    const block = b => {
      const type = word(own(b, "type"), TYPE);
      if (!type || count.blocks >= MAX.blocks) { count.left++; return null; }
      count.blocks++;
      const made = put(bare(), "type", type), id = word(own(b, "id"), /^[A-Za-z0-9_]{1,16}$/);
      if (id && !ids.has(id) && !(id in {})) { ids.add(id); made.id = id; }
      made.on = own(b, "on") !== false;
      made.params = paramsOf(own(b, "params"));
      if (type === "ir") made.ir = refOf(own(b, "ir"));
      return made;
    };
    const blocks = list => arr(list).slice(0, MAX.chain).map(block).filter(Boolean);
    out.chain = [];
    for (const el of arr(own(raw, "chain")).slice(0, MAX.chain)) {
      const split = own(el, "split");
      if (own(el, "amp") === true) out.chain.push(put(bare(), "amp", true));
      else if (obj(split)) {
        const g = bare(), mix = arr(own(el, "mix_db"));
        g.split = put(put(bare(), "a", blocks(own(split, "a"))), "b", blocks(own(split, "b")));
        g.mix_db = [0, 1].map(i => int(mix[i], -1000, 1000) ?? 0);
        g.crossover_hz = int(own(el, "crossover_hz"), 0, 20000) ?? 0;
        g.even_gain = own(el, "even_gain") === true;
        out.chain.push(g);
      } else { const b = block(el); if (b) out.chain.push(b); }
    }
    const amp = own(raw, "amp");
    out.amp = put(put(put(put(bare(), "present", own(amp, "present") !== false), "on", own(amp, "on") !== false), "capture", refOf(own(amp, "capture"))), "tone", toneOf(own(amp, "tone")));
    out.cab_ir = refOf(own(raw, "cab_ir"));
    out.gain_db = gainOf(own(raw, "gain_db"));
    put(out, "tempo_bpm_x10", int(own(raw, "tempo_bpm_x10"), 1, 100000));
    put(out, "color", word(own(raw, "color"), /^#?[0-9a-f]{6}$/i));
    put(out, "stereo", flag(own(raw, "stereo")));
    put(out, "active_scene", int(own(raw, "active_scene"), 0, MAX.scenes - 1));
    const seen = new Set();
    out.scenes = [];
    for (const s of arr(own(raw, "scenes")).slice(0, 4 * MAX.scenes)) {
      const index = int(own(s, "index"), 0, MAX.scenes - 1);
      if (index === null || seen.has(index)) { count.left++; continue; }
      seen.add(index);
      const made = put(put(bare(), "index", index), "name", text(own(s, "name"), 15)), all = own(s, "blocks");
      if (obj(own(s, "gain_db"))) made.gain_db = gainOf(own(s, "gain_db"));
      put(made, "amp_on", flag(own(s, "amp_on")));
      put(made, "amp_tone", toneOf(own(s, "amp_tone")));
      made.blocks = bare();
      for (const id of ids) { const b = own(all, id); if (obj(b)) made.blocks[id] = put(put(bare(), "params", paramsOf(own(b, "params"))), "on", flag(own(b, "on"))); }
      out.scenes.push(made);
    }
    return out;
  }
  function presetOf(raw) {
    const sound = own(raw, "sound"), meta = own(raw, "meta"), count = { blocks: 0, left: 0 };
    if (!Array.isArray(own(sound, "chain"))) return null;
    const m = bare();
    m.name = text(own(meta, "name"), 60) || "Preset";
    m.author = text(own(meta, "author"), 60);
    m.description = text(own(meta, "description"), 2000, true);
    m.genre = text(own(meta, "genre"), 40);
    m.tags = arr(own(meta, "tags")).slice(0, 20).map(t => text(t, 30)).filter(Boolean);
    put(m, "slot", word(own(meta, "slot"), /^(?:[1-9]|1[01])[ABC]$/));
    put(m, "origin", originOf(own(meta, "origin")));
    const out = put(put(bare(), "meta", m), "sound", soundOf(sound, count));
    out.left = count.left;
    return out;
  }
  function fileOf(raw) {
    const kind = word(own(raw, "kind"), /^(?:capture|ir)$/), data = own(raw, "data"), bytes = int(own(raw, "bytes"), 1, MAX.data), hash = word(own(raw, "sha256"), HASH);
    if (!kind || !bytes || !hash || typeof data !== "string" || data.length !== 4 * Math.ceil(bytes / 3) || !/^[A-Za-z0-9+/]+={0,2}$/.test(data)) return null;
    const out = put(put(put(put(put(put(bare(), "kind", kind), "format", word(own(raw, "format"), /^[a-z0-9]{1,8}$/) || ""), "name", text(own(raw, "name"), 40)), "bytes", bytes), "sha256", hash.toLowerCase()), "data", data);
    if (kind === "ir") { out.rate_khz = int(own(raw, "rate_khz"), 24, 48) ?? 48; out.gain_mdb = int(own(raw, "gain_mdb"), -60000, 20000) ?? 0; return out; }
    const trim = own(raw, "trim_db"), level = own(raw, "in_dbu");
    out.trim_db = typeof trim === "number" && Math.abs(trim) <= 12 ? trim : 0;
    out.in_dbu = typeof level === "number" && level >= -20 && level <= 40 ? level : null;
    return out;
  }

  /* { ok, err, warn, presets, doc }: the presets of a text and the files it brings, made new. */
  function clean(raw) {
    const out = { ok: false, err: "This is not a HyperRig preset.", warn: [], presets: [], doc: null };
    if (typeof raw !== "string" || !raw.trim()) return out;
    if (raw.length > MAX.bytes) { out.err = "This file is too large for a preset."; return out; }
    let d;
    try { d = JSON.parse(raw.charCodeAt(0) === 0xfeff ? raw.slice(1) : raw); } catch (e) { return out; }
    if (own(d, "format") !== "hyperrig-preset" || !Number.isInteger(own(d, "version")) || own(d, "version") < 1) return out;
    if (Number.isInteger(own(d, "min_reader")) && own(d, "min_reader") > 1) { out.err = "This preset needs a newer HyperRig."; return out; }
    if (own(d, "version") > 1) out.warn.push("It was made with a newer HyperRig: what this one does not know is left out.");
    const all = arr(own(d, "presets")), list = all.slice(0, MAX.presets).map(presetOf), files = own(d, "attachments");
    out.presets = list.filter(Boolean);
    if (!out.presets.length) { out.err = "There are no presets in this file."; return out; }
    if (all.length > MAX.presets) out.warn.push(`The file has ${all.length} presets: the first ${MAX.presets} are shown.`);
    if (list.length > out.presets.length) out.warn.push(`${list.length - out.presets.length} of its presets are damaged and left out.`);
    out.doc = bare();
    out.doc.attachments = bare();
    if (obj(files)) for (const k of Object.keys(files).slice(0, MAX.files)) { const f = KEY.test(k) && !(k in {}) ? fileOf(files[k]) : null; if (f) out.doc.attachments[k] = f; }
    out.ok = true;
    out.err = "";
    return out;
  }

  /* What a preset needs and is not there. have: { type(name), capture(ref), ir(ref) }, each true when the pedal has it or the file brings it. */
  function needs(pre, have) {
    const out = { effects: [], captures: [], irs: [] }, add = (list, v) => { if (!list.includes(v)) list.push(v); };
    const walk = list => {
      for (const el of list) {
        if (el.split) { walk(el.split.a); walk(el.split.b); continue; }
        if (!el.type) continue;
        if (!have.type(el.type)) add(out.effects, el.type);
        const ref = el.type === "ir" ? el.ir || pre.sound.cab_ir : null;
        if (ref && !have.ir(ref)) add(out.irs, ref.name);
      }
    };
    walk(pre.sound.chain);
    const cap = pre.sound.amp.present ? pre.sound.amp.capture : null;
    if (cap && !have.capture(cap)) add(out.captures, cap.name);
    return out;
  }
  root.HyperRigPresetFile = Object.freeze({ MAX, clean, needs, originOf });
})(globalThis);
