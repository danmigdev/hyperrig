# MINI editor: representative command-family qualification

This source revision makes the original editor's FX parameter, bypass, preset
load/save and scene controls operational after representative physical trials.
It does not require a physical test of every parameter value, preset name or
scene number. `supported_by_protocol` and `physically_exercised_requests` are
separate fields; neither implies that all editor mutations have been tested.

The frozen mutation client is [probe_mini_app_mutation.py](../tools/probe_mini_app_mutation.py),
documented in [MINI_APP_MUTATION.md](MINI_APP_MUTATION.md). Its default is offline.
No physical trial was performed while implementing this revision. The existing
audio-v2 web app/APK and firmware image were not rebuilt or modified.

## Build input

The normal firmware manifest still supplies `image_path`, `image_sha256`, exact
`firmware_version`, `target: tank-mini`,
`architecture: standalone-ultrarig-port`, `hardware_verified: true`, and
`capabilities: {read: true, write: false, panel: false}`. Add, for example:

```json
{
  "family_capabilities": {
    "usb-cdc": ["FXP", "FXE", "PLOAD", "PSAVE", "SNAP", "SNAPSAVE"]
  },
  "family_validation": {
    "usb-cdc": [
      {"path": "analysis/hardware/<completed-save-trial>.json", "sha256": "<SHA-256>"},
      {"path": "analysis/hardware/<completed-FXE-trial>.json", "sha256": "<SHA-256>"}
    ]
  }
}
```

These paths are placeholders, not claims that those trials exist. A successful
save trial with an FXP marker can cover FXP, PLOAD, PSAVE, SNAP and SNAPSAVE;
an FXE roundtrip covers the remaining family. Each requested family must have a
verified representative on the same transport and firmware image. Smaller
subsets are supported. The original Save button requires both PSAVE and SNAPSAVE.

`build_mini_app.load_profile()` accepts the frozen probe's
`representative-families-v1` evidence directly. It checks:

- Exact image/version/editor/original-firmware/dialect binding and transport.
- A real-execution assertion consistent with trace and backup, verified
  restoration, and no simulated requests in the physical evidence.
- Each physically exercised request's ACK and readback observation, including
  its state hash. Its exact TX, raw RX, returned line and completed exchange must
  exist in the retained, hash-bound trace. PING must carry the matching version.
- PSAVE/SNAPSAVE reload verification, scene reload verification and cleanup of
  the exclusively created test slot, plus the retained bank backup.

Evidence remains a reviewed observation, not a cryptographic assertion by the
pedal. PONG does not attest the installed image hash. The manifest's image hash
must be tied to the installed candidate by the separate installation evidence.
Checking the journal does not independently prove its physical provenance or
re-execute every semantic comparison in the probe.

The builder emits `family_qualification` with enabled families, exact physically
exercised requests, protocol sources and `every_value_physically_tested: false`.
It does not set blanket write capability or
`all_required_editor_mutations_verified`. Existing exact-request profiles remain
supported unchanged. The default manifest enables no families.

## Runtime behavior

The adapter observes complete responses in the original serial/BLE command queue.
Malformed, truncated, timed-out or erroneous relevant responses invalidate the
corresponding context. Identity acceptance and disconnect clear all context.
Commands are checked when requested and again when their queued write begins.

| Family | Operational bounds |
| --- | --- |
| FXP | Existing ID/type from FXS, parameter index and integer min/max from FXT. All actual parameters within those bounds are eligible, including parameters outside the first experiment's conservative selection. |
| FXE | Existing ID from FXS and enable value 0/1. |
| PLOAD | Slot present in a complete coherent PLIST, within 0–31. Successful load invalidates old effect IDs and scene context until refreshed. |
| PSAVE | Slot 0–31, coherent PLIST and FXS, nonempty name up to 23 UTF-16 units, no controls, at most 190 UTF-8 bytes for the command. Occupied slots use the original editor's overwrite confirmation. |
| SNAP | Index 0–3 actually present in the last coherent SNAPS response. |
| SNAPSAVE | Index 0–3 and a known current saved preset with scene context. It may create an absent scene. |

The Save preflight plans PSAVE followed by SNAPSAVE against the prospective
destination, including an initially empty slot. Planning does not update the
observed device state: only the matching actual PSAVE acknowledgement does so.
Thus the original `savePreset()` → `sceneAOnSave()` flow works for ordinary
names/slots after qualification, rather than only for `HyperRig_Test` in the
experiment's slot. A failed or mismatched save acknowledgement does not open the
following scene save.

Context is the last observed state, not an atomic board lock. The original
editor's refresh/event handling remains in place; external footswitch or other
client changes can still race commands. A valid FXT range also does not guarantee
that enough CPU/memory exists for every setting: the original firmware's errors
and readback remain authoritative. This revision adds no automatic retry.

Saving one scene or the current preset is supported by these families. “All
scenes” save and full bank export remain unavailable in a limited profile because
their original sequences also use unqualified tuner/amp-EQ and other commands.
PDEL, uploads, chain creation/reordering, global settings and physical-panel
commands are not granted by these six families. PDEL in the isolated persistence
trial is cleanup of its own new slot, not general editor deletion support.

## Transport and validation limits

USB CDC and BLE NUS have independent evidence and capabilities. A USB trial does
not qualify BLE, Web Bluetooth, the Android APK, pairing, or encrypted write
behavior. A later BLE report can use the same evidence model with `ble-nus`, but
must retain its own physical trace/backup and representative results. The
original BLE authentication controls continue to apply.

Offline verification:

```text
python -B -X utf8 -m unittest tests.test_mini_app_families tests.test_mini_app_mutation tests.test_mini_app_transport tests.test_mini_app_protocol
```

The 72 tests include the frozen client's fake-transport roundtrips, manifest
rejection cases, actual FXT range checks, transport isolation, invalidation of old
IDs behind a queued PLOAD, and the original editor/queue saving a different name
to a different slot followed by automatic SNAPSAVE. Temporary schema fixtures
which assert hardware execution are explicitly labelled test data and are
deleted; mock output itself never qualifies a family.

Physical USB editor operation, power-cycle retention, audio quality and Android
BLE operation remain separate validations. This source change was authorized as
a new app revision after the probe freeze; it does not alter the pinned audio-v2
distribution or frozen readonly/mutation clients.
