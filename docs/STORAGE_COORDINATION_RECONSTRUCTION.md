# Storage coordination reconstruction

This module reconstructs nine complete Alpha11 M5.71 coordination bodies as
maintainable C and compares them with independently decoded original
instructions. It adds 578 code bytes and 178 instructions, and executes the
previously recovered 20-byte, six-instruction rate helper as an actual dependency.
There are no new immutable data exclusions.

This is offline reconstruction. It does not access a pedal, flash device, USB
interface, or operating-system interrupt controller. CPU observations and
platform callbacks do not establish atomicity, IRQ delivery, scheduling,
inter-core ordering, physical timing, transfer success, or storage durability.

The reconstructed files preserve the required notice for Manuel Aguirre's code.
See [the third-party license](../third_party/ultrarig/LICENSE.md). These are
reconstructions of the pinned binary, not recovered original source.

## Complete functions and ABI

All addresses and end bounds are original CPU addresses; ends are exclusive.
Only `ready_threshold` has a scalar return. The C API publishes zero for void
functions and always zero in the second result word.

| Function | Complete range | Native inputs | Instructions |
| --- | --- | --- | --- |
| `ready_threshold` | `020028f2..02002920` | threshold | 14 |
| `wait_ready` | `02002920..0200294e` | none | 15 |
| `poll_forward` | `02002bec..02002bf6` | none | 3 |
| `gate_core` | `02002bf6..02002d06` | enter, final wait | 81 |
| `gate` | `02002d06..02002d10` | enter; forwards final wait 1 | 4 |
| `notify` | `02002d10..02002d70` | kind, first payload word, second payload word | 29 |
| `event` | `02002d70..02002d9e` | kind, address, earlier timestamp | 15 |
| `irq_enter` | `01c00e2e..01c00e46` | none | 8 |
| `irq_leave` | `01c00e46..01c00e62` | none | 9 |
| Reused `rate` | `02002bd8..02002bec` | none; reads global calibration | 6 |

The API is `hyperrig_storage_coordination_execute(entry, arguments[12],
result[2], cpu, io)`. It takes pure borrowed byte maps, platform callbacks,
CPU-observation callbacks and finite work/service/event budgets. Incoming words
are copied before callbacks. All native public address relationships and aliases
are retained, including byte-aligned host backing and wrapped uint32 address
arithmetic. Each individual mapped access must remain within the address space.
CPU state, IO, arguments, results and callback bookkeeping are disjoint from
mapped memory and cannot be mutated through callbacks. Original code and tables
are immutable. The original private stack `30000000..30001040` is never exposed
through a borrowed view; callbacks are synchronous, cannot reenter, and cannot
retain a borrowed view or pointer.

## State and ordering

The public state base is `01c26890`; globals begin at `01c1f180`. The notification
ring is 128 records of 16 bytes at `01c2a0d0`. Its sequence word is state+1196;
the lock is the byte at state+55. The notifier caches global+24 before entering
the interrupt section, multiplies that cached timestamp by ten with uint32
wrap, and writes a halfword kind and two payload words. Record bytes +6/+7 are
preserved. The incremented sequence selects the record using its low seven bits.

Gate depth at state+37 is a raw byte: 255 increments to zero while taking the
original nested-entry return. A release at depth zero is a no-op. The outer gate
caches state+336 at +664. Its release checks mode, activity and global flags,
counts the change at +668, then observes the original counter and clock loops.
The desired and acknowledged bytes at +34/+36 are reloaded at the original
points. All native loops and arithmetic are retained: the four-yield fallback,
30-attempt ready wait, wrapped rate multipliers and unsigned elapsed subtraction.
Callback changes to later reads remain visible.

The ready predicate first wraps `(current-start)*1331` to uint32, divides by
1000, and compares with the threshold. The event writer uses the actual rate
helper followed by division by 1000; a zero divisor produces zero according to
the local pinned integer-division ISA evidence. This includes calibration values
whose earlier multiplication wraps to zero. The event kind contributes its low
byte to the high byte of the first payload word, whose lower 24 bits come from
the supplied address. These arithmetic units alone do not establish a physical
sample rate or clock period.

The nesting-word address is `01c1fc54 + (cnum << 2)` with native uint32 wrap.
The API imposes no artificial core-number ceiling; the resulting word must map.
Entry disables bit 9 of ICFG, reads CNUM, increments the word and observes the
barrier. Leave decrements the word and only enables bit 9 if the result is zero.
An initially zero word underflows; it does not enable interrupts.

The initialized RAM image has two zero words at `01c1fc54..01c1fc5c`, SHA-256
`af5570f5a1810b7af78caf4bc70a660f0df51e42baf91d4de5b2328de0e83dfc`.
This is auxiliary initial-state evidence. Those words precede the BSS clear at
`01c2030c`, remain mutable runtime state, and are not initialized by this API.
They add no immutable-data exclusion and are not evidence that startup ran.

## CPU observations and primary ISA evidence

The model pins canonical JSON hashes of five exact local ISA records, and checks
their decoded instruction text against the original instruction bytes. Records,
hashes and their preserved upstream notes are included in the verification
report. The source manifest includes the local ISA TOML records, semantics Python
files and dynamically loaded decoder dependencies.

| Site | Observation | Exact modeled effect |
| --- | --- | --- |
| `01c00e2e` | CLI, operation 5 | clear ICFG bit 9; preserve all other bits |
| `01c00e30` | CNUM, operation 7 | read the supplied retained CPU context word |
| `01c00e5e` | STI, operation 6 | set ICFG bit 9; preserve all other bits |
| `02002d30` | TESTSET, operation 8 | read one byte, write FF, set N/Z/C/V from the old low nibble |
| `02002d32` | original conditional branch | repeat while old bit 2 is set |

CLI/STI/CNUM events use address zero, width four and the resulting/read word.
TESTSET exposes its actual byte address, width one and the old byte value.
Barriers use operation 3 with zero address, width and value. Event callbacks run
after the instruction effect and may mutate public RAM; their uint64 return is
ignored. An admitted TESTSET retains its old-byte branch decision even if its
callback subsequently clears the lock. The next attempt sees the callback's
change. CPU state cannot be changed by callbacks.

The local TESTSET record reports byte and flag behavior but explicitly leaves
atomicity untested. Local CNUM probe evidence does not enumerate physical core
IDs. Local CLI/STI notes describe hardware observations from prior upstream
work; this module preserves those records and performs no new hardware test.

## Remaining platform boundaries

Every direct service target and argument count is authenticated by its original
call site. No indirect service site exists in this closure.

| Target | Argument count | Original sites |
| --- | --- | --- |
| Clock `01c04862` | 0 | `02002c2e`, `02002c3c`, `02002cd4`, `02002ce6`, `02002d78` |
| Yield `0203feb8` | 1 | `02002940`, `02002c68`, `02002c7c` |
| Scheduler polling `0203ea6e` | 0 | `02002bee` |

The rate helper executes real original instructions in the model and calls the
unchanged recovered C helper in the portable implementation. Clock/yield/poll
responses and public-memory callback changes are explicit test inputs, not
reconstructed scheduler execution.

## Guards and verification scope

Portable status -200 denotes invalid API/entry, -201 missing or wrapping maps,
-202 forbidden private-stack access, and -203 finite work/service/event budgets.
Guards preserve prior public RAM and CPU effects and leave result words untouched.
They are not original return codes. Event/service budgets stop before the next
CPU observation or external call and are compared as exact original prefixes.
A generic portable work budget has a different granularity from decoded
instructions, so its stopping location is not claimed as an original prefix.

The corpus compares complete memory, retained CPU state, native results, callback
argument order, and CPU/platform event order. Before/after memory-plus-CPU hashes
at every callback detect ordering differences hidden by equal final memory.
Cases include all lock low nibbles, FF/74/80 lock bytes, a held-lock stop before
TESTSET, nested/underflowed/wrapped counters, counter aliases into notification
records and state, first/last uint32 mapped words, timestamp/sequence wrap,
byte-aligned host backing, callback changes to the clock and gate bytes, ignored
CPU-event return values, zero and overflowing calibration, carried calls, and
retained effects on finite observation prefixes.

The exact-allocation C replay consumes original-generated fixtures under ASan
and UBSan, including callback mutations and guarded prefixes. API-only tests
separately reject missing objects, absent or wrapping maps, private views,
immutable code addresses, and exhausted budgets. They do not expand the claimed
native execution domain.

This standalone module does not yet join storage preparation or storage-control
private-buffer leases. That integration requires a separate direct-call-site
adapter with restricted private-buffer lifetimes and an original-instruction
comparison. Existing drivers, journal code, firmware images and reports remain
unchanged.

## Reproduction and provenance

Run from the repository root:

```powershell
python -B tools/build_storage_coordination.py --output build/reverse-storage-coordination-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder requires a fresh directory under ignored `build/`. It captures the
complete source set before the first compiler invocation, builds a host shared
library and pi32v2 objects, runs focused tests and the original-instruction
comparison, replays the exact-allocation sanitizer fixtures, and then binds every
artifact in a manifest. The source set includes recursive C headers, loaded
Python modules, dynamic ISA semantics, TOML records, input manifests and the
required license. The report is independent of earlier ignored verification
reports; reused sources are bound directly.

Pinned input SHA-256 values:

| Input | SHA-256 |
| --- | --- |
| Original packed Alpha11 M5.71 application | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Decoded original application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 application | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

The MINI binding checks all ten complete bodies and the eight-byte auxiliary
initial-state witness against the original, after verifying its whole-image hash.
No reconstructed target object is a flashable firmware image.

Original complete-body SHA-256 values:

| Body | SHA-256 |
| --- | --- |
| `ready_threshold` | `42e136cac4ce29491d33f1f93353d09603d370875dbe4abec245f430d0d08df1` |
| `wait_ready` | `f9384558222c4999f25fda7b5e9e9395773ac47b5d4bfda0fb8533c93358f54d` |
| `poll_forward` | `43eba7126ff82c5a344f66284de2b4e1c44df2a93149f324c7c2b9a96c8a0f26` |
| `gate_core` | `d2d9c2130934a813e4d621e8722dd234f494b3802497ab79033bc54d3e76f4b6` |
| `gate` | `a5fb19f0b93a9c5633cedc7dccdf7a4546ce7c2dfd9232bb9bfabf54e445c295` |
| `notify` | `f07024bd57ac39b9b91f3eb4af67bce863b363f2a2a71122b899c5824944a2ad` |
| `event` | `19e4f934df55dafdce7ab56258906c468efb70d70d83a331f9d20fc8ac244c88` |
| `irq_enter` | `461b030fe1a736706657008d1d7f249d93142c5f042d10eefa68e52a7de014de` |
| `irq_leave` | `6aa0e655a5f772c3aa119e95b506154f2496d5a6c590755e8ad213bef277fa6b` |
| `rate` | `30c0c12cfb3add81653bb701a656a0321550a10607d56f7731eb96a41971ea7f` |

## Frozen verification result

The completed run is `build/reverse-storage-coordination-01`:

| Check | Result |
| --- | --- |
| Original-instruction comparisons | 442 passed |
| Original executed steps | 15,682 |
| New instruction coverage | 178 / 178 |
| Combined coverage including the rate helper | 184 / 184 |
| Focused native/evidence tests | 24 passed |
| API-only checks | 51 passed |
| ASan/UBSan original-fixture replays | 442 passed, three exact-allocation maps per case |
| Additional sanitizer guard checks | 13 passed |
| pi32v2 objects | Seven built; six reused objects exactly match storage-preparation02 |
| Final source and artifact read-back | All 78 source hashes and 13 artifact hashes matched |

Verification report SHA-256:
`8cedc6d10c791856aee0999efce8860ee8e4c79f84ec39a1be40624056eed8cb`.

Build-manifest SHA-256:
`a0a26deca273efc47f5e1a036e35391ab3e04f1cceab83279bc7a0e47d73b14f`.

No decoded instruction gap remains in this closure. This describes the exercised
instruction corpus and explicit callback model; it is not a measure of complete
firmware recovery or proof of hardware interrupt behavior. The full driver,
coordination and preparation integration remains a separate milestone.
