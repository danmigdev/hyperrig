/* Runtime timeout extension only; no serial open, write or reconnect here. */
function installMiniSerialOpenTimeout(transport) {
  const expected = "async open(known) {                         /* known: un puerto ya autorizado (reconexi\u00f3n al recargar, sin preguntar) */\n    this.port = known || await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x3654 }] });\n    /* al recargar con el puerto abierto, el navegador a veces tarda en soltarlo y open() queda colgado: plazo de 5 s */\n    let to;\n    try {\n      await Promise.race([this.port.open({ baudRate: 115200 }),\n        new Promise((_, rej) => { to = setTimeout(() => rej(new Error(\"the port did not respond when opening: unplug the USB cable and plug it back in\")), 5000); })]);\n    } catch (e) { const p = this.port; this.port = null; try { await p.close(); } catch (e2) {} throw e; }\n    finally { clearTimeout(to); }\n    this.writer = this.port.writable.getWriter();\n    this.readLoop();\n  }";
  const anchor = ')), 5000); })]);';
  if (!transport || transport.port !== null || typeof transport.open !== 'function')
    throw Error('Original unopened SerialTransport required');
  const source = Function.prototype.toString.call(transport.open).replace(/\r\n/g, '\n');
  if (source !== expected || source.split(anchor).length !== 2)
    throw Error('Original SerialTransport.open source differs; timeout not changed');
  const extended = source.replace(anchor, ')), 30000); })]);');
  const replacement = (0, eval)('({' + extended + '})').open;
  if (Function.prototype.toString.call(replacement) !== extended)
    throw Error('Derived SerialTransport.open source differs');
  transport.open = replacement;
  return {"CDP_socket_timeout_seconds": 45, "app_html_changed": false, "extended_source_sha256": "0f53053aa248dc33dd6394bc0ae29d9937acb30542a6ed21fce0944e0fb222c0", "kind": "original-serial-open-timeout-v1", "native_open_unchanged": true, "original_source_sha256": "c42092eb3b3368bde0896b8ed57fc0d4c79a33e2c0ac494537f971ab4c1a6558", "original_timeout_ms": 5000, "reconnect_added": false, "runtime_only": true, "timeout_ms": 30000};
}
