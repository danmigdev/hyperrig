# HyperRig MINI app protocol verification over USB CDC

`tools/probe_mini_app.py` prepares verification of the original UltraRig
protocol in the complete MINI port. The CLI opens a port only with the explicit
`read` subcommand; importing it or running its default command does not enumerate
devices. This work used simulated transports only. It does not yet demonstrate
CDC enumeration, execution of the port, audio, or writes to the MINI.

The request source is
[`tankg.html`](../recovered/ultrarig-original/web/tankg.html), SHA-256
`247d152045a9d8f987281e7e943c1ea359ccc2db1392f6a0cb439587717e88e6`.
The probe checks the hash and protocol anchors before preparing a session.
It does not use USB-MIDI, stock SysEx, or the recovery ROM protocol. Descriptor
evidence is in
[`MINI_APP.md`](MINI_APP.md) and
[`mini-app-protocol.json`](../research/mini-app-protocol.json).

| USB identity | Meaning to the probe |
|---|---|
| `3654:5155` | UltraRig CDC candidate; G also uses these IDs. A subsequent `PONG tankm_fw …` is required. |
| `4C4A:C755` | Stock MINI USB-MIDI; incompatible. |
| `4C4A:8057` | Jieli recovery ROM; incompatible. |
| `3654:4155` | Template value only, before runtime PID modification; rejected. |

Enumeration reads only the serial ports exposed by the operating system. A MIDI
or ROM device may therefore not appear at all: an empty list does not prove
that the pedal is disconnected. Missing USB IDs are not inferred from the port
name. The first port is not selected automatically.

## Intended use after the port boots

The plan is entirely offline and does not require pyserial:

```powershell
python -X utf8 tools/probe_mini_app.py
```

Future serial operations require `pyserial`, which can be installed separately
with `python -m pip install pyserial`. The following enumeration does not open ports:

```powershell
python -X utf8 tools/probe_mini_app.py enumerate
```

Prepare a local manifest referring to the actual candidate image. This example
refers to the formatter's local baseline candidate; it does not certify that
the image is installed or complete for the board:

```json
{
  "target": "tank-mini",
  "architecture": "standalone-ultrarig-port",
  "firmware_version": "tankm_fw M5.71 rel ble",
  "image_path": "build/mini-ultrarig/hyperrig-mini-g-derived.app.bin",
  "image_sha256": "4e74d0c0b1c1f491afdaa92e441d4504efcaff4237b4af1706e57a6e434a20ab",
  "capabilities": {"read": true, "write": false, "panel": false},
  "hardware_verified": false
}
```

Saved, for example, as `build/mini-app-read-manifest.json`, it can be used by
both the probe and the editor. Replace the path/hash when the candidate changes;
the loader recalculates the local file's hash and rejects discrepancies. To
generate the editor in a separate directory without overwriting the default
build or its report:

```powershell
python -X utf8 tools/build_mini_app.py --firmware-manifest build/mini-app-read-manifest.json --output build/hyperrig-mini-read --report build/hyperrig-mini-read/report.json
```

With the port actually running and its port known, an initial check limits the
session to `PING` alone by passing `--queries` without arguments. These commands
**open the port and send requests**, unlike the earlier plan:

```powershell
python -X utf8 tools/probe_mini_app.py read --port COM8 --firmware-manifest build/mini-app-read-manifest.json --log build/mini-cdc-ping-001.jsonl --queries
python -X utf8 tools/probe_mini_app.py read --port COM8 --firmware-manifest build/mini-app-read-manifest.json --log build/mini-cdc-read-001.jsonl
```

`COM8` is an example to replace. The log directory must already exist; an
existing log is rejected before enumerating/opening the port. For a smaller
selection, use, for example, `--queries MEM PLIST PSTAT`. Every session still
starts with `PING`, exactly once.

## Framing, responses, and limits

Requests are ASCII with an LF terminator, one at a time. The transport uses
115200 baud, 8N1, no flow control, a 50 ms read timeout, and a 1 s write timeout.
Responses are reassembled from arbitrary chunks and decoded as UTF-8 only
when a complete line is available; CRLF is accepted. DTR/RTS are set to false
before opening, with no pulses or subsequent changes. The physical behavior
of the lines at open also depends on the OS/driver and remains to be verified
on the port. Creation with `Serial(port=None)` and this driver limitation are
described in the [official pyserial API](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

Timeouts come from the original `Pedal.cmd` call sites; the line numbers below
refer to the frontend pinned by its hash, not the derived build.

| Literal request | Completion | Timeout | Line |
|---|---|---:|---:|
| `PING` | `PONG …`, then the exact MINI version from the manifest | 700 ms | 10351 |
| `MODEL` | `MODEL` prefix | 1500 ms | 5451 |
| `MEM` | `MEM` prefix | 3000 ms | 5466 |
| `LVL` | `LVL` prefix | 800 ms | 5413 |
| `FXT` | exact line `FXT end` or `FXT fin` | 3000 ms | 5392 |
| `FXS` | `^FXS (peak\|pico)\b` | 2500 ms | 5414, 5506 |
| `FXMIX` | exact line `FXMIX end` or `FXMIX fin` | 1500 ms | 5426 |
| `FXXO` | exact line `FXXO end` | 1200 ms | 14215 |
| `PLIST` | `PLIST end/fin current/actual=N`, consistent list | 4000 ms | 12067 |
| `PSTAT` | `PSTAT` prefix | 2000 ms | 11075 |
| `SNAPS` | `SNAPS` prefix | 1500 ms | 8380 |
| `SNAPNAME` | `SNAPNAME end` prefix | 1500 ms | 8388 |
| `CLIST` | `CLIST end` or `CLIST fin` prefix | 4000 ms | 14089 |

The default selection after PING is `MODEL MEM LVL FXS PLIST PSTAT SNAPS
SNAPNAME`. Arguments, arbitrary commands, uploads, resets, event subscriptions,
and mutations are not accepted. `FXS end` is not the actual terminator. The
PLIST parser retains the 32 UltraRig slots and the original name limit of 23
UTF-16 units. It rejects duplicate, unordered, or out-of-range slots, truncated
lines, and a missing active preset. An inconsistent list does not become an
empty list. The probe does not apply the original frontend's retries.

`@…`, `NOISE ms=…`, `CALIB …`, and `ERR CALIB stopped…` are logged separately;
they do not complete a request. Other `ERR` responses, timeouts, partial writes,
and decoding/transport errors logically terminate the session: no retry,
reconnection, or subsequent command. Before each request, pre-existing bytes
are logged and discarded; input that does not become idle within 500 ms prevents
the send. Limits are 8192 bytes per line, 256 KiB per response, and 4096 nonempty
lines. A response arriving after the timeout remains in the log and is not accepted.

The JSONL log records UTC/monotonic times, manifest context, requests, received
bytes in hexadecimal, lines, and termination causes; it may include preset
names and descriptive contents. Bytes are preserved even when the parser rejects
the response. `PONG` verifies identity/version; it **does not read the firmware
hash from the device**: `image_hash_attested_by_device` remains false. Completing
these reads does not qualify audio, stability, saving, or other editor commands.

## Offline checks and editor gate

```powershell
python -X utf8 -m unittest tests.test_mini_app_transport -v
```

The 14 tests use fake ports; they do not import a driver to open devices. They
cover UTF-8/CRLF fragmentation, asynchronous responses, rejected G/B/stock
identities, forbidden commands, late data, timeouts, disconnects, partial writes,
limits, log preservation, and simulated port closure. One test runs the original
PLIST parser in Node and compares the results.

Another actually generates the editor in a temporary directory with the local
candidate hash, `read=true`, `write=false`, and `hardware_verified=false`; it then
runs the JavaScript gate: MINI PONG accepted, PLIST allowed, PSAVE denied. Reading
does not wait for completed hardware qualification: its purpose is to gather
that evidence. The frozen editor files and the
`research/mini-app-protocol.json` report have not been modified.

## Proposal for subsequent write tests, not implemented

The first useful cycle concerns a single live parameter after qualifying reads,
recovery, and audio conditions. From the original frontend at lines 7576–7578:
request `FXP <id> <index> <value>`, response `FXP ok <effective_value>`.
The proposal is:

1. Read FXT, FXS, and the active preset and scene; choose an existing parameter
   with known limits and no structural effects on routing, memory, resources,
   or audio mode. Preserve the original value and the state of other blocks.
2. Apply a different allowed value; require an ACK with the effective value and
   reread FXS to verify that value and the absence of unexpected changes.
3. Restore the original value with FXP; require an ACK and FXS consistent with
   the initial semantic state. A timeout stops the test: it is not evidence of
   successful restoration and does not authorize a blind retry.

This verifies only that live change. It does not demonstrate the absence of
automatic NOR writes or restore the internal history of delay/reverb effects.
The full app profile enables writes broadly and requires a report with
`all_required_editor_mutations_verified=true`, bound to the same image hash.
A single FXP cycle **does not meet that requirement**: the other families must
be qualified, or the new exact-request capabilities documented in
[MINI_APP.md](MINI_APP.md) must be used. These retain `write=false` and require
evidence only for the explicit subset: none is enabled at this point. Do not
generate the full qualification flag from reads alone or from the live cycle
alone. This editor extension does not add writes to the CLI.

Qualifying persistence requires a separate test on a genuinely free temporary
slot, after a backup: `PSAVE <slot> <name>` (name without added quotes; ACK
`PSAVE ok`, original timeout 8 s), PLIST, `PLOAD <slot>` (ACK `PLOAD ok`, 8 s),
and a state read; finally, restore the original preset/scene and any preceding
live changes, delete only the temporary slot with `PDEL <slot>` (ACK `PDEL ok`),
and obtain a new PLIST. PSAVE also changes the current preset; snapshots require
additional checks of their own. Restoration is logical and does not undo NOR
wear or sequences. Even the original full export is not a simple read: the
`pioReadPreset`/export functions traverse scenes with SNAP and, in some paths,
PLOAD. The probe does not invoke them.
