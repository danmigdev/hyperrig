/* Runtime timeout adjustment; no serial I/O occurs during installation. */
function installMiniSerialOpenTimeout(transport) {
  const expected = "async open(known) {                                                                                                     \n    this.port = known || await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x3654 }] });\n                                                                                                                        \n    let to;\n    try {\n      await Promise.race([this.port.open({ baudRate: 115200 }),\n        new Promise((_, rej) => { to = setTimeout(() => rej(new Error(\"the port did not respond when opening: unplug the USB cable and plug it back in\")), 5000); })]);\n    } catch (e) { const p = this.port; this.port = null; try { await p.close(); } catch (e2) {} throw e; }\n    finally { clearTimeout(to); }\n    this.writer = this.port.writable.getWriter();\n    this.readLoop();\n  }";
  const extended = "async open(known) {                                                                                                     \n    this.port = known || await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x3654 }] });\n                                                                                                                        \n    let to;\n    try {\n      await Promise.race([this.port.open({ baudRate: 115200 }),\n        new Promise((_, rej) => { to = setTimeout(() => rej(new Error(\"the port did not respond when opening: unplug the USB cable and plug it back in\")), 30000); })]);\n    } catch (e) { const p = this.port; this.port = null; try { await p.close(); } catch (e2) {} throw e; }\n    finally { clearTimeout(to); }\n    this.writer = this.port.writable.getWriter();\n    this.readLoop();\n  }";
  if (!transport || transport.port !== null || typeof transport.open !== "function")
    throw Error("Unopened HyperRig SerialTransport required");
  if (Function.prototype.toString.call(transport.open).replace(/\r\n/g, "\n") !== expected)
    throw Error("SerialTransport.open differs from the reviewed English editor");
  const replacement = (0, eval)("({" + extended + "})").open;
  if (Function.prototype.toString.call(replacement) !== extended)
    throw Error("Derived serial timeout differs");
  transport.open = replacement;
  return {"kind": "hyperrig-english-serial-open-timeout-v1", "original_timeout_ms": 5000, "timeout_ms": 30000, "original_source_sha256": "f1db6fa217cc2d893cbf8f6e05da891aaba97fb77fa8606e2495d06fa6e74242", "extended_source_sha256": "576962aae24e85f2c2c3852d9188412283e4b7c819ccbcda7fe1d7b0aecda4c4", "native_open_unchanged": true, "reconnect_added": false, "runtime_only": true, "CDP_socket_timeout_seconds": 45};
}
