# Explicit restoration of the MINI stock application only

[restore_mini_stock.py](../tools/restore_mini_stock.py) prepares and reuses the
bounded writer for the HyperRig/incomplete app→stock app direction.
The writable range remains exclusively `[0x4000,0x82000)`.
It does not reboot the pedal, repeat ambiguous commands, or automatically
restore other partitions. Import and CLI perform only local file operations.

The destination is the application extracted from this unit's full backup,
SHA256 `72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180`.
Stock application SHA256:
`11ade0ace13c48d1b633669ee8beae71d98a269690f1ffb93eb2c6ce14922eda`.
The preimage is a fresh full NOR read supplied as a local file with an explicit
expected SHA256. The caller must prove its hardware origin and freshness;
the planner does not infer them from the file's name or date.

SPL/configuration and key_mac must match the pinned backup.
An application with a corrupted header or code is accepted: requiring a valid
CRC would prevent recovery. VM, OTA, BTIF, and USR may differ; the plan lists
their hashes, differing-byte counts, and affected sectors, then preserves the
current read's bytes exactly. This is not equivalent to returning the whole
NOR or presets to the historical backup state.

The factory first verifies operational artifacts through
`prepare_installation()`, then creates an immutable `Installation` with
`purpose='restore-stock'`, the current preimage, and stock destination.
The canonical plan has a hash independent of the stock→HyperRig plan and may
be retained with exclusive creation, flush, and fsync.
`retain_plan()` overwrites no existing file.

API for an explicitly authorised and reviewed runner:

```python
from tools.restore_mini_stock import (
    prepare_stock_restoration, MiniStockRestorationSession,
    validate_restored_full,
)

prepared = prepare_stock_restoration(
    retained_fresh_full_dump_path,
    expected_sha256=accepted_fresh_full_sha256,
    slot=known_inactive_slot,
)
prepared.retain_plan(new_plan_path)

# transport, ROM entry, slot history and durable journal belong to the runner.
session = MiniStockRestorationSession(
    transport, prepared, journal=durable_journal, known_free_slot=True,
)
session.upload_and_start(
    prepared.installation.image,
    expected_sha256=prepared.installation.image_sha256,
)
session.initialize_spi()
session.verify_complete_preimage()
result = session.restore_application()  # leaves ROM active

# A separate read-only lifecycle acquires all 1MiB after the writer finishes.
validation = validate_restored_full(prepared, independently_read_full_nor)
```

The client checks the entire app before the first mutation, checks the sector
again before arming it, and verifies the frozen page through echo, erase,
every PP, the sector, and the complete app. The header sector goes last,
and its page `0x4000` follows `0x4100..0x4F00`. The header is not
invalidated at the start. A power loss can still leave mixed code: this
ordering is not atomic, and MINI OTA fallback is not qualified.
An error terminates the session without reset or automatic attempts.

`restore_application()` attests only the stock-app readback and leaves
external regions unverified. `validate_restored_full()` subsequently checks
the stock app and all external regions against the fresh preimage, separately
reporting any equality with the whole historical backup. Stock boot and
observed identity/presets remain separate hardware tests.

Local verification:

```powershell
python -B -X utf8 -m unittest tests.test_restore_mini_stock -v
python -B -X utf8 tools/restore_mini_stock.py
```

16 tests passed: an unreadable or wholly unknown app, partition endpoints,
different external data, rejection of foreign SPL/key_mac, preimage immutability,
durable logging, header-page-last, lost erase/program responses, missing
preimage, and independent final verification. The transfer test uses simulated
NOR only. The factory was also checked against the real local artifacts,
using the historical backup as a fixture without differences; this is not
a recent hardware read.

Frozen source SHA256
`aca0b65237210b5cd30a9363e66d72cc22dc5f77c0cb0ef8ddceed0653f22324`;
test SHA256
`93880e8fcc758f4d56cd6b27734c92e9741454a700f198c72a6908b2b45e46a6`.
The [dedicated report](../research/mini-stock-restoration.json) distinguishes
these checks from physical restoration, which had not been performed when
that report was captured. A later [development restoration from v4 to stock](MINI_STOCK_RESTORATION_LIVE.md)
verified the stock application, preserved external data, normal USB boot, and
a real `TANK MINI_009` MIDI identity on the development unit. The historical
report and planner pins remain unchanged.
