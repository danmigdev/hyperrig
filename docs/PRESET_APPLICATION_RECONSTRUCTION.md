# Reconstructed preset application

The complete application handler at `0x020092fa..0x02009dd0` now has maintainable
C and comparisons against its original instructions. Its two paths attempt to
update compatible effects in place or rebuild the effect arrangement. The model
executes the existing asset/header/layout dependencies and effect queries. Effect
allocation, capture/IR application, downstream reconfiguration and scheduling
remain explicit service boundaries in this corpus.

This closes the application caller's control flow and explains its result. It
does not establish a complete playable firmware, physical storage behavior or
execution of the downstream effect implementations. Earlier modules, reports,
tested firmware and original inputs remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstruction retains the original project's
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md) and notice.
It is reconstructed source, not the original source or a flashable image.

## Pinned evidence

The original M5.71 G v2 application has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited input loader checks both that artifact and its actual decoded
application. All seven new bodies are complete, with no embedded data spans:

| CPU range, end exclusive | Behavior | Instructions | Original bytes SHA-256 |
| --- | --- | ---: | --- |
| `0x020092fa..0x02009dd0` | Application, reuse and rebuild | 868 | `9e48e0dcb71a39bee2c7d05a1d064859d5f419642ef58422cff306f5ad6232ee` |
| `0x02007348..0x02007352` | Read mode byte | 3 | `5ecfb1a5cd5d739ff7484fdac19c3a6edc31082ed13a132e724455d9f6f6baf1` |
| `0x020091c0..0x020091d6` | Parameter ordering | 8 | `2c9e050379d83ae6f87c89f7b9f7ccb38dc3a08f021b50d426f6a8cff63af4f1` |
| `0x020092e4..0x020092fa` | Notification packing | 7 | `64608663004ffdd6c65165eb4c611fd61e9cf3e6d6f1da6a761b0172fe71b973` |
| `0x0202921e..0x02029248` | Parameter metadata lookup | 14 | `28b02e9ddb4b0be3f462425caa46f55037a205429479c54aae16413b61240fbf` |
| `0x02030948..0x0203097c` | Stored signed parameter | 18 | `3e9fcebf4ca443636b2b8789184d251f8868cd0e1937c8e79c7c3de39116c884` |
| `0x02030a9a..0x02030ab6` | Placement query | 10 | `8080219e3e6c237e17ead78e380fb7c38f079f4e134f8a1f4933c5cdd8a6a65c` |

Together these contain 2,950 bytes and 928 instructions. Fourteen existing
regions supply another 248 instructions: nine asset helpers, the storage header
reader, three chain/effect queries and calibration-rate arithmetic. Their original
instruction bodies execute internally, including callback-sensitive header
reloads. The model uses 21 disjoint function regions and 1,176 instructions.

The parameter metadata table occupies `0x0203a614..0x0203b334`, 3,360 bytes,
SHA-256 `a267e201259b804adc7dc0cafa79238b1aa20eed21c69a685a28d60099cd2cf4`.
The getter accepts types 1 through 39 and indices 0 through 6. It selects a
12-byte record at `base + 84*type + 12*index`, returning its original address when
the final word is nonzero, or zero otherwise. C retains the exact presence bits
and original address arithmetic. Those address tokens are never host pointers.
Other metadata fields and the effect algorithms they describe are not decoded
semantically by this getter.

## Application results and state changes

The caller receives two independent output words: capture status first, IR status
second. The application clears both after the optional initial mode-service call.
It stores 255 in global bytes 18 and 19, and writes the requested preset to byte
20, replacing every unsigned ID at least 127 with 255. It caps the working
effect count at sixteen and captures the entry mode word at state offset 280.
Later decisions deliberately retain those captured values while other fields
are read again after callbacks.

The semantic return value counts effect failures. Allocation failures, an effect
enable operation still failing after its retry, and a failing type-seven
completion operation contribute to it. Capture/IR statuses remain separate and
do not automatically increase this count. Successful in-place application
returns zero even if a capture or IR service reported an error.

The earlier [preset loader](PRESET_LOADER_RECONSTRUCTION.md) calls this handler
but does not test its result before committing the requested preset ID and
sending its report. That earlier module still uses an application callback; its
frozen report is unchanged. The present evidence explains the handler's behavior
within its declared services, without changing the loader or claiming that its
complete downstream DSP path has been joined.

## Reuse and rebuild

Capture and IR slot differences trigger header/identity checks. Their descriptors
at state offsets 1780 and 1796 determine whether an existing asset can be reused.
Header validation, J/I fallback, extended capture identity reading and descriptor
comparison execute the recovered helpers. Physical reads remain a service.

The in-place path requires entry mode two, compatible asset decisions, no cleanup
requirement and a matching mode byte. It traverses both existing chains, checking
effect membership, type, placement, special type-seven parameters and readiness.
It probes every candidate's parameter update before applying them. Probe results
form a bit mask, with the original register-shift masking retained. Tempo-related
preparation and mask acceptance can also reject this path.

Once accepted, it applies required capture/IR updates, mode changes, parameter
transitions, enable changes in two passes, branch settings and final reporting.
A later failure enters the rebuild path. Completed callback effects and output
statuses are retained; there is no transactional rollback. The duration byte is
captured at its original point and can be forced to one by the global override.

Rebuild can first attempt cleanup, whose persistent failure sets capture status
`-110`. Capture status `-111` can trigger the embedded capture installation and
invalidation path. Installation remains a service here; this comparison does
not replace the separate [native capture](CAPTURE_LIVE_RECONSTRUCTION.md) evidence.
The original counter/clock polling order and wrapped rate arithmetic are retained
without assigning physical time units.

Existing effects are collected from both chains, capped at sixteen. The first
matching type is retained for each requested effect; leftover effects are
released. Unmatched requests allocate a new effect. Allocation results `-3` and
`-4` trigger compaction and one retry. Other negative results except `-2` try the
fallback allocator. Signed byte conversion of retained IDs follows the original.

Parameter updates read the working type again for each of seven indices. Type
five swaps indices zero and four; the other indices retain their order. Only
parameters with a present metadata record are sent downstream. Placement and
enable changes, branch updates, resource checks and type-seven completion follow
the original call order. Working parameters and public state can change at the
documented callback boundaries.

The final notification helper emits code 30 and packs the tag into the upper
halfword with low halfword 65535. Application selector one uses tag three and
reads the callback-state word at `0x01c341a8`; every other nonzero selector uses
tag four and payload zero. The original conditional packet has a one-packet
THEN and two-packet ELSE, both exercised by the comparison.

## Original-address views and API guards

The public runtime contains seven disjoint original address windows:

| Start | Bytes | View |
| --- | ---: | --- |
| `0x01c1f180` | 272 | Globals |
| `0x01c26890` | 4,100 | Application state |
| `0x01c24790` | 1,490 | Converted working preset |
| `0x01c2c220` | 7,680 | Sixteen 480-byte effect slots |
| `0x01c32db0` | 640 | Control and chain state |
| `0x01c1f7d4` | 68 | Configuration |
| `0x01c34190` | 768 | Callback state |

These views total 15,018 bytes, plus eight output bytes. The caller owns them.
Unused fields are preserved and compared; assigning a window does not infer the
semantics of every byte it contains.

Service arguments use original uint32 address tokens. A synchronous mapping view
also exposes initialized pointer arguments in the application's 256-byte scratch
at comparison address `0x30000ecc`, outputs at `0x31004000`, and an optional private
read buffer normalized to `0x31005000`. The latter two are comparison addresses,
not firmware globals. Private buffers are borrowed only for the call receiving
them. Unused scratch padding and incidental return registers are not persistent
outputs and are excluded from equivalence claims.

Callbacks may mutate caller-owned state and supplied buffers synchronously.
They must preserve chain counts at most ten, buffer capacities, lifetimes, IO and
view metadata. Re-entry, retained pointers, concurrent mutation and overlapping
host objects are outside the contract. Calls compare semantic arguments with
unused argument slots normalized to zero.

New host API errors are separate from firmware results:

- `-200`: missing runtime/output/result/IO/service, zero call budget, or an
  initially invalid chain count. No calls or writes occur.
- `-201`: a service invalidated the chain-count domain. Completed effects remain.
- `-202`: the positive external-call budget was exhausted. This bounds an
  uncooperative external wait; it is not a recovered native timeout status.

The mapping helper rejects requests outside the supplied address windows.
It does not grant access to immutable firmware data or arbitrary host memory.

## Reproduction and remaining boundaries

After obtaining the pinned local input images and toolchain, use a fresh directory:

```text
python -B tools/build_preset_application.py --output build/reverse-preset-application-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder creates a warning-clean UBSan host library, six freestanding pi32v2
objects, focused native-instruction tests, exact-allocation ASan/UBSan checks and
hashed comparison/build reports. Source manifests come from maintained source
and actual imports; no earlier ignored verification report is required.
The five previous C dependencies compile unchanged.

The MINI check binds all 21 regions, every loaded instruction window and the full
parameter metadata table to the pinned v4 image, SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The inherited instruction interpreter remains an assumption supported by earlier
evidence; these are not new processor measurements.

## Frozen validation

The completed run is `build/reverse-preset-application-01`. Its source and artifact
bindings were independently read back after completion. The five previous target
objects remain byte-identical to `build/reverse-preset-assets-01`.

| Evidence | Result |
| --- | ---: |
| C/original comparisons | 1,775 |
| Complete application entries | 607 |
| Parameter-order / metadata comparisons | 484 / 484 |
| Stored-parameter / placement comparisons | 180 / 20 |
| Original instruction steps | 1,253,601 |
| Carried application calls | 12 |
| Cases with synchronous callback mutations | 21 |
| New instructions visited / decoded | 928 / 928 |
| Combined instructions visited / decoded | 1,173 / 1,176 |
| Focused native expectation tests | 18 |
| Invalid API / service-domain / budget checks | 8 / 1 / 1 |
| Mapping rejection checks | 8 |
| ASan/UBSan exact-allocation applications | 408 |
| Additional sanitizer budget-guard cases | 408 |
| Audited source / artifact hashes | 32 / 10 |

All new instruction bodies are covered from their real entries. The three gaps
in reused dependencies, `0x02006f36`, `0x02006f86` and `0x02007c90`, are retained
in the report; earlier module comparisons
remain separate evidence. The corpus covers empty through sixteen-effect layouts,
legacy routing, raw identifiers and flags, both asset headers and reuse decisions,
extended identities and partial reads, allocation/activation retries, in-place
failures followed by rebuild, polling exits, notifications, callback replacement,
parameter mutations and repeated application on carried state.

Independent source/instruction review found no further mismatch after the final
notification selector correction. The new relocatable target object is 8,764
bytes, SHA-256 `728541b1117f11b79fcfadc5494f1f6860270d3cce0ef37770528a24475787d7`.
It is not a firmware size or runtime resource measurement.

| Record | SHA-256 |
| --- | --- |
| Reconstructed C | `8ea1d2b5ad1efda842f727b0163036deaa3f2eb3f42d3d4707a095a93c9dd018` |
| Verification report | `381285224425573799f871829c92356d031ba20041840480778cc6e13bd812fc` |
| Build manifest | `f5b151f8cbf25484e5dcf99cc0db24ca9234db9cce2d3406bb8b66ec396b9f1e` |

Next integration must replace the named capture/IR/transition service boundaries
with their recovered implementations in this caller, recover effect creation,
parameter updates, enable/routing and resource ownership, and connect the result
to scene application and the audio task. Physical storage, scheduling, allocation
and asynchronous device behavior remain open. No firmware was flashed and no
hardware or audio test was performed.
