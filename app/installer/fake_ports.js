/* A MIDI port as Chromium's, for the tests and for the check of the built program: the rules of midi_port.cc and midi_input.cc
 * (third_party/blink/renderer/modules/webmidi), whose close() is carried out in a later task. Not part of the program. */
"use strict";
(function (root) {
  function fakePort({ id, name, type, send = () => {} }) {
    const port = { id, name, type, state: "connected", manufacturer: "", connection: "closed", onstatechange: null };
    let opening = false, heard = null;
    const later = f => new Promise(done => setTimeout(() => { f(); done(port); }, 0));
    const implicit = () => { if (port.connection === "open" || opening) return; opening = true; setTimeout(() => { opening = false; port.connection = "open"; }, 0); };
    port.open = () => port.connection === "open" ? Promise.resolve(port) : later(() => { port.connection = "open"; });
    port.close = () => port.connection === "closed" ? Promise.resolve(port) : later(() => { port.connection = "closed"; });
    Object.defineProperty(port, "onmidimessage", { enumerable: true, get: () => heard, set: f => { heard = f; if (f) implicit(); } });
    port.send = bytes => {
      if (port.state !== "connected") throw new Error("gone");
      implicit();
      send(bytes);
    };
    port.deliver = bytes => { if (type === "input" && port.connection === "open" && heard) heard({ data: Uint8Array.from(bytes), port }); };
    return port;
  }
  /* HyperRig's console as Web Serial gives it. The first writes after each opening are lost: `lose` of them, as the pedal does now
   * and then. answer(line) gives the text to come back, or null. */
  function fakeSerialPort({ answer, lose = 0, refuse = 0 }) {
    let opened = false, lost = 0, refused = 0, queue = [], take = null, end = null;
    const give = text => { if (take) { const f = take; take = null; f({ value: new TextEncoder().encode(text), done: false }); } else queue.push(text); };
    const port = {
      getInfo: () => ({ usbVendorId: 0x4c4a, usbProductId: 0x5155 }),
      async open() {
        if (opened) throw new Error("the port is already open");
        if (refused < refuse) { refused++; throw new Error("the port is in use"); }
        opened = true; lost = lose; queue = []; take = end = null;
      },
      async close() { opened = false; if (end) end(); },
      get readable() {
        return { getReader: () => ({
          read: () => queue.length ? Promise.resolve({ value: new TextEncoder().encode(queue.shift()), done: false }) :
            new Promise(done => { take = done; end = () => { take = null; done({ value: undefined, done: true }); }; }),
          cancel: async () => { if (end) end(); }, releaseLock() {} }) };
      },
      get writable() {
        return { getWriter: () => ({ write: async bytes => {
          if (lost > 0) { lost--; return; }
          const line = new TextDecoder().decode(bytes).trim();
          Promise.resolve(answer(line)).then(text => { if (text !== null && text !== undefined) give(text + "\n"); });
        }, releaseLock() {} }) };
      },
    };
    return port;
  }
  const api = { fakePort, fakeSerialPort };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrFakePorts = api;
})(typeof globalThis === "object" ? globalThis : this);
