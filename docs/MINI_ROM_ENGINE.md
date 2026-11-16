# MINI ROM probe for the A2L engine

This new plugin qualifies the reconstructed engine on a **synthetic three-layer
fixture**. It is neither the original 23-layer A2 capture nor installable
firmware. It links the same `hyperrig_a2l`, `rechannel`, `layer`, `head`,
and `engine` components used for A2 reconstruction; it introduces no other DSP.
The complete UltraRig/HyperRig port to MINI, including the app, remains the
target outcome. This step verifies loading and computation within available
RAM through ROM.

The [manifest](../research/mini-rom-engine.json) preserves offline build checks.
The subsequent [physical test of 15 November 2026](../research/mini-engine-hardware.json)
executed slot A on MINI: 230 frames, six blocks, and repetition after reset
in 14 blocks produced the expected CRCs. Both executions succeeded with intact
stack and arena guards and 1,288 bytes of observed stack use.
The 8,560-byte payload was read back in full before jumping. Return to stock
firmware was verified through USB/MIDI and two identical preset reads,
unchanged from the backup. No flash writes.

## Reproducible build

```powershell
python -B -X utf8 tools/build_mini_rom_engine.py
```

The [builder](../tools/build_mini_rom_engine.py) uses the toolchain and original
disassemblies already pinned by the project. It opens neither USB nor other
devices. It generates `build/mini-rom-engine/synthetic3.a2l`, `fixture.h`,
an ASan/UBSan host executable, and two ELF/bin pairs for slots `0x01C20000`
and `0x01C28000`. The manifest preserves source, header, fixture, kernel-oracle,
and payload hashes. The build includes 46 host-protocol cases and checks that
reject out-of-bounds ELF files, inconsistent mappings, and altered records even
with recalculated CRCs.

The fixture comes from `synthetic(random.Random(0x48594531))` in
[verify_engine_native.py](../tools/verify_engine_native.py): 728 bytes,
kernels and dilations `1/1`, `6/3`, `15/7`, a four-tap head, and a receptive
field of 117 samples. The seed belongs specifically to this test: golden values
from other fixtures are not reused. The fixture CRC in the record covers the
A2L body, excluding the final four CRC bytes; the SHA-256 in the manifest
identifies the entire file.

## Verified computation

The selftest loads the file with CRC verification, initialises the engine,
and processes 230 deterministic samples in blocks `1, 63, 64, 7, 31, 64`.
The rings of 64, 79, and 162 frames each cross their end at least once.
After every block, it compares three CRCs: cumulative outputs, cumulative
layer sum, and histories/positions. The path includes rechannel, convolution,
input mix, activation, residual, sum, and head.

The builder obtains these golden values by executing original G kernel bytes
in the project's interpreters. Scheduling and contexts are reconstructed,
not emulated from the complete original function. The oracle also repeats
the flow with blocks of 17: 100 signal-kernel invocations in total.
The plugin executes reset and the same repetition in 14 blocks, comparing
output and final state. It does not store an expected output trace generated
by its own C implementation.

## Memory and stack

| Target data | Bytes |
|---|---:|
| Loaded code and constants | 8560 |
| BSS, including private stack and record | 16328 |
| Total slot usage | 24888 |
| Remaining space in the 32768-byte slot | 7880 |
| Model arena: query / aligned usage | 895 / 888 |
| Engine arena: query / aligned usage | 9135 / 9128 |
| Private stack | 4096 |
| Guard below / above stack | 32 / 32 |
| Static bound for the selftest's internal chain | 1288 |

ABI structure sizes are extracted from the target ELF and used to check arena
layout. Host queries differ, at 967 and 9167 bytes, because the ASan program is
x86-64. Each arena has its own guards and eight-byte alignment. The linker and
ELF inspector require code, data, BSS, stack, and record to remain in a single slot.

The [separate trampoline](../firmware/mini/rom_stack/rom_stack_pi32v2.S) saves
eight bytes on the incoming stack, calls the core with the private stack, and
restores SP, RETS, and r4 before returning. Verification of the nine instructions
is described in [mini-rom-stack.json](../research/mini-rom-stack.json).
The core does not invoke ROM services: USB sending occurs after returning to
the incoming stack. The host test uses ASan's normal stack and does not execute
the target trampoline.

The static 1288-byte bound covers the compiled core's frames and direct calls;
it excludes interrupts, ROM, and external callers. The wrapper measures changed
fill bytes and checks guards on return. That measurement can underestimate
reserved but unwritten bytes and does not prove an absolute maximum.
Stack switching was executed in the physical test; maximum use by inherited
interrupts remains unknown.

## Protocol and record

ROM uses the same three-pointer structure and normal C ABI as the preceding
probe. Initialisation copies the send callback, initialises only private state,
runs the test, and publishes the handler. `FC62` reruns the test; `FD63`
reads only its own slot, with sends of at most 512 bytes.
The earlier `FC60` and `FD61` are not handled by this plugin.

The `FC62` response, at most 16 bytes, is:
`FC62 | frames BE32 | HYE1 | errors BE32 | 00 | version 01`.
The send callback's error-return semantics remain unknown; the host must
verify the transfer and entire record.

The record is 128 bytes long. Words are little endian:

| Offset | Field |
|---:|---|
| 0 | `HYE1` ASCII |
| 4, 8, 12, 16, 20 | Version 1, base, span 32768, runs, error bits |
| 24, 28, 32 | Frames 230, blocks 6, layers 3 |
| 36, 40, 44 | Output, sum, and histories/positions CRCs |
| 48 | Output CRC after reset/repartitioning |
| 52, 56, 60, 64 | Model query, engine query, model usage, engine usage |
| 68, 72, 76, 80 | Record address, size 128, build tag, fixture-body CRC |
| 84, 88, 92 | Reserved stack, observed changed bytes, valid stack guards |
| 96, 100, 104 | Repetition histories CRC, blocks 14, frames 230 |
| 108 | Flag: bit 0 indicates the target path with private stack |
| 112, 116 | Last C API result, valid arena guards |
| 120 | CRC32 of bytes `[0,120)` |
| 124 | `DONE` ASCII |

Error bits are defined in
[rom_engine.h](../firmware/mini/rom_engine/rom_engine.h). A valid result requires
zero status and valid guards. The builder exposes
`validate_record(raw, golden, build_tag, base, record_address, runs=..., target=True)`:
it checks every field, CRC, target sizes, and an observed stack value within
`1..4096`. Golden values, tag, and address must come from the manifest of the
image actually uploaded; payload identity and readback remain separate host
responsibilities.

This test does not validate the original A2 capture, flash boot, audio clocks,
codec, I2S, DMA, latency, or app compatibility. It contains no flash access,
GPIO access, or audio-peripheral configuration.
