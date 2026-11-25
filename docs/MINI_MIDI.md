# MIDI

The pedal as a MIDI device over USB-C, in both directions, beside the serial port of the editor
(`firmware/ultrarig/mini/product/midi.c`, and `midi_usb.h`, the port). Off until it is turned on: in the editor's
settings, or with `MIDI on` on the console.

## What the messages do

As it comes; the controllers can be others, or off.

| Message | In | Out, when the player changes it |
| --- | --- | --- |
| Program change 0 to 31 | Preset 1A to 11B | The preset |
| Controller 20 | Scene: 0 to 7; 8 the next, 9 the one before | The scene, 0 to 7 |
| Controller 21 | Bypass: on from 64 | 127 or 0 |
| Controller 22 | Tuner: on from 64 | 127 or 0 |
| Controller 23 | Tap from 64, with the time it came | |
| Controller 24 | Amp: on from 64 | 127 or 0 |
| Controllers 102 to 117 | Block at the places 1 to 16 of the chain: on from 64 | 127 or 0 |
| Controller 7 | Volume, a square, before the wheel's | |
| Four controllers of choice | A knob of a block, between two ends of its way | |
| Clock | Tempo, 40 to 300 | |

Received on all channels, one or none; sent on one or none. Everything else is passed over: notes, pressure, bend,
SysEx, other cables, what is torn.

- **In** goes through the functions that the footswitches and the console call, in the main task, once a turn (10 ms),
  in the order it comes: a preset and its scene, or bypass, or eight smaller things in a turn, and the rest in the
  next. Of several presets in a row the last is done.
- **Out** is found by looking, turn by turn. What a message did is not told, and a message that comes straight back
  within half a second is not taken. A preset or a scene that changes takes its blocks with it: one message.
- **Clock:** each packet has the time of its interrupt. The tempo is of the last beats, the newest to a quarter. A late
  packet or a short stop does not move it, two beats of another length do. It is set when it differs by 0.4.
- **When nobody reads,** what is new is not sent; when the old packet is taken at last, the preset and the scene of now
  follow it.

## Where it is kept

`GSAVE` writes it behind the 32 bytes of the lights in the record `TKGX` of the settings: the letter `M`, whether the
port is on, and the thirty bytes of the settings; the record is 64 bytes then. An older HyperRig reads the 32 bytes,
and drops the rest when it writes the lights. Presets are untouched.

## The console

`MIDI` answers `MIDI <port> <kept on> <settings> <in> <out>`: the port 0 off, 1 waiting, 2 on, 3 refused; the settings
as sixty digits; how many messages came and went. The thirty bytes: clock on; channel in (0 all, 255 off); channel out;
the controllers of scene, bypass, tuner, tap, amp, volume and the first of the blocks (255 off); and four times
controller, place and knob from 0, and the two ends in percent.

`MIDI on` and `MIDI off` are the port, `MIDI =<sixty digits>` the settings, `MIDI >b01402` does as if those bytes had
come, without the port. The editor gives all of it words, and checks what it sends.

## The port

The application's USB device is the SDK's, with a list of up to eight functions. The serial port is the first, on
endpoint 2, unchanged. MIDI is the second: an association of two interfaces (audio control 2, MIDI streaming 3) and
bulk 64 in and out on endpoint 1, which the HyperRig loader uses on the same controller. The product number stays: it
is the same device to the computer, a composite one as before, with one part more; no driver is needed. 175 bytes of
configuration instead of 75. Endpoints 3 and 4 are still free.

USB is the only way of the editor and of an update, so:

- Without the setting the descriptors and every answer are the same bytes as before, and endpoint 1 is untouched.
- Turned on, it is a trial: the link restarts with it, as after the cable was pulled; when the editor is not back
  within 45 s the link restarts without it and the setting is off. `GSAVE` keeps it only when the editor is there over
  the link that has it. Switched off and on, the pedal is as it was saved.
- At every connection: a computer that reads the description and does not take it within 15 s gets the link without
  the MIDI port, until the cable was out for three seconds.
- The guards of the start and the ROM's update mode ([MINI_PRODUCT.md](MINI_PRODUCT.md)) are as they were.

The interrupt puts packets into a row of eight; when it is full the next waits in the controller and the computer
waits. It costs 3,370 bytes of flash and 864 of RAM; a turn 30 instructions with the port off, about
1,000 with it on, 500 more for a message.

## Checks

```
python -B tools/check_mini_midi.py build/product-NN --before build/product-of-before
python -B tools/check_mini_usb.py build/product-NN --before build/product-of-before
```

The first runs every message in and out, the stream (running status, real time, SysEx, garbage, floods), the clock and
the settings, through the handler of the interrupt. The second runs the USB device of the application on a simulated
controller with a computer: enumeration, both functions at once, requests that are not for it, floods, resets, the
cable, the two guards. Neither is a test of a pedal: the real controller, its timing and real computers are not
simulated.

## Bluetooth

Nothing of this is over Bluetooth. Facts for later: the firmware has a BLE server with one service of its own (a
serial line, 6e400001) in a table of attributes in the flash; MIDI over BLE would be a second service there
(03b80e5a-ede8-4b33-a751-6ce34ec4c700) with one characteristic, its packets with times, and another line in the
advertisement. The stream and everything behind it here would be the same.
