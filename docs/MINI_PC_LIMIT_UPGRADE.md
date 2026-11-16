# MINI v2 → v3 upgrade

The desktop actually communicated with the MINI on COM3: HyperRig MINI PONG,
37 effect types, model and diagnostics. The first installed v2 was in
`safe` mode, with audio disabled. Evidence is in
`research/mini-desktop-readonly-hardware.json`; it does not certify preset
editing or saving.

Candidate v3 corrects the execution limit that caused the crash on entry
to the appended audio code. Application-area SHA256:

```text
9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c
```

Compared with v2, 11 bytes change in physical sector `0x4000`, including
container CRCs. Audio code, footswitch recovery and the RAM copy remain
identical. On November 16, 2026 at 05:00 UTC, the real upgrade completed
one erase and 16 page programs, with page `0x4000` last.
Independent verification in
[`mini-pc-limit-install-independent.json`](../research/mini-pc-limit-install-independent.json)
confirms the exact application and preservation of every external byte
from the fresh dump; USR had already changed while v2 was running.

Boot v11 observed COM3 at 05:04 UTC. The subsequent
`build/mini-desktop-v3-real-02/` session received the real PONG without
`safe`, `CLKSTATE safe=0` and `LVL m=2`.
Two `STAT` reads observed `T.nproc=328986` and `329126`, as well as
advancing audio input/output and block counters. Analog listening,
preset editing/saving and integrated footswitch recovery remain separate
trials to complete.

The frozen launcher had an 8 MiB evidence-file limit, exceeded by two closed
traces. The [compatibility driver](MINI_V3_EDITOR_DRIVER.md) reads only those
two files up to 32 MiB and checks their size and SHA256;
it records this extension in new editor evidence.

## Prepared sequence

1. Retain the desktop evidence and close its native port.
2. Open a new Web Serial session on the exact
   `Tank-M HyperRig (COM3)` row, receive PONG and send `UBOOT` once.
3. Separately verify the new ROM enumeration, arrival time and INQUIRY.
   An ACK or disconnection alone does not prove ROM.
4. Load reader B and retain a fresh complete 1 MiB read.
   The application must be exactly v2; SPL and keymac must match the backup
   from the same unit. VM, BTIF and USR are preserved as just read:
   after boot, they may differ from the stock backup.
5. Derive the plan from the fresh dump, load writer A and verify the entire
   application before writing. Update only sector `0x4000`,
   programming the header page last.
6. Reload reader B and perform a second complete read.
   The comparison must match v3 exactly plus every external byte from the
   newly acquired image. The independent verifier also checks the raw
   command log.
7. Only after full verification, perform one software reboot and open the
   v3 Web Serial editor as the first client. No Python PING before the editor;
   that path had not communicated with v2.

The installation runner does not reboot the device, automatically restore
stock, or repeat jumps or mutations with unknown outcomes.
It reuses the already verified wrappers to reconcile Win31 errors with
the device's exact state. The temporary MCN pause is closed on every exit.

## Files and checks

- `tools/plan_mini_pc_limit_upgrade.py`: offline plan from a fresh dump;
  four tests, plus independent recomposition using the real candidate.
- `analysis/hardware/run_mini_pc_limit_install.py`: controlled sequence;
  eight tests with real reader, writer and wrappers on simulated protocols.
- `tools/inspect_mini_pc_limit_upgrade.py`: independent verification of dumps,
  CDBs and raw audits; 13 tests, including a complete bundle with a read
  repeated after a justified transport error and an actual counter above
  1 MiB. Those tests emitted no hardware-success report.
- `tools/enter_mini_rom_webserial.py`: ROM entry from the application;
  nine Python tests and 61 JavaScript conditions, without a physical UBOOT trial.
- `tools/build_mini_ultrarig_v3.py` and
  `firmware/mini/pc_limit_port/patches.py`: seven derivation tests and
  14 PC-limit tests.
- `analysis/hardware/run_mini_first_boot_v11.py`: eight tests of the separate
  reboot. The reader counter must match the value actually reconstructed
  by the verifier, including any explained lost reads.
- `tools/launch_mini_desktop_v3.py`: nine tests of the v3-bound editor and
  11 desktop-base regressions. It waits 120 seconds for UIA selection of
  the exact port; it does not use DeviceAccess for the Web Serial chooser.

Reboot pins were completed using finalized hardware reports, dumps and
independent verification. The new editor driver's preflight passed against
the same real evidence before connection.

Static installation preflight had passed with 251 SHA256-bound inputs.
Before execution, the manifest reached 254 inputs, including actual desktop
closure, UIA selection and UBOOT reports. Preflight verifies these files
without accessing the device.

The previous administrator session expired at 00:17:03 UTC.
When the user returned, a new temporary session started at 04:54 UTC with
Windows UAC confirmation. It performed the upgrade and boot;
the Web Serial editor runs without elevation.
UAC settings, services and scheduled tasks were not modified.

Normal boot and real editor communication are verified.
Audio listening, in-app editing/saving and integrated footswitch recovery
remain to be completed. Simulated tests remain distinct from hardware
observations.
