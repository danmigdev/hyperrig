/* Pure preflight for the original editor. No transport, replacement UI or I/O.
 * Additions remain serial appends; unsupported compound edits stop before TX. */
(function (root) {
  "use strict";
  function appendLocation(segs, loc) {
    if (!Array.isArray(segs) || !segs.length ||
        segs.some(s => !s || !["fx", "amp"].includes(s.k)) ||
        segs.filter(s => s.k === "amp").length !== 1) return false;
    const target = loc || {t: "serial", si: segs.length};
    return target.t === "serial" && Number.isInteger(target.si) &&
      (target.si === segs.findIndex(s => s.k === "amp") || target.si === segs.length);
  }
  function add(type, segs, loc, transport) {
    if (!appendLocation(segs, loc)) return {allowed: false,
      reason: "Add at the end of the serial Pre or Post section. Moving and parallel routing are not enabled."};
    const target = loc || {t: "serial", si: segs.length};
    const bank = target.si === segs.findIndex(s => s.k === "amp") ? "P" : "Q";
    return root.HyperRigMini.commandPolicy(`FXA ${bank} 99 ${type}`, transport);
  }
  function compound(commands, transport) {
    return commands.length ? root.HyperRigMini.preflight(commands, transport) : {allowed: true};
  }
  root.HyperRigMiniFX = Object.freeze({appendLocation, add, compound});
})(globalThis);
