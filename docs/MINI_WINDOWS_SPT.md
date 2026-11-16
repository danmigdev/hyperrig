# Windows buffered SCSI transport for MINI ROM

[mini_windows_spt.py](../tools/mini_windows_spt.py) introduces
`WindowsBufferedRomTransport`, an explicit alternative to DIRECT transport.
Importing the module does not open devices. Its constructor inherits
`PhysicalDrive` selection, `4C4A:8057` USB ancestry, and exact
`WL82 / UBOOT1.00` INQUIRY from the existing client; command validation remains
that of the original profiles, through the shared
[mini_windows_aligned.py](../tools/mini_windows_aligned.py) helper.

The new `exchange(cdb, data_out=None, read_length=0)` method uses
`IOCTL_SCSI_PASS_THROUGH` (`0x0004D004`), with data included in the packet.
Microsoft describes this request as buffered and suitable for small
transfers; it requires synchronous operations and does not support a
bidirectional data phase. Access continues through the disk device,
not an adapter that bypasses the class driver.
[Microsoft IOCTL_SCSI_PASS_THROUGH documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through).

## Packet and checks

| Field/area, 64-bit Windows Python | Position or limit |
|---|---:|
| `SCSI_PASS_THROUGH.Length` | 56 bytes |
| `DataTransferLength` | Offset 12, uint32 |
| `TimeOutValue` | Offset 16, 10 seconds |
| `DataBufferOffset` | Offset 24, uint64; an offset, not a pointer |
| `SenseInfoOffset` | Offset 32, value 56 |
| `Cdb[16]` | Offset 36 |
| Sense buffer | `[56,88)` |
| Payload start | `align_up(88, AlignmentMask+1)` |
| Payload size | 1..4096 bytes, within `MaximumTransferLength` |
| Maximum packet size | 8192 bytes |

The packet is initially zeroed. The OUT payload is copied to its exact
position; IN reads only that same region. The data-phase length remains
unchanged: no bytes are added to the command, the 512-byte RAM block,
or the 260-byte STAGE packet. Offsets are relative to the start of the
structure, and the data offset follows the declared alignment mask.
[Microsoft SCSI_PASS_THROUGH structure](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ns-ntddscsi-_scsi_pass_through).

Before INQUIRY, the shared helper reads `StorageAdapterProperty` with
two bounded queries: an 8-byte header and the complete descriptor, up to
4096 bytes. Device identifiers are not requested. The backend uses
`AlignmentMask` and `MaximumTransferLength`; it retains the other fields
in `adapter_descriptor`. An inconsistent descriptor stops the constructor
before the SCSI command.
[Microsoft descriptor](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ns-ntddstor-_storage_adapter_descriptor),
[Microsoft property query](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ns-ntddstor-_storage_property_query).

Output must retain the requested layout, zero SCSI status, and the exact
transfer length. For IN, `bytes_returned` must also cover all requested
data; OUT may return only the header because it does not need to echo data.
The parser never follows returned offsets: it checks that they match those
constructed and uses local indices. Diagnostic sense data is bounded both
by its 32-byte region and by the bytes actually returned. `last_transfer`
records the CDB, direction, offsets, lengths, duration, status, and sense,
without copying payloads.

A Win32 error, nonzero SCSI status, short transfer, or inconsistent reply
makes that handle terminal. There are no retries, automatic reopens,
resets, or DIRECT fallback. A second concurrent exchange is rejected
before I/O. Selecting a new transport remains the responsibility of the
caller, which knows the plugin and installation state.

## Scope of testing

Tests are entirely simulated, including disk opening, queries, and
INQUIRY. They cover layout against independently specified offsets, IN/OUT,
HYRN and 256-byte FD7F requests, 512-byte uploads, 260-byte STAGE, the allowlist,
altered offsets, sense, status, underrun, `bytes_returned`, Win32 error
31, terminal state, and absence of retries:

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_spt tests.test_mini_windows_aligned tests.test_mini_recovery
```

This does not prove that alignment caused the earlier Win32 31 errors.
The descriptor reported by the coordinator for the MINI gives
`AlignmentMask=0`, `MaximumTransferLength=65536`,
`MaximumPhysicalPages=17`, `BusType=7`: it does not demonstrate an alignment
requirement violation. Buffered transport allows a separate test of the path
without DIRECT's user-space `DataBuffer` pointer. Only the coordinator's
subsequent physical trial can establish whether this path works in the
current state; the module neither declares the transport qualified nor
performs any pedal operation on its own.

IOCTL definitions were also checked in the locally available
Microsoft SDK `10.0.19041.0/shared/ntddscsi.h` and `ntddstor.h` headers;
the corresponding
[published Microsoft header](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/ntddscsi.h)
defines the code through `CTL_CODE`, with function `0x0401` and
`METHOD_BUFFERED`. No frozen clients were modified.
