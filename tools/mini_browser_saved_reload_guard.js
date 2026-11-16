/* Separate saved-preset continuation: exactly one original Output ArrowDown
 * then one original preset-row Enter. No save, capture write, deletion or retry.
 * Native byte/queue/UI recording derives from frozen first-preset guard v2. */
function installMiniBrowserSavedReloadGuard(config) {
  'use strict';
  const nativeSerial = navigator.serial;
  const state = {live: config.live === true, appInstalled: false, requestEnabled: false,
    requests: 0, opens: 0, closes: 0, closeError: null, stopped: false, fatal: null,
    pongMatched: false, phase: 'initial', epoch: 0, seq: 0, mutations: 0,
    events: [], ui: [], wire: [], rx: [],
    replies: [], commands: [], observations: {}, rxBytes: 0, started: performance.now()};
  let trial = null, activePolicy = null;
  const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  const clone = x => JSON.parse(JSON.stringify(x));
  const event = (kind, data = {}) => { const e = {seq: ++state.seq, time: performance.now(),
    utc: new Date().toISOString(), kind, ...data}; state.events.push(e); return e; };
  const poison = message => { state.fatal = String(message); state.stopped = true; };
  const deny = message => { poison(message); throw new DOMException(message, 'NotAllowedError'); };
  const hex = bytes => Array.from(bytes, x => x.toString(16).padStart(2, '0')).join('');
  const queries = new Set(('PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST ' +
    'LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE LIFE CRASH CLKSTATE GAIN BPM PCOLOR').split(' '));
  const readonly = line => queries.has(line) || line === 'AMPEQ info' || /^EVT [0-9]{1,10}$/.test(line);
  const snapshotNames = ['GAIN', 'LVL', 'FXS', 'PLIST', 'SNAPS', 'CLIST', 'ILIST', 'MODEL', 'CLKSTATE',
    'AMPEQ', 'BPM', 'PCOLOR', 'STW', 'SNAPNAME'];
  const knob = () => document.querySelector('#gOut .knob[role="slider"]');
  const visible = el => !!el && el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().height > 0;
  const row = () => trial && document.querySelector('#pList [data-preset="' + trial.slot + '"]');
  const gain = values => 'GAIN ' + values.join(' ');
  const fresh = values => {
    for (const name of snapshotNames) if (state.observations[name]?.epoch !== state.epoch)
      return deny('Fresh post-ACK snapshot required: ' + name);
    if (values && (!equal(state.observations.GAIN.gain, values) || !equal(state.observations.LVL.gain, values)))
      return deny('Actual GAIN/LVL differs from the planned step');
    if (!/^CLKSTATE .*\bsafe=0(?: |$)/.test(state.observations.CLKSTATE.lines[0]) ||
        !/^LVL .*\bm=2(?: |$)/.test(state.observations.LVL.lines[0]))
      return deny('Fresh normal running firmware state required');
  };
  const checkKnob = values => {
    const k = knob();
    if (!visible(k) || document.activeElement !== k || k.dataset.k !== 'Output' ||
        k.getAttribute('aria-valuemin') !== '-30' || k.getAttribute('aria-valuemax') !== '12' ||
        Number(k.getAttribute('aria-valuenow')) !== values[1] || !equal(S.gain, values))
      return deny('Actual focused Output knob and S.gain differ');
    return k;
  };
  const expected = () => {
    if (!trial) return null;
    return [gain(trial.down), trial.load_request][state.mutations];
  };
  const permit = line => {
    if (state.stopped || !state.pongMatched) return false;
    if (!trial || line !== expected()) return false;
    return ['marker_key', 'reload_key'][state.mutations] === state.phase;
  };
  const noEvents = {addEventListener() {}, removeEventListener() {}};
  const blocked = name => async () => deny('Trial blocks ' + name);
  Object.defineProperty(navigator, 'usb', {configurable: true, value: {...noEvents,
    getDevices: async () => [], requestDevice: blocked('USB')}});
  Object.defineProperty(navigator, 'bluetooth', {configurable: true, value: {...noEvents,
    getAvailability: async () => false, getDevices: async () => [], requestDevice: blocked('Bluetooth')}});
  Object.defineProperty(navigator, 'requestMIDIAccess', {configurable: true, value: blocked('MIDI')});
  Object.defineProperty(navigator, 'serial', {configurable: true, value: {...noEvents,
    getPorts: async () => [],
    requestPort: async () => {
      if (!state.live || !state.requestEnabled || state.stopped || state.requests !== 0 || !nativeSerial)
        return deny('Exactly one explicit chooser is permitted');
      state.requests++; event('serial_request_intent');
      const port = await nativeSerial.requestPort({filters: [{usbVendorId: 0x3654, usbProductId: 0x5155}]});
      const check = () => {
        const info = port.getInfo();
        if (info.usbVendorId !== 0x3654 || info.usbProductId !== 0x5155) return deny('Wrong USB identity');
        state.portInfo = {vid: info.usbVendorId, pid: info.usbProductId};
      };
      check();
      const open = port.open.bind(port), close = port.close.bind(port);
      Object.defineProperty(port, 'open', {value: async options => {
        if (state.stopped || state.opens !== 0 || options?.baudRate !== 115200) return deny('One115200 open required');
        check(); state.opens++; event('serial_open_intent'); await open(options); event('serial_open_complete');
        const stream = port.readable, getReader = stream.getReader.bind(stream);
        Object.defineProperty(stream, 'getReader', {value: (...args) => {
          const reader = getReader(...args), read = reader.read.bind(reader);
          Object.defineProperty(reader, 'read', {value: async () => {
            const value = await read();
            if (value.value) {
              state.rxBytes += value.value.byteLength;
              if (state.rxBytes > 2 * 1024 * 1024) return deny('Raw RX bound exceeded');
              state.rx.push({seq: ++state.seq, time: performance.now(), hex: hex(value.value)});
            }
            return value;
          }}); return reader;
        }});
      }});
      Object.defineProperty(port, 'close', {value: async () => {
        event('serial_close_intent');
        try { await close(); state.closes++; event('serial_close_complete'); }
        catch (error) { state.closeError = String(error); poison('Native close failed'); throw error; }
      }}); return port;
    },
  }});
  localStorage.setItem('hyperrig.updateOff', '1');
  const guard = {
    state, readonly,
    allowRequest() {
      if (!state.live || !state.appInstalled || state.stopped) return deny('Guard not ready');
      state.requestEnabled = true;
    },
    installApp(transport, pedal, profile) {
      if (state.appInstalled || profile?.target !== 'tank-mini' || profile.image_sha256 !== config.image_sha256 ||
          profile.capabilities?.read !== true || profile.capabilities?.write !== false || profile.hardware_verified !== false ||
          Object.keys(profile.family_capabilities || {}).length || Object.keys(profile.command_capabilities || {}).length ||
          typeof DEMO === 'undefined' || DEMO) return deny('Unchanged readonly v3 app required');
      const originalPolicy = HyperRigMini;
      activePolicy = Object.freeze({...originalPolicy,
        commandPolicy(line, tr, ...args) {
          if (tr === 'usb-cdc' && permit(line)) return {allowed: true, capability: 'experimental-exact-trial'};
          return originalPolicy.commandPolicy(line, tr, ...args);
        },
        preflight(lines, tr) { return originalPolicy.preflight(lines, tr); }});
      globalThis.HyperRigMini = activePolicy;
      const originalWrite = transport.write.bind(transport);
      transport.write = async text => {
        if (!state.live || state.stopped || performance.now() - state.started > 15 * 60 * 1000 ||
            typeof text !== 'string' || !/^[\x20-\x7e]{1,190}\n$/.test(text)) return deny('Malformed/stopped write');
        const line = text.slice(0, -1);
        if (line !== line.trim() || (line !== 'PING' && !state.pongMatched)) return deny('Canonical exact identity required');
        if (state.wire.length >= 2000 || (line === 'PING' && state.wire.filter(x => x.line === line).length >= 5))
          return deny('Finite command budget exceeded');
        const command = state.commands.find(x => !x.local && x.wire_id == null && !x.completed && x.line === line);
        if (!command) return deny('Write must traverse the original editor command queue');
        let origin = 'query';
        if (!readonly(line)) {
          if (!permit(line)) return deny('Unplanned, duplicate or out-of-order command');
          const n = state.mutations;
          if (n === 0 && (!equal(S.gain, trial.down) ||
              Number(knob()?.getAttribute('aria-valuenow')) !== trial.down[1])) return deny('UI gain differs at wire');
          if (n === 1 && (curPreset !== trial.slot || S.curPre !== trial.slot)) return deny('Saved preset selection changed');
          origin = ['Output persistence marker ArrowDown', 'Original preset-row Enter'][n];
          state.mutations++; state.phase = 'ui_in_flight';
        }
        const item = {id: state.wire.length, command_id: command.id, line, hex: hex(new TextEncoder().encode(text)),
          origin, seq: ++state.seq, started: performance.now(), utc: new Date().toISOString(), completed: false};
        command.wire_id = item.id; state.wire.push(item);
        try { await originalWrite(text); item.completed = true; item.finished = performance.now(); }
        catch (error) { poison('Serial write failed; no retry'); throw error; }
      };
      const originalLine = pedal.onLine.bind(pedal);
      pedal.onLine = line => {
        if (state.replies.length >= 10000 || String(line).length > 2048) return deny('Reply bound exceeded');
        state.replies.push({seq: ++state.seq, time: performance.now(), line: String(line)});
        if (String(line).startsWith('PONG')) {
          if (line !== config.pong || /\bsafe\b/.test(line)) poison('Exact non-safe PONG required');
          else state.pongMatched = true;
        }
        return originalLine(line);
      };
      const originalCommand = pedal.cmd.bind(pedal);
      pedal.cmd = async (line, ...args) => {
        if ((line === 'BLE key' || line === 'BLEKEY' || /^LVLSUB \d+(?: 2)?$/.test(line)) &&
            !activePolicy.commandPolicy(line, 'usb-cdc').allowed) {
          const lines = await originalCommand(line, ...args);
          if (!Array.isArray(lines) || !lines.length || lines.some(x => !/^ERR MINI_APP /.test(x)))
            return deny('Unexpected local optional-feature reply');
          if (line === 'BLE key' &&
              (!equal(lines, ['ERR MINI_APP firmware mutations are not validated for this MINI build']) ||
               state.wire.some(item => item.line === line)))
            return deny('BLE key must remain an exact local policy rejection with no wire command');
          event('local_editor_policy_rejection', {line, lines,
            ...(line === 'BLE key' ? {local_only: true, wire_command_observed: false} : {})}); return lines;
        }
        const item = {id: state.commands.length, line, epoch: state.epoch, wire_id: null, completed: false};
        state.commands.push(item);
        let lines;
        try { lines = await originalCommand(line, ...args); }
        catch (error) { poison('Command failed; no retry'); throw error; }
        item.lines = lines; item.completed = true; item.seq = ++state.seq;
        if (!Array.isArray(lines) || !lines.length || lines.some(x => typeof x !== 'string' || /^ERR\b/.test(x)) || item.wire_id == null)
          return deny('No real successful command response; no retry');
        if (!readonly(line)) {
          const n = state.mutations - 1;
          let okay = false;
          if (n === 0) okay = equal(lines, ['GAIN in=' + trial.gain[0] + ' out=' + trial.down[1] + ' dB']);
          if (n === 1) okay = lines.length === 1 && new RegExp("^PLOAD ok " + trial.slot + " '" +
            trial.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "' missing=0 capture=" + trial.capture_slot +
            ' ir=' + trial.ir_slot + ' ms=\\d+$').test(lines[0]);
          if (!okay || state.phase !== 'ui_in_flight') return deny('Exact actual mutation ACK differs');
          state.epoch++; state.phase = ['marker_ack', 'reload_ack'][n];
          event('mutation_ack', {line, lines, epoch: state.epoch});
        } else if (snapshotNames.includes(line) && item.epoch === state.epoch) {
          let values = null;
          if (line === 'GAIN') {
            const m = lines.length === 1 && /^GAIN in=(-?\d+) out=(-?\d+) dB$/.exec(lines[0]);
            if (!m) return deny('Malformed GAIN response'); values = [+m[1], +m[2]];
          }
          if (line === 'LVL') {
            const m = lines.length === 1 && /\bg=(-?\d+)\/(-?\d+)(?: |$)/.exec(lines[0]);
            if (!m) return deny('Malformed LVL gain'); values = [+m[1], +m[2]];
          }
          if (line === 'PLIST' && !parsePlist(lines).ok) return deny('Incomplete PLIST; no retry');
          if (line === 'FXS' && !/^FXS (?:peak|pico)=\d+ ticks skipped=\d+$/.test(lines.at(-1))) return deny('Incomplete FXS');
          state.observations[line] = {epoch: item.epoch, lines: clone(lines), gain: values};
        }
        return lines;
      };
      document.addEventListener('keydown', e => {
        if (!['marker_armed', 'reload_armed'].includes(state.phase)) return;
        try {
          const reload = state.phase === 'reload_armed';
          const key = reload ? 'Enter' : 'ArrowDown';
          const target = reload ? row()?.querySelector('.n') : checkKnob(trial.gain);
          if (!e.isTrusted || e.repeat || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey ||
              e.key !== key || e.code !== key || e.target !== target || !visible(target) || document.activeElement !== target)
            return deny('Exact trusted original-control key required');
          state.ui.push({kind: 'keydown', key, trusted: e.isTrusted, target: reload ? 'preset-row' : 'Output', seq: ++state.seq});
          state.phase = state.phase.replace('_armed', '_key');
        } catch (error) { e.preventDefault(); e.stopImmediatePropagation(); throw error; }
      }, true);
      state.appInstalled = true; event('experimental_guard_installed');
    },
    configureTrial(value, responses) {
      if (state.phase !== 'initial' || trial || !state.pongMatched || !value || !equal(value, config.plan) ||
          !Array.isArray(value.gain) || value.gain.length !== 2 || !value.gain.every(x => Number.isInteger(x) && x >= -30 && x <= 12) ||
          value.gain[1] <= -30 || !equal(value.down, [value.gain[0], value.gain[1] - 1]) ||
          !Number.isInteger(value.slot) || value.slot < 0 || value.slot > 31 ||
          !Number.isInteger(value.capture_slot) || value.capture_slot < 0 || value.capture_slot > 14 ||
          !/^[A-Za-z0-9 _.-]{1,23}$/.test(value.name || '') || value.load_request !== 'PLOAD ' + value.slot)
        return deny('One exact already-saved preset plan required');
      fresh(value.gain);
      for (const key of snapshotNames) if (!equal(responses[key], state.observations[key].lines)) return deny('Unobserved baseline supplied');
      const p = parsePlist(responses.PLIST), lib = pioLib(responses.CLIST, true);
      const saved = p.list.filter(item => item[0] === value.slot);
      if (!p.ok || p.cur !== value.slot || saved.length !== 1 || curPreset !== value.slot || S.curPre !== value.slot ||
          !equal(responses.SNAPS, ['SNAPS 1000 current=0']) || lib.cur !== value.capture_slot || S.capSlot !== value.capture_slot ||
          !lib.list.some(x => x.slot === value.capture_slot && x.bytes === 4892 && x.name === 'A2'))
        return deny('Saved preset/capture baseline differs');
      trial = clone(value); state.phase = 'trial_ready'; event('trial_plan', {plan: trial});
    },
    arm(action) {
      const phases = {marker: 'trial_ready', reload: 'marker_ack'};
      if (!trial || state.stopped || phases[action] !== state.phase) return deny('Out-of-order UI arm');
      fresh(action === 'reload' ? trial.down : trial.gain);
      if (action === 'marker') checkKnob(trial.gain);
      if (action === 'reload' && (!visible(row()?.querySelector('.n')) || document.activeElement !== row().querySelector('.n') ||
          row().querySelector('.n.vacio') || curPreset !== trial.slot)) return deny('Actual newly saved preset row required');
      state.phase = action + '_armed'; event('ui_armed', {action});
    },
    finish() {
      if (state.stopped || state.phase !== 'reload_ack' || state.mutations !== 2 || state.ui.length !== 2)
        return deny('Two-command original-UI continuation incomplete');
      fresh(trial.gain); state.phase = 'complete'; event('trial_complete');
    },
    stop() { state.stopped = true; state.requestEnabled = false; event('guard_stopped'); },
  };
  Object.defineProperty(globalThis, '__miniSavedReloadGuard', {value: guard});
  return guard;
}
