# Persisting the A2 capture before the first preset

The real Web Serial session `build/mini-desktop-real-03/connected-proof.json`
returned `MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0`,
`CLIST end current=-1 slots=15` and `PLIST end current=-1`. The capture is
therefore active without a selected persistent slot. The original editor code
explains that `current=-1` also includes the factory-embedded capture.
This observation was in `safe` mode; it does not prove working audio.

No real `CSAVE` or `CREAD` was executed for this preparation.
The offline audit, input hashes and plan derived from the previous observation
are retained in
[`mini-default-capture-persistence.json`](../research/mini-default-capture-persistence.json).
The plan must be derived again from fresh observations in the session that
will execute the trial.

## Why a direct save is possible

In the original G M5.71 firmware, the `CSAVE` handler at `0x0200C28C` checks
slot `0..14`, the current capture pointer and its length. It does not require
a previous upload or a current slot other than `-1`. Initial data at
`0x0207593C` contains pointer `0x02033C8C` and length `4892`.
On success, `0x0200C532` selects the saved slot.

The original blob is
[`embedded-0.a2l`](../analysis/firmware/m571_g_app/embedded-0.a2l):

- 4,892 bytes, `A2L1` format, name `A2`, 23 layers, 3 channels;
- SHA256 `86f5ea91f8069180e30612bcaad5820b14a94dd6c2552290ca09253082238c47`;
- whole-blob CRC32 `2144df1c`; final little-endian CRC and content ID `77ac505b`;
- the same complete sequence occurs exactly once at `0x02033C8C`, in both
  the installed v2 candidate and the prepared v3 candidate.

`CSAVE` constructs a 40-byte `TKGC` header and saves the payload.
The original store compares the header and payload read back before returning
success. The prepared trial nevertheless requires a second independent
comparison through `CREAD`. Slot 0 occupies NOR `[0xDF000,0xE1000)`:
saving is a persistent library write, not a temporary change.
Only the first slot absent from a complete `CLIST` is used; no existing
capture is selected as the destination. The new capture is intentionally retained.

## Plan and readback contract

[`mini_capture_persistence.py`](../tools/mini_capture_persistence.py) contains
only pure functions. It opens no files, browsers or devices and sends no commands.
`plan_capture(answers, blob)` requires the exact `MODEL` and a complete,
consistent `CLIST`. If `current=-1`, it prepares one `CSAVE <slot> A2`
request. If A2 is already selected and metadata matches, it prepares readback
only. There are no uploads, `CLOAD`, deletions, audio commands or automatic
attempts after an error.

The original protocol uses:

| Request | Response |
| --- | --- |
| `CSAVE 0 A2` | `CSAVE ok 0 'A2' 4892 B` |
| `CREAD 0` | `CREAD 0 len=4892 crc=2144df1c id=77ac505b aux=0 fs=0 name='A2'` |
| `CREAD 0 <offset>` | `CREAD 0 <offset> <n> <crc8hex> <base64>` |

There are 51 chunks at offsets `0,96,...,4800`: 50 of 96 bytes and a final
92-byte chunk. The original request has no length parameter. The verifier
checks the slot, offset, length, canonical base64, every CRC, and finally all
bytes against the original blob. It also requires an unchanged `MODEL`,
the correct current slot, and unchanged metadata for other `CLIST` entries.
It does not read or claim to verify every existing payload.

`aux=0` follows from zero trim and absence of the optional training level:
the `MODEL` formatter and `CSAVE` read the same structure at `0x01C26B48`;
`0x0200A5F6` packs those values into the header. The parser requires the
exact `MODEL` without an `in=` suffix, then rechecks `aux` and `CLIST`
after saving. `fs=0` is the value produced by the capture branch of
`CREAD` at `0x020072CC`. It is not the 48 kHz sample rate in the A2L file.

## Editor integration and evidence limits

The original editor uses `CSAVE` at the end of `captureToSlot`, normally
after an upload. The library has no original dedicated button for saving
the currently embedded model. The trial's diagnostic preamble can use the
same editor queue for one planned `CSAVE`, retaining requests and responses;
it does not simulate an existing UI feature.

Original method `pioSlotHead` sends `CREAD <slot>`, and `pioSlotRead`
sends `CREAD <slot> <offset>`. The frozen MINI adapter's `isRead` pattern
instead requires three numeric arguments for `CREAD`, excluding both forms.
The experimental wrapper must therefore explicitly permit only the planned
header and offsets. Frozen files remain unchanged, and retries from the
original generic reader are not imported into the trial.

The result of `verify_capture` attests to the supplied transcript, not its
hardware provenance. The lifecycle must add the port, real PONG, image hash
derived from installation, trace and connection closure. An immediate
`CLOAD` of the same slot can reuse the model already in RAM:
it would not demonstrate a cold load. Even a complete `CREAD` comparison
does not prove retention after a power cycle or audio quality.

Completed offline verification: 17 tests in
[`test_mini_capture_persistence.py`](../tests/test_mini_capture_persistence.py),
covering original data and the v3 candidate, occupied slots, incomplete replies,
altered metadata, out-of-order chunks, incorrect CRCs and noncanonical base64.
