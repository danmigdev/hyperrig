# Storage platform reconstruction

This module reconstructs nine complete Alpha11 M5.71 platform bodies used by
the storage path: interrupt registration, two peer-control operations, critical
entry and leave, the separate peer interrupt, and a counter read. The new bodies
contain 580 bytes and 200 instructions. The previously recovered IRQ nesting
helpers execute unchanged as dependencies, adding 52 bytes and 17 instructions.
There are no new immutable data exclusions. This standalone module does not
replace any service boundary in the frozen storage-runtime reconstruction.

This is offline instruction and portable-C verification. No device, flash,
interrupt controller or audio hardware is accessed. Explicit MMIO responses,
lock completion, peer acknowledgment and callback completion fixtures do not
establish physical scheduling, atomicity, fairness, timing, inter-core ordering
or storage durability.

The reconstructed files retain Manuel Aguirre's required notice and
[third-party license](../third_party/ultrarig/LICENSE.md). They are reconstructed
source, not the original source code.

## Complete bodies and interfaces

Addresses are original CPU addresses and all ends are exclusive.

| Entry | Complete range | Native inputs | Instructions |
| --- | --- | --- | --- |
| `gate_disable` | `02000558..02000564` | none | 4 |
| `gate_enable` | `02000564..02000570` | none | 4 |
| `register` | `020005ac..02000604` | number, priority, handler, core selector | 30 |
| `peer_stop` | `01c010e4..01c01108` | zero selects first peer register; nonzero selects second | 12 |
| `enter` | `01c01108..01c011c2` | callback token, argument | 67 |
| `peer_resume` | `01c011c2..01c011da` | same selector as `peer_stop` | 6 |
| `leave` | `01c011da..01c01234` | none | 31 |
| `interrupt` | `01c041dc..01c04256` | separate supplied CPU activation | 43 |
| `clock` | `01c04862..01c0486c` | none | 3 |
| Reused `irq_enter` | `01c00e2e..01c00e46` | none | 8 |
| Reused `irq_leave` | `01c00e46..01c00e62` | none | 9 |

The ordinary API is `hyperrig_storage_platform_execute(entry, arguments[12],
result[2], cpu, io)`. It accepts the eight ordinary new entries. Only `clock`
publishes a scalar result; unspecified native return words are normalized to
zero. Incoming argument words are copied before any callback.

The separate API `hyperrig_storage_platform_interrupt(input, output, cpu, io)`
executes the complete interrupt body. Its input supplies all 16 general
registers, PSR, RETS and RETI. The retained coordination CPU object supplies CNUM
and ICFG independently. No vector delivery or hardware activation transition is
invented. Original instructions execute the actual 32-byte private save frame;
the C implementation preserves equivalent saved context and exposes the same
frame observations. Output is published only after RTI completes. General
registers are restored, PSR retains bits 0..3, and RETS/RETI retain bits 1..26.
An incomplete interrupt does not publish partial private GPR or PSR temporaries.

Both APIs use stable, pure borrowed byte maps. Original public address
relationships and byte aliases are retained; each individual access must map
without crossing uint32 address wrap. Address calculations, counters, priorities,
core selectors and callback tokens retain their full uint32 behavior. There is
no fixture-sized core or vector-number restriction. The original private stack
`30000000..30001040` is unavailable to callbacks and ordinary mapped objects.
Original code and tables are immutable. CPU state, input, output, IO and callback
bookkeeping are disjoint from mapped memory. Callbacks may synchronously mutate
public RAM, but cannot change CPU/API storage, reenter, retain a borrowed view,
or map MMIO as ordinary pointers.

## Shared state and ordering

| Address | Role |
| --- | --- |
| `01c1fc40` | callback token |
| `01c1fc44` | acknowledgment byte |
| `01c1fc48` | callback argument |
| `01c1fc4c + (CNUM << 2)` | raw lock-depth word, uint32 address arithmetic |
| `01c1fc54 + (CNUM << 2)` | unchanged IRQ-depth word |
| `01c3748d` | mode byte |
| `01c7fe00 + (number << 2)` | supplied interrupt vector storage |

The 20 bytes at `01c1fc40..01c1fc54` are zero in the initialized application
image, SHA-256
`de47c9b27eb8d300dbb5f2c353e632c393262cf06340c4fa7f1b40c4cbd36f90`.
They remain mutable state and are not initialized by the API or classified as
immutable tables. The mode byte is in BSS, while the vector area is outside the
initialized application image. Fixtures supply both explicitly.

Interrupt registration writes a nonzero handler to its vector before masking
ICFG bit 8. It computes the priority nibble using native shifts and masks. An
exact selector value 255 obtains CNUM; otherwise the selector is retained. Its
low byte chooses the first or second priority bank. The original priority word
is read, its nibble replaced, and ICFG bit 8 is enabled unconditionally afterward.
All other ICFG bits are preserved. A missing vector can therefore fail before
the first CPU observation. Raw indices whose arithmetic lands in ordinary
mapped RAM remain ordinary accesses rather than being restricted to a nominal
controller size.

In nonzero mode, entry invokes the unchanged IRQ helper, waits while the
acknowledgment byte equals exactly 1, clears it, and publishes callback and
argument in the original order. It raises the peer interrupt, waits for the
cache bit and acknowledgment, then reloads the callback token. A zero token
selects the peer-stop path. A raw acknowledgment value 2 skips the initial
equality wait. In zero mode, entry waits for the cache bit first, invokes the IRQ
helper, increments the raw lock depth, and observes LOCKSET only when the old
depth was zero. It publishes the callback and argument before conditionally
raising the peer interrupt.

Leave follows the original mode-specific order. In nonzero mode it clears the
acknowledgment before checking the current callback token and possibly resuming
the peer. In zero mode it clears the token, decrements raw lock depth and
observes LOCKCLR only when the result is zero. Zero underflows; it does not act
like a balanced release. Both paths invoke the unchanged IRQ leave helper.
Its counter address must map ordinary RAM, as required by the frozen helper.
Raw CNUM values that select the interrupt's populated private save frame are
rejected at the reached counter access. The native model applies that domain
guard to ordinary loads/stores while allowing the actual IRQ PUSH/POP operations
to save and restore private bytes.

The interrupt acknowledges the controller, enters the IRQ section and waits
for the cache bit. Nonzero mode sets acknowledgment before its barriers and
callback, then waits for the byte to become zero. Zero mode invokes the callback
without that handshake. Later loads remain visible to synchronous callback
mutations. The original loops are retained. Their completion in a fixture is
explicit input, not proof that hardware would make progress.

## Calls, CPU observations and MMIO

The decoder authenticates all nine direct call sites:

| Site | Target |
| --- | --- |
| `020005d0` | `02000558` |
| `02000600` | `02000564` |
| `01c0112e`, `01c01188`, `01c041f4` | `01c00e2e` |
| `01c0117c` | `01c010e4` |
| `01c01208` | `01c011c2` |
| `01c0122c`, `01c0424a` | `01c00e46` |

No direct platform service remains in this closure. The two indirect sites
`01c04230` and `01c04248` always forward one word to an external callback,
including when the token equals any loaded original entry. Target equality
never converts an indirect callback into an internal function call. The native
callback ABI preserves r4..r15; r0..r3 are caller-saved. Return values are ignored.

The model pins canonical hashes of 13 exact primary ISA records, checks their
decoded instructions, and includes the complete records in its report. They
cover ICFG read/write, CNUM, LOCKSET/LOCKCLR, special and general push/pop, RTI,
CLI/STI, and the encoded conditional at `01c011c2`. That conditional has an
actual else instruction and cannot be treated as two unconditional address
loads. Source provenance includes the local ISA TOML, semantics Python modules
and dynamically loaded decoder code.

| Operation | Observation and effect |
| --- | --- |
| MMIO READ/WRITE, 1/2 | exact address, width and written value; only READ uses the supplied return |
| BARRIER, 3 | zero address, width and value; synchronous memory observation only |
| CLI/STI, 5/6 | unchanged helper clears/sets ICFG bit 9, preserving other bits |
| CNUM, 7 | supplied raw CPU word; address 0, width 4 |
| ICFG READ/WRITE, 9/10 | address 0, width 4, read/new word; WRITE follows admission |
| LOCKSET/LOCKCLR, 11/12 | zero address, width and value; admitted completion is explicit |
| IRQ PUSH/POP, 13/14 | exact private frame address and size; value is the decoded register mask |
| RTI, 15 | restored RETI address, width 0, value 0 |

The special push at `01c041dc` stores RETI, RETS and PSR in the 12 bytes at
`30000ff4..30001000`, then clears live PSR flags. Its mask is `0x10029`. The next
push stores r0..r4 in the 20 bytes at `30000fe0..30000ff4`, with mask 31. Pops
restore these in reverse order, then RTI ends this independently supplied
interrupt context. Ordinary nested function frames remain the existing model's
ABI abstraction; the interrupt's special/general save frame is actual private
byte memory. A callback cannot access it.

The exact bus windows are `00010704..00010708`, `01eee000..01eee00c`,
`01eef100..01eef180`, `01eef1a0..01eef1a8` and `01eef300..01eef380`.
Partial accesses crossing a window boundary are rejected. Other calculated
addresses must be ordinary public mappings. The counter read is a raw MMIO
word; no physical time unit is assigned to it.

## Failure contracts and comparison scope

Portable status -200 means invalid API/entry; -201 means missing/wrapping maps
or forbidden MMIO pointer access; -202 means private-domain access; -203 means
a finite work, service or event allowance was exhausted. The first fault is
retained. Earlier public memory and ICFG effects remain, while scalar results
and interrupt context stay untouched. These are portable guard statuses, not
original return codes or resumable native states.

External service/event allowances are admitted before the next observed effect
and shared across the unchanged IRQ helper. Those stop points are compared with
original instruction prefixes. Portable work allowance counts source operations;
the child retains a local ceiling and its mapped accesses also consume the
outer allowance. It is not a shared native instruction counter or a claim of
arbitrary matched instruction-prefix stopping.

The corpus compares full supplied memory, retained CPU words, restored interrupt
context, ordered callbacks and CPU/MMIO events, plus before/after memory and CPU
hashes at every event. It covers cold and carried calls, both mode handshakes,
raw depths and wrapped CNUM/index calculations, entry/leave underflow, priority
and vector aliases, callback changes to later loads, callbacks whose tokens
collide with all loaded entries, and exact event/service guard prefixes.
Negative checks include missing neighbors, private frame access, MMIO pointer
access, first-fault retention and output suppression. Portable work-budget cases
are reported separately from matched instruction prefixes.

## Provenance and reproducibility

The original packed application is
`artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin`, SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The decoded `analysis/firmware/m571_g_app/app.bin` is SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
RAM bytes are read through the preserved original memory layout.

The reviewed MINI v4 image is
`build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin`,
SHA-256 `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Verification checks its whole-image identity and all 11 complete regions,
217 instruction windows and 20 mutable auxiliary bytes against the original.
The images and previous reports remain unchanged.

Run the builder with a fresh output directory under `build/`:

```text
python tools/build_storage_platform.py --output build/reverse-storage-platform-02 --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder captures all source inputs before compilation, builds the host
library and pi32v2 objects, runs focused native tests, regenerates original
fixtures, and replays every fixture under ASan/UBSan using exact allocation
bounds. It requires the final source set and hashes to equal the initial
capture. Recursive C headers, dynamically imported Python, the local ISA records
and semantics, input manifest, layout and license are included. Generated
reports, fixtures and binaries remain ignored under `build/`.

## Frozen validation result

The final output is `build/reverse-storage-platform-02`:

| Check | Result |
| --- | --- |
| C versus decoded original comparisons | 641 |
| Original instruction steps | 21,883 |
| New instruction coverage | 200 / 200 |
| Total loaded instruction coverage | 217 / 217 |
| Reached direct / indirect sites | 9 / 2, all covered |
| Matched guarded observations | 132, included in the 641 comparisons |
| Focused native tests | 21 passed |
| Separate C API and work guards | 32 passed |
| Exact-allocation ASan/UBSan fixture replays | 641 passed, six separately bounded maps each |
| Additional sanitizer API guards | 20 passed |
| Host and pi32v2 compilation | passed; eight target objects |
| Read-back source / artifact bindings | 81 / 14, all matched |
| Reused target objects | seven byte-identical to coordination01 |

The final verification report SHA-256 is
`82bb5477eff5ce088e14ab9d13463fc11033a34725f011700b4c56264c33136b`.
The build manifest SHA-256 is
`c20b96bf5512cdddc74be7ebf88351609ebb9188159c6a149748aee6403a7087`.
Both records bind the exact final evidence; no instructions remain unvisited.
This is corpus coverage, not proof of every possible state or physical behavior.

Candidate01 is preserved. Independent review found that its native model could
resolve a raw IRQ-counter address into an already populated private save frame,
although C and the public contract rejected that domain. Candidate02 adds the
reached native domain stop, 18 comparison witnesses and one focused frame test.
The reconstructed C behavior is unchanged. Independent source review also
checked all nine complete body flows, raw arithmetic and the encoded else path.
The scoped maintained-file audit found no local user paths or credential
literals. No frozen dependency, original image or earlier report was modified.
