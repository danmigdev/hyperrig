# Complete UltraRig application for TANK MINI

The current candidate in `build/hyperrig-mini-audio-v2/` contains the complete
UltraRig G alpha11 v2/M5.71 application, adapted through patches with verified
preimages, a compiled C shim, and a mandatory v2 recovery guard at entry.
The stock MINI application firmware is not included. The
[report](../research/mini-integrated-port-v2.json) lists every change and
verifies that reversing the patches recovers the original G application exactly.

The composition with the guard is 516,096 bytes: 20 patches in total and 2,630
bytes of added code, with no new BSS. SHA-256:
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
This verification covers the file; it does not yet certify physical boot or audio.

The version with audio shim v1 and recovery guard v2, SHA-256
`639f58864e2b7c29c4312545fe94b345b2f8c8c21eb72eceb0932712bd608f70`,
remains in `build/hyperrig-mini-integrated/`. The HYW1 probe with writes disabled
was executed using a page from that version; its evidence is not attributed
to the new candidate.

The earlier candidate, SHA-256
`f8835a7fd45b1b324d66c457434c7943d70525ed5eb98b514aaac1095031f068`,
is preserved in `build/hyperrig-mini-integrated-before-guard/` with its firmware
manifest, canonical report, composition report, and editor. The
`archive-manifest.json` file records hashes of the eight files archived before
regeneration.

| Group | Adaptation |
|---|---|
| Identity and storage | HyperRig, `tankm_fw`, USB `Tank-M HyperRig`, MINI VM geometry |
| Panel | Three inputs, incompatible G LED writer removed, unmapped analog controls disabled |
| Startup | G context extensions initialized without reading bytes not guaranteed by the MINI bootloader |
| Audio | MINI codec and PA9, retaining G DSP, RTOS, and ALNK path |
| Recovery | V2 guard before the first G call, three footswitch inputs, and explicit ROM marker/reset after combination detection |

Audio shim v2 reproduces the 22 stock records without changing OSR. It prepares
PC5 using G locks and continues after NACK according to the stock caller's
policy, distinguishing attempted records from acknowledged ones. Timing or
cleanup errors remain fatal; the explicit STOP after NACK is a difference
documented in [MINI_AUDIO_PORT_V2.md](MINI_AUDIO_PORT_V2.md).
Configuration at the nominal G frequency and complete audio are not yet
qualified in this application. ROM codec, DSP, and switch/reset diagnostics
have separate evidence; they are not automatically converted into boot
evidence for this candidate.

The current guard occupies 298 bytes from `0x020773C8` to `0x020774F2`, after
the 2332-byte audio shim. The builder calculates the address from the shim's
actual length, applies any alignment padding, and recompiles the guard; it
does not use a fixed address when the audio changes. `bind_append` verifies
that the actual payload and entry branch match that allocation. The integrated
`entry-recovery-manifest.json` preserves the 1280 instruction-model cases and
the hashes of the unchanged v1 callables.

The application policy sets `PORTA.DIR |= 0x409` before the check. The three
pins remain inputs and other bits are preserved; the G context, including R0,
is restored when boot continues. It does not depend on the initial direction
left by the cold SPL. The HYK1 ROM probe retains its different restoration
policy and is unchanged. Details are in
[MINI_ENTRY_RECOVERY_V2.md](MINI_ENTRY_RECOVERY_V2.md).

## Local reproduction

With originals, extractions, and the toolchain already present as described
in the README:

```powershell
python -B -X utf8 tools/audit_mini_ultrarig_port.py
python -B -X utf8 tools/audit_mini_panel_port.py
python -B -X utf8 tools/audit_mini_boot_contract.py
python -B -X utf8 firmware/mini/audio_port_v2/verify.py
python -B -X utf8 tools/build_mini_ultrarig.py --audio-manifest build/mini-audio-port-v2/manifest.json --output build/hyperrig-mini-audio-v2 --report research/mini-integrated-port-v2.json
python -B -X utf8 tools/plan_mini_install.py --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --output build/mini-install-plan-v2
python -B -X utf8 tools/build_mini_android.py --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --output build/hyperrig-mini-audio-v2/android
```

These commands operate on local files and tests. They do not open the pedal.
The builder checks shim hashes, its ELF, call symbols, the mandatory guard,
disjoint patches, partition limits, and CRCs after decoding. The `recovery`
group must contain the entry patch; there is no build option to omit it. The
editor at `build/hyperrig-mini-audio-v2/app/web/tankmini.html` is derived from
the originals with the exact firmware hash: it recognizes `tankm_fw` and enables
the intended queries. Mutations require physical evidence bound to the image
and transport; ordinary builds do not enable them. The builder regenerates the
web editor, not the APK: the final APK must be rebuilt after the final audio
and firmware revision. Any earlier installation plan must also be regenerated
and checked against the new hash. The v2 APK has been rebuilt: SHA-256
`69273b95adeefe3c865d1e6da8e18fc2bf612fd995e19462a77c7dae6eb1c82b`,
associated with image `3b0eac3b…`. It has not yet been tested on the phone.

## Replacement and restoration

The offline plan contains 126 4 KiB sectors in physical range
`[0x4000,0x82000)` and `stock-mini-app-area.bin` for exact restoration of the
same area. It separately preserves each sector's before/after hashes. It
contains no erase or program commands and does not make the update atomic.

Installer data reception and comparison were verified on the MINI with the
write gate continuously disabled: the first sector matched the backup, 260
bytes were received, and the frozen 256-byte page was returned exactly.
WREN, erase, and program remain zero. Return to stock and unchanged presets
are documented in the [HYW1 report](../research/mini-writer-observer-hardware.json).
This test does not yet qualify actual erasure or programming.

SPL, boot configuration, VM, BTIF, USR, and unit-specific data remain outside
the application replacement. The factory updater in `0xB7000..0xBD000` is also
preserved. This separation is consistent with the original UltraRig installer:
preserving boot infrastructure does not mean using the MINI application or
DSP as the port's base.

Using a writer requires a current flash read, checks of the writer for this
NOR, and qualification of the intended recovery path. The guard runs before
the G RTOS/clocks/DSP and may allow return to ROM when a valid image hangs
later. It does not cover a damaged header, entry, or guard. Physical switch
and marker/reset testing through HYK1 is distinct from cold execution of the
XIP prefix and recovery of the actual installed candidate: the builder keeps
those latter flags `false`. Boot details are in
[MINI_BOOT_CONTRACT.md](MINI_BOOT_CONTRACT.md).

`boot_verified_on_mini`, `audio_verified_on_mini`, `flashable`, and the editor's
write capability remain `false`. Composition alters no target-profile file
or hardware-observation report.

The goal remains open until stable boot, real audio, and preset reading/editing
through the HyperRig app on the MINI have been achieved.
