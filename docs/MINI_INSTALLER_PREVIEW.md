# Portable MINI installer preview

The Windows preview implements the stock-to-HyperRig workflow described in
[INSTALLATION.md](../INSTALLATION.md). The standalone executable and editor are
packaged without a historical unit dump, preset data, or hardware trace.
The current candidate uses [one-switch recovery](MINI_ONE_SWITCH_RECOVERY.md).
No fresh stock-to-v4 installation has been performed.

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

`tools/build_mini_installer_one_switch_bundle.py` creates the v4 preview using
an explicit file inventory, exact payload pins, a release seal, and isolated
validation from the copied directory. It can package the already installed
Python runtime with PyInstaller; it downloads no dependencies.

The v4 editor preserves the protocol-policy JavaScript and binds the new image
hash, but sets hardware verification to false and leaves mutation families
empty. Tests of the actual policy allow identity and read commands and reject
all eight mutation families. Historical v3 tests are identified as historical;
they do not certify the new image on hardware.

The current delivery is `build/HyperRig-MINI-one-switch-preview.zip`, derived
from `build/hyperrig-mini-installer-one-switch-preview-02`. The ZIP contains the
entire package; the executable needs its sibling assets and release manifest.
The separate SHA-256 file checks the archive. These checks detect changed bytes;
they are not a publisher signature or hardware compatibility guarantee.

For the source launcher, install the project's `installer` extra in a suitable
Python environment. The packaged executable already contains the runtime.

```powershell
python -m pip install -e ".[installer]"
python -B -X utf8 tools/launch_mini_installer.py --bundle build/hyperrig-mini-installer-one-switch-preview-02 --check-only
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
in these trials. The one-switch v4 image remains uninstalled.

`tools/mini_usb_port_cycle.py` is a separate development diagnostic for the
recorded failed port on this PC. It checks the exact leaf, parent, problem code,
and port before one request, journals the intent, and records completion without
claiming enumeration. It is not included in the portable installer. Its Windows
API is documented by [Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/usbioctl/ni-usbioctl-ioctl_usb_hub_cycle_port).

Outstanding work is physical v4 installation/boot, the one-switch cold-start
test, editor write qualification, a fresh stock-to-v4 trial, and portable
interrupted-installation recovery/restoration. The preview must not be described
as a generally qualified release.
