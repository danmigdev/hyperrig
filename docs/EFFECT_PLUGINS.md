# Effects of HyperRig's own

A product build has effects beside those of the application, and a frame that makes
the next one a single file and one word. They are compiled into the firmware: nothing is
loaded at run time. Without the product option the image is MINI v4, byte for byte.

What follows is measured in the simulator and on recordings. The effects from the id 40 on were not
played on a pedal.

## What exists

| Id | Name | What it does | Ticks | Memory |
| ---: | --- | --- | ---: | ---: |
| 6 | `acoustic` | [Acoustic guitar of 6 or 12 strings](MINI_ACOUSTIC.md); older than the frame, with code of its own in each place | 12,500 or 32,500 | 8.9 KB |
| 40 | `octaver` | One and two octaves below and one above, with a fuzz; for single notes | 8,000 | 0.8 KB |
| 41 | `swell` | Every note grows out of nothing, as with a volume knob turned up after the pick | 4,000 | 1.4 KB |
| 42 | `reverse` | A delay that plays each piece of the sound backwards | 6,500 | 33.4 KB |
| 43 | `ensemble` | Three voices, each a little late and a little out of tune | 6,000 | 4.6 KB |
| 44 | `vintage` | A delay whose repeats grow darker and softer, with a slow waver | 7,200 | 33.4 KB |
| 45 | `glide` | One voice whose pitch slides to an interval and back as its bend moves | 12,000 | 12.9 KB |

Ticks are of the 154,950 of a block of 128 samples, as the firmware counts them; beside the A2 amp
some 22,700 are left. The compiled code takes 21,242, 10,926 and 17,209 instructions at most, some
7,400, 3,800 and 6,000 ticks at the 2.1 cycles an instruction that the application's own costs have; that of the
other two is in the check.
Each is of one channel: in stereo it has one sound. In live mode no footswitch takes one; in Stomp
it has the light of its group.

**Octaver.** The known way of octave pedals with a divider: a low-pass of the sound tells where a cycle
begins (over half of the last peaks, then under half of the last dips), and every second cycle is
turned over. That leaves half of the pitch with the fall of the string; a low-pass takes the edges
away. Two octaves are the same done to the first. Above, the lower half of the sound is turned over,
after a fuzz. On eight solos of GuitarSet, where one note sounds, the cycle was right 94 times of a
hundred, and on computed strings from 82 to 880 Hz always; chords have no single octave, and it shows.

**Swell.** A sound that is over a gate and louder than it has been is an attack. The sound is 4 ms late,
so that the gate is shut when the attack comes out. At half the sensitivity all of eight notes played
into each other started anew, and held notes and chords started once.

**Reverse.** One sample of three is kept, as 16 bits (some 6 kHz); pieces of 60 to 500 ms, one over into the next
within 8 ms; feedback and damping.

**Ensemble.** One line is read at three places, a third of a cycle apart: each wavers slowly and widely (4 ms either
way at most) and eight times as fast an eighth of it, and goes from one place to the next on a straight line within 32 samples. The three are added up
at the level of one, and rounded by a low-pass. A chord is as loud at every mix within 1.1 dB.

**Vintage.** What is kept is as in the reverse delay, and the code is shared (`thirds.c`). The line is read between two
samples at a place that wavers (0.8 Hz, 1 ms either way at most) and follows a new time over some 60 ms, so the
pitch bends on the way. Two low-passes are in the loop: each repeat is darker, and 4 dB softer at a feedback of 70. A
knee over three quarters of the full level keeps many repeats in bounds; at a feedback of 100 a note was 2.6 dB
softer after 16 s.

**Glide.** The harmonizer's engine ([MINI_HARMONIZER.md](MINI_HARMONIZER.md)), with one voice: the period of what is played
is heard every 128 samples, and the voice reads the line of the last 2048 samples faster or slower, stepping back or on by
whole periods before it runs out. Its interval is the block's own, in 1/256 of a semitone, glided by the frame, and it never
jumps to a new note. Faster than twice (more than an octave up) a step back of some periods would be used up within the fade
to it, so it steps as many periods more as the fade needs. The frame gives 32 samples or fewer; the glide gathers 32 and gives
them back 32 later (0.67 ms), so a block in parts sounds the same. What the voice reads is held within the full level, where the
engine's crossing of two places has room. After a pause the voice is silent for 16 chunks (11 ms), until what it reads is new.
With the dry sound beside it, the voice comes in over the first semitone of the way, so at rest only the dry sound is heard.
Its code is in `harmonizer.c` beside what it shares, and nothing of the sound is in the flash twice: 886 bytes of flash and 544
of RAM in all. On computed tones, at every interval from two octaves down to two up, the pitch was right to 0.1 Hz with no step
larger than the tone's own; a power chord moved as a whole.

All of them are written here from published methods and own derivation. No code, table or recording of
others is in them, so they add nothing to [the notice](../release/NOTICE.md).

## How one is added

1. `firmware/ultrarig/mini/product/fx_NAME.c`, with one `EFFECT hyperrig_fx_NAME`
   ([`effects.h`](../firmware/ultrarig/mini/product/effects.h) says what is in it): the name, up to seven
   parameters with their ends and defaults, the effect of the application whose group and light it has, its ticks, its memory, and
   `set` and `run`. Names of parameters that the application has are there as well, and cost nothing.
2. The name at the **end** of the list in [`effects.c`](../firmware/ultrarig/mini/product/effects.c). The place is the
   id, and the id is in people's presets: never take one out or change the order.
3. Its numbers, if it has any, in [`tools/make_effect_tables.py`](../tools/make_effect_tables.py).
4. The same arithmetic in [`tools/effects_reference.py`](../tools/effects_reference.py), and its ticks, group and light in
   [`tools/check_mini_effects.py`](../tools/check_mini_effects.py).
5. Its look, its words and its tips in [`app/mini/effects.json`](../app/mini/effects.json).

What the frame does: parameters within their ends; settings as whole numbers in the words that the
application replaces when a knob moves; those marked in `glides` go in steps, the gains `DRY` and `WET` with
every sample; chunks of 32 samples or less; the beginning of the memory cleared again after a pause, which
the count of blocks shows, so cleared memory has to be a good start; samples up to 2^27, 24 dB over the full level; without memory the sound goes by.

Rules: everything that runs with the sound is `SOUND`, its numbers `TABLE` (both in the RAM); helpers are always inlined, or they would
land in the flash; no addresses in the memory, which the application may move; a glided setting is under 2^24; products by `times`,
which stays 32 by 32 bits. A hook in a small function of the application saves r1 to r3, as the
application was compiled with each function knowing which registers the ones it calls leave alone.

## What the firmware can hold

The application has ids up to 39, and each has an effect: 37 of its own, 6 the acoustic, and 24, an old
pitch that is turned into a newer one when it is added, the last that could be reused. The id is one
byte in every place, so it can go to 255; the table of the stages has room for 24 ids, 40 to 63, and
takes a byte for each further one.

| | Now | For each more |
| --- | --- | --- |
| Flash, of 516,096 bytes | 12,722 free in the build of the first three, 3,726 less than in 0.2.0: the frame with its hooks 1,034, octaver 1,174, swell 604, reverse 914; ensemble and vintage 1,374 together | 0.6 to 1.2 KB: some ten, if nothing else takes it |
| RAM | 2.7 KB less heap, of 283 KB | 0.4 to 0.9 KB |
| Names, rows, groups, lights | In the effect's own file | Nothing |

**Stored form.** Unchanged: presets and scenes keep the id and seven numbers for each block. An older HyperRig,
and UltraRig, leave out a block they do not know and keep the rest and the scenes; saved there, the preset
is without it. Checked with a build from before.

Where the application knows the ids, and what was changed, each under `.if MINI_PRODUCT`:

| What | Where |
| --- | --- |
| Name, number from a name, the list of the console | `console_reports_type_name`, `dispatch_helpers_effect_number`, `console_reports_effect_table` |
| Parameters | `preset_application_metadata`, `effect_setup_create` |
| Group | `slot_queries_type_name` |
| Ticks | `effect_setup_type_cost`, `slot_queries_type_cost`, `effect_processing_cost` |
| Memory | `effect_setup_demand_by_type`, `slot_queries_type_demand`, `slot_queries_type_fits` |
| Made, its settings, its sound | `effect_setup_create`, `effect_construction_construct`, `effect_processing_dispatch` |
| Stereo stages | `effect_stage_capabilities`, a byte for each id |
| Light | The colours of the footswitches (`0x02015760`) |
| Left as they were | Conversion of old ids, kinds of live mode, oversampling modes, ramps of a parameter (0: replaced at once), tails, extra stereo ticks: their ranges end before 40 |

## Where more could come from

The licences are what the projects state, read 2026-11-24. This is not legal advice. The firmware is PolyForm
Noncommercial; code with conditions of its own (GPL, LGPL) adds them to all of it, so only MIT, BSD, ISC,
Apache or CC0 code with its notice is taken.

| Collection | Licence, as stated | Fits? |
| --- | --- | --- |
| DaisySP | MIT | Best candidate: plain C++ modules, floating point |
| DaisySP-LGPL | LGPL-2.1 | No |
| Mutable Instruments, STM32F code | MIT (AVR code GPL 3.0, hardware CC BY-SA 3.0); the name is a trademark | Possible, one module at a time |
| Faust libraries | Each its own; needs Faust's compiler | Later, with the licence of each |
| LV2, Web Audio Modules | Plugins for a computer or a browser | No: no sound passes through the computer |

Weighed against use for a guitar, ticks and memory, and left for later: a bitcrusher with a sample reducer and a
ring modulator (cheap, but few play them), tape saturation with wow (near to what boost, overdrive and vibrato
do), a freeze (the application has Spectral, and a looper). A loader for code at run time is not planned:
there is no memory protection between effects.

## Checks

| | With |
| --- | --- |
| The list, the life of each, every sample against the reference with each parameter at its ends, silence, the loudest, parts of a block, a pause, the ticks, a preset and two scenes stored and read, a build from before | `tools/check_mini_effects.py BUILD --before BUILD` |
| The acoustic block | `tools/check_mini_effect_block.py` |
| Tables, descriptions, sounds of the reference | `tests/test_mini_effects.py` |
| The editor | `tools/check_mini_dev_editor.py` |

`python -B tools/effects_reference.py EFFECT IN.wav OUT.wav name=value ...` renders a recording, to be heard
before it is on a pedal.

Not proven: how they sound and feel, and the time the pedal takes. The pedal measures that itself: `ticks=` of a
block in the answer to `FXS`, against the numbers above.
