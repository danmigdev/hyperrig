# What HyperRig adds to the firmware

`tools/build_hyperrig_mini_image.py` builds the TANK-MINI's application area from
[the source](ULTRARIG_SOURCE.md). Without options the result is the MINI v4 area, the first port of
UltraRig, byte for byte. With `--product` it is HyperRig: the changes of the application under
`.if MINI_PRODUCT`, and the code of `firmware/ultrarig/mini/product`.

```
python -B tools/build_hyperrig_mini_image.py --output build/product-NN --product
```

## Which build is it

```
HRID  ->  HRID 1 <version> <build id> banks=3
```

The version is `mini/product/VERSION`. The build id is the first 16 digits of a SHA-256 over the
name and hash of every source file, so it changes with any change of the source. The build manifest
names both under `product`. `PING` answers the same for every build.

## The switches

| Gesture | v4 | HyperRig |
| --- | --- | --- |
| A, B or C | Preset of the bank | The same |
| A, B or C again | Bypass | The same |
| A, B or C held one second | Saves there | The same |
| A+B | The bank before | BANK-, the bank before |
| B+C | Preset or live mode | BANK+, the next bank |
| B+C held one second | Tuner | Tuner |
| Held three, six seconds | B+C: Bluetooth on, off | A+B: the same |
| Presets | Banks of four, for four switches | Banks of three, 1A to 11B |

The gestures are the ones printed on the pedal. The Bluetooth gesture is the firmware's own; v4 had
it on B+C, where it opened the tuner on the way.

With the Scenes and the Stomp of the editor (`layout=custom` and one kind of action on the three
switches) the pairs work too (`pairs.c`): a press waits 45 ms for its neighbour, and then A+B and
B+C are the group of three scenes before and after, or the preset before and after. B+C held a
second is the tuner, and a tap closes it. The lights show the scenes of the group.

In live mode the application's table of kinds called the id 6 a reverb; it is the acoustic block now,
and no footswitch takes it. The id 24, the harmonizer, is a modulation as before.

## The tuner's memory

The tuner takes 7,168 bytes while it is open: of the heap, or of the memory the effects share. In the
application it asks for one piece of that size and stays silent when there is none, although there may be
more than enough in smaller pieces. Here (`tuner.c`) the pieces are put together first, as for a block
that is added, with the sound paused once, and the second memory is asked too when it is in use. When there
is really no room `TUNE` says `nomem`, and the editor says it in words.

## The cuts of the cab

The cab block has a low cut (0 to 800 Hz) and a high cut (20 kHz down to 2 kHz), 12 dB an octave, both off at
0 (`cab.c`): two biquads behind the convolution, as the application runs them for its equalizers, on what the
block gives. They are within 0.02 dB of a Butterworth filter. The control scan moves the frequency a quarter of
the way in each turn, and a filter that is switched on or off is faded within 21 ms: the sound has no pause and
no step. A block of 128 samples takes 34 instructions more when both are off and some 2,000 for each that is on.
Their memory is in the block's object, in a part that the cab did not use. The two are the fifth and the sixth
parameter, which had no meaning and were stored as 0; the high cut is kept as Hz below 20,000.

Another cab in a block (a scene, a preset, an upload) was made beside the one before, and kept that when there
was no room for two. The one before now gives its place when there is none and the new one is no longer
(`hyperrig_cab_room`); the sound is paused for a change of cab as before.

## Eight scenes

The application has four scenes in a preset. Here the records of the scenes and their names are eight
each (`scene_memory.S`, `scenes.c`), and the application's code finds them there.

- **Stored.** A preset with four scenes at most is stored as before, byte for byte (version 5), and an
  older HyperRig reads it. With more it is stored in version 6, packed: for each scene only the blocks
  it has, and of each only the knobs that differ from the preset's. It is longer than an older HyperRig
  accepts, which then takes its place as empty. A preset has 2,048 bytes; eight scenes always fit with
  up to eleven blocks. What does not fit is refused: `ERR SNAPSAVE no room for these scenes`.
- **A block that is added later.** In the application a scene that was saved before a block was added
  has no values of it, and the block stays as the scene before left it. Here it takes the block as it
  plays, before a scene is applied and before a preset is stored.
- **Choosing a scene** keeps the blocks: no pause, the knobs glide (42 ms by default), and delays and
  reverbs that are switched off ring out.

## Another capture, and a capture for each scene

The application stops the engine to load a capture, and starts it again; and its pause of the sound
waits until the output has run dry, a tick of 10 ms at a time. Every A2-Lite has the same shape: the same
layers at the same places of the engine's memory, with other numbers. So (`swap.c`) a capture of the shape
of the one that plays is read and checked while that one plays. Then the sound task is asked, at a gate in
`capture_async_run`, to leave the capture alone: at the end of its block it fades the capture out, and
from then on the capture is silent while the rest of the chain, the cab and the reverbs, plays on. When
the second core and the IR unit are done with it, the application's own loader writes the numbers. What it
clears and checks a second time is left out, because the network is settled next (`audio_task_warmup`),
which fills it; the next block fades the new capture in. A sound task that does not answer within 20 ms
(no amp in the chain) is paused as the application pauses it. Anything else goes the application's way:
another shape, an engine that does not run, its memory lent to the effects.

In the simulator the memory is byte by byte what a stop leaves, and the capture is left alone for some
118,000 instructions, about 0.7 ms. On the pedal, with a trial build that played a tone into the input
and measured every block at the end of the chain (inside the pedal, not the sound that leaves it): the
pause of before kept the sound off some 25 ms for 0.9 ms of loading; at the gate, the capture is back
some 6 ms after it was asked, and about 10 ms of blocks are quieter.

The flash is read 256 bytes at a time, and each piece holds the other core for a moment. A cab block with
an IR of its own reads it, 8 KB, while the sound is paused for another preset: some 120 ms. While the
sound is paused, and only then, `storage_control_read` reads 4 KB at a time (`hyperrig_flash_piece`):
some 45 ms, most of it the transfer itself, about 4 microseconds a byte.

A scene may have a capture of its own (`scenes.c`):

```
SNAPCAP <scene> <capture>     0 to 14, or -1 for the preset's; the scene that is on is heard at once
SNAPCAP                       SNAPCAP <eight of them> preset=<the preset's own, or -1>
```

- Choosing a scene puts its capture in, before its knobs, when it is another than the one that plays. A
  capture that is gone, and a chain without a capture, leave what plays.
- While the capture of a scene plays the preset's own is remembered, and that is what is stored. A capture
  that is loaded by hand is the preset's from then on. A scene that is kept has the capture that plays.
- A preset starts with the capture of the scene it starts with, loaded once.
- **Stored:** a preset with such a scene in version 7, which is version 6 and eight numbers; an older
  HyperRig takes its place as empty. Every other preset is stored as before, byte for byte.

## Sixteen blocks

The application holds ten blocks before the AMP block (P) and ten after it (Q), sixteen in all. When
the capture is taken out nothing stands between the two: the audio task copies the samples from one
to the other, with no gain, filter or other path. `tools/check_mini_places.py` runs it with the same
blocks in P and in Q. In mono they give the same samples and end in the same state, every effect,
chains divided anywhere, parallel paths, knobs that move, scenes. What is not the same:

- **Stereo** is only in Q. In P a block is mono. What is followed by a mono block is so anyway.
- **Drives with oversampling side by side** are worked as one, up and down once, within a section.
  Divided between the sections they are worked one by one: 9 samples later, 50 dB under the sound
  different, and 1,875 ticks more.
- **Three splits** fit in each section, each with its levels and crossover.
- **The last moment of a block** in P is earlier than in Q by what the rest of the audio takes; the
  room that blocks are admitted to is without it, so a chain that was admitted runs in both.

The editor puts the meeting of the sections of a chain without a capture where this does not matter
([MINI_DEV_EDITOR.md](MINI_DEV_EDITOR.md)). What was missing in the application for chains of more
than twelve: with the trails on, a preset change leaves up to four delays and reverbs in their places
while they ring, and the last blocks of the next preset found none. Here what rings gives its place
(`places.c`). What rings goes on for 1,500 blocks at most (about four seconds), as before: at the end of it
the application cuts a delay off and fades a reverb in 31 blocks; here both fade in the last 500 and 511 (1.3 s).
The level of a delay goes down in the call that makes its sound, so what it is set to stays as it is. The stored form of a preset is the same.

## A block in the place of another

```
FXC <preset> <id> <its type> <new type>  ->  FXC id=<the new one's> <new type>, and the line FX cpu=...
```

One word (`replace.c`), so the sound pauses once, and no switch, no scene and no lost connection comes
between taking away and adding. The preset is that of `LVL`, -1 without one: with another on the pedal,
or another type at the id, it answers `ERR FXC another preset` or `another block` and does nothing.

The new block has the old one's place, section, branch and switch; in each scene it has the switch the
old one had there, and the knobs of a block that was added later. Both need not fit at once: the old
one's place and memory are the new one's. When it does not fit (`not enough CPU`, `out of memory`,
`no IR loaded`) the old block is as it was, in every scene; of a delay or reverb that was refused for
memory only what still rang is gone. A block that is off needs neither processor nor memory.

## The wheel and the battery

The wheel on the rear is a voltage on PC9, converter channel 8, read every 10 ms with a 1/16 low
pass; the level is 124 less the value / 8 and the gain its square, full at 124. `KNOB off` gives full
volume; a converter that does not answer keeps the last one. The battery is on PC0, channel 6: 558 is
empty and 636 full. Under a tenth the light of the current preset flashes every eight seconds.

```
HRST wheel=<0..1023> level=<0..124> volume=<0..65536> battery=<percent> raw=<0..1023>
```

The channels, levels and limits are facts about the pedal; none of the original application is here.

## Bluetooth

The application lets a line that came over Bluetooth by when its word is in one of its two lists: the
words that only read, for anyone who is connected, and the words that change something, for a phone
that is paired or a computer that showed the pedal's key (`AUTH`). Any other word is answered
"usb only", and so were HyperRig's own words, `HRID` among them. `air.c`, at the gate of the console
(`main_task`), sorts them as the application sorts its own: `HRID`, `HRST`, `HRBYE`, `AMPK`, `MIDI`,
`KNOB`, `HRLV` and `SNAPCAP` by themselves, always; `MIDI`, `KNOB`, `HRLV`, `FXC` and `SNAPCAP` with something
after them, with the key. `STAGE`, `REC`, `RECD`, `INJBEGIN` and `INJB` stay with the cable.

A computer may keep the link after its program has closed; the pedal then does not advertise, and
nothing can connect. In each turn of the control scan the pedal ends a link on which no line came for
90 seconds, and at once after `HRBYE`, which the editor says before it disconnects (it says `PING`
every 20 seconds while it has nothing to ask). After A+B held three seconds the pedal gives its key,
or pairs, for one minute, with its lights pulsing blue; the minute ends as soon as the link that came is
one the pedal takes changes from.

## MIDI

Over USB-C in both directions, off until it is turned on: [MINI_MIDI.md](MINI_MIDI.md).

## The way to the loader

The original firmware stored HyperRig's loader in the flash when HyperRig was installed
([INSTALLER.md](INSTALLER.md)). `STAGE` looks for it as the bootloader does and says where its update
record is; `STAGE GO` gives that record to the bootloader and restarts the pedal into the loader.
Nothing is written to the flash. A missing, damaged or foreign loader gives `STAGE 0` and `STAGE ERR`.

## If it does not start

- **A write that was interrupted:** the boot area, which HyperRig never changes, finds no valid
  application and starts the loader stored in the flash.
- **A HyperRig that freezes:** the watchdog resets it, and the third start in a row that does not get
  healthy asks the ROM for the update mode (UltraRig's own guard, unchanged).
- **The last resort:** any of the three switches held at power-on leads to the ROM's update mode.

These are shown in the simulator. On a pedal the left switch was seen to lead to the update mode.

## Captures and cab IRs

Captures: fifteen slots of 8 KiB, the first eight from `0xDF000`, the others from `0xCF000`. Cab IRs:
seven slots of 8 KiB from `0xEF000` (4,076 samples, 85 ms at 48 kHz) and one of 4 KiB (2,028 samples,
42 ms), because the global settings are behind it at `0xFE000`. A capture is checked and prepared by
the firmware's own loader before it can be saved. One that keeps knobs of what it was made of has them on the amp's
controls, and `AMPK` says which ([PARAMETRIC_NAM.md](PARAMETRIC_NAM.md)).

A cab IR is heard as soon as it is uploaded, without a slot (`irlive.c`): after `IREND` the cab blocks
that play the loaded IR are made again from it, as `ILOAD` does; a block with an IR of its own keeps
it. In the application a block went on with the IR before, also after `ISAVE` and after `ILOAD` of
that same slot. A capture plays from `LDEND`, without a slot. Neither writes the flash; `ISAVE` and
`CSAVE` do.

The original firmware keeps its amps, cabs and settings in the same places. They come back with the
original firmware, from the pedal's own copy.

## The measure of loudness

The console word `HRLV` ([MINI_LOUDNESS.md](MINI_LOUDNESS.md)): strokes of the guitar that are
recorded, played into a preset and measured at the end of its chain, and output gains that are
written into stored presets. `REC` and `INJ`, the diagnostic words, lend the memory for it.

## Checks

| | With |
| --- | --- |
| The switches, banks, pairs, holds, lights of the scenes, wheel, battery, `HRID`, `STAGE` | `tools/check_mini_panel.py` |
| Eight scenes, stored and read, what does not fit, blocks that come later, the pairs | `tools/check_mini_scenes.py` |
| A chain without a capture in both sections, sixteen blocks stored and read | `tools/check_mini_places.py` |
| Captures and cab IRs, power cut at each erase and program; an uploaded cab that is heard at once | `tools/check_mini_library.py` |
| A block in the place of another | `tools/check_mini_replace.py` |
| The tuner with little memory | `tools/check_mini_tuner.py` |
| Another capture without a stop | `tools/check_mini_swap.py` |
| A capture for each scene | `tools/check_mini_scene_captures.py` |
| HyperRig's words over Bluetooth, the end of a silent link, the minute for letting a device in | `tools/check_mini_air.py` |
| The cuts of the cab | `tools/check_mini_cab.py` |
| The settings for every preset, what they do to the sound, how they are stored; the calibration of the input | `tools/check_mini_globals.py` |
| The acoustic block | `tools/check_mini_effect_block.py` |
| The [effects from the id 40 on](EFFECT_PLUGINS.md) | `tools/check_mini_effects.py` |
| The harmonizer | `tools/check_mini_harmonizer.py` |
| A capture that keeps knobs | `tools/check_mini_parametric.py` |
| MIDI: every message, the map and how it is kept; the USB device with both functions | `tools/check_mini_midi.py`, `check_mini_usb.py` |
| The measure of loudness, what ends it, the gains that are stored | `tools/check_mini_loudness.py` |
| The embedded capture, the guards of the start | `tools/check_mini_embedded_capture.py`, `check_mini_entry_guard.py`, `check_mini_boot_guard.py` |

They run the built application in the pi32v2 simulator ([`tools/mini_sim.py`](../tools/mini_sim.py)),
with the store of presets, Bluetooth and the link to the editor recorded instead of run. The sound,
the processor's time, the converter and the pins are not simulated: they are no test of a pedal.
