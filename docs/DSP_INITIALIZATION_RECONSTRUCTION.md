# Reconstructed DSP initialization and guarded startup

The subsequent [dynamics reconstruction](DSP_DYNAMICS_RECONSTRUCTION.md) replaces
the configuration-service boundary with its original numerical body. That newer
startup adapter retains only the platform input service as external. The evidence
below remains the independent initializer milestone.

The complete initializer, its slot and four-filter reset helpers, and the guarded
startup caller now have compilable C and comparisons against decoded original
instructions. The previously static **48000 to 48077 divisor path** executes in
the reference model. It writes 48077 before generating four sections through
the recovered mathematical producer.

Two startup dependencies remain explicit synthetic calls. This is an offline
reconstruction of the identified bodies, not a physical startup, rate, audio or
complete-firmware validation. No device was accessed or firmware changed.

Sources: [`hyperrig_dsp_initialization.c`](../firmware/src/hyperrig_dsp_initialization.c)
and [`hyperrig_dsp_initialization.h`](../firmware/include/hyperrig/hyperrig_dsp_initialization.h).
The Required Notice and third-party license are retained. Earlier DSP sources,
models, tested images and completed reports remain unchanged.

## Executable scope and provenance

The original G v2 M5.71 image has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The inherited loader validates both that original artifact and its complete
decoded `app.bin` before executing instructions. CPU flash address `a` maps to
offset `a - 0x02000120`. RAM code maps through the reset copy starting at CPU
flash `0x02056780`, corresponding to RAM `0x01c00000`.

| CPU range, end exclusive | Complete recovered body | Instructions | SHA256 |
| --- | --- | ---: | --- |
| `0x01c0539c..0x01c053bc` | Binary32 to signed Q16 conversion | 9 | `95ddece179840d812709c19cf3cf0364cfcf4d756d058705cbff611e3d19d286` |
| `0x02028968..0x0202898e` | Parameter to gain-word conversion | 10 | `662ac4568114c993ca2697ad1db0b3a23101671e226285eee2bbf4ffe7f507d6` |
| `0x0202898e..0x020289d4` | Second-table coefficient setup | 22 | `7bc1097065c4147dd75204862b37b017ac2d9954fd892c88692ad5d78184b5d0` |
| `0x020289d4..0x02028a34` | Four-section and gain reset | 31 | `41a9e76d9be98d088dae7479ae9778febf0ed877d4187e4fa2393714912176fe` |
| `0x020290cc..0x02029112` | Reset routes associated with one slot | 23 | `302d1d26620e629caffac6d3f4049ff05d93253caaf4001fdeb139b26c45ffb6` |
| `0x02029112..0x020291f8` | Complete broader DSP initializer | 70 | `39b63bd3121f79194eb1abfc1d65129b8b7dcf12be22a358e2360ed69371dbc7` |
| `0x020291f8..0x02029204` | Bind two callback words | 4 | `57a18969dc362b42cb5f6a09886bcce04973b55b7bc037ab1c7f22017fdca8c6` |
| `0x020024ec..0x020025ca` | Complete guarded startup helper | 51 | `5b6ea9d65dde89e84288c1f27080bed8f56d79378c033a2e571190983f2a396e` |

The new second setup table at `0x0203a566..0x0203a570` contains five unsigned
halfwords `(0, 150, 650, 2000, 4500)`; its SHA256 is
`fe845985ec7e666fcd26dd0d255b41a84b7863843d04287ac14ab38b19da76a6`.
The recovered reset only uses indices one through four.

The reset-copy divisor at `0x01c1f7f8..0x01c1f7fc` contains 48000, SHA256
`66d85f78876e0fab490f733649bf372210d32034677b958fd4b2575589f65798`.
The startup helper passes 48077 to the initializer. These integer words are
image and executed-model observations; their relationship to a physical sample
rate remains unmeasured.

All eight new bodies, every loaded mathematical/conversion dependency, both
setup tables and the reset-copy divisor match reviewed MINI v4 byte for byte.
That image has SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

## Portable runtime mapping

The new API uses seven disjoint mapped regions totaling 12,920 bytes. Larger
byte arrays deliberately retain untouched fields and gaps so comparisons can
detect accidental clearing or overwritten neighbors. They do not claim that
every field inside those ranges has an established meaning.

| Original RAM base | Bytes | Portable field |
| --- | ---: | --- |
| `0x01c1f7d4` | 68 | Configuration bytes, gain word at zero and divisor at +36 |
| `0x01c2249c` | 4 | Startup guard and three preserved neighbor bytes |
| `0x01c2c220` | 7,680 | Sixteen records of 480 bytes |
| `0x01c2e5a0` | 3,584 | Eight route records of 448 bytes |
| `0x01c32db0` | 640 | DSP control bytes and signed stored parameters |
| `0x01c33030` | 176 | Four 44-byte filter sections |
| `0x01c34190` | 768 | Callback words, counters and preserved surrounding bytes |

These four sections occupy a different bank from the previously recovered
[five-section pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md). They reuse the same
44-byte coefficient/history format and mathematical generator. This milestone
does not execute their surrounding sample-processing caller or infer an effect
identity from their table values.

## Slot reset and initializer ordering

The slot-reset helper scans all eight routes. For an enabled route whose byte
identifier equals the supplied unsigned slot, it clears record byte zero,
increments record byte four modulo 256, and clears that route's enabled byte
at control offset `210 + route`. A disabled or nonmatching route is preserved.
Slot values below sixteen also clear control byte `316 + slot`; other values
skip that final store. A uint32 value above 255 cannot match a route's byte ID.

The broader initializer first stores the supplied divisor at `0x01c1f7f8` and
the second input word at control +48. It then visits slots zero through fifteen,
executing the complete reset helper, clearing each 480-byte record's byte +2
and clearing the corresponding callback-table word at `0x01c343d8 + 4*slot`.
It does not unconditionally clear routes assigned to IDs above fifteen.

It clears `0x01c3443c`, control byte 6 and the word at control +24 before calling
the four-section reset. After that reset, it clears control bytes 14 and 15 and
initializes six lanes:

- Halfwords at control +368 through +390 and words at +392 through +412 become zero.
- Twelve words at control +496 through +540 become `0x8000`.
- Six-byte fields at offsets 174, 186, 192, 198 and 204 become zero.
- The six bytes at +180 become 255; six halfwords starting at +230 become zero.

Finally, it clears control byte 7 and bytes 16 through 19, then writes bytes
20 and 21 as one and two. Stored signed parameters at +218 through +226 remain
unchanged. Tests compare all mapped bytes, including unrelated preserved fields.

## Four-section setup, reset and gain

For setup index one, the coefficient producer receives mode zero. Index two
uses mode one; indices three and four use mode two. The frequency-like input
is the corresponding unsigned second-table value converted to binary32. The
signed parameter is converted to binary32 and multiplied by raw word
`0x3dcccccd`; the width input is `0x3f333333`. The names of these mathematical
inputs do not establish physical units.

Setup invokes the complete previously recovered producer at `0x02028734`,
including scaled exponential, trigonometric approximations, square-root
iterations, normalization and Q28 conversion. No coefficient result is supplied
by a script. Setup retains history, residue and the two reserved section bytes.

The reset begins by clearing control byte 1. It reads four signed halfwords at
control +220, +222, +224 and +226, generates sections one through four in order,
and clears each section's four history words and residue. Coefficient/flag
writes precede those history clears. Reserved bytes survive.

It then reads the signed halfword at control +218. Zero produces the exact gain
word 65536 without exponential or Q16 calls. Otherwise the helper converts the
parameter to binary32, multiplies by `0x3dcccccd`, executes the original scaled
exponential and converts the result to signed Q16. The reset clears control +32,
stores the gain word at `0x01c1f7d4`, and sets control byte 28 to one.

The Q16 helper multiplies by `2^16`, adds a sign-selected half-unit bias and
truncates to a saturated signed 32-bit integer. Binary32 rounding occurs after
each floating operation, so this is not an ideal real-number rounding formula.
Both NaN signs/classes become the arithmetic NaN during multiplication and
ultimately return `INT32_MAX`. Negative infinity returns `INT32_MIN`.
The C uses the unchanged integer implementations of binary32 arithmetic;
the reference uses the pinned ISA's separate exact-rational instruction models.

The new bounded gain/setup interfaces accept signed parameters from -1280
through 1280, keeping reused exponential inputs within their verified domain.
Reset and initialization check the five stored signed halfwords before effects.
This domain contains the setter clamp ranges visible at `0x02028936`, but that
setter body is not executed or claimed recovered here. Q16 accepts every raw
binary32 word; divisor and initializer input words accept every uint32 value.

## Guarded startup and remaining service bodies

A nonzero byte at `0x01c2249c` returns immediately, without inspecting parameters
or invoking a service. With a zero guard, the complete helper executes:

1. Set the guard to one and call `0x01c010a6` for the platform input word.
2. Invoke the complete initializer with divisor 48077 and that returned word.
3. Call `0x02030f8e` with `(1, -3, 100)`; its return is ignored.
4. Bind the words `0x0201a864` and `0x0201a96a` at control +52/+56.
5. Store eleven original callback tokens in their original order.

| Destination RAM word | Stored token |
| --- | --- |
| `0x01c343c4` | `0x0201a9ac` |
| `0x01c34458` | `0x0200e40e` |
| `0x01c34194` | `0x0201a9dc` |
| `0x01c3446c` | `0x0201a9ea` |
| `0x01c343d4` | `0x0201aa6a` |
| `0x01c34434` | `0x0201aac2` |
| `0x01c34198` | `0x01c04862` |
| `0x01c343d0` | `0x0201aace` |
| `0x01c341c0` | `0x01c047de` |
| `0x01c341a0` | `0x01c0486c` |
| `0x01c3444c` | `0x01c04882` |

The platform-input body at `0x01c010a6` and separate configuration body at
`0x02030f8e` remain explicit synthetic boundaries. The latter has API token
`HYPERRIG_DSP_DYNAMICS_CONFIGURE`; its internal mathematical/state effects are
not recovered by this module. Stored function words are opaque tokens, not
host function pointers, and their target bodies are not called during these tests.

Boundary callbacks may synchronously mutate the mapped runtime within the
documented parameter domain. Later original reads and writes determine which
changes survive. Tests cover parameters changed before initialization, guard
changes, divisor changes before/after the initializer, and callback-table writes
subsequently replaced by startup's fixed tokens. Thus the modeled initializer
write of 48077 does not imply an arbitrary subsequent callback cannot change it.

The normal unmodified-service path is tested from the pinned reset divisor
48000 through startup and four actual generated sections using 48077. A second
call with the guard still set changes nothing and calls no service. Guard clearing
by a synthetic callback also exercises a later complete startup on carried state.

The C status interfaces return new zero/-1 success/invalid-API values rather
than exposing incidental native return-register contents. Q16 and the gain
output preserve their original numerical values. Invalid API calls fail before
writes/callbacks. IO and runtime must be distinct; re-entry, concurrency and
retained pointers are excluded. A guarded no-op accepts null IO.

## Verification and artifacts

`build/reverse-dsp-initialization-01` passed **4,529 comparisons**:

| Entry point | Comparisons |
| --- | ---: |
| Q16 conversion | 2,346 |
| Gain conversion | 415 |
| Second-table setup | 1,124 |
| Four-filter reset | 32 |
| Slot reset | 258 |
| Complete initializer | 80 |
| Callback binding | 3 |
| Guarded startup | 271 |

The run executed **1,608 complete coefficient-producer calls**, eighteen startup
boundary calls, three mutating-service scenarios and eight carried startup calls.
All **220 of 220 new instructions** were visited; combined coverage was
455 of 507 loaded instructions. Unvisited inherited instructions belong to the
larger previously verified coefficient/staging corpus, not the new initializer
scope. This is instruction coverage, not exhaustive proof over every state.

Cases include every binary32 exponent and both signs, special values and rounding
boundaries; every integer setup parameter -120 through 120 at each index; gain
parameters -240 through 120; extended bounded parameters and divisor edge words;
route-byte counter wrap; IDs outside the sixteen-slot initializer loop; all 255
nonzero guards; repeated startup; and before/after-boundary snapshots of all seven
mapped regions. Surrounding C guard words are also checked. The largest original
execution took 3,930 decoded packets, not measured processor cycles.

Fifteen focused instruction tests, **81 invalid-API checks**, a guarded null-IO
check and **257 ASan/UBSan exact-buffer cases** passed. Host compilation uses
warnings as errors and UBSan; all three objects compile for pi32v2 r3.

| Object | Bytes |
| --- | ---: |
| Existing coefficient conversion/staging | 1,860 |
| Existing mathematical generator | 3,556 |
| New DSP initialization | 2,824 |

Both dependency objects are byte-identical to the prior pipeline build. The new
target object SHA256 is
`c3e2c899074d1ade6a98f8de871b05cc54bf1971c3a9b96c57cc31c9819496c6`.
These are relocatable object sizes, not linked firmware size, RAM use or latency.
The new C source SHA256 is
`eabed2763502e2ffe1c0bb0e002fe14a5a0838631335e81e3334f9bafd1532a3`.
The completed comparison report SHA256 is
`f22a093dea4c327e7c541cbc4036c55600d034443919738812cc8f602f1e1bc4`.
All 34 source hashes and seven artifact hashes matched after completion.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_dsp_initialization.py --output build/reverse-dsp-initialization-new
```

Optionally provide `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder requires a fresh directory under ignored `build/` and
preserves existing outputs. It records sanitizer results, comparison evidence
and artifact hashes. It creates no flashable firmware and accesses no device.

Later [dynamics](DSP_DYNAMICS_RECONSTRUCTION.md) and
[startup input/four-section processing](DSP_AUDIO_PATH_RECONSTRUCTION.md)
reconstructions close both service bodies in this startup path. The latter
executes startup and subsequent sample processing on carried state without
scripted services. The callers that schedule startup, physical units, surrounding
audio routing, final linkage and hardware/audio behavior remain unvalidated.
