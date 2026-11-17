# Effect processing callers

This milestone reconstructs the complete original dispatcher, individual effect
wrapper and grouped oversampling wrapper. Their real callers now execute through
the previously recovered stage router and audio task. The C implements their
control flow and caller arithmetic directly; the comparison model executes the
independently decoded original instructions.

The original numerical leaves reached by several effect types are still explicit
services. A caller passing its verification corpus does not recover those leaves,
prove hardware timing, or establish that audio on a pedal is correct. No device
was accessed and no firmware image was changed.

## Original bodies

| Body | Start | Exclusive end |
| --- | --- | --- |
| Capture-object timing probe | `0x01c0588e` | `0x01c058bc` |
| Base effect cost | `0x01c058bc` | `0x01c05c08` |
| Six-argument extra cost | `0x01c05c08` | `0x01c05d02` |
| Timing warning publication | `0x01c0735e` | `0x01c07400` |
| Peak-limited transition | `0x01c07400` | `0x01c07588` |
| Quarter-block parameter update | `0x01c07588` | `0x01c0767e` |
| Q16 product | `0x01c08b34` | `0x01c08b3e` |
| Fractional exponential | `0x01c08c76` | `0x01c08c98` |
| Complete effect dispatcher | `0x01c0deb6` | `0x01c0f678` |
| Complete individual wrapper | `0x01c0f678` | `0x01c10446` |
| Complete grouped wrapper | `0x01c10446` | `0x01c10818` |
| Active IR predicate | `0x01c11f56` | `0x01c11f66` |
| IR accelerator predicate | `0x01c12446` | `0x01c1245c` |
| Signed peak over 16 samples | `0x01c19bee` | `0x01c19c98` |
| Saturating gain over 16 samples | `0x01c19c98` | `0x01c19d36` |
| Wrapping gain over 16 samples | `0x01c19ede` | `0x01c19efa` |

The complete dispatcher preserves all 40 type-selector outcomes, including no-op
types. It recovers stereo state caching, sequential history copies, Q28 section
selection, gain interpolation, the inline envelope and modulation arithmetic,
dual-descriptor construction and mixing, and calls to effect-specific leaves.
The individual wrapper retains its sentinels, tail counters, skip/retry timing,
four-step fades, stereo borrowing, quarter-block automation and cost publication.
The grouped wrapper selects and transfers the first active effect's histories,
executes real up/down resampling, and updates each effect's measured overhead.

## Actual numerical dependencies

The new adapter borrows the unchanged Q28 filters, variable-length saturating
gain, stage mixer, IR software convolution and six effect resampling bodies.
The guarded reset at `0x01c11f76..0x01c11faa` comes from
[effect enable reconstruction](EFFECT_ENABLE_RECONSTRUCTION.md); it is not
implemented again here. Every recovered dependency called by the corpus executes
its original instructions and its C implementation.

The constructed-IR corpus first compares the original and C constructors for
1, 129 and 513 coefficients. It carries their matching object bytes at original
token `0x33000000` into the shared-memory fixture. The fixture publishes that token
at `effect+288`, sets `effect+292` and the wet/dry words, and explicitly chooses
`object+548` for software or accelerator sequencing. Those publications are test
fixture writes. This corpus does not execute the enclosing installation/enable
caller during that handoff. Actual stage, individual, dispatcher and IR runtime
calls then operate on the carried object across multiple blocks.

Separate retry witnesses execute the original guarded IR reset on one- and
32-partition histories and carry the retry counter into later calls. Audio-task
observations also reach the dual descriptor boundary through the real stage and
effect callers; the descriptor is read through its temporary borrowed mapping.

Accelerator operations remain a hardware boundary. The adapter synchronizes the
original descriptor and runtime globals before and after each read, write or
sync callback. Synthetic operation tokens `0xffff0000`, `0xffff0001` and
`0xffff0002` identify those adapter operations; they are not original function
addresses. Scripted register responses exercise software sequencing and mutable
data, never an emulated claim of physical accelerator output.

## External ABI and temporary descriptors

The new callback accepts up to twelve argument words. The first four correspond
to `r0..r3`; later words are incoming stack arguments. A borrowed mapping is valid
only during that callback and includes initialized temporary descriptors passed
by the original caller. Services may change documented mapped state and explicit
descriptor outputs. They cannot retain that mapping, reenter processing, or
inspect unrelated private stack words.

| Unrecovered entry | Argument words | Contract at this boundary |
| --- | ---: | --- |
| `0x01c04862` | 0 | Clock word |
| `0x01c06b2c` | 1 | Effect integrity probe |
| `0x01c06b82` | 1 | Corrupt-slot handling |
| `0x01c06f84`, `0x01c0767e`, `0x01c089e8`, `0x01c0ddae` | 3 | Effect, sample token, count |
| `0x01c08f80`, `0x01c0a7aa`, `0x01c0b3b0` | 4 | Effect, samples, count, active/auxiliary word |
| `0x01c0b4b8` | 3 | Effect, samples, count; caller saves/restores selected state |
| `0x01c08b3e` | 9 | Samples, count, section state, first section count, two history tokens, second section count, masks |
| `0x01c0b524` | 5 | Samples, count, dry gain, post-filter word, mutable history token |
| `0x01c0b5d6`, `0x01c0bd8c` | 1 | Effect transition updates |
| `0x01c0ba14` | 8 | Two sample tokens, count, gain, gain delta, two mixing gains, mode |
| `0x01c0bbce` | 4 | Width, mode, two output-word tokens |
| `0x01c18f90` | 1 | Borrowed 68-byte processing descriptor |
| `0x01c1958e`, `0x01c19a8a`, `0x01c1ee40` | 3 | Samples, count, state token |

The high-arity boundaries were checked at their callees: `0x01c08b3e` saves 52
bytes and reserves 68, then reads incoming words at stack offsets 120 through
136; `0x01c0ba14` saves 52 and reserves 44, then reads offsets 96 through 108;
`0x01c0b524` saves 48 and reads its fifth argument at offset 48. The two output
pointers of `0x01c0bbce` are incoming `r2` and `r3`, not omitted scratch values.
The six-argument cost estimator is recovered internally, including both stack
words, and is also available to the parameter module.

Original transient stack tokens are reproduced for standalone, grouped, stage
and audio-task calls. This lets the comparison check descriptor argument identity
as well as callback order and shared-state snapshots. The comparison additionally
hashes every initialized byte of the 68-byte dual descriptor and the borrowed
post-filter history word before their services run. The unresolved leaf scripts
are declared test services, not recovered effect arithmetic.

## Bounded borrowed-memory contract

The shared map preserves original address identity. It is pure and consistent,
and distinct address spans have distinct host backing. API structures, returned
results, IO objects and persistent task controls are disjoint from mapped bytes.
Concurrent mutation and callback reentry are outside the domain. A guard failure
can leave earlier original writes in place and is not a resumable observation.

Slots are `0..15`; types used by cost/capability indexing are `0..39`. Direct
dispatcher and individual sample counts are bounded to 512. Group lists contain
at most 16 valid slots and their first byte must be readable even when the list
is empty. A grouped call with actual resampling requires a positive count and
disjoint native history/input/output spans; the shared fixed buffers support the
normal counts up to 128. Existing stage and audio-task bounds remain unchanged.

Sixteen-sample peak/gain operations retain their full native 16-word access,
including a final partial logical block. Callers must provide that rounded-up
sample backing. Fixed history and scratch buffers, effect state, stereo caches,
automation records and borrowed descriptors must cover every original access.
Automation records have at most 40 entries with parameter/reference indices
below 48, and quarters are `0..3`.

Q28 state and ramp sample tokens must be aligned to four bytes; the adapter checks
those tokens before borrowing typed storage, and then checks the returned host
pointer alignment. Host backing used as `int32_t` or Q28 state has compatible
types and is little-endian. Q28 state and its sample window are disjoint. The IR
object keeps the coherent constructor layout and the inherited 1..32-partition
domain. Its structural fields, callback view and tables stay fixed during MMIO
callbacks; allowed numerical buffers and runtime globals may change.

The integer reconstruction retains modulo-32/64 arithmetic, signed division
toward zero, native zero-divisor quotient zero, packet operand timing and the
individual wrapping/saturating operations. It does not substitute host floating
point for the pinned binary32 operations. The new model overrides an older
dependency's zero-divisor restriction using the pinned ISA division evidence;
the older verified model and report remain unchanged.

## Instruction and data provenance

Four embedded tables are excluded from instruction decoding: cost branches at
`0x01c058e2..0x01c0592a`, extra-cost branches at
`0x01c05ca2..0x01c05cc6`, dispatcher branches at
`0x01c0e0a8..0x01c0e0f6`, and individual branches at
`0x01c10204..0x01c1023e`. The extra-cost table includes a final padding byte.
State-copy layouts occupy exactly `0x0203b7b0..0x0203b7c8`.
The report binds these bytes, every loaded instruction window, and the cost,
resampling, capability and inherited numerical tables to both pinned images.
It also checks that the complete decoded input is the decompressed payload of
the pinned original image.

Verification compares complete mapped state, defined return values, ordered
service arguments and state at each service. Its sanitizer replay uses the
original comparison outputs and recorded external-service writes, including
temporary-descriptor writes and audio-task observation/resume state. It never
derives expected output from the reconstructed C. Manifests include executable
Python imports, dynamically loaded ISA semantics and TOML, recursively included
local C headers, the C sources and all generated build artifacts. Previous
ignored reports are not prerequisites for source or input discovery.

Independent read-only review covered the individual/grouped control flow,
callback-sensitive reloads, Q16 fades and native packet ordering. The reviewer
identified the typed-storage alignment gap; explicit token guards resolve it.
The dispatcher review separately checked stereo recursion, complete type 38
inline arithmetic, and the type 25 descriptor transition and final mix loop,
including the asymmetrical saturation bounds and per-four-sample gain steps.
No remaining semantic mismatch was found within the declared input domain.
The remaining effect numerical leaves and hardware services are separate future
reverse-engineering work.

## Frozen validation

The final evidence is in ignored directory `build/reverse-effect-processing-02`.
It passes 4,664 original/C comparisons over 5,283,702 original instruction steps,
14 focused tests, 18 C API/domain guard checks, and 2,272 ASan/UBSan replay cases.
The guards include both misaligned original tokens and misaligned host backing.

The executed coverage is 4,218 of 4,223 new instructions across 16 complete
bodies. The dispatcher executes 1,991 of 1,992, the individual wrapper 1,141 of
1,142, and the grouped wrapper all 322. The five gaps are explained below.
Across all loaded current and inherited code, this run executes 8,808 of 17,064
instructions. It includes 30 audio-task dispatcher entries, two audio-task dual
descriptor service entries, three real constructor comparisons and 48 carried
IR stage blocks. These are scoped counts, not an overall reverse-engineering
completion percentage.

Strict host and pi32v2 builds pass. All 32 pi32v2 objects are byte-identical to
the first passing candidate; the new processing object is 29,524 bytes. The final
report binds all 17,064 loaded instruction windows and 23 static windows to the
unchanged MINI v4 image. All 139 source bindings and 38 artifact bindings were
rechecked after completion and match. Candidate 01 remains preserved separately.

| Frozen evidence | SHA-256 |
| --- | --- |
| `verification.json` | `c6998160f2863a3a80339dc45bfb9af36cb4f86d15c76f15b9b1de5b18e88cbe` |
| `build-manifest.json` | `247f15bc9431c71ac2f9caf9041fe177e22cf0cdcbe255103959bdd776778642` |

Reproduce with a fresh ignored output directory:

```text
python tools/build_effect_processing.py --output build/reverse-effect-processing-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

## Unvisited fallback instructions

Five new instructions remain unexecuted and are not counted as coverage:

- `0x01c05ce4`, `0x01c05ce6`, `0x01c05ce8`: the extra-cost range fallback is
  excluded by the declared type range and the immutable capability table.
  Types 0 through 4 have table bytes `0, 0, 15, 0, 15`, hence capability 0 or 3
  in either field; those cases exit before the type-minus-5 table branch.
  Types 5 through 39 are within that table's range.
- `0x01c0e816`: type 38 enters its outer loop with positive remaining count,
  takes at most 32 samples, and advances by 32. Its inner count cannot be zero.
- `0x01c0fcac`: the stereo setup block is entered with selected mode 1, 2 or 3.
  It reloads that saved positive mode before the nonpositive fallback, with no
  intervening service or aliased write allowed by the mapped-storage contract.

The joined corpus also leaves inherited instructions unvisited. Its report lists
those addresses separately; earlier reports' coverage is never added to this
run's execution count. Independent review confirmed all five fallback proofs
against the original capability helper, loop entry/back-edge, and saved stereo
mode reload. These proofs apply only within the documented input and mapping
domain.

Required Notice: Copyright (c) 2026 Manuel Aguirre

This reconstruction retains the upstream
[PolyForm Noncommercial 1.0.0 license](../third_party/ultrarig/LICENSE.md) and
[required notice](../third_party/ultrarig/NOTICE.md).
