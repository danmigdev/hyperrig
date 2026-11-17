# UltraRig reverse engineering and TANK MINI comparison

Research started on 15 November 2026. Conclusions concern the hash-identified
artifacts, not every commercially available hardware revision.

Current development order is maintained in the
[reverse engineering roadmap](REVERSE_ROADMAP.md). Newer bounded C results are
documented in [native DSP reconstruction](NATIVE_RECONSTRUCTION.md),
[switch transition reconstruction](CONTROL_RECONSTRUCTION.md),
[action dispatch and timers](CONTROL_ACTIONS.md),
[selection reconstruction](SELECTION_RECONSTRUCTION.md),
[preset storage validation](PRESET_STORAGE_RECONSTRUCTION.md),
[preset preflight and conversion](PRESET_PREFLIGHT_RECONSTRUCTION.md),
[preset loader/binding/report reconstruction](PRESET_LOADER_RECONSTRUCTION.md),
[asset/application dependencies](PRESET_ASSETS_RECONSTRUCTION.md),
[recursive DSP filters](BIQUAD_RECONSTRUCTION.md),
[IR loading and ownership](IR_LOADER_RECONSTRUCTION.md),
[the five-section DSP chain](BIQUAD_CHAIN_RECONSTRUCTION.md),
[capture loading and gain metadata](CAPTURE_LOADER_RECONSTRUCTION.md),
[coefficient staging/conversion](BIQUAD_COEFFICIENT_RECONSTRUCTION.md),
[capture container installation](CAPTURE_CONTAINER_RECONSTRUCTION.md),
[capture journal/cache](CAPTURE_METADATA_RECONSTRUCTION.md),
[bounded coefficient generation](BIQUAD_GENERATOR_RECONSTRUCTION.md),
[capture DSP dispatch](CAPTURE_DISPATCH_RECONSTRUCTION.md),
[journal writes and verification](CAPTURE_JOURNAL_RECONSTRUCTION.md),
[the integrated filter pipeline](BIQUAD_PIPELINE_RECONSTRUCTION.md),
[the whole native capture parser](CAPTURE_PARSER_RECONSTRUCTION.md),
[capture memory reset](CAPTURE_RESET_RECONSTRUCTION.md),
[the complete metadata command](CAPTURE_COMMAND_RECONSTRUCTION.md) and
[DSP initialization and guarded startup](DSP_INITIALIZATION_RECONSTRUCTION.md),
[integrated native capture loading](CAPTURE_NATIVE_RECONSTRUCTION.md),
[native capture processing](CAPTURE_PROCESSING_RECONSTRUCTION.md),
[dynamics setup](DSP_DYNAMICS_RECONSTRUCTION.md) and
[IR installation](IR_INSTALLATION_RECONSTRUCTION.md),
[native warm-up](CAPTURE_WARMUP_RECONSTRUCTION.md),
[live capture loading and processing](CAPTURE_LIVE_RECONSTRUCTION.md) and
[startup input/four-section processing](DSP_AUDIO_PATH_RECONSTRUCTION.md) and
[four-section parameter transitions](DSP_TRANSITION_RECONSTRUCTION.md) and
[IR convolution construction](IR_CONVOLUTION_RECONSTRUCTION.md),
[IR runtime convolution](IR_PROCESSING_RECONSTRUCTION.md),
[complete preset application](PRESET_APPLICATION_RECONSTRUCTION.md) and
[dynamics sample processing](DSP_DYNAMICS_PROCESSING_RECONSTRUCTION.md) and
[the complete audio task](AUDIO_TASK_RECONSTRUCTION.md),
[scene application](SCENE_APPLICATION_RECONSTRUCTION.md) and
[transition notification](DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md) and
[asynchronous capture](CAPTURE_ASYNC_RECONSTRUCTION.md) and
[DSP stage/routing](DSP_STAGE_RECONSTRUCTION.md),
[effect resampling](EFFECT_RESAMPLING_RECONSTRUCTION.md),
[effect enable and fades](EFFECT_ENABLE_RECONSTRUCTION.md),
[parameter support](EFFECT_PARAMETER_SUPPORT_RECONSTRUCTION.md),
[effect processing callers](EFFECT_PROCESSING_RECONSTRUCTION.md) and
[parameter updates](EFFECT_PARAMETERS_RECONSTRUCTION.md) and
[parameter resources](EFFECT_PARAMETER_RESOURCES_RECONSTRUCTION.md),
[effect construction](EFFECT_CONSTRUCTION_RECONSTRUCTION.md),
[parameter/resource integration](EFFECT_PARAMETER_LIFECYCLE_RECONSTRUCTION.md),
[signal kernels](EFFECT_SIGNAL_RECONSTRUCTION.md),
[effect ownership](EFFECT_OWNERSHIP_RECONSTRUCTION.md),
[resource/ownership integration](EFFECT_RESOURCE_OWNERSHIP_RECONSTRUCTION.md),
[constructor-to-signal integration](EFFECT_CONFIGURED_SIGNAL_RECONSTRUCTION.md),
[IR effect lifecycle](IR_EFFECT_LIFECYCLE_RECONSTRUCTION.md),
[effect model construction](EFFECT_MODEL_CONSTRUCTION_RECONSTRUCTION.md),
[preset storage preparation](PRESET_STORAGE_PREPARATION_RECONSTRUCTION.md),
[IR numerical integration](IR_EFFECT_NUMERICAL_RECONSTRUCTION.md),
[parameter-constructor integration](EFFECT_PARAMETER_CONSTRUCTION_RECONSTRUCTION.md),
[storage control](STORAGE_CONTROL_RECONSTRUCTION.md),
[storage coordination](STORAGE_COORDINATION_RECONSTRUCTION.md),
[effect sample processing](EFFECT_SAMPLE_PROCESSING_RECONSTRUCTION.md),
[storage runtime integration](STORAGE_RUNTIME_RECONSTRUCTION.md) and
[effect setup](EFFECT_SETUP_RECONSTRUCTION.md). The
[audited inventory](REVERSE_INVENTORY.md) distinguishes reconstructed regions
from unverified function candidates; the investigation
notes below retain the context of the original analysis.

## Samples and sources found

Official repository: [manuaguirre9/ultrarig](https://github.com/manuaguirre9/ultrarig).
Main sample: [alpha11 release](https://github.com/manuaguirre9/ultrarig/releases/tag/alpha11),
published on 12 November 2026; internal version `M5.71`.

All reachable repository commits and tags, the four identified public forks,
their branches, and the release asset lists were checked. Branch
`heil-j/ultrarig:feature/ai-tone` contains a web editor, not firmware C sources.
Later test releases are not the sample for this analysis.
Evidence: `research/source-audit.json`.

The [original NOTICE](https://github.com/manuaguirre9/ultrarig/blob/main/NOTICE.md)
states binary distribution. What we actually recovered:

| Component | Recovery obtained | Limitation |
|---|---|---|
| Editor and NAM converter | Original readable HTML/JS sources | Original licence preserved |
| Android APK | Web assets, Capacitor configuration, declared plugins | Java/Dex portion not decompiled |
| Windows installer | Python 3.12 modules, constants, and disassembled bytecode | No complete original `.py` recovered |
| pi32v2 firmware | Decoded application, assembly, Ghidra pseudocode | No original C source or rebuildable project |
| Hardware SDK | GPIO/ADC/DAC headers and register map from an SDK mirror | Not the UltraRig DSP source |

## Integrity and images

ZIPs and APK match digests published in the GitHub API.
Every `*_app.bin` matches its corresponding JSON. CRC16 values for every
JLFS directory and extracted application file are valid.

| Model | File | Bytes in distributed area | Bytes in `app.bin` alone |
|---|---|---:|---:|
| TANK-G v2 | `m571_g_app.bin` | 487424 | 485772 |
| TANK-G v1 | `m571_v1_app.bin` | 487424 | 485868 |
| TANK-B v2 | `m571_tb_app.bin` | 487424 | 485772 |
| TANK-B v1 | `m571_tbv1_app.bin` | 487424 | 485772 |
| TANK MINI stock 009 | `TANK-MINI.fwsc` → `flash.bin` | 532480 for `flash.bin` | 511032 |

Full hashes, CRCs, and embedded versions are in `research/input-manifest.json`
and the reproducible output `analysis/summary.json`.
The MINI FWSC has SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
The manufacturer's catalogue identifies it as V09; observed HTTP Last-Modified:
8 July 2026. Catalogue, build, and HTTP modification dates are not equivalent.

## Platform and addresses

UltraRig JSON files specify AC791N, 396 MHz, and chip key `0x980F`.
For MINI, AC791N appears in the official container, and the same key decodes
its JLFS with valid CRCs. Initial instructions in all samples are consistent
with pi32v2. This does not prove MINI can use the UltraRig clock.

Three address spaces must be distinguished:

- Offset in the application-area file: starts at zero.
- Physical flash address: the preceding offset + `0x4000`.
- CPU flash-window address: the preceding offset + `0x02000000`.

`app.bin` is at area offset `0x120`, hence physical flash `0x4120` and CPU
address `0x02000120`. It must not be imported into Ghidra as ARM or RISC-V.

Reset code also copies code/data into RAM:

| Sample | Flash CPU source | RAM destination | Length |
|---|---|---|---:|
| UltraRig G v2 | `0x02056780` | `0x01C00000` | `0x2030C` |
| MINI stock 009 | `0x0206ED20` | `0x01C00000` | `0xE018` |

Other samples' maps are extracted automatically from their resets into
`memory-layout.json`. Uninitialised RAM regions created for Ghidra analysis
are workspace, not a measurement of free RAM.

## SFC decoding and JLFS filesystem

Application encoding is XOR with a 16-bit state, reinitialised every 32-byte
block. For a block starting at application-area offset `o`:

```text
state = 0x980F XOR (o >> 2)
plain_byte = stored_byte XOR (state & 0xFF)
state = ((state << 1) XOR (0x1021 if bit 15 was one, otherwise 0)) & 0xFFFF
```

The calculation base is the application-area start, not the beginning of
the whole flash. Padding beyond the container's actual length is preserved.
CRCs use polynomial `0x1021`, initialised to zero.

Each directory entry is a 32-byte little-endian structure:
`<HHIIBBH16s`: header CRC, data CRC, address/offset, length, flags, reserved
byte, index/terminator, name. Flags `0x82` identify extracted files;
`0x83` identifies `app_area_head`. Reserved-area fields are not payload
offsets to read from the application file.

Validation: the four UltraRig samples and MINI pass; tests reject a changed
byte, wrong key, and truncated FWSC.

## Flash maps: the decisive porting difference

Half-open ranges `[start, end)`:

| Area | UltraRig G/B M5.71 | MINI stock 009 |
|---|---|---|
| SPL/initial directory | `0x00000–0x04000` | `0x00000–0x04000` |
| Reserved application | `0x04000–0x7B000` | `0x04000–0x82000` |
| VM declared in JLFS | `0x7B000–0xBD000` | `0x82000–0xBE000` |
| BTIF | `0xBD000–0xBE000` | `0xBE000–0xBF000` |
| OTP entry | `0xBE000–0xBF000` | No OTP entry with that name |
| USR | `0xBF000–0xFF000` | `0xBF000–0xFF000` |
| key_mac, upper directory | Final sector expected by installer | `0xFF000–0x100000` |

The lack of an OTP entry in MINI does not prove that the chip has no OTP.
MINI `flash.bin` ends at `0x82000`: it does not contain the user's pedal VM,
BTIF, USR, or key_mac. It is not a full backup to write onto the chip.
Its header reports `0xFF000`; the directory also reserves the final sector
through `0x100000`. Physical capacity must be verified on the device.

For original Tank-B, installer bytecode describes an application extending to
`0x7F000` and migration of VM to the UltraRig location. This result comes
from the installer, not an original Tank-B dump acquired here.

## UltraRig protocol

Reconstructed from actual calls in `tankg.html` and compared against binary
strings. It has not been hardware-tested in this session.
`analysis/protocol-call-sites.json` preserves source lines.

- USB: Web Serial/CDC, VID filter `0x3654`, opened at 115200 baud.
- Newline-terminated text messages, serialised requests.
- Asynchronous events `@L` and `@K`; errors start with `ERR`.
- BLE: NUS service `6e400001-b5a3-f393-e0a9-e50e24dcca9e`, RX `...0002`,
  TX `...0003`, pairing characteristic `...0004`.
- The client uses lines up to 190 characters on recent firmware.
  Initial BLE fragments are 20 bytes, rising to 244 after MTU negotiation.

| Family | Observed commands |
|---|---|
| Diagnostics | `PING`, `STAT`, `MEM`, `MODEL`, `EVT`, `LIFE`, `CRASH`, `CLKSTATE` |
| Effect chain | `FXT`, `FXS`, `FXA`, `FXR`, `FXM`, `FXE`, `FXP`, `FXL`, `FXOS` |
| Routing | `FXMIX`, `FXXO`, `FXIR`, `AMP`, `AMPX`, `AMPEQ` |
| Presets and scenes | `PLIST`, `PLOAD`, `PSAVE`, `PNEW`, `SNAP`, `SNAPSAVE`, `SNAPNAME` |
| Capture | `LDBEGIN`, `LDB`, `LDEND`, `CLIST`, `CLOAD`, `CSAVE`, `CREAD` |
| IR | `IRBEGIN`, `IRB`, `IREND`, `ILIST`, `ILOAD`, `ISAVE`, `IREAD` |
| Controls | `FSA`, `FSMODE`, `FSPRESS`, `FSLED`, `LEDCFG`, `BPM`, `TAP`, `TUNE` |

Transfers to the pedal use offsets and hexadecimal bytes; the final command
carries IEEE CRC32. Examples document the protocol, not operations sent to
the device.

## Capture, IR, and presets

The embedded `A2` capture was extracted and validated: 4892 bytes,
23 layers, 3 channels, final kernel 16, 48 kHz, int16 weights, int32 activations,
int64 biases, and a receptive field of 6347 samples. The parser is in
`hyperrig/a2l.py`. The capture also passes the original converter's
`validateBlob()`.

A2L1 header: 36 bytes, little-endian, signature `A2L1`, version, weight and
activation bits, sample rate, layers, channels, kernel, four Q exponents,
and a 16-byte name. Rechannel, layers with kernel/dilation/weights/biases,
head, and CRC32 follow. The format differs from `.nam` JSON files and original
firmware AM3/AM4 formats. The analysed release declares `amx=false`.

The client prepares IR as int16; storable capacity is 4076 samples in slots
0–6 and 2028 in slot 7, with separate gain. The protocol can allocate
4096 samples for upload: temporary and saved capacities differ.

The client's preset export is JSON `format="ultrarig-preset"`, version 1;
it may include attachments with SHA-256. Scenes and effects are reconstructed
with protocol commands. Original MINI instead uses 92-byte binary records,
21 per bank: renaming a JSON file does not convert the preset.

## Reconstructed DSP reference

`hyperrig/a2l_reference.py` implements a causal Float64 model with ring
buffers for dilated convolutions, LeakyReLU, residuals, activation sums,
and final convolution. Weights and biases are dequantised using the file's
exponents. Convolution biases use `conv_F + previous_F`,
residual biases use `linear_F + activation_F`, and the final bias uses
`head_F + sum_F`.

Pre-roll of `receptive_field - 1` zeros preserves the converter's temporal
alignment. Tests compare the 49 peak measurements of each pass against
`measure()` from recovered JavaScript, using the same dequantised weights:
silence, impulse, and an alternating/sinusoidal signal. Tolerances:
`rel_tol=1e-11`, `abs_tol=1e-12`. Other tests check sample-by-sample results
for a small network calculable by hand, bias scaling, block continuity,
and WAV clipping.

This verifies the mathematical structure of the floating-point reference.
It is not bit-for-bit verification against firmware. The separate native
reconstruction now includes two dot products and a three-channel head, with
shifts, saturation, and wrap; see
[NATIVE_RECONSTRUCTION.md](NATIVE_RECONSTRUCTION.md). Layers, activations,
and performance of the entire engine remain to be verified.
The Float64 model includes neither IR, effects, nor audio routing.

## Decompilation and limitations

Ghidra 12.2 with `virtualabs/ghidra-jieli`, plus an independent disassembler
based on `jvitkauskas/pi32v2-isa`. Versions and hashes are pinned in the lock file.

| Sample | Functions for which Ghidra emitted C | Complete failures |
|---|---:|---:|
| G v1 | 260 | 0 |
| G v2 | 260 | 0 |
| B v1 | 260 | 0 |
| B v2 | 255 | 0 |
| MINI | 662 | 1 |

These counts are neither coverage nor proof of correctness: even an exported
function may contain unrecognised instructions, incomplete p-code, and
`halt_baddata`. Total recovery is 1697 exported functions, not the whole DSP.
`.asm` listings are linear scans and include data interpreted as possible
instructions; they are not a fully verified control-flow graph.

Entry and RAM copies are confirmed by bytes. Pins, function names, and
algorithms require further reconstruction and cross-checking.
pi32v2 branch annotations were corrected to use actual instruction length,
and all listings were regenerated. The ALNK0 audio path is documented in
[TANK_MINI_AUDIO.md](TANK_MINI_AUDIO.md).
No firmware was installed, no pedal modified, and the installer's telemetry
service was not contacted.
