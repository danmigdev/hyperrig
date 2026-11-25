# The same volume for every preset

A tool, run on request, that sets the output gains of a scene, of a preset with its scenes, or of all
presets, so that the same stroke of the guitar is as loud in each. Nothing of it runs while one plays.

- [`mini/product/loudness.c`](../firmware/ultrarig/mini/product/loudness.c), the pedal's part, and its
  numbers, made by [`tools/make_loudness_tables.py`](../tools/make_loudness_tables.py);
- `app/mini/product-loudness.js`, the arithmetic, and `product-loudness-ui.js`, the window;
- [`tools/check_mini_loudness.py`](../tools/check_mini_loudness.py), `tests/test_mini_loudness.py` and a
  step of [`tools/check_mini_dev_editor.py`](../tools/check_mini_dev_editor.py), the checks.

## What is made equal

The loudest 400 ms after the stroke, with the K weighting of ITU-R BS.1770 (the momentary loudness). A
mean over seconds would reward sustain and turn a distorted sound down too much. Every preset gets the
same input at the level of the player's guitar: how much a distortion adds depends on it.

The measure is at the end of the chain, after the global equalizer and before the output gain, the
wheel and the limiter. The new output gain is the volume that all shall have, less what was measured,
in whole dB from -30 to +12: what is left is at most half a dB, and 1 dB between two sounds. The peak
is measured too, and the window says where loud notes would reach the limiter.

## How it goes

1. **The guitar, once.** The pedal records some ten seconds of playing. The editor finds the strokes
   and keeps three in the middle of how they are played, 0.47 s each, on the computer. Without a
   guitar there are strokes that nobody played, for soft, medium and hot pickups.
2. **The measure.** One stroke is sent to the pedal. For each preset and scene it is played twice
   into the input, the output silent, and the second play counts (a third, when the two differ by
   more than 0.7 dB; again, up to three times, while echoes of what was there before are heard).
   Then the next stroke, over all of them again. The mean of the three is the result. A sound takes
   some fifteen seconds in all: about five for each stroke.
3. **The gains**, before and after, with one volume for all that can be moved and a correction by
   hand for each. Nothing is written before Save.

What a preset starts with is measured by itself when it is none of its scenes.

## What stays as it was

Measuring changes nothing that is stored. A press of a footswitch stops it and is nothing else; so do
four seconds without a word from the editor (the cable). The preset and the scene of the beginning
come back, then the sound; the editor looks whether it is the same sound, for a preset that starts
with another one than the scene it names. It stops too when another preset or scene is chosen in
between, and does not begin with the tuner open, in bypass, or without the engine.

Saving reads a stored preset, changes the output gain it starts with and those of its scenes, and
writes it back, as the colour of a preset is changed. The stored form is the same. A single scene is
different: its gain is a change like any other, saved with the preset.

## In the pedal

The editor does what it can, with diagnostic words that the firmware has: `REC 4 <words>` takes the
memory that the measure is in and `RECD <at>` reads it; `INJBEGIN` takes the memory of a stroke and
`INJB <at> <bytes>` fills it. The word of the measure has one operation, in hexadecimal bytes:

| Word | |
| --- | --- |
| `HRLV` | The editor is there |
| `HRLV 01` | Ends it, and gives the memory back |
| `HRLV 02<preset><gain><gain of each scene>` | Writes output gains into a stored preset, `7f` for one that stays |
| `HRLV 05` | Records the input |
| `HRLV 06<blocks of a play><plays><blocks before><slices>` | Plays the stroke and measures; a block is 128 samples, a slice 512 |

It answers `HRLV <result> <slices or codes there>`: 0, what the saving returned, or the operation when
it was not done, because the memory is not there, or not any more, or because a byte of the line was
lost on the way. The memory is laid out as `struct session` of the source: how many slices or codes
there are, the peak, whether it still runs, and from word 32 on the energies or a ring of codes.

| | Memory |
| --- | ---: |
| To measure: 184 words, and a stroke of 1,408 halfwords | 3,552 bytes |
| To record: 1,142 words | 4,568 bytes |

Both are taken where the firmware takes such memory: outside the pool of the effects if there is room
(some 6 KB beside a full preset), else from it. An effect that does not fit then is said.

A stroke is at a quarter of the rate, four bits a sample: a difference in steps that follow the size
of the differences. An upload to the pedal takes 33 ms for 95 bytes, so a phrase cannot be streamed;
one stroke is there at a time. A recording is read while it is made, some 11 ms for 192 codes of the
16 ms that they last, with a ring of 0.7 s. When it was too slow the recording goes on anew, and a
stroke with such a gap in it does not count.

The audio looks at one byte in two places, four instructions a block. While it measures, playing takes
1,705 ticks and measuring 1,273 for one channel and 2,537 for two, of the 159,744 of a block; recording
takes 1,677. These are counted from the instructions in the simulator at 2.1 cycles, not measured.
A preset that uses nearly all of the 154,950 that effects and amp may have leaves too little: the
editor compares what `LVL` counts of blocks that came late or were let by, before and after, measures
once more, and then says that there was no time.

It costs 1,452 bytes of the flash, code and numbers together; 936 of them are in the RAM, and the heap
is 960 bytes smaller. Two functions outside it changed for it: what changes the colour of a stored
preset (`command_services_save_word`) can write gains in its place, and the scenes have one function
for where a scene is.

## How exact it is

Against BS.1770 in Python, in double precision on every sample, what the compiled code measures of a
clean, a compressed, a clipped, a too loud and a two-channel sound is within 0.02 LU. 997 Hz at full
scale is -3.01 LUFS. A stroke through recording, codes and play is as loud as it was within 0.01 LU.

What the three strokes stand for was measured on twelve pieces of a guitar recorded directly
(Guitar-TECHS, <https://zenodo.org/records/14963133>, CC BY 4.0), 14 s of each, through five models
of amps from bright to very distorted. The offset of each to a clean one, against the median over all
strokes of the piece:

| | Mean error | Worst |
| --- | ---: | ---: |
| Three strokes in the middle (40, 50 and 60 % of the levels), mean | 0.25 dB | 0.8 dB |
| Three strokes at 25, 50 and 75 %, median | 0.48 dB | 2.2 dB |
| One stroke | 0.34 dB | 2.2 dB |
| Built-in strokes at the level of the guitar | 0.5 dB | 1.8 dB |

The built-in strokes are two chords and a note of decaying partials; their tilt and fall were chosen on
the same recordings. At a wrong level they mislead: 6 dB off in the level of the guitar is some 5 dB
between a clean and a very distorted sound. And one plays louder and softer: the first 14 s of a piece
and the whole of it differ by up to 2.4 dB. That is the player, not the measure.

Not shown: the time of the pedal, its flash, its sound, a real guitar and real presets. None of this is
a hardware or audio test.
