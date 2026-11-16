# CDC diagnostic with DTR enabled

The new `tools/probe_mini_app_cdc.py` leaves historical clients and logs
unchanged. It uses the specified manifest, verifies the corresponding
firmware file and requires the exact `tankm_fw` version in PONG.
PONG does not attest to the binary's hash.

```powershell
python tools/probe_mini_app_cdc.py --check-only --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-new-session.jsonl --queries
python tools/probe_mini_app_cdc.py --execute --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-new-session.jsonl --queries
```

`--queries` without names sends only PING. Without that option, the original
client's read set is used. No argument accepts arbitrary commands, mutations,
resets, retries or line toggles.

Opening requires DTR=true and RTS=false before `open`, waits 1 second and
sends a single PING with a 3-second timeout. TX/RX bytes and errors are
recorded in a new JSONL; `session_complete` is written only after the port
has closed. Default mode and `--check-only` do not enumerate devices.

The original CDC handler requires DTR to enable RX/TX: the eight fragments
in `research/mini-cdc-host-open.json` are also identical in v3 firmware
`9c612d2c…e2363c`. Timeouts from the old `probe_mini_app.py`, which requests
DTR=false, do not demonstrate a stalled application task. DTR=true remains
a prerequisite, not a response guarantee: the log attests to the client's
request, not actual delivery of the USB control transfer. The old
`probe_mini_app.py` and `probe_mini_app_host_open.py` CLIs remain frozen;
the latter has a v2-bound preflight and must not be used directly for v3.
