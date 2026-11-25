/* The pedal's MIDI ports, as the browser's Web MIDI gives them, for the core: one link per port at a time.
 *
 * Chromium carries out close() in a later task, and open() on a port that is still open does nothing: a port that is closed and
 * opened again at once ends up closed. Messages still go out, since send() opens its own side, but what the pedal answers is
 * dropped (third_party/blink/renderer/modules/webmidi/midi_port.cc and midi_input.cc). So an opening waits for the closing of
 * what used the port before, and the two ways the program uses a port, looking around and a job, never share one. For the page
 * and for node. */
"use strict";
(function (root) {
  const plain = name => String(name || "").replace(/^\d+-\s*/, "");

  function midiOf(access, { patience = 15000 } = {}) {
    const free = new Map();       // of each pair of ports, when the link before has closed it
    const connected = map => [...map.values()].filter(p => p.state === "connected");
    function pairs() {
      const outputs = connected(access.outputs), out = [];
      for (const input of connected(access.inputs)) {
        let i = outputs.findIndex(o => o.name === input.name);
        if (i < 0) i = outputs.findIndex(o => plain(o.name) === plain(input.name));
        if (i >= 0) out.push({ id: input.id + "|" + outputs[i].id, name: plain(input.name), input, output: outputs.splice(i, 1)[0] });
      }
      return out;
    }
    const patient = before => new Promise(done => { const timer = setTimeout(() => done(false), patience); before.then(() => { clearTimeout(timer); done(true); }); });
    async function open(id) {
      const before = free.get(id);
      let release;
      const released = new Promise(done => { release = done; });
      free.set(id, released);
      try {
        if (before && !await patient(before)) throw Object.assign(new Error("the port is in use"), { code: "busy" });
        const p = pairs().find(x => x.id === id);
        if (!p) throw Object.assign(new Error("the port has gone"), { code: "gone" });
        await Promise.all([p.input.open(), p.output.open()]);
        let closed = false;
        const link = { onmessage: null, ongone: null, send: bytes => p.output.send(bytes), close: () => {
          if (closed) return;
          closed = true;
          p.input.onmidimessage = p.input.onstatechange = p.output.onstatechange = null;
          Promise.allSettled([p.input.close(), p.output.close()]).then(release);
        } };
        p.input.onmidimessage = e => { if (e.data[0] === 0xf0 && link.onmessage) link.onmessage(Uint8Array.from(e.data)); };
        p.input.onstatechange = p.output.onstatechange = e => { if (e.port.state === "disconnected" && link.ongone) link.ongone(); };
        return link;
      } catch (e) { release(); throw e; }
    }
    return { list: async () => pairs().map(({ id, name }) => ({ id, name })), open };
  }

  const api = { midiOf };
  if (typeof module === "object" && module.exports) module.exports = api; else root.HrWebMidi = api;
})(typeof globalThis === "object" ? globalThis : this);
