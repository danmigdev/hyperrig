# Reconstructed five-section DSP filter chain

The complete caller of the [two Q28 filters](BIQUAD_RECONSTRUCTION.md) is now
reconstructed in C, together with its pending-section update helper. It applies
staged coefficients and flags, runs enabled sections in order, and updates two
timing counters through an explicit clock callback. Both original numerical
kernel bodies execute inside the instruction comparisons; they are not mocked.

Sources: [`hyperrig_biquad_chain.c`](../firmware/src/hyperrig_biquad_chain.c) and
[`hyperrig_biquad_chain.h`](../firmware/include/hyperrig/hyperrig_biquad_chain.h).
The original Required Notice and license are retained. Earlier sources, reports
and firmware images remain unchanged. Coefficient generation and the physical
audio pipeline are separate boundaries.

## Pinned functions

The original G v2 M5.71 application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x01c051a2..0x01c051f0` | Apply one staged section | `343405176fd9c5b1e3212061596ba7d1f8c91dd307fb3cc68078a26e23634682` |
| `0x01c051f0..0x01c0539c` | Apply pending sections, process chain and account time | `c4e6961f2ec2dc039a8054150553d23c523a41a832a89dfe12c067700b202847` |

These execute from the RAM copy starting at `0x01c00000`, loaded from CPU flash
`0x02056780`. Both new functions and both filter kernels are byte-identical in
the reviewed MINI v4 image, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
This binds the reconstruction to that image without establishing target execution.

## Section ownership and updates

The original data areas are:

| CPU address | Modeled contents |
| --- | --- |
| `0x01c33240` | Five staged sections, 44 bytes each |
| `0x01c33320` | Five active sections, 44 bytes each |
| `0x01c32e54` | Five pending-update bytes |
| `0x01c34198` | Optional clock function pointer, represented as an opaque uint32 token |
| `0x01c32dc8` | Smoothed elapsed counter |
| `0x01c34470` | Accumulated elapsed counter |
| `0x01c34488` | Byte cleared when at least one section is enabled |

Each section has the previously recovered 40-byte filter state: five Q28
coefficients, four history words and a residue word. Byte 40 enables the section;
byte 41 chooses the residue kernel when nonzero, otherwise the rounded kernel.
Bytes 42/43 are retained without assigning a meaning.

An update copies only the five coefficient words and bytes 40/41 from staged to
active storage, then clears the section's pending byte. Active input/output
history, residue and reserved bytes are preserved. Staged history/residue are
not copied. The standalone helper performs this copy regardless of whether the
pending byte was set; the caller invokes it only for nonzero pending bytes.

The caller visits sections zero through four, applying pending updates before
reading each section's enabled byte. It retains whether any update occurred.
If all resulting enabled bytes are zero, it returns without audio processing,
clock calls, timing updates or clearing the activity byte. Pending updates have
still taken effect, so disabling the final enabled section is observable.

## Processing and timing order

When any section is enabled, the caller clears the activity byte and reads the
optional clock pointer. A nonzero pointer produces the start-clock call. The
five active sections then process the same sample buffer in order, selecting
their rounded/residue variant independently. Disabled sections preserve their
history and residue; their samples pass through to the next section unchanged.

The enabled/variant flags are read after the start-clock callback. Synchronous
callback changes to those flags, coefficients, histories or samples therefore
affect this block. The elapsed counters and clock token are also mutable at
the callback boundary. This describes observed sequencing, not interrupt safety.

Zero sample count suppresses all numerical kernel calls but does not suppress
pending updates or timing when any section is enabled. After section processing,
the caller reads the clock pointer again. A start callback can remove the second
call by clearing it, or replace its opaque token. There is no time update when
the second pointer is zero.

With a second clock call, all arithmetic below is uint32:

```text
elapsed = end_clock - start_clock                  modulo 2^32
previous = 0 if any section was updated else current elapsed_average
if previous == 0:
    average = elapsed
elif elapsed > previous:
    average = previous + ((elapsed - previous) >> 2)
else:
    average = previous - ((previous - elapsed) >> 2)
elapsed_average = average
elapsed_total = elapsed + current elapsed_total   modulo 2^32
```

Both prior counters are read after the second callback; its changes are observed.
The average moves by a truncated quarter of the difference, so differences below
four leave it unchanged. Applying any pending section resets this smoothing for
the current call, even if the coefficient values happen to match. The total uses
the raw elapsed difference, not the smoothed value. Physical time units and clock
implementation remain outside this reconstruction.

## Coefficient-generation boundary

Static tracing identifies a concrete upstream chain:

- `0x020288d6..0x02028920`, SHA256
  `e4d5de92ac4b351c662d1ba5ccb31affc3dc3a27c111525ecb2693e45d9979b6`,
  accepts section indices zero through four, clamps a signed parameter to
  -12..12, clears its pending byte, calls the producer, then marks it pending.
- `0x02028892..0x020288d6`, SHA256
  `bf388a6f01fe1fc4b8bc43775729599503112bd34e115cc588c344ad58ebf3c6`,
  loads a per-section uint16 table value and signed parameter, converts them to
  float, and calls `0x02028734` with the staged section destination.
- `0x02028734..0x02028892`, SHA256
  `e9d849f6733af1988a38931495d2039c90586e8b759f1db5fd86ae5c3a6dc9eb`,
  uses floating-point arithmetic and additional helpers before calling
  `0x020286a0` to store converted coefficients. That conversion reaches
  `0x01c05182` for float-to-Q28 conversion.

The ten-byte table at `0x0203a55c`, SHA256
`54f4a53a7dfc1bfa17702e31c5d031ce4f6e0dc2f6125463b53ffe00edb415c7`,
contains the little-endian values `100, 400, 1200, 3200, 7000`. These caller and
table observations are static evidence only. The float conversions and producer
are not executed by this verifier, and no specific user-facing effect identity
or sample rate is certified. Reconstructing those numerical dependencies is
the next bounded DSP step.

## API and verification

The portable runtime contains independent staged/active arrays and mapped
control/timing fields. It does not reuse original absolute pointers. The optional
clock callback receives the current opaque token and returns a uint32 clock word.
Runtime, sample and IO storage must be distinct and sufficiently sized. Callback
mutation is synchronous; re-entry, concurrent changes and retained pointers are
excluded.

The new C status is zero on completion, **-1** for invalid API before calls or
writes. The update API accepts section indices zero through four. Processing
accepts zero through 128 int32 samples, with a null sample pointer allowed only
at count zero. A valid runtime is always required. An initially nonzero clock
token requires a valid callback, even when all sections will be disabled.
Incidental original return-register contents are not semantic outputs.

The completed run passed **2,445 C-versus-instruction comparisons**: 1,280 section
updates and 1,165 complete caller executions. All **172 new instructions** and
all **518 combined caller/helper/kernel instructions** were visited. Both kernel
variants execute at every section position. Cases include all `3^5` effective
enabled/variant configurations, every pending mask, every supported block length,
all byte flag values on updates, wraparound and both smoothing directions.

Comparisons check every output sample, all staged/active bytes, pending/activity
bytes, clock tokens and timing counters. They also compare clock-call order and
all mapped state/samples at each call, plus guard and reserved bytes. The total
includes 26 mutating-clock cases and 120 carried sub-block comparisons.

Eighteen focused instruction tests, ten invalid-API checks and one valid
empty/null/no-IO check passed. The host build uses warnings as errors and UBSan.
An ASan/UBSan executable passed **387 exact-buffer cases**. Both target objects
compile for pi32v2 r3: the new chain object is **896 bytes**, and the unchanged
filter object is **628 bytes**. These are relocatable object sizes, not firmware
size, RAM use or latency measurements. No new hardware or audio test was performed.

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing):

```powershell
python -B tools/build_biquad_chain.py --output build/reverse-biquad-chain-new
```

Optionally supply `--mini-image` with the reviewed `hyperrig-mini-v4.app.bin`
inside the workspace. The builder refuses existing output directories and emits
the host library, target objects, sanitizer executable/report, source-hashed
verification report and artifact manifest. Generated files remain outside Git.
The completed local run is `build/reverse-biquad-chain-01`.

The subsequent [coefficient staging/conversion milestone](BIQUAD_COEFFICIENT_RECONSTRUCTION.md)
recovers request ordering, producer argument setup, normalization and Q28 conversion.
The mathematical producer remains external; the chain results above retain their
original scope and evidence.

The later [filter pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md) executes the
reconstructed mathematical generator, staging and this unchanged chain together.
It preserves the reports above and adds comparisons with real generated
coefficients, carried state and deferred requests across blocks.
