# Application guard v2 for footswitch recovery

V2 makes PA10, PA0, and PA3 inputs **before** calling the v1 check. This removes
the requirement that the cold SPL must already have left them as inputs. The
policy belongs to the new HyperRig firmware for MINI: those pins are assigned
to the three footswitches and remain inputs until subsequent panel
initialization. Other GPIO bits are preserved. V1 and the HYK1 ROM probe are
unchanged: HYK1 continues to reject output directions and restore the prior state.

This is an XIP component for the complete adapted UltraRig G application, not
a plugin executable from ROM. It has not been sent to the device or inserted
into the integrated candidate by this tool. Hardware execution and physical
recovery remain separate qualifications.

## Hook and boot context

The only patch to the original G is the 12-byte block at `0x0200018A`:

```text
preimage: eeffb850c301edffb860c301
          sp = 0x01C350B8; ssp = 0x01C360B8
patch:    goto.l <assigned address>; four nop instructions
```

The `0x02000120` entry, vectors, and all other original bytes remain intact for
this component. The prefix exactly reproduces the two stack instructions,
saves PSR/RETS/RETI and all registers r0…r15, then executes:

```text
PORTA.DIR = PORTA.DIR | 0x409
csync
call hyperrig_mini_entry_recovery_check
```

Only `ALL_THREE_HELD` reaches reset. Other outcomes, including a GPIO
configuration error, restore GPR/PSR/RETS/RETI and continue at `0x02000196`,
before the first original G call. R0 therefore retains the SPL context. The
reset branch does not return and does not need to resume the application context.

The v1 callable still saves and restores DIR/DIE/PU/PD for only the three bits,
but the saved DIR is now already input: it does not re-enable an output
direction against a pressed switch. OUT, other pins, and clock/cache/IRQ
registers are unchanged. Reset is the same as v1: `usb_update_mode\0` marker,
barrier, RST_CON bit 4, barrier, and wait. There is no arbitrary jump into ROM.

## Allocation and builder API

The address has no default. It must follow the appends already allocated by
the builder, starting from the original end of `app.bin`, `0x02076AAC`:

```powershell
python -X utf8 tools/build_mini_entry_recovery_v2.py --address 0x020772C0
```

`0x020772C0` is only the fixture corresponding to the currently available
2068-byte audio shim. A new audio shim requires a new address and build. The
code requires four-byte alignment; any padding must already belong to the
preceding append. The final limit `0x0207DE81` reserves the original 383 bytes
of `cfg_tool.bin` within the MINI app area.

The `tools.build_mini_entry_recovery_v2` APIs are:

- `build(address)`: compiles and verifies; produces payload/ELF/manifest under
  `build/mini-entry-recovery-v2/<address>/` and returns the manifest.
- `patches(g_plain, address)`: returns a tuple of `BinaryPatch` after checking
  the original decoded G hash and the 12-byte preimage.
- `bind_append(g_plain, preceding_append, payload, manifest)`: verifies that
  the address equals `0x02076AAC + len(preceding_append)`, checks hashes, sizes,
  and patches, and returns the concatenated append. It neither writes files
  nor accesses devices.

An isolated build's manifest correctly states
`actual_preceding_payload_validated=false`: a link address does not establish
that the space is allocated. The integrator must call `bind_append` with the
actual preceding bytes and pass the result and patch to the existing formatter.
The formatter remains responsible for CRCs, directories, and overlap with
other patches. It was not modified by this work.

## Reproducible checks

The component occupies 298 bytes: a 54-byte v2 prefix, 190-byte v1 check, and
54-byte v1 reset. It adds no BSS or data to copy into RAM. Maximum stack usage
is 100 bytes; both independent-SP and SSP-alias models are verified.

At each address, the model of the **actually linked instructions** runs 1280
cases: eight initial directions, eight level combinations, varying contexts,
both SP/SSP models, readback errors, and release of each switch at every point
in the 32 samples. It deliberately disturbs PSR after saving it to check
restoration; it does not simulate CPU flags. It checks R0 with both the SPL
pointer and varying values, all other registers, unrelated GPIO bits, barrier
order, and absence of reset on the normal branch.

The hook branch is also disassembled by the vendor toolchain. The ELF parser
rejects writable segments, BSS, unresolved symbols, out-of-range addresses,
and changes to the frozen callables. Both bodies must retain these hashes
even after relocation:

| Body | Byte SHA256 |
| --- | --- |
| check v1 | `0872924dc1d476913a441a6d58b83025962a00ca6b9ceb0e8b66e07d8afc045d` |
| reset v1 | `a84be9b34190a67265f001ed328372eaba2c48fcea3111b2ead481a6bb7ee48f` |

Relocation to `0x0207DD54`, ending at `0x0207DE7E` near the reserved limit, was
also verified. Its manifest remains in its build directory; the report
`research/mini-entry-recovery-v2.json` instead describes the `0x020772C0` fixture.

Physical HYK1 qualification covers switches and marker/reset in ROM. V2 removes
the dependency on the initial cold-SPL direction, but does not turn that test
into evidence for the entire XIP prefix or G boot. The actual switch mux/detection
and check duration under the inherited clock remain to be verified on hardware.
Loop counts are neither a time measurement nor an electrical or continuous
debounce model.

The guard is useful for a valid image that hangs **after** entry. A damaged
header, entry, or prefix is a different case: universal recovery from any
corrupted image is not claimed.
