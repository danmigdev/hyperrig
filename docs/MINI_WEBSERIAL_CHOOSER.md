# CDP chooser limitation observed in desktop session 01

Session `build/mini-desktop-real-01/session.json`, read through
`read_shared_bytes`, records `requests=1`, `opens=0`, no TX/RX lines, and
no `chooser_prompts` events. After 60 seconds, the launcher stopped the
guard. **This session neither opened the serial port nor tested the firmware
through WebSerial.** Root subsequently used UIAutomation, only in that
session's Chrome window, to observe the native chooser with the exact
`Tank-M HyperRig (COM3)` row and the Connect button.

The observed Chrome version is `157.0.8103.52`; `/json/version` reports revision
`0985600c06a688b9c669e74afde7dacd5aaed047`. In the corresponding source,
`SerialChooserController` populates the native list and, in `Select`, grants
permission and completes the callback. It does not forward the request to
the DeviceAccess domain. Option names include the COM component of the path.
[Chromium source at the observed revision](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/chrome/browser/ui/serial/serial_chooser_controller.cc).

The serial service invokes the chooser through `SerialDelegate::RunChooser`;
only after selection can it resolve `requestPort`. Opening the device
is a separate, subsequent operation. This agrees with `requests=1` and
`opens=0` in session 01.
[SerialService at the same revision](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/content/browser/serial/serial_service.cc).

At the same revision, the Bluetooth controller implements
`BluetoothDeviceRequestPromptInfo` and explicitly calls
`UpdateDeviceRequestPrompt`. Availability of the CDP domain in the schema
therefore does not demonstrate that the WebSerial chooser emits that event type.
[Bluetooth controller at the same revision](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/content/browser/bluetooth/bluetooth_device_chooser_controller.cc).

The previous check for the mere presence of the CDP domain was insufficient
evidence of integration. The guard's Node tests verify the allowlist,
identity, limits, and closure with a fake serial port; they do not prove
delivery of native chooser events. Another mock that assumes the very
event that is missing would not be useful.

For a new session, root can select the exact COM row in the native chooser
without changing the guard's capabilities. The frozen launcher does not require
selection through CDP: it proceeds when `requestPort` returns the port,
rechecks VID/PID, and permits only PING until PONG.
Session 01 has already stopped and must not be reactivated by manipulating guard state.

Diagnosis of the new trial must distinguish: chooser requested, port
returned, native open completed, write completed, and PONG received.
An entry in the TX list before `write()` resolves does not prove that
the firmware read the command. Success remains a real PONG followed
by read-only replies, rather than port selection alone.

No frozen source, browser, device, or window was modified during
this analysis.
