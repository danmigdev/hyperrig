# Reconstructed generated-coefficient filter pipeline

The recovered coefficient generator, staging requests, pending-section updates
and five-section numerical chain now run together in an offline comparison with
carried state and sample blocks. A new C adapter performs a bounded sequence of
requests followed by processing. Every constituent original entry point executes
decoded instructions in the reference model; the batch adapter itself is new
orchestration, not a claimed original firmware function.

The divisor investigation also distinguishes two values: its reset-copy word is
**48000**, while an identified startup call supplies **48077** to the function
that writes it. These are image/code observations, not measured physical rates.

Sources: [`hyperrig_biquad_pipeline.c`](../firmware/src/hyperrig_biquad_pipeline.c)
and [`hyperrig_biquad_pipeline.h`](../firmware/include/hyperrig/hyperrig_biquad_pipeline.h).
They retain the original Required Notice and license. All earlier DSP sources,
reports and tested images remain unchanged.

## Divisor initialization and writer evidence

The original G v2 M5.71 application SHA256 is
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Its reset copy maps CPU flash `0x02056780` to RAM `0x01c00000` for `0x2030c`
bytes. Within that copy, RAM `0x01c1f7f8` contains little-endian bytes
`80 bb 00 00`, the integer 48000.

Static tracing identifies a later write path:

```text
0x020024ec: enter a startup helper with a byte guard at 0x01c2249c
0x020024fc: call 0x01c010a6
0x02002502: r1 = returned r0
0x02002504: r0 = 48077
0x0200250a: call 0x02029112

0x02029114: r2 = 0x01c1f7f0
0x0202911a: [r2+8] = r0
0x02029122: [0x01c32db0+48] = r1
```

Thus, **if this guarded startup path runs**, it replaces the divisor with 48077.
The function at `0x02029112` also clears broad slot/effect state and calls
`0x020290cc` and `0x020289d4`. This milestone does not execute that complete
initializer or infer the meanings of all its other writes. The writer search
is not an exhaustive proof that no other direct or indirect writer exists.

The coefficient producer's known read remains `0x02028754`, loading
`[0x01c1f7f0+8]` before unsigned-to-binary32 conversion. The new adapter takes
the divisor as an explicit immutable input per batch. Header constants identify
both observed values without silently choosing a hardware configuration.

The pinned static windows are:

| CPU range, end exclusive | Evidence only, not executed here | SHA256 |
| --- | --- | --- |
| `0x01c1f7f8..0x01c1f7fc` | Reset-copy divisor word | `66d85f78876e0fab490f733649bf372210d32034677b958fd4b2575589f65798` |
| `0x020024ec..0x02002510` | Guarded startup call supplying 48077 | `cb9bc7cb5e20d2a36bb98a5ef80cedfddf0178928ca3fed7322b14ed10cae714` |
| `0x02029112..0x020291f8` | Broader initializer containing the divisor write | `39b63bd3121f79194eb1abfc1d65129b8b7dcf12be22a358e2360ed69371dbc7` |
| `0x01c026ce..0x01c026e4` | Native caller passes a 128-word block to the chain | `522f48badc3d6e55f7102bd1a3a41f607d7371e33aeda035b73e410650819484` |

The last window loads r1=128 at `0x01c026da`, places the r5 buffer in r0, and
calls `0x01c051f0` at `0x01c026de`. Its preceding call to `0x01c10e06` and the
surrounding larger processing function remain outside this integration test.

## Newly recovered parameter getter

`0x02028920..0x02028936`, SHA256
`d18b64a70ccc1df29111241f5206ac2d1074b7a932c6409130bb5d680fc37779`,
contains seven instructions. It returns the sign-extended stored parameter byte
for unsigned indices zero through four; any other index returns zero. It does
not clamp, generate coefficients, increment the request counter or change state.

The new C getter writes that value through an output pointer and returns status
zero. Null control/output pointers return -1 before writes. These statuses and
the output-pointer interface are new C API conventions.

## Request-to-sample integration

The batch adapter validates its arguments before any calls or writes, stages
zero through sixteen requests in order, then runs zero through 128 int32 sample
words through the existing active chain. Repeated section indices are allowed:
the final request determines that staged section's coefficients and parameter,
while every request increments the shared counter. Ignored unsigned indices
also increment the counter, as recovered previously.

The executed path is:

```text
request -> signed clamp -> stored parameter / pending clear / average reset
        -> original setup and full mathematical producer
        -> normalization and binary32-to-Q28 conversion -> pending set

block   -> apply pending coefficients and flags while retaining active history
        -> process each enabled section in order
        -> retain updated history/residue and account elapsed counters
```

The [generator](BIQUAD_GENERATOR_RECONSTRUCTION.md),
[staging/normalization](BIQUAD_COEFFICIENT_RECONSTRUCTION.md),
[chain caller](BIQUAD_CHAIN_RECONSTRUCTION.md) and
[two numerical kernels](BIQUAD_RECONSTRUCTION.md) are reused without editing
their verified sources. The reference model invokes those separate original
entries on the same carried memory state. No mathematical or numerical kernel
is replaced by a scripted result.

Changing coefficients preserves the active section's four history words and
residue. Disabling the final active section still applies pending updates but
then passes samples through without clock calls. Zero-frame blocks apply pending
updates and can account time without invoking a numerical kernel. All of these
transitions are checked after actual coefficient generation.

The indirect clock service remains the existing explicit test boundary. Twelve
test requests occur synchronously during clock calls, with the complete original
staging/generator path executed at that point. Because the active-update pass
has already finished, those requests remain pending for a later processing call.
Their new coefficients do not replace the current block's active coefficients.
The next zero-frame or nonempty block applies them while retaining history.

Clock scripts also exercise counter mutation, clock-token replacement/removal,
and selection of either numerical kernel at each section position. Those flag
mutations are explicit test inputs, not observations that the firmware's real
clock callback performs them. With ordinary generated flags, section zero uses
the residual kernel and sections one through four use the rounded kernel when
enabled. Both arithmetic bodies execute on real generated coefficient values.

Comparisons cover every output sample, staged/active byte, parameter, pending
flag, counter, divisor word, history/residue and reserved byte. Clock comparisons
include the token and complete mapped state/sample contents before and after
each synchronous callback. Guarded C buffers and unchanged request arrays are
also checked. The wrapper's buffers and IO storage must be distinct; callback
re-entry into the batch/chain, concurrent mutation and retained pointers are
outside the supported domain.

## Verification and artifacts

The completed run `build/reverse-biquad-pipeline-01` passed:

- **1,698 comparisons**: 1,287 parameter reads and 411 integrated blocks.
- **11,459 output sample words**, 1,208 original staging executions and
  1,398 original numerical-kernel calls.
- **99 carried blocks**, 803 clock calls, and 12 requests made during clock
  callbacks; these are subsets of the totals above.
- Every block length from zero through 128, every stored parameter byte at
  each section, every clamped parameter, all 32 enabled-section masks,
  repeated/ignored requests and counter wrap.
- Divisor inputs 0, 1, 8000, 44100, 48000, 48077, 96000 and UINT32_MAX,
  including preservation of the original special-value paths.

All **7 new getter instructions** and **812 combined instructions** were visited.
No inherited instruction was left unvisited in this run. The number includes
sixteen original functions across the generator, staging, caller and numerical
kernels; it does not mean the complete firmware has been recovered.

Fifteen focused tests, ten invalid-API checks and **387 ASan/UBSan exact-buffer
cases** passed. The host build uses warnings as errors and UBSan. All five
pi32v2 r3 objects build successfully:

| Object | Bytes |
| --- | ---: |
| Numerical kernels | 628 |
| Active-chain caller | 896 |
| Coefficient conversion/staging | 1,860 |
| Mathematical generator | 3,556 |
| New pipeline adapter/getter | 716 |

The four dependency objects are identical to their previously verified builds.
The new pipeline object SHA256 is
`41f28e78428a5464730ee1f7a0ddeec3cd370316f37fe0dfedaffbb0804020e1`.
These are relocatable object sizes, not complete firmware sizes, RAM-use or
latency measurements. Earlier documented `memset` and compiler-runtime division
dependencies still require resolution when linking a complete target image.

The new C source SHA256 is
`f701d45065c70262058b16fad67fceeab7283df442b985091ae3996c61886f93`.
The completed verification report SHA256 is
`91a7daf4de26f3ac200f2c6ad613d3fa4570c4a3046752ace07f9505969bbfce`.
Its 36 source hashes include the unchanged earlier modules and independent
decoder/ISA models. Source and artifact hashes still match the earlier chain,
coefficient and generator reports.

All sixteen executed regions, the setup table and all four static windows are
byte-identical in reviewed MINI v4, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This establishes image binding for the comparison, not live execution.
No hardware or audio test was performed; no firmware was flashed or changed.
Physical rate, block scheduling, surrounding audio routing, final linkage and
filter stability/latency remain unvalidated.

Use the [native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_biquad_pipeline.py --output build/reverse-biquad-pipeline-new
```

Optionally provide `--mini-image` with the reviewed MINI v4 image inside the
workspace. The builder requires a new directory under ignored `build/` and
preserves existing reports. Generated libraries, objects, executables and reports
remain outside Git.

The next configuration boundary is the broader initializer at `0x02029112` and
its reset helpers; the surrounding block caller is a separate execution boundary.
Recovering those bodies would connect the pinned startup evidence to a more
complete runtime initialization and scheduling model.
