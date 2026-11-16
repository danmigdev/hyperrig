# Any-one-footswitch application recovery

This is a separate, offline revision of the entry guard used by the HyperRig
MINI v3 application. Holding any one of PA10, PA0 or PA3 low through the sampled
window requests the existing ROM-reset path. Their physical left/middle/right
labels are not assumed. All released inputs continue normal startup.

The exact condition is `(PORTA.IN & 0x409) != 0x409` at each of 32 samples. The
pressed subset may change between samples. It does not require one particular
switch to remain held throughout, nor does it detect a release between samples.
An observed all-released sample returns to normal startup immediately. The
100,000-iteration settling loop and 32 possible 100,000-iteration hold loops are
unchanged; their wall-clock duration has not been measured.

## Small, reversible change

The only source-level assembly change is the sample comparison in `check.S`:

```asm
    r0 = [r4+4]
    r0 &= r5
    if (r0 == r5) goto .Lrestore
```

The original comparison was `if (r0 != 0) goto .Lrestore`, which required all
three inputs to be low. Merely changing the mask cannot express the new policy.
The emitted comparison at `0x02077474` changes from `8049` to `05e80900`.
Seven existing relative branch operands change to accommodate the two added
bytes. The independent decoder checks every other instruction and destination.

The frozen prefix still makes all three selected lines inputs, preserves the
incoming G context, and calls the check before the original startup continuation
at `0x02000196`. The check restores digital-input and pull configuration, leaves
the selected direction bits as inputs, and preserves unrelated GPIO bits. Its
maximum modeled stack use remains 100 bytes. The 54-byte reset body is identical
to v3; no new SFC, clock, interrupt, codec or USB setup is introduced.

| Application detail | v3 | v4 |
| --- | --- | --- |
| Guard entry | `0x020773C8` | `0x020773C8` |
| Guard size | 298 bytes | 300 bytes |
| Executable end / PC upper bound | `0x020774F2` | `0x020774F4` |
| `cfg_tool.bin` application-area offset | `0x774F2` | `0x774F4` |
| JLFS head end | `0x77671` | `0x77673` |
| SFC encoding end | `0x77680` | `0x77680` |

The 383-byte configuration file moves by two bytes without changing content.
Its directory offset, the application length/CRC, and the head length/CRC are
regenerated. The separate PC-limit instruction at `0x0200067E` changes its bound
by two bytes. Original RAM-copy source literals remain untouched.

The full application-area candidate is 516,096 bytes. Compared with the pinned
v3 image, only physical sectors `0x4000` and `0x7B000` differ: 14 and 360 encoded
bytes respectively. Every original application byte outside the PC-limit
instruction, all 2,332 audio-shim bytes, the entry hook, the reset body and the
partition records are preserved. The integration report lists exact encoded
and decoded difference ranges, unchanged executable ranges, header preimages,
sector hashes and an inverse transformation that regenerates the complete v3
image, including its original CRCs and SFC encoding.

## Build and verification

From the repository root, with the existing vendor pi32v2 toolchain available:

```powershell
python tools/build_mini_one_switch_v4.py --output build/hyperrig-mini-audio-v4
python -m unittest tests.test_mini_entry_recovery_one -v
```

The builder refuses an existing output directory. It reproduces the pinned v3
first, compiles only the small guard, and writes the new application, ELF,
disassembly and manifests to the chosen directory. It does not rewrite any
historical source/image, access a device, or change the portable installer's
approved firmware hash. It deliberately does not rebuild an editor or inherit
v3 command-family hardware qualification.

The new application SHA-256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The baseline v3 SHA-256 is
`9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c`.
The 300-byte guard SHA-256 is
`2fa6b5396944a33156e3777632e249933cdd1e47f5d983dc5811ea0c3049bf93`.

Twelve offline tests include the assembled instruction model's 1,038 cases:
all input and inherited-direction combinations, both modeled SP aliases,
configuration readback faults, a release at every sample position, and changing
pressed subsets. They also reject wrong predicates, changed GPIO/reset bytes,
invalid ELF mappings, stale components, and unrelated application changes even
when the CRCs have been repaired. The model counts delay loops and matched stack
frames; it does not establish electrical levels or physical timing.

The historical audio manifest lists one README whose hash changed during the
English documentation migration. The new loader records its historical and
current hashes explicitly as documentation, without altering that manifest.
All executable source and compiled artifact pins must still match.

## Qualification boundary

This candidate has not been executed on hardware. The previous ROM key/reset
test covered a ROM-to-ROM transition, not cold SPL entry through this XIP guard.
The reported USB descriptor failure with all three switches held already takes
the positive branch under both policies. Changing the predicate therefore does
not explain or fix that failure; the reset implementation is deliberately kept
unchanged for this isolated revision.

Recovery depends on the application header, entry and guard remaining readable
and executable. It does not establish recovery from their corruption or from an
interrupted installation. A future actual installation and boot observation
must bind to this new image hash. v3 audio/editor evidence remains evidence for
v3, and the unchanged PONG version cannot identify v4 by itself.
