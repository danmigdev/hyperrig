# Parameter resource reconstruction

This module reconstructs nineteen complete M5.71 functions that manage effect
buffers, migrate packed history, summarize effect state, change processing mode,
and select IR lengths. It adds 579 decoded instructions in 1,670 bytes of whole
function ranges. Those ranges contain 48 bytes of authenticated branch tables
and alignment padding, leaving 1,622 instruction bytes.

The reconstruction is compilable research C with an independent interpreter of
the original instructions. It is not original source, a replacement firmware
image, or evidence of a hardware or audio test. Original images and all earlier
reconstruction sources and reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre.
The original work's [PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md)
and required notices remain applicable.

## Complete functions and ABI

End addresses are exclusive. Arguments below are original unsigned 32-bit ABI
words; signed interpretation is applied only where the original instructions
require it. The public adapter accepts twelve words and reports defined scalar
results in the first result word. The second result word and original void
results are normalized to zero.

| Entry | End | Instructions | Arguments and behavior |
| --- | --- | ---: | --- |
| `0x01c05ec6` | `0x01c05ed6` | 6 | `mode`; invoke the installed mode callback if nonzero |
| `0x01c05ff2` | `0x01c05ffa` | 2 | no semantic inputs; return 56,480 bytes |
| `0x01c065e2` | `0x01c065f6` | 7 | `buffer, logical_count, index`; decode one packed sample |
| `0x01c065f6` | `0x01c067e0` | 175 | `buffer, logical_count, block, samples16`; encode one group |
| `0x01c067ea` | `0x01c06808` | 9 | `effect`; sum three stored section bytes |
| `0x01c06808` | `0x01c06846` | 21 | `effect`; derive type 36 state flags |
| `0x01c06846` | `0x01c0688c` | 27 | `effect`; derive type 37 state flags |
| `0x01c0688c` | `0x01c068b6` | 13 | `effect`; sum four stored section bytes |
| `0x01c068b6` | `0x01c068e0` | 14 | `effect`; select a stored delay-state word |
| `0x01c068e0` | `0x01c06926` | 18 | `effect`; reset selected derived fields |
| `0x0202df04` | `0x0202df38` | 19 | `bytes`; allocate with a sixteen-byte canary trailer |
| `0x0202ed7e` | `0x0202edb8` | 21 | no arguments; remove the queued effect slots |
| `0x0202edb8` | `0x0202ee3c` | 47 | `effect, capacity, out_released`; allocate/recover a delay buffer |
| `0x0202ee3c` | `0x0202eeba` | 45 | `effect, old_buffer, old_logical, new_buffer, new_logical`; migrate history |
| `0x0202eeba` | `0x0202eefa` | 23 | `effect`; allocate and publish extra state |
| `0x0202eefa` | `0x0202efe2` | 78 | `effect`; compute the native state fingerprint |
| `0x0202efe2` | `0x0202f014` | 16 | `effect, mode`; clear histories and change mode |
| `0x0202f014` | `0x0202f02e` | 8 | `effect`; obtain object/global IR state |
| `0x0202f02e` | `0x0202f07e` | 30 | `effect, mode, desired_length`; choose an effective IR length |

The migration routine's fifth word is an incoming stack argument. The native
frame saves 48 bytes and reserves 64 bytes, so its load at `0x0202ee50` reads that
word from `sp + 112`. The IR wrapper at `0x0202f072/74` similarly forwards the
original third argument on the stack while changing the third register argument
to the stored format byte. Both packets execute with their original register
snapshot in the comparison model.

Ten already reconstructed complete functions are reused, adding 166 decoded
instructions: selector `0x01c060e6`, halfword clearing `0x01c06554`, installed
clear `0x0201a9dc`, memset `0x02033412`, active state `0x01c055d2`, IR-active state
`0x01c11f56`, and the four IR size functions from `0x02029248` through
`0x0202930e`. C delegates to the unchanged support, stage, processing and IR
installation implementations. The native reference executes their actual
decoded bodies; it does not substitute their numerical or scalar results.
The global effective-length helper is adapted to borrowed control fields and
then invokes the existing pure IR limit function.

## Packed history and migration

Packed storage holds signed little-endian halfwords followed by one exponent
byte per group of sixteen samples. Decoding sign-extends a halfword and shifts
its raw word left by the exponent masked to five bits. The encoder derives its
shift from the OR of sign-adjusted magnitudes, adds the original rounding bias
with 32-bit wraparound, shifts arithmetically, and applies only the original upper
clamp of 32,767. Its exponent store updates one byte lane of a word while
preserving the other three lanes.

This is not interchangeable with host floating-point quantization or a symmetric
clamp. For example, a group of `0x7fffffff` samples selects shift sixteen; the
rounding addition wraps and produces packed halfwords `0x8000`. A group of
`0x80000000` also produces `0x8000`, for a different arithmetic reason. The
comparisons and focused tests retain these exact native results.

The encoder caches the first two samples and scans all sixteen before writing
output. After the first output word it reloads each subsequent pair, high sample
first. Consequently, partially overlapping input/output buffers can affect later
samples. The C follows this order and the corpus includes such aliases.

Migration caches the old cursor, selects encoded samples until the pending
history tail begins, and accumulates sixteen words on its private stack. Each
complete group is passed through the real encoder. An incomplete final group
is discarded; the routine still publishes the old logical count to `effect+288`.
Zero count performs that final store without accessing either sample buffer.
Counts need not be multiples of sixteen. Carried resize and overlapping-buffer
cases compare the entire resulting storage, including untouched neighbors.

## Allocation and mutable boundaries

The allocation wrapper rereads `control+52` and requests the original byte count
plus sixteen, using native unsigned wraparound. After a nonzero return it writes
four words `0xc0de5eed ^ index` after the requested span. A successful callback
therefore requires mapped storage for the requested data and this trailer.

Delay growth clears `out_released` before its first attempt. On failure, if a
release callback exists, it caches the old pointer/capacity, publishes zero in
the effect's pointer/capacity fields, releases the cached pointer, and sets the
output flag. It retries, flushes queued slots, retries again, and finally tries
to restore the old allocation. Restored storage is cleared; failed restoration
disables the same two native flags. Output-flag aliases with those fields,
callback mutations, replacement callback tokens, and all recovery outcomes are
included in comparisons. This adapter preserves the writes; it does not impose
a new heap ownership policy.

Queue flushing clears each slot's original flags before calling complete slot
removal at `0x0202eb4c`, then rereads the queue count and next slot. That removal
body remains an explicit service. Allocation/release callbacks at `control+52`
and `control+56`, mode callback `0x01c34458`, and alternate clear callbacks remain
explicit services too. They may synchronously modify mapped firmware bytes.
Allocator, release, mode and slot-removal calls each have one semantic argument;
alternate clear has two. Arity follows the original call site even if a token
equals a different loaded function. Only the installed clear target
`0x0201a9dc` at call site `0x01c0656e` executes internally.

Extra-state allocation performs its actual 56,480-byte allocation/retry/clear
sequence and publishes the pointer, halfword length and flag in native order.
The module does not reconstruct complete effect destruction, effect coefficient
construction at `0x0202cf62`, allocator internals, or scheduler behavior.

## Mapping and guard domain

The generic API borrows original-address byte storage. Mappings must be pure,
stable and preserve address relationships; original aliases within that storage
are allowed. The C does not require aligned host backing for these byte accesses.
The IO and result objects remain disjoint from mapped firmware state. Incoming
arguments are copied before callbacks, allowing callback changes to their former
mapped backing without changing saved native argument values.

Supplied/returned addresses cannot alias the original private stack reservation
`0x30000000..0x30001020`. The model owns that stack and the C uses separate local
storage; accepting such aliases would give them different meanings. Accesses
into that reservation return the new domain guard `-202`. Individual accesses
must not cross the end of the 32-bit address space. Arithmetic producing the
next address may wrap, and separate valid spans on either side are compared.

The inherited active helper retains its effect-type domain `0..39`. Accessed
sample/history spans must exist and the finite work budget must suffice. There
is no artificial multiple-of-sixteen or small-count restriction. Status `-200`
means invalid API or a missing reached callback, `-201` means missing storage,
`-202` means an unsupported domain, and `-203` means exhausted work/service
budget. These are research API guards, not recovered firmware return values.
They preserve preceding writes and do not publish a result. No concurrent
mutation, reentry, relocation, or retained callback views are supported.

## Evidence and reproducibility

The original container is pinned to SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`;
its extracted application is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
The reviewed MINI v4 container is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier authenticates these whole images and compares all 745 loaded
instruction windows and all five static windows against that MINI application.

| Static input | Exact range | SHA-256 |
| --- | --- | --- |
| Reset branches, 21 entries and one zero alignment byte | `0x01c068ee..0x01c06904` | `364714e6758d1e612d58b7417c4f2d6f083606b97788ef99aef496999f432930` |
| Upper fingerprint branches, 15 entries and one zero alignment byte | `0x0202ef12..0x0202ef22` | `8c849a46f8332905a3cefae75d7a283637b818d31c0506571934e129b064906a` |
| Lower fingerprint branches, ten entries | `0x0202ef3e..0x0202ef48` | `9df17c4d5cb6efffbb8ce9e5ddffbdd1f42f6d0058eb696717eda747beb80da7` |
| Reused parameter selectors | `0x0203b880..0x0203b8d4` | `3d558f81b50146dd3006396db32da015bd93e4df55bf01c78d52e76cdda324a4` |
| Reused capabilities | `0x0203b480..0x0203b4a8` | `ad42fb64992b7995f180484ba717298b55c46909537d0e9a01ee333cf4662362` |

The first three ranges are data, not decoded instructions or function entries.
The two padding bytes are authenticated separately by the table validation.
All valid table destinations must resolve to loaded instructions.

The model inherits pinned instruction semantics and implements only the extra
register arithmetic/address forms needed by these bodies. Parallel packets use
the old register snapshot. This remains a bounded instruction interpreter,
including the inherited REP semantics, not a complete CPU/peripheral model.
No original binary is modified or executed on a connected device.

Run a fresh build from the repository root:

```powershell
python -B tools/build_effect_parameter_resources.py `
  --output build/reverse-effect-parameter-resources-next `
  --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles the host comparison library, pi32v2 objects and an
ASan/UBSan replay executable. It includes the complete transitive C sources,
recursive headers, Python modules, dynamically loaded ISA semantics, ISA TOML
and input manifest in source hashes. It rejects changed source bytes during the
build. Reports and replay fixtures are written only to a fresh ignored build
directory; no previous generated report is an input. Final comparison reports
bind complete memory, scalar results, callback arguments, callback arities and
state at every external service boundary.

The independent source review found no in-domain semantic mismatch. Its private
stack alias concern was resolved with the explicit contract and guard above.

## Frozen result

The completed run is `build/reverse-effect-parameter-resources-01`.

| Check | Result |
| --- | --- |
| Original-instruction versus C comparisons | 2,850 passed |
| Original instruction steps | 382,440 |
| New instruction coverage | 579 / 579 |
| All loaded instruction coverage | 737 / 745 |
| Focused native tests | 25 passed |
| New API guard checks | 13 passed |
| Exact-allocation ASan/UBSan original-fixture replays | 2,850 passed |
| Additional sanitizer invalid-API check | 1 passed |
| Callback-mutation cases | 8 |
| Carried calls | 24 |
| Built pi32v2 objects | 34 |
| Independently reread source hashes | 112 matched |
| Independently reread artifact hashes | 40 matched |
| Reused target objects compared with earlier same-source artifacts | 33 / 33 identical |

The corpus contains 746 direct codec comparisons, 82 full migrations, 1,681
property/mode cases, 119 ownership/callback cases, and 222 IR cases. Migration
executes the original decoder 3,261 times and encoder 201 times. Installed clear
and memset each execute five times, including leading/trailing byte paths for
unaligned native allocations. The clear callback's exact original slot
`0x01c34194` is used, and a focused test requires actual memset execution.

There are no missing new instructions. The eight missing inherited instructions
are classified explicitly in the report:

- `0x01c055da`, `0x01c055de`, `0x01c055e2`, `0x01c055e4`, `0x01c055e6`,
  `0x01c055e8`: the type 25 path of the active helper cannot be called by this
  cluster, because fingerprint returns directly for type 25.
- `0x01c11f62`, `0x01c11f64`: the zero-object path of IR-active cannot be called
  by the IR-state wrapper, which calls that helper only for a nonzero object.

Full path visitation does not prove equivalence for every possible callback or
memory configuration. The comparison domain and explicit service boundaries
above still apply.

Final SHA-256 bindings:

| Artifact | SHA-256 |
| --- | --- |
| `verification.json` | `e90b609863eeadffc7d12f8dfd10b1052cbcf3fce55a02429617253fd3eeb453` |
| `build-manifest.json` | `242259ed06fbb47f8373fca4fed1571d60047f2cd6c46f4dbea88ab4f3a9771f` |
| `hyperrig_effect_parameter_resources.pi32v2.o` | `d5ed18491abddaa1e57144479b23b627a3d2bed349a0b8e88de3c214935fd005` |
| `sanitizers.json` | `f60d6161ab1e5adc7f1c19fab114a695b04d2cfad93e029f4b765d5d04ad34fc` |

All eight maintained module files passed a local line-ending, whitespace and
private-path scan. The source and artifact audit reread every declared file.
The earlier development libraries remain in their ignored output directory;
they are not the frozen evidence and are not inputs to this run.
