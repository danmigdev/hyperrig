# Portable MINI installer preview

The Windows preview implements the stock-to-HyperRig workflow described in
[INSTALLATION.md](../INSTALLATION.md). The standalone executable and editor are
packaged without a historical unit dump, preset data, or hardware trace.
The current candidate uses [one-switch recovery](MINI_ONE_SWITCH_RECOVERY.md).
An assisted GUI installation from restored stock 009 to v4 has completed on
the development unit. An unassisted installation remains unqualified.

## Implementation

- `hyperrig/installer/core.py` verifies the exact v3/v4 release variants, linked
  writer/reset payloads, two matching full backups, the common stock 009 boot
  and application bytes, application-only plans, and complete final readback.
  Distinct unit-specific tails are accepted and preserved.
- `service.py` separates backup, review, installation, verification, and boot.
  It owns exclusive backup files and a durable journal. A changed preimage or
  failed verification ends the session without automatic boot or rollback.
- `windows.py` identifies the selected stock MIDI endpoint, requests ROM once
  on that same connection, binds fresh ROM ancestry/arrival, and uses the
  reviewed HYRN/HYW1 payloads and Windows transports. Recovery of transport
  errors uses the existing bounded target-state witnesses. It never blindly
  repeats a firmware mutation.
- `gui.py` keeps device work out of window construction and on a worker thread.
  Install is disabled before matching backups; Boot is disabled before complete
  verification. UAC is an explicit action. Failed sessions cannot be restarted
  through the same controls.

The [UltraRig installer audit](MINI_INSTALLER_UPSTREAM_REUSE.md) records reused
workflow patterns and the G/B assumptions that were excluded. The historical
MINI tools and sealed bundles remain unchanged.

## Distribution and verification

For the first GitHub release, use the [release workflow](RELEASE_BUILD.md). It
rebuilds the Windows executable from the checkout and packages a hash-locked,
sanitized input set from preview 05. The historical builders below remain useful
for reproducing local evidence and require their original private inputs.

`tools/build_mini_installer_one_switch_bundle.py` creates the v4 preview using
an explicit file inventory, exact payload pins, a release seal, and isolated
validation from the copied directory. It can package the already installed
Python runtime with PyInstaller; it downloads no dependencies.

The original v4 preview preserved the protocol-policy JavaScript and disabled
all mutations pending its own evidence. Preview 05 derives a separate profile
from a completed [v4 USB controls trial](MINI_V4_EDITOR.md), enabling nine
bounded families. It preserves that policy, displays A/B/C preset banks and
identifies the MINI v4 build. Historical bundles remain unchanged.

The current delivery is `build/HyperRig-MINI-one-switch-preview-05.zip`, derived
from `build/hyperrig-mini-installer-one-switch-preview-05`. The ZIP contains the
entire package; the executable needs its sibling assets and release manifest.
The separate SHA-256 file checks the archive. These checks detect changed bytes;
they are not a publisher signature or hardware compatibility guarantee.

For the source launcher, install the project's `installer` extra in a suitable
Python environment. The packaged executable already contains the runtime.

```powershell
python -m pip install -e ".[installer]"
python -B -X utf8 tools/launch_mini_installer.py --bundle build/hyperrig-mini-installer-one-switch-preview-05 --check-only
```

No flashing occurs in check-only mode. GUI smoke checks also disable device
actions. Simulated transports exercise failure cases separately from physical
observations.

## Physical status on November 16, 2026

The existing v3 MINI was observed normally on USB before a user-assisted
all-three-switch startup trial. That trial did not establish ROM enumeration.
Windows reported a USB descriptor error, Code 43. Reconnecting USB, a complete
user-reported power-off, and software USB recovery did not restore enumeration.
The original editor's stale USB handle was subsequently closed and its process
stopped. A native port-cycle request returned success, but a separate observation
still found no usable application port or ROM disk. Windows then explicitly
reported a pending system reboot when another hub restart was requested.

The MINI subsequently answered the normal HyperRig PONG and read-only MODEL,
LVL, and PSTAT requests over Bluetooth. This confirms application communication,
not the binary hash, audio quality, or USB recovery. No flash write was performed
in those trials. The one-switch v4 image was still uninstalled at that point.

After the PC restart, normal v3 USB communication returned. A separate
[development upgrade](MINI_ONE_SWITCH_UPGRADE.md) installed v4 using two matching
fresh backups, another pre-install read, two sector writes, and a full final
readback. Every byte outside the application was preserved. Normal software
boot and USB PONG/MODEL/LVL/PSTAT reads succeeded. A subsequent user-assisted
cold start with the left footswitch alone produced fresh ROM enumeration and a
valid INQUIRY. The other individual switches and v4 audio remain untested.

The development MINI was then [restored to the original stock application](MINI_STOCK_RESTORATION_LIVE.md)
at the user's request. Three matching pre-installation reads, 126 verified
sector writes, and a complete final read established the stock application
and preservation of all external bytes. Stock USB boot and a real
`TANK MINI_009` MIDI identity succeeded. This prepares the user-operated
portable installer trial; it does not itself qualify that installation path.

Two subsequent GUI attempts stopped during stock-to-ROM USB entry, before any
ROM command or flash write. Preview 03 corrected MIDI input cleanup; preview
04 adds [backup continuation after USB recovery](MINI_INSTALLER_USB_CONTINUATION.md).
The development PC needed a separately requested hub restart. The app can now
continue from the recorded entry instead of requiring another mode change.

The continued GUI session then completed two matching stock backups, another
pre-installation read, 126 verified sector writes, and complete final readback.
One read-only USB error was reconciled without retrying a flash mutation.
The user booted HyperRig through the GUI and confirmed that its editor
connected and displayed data. Independent PING/MODEL/LVL/PSTAT reads also
passed. Evidence is retained in `build/mini-first-user-install-04`; audio
and editor writes were not tested.

`tools/mini_usb_port_cycle.py` is a separate development diagnostic for the
recorded failed port on this PC. It checks the exact leaf, parent, problem code,
and port before one request, journals the intent, and records completion without
claiming enumeration. It is not included in the portable installer. Its Windows
API is documented by [Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_hub_cycle_port).

Outstanding work includes the other individual footswitches, audio and editor
write qualification on v4, an unassisted stock-to-v4 trial, and portable
interrupted-installation recovery/restoration. The preview must not be described
as a generally qualified release.
