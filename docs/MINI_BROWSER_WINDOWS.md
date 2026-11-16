# Web Serial enumeration on Windows

The Chrome 157 chooser can remain on “Finding devices” before opening the
serial port. In Chromium revision `0985600c06a688b9c669e74afde7dacd5aaed047`,
`SerialUsbDisplayNameWin` is enabled by default: it reads USB descriptors through
synchronous hub-driver calls to obtain the port name. The alternative path uses
device properties already registered in Windows.
Sources: [feature definition](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/public/cpp/device_features.cc)
and [Windows enumerator](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/serial/serial_device_enumerator_win.cc).

`tools/mini_browser_windows.py` adds only `SerialUsbDisplayNameWin` to the
single existing `--disable-features` argument, exclusively on Windows.
The saved-reload v2 probe and normal launcher record the actual arguments,
reason and helper hash before starting the isolated process.
Permissions, VID/PID identification, guard and protocol remain as already
verified. No system setting is changed.

This change removes a documented blocking path; it does not prove that this
path caused the failed attempt. Chrome also waits for Bluetooth-adapter
initialization before completing the list: the USB filter does not bypass
that wait ([port manager in the same revision](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/serial/serial_port_manager_impl.cc)).
These tests verify only configuration and simulated flows; chooser and PONG
outcomes require a separate real session.

Chrome attempt v2-02 recorded COM3 in `chrome://device-log`, but the chooser
did not finish listing devices. Root's subsequent real trial with the installed
Edge showed COM3 and returned its `getInfo` without opening the serial port.
The helper therefore now selects Edge on Windows, with the same arguments and
an isolated profile. It records the selected executable; if Edge is missing,
it does not silently substitute Chrome. Other platforms retain the original
selection. A chooser result is not yet evidence of opening, PONG or presets.
