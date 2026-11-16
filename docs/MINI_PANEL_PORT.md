# HyperRig MINI panel: adapting the complete G firmware

`tools/audit_mini_panel_port.py` prepares ten local patches spanning 53 bytes
in the original UltraRig G M5.71 application. It produces no installable file
and does not access the pedal. Stock MINI firmware serves only as the source
for board connections. DSP, events, actions, presets, and protocol remain
those of the G application.

```powershell
python -X utf8 tools/audit_mini_panel_port.py
```

The reproducible report is `research/mini-panel-port.json`. It includes source
hashes, addresses, preimages, new instructions, checks, and test limitations.
The formatter API is:

```python
from tools.audit_mini_panel_port import panel_patches
from tools.audit_mini_ultrarig_port import compose_candidate

# g_plain is the original G app area decoded by unpack_app(g_container).
patches = panel_patches(g_plain)
candidate, report = compose_candidate(
    g_container, mini_fwsc, additional_patches=patches)
```

All patches preserve length and require the exact G hash. Patches for code/data
copied to RAM use the **flash load address**; the report also gives the execution
address. They must not be applied directly to encrypted NOR bytes.

## Incompatible writer and return to the caller

G function `0x02015858..0x020158C2` configures PA0, PA1, PA2, and PA3 as outputs
and serializes 29 bits. PA2 acts as clock, PA3 as data, and PA0 as latch; PA1 is
lowered at the end of transmission. This structure is compatible with a shift
register with enable; the 74HC595 component and its electrical connections
have not been verified on the board.

On the MINI, PA1 and PA2 are codec SDA/SCL, while PA0 and PA3 are switch inputs.
Leaving the writer active would compromise both paths.

The verified direct caller `0x02017568` compares the new frame with
`0x01C1F208`, calls the writer when it differs, and finishes without using the
return value. The 12-byte stub writes the new frame to that same RAM word and
returns. It changes neither the stack, callee-saved registers, nor special
registers; it uses only `r1` as a temporary and preserves `r0`. Original
instructions after the stub remain in the file, unreachable from normal entry.

The LED panel is therefore **disabled**, not ported. The MINI editor keeps
its panel capabilities disabled until the whole path is verified. Blocking
commands in the app alone would not have neutralized this periodic firmware writer.

## Three inputs, two scanners, and the logical map

| Path | Original G | MINI adaptation |
| --- | --- | --- |
| Physical tables | PH6, PH7, PH8, PH9, PA10 | First three: PA10, PA0, PA3 |
| Initialization `0x0201599C` | 5 inputs | 3 inputs |
| Main polling `0x02015AD0` | 5 inputs | 3 inputs |
| RAM IRQ `0x01C03338` | 5 inputs | 3 inputs |
| A/B/C/D logical map | 4, 3, 1, 0 | 0, 1, 2, 3 |

Stock MINI initializes PA10, PA0, and PA3 at `0x02006096`; scanner
`0x0200A060` reads `PORTA.IN` and builds the three bits in that order. Both
firmwares interpret a low level as a press. The order of physical labels on
the pedal has not yet been verified: assigning PA10/PA0/PA3 to A/B/C is an
explicit port policy.

Changing only the GPIO tables would be insufficient: in the original G map,
physical index 2 corresponds to no logical switch. The port changes the four
initial bytes at `0x02075974`, copied to `0x01C1F1F4`, and the configuration
loader at `0x02003F32` to retain an identity map even when it reads an old saved
permutation. It retains four action slots: D uses valid state 3, initially
released, without a physical scanner.

States 3 and 4 lie in the BSS cleared by the original reset,
`[0x01C2030C, 0x01C38050)`. The patch does not invent an index of `0xFF`, which
several G consumers would use unchecked as a memory offset. Original dispatch
`0x02014C04`, timers, and actions remain unchanged. Functionality of fourth-switch
gestures on three buttons is not claimed.

The RAM scanner is part of the IRQ registered by G audio initialization. It
reads the IN/mask tables prepared by the panel and queues events; the patch
to its limit must be applied at **LMA `0x02059AB8`**, not the RAM VMA. The flag
enabling the scanner is set only after initialization of all three pointer/mask
pairs is complete.

## G potentiometers and other GPIO owners

G uses PB1 and PC6..9 for analog controls/multiplexers. No proven MINI electrical
map exists for these controls yet. The patch skips G initialization
`0x020159C2..0x020159FC` and leaves flag `state+832` zero. This flag protects
both the periodic panel block `0x02015CC6..0x02016150` and path
`0x0200CE8E → 0x0200CDE0`.

In the decoded paths, this excludes writers `0x0201453A` (PB1/PC6..8),
`0x02014578` (PB1 pull), `0x0200CC1A` (PC9), and `0x0200CC40` (PC6..8 mux).
RAM-data initialization before the jump and the final state update remain.
Physical analog controls and any expression input remain pending; DSP
parameters continue to be those of the G editor.

This patch does not replace shared GPIO driver `0x02004998`. The G audio
preamble on PC0/PC1/PC5/PA9 belongs to the audio port. Generic power-saving
paths at `0x0201D40E` and restoration at `0x0201D95A` can reconfigure entire
ports and require a separate MINI ownership check. The report does not claim
complete analysis of every alias or indirect call in the binary.

## Tests and limitations

The verifier executes actual instructions from the stub, input initialization,
modified restore section, and original logical lookup using a limited
interpreter and Python memory. Unsupported instructions cause an error; no
actual MMIO access exists. It verifies:

- 5 frame values: one RAM-cache write, no reads or GPIO access;
- 4 initial GPIO patterns: only PA10/PA0/PA3 change, with PA1/PA2 preserved;
- 32 combinations of presses and other input bits;
- 1024 index/configuration-byte pairs, always with identity mapping;
- 10 physical→logical lookups in the G and MINI maps;
- 3 loop limits with unchanged targets, rejection of incorrect sources, and
  patch reversal recovering every byte of the original G.

The entire IRQ, task scheduler, electronics, and debounce timing are not
emulated. The four polling samples and thirty IRQ samples remain those of G;
their duration on MINI has not been measured. The direct-reference comparison
includes flash and RAM, but a linear scan may include data and does not prove
the absence of indirect entry points.

`hardware_verified`, `flashable`, and the app's panel capability remain `false`.
The adaptation is an offline-verified component of the complete candidate,
not a claim of boot success or complete physical compatibility.
