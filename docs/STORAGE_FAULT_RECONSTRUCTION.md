# Diagnostic records and fatal control path

This module reconstructs fifteen complete M5.71 bodies and executes their two
previously recovered IRQ dependencies. It compares portable C with independently
decoded original instructions, including public aliases, ordered CPU/MMIO
observations, callback mutations and incomplete paths. It performs no device
access and does not change firmware images.

The storage caller at `0x02002b7a` has a four-byte direct call to `0x0200096e`;
its next address is `0x02002b7e`. The verifier binds this exact call in the pinned
original and MINI images. The caller itself is not executed or replaced by this
standalone module. The fatal body ends at a self-loop at `0x020009c8`. Observing
that instruction is explicitly different from returning, restarting a device or
completing a durable storage write.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
The reconstructed source retains the required notice; see
[the preserved license](../third_party/ultrarig/LICENSE.md).

## Complete scope and ABI

Addresses below are half-open. Argument names describe the recovered behavior;
they are not recovered source symbols. Every argument occupies one raw uint32
word unless its pointer is used for byte access. Void helpers normalize the
portable result to zero only after an ordinary native return.

| Name | Start | End | Bytes | Instructions | Arguments and result |
| --- | --- | --- | ---: | ---: | --- |
| tag | `0x02000730` | `0x02000758` | 40 | 11 | word; recognized tag boolean |
| record_count | `0x02000758` | `0x0200077c` | 36 | 12 | none; validated low-halfword count |
| append | `0x0200077c` | `0x02000800` | 132 | 46 | source record token; void |
| checksum | `0x02000800` | `0x02000830` | 48 | 16 | first word, second word, tail word; checksum |
| decode | `0x02000830` | `0x0200088e` | 94 | 37 | output token, zero permits validation alone; boolean |
| encode | `0x0200088e` | `0x020008ee` | 96 | 31 | eleven-byte input token; void |
| update | `0x020008ee` | `0x02000952` | 100 | 36 | kind, alternate counter selector; void |
| once | `0x02000952` | `0x0200096e` | 28 | 10 | kind; void |
| fatal | `0x0200096e` | `0x020009ca` | 92 | 31 | none; reaches the infinite loop |
| acquire | `0x01c00e86` | `0x01c00e9c` | 22 | 8 | none; void |
| exchange | `0x01c00e9c` | `0x01c00eb6` | 26 | 9 | raw data word; low-byte reply |
| release | `0x01c00eb6` | `0x01c00ec8` | 18 | 7 | none; void |
| read_register | `0x01c00ec8` | `0x01c00f0c` | 68 | 24 | raw identifier; reply byte |
| write_register | `0x01c00f0c` | `0x01c00f4a` | 62 | 21 | raw identifier, data word; void |
| masked_register | `0x01c00f4a` | `0x01c00f72` | 40 | 16 | identifier, shift, width, value; void |

The new scope is 902 bytes and 315 instructions. Reused IRQ enter
`0x01c00e2e..0x01c00e46` and IRQ leave `0x01c00e46..0x01c00e62` add 52 bytes and
17 instructions to the execution closure. The original contains 24 direct calls
within this closure and no indirect function calls. All complete endpoints and
calls are decoded and authenticated before execution.

## State and record ordering

| Original address | Mutable role |
| --- | --- |
| `0x01c26890 + 8` | once-only update byte |
| `0x01c26890 + 104` | flags read by the counter update and fatal record |
| `0x01c7fba0` | record header: upper halfword `0xc7a5`, lower count |
| `0x01c7fba4..0x01c7fbd4` | two six-word diagnostic records |
| `0x01c7fbd4..0x01c7fbe0` | three encoded metadata words |
| `0x01c7fdd8..0x01c7fdf0` | current six-word diagnostic record |
| `0x01c1fa2c` | byte used by TESTSET and release |
| `0x01c1fc54 + (CNUM << 2)` | wrapped IRQ nesting word address |

The lock's four initialized application bytes are bound separately as mutable
startup evidence. The upper-RAM diagnostic records lie beyond the initialized
application image; fixtures supply those bytes. This does not establish a
physical nonvolatile region, persistence across reset or storage durability.
No immutable table or inventory data exclusion is introduced.

The tag accepts exactly upper-twelve-bit values `0xa5e`, `0xd06` and `0xe7c`.
`record_count` returns zero for an invalid header or a count above two. This is
the native validation, not a portable input restriction. `append` first checks
the source tag, compares all six words with the most recent record for
deduplication, shifts the old record word by word and then rereads the supplied
source. Source aliases are preserved: a source pointing at the second record
can be overwritten by the shift before the subsequent source copy. The header
is published last.

The checksum wraps uint32 multiplication and xor operations before selecting
the low halfword. The decoder caches three metadata words before any output
store. It checks the checksum, upper mode bound, nonzero low tail byte and its
zero high nibble. It initializes exactly eleven output bytes. The encoder reads
its fields in native order, caps the mode at five, masks the two counter nibbles
and publishes three metadata words in order.

`update` owns a twelve-byte private buffer, with one unused byte left
uninitialized. Only bytes actually written by a successful decoder are read by
the updater and encoder. Depending on kind/alternate, one byte counter
saturates at 255 or one nibble counter saturates at 15. `once` sets its flag
before attempting that update, including when the metadata is invalid.

The fatal body captures entry RETS and CNUM, archives the previous current
record, performs the once-only counter update, then writes its new current
record. It stores flags/core/tag, zeroes offsets 8 and 4 in that order, stores
the captured caller address and zero at offsets 12 and 16, then reads peer
status into offset 20. Finally it performs the recovered masked register update
and reaches the original self-loop. Callback mutations at each observation
remain visible according to this order.

## Register and CPU boundaries

The explicit MMIO spans are `0x00013e08..0x00013e10`,
`0x01eef07c..0x01eef080` and `0x01eef27c..0x01eef280`. The module does not assign
a physical peripheral identity to them. READ events return supplied values;
WRITE, barrier and CPU events preserve their original width, order and value.
Only event completion and returned register contents are fixtures. No function
computations in the recovered closure are replaced with scripted results.

`acquire` runs actual IRQ enter, a barrier, the byte TESTSET loop and a final
barrier. TESTSET reads the old byte, stores `0xff`, derives flags from its low
four bits and branches on old bit 2. Its event callback runs after those effects;
a mutation does not retroactively change the captured flags. The loop is
unbounded in the original. `exchange` writes the full supplied word, updates
the control word, observes a barrier and waits while control bit 1 stays set.
Its loop also has no native timeout. `release` clears the byte before executing
actual IRQ leave.

Register identifier bit 15 selects the signed-low-halfword branch. The command
and identifier transfers retain their native masks; the value transfer is a
raw word. The masked update uses shift counts modulo 32 and truncates the final
word to a byte. A width of 32 therefore follows the original zero-width mask
behavior.

The exact primary ISA records are captured and hashed in the report:

- `mov.r_sr` defines RETS bits 26..1 and CNUM reads. The API supplies entry RETS;
  its native caller is independently bound as described above.
- `cli` and `sti` change ICFG bit 9 and preserve the other bits. Reused IRQ
  helpers execute their real wrapped counter operations.
- `testset.b` defines the old-byte flags and `0xff` store; `bc.eq` selects bit 2.
- `ext.l.s` sign-extends the low halfword and updates N/Z while preserving C/V.
- `rmw.or.modimm`, `rmw.and.nmodimm`, `rmw.or.r` and `rmw.and.r` define the
  memory read/modify/write forms used for register control.

These records come from the pinned local
`upstream/pi32v2-isa/isa/pi32v2.toml`; its hardware provenance is preserved
verbatim. The module itself does not test hardware atomicity, cache ordering,
interrupt delivery, inter-core fairness or physical reset behavior.

## Portable contract and incomplete paths

The public API is `hyperrig_storage_fault_execute(entry, arguments, result,
cpu, caller_return_address, io)`. Its byte maps preserve native address
relationships and public aliases, including unaligned host backing. Maps must
be pure and stable. Code remains immutable. Inputs, outputs, CPU and IO
bookkeeping remain disjoint from mapped firmware state and cannot be mutated
by callbacks. All twelve input words are copied before any observation.

Callbacks receive a synchronous public-only borrowed view. They cannot retain
it, reenter, map MMIO as a pointer or access reserved private addresses
`0x30000000..0x30001040`. The updater's private codec buffer is accessible only
to its real internal codec calls during its lifetime. Original private tokens
cannot be supplied as public arguments. Raw CNUM-derived nesting addresses
must resolve to ordinary RAM, including wrapped arithmetic; mappings into a
private frame or MMIO stop at the reached access.

Status zero publishes the scalar result, or a normalized void zero, and zero
in the second result word. Status one observes the fatal loop without
publishing either result word. Portable errors preserve the first fault and
earlier public memory/CPU effects: `-200` invalid API, `-201` missing/wrapping
map or pointer mapping of MMIO, `-202` forbidden private access, `-203` finite
work/event allowance. The original did not return these errors. Private
temporary registers/stack are not exposed as a resumable CPU context.

Event allowances are shared across the recovered caller and unchanged IRQ
helpers and are admitted before the next observation effect. Matched event
limits and mapping failures are compared as explicit prefixes. The generic
work allowance bounds entry, loop, map and event operations, with local IRQ
helper ceilings; it is not a native instruction count, cycle count or claim
that arbitrary work stops match native prefixes.

## Reproduction and evidence

Run from the repository root with WSL Ubuntu and the existing compiler:

```text
python -B tools/build_storage_fault.py --output build/reverse-storage-fault-01 --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder requires a fresh ignored output directory. It snapshots every
source before compilation, builds the host library and pi32v2 objects, runs
focused independent assertions, compares the full original instruction
closure, then replays every original fixture under ASan/UBSan with exact-sized
maps. Its manifest binds all generated files. Source provenance includes the
dynamic ISA modules, TOML records, recursively included C headers, input
manifest, memory layout and preserved license. It does not rely on an earlier
ignored verification report as a build input.

Pinned input hashes:

| Input | SHA-256 |
| --- | --- |
| Alpha11 M5.71 packed application | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Decoded application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 packed application | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

The MINI check requires the complete packed-image digest and identical bytes
for all seventeen complete bodies, the incoming four-byte call and the
four-byte auxiliary lock witness. Runtime fixture records are supplied data,
not user/device dumps. Generated outputs remain outside Git.

## Frozen result

`build/reverse-storage-fault-01` passed the host and pi32v2 builds, all 25 focused
tests and 1,744 C/original comparisons. The corpus executed 130,056 original
instructions, covering all 315 new and all 332 loaded instruction addresses.
Every new body and all 24 internal direct-call sites were reached. No instruction
gap remains in this bounded corpus.

The comparisons include 279 mapping/event-fault observations and 54 successful
fatal-loop observations, with no native return asserted for either category.
Twenty-seven C API/work guard checks passed separately. All 1,744 original
fixtures passed ASan/UBSan replay with exact-sized allocations; twelve additional
sanitizer API guards passed.

| Frozen artifact | SHA-256 |
| --- | --- |
| `verification.json` | `c46a56e99c8f0b003f58984fcd47466181f22b73bb1b28180128f7c2b145adfb` |
| `build-manifest.json` | `c2a4684c16479ce362b1308259ca69afd726dc50fe28e4cb916040f1eda27022` |

All 81 recorded source hashes and 14 artifact hashes were read back after the
build. The seven reused pi32v2 object files are byte-identical to the frozen
storage-coordination01 outputs. The eight maintained module files passed a
scoped scan for local absolute paths and credential patterns. These checks
establish offline reproducibility and the stated domains, not hardware behavior.
