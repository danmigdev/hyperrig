# Windows DIRECT allocation investigation

`tools/mini_windows_aligned.py` is a separate, offline-by-default transport
experiment. It does not modify the frozen ROM transport, writer, installer,
candidate image or any device. Constructing `WindowsAlignedRomTransport`
explicitly opens an identified ROM disk; running the module merely prints its
offline contract. No real aligned-DIRECT transfer was performed by the agent.

## What the saved failures establish

The first install stopped on FD7F/IN256 at NOR `0x5900`; the next attempt,
with 20 ms command spacing, stopped on the same operation at `0x5D00`. Both
reported Windows error 31 immediately, with zero returned SPTD packet bytes.
The initial zero SCSI status and unchanged requested transfer length are not
successful SCSI completions when `DeviceIoControl` returns false.

The second attempt's last validated audit has sequence 30, page bitmap `0x3FFF`,
14 successful programs, error 0, and read counter 547072. The later audit was
byte-identical, SHA256
`a6591142516fbe06eebb654112c534919fe900f7752a685e7fad905dfff495f1`.
The subsequent independent full read confirms fourteen candidate pages in
sector `0x5000`, two erased pages, and stock bytes everywhere else. Its SHA256 is
`7fd0c32e295758fe8a3fdff40f5315cb83fa31091920c5b7f99fdd49aa05e4fc`.
See `analysis/hardware/mini-first-resume-run.json`, its trace, and
`analysis/hardware/mini-partial-inspect2-run.json`.

These observations localize the immediate failure to the FD7F transfer before
any new successful read was recorded. They do not distinguish a Windows/USB
driver rejection from a fast device-side USB rejection. They do not establish
a NOR page/program failure or a timing calibration.

## Microsoft contract and actual adapter metadata

DIRECT carries a pointer to a user buffer that Windows locks for the transfer;
the allocation must survive the synchronous request. Its native x64 header is
56 bytes, with the pointer at offset 24 and sense data at offset 56 in this
implementation. [Microsoft SCSI_PASS_THROUGH_DIRECT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ns-ntddscsi-_scsi_pass_through_direct)

The data pointer must satisfy the adapter's alignment mask. Microsoft documents
querying `StorageAdapterProperty`/`PropertyStandardQuery`, and recommends
DIRECT primarily for larger transfers; small transfers are not prohibited.
[Microsoft IOCTL_SCSI_PASS_THROUGH_DIRECT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through_direct)

Root's read-only adapter query returned:

```
2000000020000000000001001100000000000000000000000700010000000000
Version=32 Size=32 MaximumTransferLength=65536 MaximumPhysicalPages=17
AlignmentMask=0 BusType=7 (USB)
```

Mask 0 imposes byte alignment only. Therefore the old ctypes allocation does
not violate the declared alignment requirement. Page alignment is a controlled
allocation/page-boundary experiment, not a proven correction for error 31.
The descriptor also supplies the transfer and scatter/gather limits.
[Microsoft STORAGE_ADAPTER_DESCRIPTOR](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-storage_adapter_descriptor)

## Separate implementation and limits

`query_adapter_descriptor(kernel, handle)` issues two bounded metadata queries:
the eight-byte header and then its declared complete size, at most 4096 bytes.
It rejects short, changing, unsupported or inconsistent descriptors, including
an invalid mask or zero transfer limits. There is no assumption of mask 0 when
the query fails. This is a query only, with no SCSI/NOR command.
[Microsoft STORAGE_PROPERTY_QUERY](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-storage_property_query)

`AlignedBuffer` owns the backing allocation and its ctypes view. Alignment is
`max(4096, AlignmentMask+1)`; neither the CDB nor transfer length is padded.
An IN256, OUT260 or IN512 buffer starts on a 4 KiB boundary and occupies one
such page. The adapter's maximum transfer and page count are checked first.

`WindowsAlignedRomTransport(path, slot=..., profile=...)` inherits the frozen
USB ancestry and WL82/UBOOT1.00 checks. The new shared
`validate_profile_request` dispatches to exactly the existing ten validators;
it does not add an opcode. The timeout remains 10 seconds. Every failure is
terminal for that handle; there is no retry, reopen, backend fallback or reset.
`last_transfer` records pointer/allocation addresses, page offset/span,
alignment/mask, length, monotonic times, Win32 status, SCSI status, returned
lengths and bounded sense bytes. It contains no flash payload.

The optional FD7F recovery wrapper remains separate. If a runner ever combines
it with a new backend, its explicit `reopen_factory` must construct that same
backend and preserve pacing/logging. The wrapper's old default constructs the
frozen DIRECT transport. It cannot be used to retry OUT, erase, program, finish,
jump or reset operations.

## Offline validation

Sixteen tests replace every Windows API. They exercise the actual descriptor,
malformed/truncated/changing descriptors, immediate last-error capture, alignment
and allocation bounds over 27 size/alignment combinations, exact IN256/OUT260,
larger masks, allowlist and transfer limits, failed/short completions, handle
closure, and imports of all profiles in a fresh Python process.

The frozen transport SHA256 remains
`401f501729e08ecb3efbd54e6d75157989deca5cd3c0c9629bcbf9b076042073`.
The aligned helper SHA256 is
`7d7d9de2de67c08088a0e5e5de820603124582940c35a564918aef025af0d4d4`.

The separate buffered backend completed one physical gate-zero trial on this
unit at 2026-11-15 21:15:58 UTC: 2016 application-page reads of 256 bytes,
one staged page with exact echo, and an independent full 1 MiB NOR read.
All 10,220 logged commands completed; all 2029 HYW1 audits had mutation gate,
WREN, erase and program counters equal to zero. The full NOR remained
byte-identical to the pre-trial partial image, SHA256
`7fd0c32e295758fe8a3fdff40f5315cb83fa31091920c5b7f99fdd49aa05e4fc`.
The source pins, logs, audits and checks are sealed in
`research/mini-buffered-transport-hardware.json`.

That result qualifies this completed buffered transfer trial. It does not prove
the cause of error 31, future error-free operation, NOR mutation behavior or
application boot. The aligned DIRECT backend remains untested on hardware.
