/* Pure preflight for the original editor. No transport, replacement UI or I/O.
 * Additions remain serial appends; unsupported compound edits stop before TX. */
(function (root) {
  "use strict";
  function appendLocation(segs, loc) {
    if (!Array.isArray(segs) || segs.some(s => !s || !["fx", "amp", "grp"].includes(s.k)) ||
        segs.filter(s => s.k === "amp").length > 1) return false;
    const target = loc || {t: "serial", si: segs.length};
    return ["serial", "newgrp", "lane"].includes(target.t) && Number.isInteger(target.si) && target.si >= 0 &&
      target.si <= segs.length && (target.t !== "lane" || !!segs[target.si] && segs[target.si].k === "grp");
  }
  function add(type, segs, loc, transport, given) {      // given: the section, when the page has found it
    if (!appendLocation(segs, loc)) return {allowed: false,
      reason: "A block cannot be added at that place."};
    const target = loc || {t: "serial", si: segs.length};
    const amp = segs.findIndex(s => s.k === "amp");
    const bank = given || (target.t === "lane" ? segs[target.si].bank : amp < 0 || target.si <= amp ? "P" : "Q");
    return root.HyperRigMini.commandPolicy(`FXA ${bank} 99 ${type}`, transport);
  }
  function compound(commands, transport) {
    return commands.length ? root.HyperRigMini.preflight(commands, transport) : {allowed: true};
  }
  root.HyperRigMiniFX = Object.freeze({appendLocation, add, compound});
})(globalThis);
