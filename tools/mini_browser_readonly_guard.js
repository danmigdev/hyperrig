/* Separate browser-test instrumentation. It does not modify the app files. */
function installMiniBrowserReadonlyGuard(config) {
  'use strict';
  const nativeSerial = navigator.serial;
  const fail = message => new DOMException(message, 'NotAllowedError');
  const state = {
    live: config.live === true, requestEnabled: false, requests: 0, opens: 0,
    portInfo: null, pongMatched: false, stopped: false, fatal: null,
    hardwareStubCalls: [], wire: [], replies: [], commands: [], events: [], appInstalled: false,
  };
  const event = (kind, data = {}) => state.events.push({kind, time: performance.now(), ...data});
  const deny = message => { state.fatal = message; state.stopped = true; throw fail(message); };
  const plainQueries = new Set(('PING STAT MEM MODEL FXT FXS FXMIX FXXO AMPEQ PLIST SNAPS SNAPNAME CLIST ILIST ' +
    'LVL GEQ HPF SPILL GLIDE SPUR LIM PSTAT STW BLE LIFE CRASH CLKSTATE GAIN BPM PCOLOR').split(' '));
  const readonly = line => plainQueries.has(line) || line === 'AMPEQ info' || /^EVT [0-9]{1,10}$/.test(line);
  const blocked = name => async () => { state.hardwareStubCalls.push(name); throw fail('Browser test blocks ' + name); };
  const noEvents = {addEventListener() {}, removeEventListener() {}};
  Object.defineProperty(navigator, 'usb', {configurable: true, value: {...noEvents,
    getDevices: async () => [], requestDevice: blocked('usb.requestDevice')}});
  Object.defineProperty(navigator, 'bluetooth', {configurable: true, value: {...noEvents,
    getAvailability: async () => false, getDevices: async () => [], requestDevice: blocked('bluetooth.requestDevice')}});
  Object.defineProperty(navigator, 'requestMIDIAccess', {configurable: true, value: blocked('midi.requestMIDIAccess')});
  Object.defineProperty(navigator, 'serial', {configurable: true, value: {...noEvents,
    // A new profile plus this empty enumeration prevents permission-based auto reconnect.
    getPorts: async () => { event('serial_getPorts_stub'); return []; },
    requestPort: async () => {
      if (!state.live || !state.requestEnabled || state.stopped || state.requests !== 0)
        return deny('Serial chooser requires explicit live opt-in and is allowed once');
      if (!nativeSerial || typeof nativeSerial.requestPort !== 'function')
        return deny('Web Serial unavailable');
      state.requests++;
      event('serial_request_intent');
      const port = await nativeSerial.requestPort({filters: [{usbVendorId: 0x3654, usbProductId: 0x5155}]});
      const check = () => {
        const info = port.getInfo();
        if (info.usbVendorId !== 0x3654 || info.usbProductId !== 0x5155)
          return deny('Selected serial device is not MINI CDC3654:5155');
        state.portInfo = {vid: info.usbVendorId, pid: info.usbProductId};
      };
      check();
      const nativeOpen = port.open.bind(port);
      Object.defineProperty(port, 'open', {configurable: false, writable: false, value: async options => {
        if (state.stopped || state.opens !== 0 || options?.baudRate !== 115200)
          return deny('Only one explicit serial open at115200 is allowed');
        check(); state.opens++; event('serial_open_intent', state.portInfo);
        await nativeOpen(options); event('serial_open_complete');
      }});
      return port;
    },
  }});
  localStorage.setItem('hyperrig.updateOff', '1');
  const guard = {
    state,
    readonly,
    allowRequest() {
      if (!state.live || !state.appInstalled || state.stopped) return deny('Live app guard is not ready');
      state.requestEnabled = true;
    },
    installApp(transport, pedal, profile) {
      if (state.appInstalled || profile?.target !== 'tank-mini' ||
          profile.image_sha256 !== config.image_sha256 || profile.capabilities?.read !== true)
        return deny('App MINI firmware profile differs');
      const originalWrite = transport.write.bind(transport);
      transport.write = async text => {
        if (state.stopped || !state.live || typeof text !== 'string' ||
            !/^[\x20-\x7e]{1,190}\n$/.test(text)) return deny('Malformed or offline serial write');
        const line = text.slice(0, -1);
        if (line !== line.trim() || !readonly(line)) return deny('Non-query blocked before serial write: ' + line.split(' ')[0]);
        if (line !== 'PING' && !state.pongMatched) return deny('Only PING is permitted before exact PONG match');
        if (state.wire.length >= 1000 || (line === 'PING' && state.wire.filter(x => x.line === 'PING').length >= 5))
          return deny('Read-only command budget exceeded');
        const item = {line, started: performance.now(), completed: false}; state.wire.push(item);
        await originalWrite(text); item.completed = true; item.finished = performance.now();
      };
      const originalLine = pedal.onLine.bind(pedal);
      pedal.onLine = line => {
        if (state.replies.length < 6000) state.replies.push(String(line).slice(0, 2048));
        if (String(line).startsWith('PONG')) {
          if (line !== config.pong) {
            state.fatal = 'PONG differs from reviewed physical evidence'; state.stopped = true;
            return originalLine('ERR MINI_BROWSER identity mismatch');
          }
          state.pongMatched = true; event('expected_pong_received');
        }
        return originalLine(line);
      };
      const originalCommand = pedal.cmd.bind(pedal);
      pedal.cmd = async (line, ...args) => {
        const result = await originalCommand(line, ...args);
        if (state.commands.length < 2000) state.commands.push({
          line: readonly(String(line)) ? line : String(line).split(' ')[0],
          lines: readonly(String(line)) && Array.isArray(result) ? result.map(x => String(x).slice(0, 2048)) : [],
        });
        return result;
      };
      state.appInstalled = true; event('app_guard_installed');
    },
    stop() { state.requestEnabled = false; state.stopped = true; event('guard_stopped'); },
  };
  Object.defineProperty(globalThis, '__miniReadonlyGuard', {configurable: false, value: guard});
  return guard;
}
