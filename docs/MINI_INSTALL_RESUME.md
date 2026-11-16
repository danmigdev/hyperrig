# A new plan from partially programmed NOR

[resume_mini_install.py](../tools/resume_mini_install.py) prepares a new immutable
plan from the current full read and the same already reviewed HyperRig candidate.
It does not access the pedal, repeat commands from the preceding session, or
perform installations from the CLI.

The first attempt confirmed erase and ten page-program operations in sector
`0x5000`. The subsequent host `FD7F` read of 256 bytes at `0x5900` returned
Windows 31 after about 0.51 ms. A new explicit query found an identical audit:
sequence 22, bitmap `0x3FF`, `read_bytes=544000`, target error zero. The failed
read had not incremented the core's counter. This does not authorise automatic
repetition and does not replace a new NOR acquisition.

The separate full read was preserved in
`artifacts/my-mini-flash/first-install/full-partial.bin`:

- 1,048,576 bytes, SHA256
  `6072644bf91df5a5f310011835f20f534c9004399fa019ac0db2241ffeea8c87`;
- `[0x5000,0x5A00)` matches the candidate's first ten pages;
- `[0x5A00,0x6000)` contains only `FF`;
- every byte outside sector `0x5000` matches the pinned stock backup.

The comparison was repeated offline against the files actually acquired.
The separate physical log is
`analysis/hardware/mini-partial-inspect-run.json`, completed on
2026-11-15 at 20:54:31 UTC with reader B active and no reset.
The planner alone does not attest a file's hardware origin or freshness.

```python
from tools.resume_mini_install import prepare_resume, validate_completed_full

prepared = prepare_resume(
    retained_full_read_path,
    expected_partial_sha256=explicitly_reviewed_hash,
    expected_modified_sectors=(0x5000,),
    slot=0x1C20000,
)
# prepared.installation is a NEW frozen Installation for the bounded client.
# The authorized runner owns slot history, transport and durable journal.
# No old token, sequence number or bitmap is passed to the new client.
```

The factory rejects any hash, size, or sector set other than those explicitly
accepted. It also rejects any difference outside the application compared with
the backup: SPL/configuration, VM including OTA, BTIF, USR, and key_mac.
It accepts only application candidate SHA256
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
The incomplete preimage need not be bootable or pass the app parser.

The real plan retained in `build/mini-install-resume/resume-plan.json` has
SHA256
`06d52f30f00cdedd63f4f0e9356b2dd1d6e536841370d976dcf987775d4a3601`.
It contains 126 sectors to bring to the candidate state, `0x5000` first and
`0x4000` last. The current CRC32 of sector `0x5000` is `0x0A53DF86`.
The client checks the entire current app before mutations; it then checks each
sector again, erases it, and programs all 16 pages. It does not continue
directly from the old page `0x5A00`. Header page `0x4000` remains last,
after `0x4100..0x4F00`.

The expected full NOR after verified completion has SHA256
`a35868ab3a4beb42454070ce46d67efaf695615a670de177343860e88d107c47`.
`validate_completed_full()` requires the exact app and external regions
identical to the previous read. This check does not establish boot, audio, or
footswitch recovery. A power loss during writing can still leave a mixed image;
the process is not atomic.

The separate runner `analysis/hardware/run_mini_first_resume.py` was reviewed
without execution: it confirms reader B and its counter, uploads the new
writer A, verifies the preimage, installs, and acquires a full readback with
reader B. It applies a 20 ms pause between commands; this pause is a test choice,
not proof of the cause of the earlier Windows error. It performs no automatic
retry, reset, or rollback. First boot remains a separate phase, tied to the
verified outcome of this new plan.

Ten local tests passed: explicit hashes/sectors, rejection of any changed
external region, immutability, a new erase with the current CRC, a lost response
without retry, simulated completion, final NOR verification, and CLI without
hardware access. Simulations do not represent physical execution.
Frozen source SHA256
`4d8b1241440c031e2de35cde8378d9354931aae78406db3a11c4912a1a15cebe`;
test SHA256
`d89fde466816e8d7aea81c5f609dbf47524026bb2185f488b9e9a6a0a8b193c3`.
The [local report](../research/mini-install-resume.json) records initial
validation; the physical execution outcome belongs to the runner logs and is
not anticipated by this document.
