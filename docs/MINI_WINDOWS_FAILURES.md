# Windows errors during MINI installation

Each of the three Win32 31 failures coincides with six automatic
`TEST UNIT READY` requests within 3 ms. The source is the existing
`Microsoft-Windows-Storage-ClassPnP/Operational` log, StorDiag provider;
the analysis sent no device commands. The filter requires `PhysicalDrive4`,
WL82/UBOOT1.00, and the same device GUID, not just the disk number.

| Trial | Failed command | Start UTC | Interval of the six TURs relative to start |
| --- | --- | --- | --- |
| First installation | `FD7F`, 256 bytes, address `0x5900` | 20:48:44.774876 | −1.019 .. +1.451 ms |
| Resume with 20 ms pause | `FD7F`, 256 bytes, address `0x5D00` | 21:00:05.537763 | −2.176 .. +0.317 ms |
| Buffered transport | `FC7E`, 16 bytes | 21:28:00.009604 | −2.134 .. +0.493 ms |

The TURs report `NTSTATUS=0xC0000185`, `SrbStatus=0xC4`, SCSI status 2, and sense
2/3A/00. Local SDK header `srb.h` 10.0.19041.0 decomposes 0xC4 into error
0x04, queue frozen 0x40, and valid autosense 0x80. Microsoft describes
QUEUE_FROZEN as the port driver's indication that the device queue has
been frozen. This state is observed on TUR, not on our vendor CDB,
whose SRB is unavailable in the failed IOCTL reply.
[Microsoft SCSI_REQUEST_BLOCK documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/srb/ns-srb-_scsi_request_block).

The third IOCTL fails in 0.205 ms with zero returned bytes. SPT fields still
at zero or at their initialized values do not prove successful SCSI status
or received sense data. The program uses synchronous IOCTLs and the correct
class device; replacing the direct buffer with buffered transport did not
eliminate the problem. A single handle in the program does not eliminate
Windows storage-stack traffic.
[Microsoft IOCTL_SCSI_PASS_THROUGH contract](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through).

The fresh audit acquired by root after the third error confirms 32 programmed
pages, two completed sectors, WREN34, erase2, NOR idle, zero errors, and
read counter 598016: the last 512-byte read had completed.
The complete `full-partial3.bin` dump has SHA256
`74095e9ae0f69878dd5d708150b419548e28db0cf1dabc0e3076c27cd8873406`;
only sectors `0x5000` and `0x6000` contain the candidate. This permits a
new plan based on actual data, without repeating an ambiguous mutation.

The separate MCN trial retained the RAM reader without changing NOR.
No TURs appear in the 16.001 s baseline or 24.029 s pause windows.
None appear in the following 16.001 s either; immediately after re-enabling,
two `READ CAPACITY(10)` requests and two StorDiag523 notifications are recorded.
The zero/zero comparison does not prove suppression of requests present
before the pause. It demonstrates only successful control, continuity of
the 239 explicit queries, and the restoration required by the runner.

The MCN IOCTL is a documented mechanism for pausing notifications on a single
handle; the Microsoft sample checks DisableCount in the notification path.
Its effectiveness against these errors still requires a test with sufficient
traffic. This analysis changed no registry setting.
[IOCTL_STORAGE_MCN_CONTROL](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control),
[Microsoft classpnp/autorun.c sample](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/autorun.c).

The repeated correlation and queue flag support a problem in the storage
path during TUR requests. They do not identify the causal USB packet or
demonstrate a stale CSW, BOT overlap, or a specific driver defect.
There is no USB packet capture for these trials. Microsoft documents
ETW transfer events for distinguishing that layer.
[Capturing USB traces with Logman](https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/how-to-capture-a-usb-event-trace).

`tools/audit_mini_windows_failures.py` reconstructs
`research/mini-windows-failures.json` exclusively from saved exports and traces.
It retains record IDs, hashes, timestamps, and results even when they do not
support the MCN hypothesis. Query recovery is documented separately in
[MINI_READ_RECOVERY_V2.md](MINI_READ_RECOVERY_V2.md).
