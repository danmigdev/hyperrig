# Effect creation, allocation and tempo reconstruction

This module reconstructs 45 complete original bodies: effect creation and its
disabled wrapper, allocation and pool publication, type-29 and type-30
initialization, routing and cost calculations, and global tempo propagation.
The bodies contain 5,288 bytes and 1,759 decoded instructions. The byte extent
includes a 35-byte embedded branch table and its one-byte alignment padding.
The complete named registry is `REGIONS` in
[`effect_setup_machine.py`](../tools/effect_setup_machine.py).

These are offline comparisons with the pinned M5.71 instructions. They are not
device, timing or audio tests. The module does not change a firmware image,
release, hardware policy or reserved feature branch.

## Inputs and complete-body boundaries

The encrypted original image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Its decoded application has SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`.
Every loaded original instruction and immutable data window is independently
checked against the reviewed MINI v4 image, SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The original inputs, previous reconstructions and their reports remain unchanged.

The main new boundaries are:

| Entry | Complete half-open range | Role |
| --- | --- | --- |
| `create` | `0202e710..0202ea90` | Admission, defaults, resource setup, construction and publication |
| `create_disabled` | `0202ea90..0202eabc` | Temporary admission override followed by disabled publication |
| `tempo` | `0202f46c..0202f4e8` | Signed clamp and updates across 16 live effects |
| `allocate` | `0202e4c2..0202e710` | Contiguous allocation, partition fallback and rollback |
| `initialize29` | `0202dfe4..0202e328` | Layout, trigonometric tables, phase pairs and interpolation coefficients |
| `refresh29` | `0202e328..0202e346` | Real returned-object-pointer selection and initializer gate |
| `initialize30` | `0202e346..0202e3ce` | Complete clear, window generation and reused coefficient setup |
| `refresh30` | `0202e3ce..0202e3f6` | Wrapped capacity gate and initialization |
| `pool_claim` | `0202e3f6..0202e432` | Four-object pool selection and clear |
| `pool_attach` | `0202e432..0202e4c2` | Native object publication and segment-pointer attachment |
| `estimate_slot` | `01c05d02..01c05d40` | Two-word cost request and six-word extra-cost request |

All remaining declared bodies are complete demand, layout, partition, segment,
mode, grouping, routing, filter and cost helpers. The report records individual
byte hashes, decoded instruction counts, visited addresses and every gap.
Reused constructor, resource, ownership, numerical, IR and parameter bodies are
listed separately and do not add new recovered functions.

## Borrowed memory and executable joins

[`hyperrig_effect_setup.h`](../firmware/include/hyperrig/hyperrig_effect_setup.h)
exposes `hyperrig_effect_setup_execute(entry, arguments, result, io)` and the
new checked parameter adapter. Both operate on one canonical native byte map.
The map is pure; repeated addresses retain their native identity. API objects
and result storage are disjoint from mapped firmware bytes. Original code and
static input bytes remain immutable. Writable public objects may overlap.

Callbacks are synchronous. They may change mapped fields but cannot reenter,
retain views, relocate backing or alter the API objects. Reads after a callback
observe the original reload order; cached native values remain local. Numeric
callback tokens are interpreted at their original call sites. A token equal to
a loaded constructor, setup or tempo entry remains an external callback.

The exact new direct joins are:

| Original call site | Reconstructed target |
| --- | --- |
| `0202e9ae`, `0202e9d4` | Main constructor `0202cf62` |
| `0202e92a` | IR mode preparation `0202983a` |
| `0202f4ba`, `0202f4cc` | Parameter commit `0202f07e` |
| `0202f338` | Type-29 refresh `0202e328` |
| `0202f412`, `0202fda0` | Slot cost `02028cb2` |
| `0202f44a`, `0202fe48` | Total cost `02028de8` |

The five parameter substitutions are authenticated by hashing the frozen
`hyperrig_effect_parameter_construction.c` parent and regenerating the exact
expected new source in memory. Only its public prefix/header, one borrowed
bridge and those five direct calls may differ. Previous numerical, resource,
ownership and guarded scene units are unchanged. The outer preset application
is not joined in this module.

`estimate_slot` receives **two** original words. Its second word reaches the
existing cost body unchanged. Type 5 and types 27, 31, 32, 33 and 35 have different
costs for zero versus nonzero second words. The six-word neighbor helper and
extra-cost estimator retain both native stack arguments. The comparison corpus
includes earlier callback writes that change the subsequently forwarded live
enable byte.

Eight creation progress sites use three arguments: zero, the packed
type/slot/phase word, and the phase payload. The first payload is the cached
initial chain length. Both allocation-query sites use zero arguments; the
failure notice uses one. Generic allocation, release, mode, progress, query and
other platform behavior remains an explicit service boundary.

## Allocation and alias behavior

The allocator computes private segment lengths before invoking services. It
publishes the returned main pointer before clearing and publishes capacity
after clearing. Fallback allocation greedily packs the largest fitting
remaining segments, with the original unsigned additions and comparisons.
It can allocate a main buffer and three extra buffers, rotate the allocation
holding segment zero into the main slot, and execute real ownership rollback.

Private native stack addresses `30000000..30001020` and inherited transient
storage `31005000..31005020` are reserved. Private partition arrays cannot alias
public storage or be retained by a callback. Raw segment and partition helpers
retain the original unrestricted arguments, signed tests, wrapped addressing
and modulo-32 register-bit indices; the corpus includes counts 32, 33 and 63
and segment indices beyond the normal caller counts. If a callback changes the
type so a subsequent pool attachment
would consume an uninitialized original private pointer, the portable API
returns `-202` at that access and preserves prior writes. This is an explicit
portable domain guard, not an original firmware error return.

The raw segment adapter retains the original object-length calculation without
the earlier standalone API's index cap. Its unsigned 16-bit input and two
positive coefficients below one keep the converted result below 65,536; the
reused signed conversion therefore equals the original unsigned conversion
over this reached domain. This is a bounded equivalence, not a change to the
original arithmetic or the frozen helper.

The original extra-size helper at `01c05ff2` returns 56,480. Type-29 demand with
parameter 6 enabled is therefore 32,336 halfwords: an 8,192-byte first region
and the 56,480-byte extra object. Pinned default metadata sets parameter 6 to
zero, so default creation requests only 4,096 halfwords. The corpus distinguishes
default creation, a pre-existing effect with the enabled extra parameter,
contiguous allocation, split-buffer selection and absent/short-buffer gates.
The initializer receives the actual pointer returned by the recovered selector.

Type 30 clears all 5,102 words before reading parameter values. Parameters
overlapping the cleared object therefore read the cleared bytes. The native
wrapped capacity expression `((capacity << 1) >> 3)` is preserved. Type-29
layout retains the original mask value `3080`, and its phase/table arithmetic
uses the recovered float operations and sine implementation.

Creation preserves early counter and failure-byte writes even when validation
fails. Admission uses the original unsigned wrapped sums. The disabled wrapper
sets its override to one then zero, rather than restoring an earlier value.
Constructed state, live flags, route insertion and neighbor updates remain in
native order. With the override disabled, failed IR creation retains the actual
preparation status, including `-3`, after clearing the effect type. Tempo clamps
its signed argument to `400..3000`, reads each live
effect again after its real commit, and returns the freshly loaded configuration
word. No physical units are inferred from these values.

## Exact new data evidence

Four new data spans total 104 bytes:

| Half-open range | Bytes | SHA-256 |
| --- | ---: | --- |
| `01c060a6..01c060c9` | 35 | `5dc4cf8f1d20dd94c81c4f1d7c37e6c1724444715d5988a1bc6eb106fc85d2dc` |
| `01c060c9..01c060ca` | 1 | `6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d` |
| `0203b940..0203b97c` | 60 | `0b99fb255d9a4849be3201a9dc5321737f11f3bef6514cb8643cf0ac58a835ea` |
| `0203b4ae..0203b4b6` | 8 | `e5bfb2fb92a6c54c409f00b095799f42bf140499df4bfb528789bef3acfcec17` |

The complete stereo helper `01c06098..01c060e6` checks unsigned `type-5 <= 34`
at `01c0609c` and uses its TBB at `01c060a4`. A return-only target retains the
preloaded value 2,400; it is not an additional constant assignment. The single
zero padding byte is separate from the 35 dispatch bytes.

The complete group helper `01c0606e..01c06088` requires mode one and unsigned
`type-9 <= 14`, loads base `0203b940` at `01c06078`, and reads a word with stride
four at `01c0607e`.

For the newly proven four-halfword range, the complete object-mode helper
`01c05ed6..01c05eec` selects mode one for type 33. The complete count helper
`02029c22..02029c3e` gives 13 segments. In the complete segment consumer
`02029ed4..02029f8e`, the gates at `02029f0a`, `02029f0e`, `02029f12` and
`02029f16` leave indices 9 through 12. Sites `02029f1a..02029f24` map them to
zero through three, `02029f26` loads base `0203b4ae`, and `02029f2c` reads one
halfword with stride two. This independently classifies eight bytes that the
older model checkpoint left unclassified. The two-byte tail
`0203b4b6..0203b4b8` remains outside the inventory data exclusions. A separate
auxiliary immutable binding supplies those two original bytes only for the
raw helper's index-13 witness. It does not extend the caller-proven four-element
table classification. Earlier reports are unchanged.

The index bound belongs to the normal callers, rather than a raw-helper entry
guard. Complete `partition_sizes` obtains the count at `0202a1f4`, initializes
the index at `0202a1fe`, calls segment-bytes at `0202a202`, and increments/tests
it at `0202a20a`/`0202a20c`. Complete `object_total` uses the corresponding sites
`02029fa6`, `02029fb4`, `02029fba`, `02029fbe` and `02029fc2`. Complete
`segment_bytes` at `02029f8e..02029f98` forwards the index to the complete
segment consumer. The report binds every one of these full bodies.

## Verification and reproduction

The comparison executes decoded original instructions with native registers,
parallel packets, stack arguments and one shared RAM image. It compares scalar
returns, all mapped bytes, ordered callback arguments, complete callback
before/after snapshots and private output lifetimes. The C implementation is
compiled independently. Tests cover signed and unsigned extremes, wrapped
costs, carried creations, greedy allocation, failures, callback collisions,
public aliases and real nested parameter/construction paths.

The standalone builder compiles strict host C and pi32v2 objects, runs focused
tests, creates the original comparison report, and replays every comparison
under ASan/UBSan with exact buffer allocations. The replay stores zero runs
compactly; it reconstructs and compares every byte of each original mapped
buffer. The manifest binds dynamically loaded ISA helpers, the instruction
TOML, recursive local headers, all sources and generated evidence. It does not
require earlier ignored reports to reproduce the module.

```powershell
python tools/build_effect_setup.py --output build/reverse-effect-setup-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

Portable mapping, work, service and reached numerical guards preserve earlier
side effects and leave result storage untouched. They do not claim identical
native failure prefixes unless a comparison explicitly establishes that fact.
Nested mapped-access charging and local work caps are not a unified native
instruction count, and stopped calls cannot resume. Remaining loaded and
declared instruction gaps are reported separately.

## Final offline evidence

The selected build is `build/reverse-effect-setup-03`. Its final report and
manifest have these SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `verification.json` | `bde014640f2abc55e46f453408103010dcb10f95fe0d78dd09574fbaa3ce22e9` |
| `build-manifest.json` | `f991cc25f80efef64b824a2bcc322242e1fd699458eb7aa7c06860e9cf4f6840` |

All 214 source bindings and 53 artifact bindings were read back successfully.
The 47 pi32v2 objects include 45 reused objects that are byte-identical to their
same-source frozen parent artifacts. The new main C source has SHA-256
`7e6c8e009969c4ace7f89eb2a87c3371149c022c7fb40092dc6d91e59e3c149e`.
Its captured CRLF line endings are preserved by an exact-path Git attribute,
so checkout and staging retain the source bytes identified by the report.
No previous source, input image or report was changed.

| Check | Result |
| --- | ---: |
| Original/C comparisons | 4,229 |
| Executed original instructions | 9,664,208 |
| Focused tests | 20 |
| Exact-allocation ASan/UBSan comparison replays | 4,229 |
| Additional sanitizer invalid-API checks | 4 |
| C-only API, mapping, budget and domain checks | 16 |
| Callback mutation cases | 39 |
| Carried calls | 5 |
| New complete-body instruction coverage | 1,758 / 1,759 |
| Declared new and reused instruction coverage | 8,164 / 9,761 |
| All loaded instruction coverage | 8,518 / 22,289 |

All ten authenticated direct joins executed. The two probe joins at
`0202fda0` and `0202fe48` executed 28 and two times respectively. The report
lists every join count and distinguishes the 45 new bodies from 144 reused
role declarations. Shared bodies are not additional reconstructed functions.
All 22,289 loaded instruction windows and 60 static windows match MINI v4.

The only unvisited new instruction is `0202e3b6`, the positive saturation
assignment in the type-30 window initializer. The original execution records
all 256 fixed loop indices at `0202e3aa`; every returned sine word is below
the representation of 1.0. The maximum is `0x3f7fffb2`. The ordered index/value
pairs have SHA-256
`0109e6171e613d6ac1e25ef6ed7d794cd870d2a39b8cb2bf8e4ddcd7e67dca2e`.
The fixed argument sequence and recovered pure sine calculation do not depend
on mapped state or callbacks. This explains the unreachable assignment under
the pinned execution semantics; it is never counted as executed. Every
inherited joined or loaded gap remains explicit in the report.

An independent review reran the 256 exact arguments through the earlier frozen
original sine machine: all 19,968 original steps reproduced the recorded words,
with no external calls or mapped-state changes. This is offline evidence under
the pinned floating-point semantics, not an additional hardware measurement.

The table evidence retains exactly four new spans, 104 bytes in total, with
complete consumer bodies and 41 decoded proof-site records. The two-byte raw
index-13 witness remains an auxiliary immutable binding with
`inventory_data_exclusion: false`.

The inventory audit separately decodes all eight complete table consumers and
callers. Seven additional original mode/count and loop sites supplement the
report's 41 proof-site records. The new four-halfword proof supersedes exactly
`0203b4ae..0203b4b6` of the earlier model inventory's unknown prefix; the adjacent
`0203b4b6..0203b4b8` remains unclassified, including the raw index-13 witness.
Earlier inventory sources, reports and classification records remain unchanged.

Independent source review checked the derivative, callback sequencing, both
estimator words, type-30 clear order, raw signed segment indices, modulo-32
partition masks, wrapped sums and preserved IR preparation status. The raw
helper caps identified during review were removed, and their native cases
are included in the final corpus. Development builds `-01` and `-02` remain
unchanged: `-01` predates the IR status correction; `-02` predates the final
probe-join, alias and caller-loop evidence. Only `-03` is selected.
