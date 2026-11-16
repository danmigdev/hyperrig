# Windows handle with share mode zero

`tools/mini_windows_exclusive.py` exposes
`ExclusiveBufferedRomTransport(attestation, slot=..., profile=...)`.
It reuses the immutable selection and CfgMgr checks from `mini_windows_quiet`,
the disk number, adapter, and INQUIRY; all transactions inherit the
frozen buffered SPT. The only difference when opening is
`CreateFileW(interface, GENERIC_READ|GENERIC_WRITE, 0, ..., OPEN_EXISTING)`.
A sharing violation ends the attempt. There is no shared-mode fallback,
WMI scan, retry, reset, or service/registry/driver change.

The [CreateFileW documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
requires FILE_SHARE_WRITE for volumes and floppy drives; it does not state
that requirement for a physical disk. This opens the identified disk
interface, not a volume. Share0 requests exclusion of subsequent opens
with read/write/delete data access, but exempts attribute-only access.
Existing data handles may cause the attempt to fail. The module
does not close handles belonging to other processes.

It has not been demonstrated that this raw-device stack applies every
sharing check. In the [Microsoft Classpnp sample](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/create.c),
`ClasspCreateClose` prepares the file context and forwards CREATE to the lower
driver, without a ShareAccess check in its own body. This is a sample,
not the installed Windows binary. In addition,
[device-object exclusivity](https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/specifying-exclusive-access-to-device-objects)
depends on the named object's property and its stack; this module
does not add it.

## Explicit second-open test

The constructor does not perform a contention test. The coordinator can
separately call `probe_competing_data_open(transport)`: one second CreateFile
on the same interface, GENERIC_READ and share READ|WRITE,
without DeviceIoControl or CDBs. The function returns:

| `data_open_exclusion_result` | Observed meaning |
|---|---|
| `denied32` | The second open was denied with ERROR_SHARING_VIOLATION. |
| `not_enforced` | The second open succeeded and was closed immediately. |
| `inconclusive` | An error other than 32; does not prove exclusivity. |

A CloseHandle error is propagated; no further open or retry is attempted.
The test does not change the main handle. CreateFile itself may generate
internal stack activity: the absence of explicit CDBs does not guarantee
the absence of implicit driver requests.

## MCN and polling remain separate

The MCN handle retains FILE_READ_ATTRIBUTES/share3 and its own
disable/enable/close lifecycle, according to
[IOCTL_STORAGE_MCN_CONTROL](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control).
Its compatibility with share0 follows from the attribute exception;
it must nevertheless be observed on the device. The new constructor
neither creates nor manages it.

The same exception prevents any promise that TUR requests will disappear:
[CHECK_VERIFY2](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_check_verify2)
can operate with FILE_READ_ATTRIBUTES. Kernel and filter-driver requests
also remain. Even `denied32` qualifies only that specific second open:
`polling_exclusion_proven` remains false.

## Offline verification

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_exclusive tests.test_mini_windows_quiet tests.test_mini_windows_spt tests.test_mini_windows_mcn
```

72 tests PASS, including 27 for the new module. All Windows APIs are mocked;
the tests verify exact share0, identity/attestation, cleanup, errors without
fallback, second-open results, no IOCTL in the contention probe, and
separate MCN parameters/cleanup. They are not physical exclusion tests.
Local SDK 10.0.19041.0 confirms access values 0x80000000/0x40000000,
FILE_READ_ATTRIBUTES 0x80, and share values 1/2; CHECK_VERIFY2 and MCN_CONTROL use
FILE_ANY_ACCESS. Sources, hashes, and limitations are in
`research/mini-windows-exclusive.json`. No hardware I/O was performed.
