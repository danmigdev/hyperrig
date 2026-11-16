# Native capture warm-up reconstruction

The complete native warm-up body at `0x01c12f20..0x01c13072` now has compilable
C and an independent comparison against its original instructions. Its layer
calculations and reset fallback execute previously recovered bodies internally.
The new code preserves those earlier sources and reports.

The implementation is
[`hyperrig_capture_warmup.c`](../firmware/src/hyperrig_capture_warmup.c), with
the public contract in
[`hyperrig_capture_warmup.h`](../firmware/include/hyperrig/hyperrig_capture_warmup.h).
Required UltraRig notices and the
[third-party license](../third_party/ultrarig/LICENSE.md) remain applicable.
This is an offline reconstruction, not a hardware, audio or timing test.

## Native behavior

The function accepts the existing 228-byte capture context and an optional
address for a three-word result. It returns 1 after warming an eligible capture,
or 0 after resetting an ineligible capture. Eligibility requires:

- A nonzero layer count, descriptor-table address, first-history address and
  first-history length.
- Three channels at context byte 2 and value 32 at context byte 1.
- A nonzero flag at context byte 164.

The native body first clears the first layer's history and its 64-frame mirror,
using the original unsigned count arithmetic. It zeros four dry samples at
`0x01c33ed0` and resets the sample position at context offset 88.

It then calls the actual layer-setup body at `0x01c12a54` for four frames per
layer, with zero dry input and the accumulator at `0x01c33ee0`. After each
nonfinal layer, it replicates that layer's first output triplet through the next
history and its mirror. The final layer uses the one-frame output ring and
mirror at `0x01c33f10`. These numerical calls use the unchanged
[capture processing module](CAPTURE_PROCESSING_RECONSTRUCTION.md).

Finally, the first accumulated triplet fills the head history. If the head
history length is `L = context[84..87] + 1`, the written extent is
`L + min(L, 64)` frames, with uint32 wrap retained. This includes small head
rings. Warm-up does not invoke the head convolution kernel. A nonzero result
address receives that accumulated triplet, before head convolution; zero
suppresses the final copy.

The three result loads and stores remain sequential. A result address overlapping
the accumulator can therefore change later copied components, as in the
original. Tests cover that behavior rather than replacing the copy with an
assumption of disjoint result storage.

An ineligible capture executes the complete original reset at
`0x01c12878..0x01c1296c`, including its auxiliary-history paths, and returns 0.
The result buffer is not written by that fallback. Its contents can still change
if it aliases a history that the reset clears.

## API and supported domain

```c
int hyperrig_capture_warmup(uint8_t context[228], uint32_t optional_output,
    const hyperrig_capture_processing_io *io);
```

The mapping contract and original address tokens are the same as for capture
processing. The existing numerical callback can observe or implement each
kernel boundary; a null callback runs the reconstructed numerical adapter.
The fallback always executes the reconstructed reset internally.

The warm-up body adds no arbitrary layer-count or history-length limit.
Unsigned size and address wrap, dynamic rereads of the first history length,
small head histories and optional output aliasing are preserved. Every accessed
word must be mapped consistently. Context and IO must remain disjoint from the
indirectly accessed storage, and concurrent mutation is outside the contract.
The processing module's ownership and numerical-domain requirements apply
during each four-frame numerical call. The reset contract applies on fallback.

The C APIs add `-200` for invalid pointers, `-201` for missing mappings and
`-202` for an unsupported numerical shape. A numerical callback's error is also
propagated. These are new guard outcomes, not native status values. Earlier
writes can remain after a failure; no rollback is claimed.

One synthetic case sets the next history length to `0xffffffc1`, making its
replication count wrap to zero. Its output-ring geometry exceeds the existing
numerical adapter's domain. That case explicitly scripts the numerical calls
to compare the surrounding control flow. It is counted separately and does not
claim real numerical execution for that geometry. Other wrapped first-history
length and address cases execute actual one-tap numerical kernels.

## Evidence

The newly reconstructed body occupies 338 bytes and contains 118 decoded
instructions. Its original byte SHA-256 is
`3e55c228aaf2045eae93b8270fc452e9cf1ff71b50f0ead73c3e07ea22ec3102`.
The instruction model includes the unchanged processing regions, numerical
kernels and reset body; those dependencies are not new recovered functions.

Final evidence is in the ignored directory `build/reverse-capture-warmup-02`.
The preceding development and build reports remain unchanged.

| Check | Result |
| --- | ---: |
| C versus original-instruction comparisons | 216 |
| Warm-up calls returning 1 / reset fallbacks returning 0 | 170 / 40 |
| Separate normal-processing continuation comparisons | 6 |
| Actual numerical kernel calls / actual reset entries | 442 / 40 |
| Explicitly scripted numerical cases | 1 |
| Warm-up calls on carried state | 9 |
| Decoded instruction steps | 1,819,113 |
| New instructions visited / decoded | 117 / 118 |
| Combined instructions visited / decoded | 2,049 / 2,203 |
| Focused tests | 17 |
| Invalid API / mapping / numerical / callback guard checks | 3 / 14 / 2 / 1 |
| Exact-buffer ASan/UBSan cases | 189 |
| Bound source files / generated artifacts | 45 / 18 |

The single unvisited new instruction is the redundant loop fall-through jump
at `0x01c12ff0`. For the final index, the branch at `0x01c12fa0` enters the last
layer call and then proceeds directly to the head-history fill. The saved layer
count is unchanged. The report records this gap and groups every unvisited
reused instruction by its earlier region. It does not claim full firmware or
exhaustive branch coverage.

Comparisons check the returned native status, every mapped context/arena/scratch
byte, and numerical-call targets, parameter addresses and entry snapshots.
The corpus includes disjoint captures with 1, 2, 3, 4, 8 and 16 layers; all five
layer kernels; signed shifts and saturation; small and wrapped head extents;
wrapped first-history counts and addresses; all eligibility conditions;
auxiliary reset paths; output aliasing; and repeated processing/warm-up/fallback
sequences on carried byte state. Explicit synthetic mappings at zero and the
top of the 32-bit address space exercise address-token behavior. They are not
claims about physical device memory availability.

The sanitizer harness uses exact allocations for descriptors, coefficients,
histories and the optional 12-byte result. Each of its 189 cases performs real
warm-up followed by the reset fallback. The builder also compiles a UBSan host
library and freestanding pi32v2 objects. All 14 dependency object hashes remain
identical between the two completed warm-up builds.

## Provenance and reproduction

The original image is pinned by SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The existing loader authenticates it and its decoded extraction before running
the model. The final report binds all 15 loaded code regions to the reviewed
MINI v4 image, requiring its exact SHA-256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

| Final item | SHA-256 |
| --- | --- |
| `verification.json` | `4ea08bb8bc3844430978d2356136e131f1100369c97fa671c34d0c019f82f357` |
| `build-manifest.json` | `3f39c450ef6e53c11c67006d5b20b8a291f53f1c0a8133fb2866cf39bcaa8b42` |
| Warm-up C source | `5f291704be91c768c4c6196fc24fa8a8958455cfd56c4482fca5da0615cc3208` |
| Warm-up pi32v2 object, 1,568 bytes | `62ed1bc539a12ad3d30634ea9adacb01845a2d0d8adb9193946d191a4565271d` |

All source and artifact bindings were checked after completion. The deterministic
compared output/state stream has SHA-256
`52e7c4fdf7e568683cae0f396181ec99c1643523149d073faffeeb280733e0e3`.

From the repository root, choose an unused output directory:

```powershell
python -B tools/build_capture_warmup.py --output build/reverse-capture-warmup-check --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

On Windows the builder uses the configured Ubuntu WSL distribution. Original
images, decoded inputs and generated evidence remain ignored local files. The
builder performs no device access or firmware installation. Platform scheduling,
audio I/O, invocation by the complete native firmware and hardware timing remain
separate integration work.
