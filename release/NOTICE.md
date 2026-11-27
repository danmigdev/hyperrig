# HyperRig for the M-VAVE TANK-MINI: notice

HyperRig is an independent firmware, editor and installer for the M-VAVE TANK-MINI. It is
not affiliated with, endorsed by or supported by M-VAVE, Sinco, JieLi, the author of
UltraRig, TONE3000 or Patchstorage. Their names and marks are theirs and are used only to say what
HyperRig works with or comes from. Installing it replaces the firmware of the pedal, at the
risk of the person who does it. It comes without any warranty.

It contains no firmware, software, capture or impulse response of M-VAVE or Sinco.

## Terms

HyperRig is based on UltraRig. UltraRig is under the PolyForm Noncommercial License 1.0.0
(`LICENSE.md`), and what is derived from it stays under it: **noncommercial use only.** It
may not be sold, nor may pedals with it.

> Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)

HyperRig's own code is under the same licence.

> Required Notice: Copyright (c) 2026 the HyperRig project (https://github.com/danmigdev/hyperrig)

The firmware in this package is based on UltraRig's and was changed by HyperRig; it is not a
release of UltraRig's author. UltraRig's own notice and its
list of licences are kept unchanged in `ultrarig/`. They describe UltraRig's package, not
this one: of the parts they list, the Windows installer, its Python, python-rtmidi, pyserial,
crcmod, PyInstaller, jl-uboot-tool and `wl82loader.bin` are **not** in HyperRig.

The other parts keep their own licences, which the terms above do not replace or restrict.

## What is in it

| Part | Where | Whose, and the licence | Text |
|---|---|---|---|
| UltraRig, changed | Firmware; the editor's page and its capture converter | Manuel Aguirre, 2026; PolyForm Noncommercial 1.0.0 | `LICENSE.md`, `ultrarig/NOTICE.md` |
| HyperRig's own code | Firmware, loader, editor, installer, desktop program | The HyperRig project, 2026; PolyForm Noncommercial 1.0.0 | `LICENSE.md` |
| JieLi AC79 / WL82 SDK | Firmware | Zhuhai Jieli Technology Co., Ltd.; Apache License 2.0 | `ac79-sdk-LICENSE.txt` |
| FreeRTOS V9.0.0, in the SDK's libraries | Firmware | Real Time Engineers Ltd., 2016; GNU GPL v2 with the FreeRTOS exception | http://www.freertos.org/a00114.html |
| micro-ecc, in the SDK's libraries | Firmware | Kenneth MacKay; BSD 2-Clause, by the SDK's record | `ac79-sdk-LICENSE.txt` is the SDK's own; the notice of micro-ecc is in its source, https://github.com/kmackay/micro-ecc |
| Parts of `btstack.a` of the SDK | Firmware | JieLi's, under the SDK's licence. Their file and function names match BlueKitchen BTstack (Copyright (C) 2009 BlueKitchen GmbH), so they appear to derive from it; if they do, its licence applies too: personal, noncommercial use | `btstack-LICENSE.txt` |
| NeuralAmpModelerCore (`A2.nam`) | Firmware: the capture that plays when there is no other | Steven Atkinson, 2023; MIT | `ultrarig/THIRD_PARTY_LICENSES.md`, part 3 |
| m-bootloader | HyperRig's loader, which the installer puts on the pedal; the descriptors of the firmware's MIDI port | Julius Vitkauskas, 2026; MIT | `m-bootloader.md` |
| Big Shoulders Display, Public Sans | Editor and installer | SIL Open Font License 1.1 | `fonts.md` |
| TONE3000's logos | Editor | TONE3000; used to identify it, as its API terms ask | `tone3000.md` |
| Patchstorage's logo | Editor | Patchstorage; used only to name it, on the button to its presets | `patchstorage.md` |
| Electron, Chromium and their parts | The desktop program | OpenJS Foundation, Electron contributors and others | `ELECTRON-LICENSE.txt`, `CHROMIUM-LICENSES.html` |

## Where numbers came from

No recording is in HyperRig. The acoustic block was fitted to recordings of two datasets, and
the built-in strokes of "Same volume" to those of the second,
both under the Creative Commons Attribution 4.0 International licence
(https://creativecommons.org/licenses/by/4.0/); only fitted numbers are used, and they were
changed:

- GuitarSet, Q. Xi, R. Bittner, J. Pauwels, X. Ye and J. P. Bello, ISMIR 2018,
  https://zenodo.org/records/3371780;
- Guitar-TECHS, https://zenodo.org/records/14963133.

The limits of the harmonizer's listening were set with the solos and the notes of the first.

## Privacy

The program sends nothing over the network, except to TONE3000 when the person opens Browse
TONE3000 in it, and to Patchstorage when they open Browse Patchstorage. It has no telemetry and sends no report by itself.
