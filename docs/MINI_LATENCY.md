# MINI timing and latency

The real trial with **all nine selected effects enabled** measured **2.395 ms mean internal block processing** and a **2.526 ms largest observed block duration**. The original A2 model remained enabled. These are nominal firmware-timer measurements, **not ADC-to-DAC latency**.

The root controller performed [trial03](../build/mini-fx-latency-03/report.json) on 2026-11-16. Its SHA256 is `379a39fc8098fafc84ab35eb49ecb947406e57a87691038abc80c4cfd93d0729`. [The independent replay report](../research/mini-latency-hardware.json) verifies the saved native TX/RX, source hashes, unchanged measurement epochs, actual effect readback, and restoration. The analysis itself performed no device or browser I/O.

| Trial03 enabled effects, alongside A2 | Three fresh STG windows | Mean of window averages, ms | Largest observed duration, ms |
|---|---|---:|---:|
| 0 | 5323, 5324, 5325 | 2.145517 | 2.427967 |
| 4 | 5330, 5331, 5332 | 2.210511 | 2.296300 |
| 8 | 5337, 5339, 5340 | 2.326361 | 2.461583 |
| 9 | 5344, 5345, 5346 | 2.394822 | 2.526133 |

Each accepted window covers 512 blocks. Three fresh, nonmixed windows were used per configuration, after waiting at least two window increments. The nine-effect window means were 2.395100, 2.394433 and 2.394933 ms. Fresh CLKSTATE before/after each interval reported 360 MHz, converted at 60000 ticks/ms; the timer has not been externally calibrated.

The selected chain was **P: gate, compressor, EQ, boost, overdrive, hum filter, envelope filter; Q: tremolo, chorus**. Every instance read back `on=1`. Parameters and routing are retained in the independent report: gate threshold -90 dB, compressor makeup 0/wet 25%, EQ bands -3 dB, boost -1 dB, envelope/chorus wet 25%, other controls at the tested defaults. Output gain was -12 dB during effect measurements. This is a chosen progressive stress chain, not a proof of the globally largest possible chain or all 37 catalog types.

Across the nine-effect observation, A2 nproc advanced 2439, AUD input/output each 4876 and block count 2438; overrun, underrun, full, timeout, cancellation and skipped deltas were zero. Reported AUD.err/DSP.rc and clip observations were zero. These finite observations do not establish acoustic quality or a worst-case bound; stimulus and playing were not controlled.

Trial03 used 157 native commands, 49718 captured RX bytes and 38 explicit mutations. The final PLOAD0 restored preset 0, scene A, capture 0, no IR, gain 0/0 and an empty effects chain; full readback and original UI refresh passed, and the temporary guard detached. No preset was saved over or deleted during the stress test.

### Earlier trial02: admission and measurement are distinct

[Trial02](../build/mini-fx-latency-02/report.json), SHA256 `9e3278a5cd5bfae31fc1cf4e60729511008c1a8f18a62c30f0f9206f0b6beb08`, measured 0/4/8 enabled effects. At eight it observed 2.326072 ms mean and 2.400217 ms maximum. Nine instances were later admitted, but the tenth enable returned `ERR FXE not enough CPU`; the runner stopped before a nine-instance measurement. Its result therefore provides no nine-effect latency. Restoration and detach passed. Trial03 selected the first nine steps explicitly, avoiding a tenth addition and adding the final nine-instance measurement.

### Historical A2-only baseline

The real A2-only baseline has **2.1451–2.1455 ms average internal block processing**, with a **2.2584 ms maximum** across three fresh reporting windows. These are nominal conversions from the firmware timer. **No effects were enabled, and ADC-to-DAC latency was not measured.**

The underlying observations are [mini-v3-latency-baseline-01.json](../analysis/hardware/mini-v3-latency-baseline-01.json), captured by the root controller on 2026-11-16 at 05:59:57–06:00:00 UTC. [mini-latency-audit.json](../research/mini-latency-audit.json) records input hashes, the actual FX catalog, calculations, and 16 instruction fragments checked byte for byte against both the original G firmware and the installed v3 candidate. This audit performed no device or browser I/O.

| Fresh `STG win` | `blk` average / maximum, ticks | Nominal average / maximum, ms |
|---|---:|---:|
| 2398 | 128708 / 133440 | 2.14513 / 2.22400 |
| 2399 | 128731 / 135502 | 2.14552 / 2.25837 |
| 2400 | 128706 / 131917 | 2.14510 / 2.19862 |

The model was A2, 23 layers, 3 channels; `FXS` had zero effect instances. `AUD ovr/und/full/err` remained zero. Queue waiting averaged 17.53–17.58 microseconds, with a 31.60 microsecond maximum, using the same nominal conversion. These observations establish activity and internal timing, not sound quality.

## What the firmware measures

| Field | Proven meaning | Important limit |
|---|---|---|
| `STG lat` | Time from completion of a 128-sample input block to audio-worker start | Excludes collecting the block and ADC conversion |
| `STG blk` | Worker start through processing and publication to the output ring | Excludes output-ring waiting and DAC/filter delay |
| `STG in/pre/eng/post/out` | Original processing-stage durations | `eng` includes A2; individual stage maxima may come from different blocks |
| `STG win` | Increments when the next 512-block average/max window is published | A repeated window is stale for a new measurement |
| `STG isr` | Average/max of the handler at `0x01C03278` over 1024 invocations | A separate window from the other `STG` fields |
| `T nproc` | Completed A2 process calls, each handling two 64-sample jobs | Generic `FXS posts/takes=0` is valid for this A2 path |
| `T last/max/avg` | A2 call duration; average is cumulative | `STAT` clears `T.max` after reporting it |
| `RS lat/eng/blk us` | The first 16 triples after a nonzero audio-mode start | **Historical, not rolling**; changing effects does not refresh them |
| `NIVEL`, `LVL ci/co` | Peaks, clipping and limiter observations | `ci/co` are clip counts, not processed-sample counts |

The three baseline replies contain identical `RS` samples, also present in the earlier UI trial. The producer stops recording when its counter reaches 16 (`0x01C02C52..7A`); audio-mode initialization resets that counter (`0x0200544E..5A`). `STAT` does not rearm it. There is no need to restart audio to obtain fresh measurements: use advancing `STG win` instead.

The worker timestamps the completed input block at `0x01C02FF4..FFE`, computes queue waiting at `0x01C01EC2..EEC`, and records block duration at `0x01C02B84..90`. Output consumption occurs later in `0x01C03100...`. Adding `lat + blk` still omits input acquisition, output waiting and codec latency.

## Timer conversion

The timer helper reads `TIMER3_CNT` at `0x00010704`. The pinned WL82 SDK identifies this register, and the original conversion function at `0x02002BD8` returns:

```text
nominal ticks/ms = nominal CPU MHz × 1000 / 6
nominal ticks/us = nominal ticks/ms / 1000
```

The preceding real `CLKSTATE` replies reported 360 MHz, giving 60000 ticks/ms. This audit assumes that nominal clock remained unchanged during the baseline; the baseline file does not itself contain a fresh `CLKSTATE`. The observed timer/coarse-millisecond deltas yield 60039.99 ticks/ms over the whole interval, consistent with that nominal scale. The coarse counter advances in 10 ms units and is read separately from TIMER3. This is a consistency check, **not external clock calibration**.

`STG` prints raw ticks. `RS` already divides by nominal ticks/us and truncates to integer microseconds. Do not divide its values a second time. `STAT` also clears peak accumulators and `T.max`; it does not save settings or write NOR.

## What “all effects on” can mean

The actual `FXT` reply exposes **37 effect types**. The original firmware has **16 instance slots total and at most 10 per bank**; its editor allows three parallel groups per bank. CPU and memory admission checks apply in addition to these structural limits.

With the current A2 model, the observed remaining FX budget was 21364 ticks and `MEM fxcap` was 113096 bytes. The 16 cheapest distinct types at their reported defaults total 26365 ticks. All 37 defaults total 170822 ticks and 341328 bytes. These sums describe published estimates, not measured processing time, and they do not prove that a particular chain will be admitted. Parameter-dependent buffers, algorithm-specific checks and oversampling changes require reading back the actual `FXS` state.

Therefore the useful tests are either every effect in a chosen preset enabled, or a gradually admitted stress chain with an explicit final list of instances, parameters, routing and oversampling. Neither should be labelled “all 37 effects simultaneously.”

## Bounded measurement procedure

1. Require the completed real UI save/reload roundtrip. Preserve the baseline preset and scene, capture/IR references, gain, and complete `FXS` state. Once preset 0 has been physically established, use `PLOAD 0` to restore it after the stress test.
2. Build a gradual exact-command trial from the real `FXT` ranges. Preserve output level, use controlled wet mixes/default level parameters, and record every actual `FXA`, `FXP` and `FXE` reply plus `FXS` readback. Stop on resource rejection; do not force 16 instances. This is a separate experimental trial, not a grant of general app command families.
3. With the chosen state settled, read `CLKSTATE`, `MODEL`, `GAIN`, `FXS`, `MEM` and a complete `STAT` response. Allow two later `STG win` increments before accepting a measured window, to avoid a window containing both old and new configurations.
4. Collect three distinct fresh windows, with a limit of 12 complete `STAT` samples and 20 seconds. Retain raw lines. Confirm unchanged model, chain, gain and nominal clock; compare `AUD`, A2 and generic-worker counters before/after. Report underrun, overrun, full, error, timeout and skipped/cancelled deltas explicitly.
5. Restore the saved baseline and read it back. During the stress test, do not save over or delete existing presets. Keep the exact chain and restoration evidence with the timing result.

Report window averages and observed maxima, not percentiles inferred from averages. Do not sum stage maxima as if they came from the same block, or subtract unrelated maxima to estimate one effect's cost. New `RS` values are not required for this procedure.

## Physical input-to-output latency

A physical latency result requires confirmed routing: record a reference signal and the processed analog output simultaneously, then compare their time positions while accounting for reference-path skew and the recording interface. USB control-command response time is not audio latency.

Delay, predelay, pitch windows and modulation can intentionally move or spread signal energy. Separate transport/dry-path delay from those effect delays; the strongest correlation peak may select an intentional echo. Gates may suppress a test signal. The current Windows inventory contains generic audio-device names but no confirmed measurement routing, so it does not establish an interface or identify a MINI audio endpoint. No audio recording has been performed for this audit.

## Concrete host experiment

[probe_mini_browser_latency.py](../tools/probe_mini_browser_latency.py) attaches only to an already connected, locally owned qualified WebSerial editor. It creates no browser, opens no serial port, changes no installed profile, and grants no general effect-command families. A real preset-0 save/reload proof and a fresh matching preset/scene/capture/gain snapshot are prerequisites. An intentionally retained first preset does not require a fabricated global-restoration or deletion claim.

The default command performs no I/O. `--check-only --session build/<qualified-editor-session>/session.json` validates local evidence only. The root controller uses `--execute` with that session and a new `--output build/<latency-trial>` directory. Physical attempt 01 stopped on an ACK-format mismatch, as documented below. Trials 02 and 03 subsequently completed; their separate results and limits are recorded above.

[mini_latency_observation.py](../tools/mini_latency_observation.py) derives a bounded sequence from the actual FXT and current FXS/MEM budget. At the earlier 21364-tick budget it selects 13 types totalling a published estimate of 20095 ticks; the later saved-state observation had a smaller 17394-tick budget. The runner recalculates from fresh replies. This is a chosen progressive stress chain with every admitted instance enabled, **not a proof of the globally largest chain** among 37 types and possible duplicates.

Before additions, output gain is reduced to at most -12 dB, since FXA initially enables an instance with defaults. Each new instance is disabled, assigned exact conservative parameters from the real catalog, then enabled and read back. Checkpoints follow 4, 8, 12 and the final planned instance count. The optional `--max-effects 9` selects at most the first nine steps, retains their exact parameters, records the selected cumulative estimates, and makes nine a final checkpoint. Without this option the original finite plan is unchanged. A smaller actually derived plan remains smaller; the cap never promises admission. A firmware resource rejection ends additions; processing faults end the progression. An unhealthy baseline ends the trial before any mutation is armed. There is no controlled test stimulus: CPU cost can depend on input and parameters. The report retains observed peaks/clips and states `stimulus_controlled=false`, `worst_case_latency_proven=false`, and `analog_latency_measured=false`.

[mini_browser_latency_guard.js](../tools/mini_browser_latency_guard.js) wraps the existing original queue and native reader/writer. The first PING advances the previously pending native read into the hook. Any readonly polling that was queued in that brief priming interval is retained and explicitly excluded from raw-RX proof. A subsequent exact PONG and all later trial responses must occur in the native bytes. Native-write completion is checked even when RX arrives first. Reported snapshots and STAT windows are independently matched in command order and mutation epoch; timing calculations are recomputed from those raw lines.

At completion, one `PLOAD 0` restores the saved baseline, followed by full readback and original readonly UI refresh (`applyLvl`, `loadChain`, `loadSnaps`, `loadModelName`). Both `curPreset` and `S.curPre` must agree with preset 0. Only then are the exact original transport/policy references restored and the UI returned. A timeout or uncertain write causes no replay or automatic restoration command; the wrapper and UI remain blocked for diagnosis. A normal protocol rejection can still be followed by that single verified restoration. No preset is saved or deleted during the stress trial. A report marked pass establishes completion and verified restoration, not absence of reported stress faults or physical sound quality.

Offline verification is reproducible with `python -m unittest tests.test_mini_browser_latency tests.test_mini_latency_observation -q`. It exercises the real original JavaScript read loop and command queue on fake native streams, raw-reply forgery rejection, bounded windows, baseline faults, resource rejection, timeout, unique restoration and UI refresh. Synthetic test data is never written as physical evidence. [mini-latency-tool.json](../research/mini-latency-tool.json) records the reviewed preparation and source hashes.

The runner now pins the reviewed qualifier that also accepts the separate saved-reload v2 evidence model. That model proves the actual native USB open and PONG and permits only the original bounded empty-PING bootstrap; it does not invent UIA selection or a COM-name observation. This update changes only the qualifier binding. The latency parser, effect sequence, restoration and requirement for a successful real saved-preset reload remain unchanged.
The latest binding also checks the recorded [Windows chooser configuration](MINI_BROWSER_WINDOWS.md), including the installed Edge selected by the launcher. The continuation applies one fresh native LVL reply with the original `applyLvl` function before its UI trial; the qualifier checks that distinct exchange and the observed UI state. It also binds the exact runtime extension of the original single native-open timeout from 5 to 30 seconds, without adding a reopen. These bindings add no browser flag or device operation to the latency runner itself.

The restoration ACK requires `missing=0 capture=0 ir=0`: `capture` and `ir` are loader results, not library slots. The separate restored PRE/ILIST readback must still report IR slot -1, and the saved preset and gains must match. [The original PLOAD audit](MINI_PLOAD_ACK.md) explains why a zero result alone does not prove a cold reload. The previous ACK assumption was corrected after the closed continuation-06 report; that failed report remains unchanged and does not qualify the benchmark.

Attempt 01 recorded native success replies for `GAIN 0 -12`, `FXA P 99 gate` and `FXE 0 0`. Its guard then rejected the valid reply `FXE ok cpu=0/22799 ticks (0%) mem_fx=0 B` because it had expected only `FXE ok`. [The failed report](../build/mini-fx-latency-01/report.json) remains unchanged. The root controller closed that session and restored preset 0 through a separate single `PLOAD 0`, with complete state and UI readback; [that recovery report](../build/mini-qualified-editor-live-02/recovery.json) explicitly does not claim a native-RX audit.

The revised guard and independent Python replay accept the full original FXE resource reply. Original code at `0x02012CBC..CC4` passes the `FXE ok` prefix to `0x0200EB78`, whose formatter at `0x02039FF1` appends CPU, budget, percentage and memory. The FXP success path at `0x02012C3C..C58` instead reads the effective parameter and formats only `FXP ok %d`. These paths and strings were checked byte for byte between the original G and installed v3 image.

| Planned command | Original success form |
|---|---|
| `GAIN` | `GAIN in=<n> out=<n> dB` |
| `FXA` | `FXA id=<id> <type>`, then `FX cpu=<n>/<n> ticks (<n>%) mem_fx=<n> B` |
| `FXE` | `FXE ok cpu=<n>/<n> ticks (<n>%) mem_fx=<n> B` |
| `FXP` | `FXP ok <effective integer>` |
| `PLOAD 0` | Exact saved name and `missing=0 capture=0 ir=0 ms=<n>`, followed by state readback |

An FXE ACK does not echo the enabled bit; subsequent FXS readback still proves that every measured instance is enabled with the planned parameters. No mutation is replayed after a malformed or missing reply. Eighteen benchmark tests passed for this correction, including the actual attempt-01 FXE reply through the original JavaScript queue and fake native streams, malformed ACKs with matching raw bytes, and unchanged restoration checks. An independent agent reran three focused tests successfully. This correction establishes no completed physical stress result or analog latency.
