# Transition notification and shared gain state

This milestone reconstructs the complete callback at `0x0201a9ea..0x0201aa08`
and executes it inside the recovered transition-request path. The callback's
gain result is calculated by the original instructions and the unchanged gain
table. It is no longer supplied by a notification script in this integration.
Earlier source files and reports remain unchanged.

The new borrowed C adapter also executes the existing request and gain helpers
against mapped firmware storage. This lets scene application share its actual
parameter record, configuration, filters and callback state across the call.
It does not copy the old fixed runtime into a temporary object around a callback.

## Original evidence

The reference is the preserved Alpha11 v2 M5.71 image, SHA256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
The verifier first checks both that hash and the full decoded `app.bin` against
the application unpacked from it.

| Body | Original range, end exclusive | Bytes | Instructions | Status |
| --- | --- | ---: | ---: | --- |
| Installed notification | `0x0201a9ea..0x0201aa08` | 30 | 9 | New complete reconstruction |
| Gain clamp | `0x02007ece..0x02007ee2` | 20 | 8 | Reused |
| Gain table lookup | `0x02007ee2..0x02007ef2` | 16 | 5 | Reused |
| Gain mixer | `0x02007ef2..0x02007f3a` | 72 | 24 | Reused with borrowed storage |
| First gain setter | `0x02007f3a..0x02007f50` | 22 | 8 | Reused with borrowed storage |
| Parameter request | `0x02028a34..0x02028b6c` | 312 | 104 | Reused with borrowed storage |

The new callback bytes have SHA256
`8a638ea84aa410b5e27a433f23716b1b20d13cefd4937dfe6cf094ff685332f8`.
The full report declares 37 complete regions, including existing reset,
configuration, coefficient-generation and sample-processing dependencies. Only
the callback adds an original function; borrowed adapters add no guessed entries.

Recovered startup loads the callback address at `0x0200255e` and installs it at
`0x01c3446c`, callback-array offset 732. The request loads that slot at
`0x02028a92..0x02028a9a` and calls it indirectly at `0x02028a9e` when its sixth
clamped parameter changed and the token is nonzero. These instructions belong
to the declared, locally bound startup/request bodies.

The 49-word capture gain table occupies `0x02033bc8..0x02033c8c`, SHA256
`cd539f2ab0183841f5adecc529273af02213eeb221c7723ef556f9229aa620da`.
The original lookup uses the center pointer `0x02033c28` plus four times the
clamped signed index. No ideal exponential or host floating-point formula
replaces those table words.

The tested MINI v4 input is independently pinned to SHA256
`d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2`.
The verifier binds all 37 loaded code regions, all used coefficient/gain tables,
reset data and prior audio caller windows to that exact image. This is an
offline byte comparison, not a device or audio test.

## Callback and gain behavior

The callback accepts every signed32 argument bit pattern. It divides by five
toward zero, clamps the result to -24 through 24, and stores it at state offset
268. Thus -4 becomes zero and -9 becomes -1. The raw callback itself does not
round its input to a multiple of five; the normal transition producer performs
that quantization before calling it.

The mixer reads the first parameter at state offset 264 and the second at 268.
It clamps each lookup index separately. If the second parameter is nonzero,
the combined word is `(first_scale * second_scale + 0x800000) >> 24` using the
original wide product and rounding bias. Otherwise it keeps the first table
word. The callback then leaves these observable effects:

- State offset 268 contains the divided/clamped second parameter.
- Offset 272 contains the combined gain word.
- Byte 16 is zero, selecting the observed deferred-update flag value.
- Offset 276 increments modulo 2^32.

The first parameter and all other state bytes remain unchanged. The standalone
borrowed setter updates offset 264 and passes its original flag to the same
mixer; the standalone mixer preserves both parameters. Physical gain units
and the eventual audible result are not established by these operations.

## Borrowed request interface

The public interface is
[`hyperrig_dsp_transition_notification.h`](../firmware/include/hyperrig/hyperrig_dsp_transition_notification.h).
Its request accepts an original parameter-address token, a raw signed32 duration
bit pattern, a native-result output and an IO object containing map/call/opaque.
It uses these original windows:

| Window | Bytes | Purpose |
| --- | ---: | --- |
| `0x01c1f7d4` | 68 | Configuration and coefficient divisor |
| `0x01c32db0` | 640 | Stored parameters, pending flag and reset state |
| `0x01c34190` | 768 | Request counter and notification token |
| `0x01c33030` | 176 | Four active filter sections |
| `0x01c330e0` | 176 | Generated transition record |
| Supplied parameter token | 12 | Six signed16 input values |
| `0x01c26890` | 280 | Gain state, needed by the installed callback |

The disabled-bank reset executes before input reads. The request then retains
its six clamped local values across the notification, copies them into stored
parameters, and generates coefficients using configuration and active-filter
state as they exist after the callback. It retains the original signed duration
clamp, wrapped coefficient/gain differences, quantized gain increment, one-step
special case and final pending flag. The scalar clamp, gain conversion and
mathematical coefficient producer reuse unchanged C implementations.

Parameter tokens can refer to existing mapped objects, including scene records.
The corpus includes aliases into configuration, control and gain-state storage,
including an odd byte address. A focused configuration alias deliberately
changes during reset, distinguishing reset-before-read from pre-reading input.
An alternate notification mutates source parameters after the local copy;
stored/staged parameters retain the original clamped local values while the
source mutation remains visible in shared memory.

The installed callback token always executes internally. Other nonzero tokens
retain the prior explicit synchronous callback domain through IO.call, with
one semantic argument and an ignored return value. These alternate callbacks
can mutate mapped firmware state and source bytes, but cannot replace IO,
result storage, allocation lifetimes or filter storage types. Mapping is pure
and stable and preserves the original address relationships. IO/result must
be disjoint from mapped firmware memory; arbitrary host aliases between
distinct firmware windows are outside the API. Re-entry and concurrent changes
are outside the comparison domain.

Return status zero means completion; the separate result is the native request's
zero/one result. New -200 rejects invalid API, -201 reports missing mapping,
and -202 reports an inherited-domain or callback guard. Guards can follow
partial native writes: for example, a missing callback-state mapping is found
after the request counter increments and the pending flag clears. Result is
written only on completion. When reset is required, the previous bound of
-1280 through 1280 for the five stored parameters remains explicit. All incoming
signed16 parameters and signed32 duration bit patterns retain their full domain.

## Comparison and limits

[`dsp_transition_notification_machine.py`](../tools/dsp_transition_notification_machine.py)
extends the frozen transition model with the nine original callback instructions
and four reused gain bodies. The indirect callback pushes its actual native
continuation and executes clamp, lookup, mixer and return in the same register,
stack and memory state. The immutable gain table is loaded at its original
address. Alternate callbacks alone use explicit scripts.

The comparison checks all 13 mapped regions, request results, all sample words,
complete callback-boundary snapshots and preserved guards. Cases cover raw
signed extrema, division around zero, all effective callback clamp intervals,
both gain sources, counter wrap, no-change requests, reset timing, original
address aliases, alternate callback mutations, startup-installed callbacks,
pending request replacement and carried filter histories. Every integration
coefficient and transition record is produced by the actual request path.

The parent agent independently reviewed the complete original request, reset,
notification and mixer against the new C. No mismatch within the documented
domain was found; the review clarified storage alias/lifetime requirements.

The frozen output is `build/reverse-dsp-transition-notification-05`:

| Comparison entry | Cases |
| --- | ---: |
| Raw installed notification | 340 |
| Borrowed mixer | 63 |
| First gain setter | 67 |
| Borrowed parameter request | 381 |
| Real startup | 4 |
| Carried sample processing | 63 |
| **Total** | **918** |

The corpus executes 302 actual installed callbacks, seven alternate callbacks,
4,412 gain-helper calls, 1,792 coefficient producers and 592 numerical filter
calls. It compares 4,492 sample words, 147 carried calls, five callback-mutation
cases and 25 API/domain/mapping guards. The longest comparison takes 10,574
instruction packets.

All nine new instructions are visited. Joined and loaded coverage are both
1,287 of 1,437 instructions. The 150 remaining instructions are inherited:
audio input 2, block 12, ramp 58, residual kernel 6, dynamics configure/get/meter
4/9/11, Q16 conversion 1, and older coefficient setup/staging 22/25. Their exact
addresses remain in the report; prior standalone coverage is not added to this
corpus and they are not relabeled as executed.

All 11 focused instruction-model tests and 384 exact-allocation ASan/UBSan cases
pass. The sanitizer cases include 64 alternate callback mutations. The build
produces 14 pi32v2 objects; the 13 reused objects are byte-identical to their
earlier completed module outputs. Independent read-back verifies all 79 source
hashes and 18 artifact hashes. The new target object is 2,468 bytes.

Final SHA256 values:

| Artifact | SHA256 |
| --- | --- |
| Verification report | `c7c31cbb33f4e9b1179865017df66866c8ddace3c6bbeb6eb56469799dd14159` |
| Build manifest | `55d5c50b00eaf22221a5c240a7da2aeed7f99786b01044b25d4c2d5333a2eb08` |
| New C source | `41608f2b85c8fa778e0713559214eed42277d3413a8a49b078e4b17da425cd45` |
| New pi32v2 object | `01a693b2b116c2d32ecdf2451b19e87dc146cf101b698f456de1e03563b4b0f7` |
| Sanitizer report | `51000b22b5d83677b60718150fc1e9043299abab05cf8ff4939e4bdb44cd5a8a` |

The original capture-gain sample consumer is outside this module. The tests
establish its produced gain word and update flags, and separately carry the
real four-section transition through samples; they do not claim that the gain
word has been applied by the whole audio task. Existing float/ISA assumptions
and the 0..128-sample processing bound remain explicit. This component produces
research objects, not flashable firmware, and performs no hardware operations.

## Reproduce

With the pinned local inputs available, choose a new output directory:

```powershell
python -B tools/build_dsp_transition_notification.py --output build/reverse-dsp-transition-notification-new --mini-image build/hyperrig-mini-installer-one-switch-preview-05/assets/hyperrig-mini-v4.app.bin
```

The builder compiles strict host and pi32v2 objects, runs the focused instruction-model
tests and exact-allocation ASan/UBSan harness, compares original instructions,
and writes a source-bound report and artifact manifest. No ignored prior report
is needed to assemble the source manifest. Development outputs and completed
earlier modules remain preserved; existing output directories are refused.
