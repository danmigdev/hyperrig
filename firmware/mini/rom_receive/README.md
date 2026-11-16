# HYRX: RAM-only ROM receive observer

HYRX registers a callback and uses only its own RAM and USB services supplied
by ROM. It contains no SPI, GPIO, reset, NOR access, or register writes. It
does not change writer gates. Entry and handshake do not call `receive`.

The plugin is separate from HYC1/HYC2/HYRN and is linked in slot `0x01C20000`
or `0x01C28000`, with a maximum span of 32 KiB. All private state is explicitly
initialized; fresh BSS is not assumed. Callbacks remain on the incoming ROM
stack. The generated code's small stack usage must be distinguished from
ROM stack capacity and internal consumption, which are unknown.

| CDB | Direction | Fields and response |
|---|---|---|
| FC82 + FF14 | IN16 | Echo, HYRX, version 1, flags 0, BE32 base, BE32 span 32768 |
| FC83 | IN16 | BE16 seq@2, BE16 length@4, BE32 nonce@6, BE CRC32@10, poison seed@14, FF@15 |
| FB84 | OUT1..260 | BE16 seq@2, BE32 nonce@4, BE16 length@8, FF6@10; no IN response in the same command |
| FD85 + FF14 | IN512 | LE record described in `rom_receive.h`, CRC32 at 504 and DONE at 508 |

FC83 response: echo@0, HYRX@2, BE16 seq@6, BE32 error@8, BE16 length@12,
armed boolean@14, version 1@15. The CBW must contain the USBC signature, LUN0,
CDB16, exact direction, and exact byte count. A malformed private command is
consumed/rejected without calling `receive` to drain it: an incomplete USB
phase may remain and require recovery. Legacy flash commands do not pass to
ROM. Only FB06/FD07/FB08 and standard SCSI are delegated.

States are idle → armed → receiving → returned, or a sticky fault. Sequence
and nonce prevent accidental duplicate sends; they are not authentication.
FB84 consumes the arm before the callback. If the callback does not return,
the plugin cannot impose a timeout: the host must record ambiguity and not retry.

The buffer is initialized with pattern `seed XOR (index*73+0xA5)` truncated to
8 bits, with 16 canary bytes on each side. The client requires a payload that
differs from the pattern at every position. It preserves the raw callback
result, CRC, count of bytes differing from the pattern, and a data copy. That
count is not presented as a received-byte count returned by ROM.

FD85 resamples data, guards, and CRC. Two records may differ only in the sample
counter at 92 and final CRC. A late change fails the session. Two stable
samples remain a finite observation: they do not prove that the callback is
synchronous, that DMA/cache are generally coherent, or that error cases follow
a particular convention.

At 96/100/104, the record contains the `send`, `receive`, and `handler_slot`
pointer values supplied by ROM. The plugin converts them to u32 without
reading other code or memory. In 64-bit host tests, they are only the low
32 bits of process pointers, not ROM addresses. The parser assumes no ROM
address map and introduces no commands to read it.

`MiniReceiveSession.receive_once()` sends FC83, a single FB84, and, if data
and return value are not anomalous, two FD85 requests. A negative return, a
value different from the explicitly expected one, partial data, a changed
record, or a transport error stops the session. Without an expected return
value derived from earlier evidence, the first valid observation still closes
the session: no success convention is inferred. A subsequent session can use
the observed value as a consistency check without qualifying the writer or
the callback's general semantics.

The builder runs C tests under ASan/UBSan: every partial prefix from 0 to 259
bytes, lengths 1/63/64/65/255/256/260, different raw return values, guard
corruption, late writes, duplicate/malformed commands, and simulated nonreturn
using `longjmp`. The test does not cause an actual USB timeout. Python tests
use only fake transports, including on Windows. Import and default CLI do
not enumerate devices or open ports. Only the explicit transport constructor
opens a ROM disk already identified by the caller.
