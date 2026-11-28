# The installer

It puts HyperRig on a TANK-MINI that has M-VAVE's firmware 011, updates it, and puts the original
firmware back. It is part of [the desktop program](DESKTOP_EDITOR.md), works over USB MIDI like
M-Upgrade, and needs no administrator rights, no download mode and no switch held on the pedal.

On one TANK-MINI it saved the whole pedal from 011, installed HyperRig, updated it several times and
brought the original back byte for byte. No second pedal was tried.

## How it gets in

M-VAVE's firmware takes an update over MIDI in two parts: it stores a small loader from the package,
with a record for the bootloader, and restarts; the bootloader starts the loader, which writes the
rest. HyperRig uses the first part only, with a package that holds nothing but its own loader
([`firmware/mini_stage`](../firmware/mini_stage/README.md)). Nothing of the application changes until
the loader is asked to.

From HyperRig, the console word `STAGE GO` starts the loader that is still stored
([MINI_PRODUCT.md](MINI_PRODUCT.md)).

## What is sure before anything is erased

1. The loader is HyperRig's, on the chip, the key and the flash chip of a TANK-MINI.
2. The whole flash was read, each 64 KiB compared with the checksum the chip computes, kept on this
   computer and read back from the disk. The loader itself refuses a host that does not know the
   checksum of the whole flash.
3. The firmware to write is whole: its directory, its checksums, and the manifest of the program. The
   directory gets the pedal's own partitions.
4. The bootloader, as far as the flash shows, would come back to the loader: the first update record
   it would find leads to a loader that unpacks and checks. The installer computes this from its copy
   of the flash, and the loader looks again. An older record of another loader that would be found
   first is made void.

## How it writes

The header sector of the application is erased first and written last. From the first erase to the
last page the bootloader finds no application and starts the loader again. Only the application and
the user area change: the application from `0x4000` up to where the pedal's own VM begins (`0x95000`
on a TANK-MINI with 011, whose application partition is that large), or up to `0x82000` with a loader
from before HyperRig 0.6.0. Every sector is checked when it is erased and when it is written, and at
the end the chip compares the whole flash with what was meant; only then does the application start.

## The room of 011, once through the original

From 0.6.0 HyperRig may use the whole application partition of 011, 76 KB more than before. The loader
that came with an older HyperRig writes only up to `0x82000`, and a loader cannot replace itself. So an
update that needs the room goes, once, through the original firmware: the old loader puts the original
back from this computer's copy, the original's own update service takes the new loader, as for a first
installation, and the new loader installs HyperRig with the presets, captures and IRs of the copy of
HyperRig made just before. It needs both copies on this computer, which the computer HyperRig was
installed with has. If the power or the cable goes on the way, the program goes on from where it
stopped, in whichever loader the pedal is. If it stops while the original is on the pedal, as when the
original does not take the new loader, the program says so: Install HyperRig, then or after starting the
program again, goes on, and the presets come back with it. Later updates are plain ones.

If the cable or the power goes, the program finds the pedal again by its own numbers and offers to
finish. A note beside the copies says which job it was. This is so in the simulator; it was not tried
on a pedal, and nothing is promised for it.

A pedal with another build of the same or of an older version is offered the update. One with a newer
version is not offered an older one.

## Going back

The original firmware comes from the pedal's own copy, the latest one made from an original firmware:
the application and the whole user area, with the amp models, cabs and presets. HyperRig's presets are
in the copy made just before. No stock firmware is in HyperRig.

A copy is needed: on a computer without one the installer does not restore, and it does not finish an
installation that another computer began.

## Checks

| What | With |
| --- | --- |
| The loader's engine: every message, refusal, fault, and the power cut at each flash operation; each rule taken out in turn | `tools/build_mini_stage.py`, `tools/check_mini_stage_engine.py` |
| The compiled loader, with a simulated flash and USB controller | `tools/check_mini_stage_target.py` |
| The update service of the original firmware and the pedal's bootloader, from the person's own copy of M-VAVE's packages | `tools/check_mini_boot.py` |
| The installer with the loader's own engine: installing, updating, going back, messages lost, doubled and damaged, the cable pulled, the power gone, the program closed, another computer, a full disk | `tools/check_installer.py` |
| The built program with a simulated pedal, its locks and its look | `tools/check_desktop_installer.py` |
| `STAGE` in the built firmware | `tools/check_mini_panel.py` |

What they do not show: the real USB controllers, Windows' MIDI, timing, the flash chip itself.

Two things a pedal taught, which the checks have now: Chromium closes a MIDI port in a later task and
drops what arrives meanwhile, so `app/installer/webmidi.js` gives each port one link at a time and
waits for the closing; and the pedal's console can miss the first command after its port is opened, so
`app/installer/serial.js` repeats the questions that change nothing, and sends `STAGE GO` once, only
after a question that was answered.
