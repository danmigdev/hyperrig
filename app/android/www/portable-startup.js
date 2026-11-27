/* Same reviewed 30-second open timeout; no automatic connection. */
"use strict";
globalThis.HYPERRIG_PORTABLE_SERIAL_TIMEOUT = installMiniSerialOpenTimeout(SerialTransport);
