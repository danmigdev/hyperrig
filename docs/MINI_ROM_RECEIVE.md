# HYRX ROM reception on the TANK MINI

On November 15, 2026, HYRX received **exactly 260 bytes** on the MINI, with
a raw callback return value of **260**. Two successive records retain
the same data and CRC, with intact guards. This is a physical test of this
single transaction; it does not qualify a general convention for ROM return
values, the NOR writer, or HyperRig application boot.

The sealed report is
[mini-receive-hardware.json](../research/mini-receive-hardware.json). It includes
both complete records, the diagnostic payload, and hashes of the original logs.
The [build manifest](../research/mini-rom-receive.json) remains
unchanged: its `hardware_executed: false` describes the builder's offline work,
while the separate report attests to the physical trial.

## Artifact and protocol

| Item | Value |
|---|---|
| Manifest SHA256 | `a2528e6019de515b9d06055127e93cfc01a3e6d6773fbbee4179e83290feed07` |
| Builder SHA256 | `d5081295beb2785904088e2b08056c746321b1ff2c4fbff44ebac13389fec6c6` |
| Dispatcher SHA256 at the time of the trial | `1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8` |
| Executed slot | `0x01C20000`, maximum span 32 KiB |
| Build tag | `0xE539470B` |
| Image / owned RAM | 2,160 / 3,304 bytes; private state 628 bytes |
| Executed payload SHA256 | `ae427be74db2b12e2170713e6600f19d3c8b8ab1f396040d48fadd687caff403` |
| ELF SHA256 | `339d715b6597402d165d3e2e5bf04ebe385e7dfff7fe12f80004ea75d5462cd7` |

The ROM supplies the `send` and `receive` callbacks and a pointer to the
handler slot. HYRX explicitly initializes its private state, registers the
handler, and returns. Entry and handshake do not call `receive`. The callbacks
use the incoming ROM stack: the examined generated frames reach 68 bytes for
the dispatcher plus helpers, excluding the ROM's internal usage. This is
neither a measurement of stack capacity nor a complete bound for the call chain.

The [C contract](../firmware/mini/rom_receive/rom_receive.h) and
[component README](../firmware/mini/rom_receive/README.md) describe the
exact fields. `FC82` identifies HYRX; `FC83` binds the sequence, length,
nonce, CRC, and seed; a single `FB84` transfers the OUT data; `FD85` returns
a 512-byte LE record. The record ends with CRC32 at offset 504 and `DONE`
at 508. The nonce prevents accidental submissions; it does not authenticate
the command. The client consumes its authorization before OUT and does not
retry an ambiguous transaction. The component contains no SPI, GPIO, or NOR access.

## Physical observation

The FD07 read of the 2,160 uploaded bytes matches the ELF payload
after applying the original USB transformation, restarted for each command.
This match was rechecked offline against the trace, without rebuilding.

The single OUT at `2026-11-15T19:45:27.556347Z` uses sequence 1,
nonce `0x1234ABCD`, seed `0x55`, and expected CRC `0xA14F7A5A`. The payload
is the bitwise complement of the initial pattern; SHA256
`10d2653bf84c5e82647589c1efb0111ea72918d3a6fd1fcd6c9fe4d0feb0081e`.

| Record | SHA256 |
|---|---|
| Sample 1 | `ae29db1045ffcfd9693a495b0f983539438f76909662cf4dc0a8469e299127de` |
| Sample 2 | `8a544e62f4862be688b2e8a5b8be49f6fc4b45727e278894a60f068d4e51e216` |

Both attest to one callback invocation, `RETURNED` state, error 0,
expected data, and intact guards. They differ only in the sample counter
at offset 92 and the final CRC. The count of 260 bytes differing from the initial
pattern measures the data, separately from the raw return value of 260.
Two stable samples do not prove callback synchrony or general DMA/cache coherence.

| Recorded pointer | Observed value |
|---|---|
| `send` | `0x01E008E4` |
| `receive` | `0x01E0089A` |
| `handler_slot` | `0x01C01264` |

These are new values observed in this physical session, not an assumed ROM
map. The probe neither reads nor disassembles the pointed-to memory. The
truncated host-test values in the manifest do not represent ROM addresses.

## Reset and return to stock

Reception had already succeeded when the separate 26-byte reset was uploaded
and read back in slot B at `0x01C28000`, SHA256
`cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f`.
Its single jump produced transport error 121. The original run
ends with `stock_return_verified: false` and remains unchanged: the reply
to the jump does not demonstrate reset completion.

The subsequent hub restart is recorded separately. The pinned helper
can perform it only after finding USB problem 43 on a child device
of that hub; this supplies documentary support for code 43 without assuming
an additional PnP snapshot. Neither the pedal reset nor the HYRX OUT
was retried.

Only `mini-receive-stock-return.json`, completed at
`2026-11-15T19:51:35.367773Z`, attests to the return to `TANK MINI_009` and two
matching preset reads: 1,942 bytes, SHA256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`,
unchanged from the backup. This is the sixth verified return to stock;
this episode includes the hub restart. It does not prove recovery from
corrupt flash or an autonomous reset that always works.

## Offline checks

The previously pinned manifest attests to 291 C cases with ASan/UBSan, including
all 260 partial prefixes from 0 to 259 bytes, differing return values,
corrupted guards, late writes, and malformed commands. These tests were
not rebuilt while sealing the evidence. The new verification checked
14 files pinned by hash, the ELF layout, the payload read back in the trace,
both records, and 19 command/result pairs; there was no device access.

To recheck the records included in the report, run the following Python code
from the repository root. It does not invoke the builder or require
the private logs in `analysis/hardware`:

```python
import hashlib
import json
from pathlib import Path

report = json.loads(Path("research/mini-receive-hardware.json").read_text(encoding="utf-8"))
builder = Path("tools/build_mini_rom_receive.py")
expected = report["execution_pins"][builder.as_posix()]
assert hashlib.sha256(builder.read_bytes()).hexdigest() == expected
from tools.build_mini_rom_receive import validate_record

request = report["diagnostic_payload"]
for sample in report["records"]:
    checked = validate_record(
        bytes.fromhex(sample["record_hex"]),
        base=report["target_artifact"]["base"], build_tag=report["build_tag"],
        sequence=1, nonce=request["nonce"],
        payload=bytes.fromhex(request["hex"]), seed=request["seed"],
    )
    assert checked["record_sha256"] == sample["record_sha256"]
    assert checked["observed_complete_and_stable"]
    assert checked["raw_return"] == 260
```

This trial does not enable NOR writes, install firmware, or validate
application boot or audio. HYRX cannot interrupt a blocked ROM callback;
error cases and other lengths have not been qualified on the pedal.
