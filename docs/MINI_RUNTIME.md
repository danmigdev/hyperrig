# HyperRig IRQ/audio runtime for TANK MINI

The component in `firmware/mini/runtime/` connects the ALNK callback to the
worker that runs the engine in 64-sample blocks. It compiles for pi32v2 and has
host tests with simulated buffers and registers. **It has not run on the pedal**:
DMA ownership, cache coherence, IRQ latency, and DSP time remain open hardware
requirements. The report keeps all these results at `false`.

## Evidence and protocol choice

The verifier rechecks the MINI_009 FWSC SHA-256, decodes `flash.bin`, and
compares the local application area. The report records hashes and addresses
of three stock fragments:

| Fragment | Observed behaviour |
|---|---|
| IRQ11 `0x01C0374A..0x01C037DC` | Saves PSR/RETS/RETI and r0..r5, reads pending/half, RX callback, ACK, `csync; rti` |
| Callback `0x01C03EEE..0x01C03F24` | Writes the half byte to `0x01C1B22C`, calls semaphore post at `0x02044D44` |
| Task `0x01C03F24..0x01C03FB4` | Waits at `0x020456F8`, selects offset `half<<9`, calls DSP `0x01C03A18` with 64 frames |

The ALNK=11 IRQ mapping and ISR table `0x01C7FE00` are also confirmed by the
[SDK header pinned to a commit](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/hwi.h).
HyperRig uses its own state and buffers; it does not call stock tasks,
semaphores, or data addresses.

Each newly completed half replaces the previous half's availability window.
The runtime therefore keeps **only one pending event**, a sequence counter,
and an active worker. A second event while the first is still pending signals
overrun; an event during worker execution signals a missed deadline.
A half that DMA may already reuse is not queued.

A repeated half after a completed block produces a phase error. The first
half may be 0 or 1. A uint32 counter can wrap from `0xffffffff` to zero:
zero remains a valid token. This check cannot detect every possible
lost/coalesced IRQ, particularly multiple unobserved periods.
Future integration also requires measurements and controller checks.

## API and synchronisation

`hyperrig_mini_runtime_init()` copies hooks, checks implicit sizes,
32-byte alignment, and lack of overlap between state/RX/TX, then clears state.
RX and TX each contain 256 words: 1024 bytes in two 512-byte halves.
Rejected arguments do not change the context. Init/reinit requires stopped
DMA, a disabled IRQ, and no active worker.

Audio-adapter callback configuration:

```c
device.ready = hyperrig_mini_runtime_ready;
device.user = &runtime;
```

`ready()` updates metadata only and calls optional `wake_from_irq`.
`work()` claims the event, copies RX into private staging, converts left/Q23
to the model's Q format, calls `process(process_user, input, output, 64)`,
prepares private dual-mono TX, and publishes into the authorised half.
Both Q formats are explicit in `ops.input_fraction` and
`ops.output_fraction`; they are not stock calibration.
DSP and copy/cache operations do not execute in the ISR.

The worker returns `IDLE`, `DONE`, `BUSY`, `FAULT`, or `INVALID`.
`inspect()` provides a protected snapshot of sequence, pending/busy,
first error, and counters. A fault persists until reinit; subsequent events
are counted and ignored. Silence is not guaranteed after an error: TX might
still contain a previous block or might already have been written before a
cache/end failure. The board must stop or silence the peripheral through a
verified mechanism and reset the engine when its temporal history is no
longer valid.

The contract is **CPU0 only, one worker, no other ISR modifying the context,
and no CPU1 access**. Enter/leave hooks bracket all shared metadata.
The target implementation saves ICFG, clears bit8, executes `csync`, then
restores exactly the saved flags with a barrier. The assembly has a `memory`
clobber; external calls and these barriers prevent the compiler from retaining
the mailbox outside the protected region. Correctness does not derive from
`volatile`. These primitives are not an inter-CPU lock, do not stop DMA,
and do not exclude non-maskable exceptions. Do not change this contract by
introducing LTO/inlining of hooks without re-examining generated code and
barriers.

## Ownership and cache: board obligations

Mandatory hooks `begin/end(direction,half,sequence)` delimit only copy/cache
operations, not DSP. `begin()` must guarantee physical availability of the
half **throughout the transaction**, by stopping DMA or providing a demonstrated
time window covering cache, copying, and margin. Reading the half bit and
disabling CPU IRQs is insufficient: DMA would continue independently.
The board must also establish RX/TX phase alignment before using the same
half number for both.

| Transaction | Worker order |
|---|---|
| RX | begin RX, token check, `rx_for_cpu`, token check, copy 128 words to staging, end RX, token check |
| Processing | convert 64 samples, DSP, token check, prepare private TX |
| TX | begin TX, token check, copy 128 words, `tx_for_device`, end TX, final check |

Every successful begin has an end, even on error. A failed begin must leave
no active lease; end must release it even when failing. The software sequence
check prevents publications already recognised as expired, but does not replace
the physical lease guarantee. A fault observed after copying cannot undo
writes that have already occurred.

`rx_for_cpu` and `tx_for_device` are explicit hooks, mandatory even for
memory declared coherent, where at least verified barriers are needed.
They receive an aligned address and 512 bytes, or 16 complete/exclusive
cache lines. One possible integration with `firmware/mini/platform/` is:

- Before starting DMA: initialise TX to zero, make both buffers coherent,
  and keep RX strictly read-only for the CPU.
- RX: `hyperrig_mini_cache_range(..., HYPERRIG_MINI_CACHE_CLEAN_INVALIDATE, ...)`
  only if it is proven that no RX line is dirty; a dirty writeback after DMA would
  overwrite newly received samples.
- TX: `hyperrig_mini_cache_range(..., HYPERRIG_MINI_CACHE_CLEAN, ...)` while the
  CPU retains ownership of the half, including cache cost/timeout within
  the guaranteed window.

The platform reconstructs `flush`/`flushinv`, 32-byte alignment, and waiting for
bit14 at `0x01EEE008`. The runtime does not turn this evidence into assumed
DMA coherence: mapping, cache mode, CPU1 exclusion, and deadlines must be proven.
Test hooks operate on ordinary host RAM arrays; they are not board drivers
that can be reused as empty hardware hooks.

## Interrupt wrapper and ABI limits

`hyperrig_mini_runtime_irq_bind(device)` binds the device without reading
registers. It must be called with DMA stopped and IRQ11 disabled on both cores;
NULL removes the binding. It requires a valid, inactive callback and context.
It neither installs a vector nor enables a source. The dispatcher uses
`hyperrig_mini_audio_irq()`, which requires `device.prepared`; binding may
precede preparation, but both must finish before enabling IRQs.
Do not enable an unbound handler: it could not ACK.

The future CPU0 vector can point to `hyperrig_mini_irq11_entry` (IRQ11,
priority 6). The wrapper saves PSR/RETS/RETI and all 16 GPRs, calls the
dispatcher, restores in reverse order, and executes `csync; rti`.
It is **20 bytes of code, with a 76-byte frame**, plus the stack used by called
functions. Wrapper, dispatcher, mailbox, and ICFG primitives are in
`.ramtext.*`; the audio driver and future hooks need a separate placement
check if flash might be unavailable during IRQs.

The verifier also compiles an `__attribute__((interrupt))` function with
the same vendor compiler and the same external call: it saves PSR/RETS/RETI
and r0..r3, then restores and executes `rti`. Our set is a superset of both
the generated and stock prologues. The independent decoder checks bytes and
call relocation and inspects the known ISR call graph to exclude REP/coproc
or additional special registers.

The component's C units use `-mllvm -pi32v2-large-program`: external calls
have `EXTEND_CALL_32M2` relocation (type4, a 6-byte instruction).
Ordinary relative type2 jumps do not cover every crossing between flash
`0x0200...` and RAM `0x01C0...`: these include `finish` to
`fault_locked` and the RAM dispatcher to the flash audio driver.
The verifier checks that the only remaining relocated type2 relative call
is the ASM call between wrapper and dispatcher, both in RAM.
The future application must also use extended or indirect calls when calling
`ready()` from flash; checking the relocatable object alone is insufficient
for the final link.

This **does not prove IRQ delivery and return on MINI**, preservation of hidden
hardware state, IRQs during foreground REP/predicates, mode changes, or nesting.
No arbitrary save of special registers with unknown semantics is introduced.
`wake_from_irq` remains outside automatic audit: it must be short, follow
the C ABI, and perform no context switch, enable no nesting, or use
REP/DSP/coproc/extra special registers. Its instructions must be re-examined
during board integration. An RTOS port requires a dedicated interrupt contract.

## Reproduction and local result

```powershell
python -X utf8 tools/verify_mini_runtime.py
```

The command uses GCC with ASan/UBSan and the pi32v2 toolchain pinned by the
project; on Windows it invokes them through WSL Ubuntu. It produces
`build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o` and
`research/mini-runtime.json`. The component is relocatable, with explicit
dependencies `hyperrig_mini_audio_irq`, `hyperrig_mini_audio_rx_q`,
`hyperrig_mini_audio_tx_q`, and `memcpy` already supplied by the boot runtime.
Audio must be linked only once.

Results: 512 alternating blocks, 55 state/argument/dispatch cases,
7 hook errors, 7 IRQs injected at worker points, 256 frame save/restore models,
and 256 ICFG cases. Checks also cover canaries, the unselected TX half,
cache/copy order, lease release, reentrancy, sequence wrap, and absence of DSP
from the ISR. Frame tests are a state model bound to decoded bytes, not an
interrupt-controller emulator.

On target, the context occupies 1668 bytes (1536 for staging/samples), ops
56, and snapshot 64; the two DMA buffers add 2048 bytes, excluding engine
and stack. The component allocates 1180 bytes of code and data.
At 48 kHz, the nominal budget per half is 1.333 ms: it has neither been
measured nor compared against DSP cost. No pedal command, flash operation,
or installable image is produced.
