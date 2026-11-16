"use strict";
// Android presentation only: the pinned MINI command policy is unchanged.
document.addEventListener("DOMContentLoaded", () => {
  const status = document.getElementById("miniPortStatus");
  if (status && location.hash !== "#demo")
    status.textContent = "HyperRig MINI - Android preview - Bluetooth read only.";
  const note = document.createElement("div");
  note.textContent = "Android preview: Bluetooth read only. Install firmware using the Windows app.";
  note.style.cssText = "padding:8px 12px;background:#163c3b;color:#d7fff3;font:13px system-ui;text-align:center";
  document.body.prepend(note);
});
