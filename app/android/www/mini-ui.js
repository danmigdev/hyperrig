/* Small board-specific UI extension. The original editor retains its complete
 * FX/routing/preset/snapshot/NAM/A2-Lite/IR implementation and demo engine. */
(function () {
  "use strict";
  const p = HyperRigMini.profile;
  const demo = location.hash === "#demo";
  const commandNames = {FXA: "add serial effects", FXR: "remove effects", FXP: "effect parameters", FXE: "effect bypass", PLOAD: "load presets",
    PSAVE: "save presets", PDEL: "delete presets", SNAP: "select scenes", SNAPSAVE: "save scenes", GAIN: "input and output levels"};
  const scoped = Object.keys(p.command_capabilities || {}).map(c => commandNames[c]).filter(Boolean);
  const families = Object.entries(p.family_capabilities || {}).filter(([tr]) => HyperRigMini.familyWriteEnabled(tr))
    .map(([tr, commands]) => (tr === "usb-cdc" ? "USB" : "Bluetooth") + ": " + commands.map(c => commandNames[c]).filter(Boolean).join(", "));
  const note = document.createElement("div");
  note.id = "miniPortStatus"; note.setAttribute("role", "status");
  note.style.cssText = "padding:10px 18px;background:#5a3d00;color:#fff1cf;border-bottom:1px solid #45636b;font-size:13px";
  note.textContent = demo ? "HyperRig for TANK-MINI · Offline demo" :
    "HyperRig 0.5.0 · " +
    "Connect the pedal by USB to begin (editor mini-product-38).";
  const top = document.querySelector(".top"); if (top) top.after(note);
  document.title = "HyperRig editor mini-product-38";
  // Original G/B installer instructions must not tell MINI owners to install a
  // G/B image. A MINI installer is deliberately absent from this build.
  for (const id of ["guideLink", "fwHow"]) {
    const el = document.getElementById(id); if (el) { el.removeAttribute("href"); el.textContent = "HyperRig MINI installation guide"; }
  }
  const intro = document.querySelector("#firstUse ol");
  if (intro) {
    // setLock cached these two nodes' text before this board extension loads.
    // Preserve their identity/IDs so subsequent original connection updates work.
    const browserStep = intro.querySelector("#fuB"), connectStep = intro.querySelector("#fuC");
    if (!browserStep || !connectStep) throw new Error("Original connection help nodes are missing");
    const firmwareStep = document.createElement("li");
    firmwareStep.textContent = "This editor requires HyperRig for TANK-MINI.";
    intro.replaceChildren(browserStep, firmwareStep, connectStep);
  }
  for (const id of ["fsBtn", "fswBtn", "stageBtn"]) {
    const el = document.getElementById(id);
    if (el && !p.capabilities.panel) { el.disabled = true; el.title = "MINI switch and LED assignments still require validation"; }
  }
  // Do not silently navigate to the G/B package instructions from this build.
  for (const a of document.querySelectorAll('a[href*="hyperrig.invalid/#download"]')) a.removeAttribute("href");
})();
