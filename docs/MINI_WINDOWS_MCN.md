# Temporary control of Windows polling on MINI

Windows logs from the third installation contain autonomous `TEST UNIT READY`
requests to the ROM disk `WL82 / UBOOT1.00`, interleaved with installer
operations. Coincidence with Win31 alone does not prove a USB conflict or
the cause of the error.

[mini_windows_mcn.py](../tools/mini_windows_mcn.py) opens a second handle only
to the already identified MINI, with `FILE_READ_ATTRIBUTES` (0x80), and requests
`IOCTL_STORAGE_MCN_CONTROL` (0x2D0944). The parameter is a one-byte BOOLEAN:
1 suspends media-change detection, 0 balances the suspension.
The installer's SCSI handle remains separate. The context always closes the
attributes handle, even if its body or logger fails; Windows also associates
restoration with file-object cleanup. It changes neither registry, driver,
hub, power, nor NOR contents.

This procedure follows
[Microsoft documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control).
Microsoft's [ClassPnP sample](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/autorun.c)
shows the suspension-counter check before polling. This does not imply that
every request from other processes is suppressed. The code and BOOLEAN were
also compared against local SDK headers `10.0.19041.0/shared/ntddstor.h`
and `um/winioctl.h`.

Seven simulated tests cover exact access, the disable/enable pair, idempotent
closure, and cleanup after open, control, and logger errors:

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_mcn
```

Physical test `analysis/hardware/mini-mcn-probe-run.json` on 15 November 2026
completed windows of 16 seconds before suspension, 24 during, and 16 after.
All 239 identity queries during suspension succeeded; reader B state and counter
remained unchanged. Detection was explicitly re-enabled and the handle closed.
No NOR writes or resets were performed. Polling reduction must be assessed
against Windows logs for the three windows; IOCTL success is insufficient.
