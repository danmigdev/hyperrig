# Parameter and resource lifecycle integration

This offline module joins the complete parameter callers to the already
reconstructed resource bodies on shared original-address storage. Allocation
recovery, packed-history migration, fingerprints, mode resets and IR resource
queries now execute their actual recovered logic through the parameter caller.
The integration adds **zero original functions**. The earlier function counts
and individual verification reports remain unchanged.

The original routines derive from UltraRig Alpha 11, M5.71. This is reconstructed
C, not the author's original source. The required copyright notice and
[third-party license](../third_party/ultrarig/LICENSE.md) remain intact.

## Why the caller has an explicit derivative

The frozen parameter API exposes an external callback's target, arguments and
borrowed memory view. It does not expose the original instruction address.
Consequently, a one-argument free callback can have exactly the same numeric
token and argument count as a direct resource call. Intercepting target values
would turn a platform callback into a different operation.

The new C file retains the frozen parameter caller bodies and changes only
their public symbol/header/type names, adds one resource bridge, and replaces
the nineteen known direct resource calls. Indirect free, mode, allocation,
alternate-clear and scene-notification callbacks preserve their original
call-site behavior. All helper reuse, read/write ordering and error propagation
remain in the derivative.

`check_derivative()` authenticates the frozen source and reverses exactly those
substitutions. It requires byte-equivalent semantic source after normalization
of the explicitly changed names and bridge block; any other body edit fails.
The source record is:

| Input | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_effect_parameters.c` | `544d3eb301f8cc7c930ebe3cae9b4636edd20958620dda8024b894dad9b2af4b` |

The native comparison takes the other path: it merges the independently
decoded parameter and resource instructions, checks overlapping decoded
instructions for agreement, and executes calls on one register set, private
stack and public RAM image. It does not call the portable C to obtain reference
resource results.

## Joined calls

| Complete resource entry | Caller sites | Recovered operation |
| --- | --- | --- |
| `0x01c05ec6` | `f1e0`, `f1f8`, `f2b0`, `f314`, `f324` | Invoke the configured mode callback |
| `0x0202edb8` | `f1ec` | Allocate delay storage, release/retry, flush and restore |
| `0x0202ee3c` | `f276` | Migrate packed history with the real decoder and encoder |
| `0x0202eeba` | `f31c` | Allocate and clear extra state |
| `0x0202eefa` | `f34c`, `f382`, `f7a4`, `f7c0`, `fae4`, `fb02` | Compute the effect fingerprint |
| `0x0202efe2` | `f376` | Reset state and change mode |
| `0x0202f014` | `f3b0`, `fb52` | Read the actual IR active-state choice |
| `0x0202f02e` | `f3ba`, `fb5c` | Compute the IR resource-length limit |

Caller addresses in the second column have prefix `0x0202`. These eight direct
targets execute the complete nineteen-body resource module and its existing
numerical/helper dependencies. The final verifier requires all nineteen direct
call sites to execute; function instruction coverage is reported separately.

Scene inner/apply/select/flush entries continue through the original parameter
probe, immediate-update and automation producers. The stage consumer uses the
same effect slots and automation records. Their frozen APIs and original
instruction models remain unchanged.

## Allocation flag and mapped storage

The original immediate-update caller passes `sp + 8` to `0x0202edb8`. The
resource body initializes that word before entering the platform allocator.
The C caller exposes its corresponding four bytes through the borrowed token
`0x31005000`; resources use that borrowed view directly.

The original native pointer remains on the private stack. The comparison
exposes a canonical view only during its actual lifetime, from call
`0x0202f1ec` until the failure-path load at `0x0202f1fe` or the success-path load
at `0x0202f244`. This includes the failure-mode callback and success clear
callback that run before the caller consumes the flag. The comparison records
initialized flag bytes before and after such callbacks, and sanitizer replay
checks the bytes before applying recorded mutations.

| Storage | Original-address range |
| --- | --- |
| Borrowed firmware RAM | `0x01c1f180..0x01c344b4` |
| Sample storage | `0x35010000..0x35011000` |
| Allocation/history arena | `0x33000000..0x33020000` |
| Reserved native private stack | `0x30000000..0x30001020` |
| Reserved portable private views | `0x31005000..0x31005020` |

Ranges are half-open. Ordinary input and returned buffer tokens cannot alias
the private reservations. Read-only original tables are mapped separately.
Mappings are stable, pure and preserve original byte-address relationships.
API/IO/result objects are disjoint from mapped firmware storage; input ABI words
are copied before mutable callbacks. Services cannot retain views, relocate
storage, reenter or run concurrently. Successful allocation storage includes
the native sixteen-byte canary trailer.

The C APIs use finite work and callback budgets. Guard statuses retain prior
writes and publish no result on failure. These portable guard exits are not
original firmware return paths. The allocation guards specifically check that
an unmapped or private-stack result does not publish a new delay pointer or
capacity.

## Remaining boundaries

Effect construction at `0x0202cf62` remains an explicit service at both direct
sites in this checkpoint. Supplied derived words are fixture outputs from that
external boundary in this integration; they are not claimed as recovered
coefficients. A later construction join must replace those two direct sites
explicitly, preserving the callback-token distinction.

Platform allocation, release and mode callbacks, alternate clear callbacks and
slot removal `0x0202eb4c` also remain explicit. Installed clear
`0x0201a9dc` executes the existing original clear/memset bodies at its actual
support call site. Other inherited effect services, coefficient/resource cost
services and IR ownership operations keep their earlier boundaries.

The verified behavior concerns mapped offline execution. It does not establish
allocator ownership in a running system, task scheduling, USB, physical audio,
timing or a flashable firmware image.

## Reproduction and evidence

Use a fresh output directory; the builder refuses to overwrite a previous run:

```powershell
python -B tools/build_effect_parameter_lifecycle.py --output build/reverse-effect-parameter-lifecycle-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The build compiles the full unchanged dependency set on host and pi32v2, runs
focused original-instruction witnesses, compares complete public RAM and
callback traces, and replays the original comparison fixtures under ASan/UBSan.
Manifests bind all compiled C sources, recursively included headers, the
parameter-bound table include, dynamically loaded ISA Python modules and ISA
TOML. Reproduction does not depend on earlier ignored verification reports.

Both exact input images are authenticated. Every loaded decoded instruction
window and static table window is checked against the reviewed MINI v4 image:

| Image | SHA-256 |
| --- | --- |
| Original Alpha 11 container | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Decoded original application | `4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e` |
| Reviewed MINI v4 container | `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2` |

Independent read-only review found no in-domain mismatch in the explicit
direct-call substitutions, callback collision handling, shared state or private
flag lifetime.

## Final result

The completed, immutable run is
`build/reverse-effect-parameter-lifecycle-02/`. Candidate `-01` was deliberately
stopped before writing a verification report while two fixtures were improved:
the extra-state case previously reused available embedded storage, and the last
carried allocator response was changed to a released token. Candidate artifacts
remain preserved. The portable semantic C and native model did not change.

| Check | Result |
| --- | --- |
| Complete original/C comparisons | 1,293 |
| Immediate updates / fast updates / fast wrapper | 760 / 326 / 1 |
| Probes / stage calls / scene calls | 140 / 28 / 38 |
| Original instruction steps | 1,742,585 |
| Direct resource call sites | All 19, called 3,184 times |
| Native allocation-flag lifetimes | 335 |
| Callback mutation cases / carried calls | 68 / 35 |
| Focused original-instruction tests | 18 passed |
| C API guard checks | 17 passed |
| ASan/UBSan original-fixture replays | 1,293 passed, plus six invalid-API checks |
| pi32v2 objects | 39 built; all 38 reused objects match frozen parameter03/resources01 outputs |
| Source / artifact bindings | 160 / 45, all independently read back and matched |
| MINI v4 comparison | 15,590 instruction windows and 30 static windows identical |

The comparisons include both allocation retry successes, total failure, old
storage restoration, history tails and incomplete groups, extra-state retry,
mode reset, real fingerprints and IR limits, scene fallback, shared automation
state, and all direct-resource tokens used as mutating indirect callbacks.
They compare complete public RAM and ordered callback arguments, argument
counts, state before/after callbacks and live private flag bytes.

| Artifact | SHA-256 |
| --- | --- |
| `verification.json` | `c76dbdf8d80a712dad454f9555d40c16635e3a83c6bbf83c84a3671d1373c3e7` |
| `build-manifest.json` | `3dd30bb1065539b8a074d7f4d17aab95a9d68811651dc2788b64679b02e6fb62` |

## Integration coverage limits

The joined parameter/resource scope visits **1,334 of 1,573** decoded
instructions. This is 769/994 parameter instructions and 565/579 resource
instructions. The larger inherited decoder visits 2,984/15,590 instructions.
These counts describe this corpus only; they do not add earlier report coverage
or measure overall firmware completion. All complete bodies remain loaded.

The report lists every missing address. The 239 unvisited joined instructions
are classified as follows:

| Missing instructions | Reason in this integration corpus |
| --- | --- |
| 139 in section, word-kind and auxiliary-index helpers | The supplied constructor outputs exercise a limited set of automation word kinds; the standalone parameter03 classifier coverage remains separate. |
| 73 reachable instructions in fast update | Unselected readiness/boolean/timing cases, existing-record reuse scans, alternate word-kind delta calculations, larger durations and additional fallback paths. |
| One at `0x0202f960` | The previously established type-five entry invariant excludes the contrary assignment; the instruction remains decoded and preserved. |
| Nine in immediate update | Unselected normalization, already-available capture-state, IR-update rollback and stored-logical-value alternatives. |
| Three in probe | The additional increased-cost arithmetic path is not selected here. |
| `0x01c0683a`, `0x01c06880` | The type36/type37 fingerprint unity-gain alternatives are not selected. |
| `0x0202efc2` | The type8 fingerprint branch for a signed derived value at least 65,536 is not selected. |
| Eleven in `0x0202f02e` | The global IR source has no nonzero global count in these fixtures; its further source/callback gate and effective-size path are not selected. |

The 14 resource gaps were exercised by the prior complete resources01 corpus.
That earlier evidence is retained rather than relabeled as execution by this
integration. Likewise, parameter03 keeps its broader individual-function
evidence. Reaching every direct call site does not imply every path inside its
callee was visited.
