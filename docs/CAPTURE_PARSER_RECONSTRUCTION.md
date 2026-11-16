# Native capture parser reconstruction

The complete native A2L1 parser and its 64-bit reader now have compilable C and
comparisons against the original decoded instructions. This preserves the native
228-byte context, allocation ledger, descriptor layout, partial writes and error
ordering. The earlier portable loader remains unchanged and has a different API
and allocation layout. Neither parser alone establishes complete capture audio
or a bootable firmware replacement.

Sources are [`hyperrig_capture_parser.c`](../firmware/src/hyperrig_capture_parser.c)
and [`hyperrig_capture_parser.h`](../firmware/include/hyperrig/hyperrig_capture_parser.h).
Required Notice: Copyright (c) 2026 Manuel Aguirre. The reconstruction preserves
the [UltraRig license](../third_party/ultrarig/LICENSE.md).

## Original evidence

| Function | Start | Exclusive end | Original byte SHA256 |
| --- | --- | --- | --- |
| Complete parser | `0x02031c64` | `0x0203291c` | `b81804d76a1de870455beb1fd784ad5a689742d39d29b47ef7495c4f663566a7` |
| 64-bit reader | `0x01c127de` | `0x01c12850` | `40de5649768ca1529865f7d840be3447a56b95a1a7b8b81e223c9a677636ea6b` |

The pinned Alpha 11/M5.71 G v2 image SHA256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The model verifies that the decoded application equals the unpacked pinned
image before decoding these regions. Flash addresses map from base `0x02000120`;
RAM address `a` maps to application offset
`0x02056780 - 0x02000120 + a - 0x01c00000`.

Both complete regions are byte-identical in reviewed MINI v4, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier also binds the embedded capture and the reset-copy word at
`0x01c1fa18` to both images. That word contains **12**. The API receives it as
an explicit configuration argument; runtime writers and its broader purpose
remain untraced. This static value does not establish its value at every parse.

The two previously compared bias-conversion fragments lie inside this parser.
Their historical reports remain preserved; the expanded
[inventory](REVERSE_INVENTORY.md) counts the enclosing function once.

## API and failure behavior

The API receives 228 initialized context bytes, a three-word ledger
`{arena_token, used_bytes, capacity}`, the source bytes and configuration word.
Address tokens retain uint32 arithmetic. A pure, consistent callback maps tokens
to writable host arena memory. Source, context, ledger, IO and mapped arena
must be disjoint and remain stable throughout the call; concurrent mutation
and callback side effects are outside this comparison domain.

| Result | Original meaning |
| --- | --- |
| `0` | Parsing completed; the caller must still validate arena capacity |
| `-1` | Short input, reader error or trailing bytes |
| `-2` | Unsupported magic/version |
| `-3` | CRC mismatch |
| `-4` | Unsupported dimensions, precision or numerical shifts |

New API result `-200` rejects invalid arguments before effects. New result
`-201` stops before an unmapped arena access; earlier writes survive. These
guards are outside the original fully mapped comparison domain.

Inputs shorter than 44 bytes fail before context or ledger writes. The native
CRC covers every byte except its final four-byte stored value and runs before
magic/version checks. Once header processing begins, later failures can retain
context fields, reserved sizes, descriptor fields and arena writes. A failed
load must not be treated as an atomic rollback.

Every allocation aligns the current used count to eight bytes and advances it
with uint32 wrapping. A zero arena token performs a size query but still updates
context and ledger. Insufficient capacity produces null allocation tokens and
continues calculating requirements. The parser can therefore return zero with
`used_bytes > capacity`; the surrounding dispatch checks capacity separately.

The 64-bit reader performs two distinct four-byte reads. If only four through
seven bytes remain, it consumes the valid low word, retains it, supplies a zero
high word and records an error. This behavior matters to partial writes and
subsequent error precedence.

## Native layout and numerical transformations

Accepted header dimensions are 16-bit weights, 16- or 32-bit activations,
1..16 channels, 1..64 head taps and a nonzero 16-bit layer count. Each layer
requires nonzero kernel width and dilation. The native parser does not impose
the portable loader's limits of 64 layers and 15 kernel taps. Parsing a shape
does not imply that every runtime processing path supports it.

| Context offset | Observed content |
| --- | --- |
| `0..3` | Weight precision, activation precision, channel count and head length |
| `4`, `8`, `10..13` | Serialized rate word, layer count and fraction bytes |
| `14..30` | Sixteen name bytes followed by NUL |
| `32`, `36` | Receptive-field length and explicit configuration word |
| `40..55` | Signed activation minimum and maximum as 64-bit values |
| `56..57` | Rechannel and head shift bytes |
| `60`, `68`, `72..79` | Rechannel weights, head weights and converted head bias |
| `80`, `84`, `92` | Main ring token, ring mask and descriptor-table token |
| `104`, `164` | Scratch requirement as uint16 and optimized-path flag |

Allocation order is descriptor table, rechannel weights, then each layer's
linear matrix, linear biases, packed convolution/mix weights and history ring.
Head weights and the main ring follow. Descriptors have an 80-byte stride.
Preserved padding, unused bias slots and the four-byte tail after each packed
weight block are compared byte for byte.

Convolution weights transpose from `[out][in][tap]` to `[tap][in][out]`, followed
by mix weights. Linear matrices and biases retain their serialized ordering.
Head weights transpose from `[channel][tap]` to `[tap][channel]`.

Fraction calculations preserve the original distinction between signed bytes,
unsigned bytes and byte wrapping before validation. Convolution and final bias
shifts must be 0..31. Bias conversion adds the half-step before an arithmetic
shift with 64-bit wrapping; convolution biases additionally saturate to int32
when channels are at most three. Larger channel counts leave those descriptor
bias slots untouched. The optimized flag additionally requires positive shifts
and the original residual/difference limits; zero shifts can parse successfully
while disabling that flag.

For each layer, let `extent = dilation * (kernel - 1)`. The history allocation
contains `(extent + extra + 128) * channels * 4` bytes, where `extra` is 64 only
when the zero-based layer index equals the configuration word. With the pinned
4,892-byte embedded capture, the parser requires **118,664 bytes** at reset-copy
configuration 12. Synthetic configuration `UINT32_MAX`, which matches no layer,
requires **117,896 bytes**. Both query and load paths are compared; the reset
configuration also has a one-byte-short arena case. These are parser arena
requirements, not total firmware RAM use.

History allocations are not cleared by this parser. Context bytes 88..91,
among other reserved fields, remain unchanged here. The separate
[memory-reset reconstruction](CAPTURE_RESET_RECONSTRUCTION.md) owns that clearing.
The final reader/trailing-byte check occurs after the final context updates.

## Verification and limits

The final run is `build/reverse-capture-parser-03`: **424 comparisons** covering
format/CRC errors, truncated input, both activation precisions, channel/kernel/
head dimensions, layer counts, configuration, allocation alignment and wrapping,
capacity failures, signed fraction boundaries, extreme biases and the embedded
capture. It compares the return value, all context and ledger bytes, the entire
mapped arena including untouched padding, and preserved source/configuration.

The model executes every decoded parser instruction it visits, including CRC
loops and calls to the complete 64-bit reader. Cached instruction classification
does not replace instructions or loops with expected results. There are no
scripted parser-body services.

The corpus visits **1,136 of 1,213 decoded instructions**. All 77 unvisited
instructions are listed in the report and classified by dominating entry
conditions within the documented immutable-input domain:

| Unvisited instructions | Entry condition excluding the path |
| --- | --- |
| 51 | The minimum 44-byte input guarantees the fixed header through byte 35 |
| 4 | The same minimum guarantees the rechannel fraction byte at offset 36 |
| 1 | Channel count has already been checked as nonzero |
| 19 | The convolution bias shift has already been limited to 0..31 |
| 2 | Layer count has already been checked as nonzero |

These classifications are control-flow reasoning, not executed coverage. The
verifier rejects unclassified gaps. It does not claim exhaustive input coverage
or firmware-wide instruction coverage.

Twenty focused instruction tests, five invalid-API checks, one mapping-guard
case and **646 exact-buffer ASan/UBSan cases** passed. Host compilation uses
warnings as errors and UBSan. The C source also compiles to a 3,868-byte pi32v2
r3 relocatable object. This is not a linked image or a measured runtime budget.
The build manifest records hashes of the object, host library, sanitizer
executable and reports; the verification report records every source dependency.
All 20 recorded source hashes and five generated artifact hashes matched after
completion. The final comparison report SHA256 is
`57687b92f136273c91285a0e7d5099909235456c9b44d6b668c20eb98f9650a0`;
the target object SHA256 is
`58b9616a1679e80c54fee08e4495c515fab1b0edd474863082c88b2880d2ddeb`.

The instruction model maps at most 1 MiB of source and 2 MiB of arena per call.
Larger calculated requirements can be queried without allocating that arena.
The mapper must provide every requested access in a load comparison. Hardware
execution, timing, audio output and physical memory behavior are untested.

With the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_capture_parser.py --output build/reverse-capture-parser-new
```

Optionally pass `--mini-image` with the reviewed v4 application inside the
workspace. Output must be a new directory under ignored `build/`; previous
results are preserved. The builder creates no flashable image and opens no device.

The subsequent [native loading integration](CAPTURE_NATIVE_RECONSTRUCTION.md)
now connects this parser and memory reset to the dispatch/container path.
[Native processing orchestration](CAPTURE_PROCESSING_RECONSTRUCTION.md) has a
separate instruction comparison with actual numerical kernels. Joining its
processing state to loading and recovering warm-up remains work. The earlier
portable [three-channel engine](NATIVE_RECONSTRUCTION.md) remains separate evidence.
