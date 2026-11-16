# MINI timing and latency

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

## Bounded next measurement

1. Finish the real UI save/reload roundtrip first. Preserve the baseline preset and scene, capture/IR references, gain, and complete `FXS` state. Once preset 0 has been physically established, use `PLOAD 0` to restore it after the stress test.
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

The default command performs no I/O. `--check-only --session build/<qualified-editor-session>/session.json` validates local evidence only. The root controller may later use `--execute` with that session and a new `--output build/<latency-trial>` directory. No effect experiment has been executed by this preparation.

[mini_latency_observation.py](../tools/mini_latency_observation.py) derives a bounded sequence from the actual FXT and current FXS/MEM budget. At the earlier 21364-tick budget it selects 13 types totalling a published estimate of 20095 ticks; the later saved-state observation had a smaller 17394-tick budget. The runner recalculates from fresh replies. This is a chosen progressive stress chain with every admitted instance enabled, **not a proof of the globally largest chain** among 37 types and possible duplicates.

Before additions, output gain is reduced to at most -12 dB, since FXA initially enables an instance with defaults. Each new instance is disabled, assigned exact conservative parameters from the real catalog, then enabled and read back. Checkpoints follow 4, 8, 12 and the final planned instance count. A firmware resource rejection ends additions; processing faults end the progression. An unhealthy baseline ends the trial before any mutation is armed. There is no controlled test stimulus: CPU cost can depend on input and parameters. The report retains observed peaks/clips and states `stimulus_controlled=false`, `worst_case_latency_proven=false`, and `analog_latency_measured=false`.

[mini_browser_latency_guard.js](../tools/mini_browser_latency_guard.js) wraps the existing original queue and native reader/writer. The first PING advances the previously pending native read into the hook. Any readonly polling that was queued in that brief priming interval is retained and explicitly excluded from raw-RX proof. A subsequent exact PONG and all later trial responses must occur in the native bytes. Native-write completion is checked even when RX arrives first. Reported snapshots and STAT windows are independently matched in command order and mutation epoch; timing calculations are recomputed from those raw lines.

At completion, one `PLOAD 0` restores the saved baseline, followed by full readback and original readonly UI refresh (`applyLvl`, `loadChain`, `loadSnaps`, `loadModelName`). Both `curPreset` and `S.curPre` must agree with preset 0. Only then are the exact original transport/policy references restored and the UI returned. A timeout or uncertain write causes no replay or automatic restoration command; the wrapper and UI remain blocked for diagnosis. A normal protocol rejection can still be followed by that single verified restoration. No preset is saved or deleted during the stress trial. A report marked pass establishes completion and verified restoration, not absence of reported stress faults or physical sound quality.

Offline verification is reproducible with `python -m unittest tests.test_mini_browser_latency tests.test_mini_latency_observation -q`. It exercises the real original JavaScript read loop and command queue on fake native streams, raw-reply forgery rejection, bounded windows, baseline faults, resource rejection, timeout, unique restoration and UI refresh. Synthetic test data is never written as physical evidence. [mini-latency-tool.json](../research/mini-latency-tool.json) records the reviewed preparation and source hashes.
