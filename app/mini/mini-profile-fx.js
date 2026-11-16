/* HyperRig MINI FX editor policy, derived from the frozen original board adapter.
 * No stock-MINI SysEx, six-block model or substitute transport is used here.
 * This script performs no I/O. The builder injects the reviewed build profile. */
(function (root) {
  "use strict";
  const profile = root.HYPERRIG_MINI_BUILD;
  if (!profile || profile.target !== "tank-mini") throw new Error("Missing MINI build profile");
  const deepFreeze = obj => {
    Object.values(obj).forEach(v => { if (v && typeof v === "object") deepFreeze(v); });
    return Object.freeze(obj);
  };
  deepFreeze(profile);
  const query = new Set(("PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST " +
    "LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE TUNE LIFE CRASH CLKSTATE GAIN BPM PCOLOR").split(" "));
  const panelCommands = new Set(["FSA", "FSMODE", "FSPRESS", "FSDO", "FSLED", "LEDCFG"]);
  const scopedCommands = new Set(["FXP", "FXE", "PLOAD", "PSAVE", "PDEL", "SNAP", "SNAPSAVE", "GAIN"]);
  const familyCommands = new Set(["FXA", "FXR", "FXP", "FXE", "PLOAD", "PSAVE", "SNAP", "SNAPSAVE", "GAIN"]);
  const familyTransports = new Set(["usb-cdc", "ble-nus"]);
  let identified = false, identifiedTransport = null;
  const emptyState = () => ({types: null, blocks: null, presets: null, current: null, snaps: null, gain: null});
  let observed = emptyState();
  const integer = (n, lo = -2147483648, hi = 2147483647) => Number.isInteger(n) && n >= lo && n <= hi;
  const familyWriteEnabled = transport => profile.capabilities.read === true && profile.hardware_verified === true &&
    familyTransports.has(transport) && Array.isArray((profile.family_validation || {})[transport]) &&
    profile.family_validation[transport].length > 0 && Array.isArray((profile.family_capabilities || {})[transport]) &&
    profile.family_capabilities[transport].some(c => familyCommands.has(c));
  const fullWriteEnabled = () => profile.capabilities.write === true && profile.hardware_verified === true && !!profile.write_validation;
  const scopedWriteEnabled = () => profile.capabilities.read === true && profile.hardware_verified === true &&
    !!profile.command_validation && Object.keys(profile.command_capabilities || {}).some(c => scopedCommands.has(c));
  function inspectPong(pong, transport = null) {
    const version = (/^PONG (.+?) \w{3} [ \d]\d \d{4}(?: |$)/.exec(String(pong)) || [])[1];
    if (!version || !/^tankm_fw M\d+\.\d+(?: |$)/.test(version) || /\btank[gb]\b/.test(version)) {
      return {ok: false, reason: "This editor requires the standalone HyperRig MINI firmware (tankm_fw). Stock MINI and Tank-G/B are incompatible."};
    }
    if (!profile.firmware_version || version !== profile.firmware_version || !/^[a-f0-9]{64}$/.test(profile.image_sha256 || "")) {
      return {ok: false, identity: version, reason: "MINI identity received; this app has no matching firmware build profile. Only PING was sent."};
    }
    if (!profile.capabilities.read) return {ok: false, identity: version, reason: "This MINI build is limited to identity validation."};
    const scoped = scopedWriteEnabled() && transport === "usb-cdc", family = familyWriteEnabled(transport);
    return {ok: true, identity: version, read: true, write: fullWriteEnabled() || family || scoped,
      write_scope: fullWriteEnabled() ? "full" : family ? "protocol-families" : scoped ? "exact-requests" : "none"};
  }
  function acceptPong(pong, transport = null) {
    const result = inspectPong(pong, transport); identified = result.ok; observed = emptyState();
    identifiedTransport = result.ok ? transport : null; return result;
  }
  function resetIdentity() { identified = false; identifiedTransport = null; observed = emptyState(); }

  function need(value) { if (!value) throw new Error("incomplete protocol context"); }
  function parseTypes(lines) {
    need(/^(?:FXT end|FXT fin)$/.test(lines.at(-1) || ""));
    const types = Object.create(null), ids = new Set(); let cur = null;
    for (const line of lines.slice(0, -1)) {
      let m = /^FXT (\d+) (\S+) costo?=(\d+)(?: [^\s=]+=[^\s]+)*$/.exec(line);
      if (m) {
        need(integer(+m[1], 0, 65535) && !ids.has(+m[1]) && !Object.hasOwn(types, m[2]));
        cur = {params: Object.create(null)}; types[m[2]] = cur; ids.add(+m[1]); continue;
      }
      m = /^FXT\s+(\d+) (\S+) (-?\d+)\.\.(-?\d+) \((-?\d+)\)$/.exec(line);
      if (m) {
        need(cur && integer(+m[1], 0, 6) && !Object.hasOwn(cur.params, m[1]) &&
          [m[3], m[4], m[5]].every(v => integer(+v)) && +m[3] <= +m[5] && +m[5] <= +m[4]);
        cur.params[m[1]] = {min: +m[3], max: +m[4]}; continue;
      }
      need(cur && (/^FXT\s+os tiers=\d+,\d+,\d+(?: cost=\d+,\d+,\d+)?$/.test(line) || /^FXT\s+pp modes=\d+(?:,\d+)*$/.test(line)));
    }
    need(Object.keys(types).length > 0); return types;
  }
  function parseBlocks(lines) {
    need(/^FXS (?:peak|pico)=\d+ ticks skipped=\d+$/.test(lines.at(-1) || ""));
    const blocks = Object.create(null), positions = {P: 0, Q: 0}; let amp = false;
    for (const line of lines.slice(0, -1)) {
      const m = /^FX ([PQ])(\d+) id=(\d+) (\S+) on=([01]) p=(-?\d+(?:,-?\d+)*) ticks=\d+((?: [^\s=]+=[^\s]+)*)$/.exec(line);
      if (m) {
        const params = m[6].split(",").map(Number);
        need(+m[2] === positions[m[1]]++ && integer(+m[3], 0, 65535) && !Object.hasOwn(blocks, m[3]) &&
          params.length === 7 && params.every(v => integer(v)));
        const fields = new Set();
        for (const field of m[7].trim().split(/\s+/).filter(Boolean)) {
          const pair = /^(l|g|fu|irlen|mem|pcs)=(-?\d+(?:\/\d+)?)$/.exec(field);
          need(pair && !fields.has(pair[1])); fields.add(pair[1]);
          need(pair[1] === "irlen" ? /^\d+\/\d+$/.test(pair[2]) : integer(+pair[2], pair[1] === "g" ? -2147483648 : 0));
          if (pair[1] === "l") need(integer(+pair[2], 0, 2));
        }
        blocks[m[3]] = {type: m[4], bank: m[1], lane: +(m[7].match(/(?:^| )l=([012])(?: |$)/) || [0, 0])[1]}; continue;
      }
      if (/^FXS amp=[01](?: on=[01])?$/.test(line)) { need(!amp); amp = true; continue; }
      need(/^FXS cpu=\d+\/\d+ ticks \(\d+%\) mem_fx=\d+(?: B)?$/.test(line) ||
        /^FXS (?:eng|c1|lockq)=/.test(line) || /^FXMIX [PQ] \d+ -?\d+ -?\d+$/.test(line) ||
        /^FXMIX -?\d+ -?\d+ -?\d+ -?\d+$/.test(line) || /^FXXO [PQ] \d+ \d+(?: [01])?$/.test(line));
    }
    need(amp); return blocks;
  }
  function parsePresets(lines) {
    const end = /^PLIST (?:end|fin) (?:current|actual)=(-?\d+)$/.exec(lines.at(-1) || "");
    need(end && integer(+end[1], -1, 31));
    const presets = Object.create(null); let previous = -1;
    for (const line of lines.slice(0, -1)) {
      const m = /^PRE (\d+) \d+ -?\d+ -?\d+ '(.*)'(?: t=(-|[pq]\d+[ab]?(?:,[pq]\d+[ab]?)*) s=(\d+))?(?: col=[0-9a-f]{6})?(?: amp=[01])?$/.exec(line);
      need(m && integer(+m[1], 0, 31) && +m[1] > previous && m[2].length <= 23 && (m[4] == null || integer(+m[4], 0, 15)));
      previous = +m[1]; presets[m[1]] = m[2];
    }
    need(+end[1] === -1 || Object.hasOwn(presets, end[1]));
    return {presets, current: +end[1]};
  }
  function parseSnaps(lines) {
    const m = lines.length === 1 && /^SNAPS ([01]{4}) (?:current|actual)=(-?\d+)$/.exec(lines[0]);
    need(m && integer(+m[2], -1, 3) && (+m[2] === -1 || m[1][+m[2]] === "1"));
    return {present: m[1], current: +m[2]};
  }
  function invalidate(command) {
    if (command === "FXT") observed.types = null;
    if (["FXS", "FXA", "FXR", "FXP", "FXE", "PLOAD", "SNAP"].includes(command)) observed.blocks = null;
    if (["PLIST", "PSAVE", "PLOAD"].includes(command)) { observed.presets = null; observed.current = null; }
    if (["SNAPS", "SNAP", "SNAPSAVE", "PLOAD", "PSAVE"].includes(command)) observed.snaps = null;
    if (["GAIN", "LVL", "PLOAD", "SNAP"].includes(command)) observed.gain = null;
  }
  function observeReply(request, lines, timedOut = false, transport = null) {
    if (!identified || transport !== identifiedTransport || !familyWriteEnabled(transport)) return;
    const command = request.split(" ")[0];
    if (timedOut || !Array.isArray(lines) || lines.some(l => typeof l !== "string" || l.startsWith("ERR"))) { invalidate(command); return; }
    try {
      if (request === "FXT") observed.types = parseTypes(lines);
      else if (command === "GAIN") {
        const m = lines.length === 1 && /^GAIN in=(-?\d+) out=(-?\d+) dB$/.exec(lines[0]);
        need(m && integer(+m[1], -30, 12) && integer(+m[2], -30, 12));
        if (request !== "GAIN") {
          const q = /^GAIN (-?(?:0|[1-9]\d*)) (-?(?:0|[1-9]\d*))$/.exec(request);
          need(q && +q[1] === +m[1] && +q[2] === +m[2]);
        }
        observed.gain = [+m[1], +m[2]];
      } else if (request === "LVL") {
        const m = lines.length === 1 && /^LVL .*\bg=(-?\d+)\/(-?\d+)(?: |$)/.exec(lines[0]);
        need(m && integer(+m[1], -30, 12) && integer(+m[2], -30, 12));
        observed.gain = [+m[1], +m[2]];
      }
      else if (request === "FXS") observed.blocks = parseBlocks(lines);
      else if (command === "FXA" || command === "FXR") observed.blocks = null;
      else if (request === "PLIST") {
        const next = parsePresets(lines);
        if (observed.current !== null && observed.current !== next.current) { observed.blocks = null; observed.snaps = null; observed.gain = null; }
        Object.assign(observed, next);
      } else if (request === "SNAPS") observed.snaps = parseSnaps(lines);
      else if (command === "PSAVE") {
        const q = /^PSAVE (\d+) (.+)$/.exec(request), m = lines.length === 1 && /^PSAVE ok (\d+) '(.*)' \d+ blocks capture=-?\d+ ir=-?\d+$/.exec(lines[0]);
        need(q && m && q[1] === m[1] && q[2] === m[2] && observed.presets);
        observed.presets[q[1]] = q[2]; observed.current = +q[1];
      } else if (command === "PLOAD") {
        const q = /^PLOAD (\d+)$/.exec(request), m = lines.length === 1 && /^PLOAD ok (\d+) '/.exec(lines[0]);
        need(q && m && q[1] === m[1]); observed.current = +q[1]; observed.blocks = null; observed.snaps = null; observed.gain = null;
      } else if (command === "SNAP") {
        const q = /^SNAP ([0-3])$/.exec(request), m = lines.length === 1 && /^SNAP ok ([0-3]) missing=\d+ ms=\d+/.exec(lines[0]);
        need(q && m && q[1] === m[1]); observed.blocks = null; observed.snaps = null; observed.gain = null;
      } else if (command === "SNAPSAVE") {
        const q = /^SNAPSAVE ([0-3])$/.exec(request), m = lines.length === 1 && /^SNAPSAVE ok ([0-3]) preset=(-?\d+)$/.exec(lines[0]);
        need(q && m && q[1] === m[1] && +m[2] === observed.current && observed.snaps);
        const present = observed.snaps.present.split(""); present[+q[1]] = "1";
        observed.snaps = {present: present.join(""), current: +q[1]};
      }
    } catch (_) { invalidate(command); }
  }
  function familyPolicy(value, state) {
    // Only live catalog types and complete current serial chains are admitted.
    // CPU/memory admission remains the original firmware's decision.
    let m = /^FXA ([PQ]) 99 ([a-z0-9_]+)$/.exec(value);
    if (m) {
      const blocks = state.blocks && Object.values(state.blocks);
      return !!(blocks && state.types && Object.hasOwn(state.types, m[2]) &&
        blocks.every(b => b.lane === 0) && blocks.length < 16 &&
        blocks.filter(b => b.bank === m[1]).length < 10);
    }
    m = /^FXR (0|[1-9]\d*)$/.exec(value);
    if (m) return !!(state.blocks && Object.hasOwn(state.blocks, m[1]) &&
      Object.values(state.blocks).every(b => b.lane === 0));
    m = /^GAIN (-?(?:0|[1-9]\d*)) (-?(?:0|[1-9]\d*))$/.exec(value);
    if (m) return !!state.gain && integer(+m[1], -30, 12) && integer(+m[2], -30, 12);
    m = /^FXP (0|[1-9]\d*) ([0-6]) (-?(?:0|[1-9]\d*))$/.exec(value);
    if (m) {
      const block = state.blocks && state.blocks[m[1]], type = block && state.types && state.types[block.type], param = type && type.params[m[2]];
      return !!param && integer(+m[3], param.min, param.max);
    }
    m = /^FXE (0|[1-9]\d*) [01]$/.exec(value);
    if (m) return !!(state.blocks && Object.hasOwn(state.blocks, m[1]));
    m = /^PLOAD ([0-9]|[12][0-9]|3[01])$/.exec(value);
    if (m) return !!(state.presets && Object.hasOwn(state.presets, m[1]));
    m = /^PSAVE ([0-9]|[12][0-9]|3[01]) ([^\x00-\x1f\x7f]+)$/.exec(value);
    if (m) {
      if (!state.presets || !state.blocks || m[2].length > 23) return false;
      try { return encodeURIComponent(value).replace(/%[A-F0-9]{2}/g, "x").length <= 190; } catch (_) { return false; }
    }
    m = /^SNAP ([0-3])$/.exec(value);
    if (m) return !!(state.snaps && state.snaps.present[+m[1]] === "1");
    m = /^SNAPSAVE ([0-3])$/.exec(value);
    return !!(m && state.snaps && state.presets && integer(state.current, 0, 31) && Object.hasOwn(state.presets, state.current));
  }
  function isRead(line) {
    return query.has(line) || line === "AMPEQ info" || /^EVT \d+$/.test(line) ||
      /^(CREAD|IREAD) \d+ \d+ \d+$/.test(line);
  }
  function commandPolicy(value, transport = null, state = observed) {
    if (typeof value !== "string" || /[\r\n\0]/.test(value) || !value || value !== value.trim()) return {allowed: false, reason: "malformed command"};
    if (value === "PING" && profile.capabilities.identity) return {allowed: true, capability: "identity"};
    if (!identified) return {allowed: false, reason: "MINI firmware identity/build not accepted"};
    const command = value.split(" ")[0];
    if (panelCommands.has(command) && !profile.capabilities.panel) return {allowed: false, reason: "MINI switch/LED mapping is not validated"};
    if (isRead(value) && profile.capabilities.read) return {allowed: true, capability: "read"};
    if (familyWriteEnabled(transport) && identifiedTransport === transport && familyCommands.has(command) &&
        profile.family_capabilities[transport].includes(command)) {
      return familyPolicy(value, state) ? {allowed: true, capability: "family", command, transport} :
        {allowed: false, reason: "command is outside the current FXT/FXS/PLIST/SNAPS data"};
    }
    if (scopedWriteEnabled() && scopedCommands.has(command) && transport === "usb-cdc" && identifiedTransport === transport) {
      const requests = (profile.command_capabilities || {})[command];
      if (Array.isArray(requests) && requests.includes(value)) return {allowed: true, capability: "command", command};
    }
    if (fullWriteEnabled()) return {allowed: true, capability: "write"};
    return {allowed: false, reason: "firmware mutations are not validated for this MINI build"};
  }
  function preflight(commands, transport = null) {
    if (!Array.isArray(commands) || !commands.length) return {allowed: false, reason: "empty command operation"};
    const state = {...observed, presets: observed.presets && {...observed.presets}};
    for (const command of commands) {
      const result = commandPolicy(command, transport, state);
      if (!result.allowed) return {allowed: false, command, reason: result.reason};
      // Planning PSAVE changes the destination of a following scene save.
      // Only the actual matching ACK updates observed state on the wire path.
      if (result.capability === "family" && command.startsWith("PSAVE ")) {
        const [, slot, name] = /^PSAVE (\d+) (.+)$/.exec(command);
        state.presets[slot] = name; state.current = +slot;
      }
    }
    return {allowed: true};
  }
  function panelSvg() {
    // A schematic of the three switches, not a fabricated G/B panel or pin map.
    return '<rect x="4" y="4" width="928" height="188" rx="18" fill="#193437" stroke="#638082"/>' +
      '<text x="468" y="42" fill="#eef1f2" text-anchor="middle" font-size="22">HyperRig MINI</text>' +
      ["A", "B", "C"].map((s, i) => '<circle cx="' + (210 + i * 258) + '" cy="113" r="25" fill="#343c42" stroke="#96a4ab"/>' +
        '<text x="' + (210 + i * 258) + '" y="168" fill="#eef1f2" text-anchor="middle" font-size="18">' + s + '</text>').join("");
  }
  root.HyperRigMini = Object.freeze({profile, inspectPong, acceptPong, resetIdentity, commandPolicy,
    isRead, preflight, fullWriteEnabled, scopedWriteEnabled, familyWriteEnabled, observeReply, panelSvg});
})(globalThis);
