# Local adapter for v3 tests

`tools/run_mini_v3_editor.py` delegates to frozen launchers. It changes no
files, serial protocol, guard, or app permissions. In the desktop module alone,
it temporarily replaces the evidence-file reader: two closed traces already
included in the boot pins receive a 32 MiB limit, with mandatory size and SHA256.

| File in `analysis/hardware/` | Bytes | SHA256 |
|---|---:|---|
| `mini-pc-limit-install-trace.jsonl` | 17590011 | `2258850d612c9971e251fdcc581db0dc97b2e6cb3f355cd015e204624ea7bde4` |
| `mini-complete-install-trace.jsonl` | 10133042 | `8561aff779032f599f6aa4590b8f8ae2c1b60a58bc2fda67911d6f62914bc501` |

Every other read retains the original **8 MiB** limit. A wrong hash, truncated
file, or different path receives no exception. In-memory references are restored
on exit. New `session.json` and `report.json` files record
`evidence_io_extension` and the driver's hash in `source_sha256`, without
altering `prepared`, `inputs`, or earlier evidence.

Real preflight, without browser/device:

```powershell
python -X utf8 tools/run_mini_v3_editor.py desktop --check-only --boot-run analysis/hardware/mini-first-boot-v11-released-run.json --boot-sha256 8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202
```

For authorised launch, replace `--check-only` with `--execute` and add
`--output build/mini-desktop-v3-02`, a new directory. Subcommand `first-preset`
forwards the same arguments documented in
[MINI_BROWSER_FIRST_PRESET.md](MINI_BROWSER_FIRST_PRESET.md) to the frozen trial;
the validator and trial share the same adapted desktop module.

Verification: `python -X utf8 -m unittest tests.test_mini_v3_editor_driver -v`.
Nine offline tests, including the two real traces and preflight of the actual
v11 boot; tests open no browser, serial port, or device.
