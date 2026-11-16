# Retained-preset qualification: USB continuation v2

The `browser-retained-save-and-reload-two-sessions-v2` model keeps two real
sessions separate. The `mini-first-preset-ui-04` report remains a failure:
it attests to the four completed UI commands (`GAIN`, restoring `GAIN`,
`PSAVE`, `SNAPSAVE`) without claiming a reload. The continuation must prove
a new `GAIN` and `PLOAD`, compare the reloaded state, and close the native port.
The validator does not reconstruct an artificial six-command session or
modify earlier reports.

V2 concerns only the initial connection:

- A single Web Serial open on VID/PID `3654:5155`.
- Up to five `PING` requests from the original bootstrap. Repetition is allowed
  only after an entirely empty timeout, with the native write completed, no RX
  bytes, and no transport error. No mutation is repeated.
- Identity reconstructed from `getInfo()`, native open, and the exact PONG
  present in RX bytes. When UIA evidence also exists, it is checked separately.
  Its absence is not turned into an invented UIA selection, nor is selection
  attributed to a person.

The earlier model remains separate and still requires its own UIA evidence.
The historical validator version is preserved in commit `b8a786e`; the new
report records the actual hash of the v2 version used.

Bundle creation requires a successful physical continuation and verifies the
entire local chain of sources, responses, save, and reload once. Synthetic
fixtures and incomplete attempts do not grant capabilities. The only planned
families are USB `GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`; BLE, uploads, FX mutations,
and other families remain disabled.

Normal editor startup verifies the seal and local bundle files, without
replaying the historical chain or depending on the trial report's path. PONG
identifies the declared firmware; it does not attest to its hash. A successful
reload is neither an audio-quality measurement nor a general persistence test
after power-off.
