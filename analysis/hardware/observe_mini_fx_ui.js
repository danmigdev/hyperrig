/* Passive root-operated smoke-test recording. No policy grants or commands. */
(() => {
  'use strict';
  if (window.__miniFXUIAudit || !S.connected || DEMO || Pedal.tr !== SerialTransport ||
      !SerialTransport.isOpen()) throw Error('One connected real editor required');
  const state = {seq: 0, commands: [], tx: [], rx: [], inputs: [], detached: false,
    rxBytes: 0, truncated: false, started: new Date().toISOString()};
  const stamp = () => ({seq: ++state.seq, utc: new Date().toISOString(), time: performance.now()});
  const hex = bytes => Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  const tr = SerialTransport, reader = tr.reader, writer = tr.writer;
  const old = {cmd: Pedal.cmd, read: reader.read, write: writer.write};
  reader.read = async function (...args) {
    const result = await old.read.apply(this, args);
    if (!state.detached && result.value) {
      state.rxBytes += result.value.byteLength;
      if (state.rxBytes <= 2 * 1024 * 1024) state.rx.push({...stamp(), hex: hex(result.value)});
      else state.truncated = true;
    }
    return result;
  };
  writer.write = async function (bytes) {
    const item = {...stamp(), hex: hex(bytes), line: new TextDecoder().decode(bytes), completed: false};
    state.tx.push(item);
    try { const result = await old.write.call(this, bytes); item.completed = true; return result; }
    catch (error) { item.error = String(error); throw error; }
  };
  Pedal.cmd = async function (line, ...args) {
    const item = {...stamp(), line, completed: false}; state.commands.push(item);
    try {
      const result = await old.cmd.call(this, line, ...args);
      item.reply = result; item.completed = true; item.end = stamp(); return result;
    } catch (error) { item.error = String(error); item.end = stamp(); throw error; }
  };
  const listener = event => {
    const target = event.target;
    state.inputs.push({...stamp(), event: event.type, trusted: event.isTrusted,
      key: event.key || null, id: target.id || null, tag: target.tagName,
      role: target.getAttribute?.('role'), text: (target.textContent || '').slice(0, 100),
      label: target.getAttribute?.('aria-label'), dataId: target.closest?.('[data-id]')?.dataset.id});
  };
  for (const event of ['click', 'keydown']) document.addEventListener(event, listener, true);
  Object.defineProperty(window, '__miniFXUIAudit', {value: {state, async detach() {
    await Pedal.chain;
    reader.read = old.read; writer.write = old.write; Pedal.cmd = old.cmd;
    for (const event of ['click', 'keydown']) document.removeEventListener(event, listener, true);
    state.detached = true; state.finished = new Date().toISOString(); return state;
  }}});
  return {installed: true, nativePort: tr.info(), policyChanged: false};
})()
