# The acoustic block

A block of the product build that makes an acoustic guitar of an electric one, with
6 or 12 strings. It sits at the effect id 6 of the application, where an
old reverb was that the application turns into a newer one: an empty seat in every
table of the effects. Without the product option the image is MINI v4, byte for byte.

- [`mini/product/acoustic.c`](../firmware/ultrarig/mini/product/acoustic.c), the sound;
- [`tools/make_acoustic_tables.py`](../tools/make_acoustic_tables.py), its numbers;
- [`tools/check_mini_effect_block.py`](../tools/check_mini_effect_block.py), its check.

What follows is measured on recordings and in the simulator.

## The controls

| Parameter | | Default | |
|---|---|---:|---|
| `strings` | 6 or 12 | 6 | In the editor, two buttons |
| `body_pct` | 0..100 | 70 | How much of the box is heard |
| `top_db` | -12..12 | 0 | Brightness, to suit the pickup |
| `decay_pct` | 0..100 | 60 | How fast notes die; 0 keeps the electric's sustain |
| `air_pct` | 0..100 | 25 | Short dense echoes: the wood, a near microphone |
| `doubles_pct` | 0..100 | 60 | The second strings; only with 12 |
| `nivel_db` | -12..12 | 0 | Level |

## What it is made after

- **The body and the tone.** GuitarSet (Xi, Bittner, Pauwels, Ye and Bello, ISMIR 2018,
  <https://zenodo.org/records/3371780>, CC BY 4.0) has an acoustic guitar recorded at
  once by a pickup on its strings and by a microphone in front of it. From 72 excerpts
  of 6 players, the relation between the two: resonances at 108 Hz (+11 dB, the air of
  the box) and 196 Hz (+13 dB, the top), at 307, 370, 492 and 1100 Hz, a hollow around
  500 Hz, more of the top. The pickup has the spectrum of an electric guitar recorded
  directly, so the relation is one for an electric too. The phase of the relation is
  lost (the players move), so what is fitted is its size.
- **The fall of the notes.** The bands of an electric recorded directly (Guitar-TECHS,
  <https://zenodo.org/records/14963133>, CC BY 4.0) fall by 23 to 37 dB a second, those of
  the acoustic by 43 to 95. Three bands are made to fall faster, by how far each is
  below its last attack. A new attack is measured by itself: a chord 12 dB softer than
  the one before comes out 12 dB softer.
- **12 strings.** The four low pairs of a 12-string are octaves, the two thin ones
  unisons, all a little out of tune. The octave is a bank of 37 narrow filters at a
  quarter of the rate; the phase of each is doubled, and all of it is 0.7 Hz sharp. The
  second string is the sound above 300 Hz, 6 cents sharp, 0.4 to 5.4 ms late.

No recording is in HyperRig, only numbers fitted to them. The method of the octave, the
doubled phase of narrow bands, is the known one of polyphonic octave pedals; the code
is new.

## What the measures say

Twelve pieces recorded directly, through the block at its defaults:

| Band, Hz | Electric | Real acoustic | 6 strings | 12 strings |
|---|---:|---:|---:|---:|
| 80-160 | -23 | -46 | -36 | -43 |
| 160-320 | -33 | -48 | -42 | -49 |
| 320-640 | -29 | -38 | -36 | -39 |
| 640-1280 | -27 | -42 | -31 | -35 |
| 1280-2560 | -23 | -43 | -33 | -39 |
| 2560-5120 | -32 | -60 | -49 | -49 |
| 5120-10000 | -37 | -101 | -69 | -60 |

The slopes are in dB a second. The tone of 6 strings is within 3.2 dB of the real one
from 100 Hz to 5 kHz, by thirds of an octave, and 5 to 7 dB short from 6 to 10 kHz: an
electric has little there but hiss, and more of it is not worth having. The level is
that of the dry sound.

The octave, of a sine: -2 to -5 dB of it from 82 Hz to 1.3 kHz, other things 45 dB below.
Of two notes a fifth apart, the false sum of the two is 20 dB below the octaves, of a
third 3 to 19, of a tone as loud as they are. Against the ideal octave of the strings of
a chord the bank is some 8 to 9 dB off, a pair of grains 1 to 3.

A note with 12 strings starts as fast as with 6: half of its attack after 3 to 5 ms, nine
tenths after 5 to 16, by the mean over the slow beat of the second strings (the G, at
27 ms, has the resonance of the top on it, with 6 strings as well). The octave by itself
takes some 10 to 30 ms to be whole, the longer the lower: the price of telling a string
from its neighbours. Wider bands are faster and dirtier; these are between.

What is not there: a string is not told from another, so the second string is of all
that is above 300 Hz.

## In the firmware

- The sound code and its tables (4.9 KB) are in the RAM, as the application's own sound
  code is. The start-up code tells the processor where code in the RAM ends and it
  faults beyond: in a product build that is
  `ultrarig_ram_code_end`, after the product's code.
- Its memory, 8880 bytes, is given by the application when it is added, cleared, and
  taken back. Without it the sound goes by.
- Its parameters are words the application replaces when a knob moves; what could step is
  smoothed inside.
- A block is converted when it is added (`effect_setup_create`), whatever the list of old
  ids says: `preset_preflight_convert_effect` leaves the id 6 alone now.
- In live mode a footswitch turns the first reverb, delay or modulation of the chain on and off. The
  table of those kinds still had the old reverb at the id 6: in a product build the block is of no
  kind, and no footswitch takes it.
- The application counts 12,500 ticks for 6 strings and 32,500 for 12, of the 154,950 of a
  block of 128 samples. Beside the A2 amp some 22,700 are left (the engine takes 131,800 on the pedal),
  so 6 strings fit with the amp and 12 do not. The compiled code takes
  34,000 and 89,000 instructions, some 11,900 and 31,200 ticks at the 2.1 cycles an
  instruction that the application's own costs have. The time on the pedal is not
  measured. When there is no time the application lets the block go by.
- It is a block for one channel: in stereo it has one sound.

## What is saved with it

A preset that has the block is for a HyperRig that has it. An older HyperRig, and
UltraRig, read the id 6 as the old reverb and turn it into a room.

## What was tried

On a TANK-MINI, with the amp off: played with 6 and with 12 strings, saved in a preset and loaded
again. The time the pedal takes for the block was not measured.
