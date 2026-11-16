# IR convolution construction reconstruction

This milestone recovers the complete original IR construction path from the
effect allocation request through coefficient production, FFT conversion,
fixed-point packing, history reset and publication. The numerical bodies execute
in the instruction comparison; they are not coefficient fixtures or scripted
FFT services. Allocation and freeing remain synthetic services.

This is reconstructed UltraRig code, not the author's original source.

Required Notice: Copyright (c) 2026 Manuel Aguirre

License: <https://polyformproject.org/licenses/noncommercial/1.0.0>

See [the preserved license](../third_party/ultrarig/LICENSE.md),
[the required notice](../third_party/ultrarig/NOTICE.md) and the preceding
[IR installation reconstruction](IR_INSTALLATION_RECONSTRUCTION.md).
No firmware image, device, USB transport or audio stream was changed or tested.

## Evidence and complete function boundaries

The original input remains `m571_g_app.bin` from the pinned Alpha 11 v2 archive:

`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`

`NativeProgram` checks both that input and the complete decoded `app.bin` before
the new decoder loads any functions. Flash uses base `0x02000120`. RAM code is
mapped from the original load at flash `0x02056780` to `0x01c00000`.

| Function | Original range, end exclusive | Instructions |
| --- | --- | ---: |
| Allocation size | `0x01c123fa..0x01c12414` | 10 |
| History reset | `0x01c12414..0x01c12446` | 21 |
| Effect preparation and publication | `0x0202962a..0x02029728` | 87 |
| Signed16 sample getter | `0x020313dc..0x02031404` | 12 |
| Format conversion/resampling | `0x02031404..0x02031542` | 106 |
| Windowed coefficient producer | `0x02031542..0x020315b8` | 40 |
| Binary32 copy producer | `0x020315b8..0x020315c8` | 7 |
| Cosine polynomial | `0x020315c8..0x02031626` | 22 |
| Sine polynomial | `0x02031626..0x0203167a` | 20 |
| Complex phase generator | `0x0203167a..0x020316f4` | 42 |
| 128 point complex FFT | `0x020316f4..0x020317c8` | 76 |
| 256 point real-spectrum conversion | `0x020317c8..0x0203187c` | 58 |
| Saturating Q31 conversion | `0x0203187c..0x020318a8` | 12 |
| Complete convolution constructor | `0x020318a8..0x02031bf8` | 287 |

These are 14 complete new function regions, 2,406 code bytes and 800 decoded
instructions. There are no embedded data spans inside those boundaries.
The earlier five budget/length helpers and the original window cosine
`0x02028646..0x02028676` execute internally without changing their previous
sources or evidence.

Nine signed resampling coefficients at `0x0203be2c..0x0203be50` are immutable
data outside the function regions:

```text
338786260, -106304302, 56405688, -33342174, 19931383,
-11511092, 6180000, -2946008, 1235701
```

Their 36 original bytes have SHA-256
`5e4544bfe9c57a8a3dc7f9db243232a0362dca09497be8503c418e379879165c`.
The verifier binds all 20 executed function regions and these bytes to the
unchanged MINI v4 image, SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Byte identity does not establish a new hardware or audio result.

## Recovered numerical path

The signed16 getter returns zero for negative or out-of-range indices. Otherwise
it converts the sample to binary32 and applies the supplied gain. Resampling
first scales the installation gain by `1/32768`. Equal boolean format flags use
the direct sample path. Differing flags use the nine original coefficients,
converted by `2^-30`, with separate doubling and halving index patterns. The
even-position doubling path includes its original factor of one half. Negative
edge indices become unsigned words and then return zero through the signed
getter. No sample-rate label is inferred from the format flag.

The window producer reads `(length, fade, mode)`. Within the final `fade` samples
it multiplies by a raised-cosine value with denominator `fade + 1`, preserving
the original binary32 operation order. The alternative original producer copies
binary32 words verbatim, including NaN payloads and signed zero.

The constructor generates its complex phase tables with the recovered sine and
cosine polynomials. It converts each partition of at most 128 real coefficients
to binary32 at `1/128`, pads to 256 values, executes a 128 point complex FFT and
then forms the 129 complex bins of a real spectrum. Both the bit-reversal swaps
and each butterfly's multiply/add/subtract order are preserved.

The constructor chooses a common power-of-two scale from the largest component
and the largest sum of component magnitudes across partitions. Both original
thresholds and the 48 iteration cap remain. Spectra are truncated to signed
integer words and stored by bin, then by partition. Phase tables use the
separate saturating Q31 helper. Signed zeros, infinities, NaNs, unordered
comparisons and the original float-to-integer saturation are included in the
comparison corpus. C uses integer implementations of binary32 arithmetic; the
independent instruction model uses the pinned ISA's rational float semantics.
No host `libm` result is used as an expected output.

## Object layout and ownership

For output length `N`, `P = min(max((N + 127) >> 7, 1), 32)` in the original
wrapping size helper. Allocation size is `7248 + 2064*P` bytes, from 9,312 to
73,296 bytes. The complete constructor API accepts `N <= 4096`; it returns zero
for zero count, object token or producer. Source installation views contain at
most 4,076 signed16 samples. The 32 partition case executes the complete
constructor and both real producers.

Let `H = 2616 + 2064*P`. Original address fields retain their 32-bit token values
inside the byte-backed object:

| Header offset | Value or destination relative to object base |
| --- | --- |
| `+0`, `+4` | Active marker `1`, partition count `P` |
| `+8`, `+12` | Reset history indices |
| `+16` | Selected scaling exponent |
| `+20` | `2616`: bin-major integer coefficients |
| `+24` | `2616 + 1032*P`: float spectra, then cleared frequency history |
| `+28` | `552`: padded 256 value input block |
| `+32` | `H`: complex FFT scratch |
| `+36` | `H + 1024`: 128 word permutation |
| `+40` | `H + 1536`: Q31 phase table for 128 |
| `+44` | `H + 2048`: phase table for 256, converted in place to Q31 |
| `+48` | `H + 3080`: cleared 256 word time history |
| `+52` | `H + 4104`: retained binary32 phase table for 128 |
| `+56..+535` | Twenty groups of three complex Q31 phase pairs |
| `+544`, `+548` | Zero status and boolean original global flag |

Unwritten bytes, including `+536..+543`, `+1576..+2615` and the final 16
allocation bytes, retain their initial values. The instruction model evaluates
both halves of parallel packets against the old registers. This matters for
the chained pointer stores in the constructor.

Preparation reads the effective and raw lengths before allocation. Allocation
target and free target come from original global offsets `+52` and `+56`.
Synchronous callbacks may mutate the mapped runtime. The later raw-length
reload, fade selection, old-object lookup and free-target reload preserve the
original timing. Success frees the previous object when applicable, then
publishes the new allocation, halfword capacity, constructor pointer and output
length, and clears only that effect's status word.

Original status `-3` means the allocator is absent or returns zero. Mode zero
requests a zero-byte allocation; if that allocation succeeds, preparation frees
it and returns `-1`. A zero-length constructor also frees the new allocation
and returns `-1`. Publication follows the final free callback, so callback
mutations of published fields are overwritten in the same order as the original.

## API and service boundaries

Runtime, IO, parameters, result, source, copy, object and output storage must
have nonoverlapping spans and remain live throughout the call. One synthetic
allocation token maps to the writable object. The original effect array is
represented by disjoint views of offsets `+76..+91` and `+288..+295`; earlier
modules retain their own nonoverlapping fields. The comparison checks 120,250
mapped bytes plus the owner scalar across 27 regions.

The public reset API requires coherent constructor layouts: 1..32 partitions,
the exact derived frequency/time-history pointers and adequate aligned,
nonwrapping object storage. This prevents histories from overlapping header
words. An independent review identified why this matters: the original reset
reloads the time-history pointer after clearing frequency history. Arbitrary
self-overlapping headers are outside the declared API, and explicit malformed
layout checks reject them before writes.

New status `-200` denotes an invalid API/mapping request before effects. New
`-201` denotes a service contract violation, such as an unexpected allocation
token, source growth beyond the mapped signed16 domain or a missing rollback
free target; completed service effects remain. These guards are tested
separately and are not represented as original firmware statuses.

The only active external boundaries in this construction corpus are allocation
and freeing. No allocator implementation, durable write, flash service,
convolution processing kernel, scheduling, DMA, USB, Bluetooth or physical
audio operation is modeled as having executed. The wrapper beginning at
`0x02029728`, the copying constructor wrapper at `0x02031bf8`, relocation at
`0x02031c16` and downstream runtime convolution remain separate follow-up work.
The runtime consumer at `0x01c12064..0x01c123fa` accepts 128 sample blocks and
uses the recovered object fields. It includes a software numerical path and an
accelerator path through `0x01c124a8`/`0x01c1245c`, which touch `0x01ee0400`.
Those bodies were traced only; no accelerator or processing result is claimed.

## Reproduction and validation

New maintained files:

- `firmware/include/hyperrig/hyperrig_ir_convolution.h`
- `firmware/src/hyperrig_ir_convolution.c`
- `tools/ir_convolution_machine.py`
- `tools/verify_ir_convolution.py`
- `tools/build_ir_convolution.py`
- `tests/test_ir_convolution_machine.py`
- `tests/ir_convolution_sanitize.c`
- this document.

After obtaining and decoding the pinned inputs using the existing repository
instructions, run:

```powershell
python -B tools/build_ir_convolution.py --output build/reverse-ir-convolution-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

Use a fresh output directory. The builder produces a host shared library with
undefined-behavior checks, all ten dependency objects for pi32v2, an address/
undefined-behavior sanitizer executable, comparisons and a hashed manifest.
Its explicit source manifest does not read earlier ignored verification reports.

The new C module is the only changed numerical implementation. All nine earlier
source modules are compiled unchanged, and their nine pi32v2 objects match the
previous installation build byte for byte. All 47 overlapping source bindings
match that earlier frozen report. Original instructions are decoded from
the input image; no reconstructed C calculation supplies the instruction
model's expected coefficients. The corpus compares semantic return values, the
complete mapped state and ordered allocation/free arguments and state at every
service boundary. Void functions' incidental return registers are not API
results.

One instruction remains deliberately unexecuted: `0x020319be`, an unconditional
jump after the phase-table loop's bottom check. The counter starts at zero,
increases by one, and the top check at index 128 jumps to the fixed Nyquist pair.
Consequently the bottom check never receives 129. The verifier binds this
entry-invariant proof to the exact five original instructions; it does not
manufacture a mid-function entry to inflate coverage.

The frozen output is `build/reverse-ir-convolution-02`:

| Validation | Result |
| --- | ---: |
| C/original instruction comparisons | 479 |
| Original producer calls executed internally | 199 |
| Original instruction steps | 7,506,096 |
| Cases with synchronous callback mutation | 12 |
| Calls carrying earlier object/runtime state | 7 |
| Focused expectation tests | 23 |
| Invalid API checks before effects | 49 |
| Service/mapping violation checks | 3 |
| ASan/UBSan exact-allocation constructions | 190 |
| ASan/UBSan exact-buffer producer calls | 285 |
| ASan/UBSan preparation cases | 31 |
| New instruction coverage | 799 / 800 |
| Coverage of the 20 declared new/reused regions | 907 / 916 |
| Coverage across all loaded inherited decoder regions | 907 / 2,442 |
| Audited source/artifact hashes | 59 / 14 |

The eight additional unvisited instructions in the inherited length helpers are
`0x02029262`, `0x02029270`, `0x02029282`, `0x02029284`, `0x02029286`,
`0x020292a6`, `0x020292d0` and `0x020292e2`. They remain visible in the joined
coverage list. The previous installation corpus and its evidence remain
separate; no overall firmware coverage percentage is inferred.

All nine previous pi32v2 dependency objects are unchanged. The new
`hyperrig_ir_convolution.pi32v2.o` is 9,312 bytes, SHA-256
`be6deab9c0ed58c5ad529abb5432f3e100cadaa739b40a357f20473aa891fada`.
It is a relocatable research object, not a flashable image.

Frozen verification report SHA-256:
`d23c27ea4ebfcc9cf17003c3d521cbbef9ad4417e77a75b1704c4e68c3dd9f59`.

Frozen build manifest SHA-256:
`ca5e2a3b13351050d9210f0f7e4661180455971c4239aca006af387ba81cfb1d`.

Reconstructed C SHA-256:
`260a733288a1f9a95853364cb4e94ec70131e85e96cf11f5945db1d4ea74aa1a`.

The final source and artifact bindings were rechecked after completion.
Independent source/instruction review found no remaining mismatch within the
declared domain after the reset-layout guard correction. All earlier verified
modules, images and reports remain unchanged.

The later [IR runtime reconstruction](IR_PROCESSING_RECONSTRUCTION.md) executes
these constructor objects through the full 128-sample software convolution path.
It adds sixteen complete bodies and 399 comparisons, covering all 2,266 new
instructions. Accelerator control executes against explicit simulated register
responses and output; this is separate from physical accelerator validation.
The installation/effect caller still needs to be joined to that runtime.
