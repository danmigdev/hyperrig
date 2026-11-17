# Actual constructor-to-signal state integration

This checkpoint executes the recovered original constructor at `0x0202cf62`,
then carries its actual output bytes into the recovered gate, all-pass and
state-variable processing paths. The C calls the unchanged construction and
signal APIs. The independent model executes their original instructions. It
adds no native functions and does not declare previous bodies again as newly
recovered code.

Required Notice: Copyright (c) 2026 Manuel Aguirre

https://polyformproject.org/licenses/noncommercial/1.0.0

See [the preserved license](../third_party/ultrarig/LICENSE.md).

The underlying checkpoints remain unchanged:
[construction](EFFECT_CONSTRUCTION_RECONSTRUCTION.md) and
[signal processing](EFFECT_SIGNAL_RECONSTRUCTION.md).

## Producer and consumer relationship

| Type | Actual preparation | Actual processing |
| --- | --- | --- |
| 1 | Thresholds and rate-dependent Q16 coefficients in effect `+288..+304` | Gate at `0x01c19a8a..0x01c19bee`, retaining envelope/gain at `+308/+312` |
| 13 | Phase increment, feedback, 33 Q30 lookup words, duplicate endpoint and conditional cold coefficient initialization | Four-stage all-pass at `0x01c1958e..0x01c19a8a`, with real phase/table interpolation and retained histories |
| 38 | Envelope/filter controls, output targets, logarithmic frequency/sweep values and rate coefficients | The actual dispatcher computes working filter coefficients before calling `0x01c1ee40..0x01c1f088` |

Type 38 requires both original steps. Its constructor does not produce the
three working state-variable coefficients by itself. The integrated corpus
first executes the real dispatcher on the constructed state; later direct
filter calls use those resulting coefficient bytes. The original inline
coefficient updates, residual arithmetic and output mixing remain active.

Input halfwords, initial sample buffers and initial history values are explicit
fixtures. No constructor-generated coefficient or lookup table is replaced by
the harness. Parameter changes edit the original halfword fields and call the
real constructor again. Current coefficients and histories that the constructor
retains are carried from the preceding processing call. Sample/state aliases
may overwrite coefficient or table storage through the original numerical
writes; these are native effects rather than fabricated replacement inputs.
In the explicit shared-configuration alias witness, the existing current
coefficient word also represents the sample-rate field. The constructor's
conditional retention of that word is preserved; it is not presented as a
freshly generated coefficient. Ordinary cold all-pass chains initialize the
current coefficient to zero and receive the real generated midpoint value.

## Invocation and callback boundaries

`hyperrig_effect_configured_signal_prepare` directly invokes the constructor as
a separate synchronous operation. The execute, stage and audio-resume
operations call the frozen signal API on the same caller-owned storage. No
service target is intercepted as a request to construct an effect. Consequently
this integration does not inherit the earlier constructor verifier's
restricted target-only parameter bridge.

The constructor model validates each external service against its original
instruction address, target and argument count. Its full dispatch remains
unchanged, including the common effective-rate write before the effect type is
read. Remaining larger builders stay explicit. Two boundary witnesses script
a type 17 or type 39 builder that changes the effect type. A second real
preparation then constructs type 13 or type 1 before recovered processing runs.
These witnesses do not claim to reconstruct the larger builders or their
numerical output.

Constructor and processing entries share public state across successful calls;
this is a data handoff, not a newly identified native constructor-to-audio call
edge. When preparation occurs between audio observations, the original
constructor executes with its own balanced invocation stack. Only its actual
public-memory writes are carried back into the paused task. The task's program
counter, registers, private stack, return frames and conditional state are
preserved. The C uses the same stable public allocations throughout that chain.
No concurrent scheduling, interrupts or physical task switching are simulated.

## Domains and failure behavior

The underlying construction and signal contracts apply unchanged. Mappings are
pure, stable little-endian byte storage preserving native alias relationships.
Distinct original bytes cannot acquire additional host aliases. API, IO,
result and task-control storage are disjoint from mapped data. The native
private stack `0x30000000..0x30001020` remains reserved. Callbacks cannot relocate
storage, retain borrowed views, reenter or run concurrently.

Constructor and direct numerical bodies support unaligned host byte storage.
The inherited dispatcher, stage and audio paths retain their existing host
alignment and typed-storage requirements. The integration does not weaken those
requirements by changing the underlying files.

Preparation resets its service/work budgets from the new IO object for each
invocation. Reached exponential inputs must be finite with magnitude at most
65536, and reached coefficient-generator parameters retain their earlier
finite magnitude bound of 128. The original integer binary32 arithmetic and
range reduction execute; no host `float` or `libm` substitute is used. Budget
or finite-domain failures retain earlier writes under the frozen constructor
API contract. The verifier compares delegated C failure behavior separately;
those checks are not claims of original firmware error returns or fault-prefix
equivalence.

Processing resets the signal block budget for each invocation and retains the
raw modulo count and pointer rules. No integration-specific sample ceiling is
introduced. The corpus includes counts above 512 and a large raw count with a
short wrapped filter endpoint. Zero/underflow block counts and unreachable
filter endpoints are bounded at native block entries, preserving their actual
public-memory prefixes. Such errors are not resumable audio observations.
Existing bounded caller domains still apply when the dispatcher, group, stage
or task wrapper is selected instead of a raw numerical entry.

## Verification method

Each retained-allocation chain compares the complete public memory, ordered
service arguments and boundary state after preparation and processing.
Preparations execute actual original exponential/trigonometric/logarithmic
dependencies where reached. Complete signal callers remain original decoded
execution; recovered kernels are never replaced by scripted sample output.

The corpus includes cold preparation, rate/mode changes, signed parameter edges,
re-preparation after processed history, sample/table/state aliases, a constructor
output alias with shared configuration, raw count and block-budget edges,
individual effects, both stage sides and preparations between carried audio
observations. Remaining audio/output/platform services are explicit scripts.
This is neither a hardware test nor a physical audio or timing measurement.

Sanitizer replay retains the same allocations for every operation in a chain.
Before each operation it applies only recorded parameter/input mutations and
checks that the retained bytes equal the original input snapshot. It then
compares the complete result against the original instruction execution.
Neither the replay nor the ordinary C comparison silently restores expected
coefficient/history bytes between calls.

The new source manifest is captured before the first compiler invocation and
must equal the final verifier manifest. It includes all compiled C inputs,
recursive headers, transitive Python models, dynamically loaded ISA helpers,
the ISA TOML, builder, focused tests and sanitizer driver. It requires no old
ignored verification report as an input. Original firmware and compiler inputs
remain local evidence outside Git.

The original image SHA-256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`;
the decoded payload is
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`;
the preserved MINI v4 image is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The report binds every loaded original instruction window and relevant static
range to both payloads, and lists unvisited loaded instructions explicitly.
It adds no native function entries or new static data exclusions and does not
claim an overall firmware completion percentage.

Final evidence is frozen in ignored
`build/reverse-effect-configured-signal-02/`:

- 681 original/C comparisons on 142 retained-allocation chains.
- 334 actual constructor calls, including 18 preparations between audio
  observations; 4,769 original constructor exponential calls.
- 3,530,144 original instruction steps and 5,858 actual signal blocks.
- 13 focused tests, 14 C API/delegation checks and all 681 ASan/UBSan replays.
- 36 pi32v2 objects built. All 35 inherited objects match the frozen signal01
  or construction02 builds byte for byte. The new adapter object is 1,056 bytes.
- All 151 source and 42 artifact bindings rehashed after completion. The MINI
  comparison binds all 19,023 loaded instruction windows and 32 static windows.

This integration visits 3,120 of 19,023 loaded instructions. Within the four
main reused bodies it visits constructor 264/971, all-pass 395/415, gate
113/117 and state-variable filter 176/176. The narrower constructor/type and
generated-coefficient corpus does not revisit every branch from the earlier
complete-body checkpoints. Every unvisited loaded address remains listed;
there are zero new native functions or new instruction declarations.

`verification.json` SHA-256:
`064cb4a86f6e764e5408ee13f1461678034f0f08a0d3464b2ddad7876fdd47a8`.

`build-manifest.json` SHA-256:
`a48dd61894d50840ad3d7d7bbd1e4944e4c8b9c1379900b13075ed4217ef2e3e`.

Candidate01 is preserved as incomplete evidence: report hashing stopped when
an explicit constructor callback trace contained byte snapshots. Candidate02
fixes only that new verifier's digest serialization and separates its boundary
fixture function. The semantic C/header/model and sanitizer driver are
unchanged. Candidate01 has no completed passing report or build manifest.

Reproduce from the repository root in WSL with a fresh directory:

```sh
python3 -B tools/build_effect_configured_signal.py \
  --output build/reverse-effect-configured-signal-new \
  --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

Independent read-only review found no in-domain C/model state-transfer or
callback mismatch. It confirmed that the explicit constructor invocation avoids
callback-token collisions and that only public bytes cross the paused audio
boundary. Its request to capture source hashes before compilation was adopted
before the final run. The reviewer did not edit files or repeat the suites.

## Remaining integration work

The new API does not execute the original parameter commit/resource-lifecycle
caller, command transport or scheduler. Those paths remain separate recovered
checkpoints or explicit boundaries. It verifies types 1, 13 and 38 through the
declared preparation and processing sequence, without extending that claim to
every constructor branch or effect model. Remaining larger builders, other
numerical leaves, output/peripheral services and hardware validation still need
their own evidence.

The eight maintained files use the new `effect_configured_signal` stem: the
public header, C adapter, original model, verifier, builder, focused tests,
sanitizer driver and this scoped document. Generated evidence remains under
ignored `build/`; frozen earlier sources, reports and firmware images are
unchanged. No device was accessed or flashed.
