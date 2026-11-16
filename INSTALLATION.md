# Install HyperRig on a stock TANK MINI

**Status as of November 16, 2026: Windows developer preview.**
A portable installer with a standalone Windows executable is now available in
the local build. It automates identification, per-device backup, installation,
full readback, and a separate boot step. The complete new workflow has not yet
been tested on a stock pedal. Installation remains developer-assisted, and no
GitHub release has been published.

The physical installation started from M-VAVE `TANK MINI_009` on one pedal.
It went through HyperRig v2 and then v3. The new preview targets v4, which changes
recovery to accept **any one footswitch held during power-on**. V4 has been built
and checked offline; it has not been installed or physically qualified. Other
stock versions and hardware revisions have not been qualified either. These
revision labels identify internal port builds, not published release versions.

The current preview directory is
`build/hyperrig-mini-installer-one-switch-preview-02`. Extract the whole package
and open `start.cmd` or `HyperRig-MINI-Installer.exe`. Opening the window performs
no device operations. `check.cmd` validates the package without accessing a
pedal. A Git checkout does not include the generated package or its input assets.

## What the user needs

- A TANK MINI, a USB data cable, and stable pedal power during installation.
- A 64-bit Windows PC. The bundled executable includes its Python runtime.
  ROM access requires a Windows UAC confirmation; the editor does not require
  elevation. Opening the installer does not request UAC automatically.
- Local storage for a private backup of that exact pedal, plus a second copy
  kept separately.
- Access to the project maintainer for a reviewed installation session. The
  repository is currently private; repository access alone does not supply a
  ready-to-install firmware/editor package.
- An instrument and headphones or an amplifier for the final listening check.

The selected installation path uses USB. It does not require opening the pedal,
soldering, a Raspberry Pi, or an external recovery dongle. This describes the
working stock-to-ROM path; recovery from an interrupted flash write is a
separate, unresolved qualification.

## The installation journey

These controls exist in the preview. Their state transitions have been tested
offline; that does not establish a successful installation on another pedal.

1. **Identify the pedal.** Close other pedal editors, connect one powered stock
   MINI, and open the installer. Choose **Enable installation (Windows UAC)**,
   then **Find connected devices** in the elevated window. Select the MINI's
   MIDI input and output. The installer requires stock `TANK MINI_009`, matching
   boot/application bytes, and the supported flash chip. Unknown versions and
   hardware are rejected. This is not an installer for TANK-G or TANK-B.

2. **Save the original state.** Choose a private backup folder and click
   **Create and verify backup**. The installer reads the stock presets, requests
   ROM download mode through the stock USB MIDI command, and creates two full
   flash reads. The copies must agree and pass content validation before any
   erase. Keep this backup private and tied to this pedal. Someone else's dump
   or the manufacturer's update file is not a substitute. Automatic conversion
   of stock presets into HyperRig presets has not been qualified.

3. **Review the installation.** Keep a separate copy of the verified backup.
   The installer prepares a plan for its bundled, hash-checked MINI image and
   rechecks the complete flash immediately before writing. HyperRig
   replaces the complete stock application with the adapted UltraRig-derived
   application. The existing bootloader, boot configuration, and regions outside
   the application are preserved during installation. Retaining those regions
   does not mean that the stock audio application remains in use.

4. **Write and verify.** Click **Install HyperRig** and review the replacement
   confirmation. Keep power and USB connected while the installer writes
   the application and reads the entire flash back. Success requires an exact
   match to the intended application and preservation of every byte outside its
   region relative to the fresh pre-installation read. A progress bar reaching
   100% is not sufficient verification.

5. **Boot HyperRig.** After verification, click **Boot HyperRig** with all
   footswitches released. The installer observes the new USB device; this alone
   does not prove a firmware handshake or working audio.
   Initial entry from stock uses USB MIDI; holding the three footswitches is
   not a verified stock installation shortcut.

6. **Open the editor.** Click **Open HyperRig editor** or use the package's
   `launch_editor.cmd`. Select the MINI in the USB chooser and use one connected
   editor at a time. The COM number varies between PCs. **The v4 preview editor
   currently permits identity and reads only:** v3's earlier mutation tests have
   not been presented as v4 hardware tests. The separate existing v3 editor and
   its eight qualified command families remain unchanged.

7. **Check the result.** Verify the real MINI identity and listen with an
   instrument connected. After v4 installation/boot and editor write access
   have been qualified, the acceptance check must also change an effect, toggle
   bypass, save a preset, restart, and load it again. Those editing controls are
   not yet enabled in this v4 preview. Retain the backup and installation report
   privately.

Before installation, **Return to stock** verifies that flash is unchanged and
boots the original application. It does not restore anything after a write.
Install remains disabled until two matching backups have passed validation;
Boot remains disabled until the complete post-write readback has passed.

## If installation stops

Keep the pedal powered and connected while the operator inspects the error and
the write journal. Do not blindly rerun an installation, reset the pedal, or
substitute another unit's backup. Earlier development sessions encountered
Windows USB errors and required a fresh full read and a new plan before
continuing.

There is no proven automatic rollback. A backup is necessary for restoration,
but it cannot by itself make an unreachable device accessible. The three
footswitch inputs and return-to-ROM command were tested in RAM. The new
[single-switch startup guard](docs/MINI_ONE_SWITCH_RECOVERY.md) has passed
instruction-model checks, but physical cold-start recovery remains unqualified.
The earlier all-three trial did not establish ROM enumeration. Neither guard
can be assumed to run from an incompletely written application.

## What is still needed for independent installation

| Work | Current state |
| --- | --- |
| Distributable MINI firmware, editor, and Windows installer package | Local executable preview built and checked; no GitHub release. |
| Device detection and backup for each user's pedal | Implemented without the historical unit backup; tested with distinct simulated unit data, not a second physical unit. |
| Fresh stock-to-current-version trial | Stock 009 to v2, then v2 to v3, was tested on one MINI; direct stock-to-v4 remains untested. |
| Guided boot and recovery checks | Separate boot step implemented; physical v4 boot and one-switch cold-start recovery remain untested. |
| Editor editing after v4 installation | Current preview allows reads; v4 hardware qualification remains pending. |
| Interrupted-write handling and restoration | Bounded state reconciliation reused; failed sessions stop without reset. Portable resume/restore and application-independent recovery remain outstanding. |

Full panel and LED behavior also remains outside the current qualification.
The working firmware/editor milestone does not establish readiness for general
distribution.

## Developer references

- [Stock USB entry and ROM protocol](docs/MINI_RECOVERY.md)
- [Full flash backup evidence](docs/MINI_FLASH_BACKUP.md)
- [First installation and interrupted-session reconciliation](docs/MINI_INSTALL_RESUME.md)
- [The v2-to-v3 upgrade](docs/MINI_PC_LIMIT_UPGRADE.md)
- [Boot and recovery limitations](docs/MINI_FIRST_BOOT_REVIEW.md)
- [Stock restoration API](docs/MINI_STOCK_RESTORATION.md)
- [Current editor and verified scope](README.md#launch-the-editor)

`tools/plan_mini_install.py` prepares an offline plan.
`tools/install_mini_app.py` exposes an installation API, but its CLI does not
flash a device. The historical `analysis/hardware/run_mini_first_install.py`
is bound to the development pedal and the v2 candidate. None is a generic
installer command for a new user's MINI.

The new workflow is in `hyperrig/installer/`. Build a new preview directory with:

```powershell
python -B -X utf8 tools/build_mini_installer_one_switch_bundle.py --build build/mini-installer-new --executable
python -B -X utf8 tools/launch_mini_installer.py --bundle build/mini-installer-new --check-only
```

The builder needs the locally generated pinned firmware/editor assets and the
installed build dependencies. It downloads nothing and copies only an explicit
inventory. Private dumps, presets, operation journals, and historical hardware
traces are excluded. Required third-party notices are retained.
