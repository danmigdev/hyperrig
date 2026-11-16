/* Small board-specific UI extension. The original editor retains its complete
 * FX/routing/preset/snapshot/NAM/A2-Lite/IR implementation and demo engine. */
(function () {
  "use strict";
  const p = HyperRigMini.profile;
  const demo = location.hash === "#demo";
  const commandNames = {FXP: "effect parameters", FXE: "effect bypass", PLOAD: "load presets",
    PSAVE: "save presets", PDEL: "delete presets", SNAP: "select scenes", SNAPSAVE: "save scenes", GAIN: "input and output levels"};
  const scoped = Object.keys(p.command_capabilities || {}).map(c => commandNames[c]).filter(Boolean);
  const families = Object.entries(p.family_capabilities || {}).filter(([tr]) => HyperRigMini.familyWriteEnabled(tr))
    .map(([tr, commands]) => (tr === "usb-cdc" ? "USB" : "Bluetooth") + ": " + commands.map(c => commandNames[c]).filter(Boolean).join(", "));
  const note = document.createElement("div");
  note.id = "miniPortStatus"; note.setAttribute("role", "status");
  note.style.cssText = "padding:10px 18px;background:#172b30;color:#e3edef;border-bottom:1px solid #45636b;font-size:13px";
  note.textContent = demo ? "HyperRig MINI · Offline demo: no pedal connected and no pedal audio." :
    p.capabilities.read ? "HyperRig MINI · Profile " + p.firmware_version + (HyperRigMini.fullWriteEnabled() ? " · controls enabled for this build." :
      families.length ? " · " + families.join(". ") + "." :
      HyperRigMini.scopedWriteEnabled() ? " · USB testing limited to " + scoped.join(", ") + ". Only verified presets and values are allowed." : " · port verification: read only; changes blocked.") :
    "HyperRig MINI · Port in development. Connection limited to PING until a build is assigned. Explore the editor in Demo.";
  const top = document.querySelector(".top"); if (top) top.after(note);
  document.title = "HyperRig for TANK MINI";
  // Original G/B installer instructions must not tell MINI owners to install a
  // G/B image. A MINI installer is deliberately absent from this build.
  for (const id of ["guideLink", "fwHow"]) {
    const el = document.getElementById(id); if (el) { el.removeAttribute("href"); el.textContent = "MINI firmware port in development"; }
  }
  const intro = document.querySelector("#firstUse ol");
  if (intro) {
    // setLock cached these two nodes' text before this board extension loads.
    // Preserve their identity/IDs so subsequent original connection updates work.
    const browserStep = intro.querySelector("#fuB"), connectStep = intro.querySelector("#fuC");
    if (!browserStep || !connectStep) throw new Error("Original connection help nodes are missing");
    const firmwareStep = document.createElement("li");
    firmwareStep.textContent = "This editor requires HyperRig for TANK MINI.";
    intro.replaceChildren(browserStep, firmwareStep, connectStep);
  }
  for (const id of ["fsBtn", "fswBtn", "stageBtn"]) {
    const el = document.getElementById(id);
    if (el && !p.capabilities.panel) { el.disabled = true; el.title = "MINI switch and LED assignments still require validation"; }
  }
  // Do not silently navigate to the G/B package instructions from this build.
  for (const a of document.querySelectorAll('a[href*="hyperrig.invalid/#download"]')) a.removeAttribute("href");
})();
