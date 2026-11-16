# MINI editor in the local browser

The `build/hyperrig-mini-audio-v2/app/web/tankmini.html` build was opened
in the installed Chrome, version `157.0.8103.52`, with a separate profile
and a temporary server restricted to `127.0.0.1`. No packages or services
were installed. The personal profile was not opened.

[verify_mini_browser.py](../tools/verify_mini_browser.py) uses the already
available `websocket-client` module and the actual browser's CDP. The test
denies serial, USB, Bluetooth and MIDI through `Permissions-Policy`;
it also replaces their methods before the app scripts run. Hardware-access
requests are rejected, and enumeration would return empty lists.
Neither test invoked any of these methods. External connections are
blocked. The browser and server are stopped at the end; the isolated
profile and artifacts remain in the new test directory under `build/`.

```powershell
python -B -X utf8 tools/verify_mini_browser.py --output build/mini-browser-new-run
```

The output path must be new. The valid result is retained in
`build/mini-browser-readonly-03/report.json`, SHA256
`edb9c1a762fe06ddcdc7c3282aa925e530318d402998eb6ce23ea0be7593db48`.
The verified page has SHA256
`13d276d50136f9551cf657dae49fff8f0b4d83f0e75b9b831ddb85edcd92a3c4`
and is bound to firmware candidate
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.

Results checked through mouse/keyboard input sent to the browser:

- The disconnected page and demo complete bootstrap; MINI title and profile are correct.
- The initial tour can be dismissed; settings can be opened and closed.
- Complete demo chain, TS9 editor, and Drive knob changed from 55 to 56,
  with matching displayed and JavaScript model values.
- TS9 bypass and reactivation; selection of the Crunch scene.
- A library of four captures and a bank with four preset slots.
- Desktop `1440x1000` and phone `390x844` layouts without horizontal overflow.
- No unhandled JavaScript exception and no `console.error`.

The browser log contains a `404` for `ctl.json`, an optional endpoint of
the original launcher used to coordinate connection ownership. The static
test server does not implement it, and the app handles its absence.
It is not a request to the pedal. Screenshots of the page, effect editor
and library are retained. The tester's first development run only changed
the `#demo` fragment without reloading the document; the final tester
forces a new document through a different query. This tester error is not
attributed to the app.

These results concern the UI with demo data. They do not attest to audio,
serial communication, Bluetooth, saved presets or connected MINI hardware.
The verified build retains `read=true`, `write=false`, `panel=false`;
a future app with permissions for verified commands requires a new test.

## Subsequent connection through CDP

The experimental `DeviceAccess` domain is present in the
`/json/protocol` schema of the browser actually launched. The complete
schema is included in the report, without consulting documentation for
other versions. No chooser was enabled and no permission was granted.

Available sequence for a subsequently authorized runner:

1. Outside the browser, confirm CDC `3654:5155` and the
   `PONG tankm_fw ...` response, then close the port used for that check.
2. Open a new isolated profile and the correct app through localhost with
   a normal serial policy. The tester's server described above deliberately
   forbids connection and must not be reused for this purpose.
3. Connect CDP to the page target and send `DeviceAccess.enable`.
   Start listening for events before pressing the real Connect button
   with `Input.dispatchMouseEvent`.
4. Wait for `DeviceAccess.deviceRequestPrompted` with parameters
   `{id, devices: [{id, name}, ...]}`. The editor's `requestPort` filters
   USB vendor `0x3654`. The CDP event does not expose VID/PID: do not
   choose the first entry if its name is ambiguous or unexpected devices
   are present.
5. For a uniquely identified entry, the command is
   `DeviceAccess.selectPrompt` with `{id: requestId, deviceId: chosenId}`.
   To cancel, use `DeviceAccess.cancelPrompt` with `{id: requestId}`.
6. Verify connected state, identity/version accepted by the MINI profile,
   completed reads and any errors. A selection event alone does not
   prove that the app opened the port or completed the handshake.

The domain's presence in the schema does not yet prove that this build's
specific Web Serial request produces the event on this machine. That
check belongs to the future physical connection. The offline tester
includes no automatic selection, USB request or operation on the pedal.
