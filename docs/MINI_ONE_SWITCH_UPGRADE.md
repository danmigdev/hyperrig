# Development upgrade from installed v3 to v4

This is a separate development workflow for an already installed HyperRig v3
MINI. The stock installer and its sealed preview are unchanged. It targets the
exact v4 candidate described in [MINI_ONE_SWITCH_RECOVERY.md](MINI_ONE_SWITCH_RECOVERY.md).

`tools/upgrade_mini_one_switch.py --check-only` validates local release files
without accessing hardware. The worker needs Windows administrator access for
the ROM transport. Its default bundle is
`build/hyperrig-mini-installer-one-switch-preview-02`.

```powershell
python -B tools/upgrade_mini_one_switch.py --check-only
python -B -m unittest tests.test_mini_one_switch_upgrade -v
```

After source review, the explicitly elevated worker starts with:

```powershell
python -B tools/upgrade_mini_one_switch.py --execute --port COM3 --output build/mini-one-switch-upgrade-new
```

The worker identifies the sole HyperRig CDC device with a fresh, exact normal
PONG, sends `UBOOT` once, closes serial, and independently checks a new ROM
arrival and the existing transport's ancestry and INQUIRY checks. Neither a
successful serial write nor an ACK establishes ROM identity. No UBOOT retry
or USB reset is performed on failure.

The existing pinned NOR reader obtains two full 1 MiB backups. Both must match,
with the expected SPL and exact v3 application. The plan preserves every byte
outside the application from these fresh reads, including current presets and
unit-specific data. It changes only sectors `0x7B000` and `0x4000`, in that order,
with header page `0x4000` last. It does not restore runtime data from an older
stock backup.

After reviewing `installation-plan.json`, request the separate installation:

```powershell
python -B tools/upgrade_mini_one_switch.py --install --output build/mini-one-switch-upgrade-new
```

The requester independently reconstructs the plan from both saved backups and
the sealed release. The worker then obtains a third complete read and requires
it to match both backups before invoking the existing operational writer. A
complete final read must equal the exact v4 application plus every preserved
byte. These files remain under the ignored build directory.

After reviewing the final read and `verification.json`, request boot:

```powershell
python -B tools/upgrade_mini_one_switch.py --boot --output build/mini-one-switch-upgrade-new
```

This requester independently checks the saved pre-install and final reads
before emitting a hash-bound boot request. The worker retains the live reader
between stages and invokes the existing one-shot reset only after verification.
Each stage request has a 20-minute deadline. An error, timeout, or an optional
`stop.request` file between stages closes the worker without a reset or rollback;
the pedal remains in ROM. An active write is not interrupted by a stop request.

The new tests use public firmware and synthetic unit data, plus mocked serial,
PnP, and ROM transports. They cover changed backups, private-data preservation,
corrupted readback, uncertain writes, wrong identity, incomplete UBOOT, stale ROM
arrival, and stage binding. These offline results do not qualify physical v4
boot, audio, or footswitch recovery. The previous three-switch Code 43 failure
is not claimed fixed by changing the recovery predicate alone.

## Physical observations on November 16, 2026

The development MINI completed this workflow in
`build/mini-one-switch-upgrade-01`. Both initial 1 MiB backups and the third
pre-install read matched. The independent comparison with the unit's original
backup also confirmed the same SPL and key/MAC region.

Exactly two erase requests and 32 page programs were recorded, in the planned
order, with page `0x4000` last and no transport errors. The complete final read
matched the v4 application and every external byte from the fresh backup:

| Item | SHA-256 |
| --- | --- |
| Fresh complete preimage | `3b5635a7f12573eec9196483ae75f9d6248df83d6688c4230744dd296e1811b4` |
| Complete final readback | `f39047c4ad282a0171621e3fa0e8473452c0e66624d7a0662ecc35c63275b78a` |
| V4 application area | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

The separate software boot returned COM3. Fresh PONG, MODEL, LVL, and PSTAT
replies identified normal HyperRig, model A2, preset index 0, gain 0/0, and an
empty FX chain. The serial session closed normally.

The user then acknowledged the requested USB-disconnect, power-off, ten-second
wait, and startup holding only the left footswitch. The physical sequence was
user-operated, not independently observed. Windows enumerated a fresh
`4C4A:8057` ROM disk without an application CDC port. A separate native INQUIRY
returned `WL82 UBOOT1.00`; its arrival timestamp was newer than the closed
normal v4 session. That check uploaded no RAM code, wrote no flash, and sent no
reset. Its evidence is in `build/mini-v4-cold-start-01`.

After the user restarted with all footswitches released, COM3 returned and a
second PONG/MODEL/LVL/PSTAT session completed with model A2, preset index 0,
gain 0/0, and an empty FX chain. The port and temporary administrator session
were closed. The consolidated local record is
`build/mini-one-switch-upgrade-01/hardware-summary.json`.

This establishes the observed left-switch recovery sequence on this unit.
It does not establish all three individual switches, recovery from a damaged
header/guard, or recovery after an interrupted flash write. The user could not
listen to audio during this session; v4 audio remains untested. The preview used
at this stage had a read-only editor. The later [v4 controls trial](MINI_V4_EDITOR.md)
established the bounded USB capabilities now enabled in preview 05.

The 120 existing installer/guard tests and 19 new upgrade tests passed offline.
Those tests are separate from the physical observations above.
