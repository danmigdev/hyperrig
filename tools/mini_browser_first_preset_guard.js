/* One experimental original-editor trial. The frozen build profile is unchanged.
 * CSAVE/CREAD are an explicit diagnostic preamble; GAIN, PSAVE, SNAPSAVE and
 * PLOAD must originate in the original controls witnessed below. No retries. */
function installMiniBrowserFirstPresetGuard(config) {
  'use strict';
  const nativeSerial = navigator.serial;
  const state = {live: config.live === true, appInstalled: false, requestEnabled: false,
    requests: 0, opens: 0, closes: 0, closeError: null, stopped: false, fatal: null,
    pongMatched: false, phase: 'initial', epoch: 0, seq: 0, mutations: 0,
    captureMutations: 0, captureVerified: false, events: [], ui: [], wire: [], rx: [],
    replies: [], commands: [], observations: {}, rxBytes: 0, started: performance.now()};
  let capture = null, trial = null, captureNext = 0, activePolicy = null;
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
    return [gain(trial.down), gain(trial.gain), trial.save_request, 'SNAPSAVE 0', gain(trial.down), trial.load_request][state.mutations];
  };
  const permit = line => {
    if (state.stopped || !state.pongMatched) return false;
    if (capture && state.phase === 'capture' && capture.requests[captureNext] === line) return true;
    if (!trial || line !== expected()) return false;
    return ['down1_key', 'up_key', 'save_click', 'psave_ack', 'marker_key', 'reload_key'][state.mutations] === state.phase;
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
        preflight(lines, tr) {
          if (tr === 'usb-cdc' && trial && state.phase === 'save_click' &&
              equal(lines, [trial.save_request, 'SNAPSAVE 0'])) return {allowed: true, experimental_trial: true};
          return originalPolicy.preflight(lines, tr);
        }});
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
          if (state.phase === 'capture') {
            origin = line.startsWith('CSAVE ') ? 'diagnostic capture persistence' : 'diagnostic capture byte read';
            if (line.startsWith('CSAVE ')) state.captureMutations++;
            captureNext++; state.phase = 'capture_in_flight';
          } else {
            const n = state.mutations;
            if ([0, 1, 4].includes(n) && (!equal(S.gain, n === 1 ? trial.gain : trial.down) ||
                Number(knob()?.getAttribute('aria-valuenow')) !== S.gain[1])) return deny('UI gain differs at wire');
            if (n === 2 && (curPreset !== -1 || !parsePlist(state.observations.PLIST.lines).ok ||
                parsePlist(state.observations.PLIST.lines).list.some(p => p[0] === trial.slot))) return deny('Destination no longer free');
            if (n === 3 && (S.curPre !== trial.slot || state.observations.SNAPS?.epoch !== state.epoch ||
                !/^SNAPS 0000 (?:current|actual)=-1$/.test(state.observations.SNAPS.lines[0])))
              return deny('Automatic scene A no longer belongs to the new preset');
            origin = ['Output ArrowDown', 'Output ArrowUp', 'Original empty-row Save',
              'Original sceneAOnSave', 'Output persistence marker ArrowDown', 'Original preset-row Enter'][n];
            state.mutations++; state.phase = 'ui_in_flight';
          }
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
        if ((line === 'BLEKEY' || /^LVLSUB \d+(?: 2)?$/.test(line)) &&
            !activePolicy.commandPolicy(line, 'usb-cdc').allowed) {
          const lines = await originalCommand(line, ...args);
          if (!Array.isArray(lines) || !lines.length || lines.some(x => !/^ERR MINI_APP /.test(x)))
            return deny('Unexpected local optional-feature reply');
          event('local_editor_policy_rejection', {line, lines}); return lines;
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
          if (state.phase === 'capture_in_flight') {
            if (line.startsWith('CSAVE ') && (lines.length !== 1 || !lines[0].startsWith('CSAVE ok ' + capture.slot + ' ')))
              return deny('CSAVE ACK missing or wrong slot');
            state.phase = 'capture';
          } else {
            const n = state.mutations - 1;
            let okay = false;
            if ([0, 1, 4].includes(n)) okay = equal(lines, ['GAIN in=' + trial.gain[0] + ' out=' + (n === 1 ? trial.gain[1] : trial.down[1]) + ' dB']);
            if (n === 2) okay = equal(lines, ["PSAVE ok " + trial.slot + " '" + trial.name + "' " + trial.blocks +
              ' blocks capture=' + trial.capture_slot + ' ir=' + trial.ir_slot]);
            if (n === 3) okay = equal(lines, ['SNAPSAVE ok 0 preset=' + trial.slot]);
            if (n === 5) okay = lines.length === 1 && new RegExp("^PLOAD ok " + trial.slot + " '" +
              trial.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + "' missing=0 capture=" + trial.capture_slot +
              ' ir=' + trial.ir_slot + ' ms=\\d+$').test(lines[0]);
            if (!okay || state.phase !== 'ui_in_flight') return deny('Exact actual mutation ACK differs');
            state.epoch++; state.phase = ['down1_ack', 'up_ack', 'psave_ack', 'scene_ack', 'marker_ack', 'reload_ack'][n];
            event('mutation_ack', {line, lines, epoch: state.epoch});
          }
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
        if (!['down1_armed', 'up_armed', 'marker_armed', 'reload_armed'].includes(state.phase)) return;
        try {
          const reload = state.phase === 'reload_armed', up = state.phase === 'up_armed';
          const key = reload ? 'Enter' : up ? 'ArrowUp' : 'ArrowDown';
          const target = reload ? row()?.querySelector('.n') : checkKnob(up ? trial.down : trial.gain);
          if (!e.isTrusted || e.repeat || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey ||
              e.key !== key || e.code !== key || e.target !== target || !visible(target) || document.activeElement !== target)
            return deny('Exact trusted original-control key required');
          state.ui.push({kind: 'keydown', key, trusted: e.isTrusted, target: reload ? 'preset-row' : 'Output', seq: ++state.seq});
          state.phase = state.phase.replace('_armed', '_key');
        } catch (error) { e.preventDefault(); e.stopImmediatePropagation(); throw error; }
      }, true);
      document.addEventListener('click', e => {
        if (state.phase !== 'save_armed') return;
        try {
          const button = row()?.querySelector('[data-a="s"]');
          if (!e.isTrusted || !visible(button) || !button.contains(e.target) || !row().querySelector('.n.vacio'))
            return deny('Exact trusted empty-row Save required');
          state.ui.push({kind: 'click', trusted: true, target: 'empty-row Save', seq: ++state.seq}); state.phase = 'save_click';
        } catch (error) { e.preventDefault(); e.stopImmediatePropagation(); throw error; }
      }, true);
      state.appInstalled = true; event('experimental_guard_installed');
    },
    configureCapture(value) {
      if (state.phase !== 'initial' || capture || !state.pongMatched || !Number.isInteger(value?.slot) ||
          value.slot < 0 || value.slot > 14 || !Array.isArray(value.requests) || value.requests.length < 2)
        return deny('One bounded capture plan required');
      fresh();
      const reads = ['CREAD ' + value.slot, ...Array.from({length: 51}, (_, k) => 'CREAD ' + value.slot + ' ' + k * 96)];
      const withSave = value.requests[0] === 'CSAVE ' + value.slot + ' A2';
      if (!equal(value.requests, withSave ? ['CSAVE ' + value.slot + ' A2', ...reads] : reads))
        return deny('Only the exact A2 capture save and 4892-byte read plan is permitted');
      const lib = pioLib(state.observations.CLIST.lines, true);
      if (!lib.full || (withSave ? lib.cur !== -1 || lib.list.some(x => x.slot === value.slot) : lib.cur !== value.slot))
        return deny('Capture destination/current slot changed');
      capture = clone(value); state.phase = 'capture'; event('capture_plan', {plan: capture});
    },
    captureDone() {
      if (state.phase !== 'capture' || captureNext !== capture.requests.length) return deny('Capture byte verification is incomplete');
      // The Python caller invokes this only after the pure verifier compared all
      // real header/chunk bytes to the pinned A2. It is not a firmware ACK.
      state.captureVerified = true; state.phase = 'capture_verified'; state.epoch++; event('capture_verified_by_host');
    },
    configureTrial(value, responses) {
      if (state.phase !== 'capture_verified' || trial || !state.captureVerified || !value ||
          !Array.isArray(value.gain) || value.gain.length !== 2 || !value.gain.every(x => Number.isInteger(x) && x >= -30 && x <= 12) ||
          value.gain[1] <= -30 || !equal(value.down, [value.gain[0], value.gain[1] - 1]) ||
          !Number.isInteger(value.slot) || value.slot < 0 || value.slot > 31 || value.capture_slot !== capture.slot ||
          !/^[A-Za-z0-9 _.-]{1,23}$/.test(value.name || '') || value.save_request !== 'PSAVE ' + value.slot + ' ' + value.name ||
          value.load_request !== 'PLOAD ' + value.slot) return deny('One exact UI plan required');
      fresh(value.gain);
      for (const key of snapshotNames) if (!equal(responses[key], state.observations[key].lines)) return deny('Unobserved baseline supplied');
      const p = parsePlist(responses.PLIST), lib = pioLib(responses.CLIST, true);
      const first = Array.from({length: 32}, (_, n) => n).find(n => !p.list.some(x => x[0] === n));
      if (!p.ok || p.cur !== -1 || first !== value.slot || curPreset !== -1 || S.curPre !== -1 ||
          !equal(responses.SNAPS, ['SNAPS 0000 current=-1']) || lib.cur !== capture.slot || S.capSlot !== capture.slot ||
          !lib.list.some(x => x.slot === capture.slot && x.bytes === 4892 && x.name === 'A2'))
        return deny('First-preset/capture baseline differs');
      const name = (S.pendName || presetName() || `Preset ${Math.floor(value.slot / 4) + 1}${SLOT(value.slot)}`).slice(0, 23);
      if (name !== value.name) return deny('Planned name is not generated by original UI');
      trial = clone(value); state.phase = 'trial_ready'; event('trial_plan', {plan: trial});
    },
    arm(action) {
      const phases = {down1: 'trial_ready', up: 'down1_ack', save: 'up_ack', marker: 'scene_ack', reload: 'marker_ack'};
      if (!trial || state.stopped || phases[action] !== state.phase) return deny('Out-of-order UI arm');
      fresh(action === 'up' || action === 'reload' ? trial.down : trial.gain);
      if (['down1', 'up', 'marker'].includes(action)) checkKnob(action === 'up' ? trial.down : trial.gain);
      if (action === 'save' && (!visible(row()?.querySelector('[data-a="s"]')) || !row().querySelector('.n.vacio')))
        return deny('Actual empty destination row required');
      if (action === 'reload' && (!visible(row()?.querySelector('.n')) || document.activeElement !== row().querySelector('.n') ||
          row().querySelector('.n.vacio') || curPreset !== trial.slot)) return deny('Actual newly saved preset row required');
      state.phase = action + '_armed'; event('ui_armed', {action});
    },
    finish() {
      if (state.stopped || state.phase !== 'reload_ack' || state.mutations !== 6 || state.ui.length !== 5)
        return deny('Full original-UI sequence incomplete');
      fresh(trial.gain); state.phase = 'complete'; event('trial_complete');
    },
    stop() { state.stopped = true; state.requestEnabled = false; event('guard_stopped'); },
  };
  Object.defineProperty(globalThis, '__miniFirstPresetGuard', {value: guard});
  return guard;
}
