# MINI recovery with any one footswitch

The separate v4 candidate accepts any one of the three active-low inputs
PA10, PA0 or PA3 during its startup recovery check. Physical left/middle/right
labels are not assumed. All released inputs continue normal startup.

The predicate is `(PORTA.IN & 0x409) != 0x409` at each of 32 samples. A single
switch held throughout that window is sufficient. The held subset may also
change between samples; an observed all-released sample cancels recovery.
This does not prove continuous same-pin debounce. The unchanged settling and
hold loops use 100,000 iterations each; their physical duration is unmeasured.

## Exact v3-to-v4 change

Only the small guard is assembled. At `0x02077474`, the original `8049`
(`if (r0 != 0)`) becomes `05e80900` (`if (r0 == r5)`). Seven relative branches
are relocated for the two added bytes. The GPIO mask, setup, restoration,
100-byte modeled stack bound and 54-byte reset body remain unchanged.

| Property | v3 | v4 |
| --- | --- | --- |
| Guard entry | `0x020773C8` | `0x020773C8` |
| Guard bytes | 298 | 300 |
| Executable end / PC upper bound | `0x020774F2` | `0x020774F4` |
| `cfg_tool.bin` area offset | `0x774F2` | `0x774F4` |
| JLFS head end | `0x77671` | `0x77673` |
| SFC encoding end | `0x77680` | `0x77680` |

The configuration file's 383 bytes are unchanged. Its offset, application
length/CRC, head length/CRC, and PC-limit immediate are regenerated. Only
physical sectors `0x4000` and `0x7B000` differ, by 14 and 360 encoded bytes.
All original application bytes outside the PC-limit instruction, all 2,332
audio-shim bytes, the startup hook, reset body and partition records are
preserved. No SPL or unit-specific partition data is included in the candidate.

The integration report gives exact decoded/encoded changes and unchanged code
ranges. Its inverse transformation regenerates the entire v3 image, including
headers, CRCs and SFC encoding. See the [component details](../firmware/mini/entry_recovery_one/README.md).

## Build and checks

Use the existing vendor pi32v2 toolchain and a new output directory:

```powershell
python tools/build_mini_one_switch_v4.py --output build/hyperrig-mini-audio-v4-review
python -m unittest tests.test_mini_entry_recovery_one -v
python -m unittest tests.test_portable_mini_installer_core -v
```

The builder refuses to overwrite historical outputs. Twelve guard tests passed,
including 1,038 emitted-instruction model cases. The portable core suite has
24 tests covering both pinned variants, distinct synthetic unit data, exact
final-byte validation, variant/qualification mismatches and malformed hashes.
These are offline checks, not physical observations.

Frozen source SHA-256 values:

| Source | SHA-256 |
| --- | --- |
| `tools/build_mini_one_switch_v4.py` | `d207fafe5950076728d55d5c4d2f8bfa2f6ad805aab1b7f826a8e77234557deb` |
| `tools/build_mini_entry_recovery_one.py` | `df2eb9af697b81c150a8ca07bc6cbcedc5e26613c2495c873d02b8b115eea592` |
| `firmware/mini/entry_recovery_one/check.S` | `be240fb9587f752af52e0af627450780fd0694b275da08fc5ae39ff3a08d0347` |
| `firmware/mini/entry_recovery_one/verify.py` | `635a27be6d7c4ad04b1c256d862664da15637e80fd7e8bd897921f6c66c15033` |
| `tests/test_mini_entry_recovery_one.py` | `9611f1c6f2f54574e626858134ac1652abad9c87d14f3abfbbded914e5c143cb` |

Frozen artifacts under `build/hyperrig-mini-audio-v4/`:

| Artifact | SHA-256 |
| --- | --- |
| `hyperrig-mini.app-area.bin` (516,096 bytes) | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |
| `integration-report.json` | `437b45f89b2a92b2228b7658f40a16e6f5cbab095daace32c42553396ae2d2c5` |
| `entry-recovery-manifest.json` | `7e47d84d8946e3d61d2f1cb65ae5f08ea37290bcfa2f9999260193bfef300da6` |

## Physical limits

V4 was installed on the development MINI on November 16, 2026. Two matching
fresh backups, a third pre-install read, and complete final readback verified
the exact v4 application and preservation of every external byte. Normal
software boot and USB PONG, MODEL, LVL, and PSTAT replies were observed. See the
[development upgrade](MINI_ONE_SWITCH_UPGRADE.md) for the separate workflow.

A user-assisted cold start with the left footswitch alone subsequently reached
ROM: fresh `4C4A:8057` enumeration and `WL82 UBOOT1.00` INQUIRY were verified,
with no application CDC port present. No RAM program, reset, or flash write was
sent during that ROM-access check. This qualifies that observed sequence on
this unit; the other two individual switches and interrupted-write recovery
remain untested. The earlier
ROM key/reset test covered ROM-to-ROM execution, not cold SPL entry through
this XIP guard. A damaged application header, entry or guard may prevent the
check from running at all.

The reported descriptor failure with all three switches held already reaches
the positive branch under both policies. This condition-only change therefore
does not claim to fix that failure. The reset sequence is deliberately unchanged.

V3 physical editor/audio evidence remains evidence for v3. An unchanged PONG
version cannot identify the new image; the v4 observation is bound to the actual
installation/readback and subsequent boot. The v4 preview enables no write
families by inheriting v3 evidence alone.
