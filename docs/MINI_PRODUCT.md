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
