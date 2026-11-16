# Opening Windows devices from an attested selection

`tools/mini_windows_quiet.py` removes fresh `Win32_DiskDrive` enumeration
from each open and reopen. It inherits `exchange`, `_exchange_once`,
`close`, and the buffered SPT transport's context manager unchanged.
The previous constructor and all frozen protocols remain unchanged.

Importing the module and calling `RomDiskAttestation.from_discovery()` perform
no I/O. Explicit construction of `QuietBufferedRomTransport` opens the selected
device and reads its INQUIRY; it installs, retries, and resets nothing.

```python
from tools.mini_windows_quiet import RomDiskAttestation, QuietBufferedRomTransport

# disk is a single descriptor already selected by the caller, or a descriptor
# retained and verified in its plan. No discovery takes place here.
attestation = RomDiskAttestation.from_discovery(disk)
with QuietBufferedRomTransport(attestation, slot=0x01C20000,
                               profile="app-writer-operational") as transport:
    attestation = transport.attestation
    journal(transport.open_metadata)
    # The caller still verifies HYW1, slot, build, and writer audit.

# Each reopen must reuse attestation rather than recreate it from disk:
# this also preserves the exact interface and USB ancestor's LastArrivalDate.
```

Selection requires an immutable chain of 2–12 devnodes ending at the
`4C4A:8057` USB device. Configuration Manager locates only the attested
`pnp_id` with `CM_LOCATE_DEVNODE_NORMAL`, compares every parent, and
requires started nodes with no problems. It obtains only that instance's
disk interface using `CM_GET_DEVICE_INTERFACE_LIST_PRESENT`; it does not enumerate
all disks. Exactly one name and at most 8192 characters are accepted.
Any error, ambiguity, or change ends the open without fallback. These
filters follow the Microsoft contracts for
[CM_Locate_DevNodeW](https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_locate_devnodew)
and [CM_Get_Device_Interface_ListW](https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_get_device_interface_listw).

The first open binds `interface_path` and `last_arrival_filetime` to the
returned object. Subsequent opens compare them exactly. The property is
`DEVPKEY_Device_LastArrivalDate`, GUID `83da6326-97a6-4088-9453-a1923f573b29`,
PID 102, FILETIME type 16, eight bytes, as defined in Windows SDK
10.0.19041.0 headers `shared/devpkey.h` and `shared/devpropdef.h`.
A new USB enumeration requires a new explicit selection.

The code opens the disk-interface name, then uses
`IOCTL_STORAGE_GET_DEVICE_NUMBER` (`0x002D1080`) and accepts exactly 12 bytes:
disk type 7, a number matching the attested `PhysicalDrive` alias, and
partition 0 or `0xffffffff`. This preserves compatibility with the frozen
MCN control, which opens the PhysicalDrive alias. The IOCTL retrieves the
driver-assigned number without requesting media size or geometry.
[Microsoft contract](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_get_device_number).

Next come the two adapter-descriptor queries already used by the backend
and a 36-byte buffered INQUIRY, with exact vendor `WL82` and product `UBOOT1.00`.
The PnP chain, interface, and LastArrivalDate are checked again after INQUIRY.
A change closes the handle. The `open_metadata` record retains the actual
interface, disk number, attestation, and duration.
`transport.disk['path']` remains the original alias; `opened_interface` indicates
the path actually opened.

The new constructor removes an observed behavior: in the first four reopens
of the fourth attempt, the previous discovery coincided with a READ CAPACITY,
two TURs, and approximately 11.1 seconds before the new HYW1 identity.
The local export is
`build/mini-windows-diagnostics/stordiag-mcn-install-initial.json`.
Separate groups of six TURs coincided with Win31 before reopening.
This change therefore does not demonstrate elimination of all Win31 errors
or traffic from other Windows components. Attestation identifies continuity
of the PnP selection; it is not cryptographic authentication of the pedal.

Offline verification passed 20 new tests and 58 tests in total with
the backend and v2 recovery. All native APIs are simulated. Tests cover
an absent/replaced device, enumeration changes during opening,
an incorrect chain, multiple/truncated interfaces, limits, INQUIRY failure,
a different disk number, handle closure, and identity of inherited functions.
No physical trial was performed by this tool. Initial physical qualification
must precede any WREN: INQUIRY, the expected plugin identity, and a complete
read of the expected preimage remain runner gates.

```text
python -B -X utf8 -m unittest tests.test_mini_windows_quiet tests.test_mini_windows_spt tests.test_mini_read_recovery_v2 -q
```
