# First CDC connection within the same opening

`tools/probe_mini_app_cdc_handshake.py` is a new diagnostic. It does not modify
the v1 clients or previous results. It follows the original editor loop at
`tankg.html:10351`: at most five PINGs, each with a 700 ms timeout, within the
same opening. DTR=true and RTS=false are required before opening;
the initial wait is 1 second. There are no reopenings or line toggles.

```powershell
python tools/probe_mini_app_cdc_handshake.py --check-only --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-handshake-new.jsonl --queries
python tools/probe_mini_app_cdc_handshake.py --execute --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-handshake-new.jsonl --queries
```

Repeating requires precise evidence: one completed native write of all five
bytes, at least one read after the write, zero RX bytes throughout the attempt,
and only an empty response timeout. Partial bytes, unexpected text, transport
errors, an incomplete write, or a write that already consumes the timeout stop
the session. Late bytes during the drain before the next PING prevent another
send. The failed parser is not reenabled.

The new JSONL retains the attempt number, native TX intent/outcome, RX bytes,
reason for repeating, identity and closure. A late PONG is not causally
attributed to a particular send. `automatic_retry=true` applies only to this
bounded handshake; subsequent permitted reads have no retries, and there is
no mutation API. An empty `--queries` requests only the connection;
without the option, standard reads follow PONG. Completion is never declared
before the port closes.

The default and `--check-only` do not enumerate devices. Tests are simulated
and do not demonstrate a physical MINI response. Requesting DTR does not
prove delivery of the corresponding USB control transfer.
