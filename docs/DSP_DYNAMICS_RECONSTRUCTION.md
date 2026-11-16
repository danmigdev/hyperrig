# Reconstructed dynamics configuration and startup connection

The previously external startup service at `0x02030f8e` now has compilable C and
comparisons against its original decoded instructions. A new adapter connects it
to the unchanged DSP initializer. The startup path has one remaining external
service, the platform input word at `0x01c010a6`.

The module also recovers the adjacent configuration getter and meter read/reset
helper. This is configuration and state access, not the dynamics sample processor.
No device, flash, USB, physical sample rate or audio behavior was tested. Earlier
sources, instruction models, tested images and completed reports remain unchanged.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstruction retains the original project's
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md) and notice.
It is not original source code or a firmware image.

## Executable scope and original evidence

The pinned original M5.71 G v2 image has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited loader verifies both that artifact and its actual unpacked
`analysis/firmware/m571_g_app/app.bin`. Flash address `a` maps to decoded offset
`a - 0x02000120`; RAM reset-copy bytes map through CPU flash `0x02056780` for RAM
`0x01c00000`.

| CPU range, end exclusive | Complete body | Instructions | Original bytes SHA-256 |
| --- | --- | ---: | --- |
| `0x02030f8e..0x0203104e` | Dynamics configuration | 53 | `5ca32f6cb6ae181cb21cf04a36bb4fdc9322a49443644666445dd7f4e2529698` |
| `0x0203104e..0x0203106c` | Stored configuration getter | 9 | `cf29fff60ca496d5da718ff617e100409c1fb07cd410882f9572791f2a2e9f99` |
| `0x0203106c..0x0203108e` | Optional meter outputs and reset | 11 | `9f86d6bd67a973b9c58473fb633c2ad154c48663e92e73f8fd3bc3564af37b9d` |

Configuration calls only the recovered scaled exponential at
`0x01c0516e..0x01c05182` and exponential at `0x020285d4..0x02028646`.
Both execute original instructions in the reference model. The existing
[coefficient-generator reconstruction](BIQUAD_GENERATOR_RECONSTRUCTION.md)
provides the integer implementation of rounded binary32 arithmetic; host `float`
and `libm` are not used. The new module does not modify those earlier APIs.

The reset-copy bytes at `0x01c1f7f0..0x01c1f818` have SHA-256
`ca25495ca89ac22d109f1bf553d967fc88013889c9b6e17419d3299b93535bb6`.
They contain threshold halfword `-3`, time halfword `100`, divisor `48000`,
threshold word `8388607`, coefficient word `1` and meter word `0x01000000`.
These are static initialized-image bytes. They do not establish the values at a
later physical runtime point, and the enable byte is not inferred from this copy.

## State and API contracts

The new APIs reuse `hyperrig_dsp_initialization_runtime`, with its seven mapped
regions totaling 12,920 bytes. The complete map remains documented in
[DSP initialization](DSP_INITIALIZATION_RECONSTRUCTION.md). No additional opaque
memory bank is introduced.

| Original location | Portable runtime location | Behavior |
| --- | --- | --- |
| `0x01c1f7f2` | `configuration+30` | Signed threshold halfword |
| `0x01c1f7f4` | `configuration+32` | Signed time halfword |
| `0x01c1f7f8` | `configuration+36` | Unsigned divisor, read only by configuration |
| `0x01c1f808` | `configuration+52` | Computed threshold word |
| `0x01c1f80c` | `configuration+56` | Computed coefficient word |
| `0x01c1f810` | `configuration+60` | Second meter output; reset when requested |
| `0x01c32e1c` | `control+108` | Cleared by configuration |
| `0x01c32e20` | `control+112` | First meter output; preserved |
| `0x01c3448c` | `callbacks+764` | Enable byte |

`hyperrig_dsp_dynamics_configure` interprets the threshold/time arguments as
signed uint32 bit patterns. It clamps them to `-200..0` and `10..2000`, stores the
halfwords and computes the two words. Every nonzero enable argument becomes one;
zero becomes zero. Its 0/1 return matches the original return register.

The threshold path converts the clamped integer to binary32, divides by
`0x41200000`, calls the original scaled exponential, multiplies by
`0x4afffffe`, truncates, and retains the original signed bounds 1024 and 8388607.
The second path converts time and the unsigned divisor, multiplies them, divides
`0xc67a0000` by that product and calls the original exponential. It subtracts that
result from `0x3f800000`, multiplies by `0x49800000`, adds `0x3f000000`, truncates
and clamps to at least one. Each original arithmetic rounding point is retained.
These operations do not establish physical units or calibration.

All positive uint32 divisor words are supported. After clamping time, the
exponential input lies in `[-1600,0]`. The old public exponential API remains
bounded to magnitude 16. A private helper handles the additional negative range
by performing the original repeated addition of `0x3f317218`, using the existing
polynomial after reduction, and applying the original repeated multiplication by
one half. It does not replace the original approximation with an ideal formula.

Divisor zero is rejected with new `-1` before any write. In the original
arithmetic it supplies negative infinity to the exponential's reduction loop;
adding the finite reduction constant cannot make that value reach the loop exit.
The rejected domain has no completed original-execution equivalence claim.

`hyperrig_dsp_dynamics_get` reads the raw enable byte and sign-extends both stored
halfwords, including values outside the setter's clamps. It returns new 0/-1 API
status instead of exposing the native helper's incidental terminal register value.
All three output pointers are required and must be distinct from one another and
the runtime.

`hyperrig_dsp_dynamics_meter` accepts either output pointer independently. The
first copies `control+112`. The second copies `configuration+60`, then replaces
that word with `0x01000000`. An omitted second output leaves it unchanged. The
function returns the original constant 48, including when both outputs are
omitted. Null runtime returns new `-1`; outputs must not overlap runtime or one
another. No meaning beyond the recovered state access is assigned to these words.

## Guarded startup integration

The new `hyperrig_dsp_dynamics_startup` adapter invokes the unchanged recovered
initializer and replaces only its dynamics service callback. The decoded model
instead follows the original native call into `0x02030f8e`; no dynamics result is
scripted.

Original startup sets its guard, calls the still external platform input service,
writes divisor 48077 through the initializer, generates four coefficient sections,
and calls dynamics configuration with `(1, -3, 100)`. This produces threshold word
8103821 and coefficient word 3484, clears `control+108` and enables the byte at
`0x01c3448c`. It then installs the original opaque callback tokens. These observed
integer words come from the original instruction comparison, not a physical test.

A nonzero startup guard preserves all runtime bytes, makes no calls and accepts
null IO. Unguarded startup retains the five `-1280..1280` stored-parameter bounds
from the previous module. The one external callback may synchronously mutate
caller-owned runtime within those bounds. IO is immutable; retained pointers,
overlapping buffers, re-entry and concurrent mutation are outside the contract.
The initializer overwrites a callback-modified divisor with 48077 before running
dynamics, so an initially zero divisor remains valid for this startup path.

Other static call sites reach configuration at `0x02003f22` and `0x020123b4`,
the configuration getter at `0x02003b2a`, `0x02012226` and `0x020123c6`, and the
meter helper at `0x0200f052`, `0x0201035a` and `0x020123d2`. Their enclosing command
or reporting bodies are not reconstructed by this module.

## Independent comparison and limits

The new instruction model subclasses the unchanged initialization model, decodes
the three complete bodies from original bytes and follows both mathematical calls
internally. The only new instruction semantics are register AND and signed
minimum. Dependent parallel packets retain their pre-packet registers, including
the threshold halfword store paired with integer-to-float conversion. Saved
registers, return stacks and mapped writes retain the earlier checks.

The verifier compares every byte in all seven runtime regions, all getter output
words, the defined return values and platform-call arguments/order/runtime before
and after the callback. Its corpus covers every clamped threshold and time value,
signed input extremes, positive divisor extremes, unsigned-to-float rounding
boundaries, raw getters, every optional-output combination, all nonzero guard
bytes, callback mutation and carried calls.

It executes 72 of 73 new instructions. The remaining instruction, `0x02030fee`,
would force the computed threshold to 1024. The preceding signed clamp admits
exactly 201 threshold values; exhaustive original execution yields words from
838860 through 8388607 for all of them. There is no external callback in that
calculation, so this branch cannot be reached in the function's input domain.
The C still retains its original lower clamp. This is a finite-domain argument
for that instruction, not a claim of exhaustive whole-firmware input coverage.

Run the standalone builder with a fresh directory:

```text
python tools/build_dsp_dynamics.py --output build/reverse-dsp-dynamics-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder produces a warning-clean UBSan host library, four freestanding pi32v2
r3 objects, focused tests, an exact-allocation ASan/UBSan harness and hashed
comparison/build reports. MINI binding checks the pinned v4 image SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`
and byte identity of all loaded dynamics/initialization/coefficient/math regions,
both coefficient tables and the dynamics reset-copy bytes. The shared inherited
ISA/binary32 model remains an assumption supported by the earlier evidence;
these comparisons are not new processor measurements.

## Recorded validation

Final output is `build/reverse-dsp-dynamics-01`. The build directory is ignored
and is not a release artifact.

| Evidence | Result |
| --- | ---: |
| Original-instruction comparisons | 2,930 |
| Configuration / getter / meter / startup comparisons | 2,476 / 151 / 27 / 276 |
| New instructions visited / decoded | 72 / 73 |
| Combined loaded instructions visited / decoded | 526 / 580 |
| Internal dynamics calls / external platform calls | 20 / 20 |
| Complete coefficient-producer calls through startup | 80 |
| Mutating platform cases / carried calls | 3 / 10 |
| Maximum instruction packets in comparison corpus | 14,021 |
| Focused original-instruction tests | 15 |
| Invalid-API checks | 30 |
| Additional guarded no-op with null IO | Passed |
| ASan/UBSan exact-buffer cases, including 8 startups | 265 |
| Recorded source hashes / generated artifact hashes | 41 / 8 |

The new target object is 1,848 bytes. The three reused coefficient/initialization
objects are byte-identical to their prior build. Recorded source/artifact hashes
for the previous coefficient, generator, pipeline and initialization modules also
remain unchanged.

| Output | SHA-256 |
| --- | --- |
| `firmware/src/hyperrig_dsp_dynamics.c` | `35a0df4b3a5c7b8df671df26f8c4cef564d323fe7b01f8b760aceebe34e0cd8c` |
| `verification.json` | `fbbfff9ab528e00cfaed26fbf160cb8c15a19679c1085c6b4efbc63947ea1e42` |
| `hyperrig_dsp_dynamics.pi32v2.o` | `c331dcd15598e7396c093344d2283ef5e82b4ffdf64e88ca264f8dbf88fdf9a0` |
| `sanitizers.json` | `d10e56d702b4c8f5b63e7abf04de3fd2d507c5f98991d05a8d8bb1ee2e1cf2d0` |

The 201 native threshold words in increasing clamped-threshold order have SHA-256
`3245300be51491ce90b108b6dfb1b00e266813cc36b4e6aae1affa0b065bca37`.
