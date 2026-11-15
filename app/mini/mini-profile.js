/* HyperRig MINI board adapter for the complete original UltraRig editor.
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
  const scopedCommands = new Set(["FXP", "FXE", "PLOAD", "PSAVE", "PDEL", "SNAP", "SNAPSAVE"]);
  let identified = false, identifiedTransport = null;
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
    const scoped = scopedWriteEnabled() && transport === "usb-cdc";
    return {ok: true, identity: version, read: true, write: fullWriteEnabled() || scoped,
      write_scope: fullWriteEnabled() ? "full" : scoped ? "exact-requests" : "none"};
  }
  function acceptPong(pong, transport = null) {
    const result = inspectPong(pong, transport); identified = result.ok;
    identifiedTransport = result.ok ? transport : null; return result;
  }
  function resetIdentity() { identified = false; identifiedTransport = null; }
  function isRead(line) {
    return query.has(line) || line === "AMPEQ info" || /^EVT \d+$/.test(line) ||
      /^(CREAD|IREAD) \d+ \d+ \d+$/.test(line);
  }
  function commandPolicy(value, transport = null) {
    if (typeof value !== "string" || /[\r\n\0]/.test(value) || !value || value !== value.trim()) return {allowed: false, reason: "malformed command"};
    if (value === "PING" && profile.capabilities.identity) return {allowed: true, capability: "identity"};
    if (!identified) return {allowed: false, reason: "MINI firmware identity/build not accepted"};
    const command = value.split(" ")[0];
    if (panelCommands.has(command) && !profile.capabilities.panel) return {allowed: false, reason: "MINI switch/LED mapping is not validated"};
    if (isRead(value) && profile.capabilities.read) return {allowed: true, capability: "read"};
    if (scopedWriteEnabled() && scopedCommands.has(command) && transport === "usb-cdc" && identifiedTransport === transport) {
      const requests = (profile.command_capabilities || {})[command];
      if (Array.isArray(requests) && requests.includes(value)) return {allowed: true, capability: "command", command};
    }
    if (fullWriteEnabled()) return {allowed: true, capability: "write"};
    return {allowed: false, reason: "firmware mutations are not validated for this MINI build"};
  }
  function preflight(commands, transport = null) {
    if (!Array.isArray(commands) || !commands.length) return {allowed: false, reason: "empty command operation"};
    for (const command of commands) {
      const result = commandPolicy(command, transport);
      if (!result.allowed) return {allowed: false, command, reason: result.reason};
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
    isRead, preflight, fullWriteEnabled, scopedWriteEnabled, panelSvg});
})(globalThis);
