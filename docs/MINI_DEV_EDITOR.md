# The editor's page

[`tools/build_mini_dev_editor.py`](../tools/build_mini_dev_editor.py) makes the editor of one build of
the firmware: a page of files, which [the desktop program](DESKTOP_EDITOR.md) shows.

```
python -B tools/build_mini_dev_editor.py --output build/hyperrig-editor-NN --area build/release-parts/firmware
```

It starts from a sealed base, the editor of MINI v4 (which is UltraRig's, changed), and changes it by
exact texts that must each be found once. What HyperRig adds is in `app/mini`:

| File | What |
| --- | --- |
| `mini-profile-fx.js` | The policy of the base: which command may be sent, from what the pedal has answered |
| `mini-dev-rules.js` | The forms a build from source permits |
| `product-ui.js`, `product-ui.css` | The save line, names, replacing a block, footswitch choices, import of all presets, messages, one size for every control |
| `product-try.js`, `.css` | Trying a preset, a capture or a cab IR without saving |
| `product-presetfile.js` | The strict reading of a preset file from somebody else |
| `product-share.js` | Browse Patchstorage, in the desktop program |
| `effects.json` | The [effects from the id 40 on](EFFECT_PLUGINS.md): name, group, picture, words and tips |
| `product-parametric.js`, `product-amp-knobs.js` | Captures that keep knobs: their conversion, and the amp's panel ([PARAMETRIC_NAM.md](PARAMETRIC_NAM.md)) |
| `product-midi.js` | MIDI, in the settings |
| `product-tone3000.js`, `.css` | Browse TONE3000 |
| `product-globals.js`, `.css` | The settings for every preset, and the calibration of the input |
| `product-loudness.js`, `product-loudness-ui.js`, `.css` | The same volume for every preset ([MINI_LOUDNESS.md](MINI_LOUDNESS.md)) |

## Which pedal it may change

After `PING` the page asks `HRID`. Only the build it was made for is changed: another build, or a
firmware without `HRID`, is only read, and the policy refuses every change. The page says so in plain
words, and in the desktop program it offers the update. A pedal with a newer HyperRig is told apart,
and no update is offered for it.

## What it permits

| Commands | Rules |
| --- | --- |
| `GAIN PLOAD PSAVE SNAP SNAPSAVE FXP FXE` | For blocks, presets and scenes the pedal reported |
| `FXA FXR FXM FXL FXOS FXMIX FXXO` | The chain: sixteen blocks in all and ten in a section, as in the firmware |
| `FXC` | Another block in the place of one: for the preset and the block the pedal reported last, which the pedal compares again |
| `AMP AMPX AMPEQ STW` | The amp, its place, its controls; mono or stereo |
| `BPM TUNER` | 40 to 300 BPM; a reference of 415 to 466 Hz |
| `PNEW PNAME PDEL PCOLOR SNAPNAME SNAPDEL` | For presets and scenes the pedal reported |
| `FSA FSMODE FSPRESS FSLED LEDCFG FSDO GSAVE KNOB` | Footswitches, lights, the wheel; `GSAVE` keeps them |
| `MIDI` | The port and its settings, each within what the firmware knows ([MINI_MIDI.md](MINI_MIDI.md)); not `MIDI >` |
| `IRBEGIN IRB IREND ISAVE ILOAD IDEL IREAD FXIR` | Cab IRs: one upload at a time, its pieces within what it announced |
| `LDBEGIN LDB LDEND CSAVE CLOAD CDEL CREAD CTRIM AUDIO` | NAM captures of architecture A2; the page converts a `.nam` itself |
| `GEQ HPF LIM SPILL GLIDE SPUR` | The settings for every preset, once the pedal has said them; `GSAVE` keeps them |
| `CALIB start`, `CALIB stop` | Listening to the input, for a suggestion of the input trim |
| `HRLV REC RECD INJBEGIN INJB` | The measure of loudness, in the sizes it needs, and output gains into presets the pedal reported |

`HRLV 02`, `PSAVE`, `SNAPSAVE`, `PNAME`, `PDEL`, `PCOLOR`, `SNAPNAME`, `SNAPDEL`, `CSAVE`, `CDEL`, `CTRIM` of a
slot, `ISAVE`, `IDEL`, `FSDO` with `hold`, and `GSAVE` write the pedal's flash, in the records the
firmware keeps for them; the others change memory. Over Bluetooth an editor of a product build allows
what it allows over USB, less `REC`, `RECD`, `INJBEGIN` and `INJB`, which the firmware keeps to the cable;
on the build it was made for it asks for the pedal's key over USB (`BLE key`), shows it over Bluetooth
(`AUTH`) and says `HRBYE` before it disconnects; over either link it may open the pedal's minute for letting
another device in (`BLE pair`) and make it forget every phone and computer (`BLE forget`), which over Bluetooth
the pedal takes only from a device that has its key. Firmware update, `CALIB sens`, `NOISE`, and `REC` and `INJ`
beyond what the measure of loudness needs, stay blocked.

A chain without a capture is shown as one and uses both sections of the firmware, where a block sounds
the same ([MINI_PRODUCT.md](MINI_PRODUCT.md)). The second one, which is the one in stereo, has the last
ten; the first one has what there is more, and nothing in a chain of ten. A split, and drives with
oversampling side by side, are not divided. The page finds the meeting of the sections for each change
(`hrArrange`), sends the moves in an order that no section overflows, and refuses before it sends
anything what no place of it allows: a split that is too large, a capture with more than ten blocks on
a side. A file without a capture is taken as it is when it fits, and otherwise read the same way.

The policy keeps its own picture of the pedal. It notices a preset that a footswitch chose in `LVL`,
which the page polls, and reads the chain and the scenes again before it permits a change. What is
refused is said in words one can act on, and the reason is in the log of the desktop program.

## Trying without saving

One try at a time: loading, playing, then kept or back; an error or a disconnection leads to a state
of its own, from which it goes back or out. What plays is read first: the preset, the scene, the
chain with every knob, volume, tone, tempo, stereo, capture and cab IR. Back loads the stored preset,
chooses the scene, the capture and the IR, sends what differs, and reads and compares again; what is
still different is said. What could not come back is asked before: blocks that differ from the stored
preset, scenes of a preset without a slot, a capture or a cab IR without a slot.

- Nothing is stored before Keep. The commands that write are refused to the rest of the page while a
  sound is tried. A preset loads with none chosen on the pedal, so `SNAPSAVE` stays in its memory, and
  it is sent only while the tuner mutes the pedal: no switch chooses a preset then, the first press
  closes the tuner, as the simulator shows, and the loading stops. Names of scenes and the colour are
  sent by Keep.
- Uploads are `LDBEGIN`..`LDEND` and `IRBEGIN`..`IREND` without `CSAVE` and `ISAVE`. A firmware before
  the one of this page did not play an uploaded IR in blocks that were there.
- The output goes from -30 dB in steps of 2 dB to the preset's own, at most 0 dB or the volume that
  was there; it stops at -3 dB under full scale in `LVL`, when the limiter works, or at a clip.
- A preset from a file is read strictly: numbers and names in their form, within limits, everything
  else dropped; names reach a command only as plain letters, and only when they are kept.

## The settings for every preset

The words are UltraRig's; the rules permit exactly what the firmware takes as it is written.

| Word | Permitted | The firmware answers | At first |
| --- | --- | --- | --- |
| `GEQ band dB` | 0 to 4, -12 to 12 | `GEQ a b c d e` | Flat |
| `HPF hz` | 0 (off), 20 to 120 in steps of 5 | `HPF hz=` | 55 |
| `LIM on ceiling release` | 0 or 1; -200 to 0, tenths of dB; 10 to 2000 ms | `LIM on= thr= rel= lat=48 samples=` | On, -0.3 dB, 100 ms |
| `SPILL 0/1`, `SPUR 0/1` | Tails that ring out; the pedal's own whine | `SPILL n tails=`, `SPUR n learned=...` | On |
| `GLIDE ms 0/1` | 0 to 170; the knobs of a scene glide | `GLIDE ms= blocks= snap=` | 42, on |
| `CALIB start`, `stop` | | `CALIB running= win= ... suggest= trim= slot=`, and a line every 3 s | |

- **Where they are.** Input, high-pass, whine, input gain, blocks, amp, blocks, EQ, limiter, output
  gain. No preset and no scene has them, and the footswitch's bypass, which switches blocks off,
  leaves them.
- **The EQ** is a low shelf at 100 Hz, bells of Q 0.9 at 400, 1200 and 3200 Hz and a high shelf at
  7 kHz. A band at 0 dB is not computed. It is mono: with a band in use, stereo is paused. The firmware
  counts 580 ticks for a band (55 more for the first) of about 22,700 that blocks share, and
  takes a band also when there is no room: the editor looks at the room first. It has no switch: the
  editor's *Off* writes five zeros and keeps the values on the computer.
- **The limiter** holds the output under its ceiling, 48 samples later (1 ms).
- **Storing.** They change memory at once. `GSAVE` writes one page of 128 bytes with the footswitches
  and the rest, 30 to the sector at `0xFE000`; then the sector is erased and the last page written
  again. With the power cut in that moment the firmware starts with its first settings.
- **`CALIB`** measures the input after the high-pass, for readings of three seconds, and plays and
  changes nothing. `suggest` is the trim that brings the loudest reading, with the preset's input gain,
  to the level the capture is meant for (-18 dB, or what it says of itself). It ends after three minutes
  or with the audio. `CALIB sens` is a number about the input of UltraRig's pedals, and has no part
  in it.

[`tools/check_mini_globals.py`](../tools/check_mini_globals.py) runs the built firmware in the simulator
for every line of these, and compares the rules and the simulated pedal of the page check with it.

## Checks

[`tools/check_mini_dev_editor.py`](../tools/check_mini_dev_editor.py) uses the page in an isolated
browser without a window, with a simulated pedal that answers with lines recorded from a pedal and
refuses in a chain what the firmware refuses: the chain, replacing a block, scenes, presets, files, the footswitches, the
libraries, the size of every control, another build. [`tools/check_mini_try.py`](../tools/check_mini_try.py) adds the tries, and runs by itself too.
`tests/test_mini_dev_editor.py` tests the policy, `tests/test_preset_sharing.py` the reading of a file. Neither is a test of a pedal, and the page
claims none: `hardware_verified` is false in its profile.
