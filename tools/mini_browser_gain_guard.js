/* In-memory instrumentation for the two-key Output GAIN trial. No app-file edits. */
function installMiniBrowserGainGuard(config) {
  'use strict';
  const nativeSerial = navigator.serial;
  const pair = x => Array.isArray(x) && x.length === 2 && x.every(v => Number.isInteger(v) && v >= -30 && v <= 12);
  if (!pair(config.gain) || config.gain[1] <= -30) throw new Error('Observed output gain must be above -30 dB');
  const before = [...config.gain], down = [before[0], before[1] - 1];
  const state = {live: config.live === true, appInstalled: false, requestEnabled: false,
    requests: 0, opens: 0, closes: 0, pongMatched: false, fatal: null, stopped: false,
    phase: 'initial', mutations: 0, epoch: 0, observations: {}, events: [], wire: [],
    replies: [], commands: [], rx: [], rxBytes: 0, ui: [], closeError: null};
  const event = (kind, data = {}) => state.events.push({kind, time: performance.now(), ...data});
  const poison = message => { state.fatal = String(message); state.stopped = true; };
  const deny = message => { poison(message); throw new DOMException(message, 'NotAllowedError'); };
  const hex = bytes => Array.from(bytes, x => x.toString(16).padStart(2, '0')).join('');
  const queries = new Set(('PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST ' +
    'LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE LIFE CRASH CLKSTATE GAIN BPM PCOLOR').split(' '));
  const readonly = line => queries.has(line) || line === 'AMPEQ info' || /^EVT [0-9]{1,10}$/.test(line);
  const equal = (a, b) => Array.isArray(a) && a.length === b.length && a.every((v, i) => v === b[i]);
  const gainReply = lines => {
    const match = Array.isArray(lines) && lines.length === 1 && /^GAIN in=(-?\d+) out=(-?\d+) dB$/.exec(lines[0]);
    return match ? [Number(match[1]), Number(match[2])] : null;
  };
  const request = values => 'GAIN ' + values.join(' ');
  const knob = () => document.querySelector('#gOut .knob[role="slider"]');
  const current = () => typeof S !== 'undefined' && S.gain;
  const checkUI = values => {
    const k = knob();
    if (!k || !equal(current(), values) || Number(k.getAttribute('aria-valuenow')) !== values[1] ||
        k.getAttribute('aria-valuemin') !== '-30' || k.getAttribute('aria-valuemax') !== '12' ||
        k.dataset.k !== 'Output' || !k.getAttribute('aria-label') || !k.getBoundingClientRect().width ||
        !k.getBoundingClientRect().height || document.activeElement !== k)
      return deny('Actual Output knob, focus and S.gain differ from verified readback');
    return k;
  };
  const noEvents = {addEventListener() {}, removeEventListener() {}};
  const blocked = name => async () => deny('Browser GAIN trial blocks ' + name);
  Object.defineProperty(navigator, 'usb', {configurable: true, value: {...noEvents,
    getDevices: async () => [], requestDevice: blocked('USB')}});
  Object.defineProperty(navigator, 'bluetooth', {configurable: true, value: {...noEvents,
    getAvailability: async () => false, getDevices: async () => [], requestDevice: blocked('Bluetooth')}});
  Object.defineProperty(navigator, 'requestMIDIAccess', {configurable: true, value: blocked('MIDI')});
  Object.defineProperty(navigator, 'serial', {configurable: true, value: {...noEvents,
    getPorts: async () => { event('serial_getPorts_stub'); return []; },
    requestPort: async () => {
      if (!state.live || !state.requestEnabled || state.stopped || state.requests !== 0 || !nativeSerial)
        return deny('Exactly one explicitly enabled serial chooser is permitted');
      state.requests++; event('serial_request_intent');
      const port = await nativeSerial.requestPort({filters: [{usbVendorId: 0x3654, usbProductId: 0x5155}]});
      const check = () => {
        const info = port.getInfo();
        if (info.usbVendorId !== 0x3654 || info.usbProductId !== 0x5155) return deny('Wrong USB device');
        state.portInfo = {vid: info.usbVendorId, pid: info.usbProductId};
      };
      check();
      const nativeOpen = port.open.bind(port), nativeClose = port.close.bind(port);
      Object.defineProperty(port, 'open', {value: async options => {
        if (state.stopped || state.opens !== 0 || options?.baudRate !== 115200) return deny('One serial open at115200 only');
        check(); state.opens++; event('serial_open_intent');
        await nativeOpen(options); event('serial_open_complete');
        // Observe the native stream bytes without constructing replies or changing their contents.
        const stream = port.readable, getReader = stream.getReader.bind(stream);
        Object.defineProperty(stream, 'getReader', {value: (...args) => {
          const reader = getReader(...args), read = reader.read.bind(reader);
          Object.defineProperty(reader, 'read', {value: async () => {
            const result = await read();
            if (result.value) {
              state.rxBytes += result.value.byteLength;
              if (state.rxBytes > 1024 * 1024) return deny('RX evidence budget exceeded');
              state.rx.push({time: performance.now(), hex: hex(result.value)});
            }
            return result;
          }});
          return reader;
        }});
      }});
      Object.defineProperty(port, 'close', {value: async () => {
        event('serial_close_intent');
        try { await nativeClose(); state.closes++; event('serial_close_complete'); }
        catch (error) { state.closeError = String(error); poison('Native serial close failed'); throw error; }
      }});
      return port;
    },
  }});
  localStorage.setItem('hyperrig.updateOff', '1');
  const fresh = values => {
    for (const name of ['GAIN', 'LVL', 'FXS', 'PLIST', 'SNAPS']) {
      if (state.observations[name]?.epoch !== state.epoch) return deny('Fresh complete readback required: ' + name);
    }
    if (!equal(state.observations.GAIN.gain, values) || !equal(state.observations.LVL.gain, values))
      return deny('GAIN and LVL disagree with the bounded trial');
  };
  const guard = {
    state, readonly,
    allowRequest() {
      if (!state.live || !state.appInstalled || state.stopped) return deny('Qualified app guard is not ready');
      state.requestEnabled = true;
    },
    installApp(transport, pedal, profile) {
      if (state.appInstalled || profile?.target !== 'tank-mini' || profile.image_sha256 !== config.image_sha256 ||
          profile.hardware_verified !== true || profile.capabilities?.read !== true || profile.capabilities?.write !== false ||
          !profile.family_capabilities?.['usb-cdc']?.includes('GAIN')) return deny('Qualified USB GAIN profile required');
      const originalWrite = transport.write.bind(transport);
      transport.write = async text => {
        if (!state.live || state.stopped || typeof text !== 'string' || !/^[\x20-\x7e]{1,190}\n$/.test(text))
          return deny('Malformed, stopped or offline serial write');
        const line = text.slice(0, -1);
        if (line !== line.trim()) return deny('Noncanonical serial line');
        if (line !== 'PING' && !state.pongMatched) return deny('Exact PONG required before commands');
        if (state.wire.length >= 1000 || (line === 'PING' && state.wire.filter(x => x.line === line).length >= 5))
          return deny('Command budget exceeded');
        let origin = 'query';
        if (!readonly(line)) {
          const first = state.mutations === 0, values = first ? down : before;
          if (state.mutations >= 2 || state.phase !== (first ? 'down_key' : 'up_key') || line !== request(values) ||
              !equal(current(), values) || Number(knob()?.getAttribute('aria-valuenow')) !== values[1])
            return deny('Only the witnessed UI down/restore GAIN commands are permitted');
          const policy = HyperRigMini.commandPolicy(line, 'usb-cdc');
          if (!policy.allowed || policy.capability !== 'family') return deny('Actual editor policy denied USB GAIN');
          origin = first ? 'Output ArrowDown' : 'Output ArrowUp';
          state.mutations++; state.phase = first ? 'down_in_flight' : 'up_in_flight';
        }
        const item = {line, hex: hex(new TextEncoder().encode(text)), origin, started: performance.now(), completed: false};
        state.wire.push(item);
        try { await originalWrite(text); item.completed = true; item.finished = performance.now(); }
        catch (error) { poison('Serial write failed; no retry'); throw error; }
      };
      const originalLine = pedal.onLine.bind(pedal);
      pedal.onLine = line => {
        if (state.replies.length >= 6000 || String(line).length > 2048) return deny('Reply evidence budget exceeded');
        state.replies.push({line: String(line), time: performance.now()});
        if (String(line).startsWith('PONG')) {
          if (line !== config.pong) poison('PONG differs from reviewed physical evidence');
          else { state.pongMatched = true; event('expected_pong_received'); }
        }
        return originalLine(line);
      };
      const originalCommand = pedal.cmd.bind(pedal);
      pedal.cmd = async (line, ...args) => {
        // The unmodified editor probes these optional features. Its existing
        // MINI policy rejects them locally, before queue/write. Record that
        // rejection separately; it is neither a device error nor an ACK.
        if ((line === 'BLEKEY' || /^LVLSUB \d+(?: 2)?$/.test(line)) &&
            !HyperRigMini.commandPolicy(line, 'usb-cdc').allowed) {
          const lines = await originalCommand(line, ...args);
          if (!Array.isArray(lines) || !lines.length || lines.some(x => !/^ERR MINI_APP /.test(x)))
            return deny('Unexpected optional-feature policy response');
          event('local_editor_policy_rejection', {line, lines});
          return lines;
        }
        const epoch = state.epoch;
        let lines;
        try { lines = await originalCommand(line, ...args); }
        catch (error) { poison('Command failed; no command retry'); throw error; }
        state.commands.push({line, lines, epoch, time: performance.now()});
        if (!Array.isArray(lines) || !lines.length || lines.some(x => typeof x !== 'string' || /^ERR\b/.test(x)))
          return deny('Missing/error command response; no retry');
        if (/^GAIN /.test(line)) {
          const first = state.phase === 'down_in_flight', values = first ? down : before;
          if (!['down_in_flight', 'up_in_flight'].includes(state.phase) || line !== request(values) || !equal(gainReply(lines), values))
            return deny('GAIN acknowledgement differs from the UI command');
          state.epoch++; state.phase = first ? 'down_ack' : 'up_ack';
          event('gain_ack', {line, lines});
        } else if (['GAIN', 'LVL', 'FXS', 'PLIST', 'SNAPS'].includes(line)) {
          let gain = null;
          if (line === 'GAIN' && !(gain = gainReply(lines))) return deny('Malformed GAIN query');
          if (line === 'LVL') {
            const match = lines.length === 1 && /^LVL .*\bg=(-?\d+)\/(-?\d+)(?: |$)/.exec(lines[0]);
            if (!match) return deny('Malformed LVL gain query');
            gain = [Number(match[1]), Number(match[2])];
          }
          if (line === 'FXS' && !/^FXS (?:peak|pico)=\d+ ticks skipped=\d+$/.test(lines.at(-1))) return deny('Incomplete FXS');
          if (line === 'PLIST' && (typeof parsePlist !== 'function' || !parsePlist(lines).ok)) return deny('Incoherent PLIST; no retry');
          if (line === 'SNAPS' && (lines.length !== 1 || !/^SNAPS [01]{4} (?:current|actual)=-?[0-3]$/.test(lines[0])))
            return deny('Malformed SNAPS');
          // A response queued before the ACK cannot qualify the new epoch.
          state.observations[line] = {epoch, lines, gain};
        }
        return lines;
      };
      document.addEventListener('keydown', e => {
        if (!['down_armed', 'up_armed'].includes(state.phase)) return;
        const first = state.phase === 'down_armed', key = first ? 'ArrowDown' : 'ArrowUp';
        try {
          if (state.stopped || !e.isTrusted || e.repeat || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey ||
              e.key !== key || e.code !== key || e.target !== checkUI(first ? before : down))
            return deny('Only one trusted Output ArrowDown/ArrowUp event is permitted');
          state.ui.push({key, code: e.code, trusted: e.isTrusted, target: '#gOut .knob[role="slider"]',
            gainBefore: [...current()], ariaBefore: knob().getAttribute('aria-valuenow'), time: performance.now()});
          state.phase = first ? 'down_key' : 'up_key';
        } catch (error) { e.preventDefault(); e.stopImmediatePropagation(); throw error; }
      }, true);
      state.appInstalled = true; event('app_guard_installed');
    },
    arm(direction) {
      const first = direction === 'down';
      if (!['down', 'up'].includes(direction) || state.stopped || !state.pongMatched || state.opens !== 1 ||
          state.phase !== (first ? 'initial' : 'down_ack') || state.mutations !== (first ? 0 : 1))
        return deny('Out-of-order UI arm');
      fresh(first ? before : down); checkUI(first ? before : down);
      const policy = HyperRigMini.commandPolicy(request(first ? down : before), 'usb-cdc');
      if (!policy.allowed || policy.capability !== 'family') return deny('USB family GAIN is unavailable');
      state.phase = first ? 'down_armed' : 'up_armed'; event('ui_armed', {direction});
    },
    finish() {
      if (state.stopped || state.phase !== 'up_ack' || state.mutations !== 2 || state.ui.length !== 2)
        return deny('The two-key trial did not complete');
      fresh(before); checkUI(before); state.phase = 'complete'; event('trial_complete');
    },
    stop() { state.stopped = true; state.requestEnabled = false; event('guard_stopped'); },
  };
  Object.defineProperty(globalThis, '__miniGainGuard', {value: guard});
  return guard;
}
