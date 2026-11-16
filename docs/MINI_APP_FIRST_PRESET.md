# First HyperRig preset on the MINI

The previous persistence probe does not cover the first boot without a G
preset: `validate_saved_baseline()` requires a currently selected saved preset
and its backup; the final cycle reloads it and deletes the temporary preset.
With `PLIST ... current=-1`, it stops before PSAVE. That probe and the
read-only client remain unchanged.

[probe_mini_app_first_preset.py](../tools/probe_mini_app_first_preset.py)
handles this case separately. It creates `HyperRig_Test` in a slot observed
to be free and intentionally leaves it saved, with scene A. It does not
send PDEL or try to restore a nonexistent preset. If a preset is already
selected, this path stops before writing: that case is covered by the
previous probe.

## Actual sequence

Before any write, it acquires PONG, FXT, FXS, PLIST, SNAPS, GAIN, AMPEQ,
BPM, PCOLOR, STW, MODEL and SNAPNAME. It retains both the responses and the
parsed state in a new file. It rereads the entire state before PSAVE and
requires it to remain unchanged. No export of a presumed empty G bank is
needed; any other listed slots must remain present with the same metadata
and are neither loaded nor deleted.

1. `PSAVE <slot> HyperRig_Test`, exact ACK and a fresh PLIST/FXS/state.
2. A verified live marker; `PLOAD <slot>` must restore the saved values.
   If an initial scene is selected, it is reapplied.
3. Only after the first PSAVE test, `SNAPSAVE 0` creates or updates scene A
   in the new slot. The ACK, scene inventory and state must match.
4. A second marker; PLOAD and `SNAP 0` must independently restore the state
   of the scene just saved.
5. A final read must be stable. The new preset and scene A remain stored
   and selected, with the observed sound configuration verified through
   the protocol.

The original `sceneAOnSave()` in
[tankg.html](../recovered/ultrarig-original/web/tankg.html) adds
`SNAPSAVE 0` after PSAVE when no scenes exist. The separate test prevents
SNAPSAVE from masking a PSAVE that was not persisted. Responses, FXT ranges,
parsers and timeouts are reused from the previous probe. Runtime effect IDs
can change with PLOAD: the comparison uses position, type and values, not
the numeric identity that was just reassigned.

## A marker even with an empty chain

In `auto` mode, an actual available FXP parameter is preferred, with one
downward step within its FXT range. If no suitable parameter exists, output
gain is reduced by 1 dB; if it is already at -30 dB, input gain can be
reduced instead. Gain is not increased for the test. If both gains are at
their minimum and no other allowed marker exists, PSAVE is not sent.
FXE can be explicitly selected on a real block; no block is invented to
work around an empty chain.

The original `buildGains()` frontend uses `GAIN <in> <out>`, with a
`-30..12` dB range. The G firmware clamps at `0x02008DE2..0x02008E2C`,
called from the `0x02013140` branch; the response string is at offset
`0x365BE` in `app.bin`. The probe requires an ACK and a fresh GAIN read,
along with the other fields, before attempting PLOAD. It does not send GSAVE.

An active capture that PSAVE reports as unassociated with the library is
not treated as saved: the test stops before the marker/reload. Here, the
protocol cannot restore a scene selection of -1 when unselected RAM scenes
already exist; that case stops before writing. No error triggers a retry,
deletion or blind restoration. An incomplete report states the phase reached
and whether the new slot had already appeared in the list.

## Usage and offline tests

Importing the module and running the default command neither enumerate
devices nor import pyserial:

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py
python -B -X utf8 -m unittest tests.test_mini_app_first_preset tests.test_mini_app_families tests.test_mini_app_mutation tests.test_mini_app_transport tests.test_mini_app_protocol
```

The coordinator can use the explicit `create` subcommand only with the
manifest of the candidate actually booted, with qualified reads. Outputs
must be new, distinct and inside the workspace. Adapt this example to the
actual port and manifest; it is not evidence of a hardware test already
performed:

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py create --port COM8 --firmware-manifest build/mini-app-manifest.json --slot 0 --log build/first-001.jsonl --backup build/first-001-before.json --report build/first-001-proof.json
```

Without `--slot`, it selects the first free slot from the complete PLIST.
`--operation
GAIN` selects the gain marker; FXP requires `--block` and `--parameter`,
whereas FXE requires only `--block`. The test ends with the new preset
retained, rather than simulating a return to the initial selection state.

## Separate evidence and revised app capabilities

The new report is `mini-app-first-preset-validation`, using the
`representative-first-preset-v1` model. It explicitly declares:

- `restoration_verified=false`: there was no currently selected preset to restore;
- `preset_intentionally_retained=true` and `final_sound_verified=true` only
  after both reloads and the final read;
- `physically_exercised_requests` only for operations actually performed on
  the stated transport; mocks populate `simulated_requests` instead.

The builder accepts this form through a separate branch. It checks the same
image, version, source and transport bindings as the previous tests, then
**replays the probe offline against the retained raw TX/RX**. The replay
must consume every command in the same order and obtain exactly the
declared initial state, FXT, final result and observations. The new probe
implementation's hash is also pinned. Flags alone or an ACK alone are
insufficient; this check proves consistency of the evidence, not the physical
authenticity of a log. The semantics of the older restoration and cleanup
tests remain unchanged.

This revision adds the operational GAIN family. It is enabled only by a
representative test on the same transport; the runtime validates syntax and
`-30..12`, and requires valid GAIN or LVL context. An inconsistent ACK,
PLOAD, SNAP or disconnection invalidates that context until it is reread.
The two original knobs use the same queue and commands. A test with an
empty chain can qualify GAIN, PSAVE, PLOAD, SNAPSAVE and SNAP; **it does not
qualify FXP or FXE if they were not exercised**. USB does not automatically
enable Android/BLE. General support for uploads, FXAdd or panel commands
is not claimed.

## Expected effects on USR and limitations

Normal G preset management can rotate among the journal's 18 physical
sectors and rewrite a pair of presets within a sector. An intentional save
therefore does not promise to change only one page or keep USR byte-for-byte
identical. The mapper, write bounds and distinction from VM/OTA/BTIF are
documented in
[MINI_PRESET_STORAGE_REVIEW.md](MINI_PRESET_STORAGE_REVIEW.md).
The preservation verified by the installer applies to the point before
the app starts; it does not prevent later normal writes authorized by a save.

The comparison of other slots covers their PLIST metadata, not every hidden
payload. The state backup covers observed fields, not the internal history
of delay/reverb effects. Reload and readback do not prove retention after
a power interruption or measure audio. This revision's tests use mocks:
they do not claim a G boot, an actual save, or physical qualification of
the desktop or Android editor.
