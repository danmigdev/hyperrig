# IR installation, numerical preparation and deferred reads

This reconstruction closes the IR installer boundaries used by the earlier
[IR loader](IR_LOADER_RECONSTRUCTION.md). Direct installation, gain calculation,
quiet-tail trimming, length selection, deferred-slot switching and the slot read
callback now execute recovered C and original decoded instructions. The original
callback at `0x0201ad4c` reads and validates stored samples; it does not process an
audio block.

Required Notice: Copyright (c) 2026 Manuel Aguirre

The reconstructed bodies derive from UltraRig firmware and retain its
[PolyForm Noncommercial license](../third_party/ultrarig/LICENSE.md). These are
reconstructed sources, not the author's original sources. Existing firmware,
source files and completed verification reports remain unchanged.

## Complete recovered bodies

Ranges use exclusive ends. The ten newly recovered bodies contain 724 bytes and
267 decoded instructions.

| Original range | Recovered behavior |
| --- | --- |
| `0x02029248..0x02029268` | Signed budget gate, wrapping integer scaling, rounding and cap |
| `0x02029268..0x0202928a` | Length conversion between two nonzero/zero format modes |
| `0x0202928a..0x020292ee` | Sample limit, budget limit and aligned tail limit |
| `0x020292ee..0x0202930e` | Length query using the configured trimmed tail |
| `0x020294ce..0x0202957e` | Signed-16 sample peak, 64-bit energy and quiet-tail trimming |
| `0x0202957e..0x020295d8` | Direct buffer installation, gain and trimmed length |
| `0x020295d8..0x02029604` | Deferred slot/identity installation |
| `0x02029604..0x0202962a` | Length query without tail trimming |
| `0x0201ad4c..0x0201ade8` | One-based slot read, chunking and CRC validation |
| `0x01c05eb0..0x01c05ec6` | Signed metadata clamp to `[-60000, 20000]` |

The numerical model also executes the previously recovered `scaled_exp`
(`0x01c0516e..0x01c05182`) and `exp` (`0x020285d4..0x02028646`) instructions.
The C implementation reuses the unchanged
[coefficient math](BIQUAD_GENERATOR_RECONSTRUCTION.md), including exact binary32
conversion, division and exponential arithmetic. No mathematical result is
supplied by a scripted callback.

New adapters compose the unchanged five IR ownership/load bodies at
`0x02008972..0x02008c28`. Calls to `0x0202957e` and `0x020295d8` become internal
in both implementations. Existing asset-header, record, CRC and chain helpers
continue to run inside the original-instruction model.

## Recovered state and calculations

The new runtime stores six little-endian words from `0x01c32db0`:

| Original offset | Meaning in these bodies |
| --- | --- |
| `+60` | Direct sample-buffer address, or zero |
| `+64` | Configured sample count |
| `+68` | Boolean format selector |
| `+72` | Deferred one-based slot, or zero |
| `+76` | Deferred identity/CRC |
| `+80` | Trimmed sample count |

These six words have a separate 24-byte C view. The earlier selection runtime
already owns routing bytes elsewhere in the same original global structure;
the new view does not duplicate those bytes. The binary32 gain word resides at
`0x01c1f7dc`, and the existing loader owns the callback word at `0x01c3441c`.

Direct installation stores the address and count, clamps the signed metadata,
converts it to binary32, divides by binary32 `1000`, and calls `scaled_exp`.
That helper multiplies by the binary32 constant `0x3debc8e3` before its recovered
exponential. This is consistent with gain expressed in thousandths of a dB;
the metadata is not used as a sample-rate value in these bodies. Direct
installation then normalizes the format selector, clears the deferred slot and
identity, and stores the trimmed length. A null address stores trimmed length
zero, even when the configured count is nonzero.

Tail trimming reads signed little-endian 16-bit samples. It calculates the peak
absolute amplitude and the sum of squared amplitudes in 64 bits. All-zero input
retains its complete length. Otherwise, it removes trailing samples while both
conditions remain true:

```text
cumulative removed energy <= total energy >> 20
current absolute amplitude * 3162 <= peak absolute amplitude
```

At least one sample remains. Equality is removable, and the first sample that
exceeds either threshold remains. A null pointer returns the supplied count
without reading samples. The instruction model preserves add/subtract carry
and the sign extension of the PSR carry bit; the pinned ISA evidence identifies
PSR bit 1 as carry, with subtraction carry meaning no borrow.

The budget helper gates on signed positive input, evaluates the original
wrapping `value * 48 + 64`, shifts by seven, clamps the resulting nonzero
quantity to `1..32`, then multiplies by 128. The format converter retains the
original 18/9 padding. Final length selection caps at 4096, applies the budget,
and, when a shorter nonzero tail exists, rounds its converted length to a
64- or 128-sample boundary. The verifier includes wrapping inputs; it does not
replace this arithmetic with unbounded host integers or infer a sample rate.

## Ownership and storage behavior

Attach locks, performs actual configuration, unlocks, commits loader state, then
frees a different previous handle. The gain and trimmed length are therefore
observable by the unlock service before the loader commits its new handle.

The deferred setter requires a nonzero slot, a nonzero callback word and a
nonzero configured count. It clears the direct address and stores the slot and
identity, retaining the count, format, gain and trimmed length. It does not
validate the slot's upper bound. The read callback separately rejects slots
outside `1..8` before raising storage priority.

For a valid slot, the read callback raises priority and probes the existing
dual-format asset header, with maximum payload 8152 bytes. It requires the
requested identity and exactly twice the requested sample count. Payload reads
use at most 2048 bytes each, followed by the original CRC calculation and its
256-byte polling boundaries. It returns `-1` for header/identity/length
rejection, `-2` for a payload-read failure and `-3` for a CRC mismatch. Partial
payload writes remain visible after failure; priority is restored on every
path that raised it. A zero-length accepted record still receives CRC validation.

An original failed header read can leave a private stack length unwritten. The
original callback loads that value before taking its failure exit, but never
uses it for payload access or an observable return. The instruction fixture
initializes this private frame with several arbitrary byte patterns to check
that boundary. The C body avoids reading that unused uninitialized value.

## API and remaining boundaries

[The header](../firmware/include/hyperrig/hyperrig_ir_installation.h) documents
the host API, and [the implementation](../firmware/src/hyperrig_ir_installation.c)
contains the recovered numerical bodies and ownership adapters. Nonnull sample
buffers contain at most 4076 samples. A standalone read needs at least twice its
count in writable storage; composed loading retains the previous 8152-byte
backing-storage requirement and allocation-growth guard. One nonzero opaque
address identifies that allocation, independently of its host pointer.

Synchronous read/service callbacks may mutate mapped runtime or backing bytes.
They must preserve the IO contract and storage lifetime, with no concurrent
reentry, overlapping runtime/buffer storage, or retained private stack pointers.
Invalid host calls return `-200`; an unexpected allocator token or a changed
record larger than the allocation is outside equivalence and returns `-201`.

Physical reads, allocation/free, locking, scheduler priority/poll, activity,
notifications, effect ownership and effect refresh remain explicit services.
No flash write or erase service is invoked. These services are synthetic in the
verification and do not contact a device.

The next numerical boundary is convolution construction at
`0x0202962a..0x02029728` and its callers. That body consumes the recovered length
helpers, calls the size helper at RAM `0x01c123fa`, obtains storage through the
allocator at global offset `+52`, and calls `0x020318a8` with coefficient
producer `0x02031542`. Its kernel objects, allocation layout, producer and
audio-processing bodies are not reconstructed by this milestone. The
`0x02029728` mode-selection wrapper, temporary-state path at `0x0202976a`, and
effect-refresh service `0x020298ce` also remain beyond this module. No
placeholder convolution result stands in for those bodies.

## Reproduction and provenance

The completed run is `build/reverse-ir-installation-01/verification.json`:

- **1,143** original-instruction/C comparisons, including **54,000** sample
  inputs, **19** cases with callback mutations and **4** calls carrying state
  from the previous comparison.
- **267/267** new instructions visited; **306/306** including the two reused
  numerical helpers. The complete composed model visits **639/1,627** decoded
  instructions. That larger denominator includes older routing/storage bodies
  outside these calls and is not a firmware-completion measure.
- **23** focused instruction tests, **23** invalid-host-API checks and **2**
  separate API guards for allocation token/size violations.
- AddressSanitizer and UndefinedBehaviorSanitizer pass for **4,077** exact buffer
  lengths, covering every count from zero through 4076, plus **15** partial-read
  failures.
- Host and pi32v2 compilation pass with warnings treated as errors. All **17**
  selected code regions match the unchanged MINI v4 image. All **65** recorded
  source hashes and **13** generated artifact hashes were rechecked.

The new pi32v2 object is 3,348 bytes. Key SHA-256 values are:

| Artifact | SHA-256 |
| --- | --- |
| `hyperrig_ir_installation.c` | `fe54f3cf629405d6ea824b5472603a9cdc2e38026308c7cea20464b018d76f75` |
| `hyperrig_ir_installation.pi32v2.o` | `2e2dddb502c9789bf12a205d5dff7299129b012a640b58e5cdf0eb10d1c9950b` |
| `verification.json` | `1e75b0e7c8312edb1da02c4db0c357fc21a7f9d33b600f103eedb5e5a6a9cd50` |
| `build-manifest.json` | `16cf30817209a859119f108c97295973778068e80520b0af0889a7d8f4104810` |

Run the new builder with a fresh ignored output directory:

The verifier currently reads transitive source-name lists from
`build/reverse-ir-loader-02/verification.json` and
`build/reverse-biquad-generator-01/verification.json`. Those earlier report
inputs must exist. The completed run had both; rebuilding from only a fresh
checkout is not established here. The 17-region MINI binding is the explicit
scope above; inherited asset/storage/selection bindings remain in earlier reports.

```powershell
python -B tools/build_ir_installation.py --output build/reverse-ir-installation-next --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles an undefined-behavior-sanitized host library, nine pi32v2
objects, an AddressSanitizer/UndefinedBehaviorSanitizer exact-buffer executable,
the focused instruction tests and the original-versus-C comparison. It produces
no flashable firmware. The report records hashes of the complete transitive
source set, original region bytes and host library; the build manifest records
every generated artifact hash. Source reports and generated binaries remain
under ignored `build/` directories.

The authoritative original application has SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The optional unchanged MINI v4 image has SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
Its ten new, two numerical dependency and five ownership/load regions are
checked byte-for-byte, including RAM-copy mapping.

This is offline reconstruction and numerical verification. It is not a hardware
test, audio test, device-flashing result or proof of complete IR convolution.

The later [convolution construction](IR_CONVOLUTION_RECONSTRUCTION.md) executes
effect allocation, both coefficient producers, resampling, FFT, fixed-point
packing, reset and object publication with 479 further comparisons. The
runtime consumer, accelerator access and enclosing audio task remain open.
