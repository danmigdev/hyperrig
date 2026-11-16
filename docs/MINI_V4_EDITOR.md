# MINI v4 editor correction

Preview 05 enables nine bounded USB command families using a completed native
trial on the installed v4 image. It also displays **HyperRig MINI · v4 preview**
and groups presets into **A/B/C** banks. This is an editor/package update;
the firmware image, protected command-policy JavaScript and original license
notices are unchanged.

## Device and evidence

The installed application SHA256 is
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The association comes from the verified GUI installation and full readback;
the firmware's PONG does not attest its binary hash.

The retained private report is `build/mini-v4-controls-01/report.json`, SHA256
`7c8bc584e240c053fc3b5e901d65528b7dcc749f8c258dfd4c809ccc46191db8`.
Its native transcript is `build/mini-v4-controls-01/wire.jsonl`, SHA256
`52ad0f2367c45ad92fc5e59fe24febfbdbfe8c334d6c211e00d6516e6d4468bd`.
The report and native responses are replayed before deriving the public scope.
Neither raw record, personal paths nor preset contents ship in the package.

The real trial exercised GAIN, FXA, FXP, FXE, FXR, PSAVE, PLOAD, SNAPSAVE and
SNAP. It added one temporary gate, changed and restored its threshold and
bypass state, removed it, and exercised preset/scene persistence in a previously
empty slot. Existing presets were never saved over. The temporary preset was
deleted after the original preset and scene were recalled. The final observed
state matched the initial state exactly.

There were no mutation retries. The original handshake repeated PING once
after a witnessed completely empty timeout. The report's `automatic_retry`
field describes mutations; the transcript and derived qualification explicitly
record this bounded handshake repetition. The raw report is preserved.

These are representative protocol tests on one MINI. They do not qualify
every effect/value, the physical UI, audio, BLE writes, parallel routing,
bulk transfers, preset deletion or panel remapping. PDEL was used only to
remove the trial's own newly created preset and is not exposed by this profile.

## Presets, scenes and version labels

Device slot IDs remain 0 through 31. The editor maps them to three slots per
bank: 0/1/2 are 1A/1B/1C; 3 is 2A; 31 is 11B. The final bank has two slots.
Loading, saving, labels and bank selection use the same raw IDs. No preset is
deleted or moved by the presentation derivation.

Each preset still supports four scenes. Scene IDs, masks and the firmware's
physical switch dispatch are unchanged. Physical footswitch bank navigation
has not been qualified as a three-slot implementation by this UI correction;
the panel configuration remains disabled.

The Footswitches screen is intended to assign physical switch actions and LED
behavior. Stage is the large live-performance view of those assignments,
presets and scenes. Both entry buttons remain disabled on MINI because these
screens still assume four logical switches and depend on unqualified panel
commands. The A/B/C preset list correction does not enable these screens.

The user confirmed the v4 preview label and A/B/C preset list in the newly
opened preview 05. No physical UI mutation or audio test was reported in that
confirmation.

The upstream Alpha 11 display mapping is replaced by the actual MINI port
label. The original protocol identifier `tankm_fw M5.71 rel ble` remains intact.

## Build and verification

```powershell
python -B tools/build_mini_installer_bundle.py --build build/hyperrig-mini-installer-one-switch-preview-05 --variant v4 --editor-revision mini-v4-usb-01 --executable
python -B tools/launch_mini_installer.py --bundle build/hyperrig-mini-installer-one-switch-preview-05 --check-only
```

The optional revision leaves historical v3 and read-only v4 bundles valid.
The new revision pins its public qualification and derived UI, preserves the
existing family bounds, and does not enable blanket writes. Native transcript
replay through the unchanged JavaScript policy checks the enabled operations;
offline renderer tests check all 32 load/save destinations and the partial
last bank. These offline checks are not hardware or audio tests.
