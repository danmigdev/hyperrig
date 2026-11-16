# Reconstructed preset loader, bindings and reports

Eight more original functions are reconstructed in portable C. They cover the
top-level preset loader, action snapshots, conversion of absolute effect bindings,
timing/report arithmetic and byte comparison. Integrated control actions now run
through the existing availability checks and [preflight](PRESET_PREFLIGHT_RECONSTRUCTION.md)
into this loader. The application handler at `0x020092fa` remains an explicit
callback; its DSP implementation is not executed by this component.

The later [application reconstruction](PRESET_APPLICATION_RECONSTRUCTION.md)
executes the complete handler's reuse/rebuild control flow and asset/query
dependencies, with 1,775 comparisons. It establishes that the handler returns an
effect failure count while retaining separate capture/IR statuses. The loader's
frozen callback-based comparison remains unchanged; joining these callers and
their downstream DSP implementations is still required.

Sources: [`hyperrig_preset_loader.c`](../firmware/src/hyperrig_preset_loader.c) and
[`hyperrig_preset_loader.h`](../firmware/include/hyperrig/hyperrig_preset_loader.h).
The original Required Notice and license are retained. Earlier sources and
verification reports remain unchanged. No firmware image is produced or installed.

## Original functions and MINI binding

The G v2 M5.71 reference application has SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.

| CPU range, end exclusive | Recovered behavior | Function SHA256 |
| --- | --- | --- |
| `0x0200ca7e..0x0200cb3c` | Top-level preset loader | `f396922c03e8dfd2024e76975bd5af03c91ebcb37969e32503579a66e92a87e2` |
| `0x02003a4e..0x02003aaa` | Canonical action snapshot | `e67b83e3066b0b39fc97648d43aa7e035fbf5900890a7d47dd3a356832c38b08` |
| `0x0200c9f4..0x0200ca7e` | Rewrite absolute effect bindings | `98fdea0d6f77fb96edec6d87c43a356ada5356583a913de409292d7bb9cd2762` |
| `0x0200c7ce..0x0200c806` | Position to type/occurrence | `24bab31055a098f2b40b70e0c2b863ac3916abeb543c4cebb36263e51ac326e3` |
| `0x02002bd8..0x02002bec` | Scale the calibration word | `30c0c12cfb3add81653bb701a656a0321550a10607d56f7731eb96a41971ea7f` |
| `0x020031be..0x020031d4` | Calculate elapsed ratio | `731f92b2037973eed49afd391cc5e7a274b106413fabde6ba920ca7f8c39e23c` |
| `0x02009dd0..0x02009e14` | Pack and emit load report | `2cfa7427a6896a584314ce18603c41a1cfa4b743829469d34a9f95cbeb16e35e` |
| `0x020282bc..0x020282f4` | First differing unsigned-byte comparison | `2629c8815cb3dadd1bab28610ac721b12a5b55978ed3cb68a8190d30da6a8c23` |

All eight new regions and the twenty-four earlier function regions are
byte-identical in the released MINI v4 application, SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The prior conversion curve and both memory-library regions also match. This
binds the reconstruction to that image without establishing target execution.

## Loader sequence and success meaning

Within the original valid timing domain, the loader performs this sequence:

1. Capture a clock value, then run preflight with a local header buffer.
2. If preflight returns nonzero, return **-1**. All four detailed preflight
   failures collapse to this result. Its completed and partial writes remain.
3. Capture the end clock and the scaled calibration, then capture a third clock
   and the word at state offset 4092 for the application report.
4. Call `0x020092fa(preset, first_output, second_output)`. In the original caller,
   the two distinct output words are at stack offsets 4 and 0. The loader does
   not read either word afterward.
5. Write the requested preset ID to global offset 92, **without testing the
   application return value**. Retain that value for the final notification.
6. Snapshot the current action records, compare with the saved snapshot when
   state byte 736 is nonzero, rewrite absolute bindings, and conditionally
   refresh the saved snapshot as described below.
7. Emit report notification 26. Then, if state byte 740 is zero, emit notification
   6 with the preset ID and application return value. Return **0**.

Notification 26 is not suppressed by byte 740. That byte is read after the report
callback, so the report can change whether notification 6 is sent. Callback
changes after the current-preset write are retained; there is no second commit.

A zero loader result establishes completion of this caller sequence. It does
not establish a zero application result, successful DSP application or durable
storage. The application return value's deeper meaning still requires tracing
the application implementation. Conversely, a preflight failure is reached
before this caller's application call and current-preset write.

## Binding rewrite and canonical snapshots

The twelve action records occupy global offsets 236..271 as three-byte records:
`[type, argument, auxiliary]`. The last two bytes use the existing C action-tail
fields; the full 36 bytes participate in snapshots and rewrites.

The rewrite helper first checks whether any record is an absolute effect action:
type 8 with auxiliary 255. If none exists it returns zero without writes.
Otherwise it flattens chain 0 followed by chain 1, retaining at most sixteen
positions. As in the previous [selection model](SELECTION_RECONSTRUCTION.md),
duplicates remain and absent/out-of-range raw effect slots contribute type zero.

For each absolute action whose argument identifies an existing flattened position:

- Replace argument with the effect type at that position.
- Replace auxiliary with the number of preceding positions with the same type.
- Count one rewrite, including a conversion to type zero.

An out-of-range position retains its original record. If at least one record
was rewritten, all 36 temporary action bytes are copied back. The helper returns
the number of rewritten records. Its position-conversion dependency clears both
outputs for a negative or out-of-range position, and counts duplicates of zero
exactly like other types.

The snapshot helper first copies all records, then canonicalizes each type-8
record whose auxiliary is not 255:

```text
[8, argument, auxiliary] -> [8, auxiliary | 128, argument]
```

Absolute bindings and other action types are copied unchanged. High auxiliary
bits are preserved by the OR; they are not rejected or masked away.

The saved canonical snapshot is 36 bytes at state offset 4012. After application,
the loader computes a snapshot **before** rebinding. It updates the saved snapshot
only when all three conditions hold: state byte 736 is nonzero, the saved bytes
match that pre-rewrite snapshot, and at least one binding was rewritten. The new
saved bytes come from a fresh snapshot of the rewritten records. A mismatching
saved snapshot is retained. No meaning beyond this observed comparison/update
role is assigned to byte 736.

## Timing and report arithmetic

Let `calibration` be the uint32 word at global offset 44. The recovered rate is:

```text
rate = ((calibration * 1000) modulo 2^32) / 6
preflight_time = ((end_clock - start_clock) modulo 2^32) / (captured_rate / 1000)
elapsed = ((now - application_start) modulo 2^32) / current_rate
```

All divisions are unsigned integer divisions. In particular, the preflight
formula divides the rate by 1000 before dividing the clock difference; combining
these into a different algebraic expression can change truncation or overflow.
The report's elapsed helper reads calibration after its clock callback. The
loader's preflight calculation uses the earlier captured rate instead.

The report helper samples state word 4092 **before** calling the elapsed helper.
It saturates elapsed to 65535 and the wrapped difference from the previously
captured counter to 32767. It emits through `0x02002d10`:

```text
notify(26,
       ((preflight_time << 8) | preset) modulo 2^32,
       (min(counter_difference, 32767) << 16) | min(elapsed, 65535))
```

The preset and preflight-time inputs are not independently masked to byte-sized
fields before packing. Counter changes during the report's clock callback do not
replace the counter value already sampled. The counter's writers, physical clock
units and hardware division-by-zero behavior are outside this verification.

## API, integration and boundaries

`hyperrig_loader_runtime` embeds the unchanged preflight runtime and adds the
36 saved action bytes and four counter bytes. `hyperrig_loader_io` contains the
existing storage callbacks plus an application callback. That callback receives
two distinct borrowed output pointers and may synchronously mutate caller-owned
runtime state. Output words can remain unwritten because this loader never reads
them; their values are not persistent state in this model.

Direct loader, preset-step, action, timer and edge entry points execute the
reconstructed loader internally. Navigation therefore distinguishes availability
from preflight: a CRC-valid record with an unsupported old layout can be marked
available, fail loading, and cause the search to advance to another preset.
Clock, physical reads, storage preparation, priority, polling, application and
the remaining scene/effect services retain explicit external boundaries.

The snapshot, binding, comparison, rate, elapsed and report helpers also have
bounded entry points for independent verification. Original helpers with no
semantic return value use new C wrapper status returns; those incidental original
register values are not treated as results. Byte comparison returns the first
unsigned-byte difference, including its sign, and is bounded to 36 bytes here.
Unlike the memory moves below, its original instruction body is executed.

New API guards are separate from recovered behavior:

- Runtime/IO entry points require the full callback set and the selection domain:
  chain counts at most ten, current scene 0..3 or a negative int32 bit pattern.
  Loader/control entry points require initial rate at least 1000; elapsed/report
  require nonzero rate. Invalid calls return -2 before calls or writes.
- Snapshot, rebind and binding helpers use -1 for invalid API. Snapshot only needs
  valid source/output pointers; binding requires a count at most sixteen and
  distinct output pointers that do not overlap its type list.
- Byte comparison uses -256 for invalid API, outside the original byte-difference
  range. Null pointers are accepted only for zero length.
- Callbacks must preserve the selection/storage domains and required timing
  divisors. A callback invalidating timing returns the new error -3. Earlier
  calls/writes remain: the captured-rate check occurs before application, while
  a report-time failure can occur after the current-preset update. These guards
  are not comparisons with original hardware exception behavior.

Snapshot output may be the saved-action field but must not overlap its action
source. Re-entry, interrupt concurrency, retained callback pointers and other
unsupported buffer overlap remain excluded.

The previous bounded `memset`/`memmove` contracts are retained. The move contract
also covers the two 36-byte action copies between globals and temporary stack
storage. Those library instruction bodies are not interpreted or counted as
covered. The application implementation is scripted, not reconstructed here.

## Verification

The completed run passed **4,635 C-versus-instruction comparisons**:

| Operation | Comparisons |
| --- | ---: |
| Loader | 141 |
| Action snapshot | 3,328 |
| Binding rewrite / position conversion | 178 / 357 |
| Calibration rate / elapsed ratio / report | 306 / 45 / 31 |
| Byte comparison | 222 |
| Integrated preset step / action / timer / edge | 13 / 12 / 1 / 1 |

Checks compare semantic results, all previously mapped bytes, saved actions,
the counter word and ordered external arguments plus mapped state at each call.
The application output pointers are normalized to their original caller-stack
offsets 4 and 0. Private stack/header bytes and unused application outputs are
not compared as persistent state.

Coverage includes all auxiliary-byte values at all twelve action positions,
all serialized action types, duplicate/absent effects, clock wraparound, report
saturation, preflight failures, nonzero application results, snapshot-match
conditions, notification suppression and navigation after a load failure.
Six consecutive navigation steps and 94 mutating-boundary cases are subsets of
the total. Twenty-five focused interpreter tests, 21 invalid-API checks, an empty
null-pointer comparison and a dynamic zero-divisor guard check also passed.

All **227 new instructions** were visited. This run visited **889 of 1,130
combined instructions**, not every earlier component path. Earlier reports retain
their separate coverage. The combined host library builds with warnings as errors
and UBSan. All six components compile for pi32v2; the new relocatable object is
3,216 bytes, not a linked firmware size or runtime measurement. None of these
target objects has run on the pedal. There is no new hardware, audio, durable
write, physical clock-unit or DSP application validation.

## Reproduce and continue

Use the pinned [local sources](LOCAL_SOURCES.md) and
[native build prerequisites](NATIVE_RECONSTRUCTION.md#building-and-comparing).
On Windows, the builder uses WSL Ubuntu:

```powershell
python -B tools/build_preset_loader.py --output build/reverse-preset-loader-new
```

Optionally pass `--mini-image` with the reviewed `hyperrig-mini-v4.app.bin` inside
the workspace. Outputs include the host library, six target objects,
`verification.json` with source hashes and `build-manifest.json`. Existing output
directories are refused. Generated artifacts remain outside Git. The completed
local run is `build/reverse-preset-loader-01`.

The [asset/application extension](PRESET_ASSETS_RECONSTRUCTION.md) now independently
reconstructs its header/identity, descriptor and routing-layout helpers. These
are not yet connected to an executed application handler. The
[IR extension](IR_LOADER_RECONSTRUCTION.md) adds IR payload checks and ownership.
Next, recover capture loading, working-to-live state conversion, effect/routing
application and the meanings of its result/output words. Storage preparation/cache invalidation
and the writers of state word 4092 also remain to be traced. See the
[roadmap](REVERSE_ROADMAP.md); three-switch bank integration and Alpha 13 feature
implementation remain separate work.
