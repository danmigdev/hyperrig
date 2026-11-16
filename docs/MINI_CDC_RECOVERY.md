# MINI: entering ROM from HyperRig firmware

The original command is **`UBOOT\n`**. G M5.71 firmware contains the
**`OK UBOOT\n`** response and a reset path that writes the ROM marker.
The local audit confirms that these instructions are identical in the installed
MINI v2 candidate, SHA256
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
The new procedure is prepared and verified offline; it has not been executed.

## Original evidence

Recovered bytecode `recovered/installer/tankg_install.dis.txt` shows:

- `RealPedal.cdc_cmd`, original lines 3163–3191: opens CDC at 115200, sends PING,
  then the requested command. The UBOOT branch tolerates port closure.
- `_cmd`, original line 3219: encodes and sends `line + '\n'`.
- Update flow, original line 5185: calls `cdc_cmd('UBOOT')`.

The original installer returns the string “OK UBOOT (port closed by the
pedal)” when it catches `SerialException`. This is a synthetic installer
result. The new helper retains only an ACK actually received.

In the decoded G binary, SHA256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`:

| Step | Address / effect |
|---|---|
| Command string | `0x02035AA3`: `UBOOT\0` |
| Comparison | `0x020116E0..0x020116F2`, strcmp → branch `0x020140C8` |
| Response | `0x02035D77`: `OK UBOOT\n\0`, sent through `0x02006E24` |
| Wait | `0x020140EA`: 5 ticks through `0x0203FEB8`; physical duration not assumed |
| Retention state | `0x020140F2..0x020140FC`: clears word `0x01C7FDFC` |
| Critical section | `0x01C00FB6`: CLI, core lock, `csync` |
| Marker | `0x02000B80`: copies 16 bytes of `usb_update_mode\0` from `0x0203A135` to `0x01C7FD80` |
| Reset | P33 helper `0x01C00F4A(0xA0,4,1,1)`: sets bit 4, then loops |

The three predispatch functions `0x0200B834`, `0x0200D60C`, `0x0200E07A`
return 0 for UBOOT. The main comparison reaches the recovery branch.
The verifier follows those instructions, models only strcmp, and rejects
state-RAM reads: **no safe flag is read along the reconstructed path**.
Stack saves are omitted; this is not a complete ABI or peripheral simulation.
Send, scheduler, lock and reset functions must still work on the device.
The command branch contains no NOR operation.

This evidence makes UBOOT a concrete candidate even after the observed
`safe` PONG, but does not yet prove physical recovery from that mode.
A blocked parser cannot receive the command. An ACK or disconnection alone
does not prove a new ROM enumeration.

## Separate Web Serial procedure

`tools/enter_mini_rom_webserial.py` opens no browser or device without
`--execute`. It does not modify the editor, read-only profile or frozen
manifests. It uses a separate local recovery page, Chrome with a new profile
and a new serial port opening. It neither requires nor claims a held-footswitch
trial.

Before execution, the coordinator must:

1. Complete and review the artifacts required for the subsequent upgrade.
2. Close desktop 03 through its own closure path; verify the new **completed**
   `session.json`, `native_close_verified=true`, and stopped browser/server.
   Record its actual hash. Connected-proof 03 remains unchanged, SHA256
   `96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2`.
3. Run the preflight below first. Replace `CLOSED_SHA` with the hash of the
   actually completed report; never construct a closure report by hand.

```powershell
python -X utf8 tools/enter_mini_rom_webserial.py --check-only --connected-proof build/mini-desktop-real-03/connected-proof.json --proof-sha256 96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2 --closed-session build/mini-desktop-real-03/session.json --closed-sha256 CLOSED_SHA
```

Execution uses the same arguments, replacing `--check-only` with
`--execute --output build/mini-cdc-to-rom-01`. The output must be new.
The window shows only the ROM procedure; its title is
`HyperRig MINI · recupero ROM` (the historical title, meaning “HyperRig MINI · ROM recovery”). The session lasts at most 120 seconds before
the command. PING is sent once and must produce the same real identity observed
in the previous session.

The coordinator reads `recovery.json` with the shared-delete helper, identifies
`browser_process_id` and `origin`, selects only
`Tank-M HyperRig (COM3)` in the native chooser through UIAutomation, and
atomically publishes `build/mini-cdc-to-rom-01/selection.json`:

```json
{
  "observed_utc": "ACTUAL_SELECTION_TIMESTAMP",
  "browser_pid": 123,
  "origin": "http://127.0.0.1:ACTUAL_PORT",
  "selected_row": "Tank-M HyperRig (COM3)",
  "exact_unique_row_verified": true,
  "no_other_device_selected": true,
  "method": "Windows UIAutomation SelectionItem and Invoke"
}
```

PID, origin and timestamp are real observations of the new window.
The command does not proceed without this record and an exact fresh PONG.
The CDP DeviceAccess domain did not expose the Web Serial chooser in the tested
Chrome: see `MINI_WEBSERIAL_CHOOSER.md`. The new helper does not assume that support.

Before calling `enterROM()`, it publishes the intent and synchronizes it to disk.
The page can transmit only `PING\n` and `UBOOT\n`, once each;
it exposes no arbitrary-write API. The guard consumes the attempt before the
native write: a timeout, error, lost ACK or disconnection permits no second UBOOT.
TX/RX bytes and events remain in the report. Cleanup closes streams, port,
browser and server; a close error is recorded without claiming a native closure
that was not observed.

## Result contract

`recovery.json` always contains `command="UBOOT"`, `prior_port`,
`automatic_retry=false`, `firmware_write=false`, `ROM_verified=false`.
Separate fields:

| Field | Meaning |
|---|---|
| `pong` | Line actually received through the new Web Serial connection, identical to the previous evidence |
| `command_intent_utc` | Host timestamp before publication/fsync and invocation |
| `command_invocations` | 0 or 1, with no reissue |
| `command_submitted_once` | The guard consumed the single attempt and recorded native TX |
| `command_submitted_utc` | Timestamp of the actual browser TX event, distinct from host intent |
| `command_write_completed` | Native write resolution; not equivalent to reset execution |
| `ack_observed` | The `OK UBOOT` line was actually received after the attempt |
| `native_disconnect_observed` | Web Serial removal event for that port |
| `native_close_verified`, `serial_port_closed` | `port.close()` resolved without error; not inferred from removal |

Exit code 0 means the guard observed the single request and the procedure ended
without an orchestration error; it does **not** attest to ROM or reset.
The coordinator must verify a new ROM enumeration, arrival after TX, and an
actual `WL82 / UBOOT1.00` INQUIRY, then acquire a complete unit dump before
any NOR mutation. This helper performs none of those steps and requires
no administrative privileges.

## Offline verification

```powershell
python -X utf8 tools/audit_mini_cdc_recovery.py
python -m unittest tests.test_mini_cdc_recovery -v
node tests/mini_rom_webserial_guard_test.js tools/mini_rom_webserial/guard.js
```

Result: 9 Python tests and 61 Node conditions passed. They cover original bytecode,
absence of the safe gate on the path, evidence/closure/picker checks, fragmented
PONG, wrong device, duplicates, write error, actually received or absent ACK,
disconnection, RX limits and failed close. All test transports are fake;
no test opened the pedal or modified a live browser session.
