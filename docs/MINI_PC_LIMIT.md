# MINI: exception in appended code

The real editor test of 16 November 2026, preserved in
`build/mini-desktop-real-03/connected-proof.json`, received the complete
`tankm_fw M5.71 rel ble` PONG with the `safe` suffix, plus state, model,
presets, and diagnostics. The application genuinely communicates over USB CDC.
This test does not yet qualify audio or preset mutations.

The preceding crash contains `cpu=0`, `dbg=0x1000`, `emu=0`,
`reti=0x02076AAE`, `rets=0x020053AA`; the ETM trace begins at `0x02076AAC`.
The primary SDK source maps bit 12 of `DBG_MSG` to `c0_pc_limit_err_r`.
The saved PC is at entry to the v2 audio adapter, before its GPIO/codec calls;
the return matches the modified original call at `0x020053A6`.
Exception delivery may be delayed: RETI alone does not certify the last
completed instruction.

Original `debug_init` code sets the shared registers as follows:

| Register | Address | Original value |
|---|---:|---:|
| `PC_LIMIT0_H` | `0x01EEE380` | `0x02056780` |
| `PC_LIMIT0_L` | `0x01EEE384` | `0x02000120` |
| `PC_LIMIT1_H` | `0x01EEE388` | `0x01C1F088` |
| `PC_LIMIT1_L` | `0x01EEE38C` | `0x01C00000` |

CPU0 calls `debug_init` at `0x020011C6`, CPU1 at `0x02000AE6`.
The CPU1 branch programs both ranges. The added entry guard runs before this
initialisation; the audio adapter is called afterward. This explains why the
entry guard could start despite lying outside the old flash-code range.

The proposed correction changes a single six-byte instruction at
`0x0200067E` (area offset `0x67E`, NOR `0x467E`):

```text
c1 ff 80 67 05 02   r1 = 0x02056780
c1 ff f2 74 07 02   r1 = 0x020774F2
```

`0x020774F2` is the actual end of `app.bin` for the v2 append, including the
entry guard. The API calculates the new instruction from parameter
`executable_end`; the verifier requires it to equal
`0x02000120 + len(app.bin)` in the JLFS container with valid CRCs.
It does not remove PC protection. The lower flash limit, RAM range, stack and
write checks, and all debug enables remain identical. The flash range now also
includes initial RAM data between the original text and the append: with the
two existing ranges, this is the consequence of a contiguous extension, not
hardware separation of code and data.

In original G, value `0x02056780` also appears in instructions at
`0x020001B8` and `0x020001DC`: there it is the RAM-copy source.
The module checks all three literal occurrences and changes only the PC-limit
one. Global replacement would break startup.

New files, separate from installed artifacts:

- `firmware/mini/pc_limit_port/patches.py`: a patch with assertions, consumer
  inventory, setter-instruction simulation, and candidate gate.
- `tools/audit_mini_pc_limit.py`: links physical PONG/crash evidence to installed
  bytes and the SDK source; produces only an offline report.
- `tests/test_mini_pc_limit.py`: positive and negative cases for both CPUs,
  exact bound, RAM copy, debug enables, CRC, and evidence identity.
- `research/mini-pc-limit.json`: input hashes and model results.

```powershell
C:\Python312\python.exe -B -X utf8 -m unittest tests.test_mini_pc_limit
C:\Python312\python.exe -B -X utf8 tools/audit_mini_pc_limit.py --output research/mini-pc-limit.json
```

The offline test locates and corrects the wrong limit. It does not prove that
the new image has executed the codec, started I²S, or produced audio; these
remain outcomes to observe after a future separate installation. The module
neither clears the persistent crash nor forces an exit from safe mode.

The SDK source is
[JieLi AC79 `debug.c`, commit ffbb2a8](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/cpu/wl82/debug.c).
Its local copy and SHA256 are listed in the report; original attributions and
licences remain those of the preserved sources.
