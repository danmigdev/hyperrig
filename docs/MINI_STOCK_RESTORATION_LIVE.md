# Development restoration from v4 to stock

This procedure restores the original M-VAVE application on the development
MINI before a separate trial of the portable stock-to-HyperRig installer.
It is a reviewed development workflow, not a restoration control in the
portable application.

## Sources and write boundary

`hyperrig/installer/restoration.py` validates the sealed v4 release and its
writer ELF and payload. It uses the historical `StockRestoration` contract and
full-read validator without changing the old planner or its source pins.
The historical planner binds documentation hashes from its original source
snapshot; the new adapter has separate provenance.

The target comes from this unit's original full backup:

- Full backup SHA-256:
  `72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180`.
- Stock application SHA-256:
  `11ade0ace13c48d1b633669ee8beae71d98a269690f1ffb93eb2c6ce14922eda`.
- Required current v4 application SHA-256:
  `d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.

The adapter requires two identical fresh 1 MiB reads and matching original
SPL/configuration and key/MAC bytes. A third full read must still match before
writing. Only `[0x4000,0x82000)` may change. Every other byte is preserved from
the fresh reads, including current user data. This does not restore historical
presets or claim a whole-device factory reset.

The existing bounded writer checks its complete preimage, writes changed
sectors with the header sector and header page last, and verifies the complete
application. A separate full read then checks the stock application and every
external byte. Boot is a separate request after that validation; a failure
causes no automatic boot, rollback, or repeated mutation.

## USB recovery on the development PC

The first v4 software-entry attempt in `build/mini-stock-restore-01` did not
observe ROM after one UBOOT command. It stopped before uploading a reader or
writing flash. That failed session remains unchanged.

At the user's request, the exact recorded USB hub was restarted with
`pnputil /restart-device`. This returned exit code 0 without a Windows reboot
request. After the user reconnected the MINI to the same port, normal HyperRig
USB returned on COM3. Evidence is retained in
`build/mini-stock-usb-hub-restart-01.json` and the subsequent USB observation.
This is a PC-specific recovery observation, not a portable installer feature.

`hyperrig/installer/rom_entry_observed.py` preserves the earlier entry code
and adds a separate implementation. After one UBOOT, it observes the existing
CDC connection before closing it, with bounded reads and a timeout. It does
not repeat UBOOT or issue control-line toggles during that observation. Fresh
ROM ancestry, arrival time, and INQUIRY are then independently checked. This entry succeeded for
`build/mini-stock-restore-02`; the observation does not establish the cause of
the earlier USB failure.

`cold_rom.py` and `tools/restore_mini_stock_recovery.py` provide a separate
manual cold-entry path. They were tested offline but were not used for this
restoration.

## Staged requests and evidence

The reviewed worker retains the active transport while waiting for requests.
`tools/restore_mini_stock_live.py` defaults to file-only preflight. Its stage
requests independently revalidate the sealed release, original unit backup,
fresh reads, and canonical restoration plan:

```powershell
python -B tools/restore_mini_stock_live.py --restore --output build/mini-stock-restore-02
python -B tools/restore_mini_stock_live.py --boot --output build/mini-stock-restore-02
```

These are explicit stages for the existing reviewed session, not commands to
replay after a completed or failed session. The `--boot` request additionally
requires complete final verification. A new execution needs a new destination
and fresh hardware identification.

Private session evidence includes the two initial reads, third read, canonical
plan, USB/write journal, final full read, verification, and separate boot
observation. Stock USB enumeration, a real `TANK MINI_009` identity response,
and audio are separate checks. The current evidence does not qualify an
interrupted-write recovery or restoration on another physical MINI.

Offline verification covered 11 live-restoration tests, 16 historical
restoration tests, 6 manual cold-entry tests, and 11 observed-entry tests.
Those tests do not establish hardware or audio behavior.

## Physical restoration on November 16, 2026

The restoration completed in `build/mini-stock-restore-02`. Both initial
1 MiB backups and the third read matched:
`f39047c4ad282a0171621e3fa0e8473452c0e66624d7a0662ecc35c63275b78a`.
The writer erased and verified 126 application sectors and programmed 2,016
pages. The observed sector and page addresses exactly matched the plan, with
page `0x4000` last. No USB command error was recorded in this session.

The final full read matched the original stock application plus every external
byte from the fresh preimage, SHA-256:
`1e6582755117f19b8291cab9795c0b9f06c487433675086bec7951391461e6e5`.
Independent file and journal reviews are retained as `independent-before.json`
and `independent-after.json`. This full image differs from the historical
backup because current user data was preserved.

After the separate boot request, stock USB `4C4A:C755` returned with status OK.
A real read-only MIDI exchange identified `TANK MINI_009` through input
`USB-Midi 0` and output `USB-Midi 1`. The MIDI handles were then closed and
the temporary administrator broker stopped. The complete result is in
`hardware-summary.json`; the USB and MIDI observations remain separate files.
Audio was not tested. This restoration is separate from the subsequent
user-operated portable installer trial.
