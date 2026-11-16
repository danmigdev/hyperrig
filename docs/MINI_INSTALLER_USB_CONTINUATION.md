# Continue a backup after Windows USB recovery

The development PC can report Code 43 while the stock MINI changes from USB
MIDI to ROM mode. Two user-operated installer attempts on November 16, 2026
stopped during this transition, before any ROM command or flash write.

The first attempt also raised a WinMM input-buffer cleanup error. Preview 03
closes MIDI input before sending the stock soft key, while retaining the same
identified output. MIDI cleanup now attempts to close output even if input
cleanup raises. The next physical attempt passed this cleanup step but timed
out waiting for ROM. An explicitly requested restart of the exact PC USB hub
recovered ROM; enumeration became available too late for that attempt.

Preview 04 adds **Continue backup after USB recovery**. It can continue from
the same window after an eligible entry failure, or find the most recent
eligible entry in the selected backup directory after reopening the app.
It creates a new session and preserves the previous session unchanged.

## Preconditions and checks

Continuation accepts only an entry from the last 30 minutes that:

- Identified stock `TANK MINI_009`, saved two matching preset reads, and recorded
  exactly one stock-to-ROM request.
- Failed during identification and contains no ROM commands, flash reads,
  application plan, or write activity.
- Has an intact preset backup and consistent retained entry evidence.

The Windows backend requires one ROM device and no normal stock or HyperRig
USB device. It compares the cached stock USB connection paths with the live
ROM connection paths, then checks the ROM arrival time and existing transport
attestation. This binds the physical connection; it is not cryptographic unit
identity. It does not reopen MIDI, repeat the soft key, restart a hub, or reset
the pedal.

The normal backup workflow then takes two fresh complete flash reads and
validates the stock application, boot code, flash identity, and per-device
installation plan. Installation remains a separate user action and still
requires another complete pre-installation read. A continuation error stops
without writing. This feature cannot resume an interrupted flash write.

## Artifact lineage and verification

The continuation trial used `build/hyperrig-mini-installer-one-switch-preview-04`;
its sealed release SHA-256 is
`04232f97034ab7eb6598cf55f6907ddcd6b1003d1498cabb64544a4169636bd5`.
Preview 03 and all earlier bundles remain unchanged. Firmware, reader, writer,
reset payloads, editor files, and command policy are byte-identical to preview
03. Only the installer host code, executable, and seal changed.

`build/mini-installer-preview-04-provenance.json` records the derivation and
archive hash. The archive is `build/HyperRig-MINI-one-switch-preview-04.zip`.
The desktop copy and extracted directory were prepared by the assistant for
the ongoing user-operated trial; this is not a published release.

Thirteen new tests cover entry evidence, prior ROM access, stale requests,
changed presets, USB connection/arrival mismatch, and fresh backup consistency.
Together with the Windows and service suites, 55 tests passed. The packaged
executable also passed its isolated package check and offline GUI check.
These offline results do not qualify hardware or audio.

The physical continuation reached fresh ROM attestation and started the normal
two-read backup in private session `20261116-153630-acf3a8f9`. Its source was
the stopped session `20261116-152227-7e0d57ff`. The required PC hub recovery was
performed separately by the developer and is not automated by the app.
The same continued session subsequently completed installation. Both stock
backups and the third pre-installation read had SHA-256
`1e6582755117f19b8291cab9795c0b9f06c487433675086bec7951391461e6e5`.
All 126 sector writes and 2,016 page programs matched the plan, with the header
page last. One failed FD7F read was reconciled using the existing target-state
checks and reissued; no failed flash mutation was retried.

The final full read matched the exact v4 image and all external bytes from the
fresh stock backup, SHA-256
`f39047c4ad282a0171621e3fa0e8473452c0e66624d7a0662ecc35c63275b78a`.
The user requested boot through the GUI; normal HyperRig USB returned on COM3.
Independent native PING, MODEL, LVL, and PSTAT reads passed. The user then
confirmed that the packaged editor connected and displayed MINI data.

`build/mini-first-user-install-04/hardware-summary.json` records the completed
assisted trial, with independent before/after reviews and a separate native
CDC log. Audio and editor writes were not tested during that installation trial.
The later [v4 controls trial](MINI_V4_EDITOR.md) verified representative USB
mutations and save persistence; audio remains untested. This result does not qualify
an unassisted installation, a second physical unit, or interrupted-write
recovery. Sealed package qualification records remain unchanged.

## Measured preview latency

The earlier physical stock restoration spent 666.914 seconds in its writer
phase, including writer setup, complete preimage checks, 126 sector writes,
and complete application verification. Its journal records 36,069 USB commands
and 179,508 events for this phase. The configured 5 ms pause before each command
alone accounts for at least 180.345 seconds of requested waiting; journal
events are also individually flushed to disk.

`build/mini-installer-preview-timing-01.json` records these observations. They
identify substantial host workflow overhead but do not isolate pure device
latency. Timing and durability policies were not changed during the live
installation. The preview's speed still needs separate measured improvement.
