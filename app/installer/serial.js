/* HyperRig's console over Web Serial, for the core: one conversation per opening of the port.
 *
 * The pedal can miss the first command after the port is opened. The editor asks PING up to five times, 700 ms apart, for the same
 * reason. So a question that changes nothing is asked again, in the same conversation; what does something is asked once, after
 * a question that was answered. For the page and for node. */
"use strict";
(function (root) {
  // HyperRig on the pedal: the vendor of the chip with HyperRig's product; before the released 0.2.0, 3654.
  const isPedal = i => i.usbVendorId === undefined || i.usbVendorId === 0x3654 || (i.usbVendorId === 0x4c4a && i.usbProductId === 0x5155);
  const nap = ms => new Promise(done => setTimeout(done, ms));

  function serialOf(serial, { log = () => {}, opening = 8, gap = 400 } = {}) {
    const ports = async () => (await serial.getPorts()).filter(p => isPedal(p.getInfo() || {}));

    /* Another program, or a page of this one that is going away, may have it for a moment. */
    async function open(port) {
      for (let i = 0; ; i++) {
        try { return await port.open({ baudRate: 115200 }); } catch (e) { if (i + 1 >= opening) throw e; await nap(gap); }
      }
    }

    async function talk(task) {
      const port = (await ports())[0];
      if (!port) return null;
      try { await open(port); } catch (e) { log("serial: " + e.message); return null; }
      const reader = port.readable.getReader(), writer = port.writable.getWriter(), decoder = new TextDecoder(), lines = [];
      let text = "", ended = false, wake = () => {};
      const listen = (async () => {
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          text += decoder.decode(value, { stream: true });
          const parts = text.split(/\r?\n/);
          text = parts.pop();
          lines.push(...parts);
          wake();
        }
      })().catch(() => {}).finally(() => { ended = true; wake(); });
      async function hear(start, ms) {
        const until = Date.now() + ms;
        for (;;) {
          const i = lines.findIndex(l => l.startsWith(start));
          if (i >= 0) { const line = lines[i]; lines.splice(0, i + 1); return line; }
          const left = until - Date.now();
          if (ended || left <= 0) return null;
          await Promise.race([new Promise(done => { wake = done; }), nap(left)]);
        }
      }
      async function ask(line, start, { ms = 700, tries = 1 } = {}) {
        for (let i = 0; i < tries; i++) {
          lines.length = 0;
          await writer.write(new TextEncoder().encode(line + "\n"));
          const answer = await hear(start, ms);
          if (answer !== null) return answer;
          if (ended) break;
        }
        return null;
      }
      try { return await task(ask); } finally {
        const over = (async () => {
          await reader.cancel().catch(() => {});
          await listen;
          reader.releaseLock();
          writer.releaseLock();
          await port.close().catch(() => {});
        })().catch(() => {});
        await Promise.race([over, nap(1500)]);          // a pedal that has just restarted may never answer the closing
      }
    }
    return { present: async () => (await ports()).length > 0, talk };
  }

  const api = { serialOf };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrSerial = api;
})(typeof globalThis === "object" ? globalThis : this);
