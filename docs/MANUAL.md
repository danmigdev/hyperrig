# HyperRig on the TANK-MINI: manual

## On the pedal

| Do | What happens |
|---|---|
| A, B or C | That preset of the bank |
| The same again | Bypass |
| A, B or C held one second | Saves there |
| A+B | The bank before |
| B+C | The next bank |
| B+C held one second | Tuner; a tap closes it |
| A+B held three seconds | Bluetooth on, and for one minute a computer may unlock editing over Bluetooth (the lights pulse blue) |
| A+B held six seconds | Bluetooth off |
| The wheel | Volume; in the editor it can be switched off |

The editor shows the battery at the top. There are 32 presets, 1A to 11B. Under a tenth of the battery the light of the preset flashes
every eight seconds.

## Footswitches

In the editor, **Footswitches** has the lights, and one choice of what A, B and C do:

| | Tap | Held one second | A+B, B+C |
|---|---|---|---|
| **Presets** | A preset of the bank; again, bypass | Saves there | The bank; B+C held, the tuner |
| **Stomp** | Its block on and off | Nothing | The preset before and the next; B+C held, the tuner |
| **Scenes** | Three scenes | A the preset before, C the next | The three scenes before and the next; B+C held, the tuner |

For Stomp, choose the block of each switch there. It is the same for every preset: the first
delay, for example, or nothing in a preset without one. Any other action can be given to a tap, a
hold or a double press; the choice is then called **Custom**, and has no pairs. **Save to pedal**
keeps it. The editor shows the choice beside the preset's name when it is not Presets.

**Ramp while held** is a choice for the hold of A, B or C, in Stomp, Scenes and Custom: while the
switch is held, a knob of a block goes to where you set it, in the time you give it, and when you
let go it goes back to where the preset has it, in its own time. A tremolo that speeds up while you
stand on the switch, for example: choose the block (the first of its kind in the chain, in every
preset that has one), the knob, where it goes, and the two times, up to 12.75 seconds each. A tap
of the switch stays what it was, and acts when you let go; the ramp starts after a fifth of a
second held, and the switch then does nothing else, also when it is let go. When the tap and the
double press of that switch do nothing, the ramp starts at once (after 45 ms, the time a pair
waits). Pressed together with another switch it is a pair as before. A preset or a scene that
changes ends the ramp.

**Ramp on/off** is the same for the tap: one press sends the knob to where you set it, where it
stays, and the next brings it back, each in its time. The switch is then the ramp's alone. With
the tuner on, a press of it closes the tuner.

## The editor

It finds the pedal by itself. **Ctrl +** and **Ctrl -** make everything larger and smaller.

**Presets** are on the left, in banks of three. **+** makes a new, empty one.

**Saving:** the line under the preset's name says whether it is saved, and where **Save** writes;
Ctrl+S does the same. **Discard** goes back to what is saved. **Save as** keeps it in another
slot, with its name: use it for a copy, or for a new preset that has no slot yet.

**Files:** the buttons above the list save one preset, or all of them, to a file, and load them
back: all at once, each to the slot it came from, or one, which you then save where you want it.

**Presets to start with:** after HyperRig's first install, on a pedal that has none, the editor puts
three in 1A to 1C: **Clean**, **Crunch** and **Lead**, built-in blocks only. Their cab is HyperRig's
own IR, made from filters (`tools/make_factory_presets.py`), in the first free cab slot. They are in
the program's folder `presets` too, with the cab as a WAV file: **Try from files...** plays them.

**Names:** the pencil beside the preset's name and the one beside the scenes; Enter keeps the new
name, Esc leaves the old one. A preset has up to 23 letters, a scene up to 15, plain letters and
digits. A new preset, or one from a file, can be named before it is saved.

**The chain** is in the middle. **+** adds a block, dragging moves it, and a block can be put on
two paths, A and B. The amp is a block too: a NAM capture. A chain holds 16 blocks besides it; with
it, 10 fit before it and 10 after. How many fit also depends on the pedal's time and memory: the
numbers at the top say what is left, and when there is no more time for a block the pedal lets it
go by.

**Replace a block** from its menu, with the right button on it or Shift+F10: under **Replace with**
the blocks of its own kind come first, and each says whether it fits. The new block takes the old
one's place, its path, and is on in the scenes where the old one was on; its knobs start at their
usual values. The sound stops for a moment, once. When the new block does not fit, the old one
stays as it was, in every scene, and the editor says why.

**Captures and cabs:** open the library of the amp or of a Cab IR block, and load a `.nam` or a
`.wav` file, or press **Browse TONE3000**. A capture must be of architecture A2. There are 15
places for captures and 8 for cabs (seven of 85 ms, the last of 42 ms). A capture that keeps knobs of
its amp (a parametric one, of three channels) shows them in place of Gain, Bass, Mid, Treble and
Presence, by their names and numbers; presets and scenes keep them.

**Cab:** **Low cut** takes the boom away and **High cut** the fizz. Off is no cut. They can be turned while you
play; each takes some 3 % of the CPU while it is on. An older HyperRig plays the preset without them.

**Trying** plays a sound on the pedal before anything is saved; see below.

**Tap** the tempo or type it. **Tuner** shows the note. **Stage** is a large view for playing.

## Trying a sound

| What | Where |
|---|---|
| Presets from files | **Try from files...**, above the list of presets; several files at once, if you like |
| Captures and cabs from files | **Try a file...**, in their library; several at once |
| Captures and cabs of TONE3000 | **Try it**, where you choose the tone |
| Presets of Patchstorage | The **Patchstorage** button (its logo), above the list |

You hear it at once, and nothing is saved on the pedal. A bar at the top says what you are
trying, whose it is and under which licence. **Previous** and **Next** go through the list.

- **Volume.** It starts quietly and rises by itself, up to the preset's own volume and never above
  the limit: 0 dB, or the volume of your own preset. It stops rising when the output is loud.
  **Quieter** and **Louder** change it. A capture or a cab rises to the volume of your preset.
- **Back** puts back what was playing: the preset, the scene, the capture, the cab, and the changes
  you had not saved. When something could not come back, it is asked before the try, and you can
  save it first: blocks you added or took away, a capture or a cab that is in no slot.
- **Keep** asks for a slot and a name. A preset is kept as you hear it. The capture and the cab it
  brings go to free slots, if you want them.

Before a preset is tried you see what it needs and this pedal does not have. Its scenes can be
tried too; each comes at its own volume. A preset that is chosen with a switch on the pedal ends the
try. While one is loading, a switch only stops it. If the pedal is switched off, what you tried is
gone, and the presets are as they were. A preset with more than one cab of its own plays with one of
them until it is kept.

**Patchstorage's list** can be sorted: the newest first, the most downloaded, or the most liked. It
sorts what you searched for too.

**Sharing yours:** export a preset to a file and give it to Patchstorage on its own page, in your
browser, with your own account (**Share your own...**). The program sends nothing.

**Backup:** in Settings, **Back up the pedal...** puts everything in one file: the presets, the captures
and cabs with the slot each is in, and the settings. It loads each preset, so the sound is muted for a
moment, and nothing on the pedal is changed. **Restore a backup...** puts back what you tick; what the
pedal has already is not sent again, and what is not in the file stays unless you tick that it should be
erased. It offers a backup of the pedal as it is now first. MIDI over USB stays on or off as it was.
Import also takes the file.

**CPU overload:** when the pedal runs out of time while a preset plays, it lowers the oversampling of a block
or switches one off by itself, and the editor says which. **Turn it on** in that message switches it on again.

## Scenes

A preset has up to eight: the same blocks, amp and cabinet, with other knobs and other blocks on
or off. **+ add** makes one, with the sound as it is at that moment. A scene comes at once,
without a gap, and the knobs move smoothly; another preset takes a moment.

**A capture for each scene:** in the amp's panel, **Capture for** says **All scenes** or **This scene**. With
**This scene** the capture you choose, load from a file or keep while trying is for the scene that is on, and
the others keep theirs. A scene takes its capture from the library. Such a preset is for this HyperRig: an
older one shows its place as empty. When a scene or a preset brings another capture, the amp fades out
and in again: a short gap in the amp, while the cab, the delays and the reverbs ring on.

Adding, replacing, moving or taking away a block, or another IR, is for the whole preset. A block
you add is in every scene, as it stands when you choose another scene or save; from then on each
scene has its own. For a block that only one scene shall have, switch it off in the others.

Eight scenes always fit with up to eleven blocks; with more it depends on how many knobs differ,
and the editor says when there is no room. A preset that uses more than four scenes is for a
HyperRig that has eight.

## Bluetooth

The program can edit the pedal over Bluetooth, without the cable, on a computer that has Bluetooth.
Turn Bluetooth on at the pedal (A+B held three seconds) and keep the pedal near the computer. In the
program, **Connect via Bluetooth** is on the screen shown when nothing is connected, and in the menu of
the connection, which also has **Connect via USB** to go back to the cable. The pedal shows as
**HyperRig** and four characters; when there are several, the program asks which one.

Editing is locked until the pedal lets the computer in. A computer that was connected once with the
cable is let in at once. Otherwise the editor says **Editing is locked** and only looks, with a bar
across the top: hold A and B on the pedal for three seconds, let go, and within one minute press
**Unlock editing**. The computer then stays unlocked; the pedal keeps up to four. Connecting within that
minute unlocks it by itself. In the menu of the connection, **Let another device in** opens the same minute
from a computer that is in, and **Forget phones and computers…** makes every phone pair again and every
computer be let in again.

Everything the editor does over the cable it does over Bluetooth, except **Level volumes** and updates of
the firmware: they need the cable. The pedal ends a link when the editor disconnects, and a link on
which nothing came for 90 seconds, so that a computer that keeps it after the program has closed does
not hold the pedal. While it connects, the program says so, and how far it is: over Bluetooth it may
take up to half a minute, and when a connection does not come at once the editor tries again by itself.
When the link is lost, because the pedal was turned off or went out of reach, the editor reconnects by
itself for three minutes. The program starts the way it was connected last: over Bluetooth, even with
the cable in for power, and over the cable when the pedal is not found over Bluetooth.

## MIDI

The pedal can be a MIDI device over the USB cable: a program, or another device through a computer or a USB MIDI host,
changes its presets, scenes and blocks, and follows what you change on the pedal. It is off at first. In the editor,
**Settings**, **MIDI**: turn it **On**. The pedal leaves the computer for a moment and comes back with it; when the
editor does not find it again, the pedal turns it off by itself. **Save to pedal** keeps it on.

| Message | |
|---|---|
| Program change 1 to 32 | Presets 1A to 11B |
| Controller 20 | Scene: 0 to 7; 8 the next, 9 the one before |
| Controllers 102 to 117 | The blocks by their place in the chain: on from 64 |
| Controllers 21, 22, 24 | Bypass, tuner, amp: on from 64 |
| Controller 23 | Tap tempo |
| Controller 7 | Volume |
| MIDI clock | Tempo |

**What the messages do** changes the numbers, and gives up to four controllers a knob of a block each, as with an
expression pedal. The channels are beside it. What a message changed is not sent back.

## Level volumes

**Level volumes…**, under the list of presets and behind the gains at the top, sets the output gains
so that the same stroke of your guitar is as loud in every sound: clean, crunch or distorted.

1. **Record my guitar**, once: play chords and single notes for some ten seconds, as you do on
   stage. The pedal plays the strokes itself from then on. Record again with another guitar, or
   choose built-in strokes, which are less accurate.
2. Choose **this scene**, **this preset** with its scenes, or **all presets**, and press **Measure**.
   The pedal is silent meanwhile, some fifteen seconds for each sound. A footswitch stops it, and
   nothing is changed.
3. The list says how loud each is now, and its gain before and after. **−** and **+** at the top
   move all of them, those of a row only that one. "Loud notes reach the limiter" says where the
   sound would change: choose a softer volume, or leave it.
4. **Save** writes the gains. Nothing else of the presets changes. For a single scene it sets the
   gain, and you save the preset as usual.

Save or discard your changes first, or only this scene can be measured.

## Acoustic

Put it in a chain without the amp, before delays and reverbs. With the amp on there is room for
6 strings, not for 12: the pedal then lets the block go by.

| Control | |
|---|---|
| Strings | **6** or **12**. 12 uses more of the pedal |
| Body | How much of the wooden box is heard |
| Top | Brightness: less for a bright pickup, more for a dark one |
| Decay | How fast notes die. 0 keeps the sustain of the electric |
| Air | The wood, and the room around a near microphone |
| Doubles | The second strings, with 12 |
| Level | Loudness |

The low strings of a 12-string are doubled an octave above, the thin ones in unison. On the
lowest strings the octave takes a moment to be there in full.

## Octaver, Swell, Reverse Delay, Vintage Delay, Ensemble

**Octaver** (in Pitch) plays one octave below, two below and one above beside your sound, for single
notes: a chord has no single octave. Put it first, before drives and the amp. Octave +1 is
clearest high on the neck with the neck pickup; Fuzz pushes it.

**Swell** (in Dynamics) takes the pick away: every note grows over the time of Attack. If held chords
start again by themselves, turn Sensitivity down; if a note does not swell, turn it up.

**Reverse Delay** (in Delay) plays what you played backwards, in pieces as long as Time. Up to the
middle of Mix it comes in beside your sound, from there your sound goes out.

**Vintage Delay** (in Delay): repeats that grow darker and softer, with a slow waver (Depth), as of an old
delay. While Time is turned the pitch bends. At a Feedback of 100 the repeats go on and slowly fade.

**Ensemble** (in Modulation): three voices of your sound, each a little late and a little out of tune, as in
the string machines of the seventies. It is about as loud at every Mix.

## Settings for every preset

The gear at the top right. What is set there is heard in every preset, in bypass too, and at once; it
is in no preset. **Save to pedal** keeps it when the pedal is switched off: until then the line beside
the button says *Unsaved changes*, and closing the window asks.

| | |
|---|---|
| Global EQ | Five bands at the end of the chain, 12 dB up or down: 100 Hz and 7 kHz are shelves. **On** switches it off and on again, **Set flat** takes it away. With stereo it makes the sound mono |
| High-pass | Takes away what is below this frequency at the input: rumble. At first 55 Hz |
| Cancel the pedal's own whine | A faint tone of the electronics: the pedal learns it in silence, and takes it away |
| Output limiter | Holds the output under the ceiling, so that it does not clip. Release is how fast it lets go |
| Let tails ring out | Delays and reverbs end by themselves when they are switched off, or when another preset comes: up to four of them, some four seconds at most, and they fade at the end. Each needs one of the 16 places, memory and time of the pedal's processor: with a preset that is nearly full they stop at once |
| Smooth scene changes | The knobs move to the new scene; off, they jump |

Each band of the EQ that is in use takes about 3 % of the pedal's time for blocks. Where there is no
room for one the editor says so; a preset that is nearly full may start with a block switched off.

**Input level of a capture:** in the amp's block, **Calibrate** listens to the guitar for as long as
you play your loudest chords, then suggests the input trim for that capture. Nothing is changed until
you press the button that sets it, and it stops by itself after three minutes.

## Harmonizer

It hears the note you play and adds one or two voices at an interval of a key and a scale. Put it
before the amp and before distortions, delays and reverbs; a compressor may go before it.

| Control | |
|---|---|
| Key, Scale | Of the song: the voices stay in it. **Fixed** scales give every note the same interval |
| Voice 1, Voice 2 | What the voice sings to your note: from an octave below to an octave above, or Off |
| Balance | 0 is the voice 1 alone, 50 both, 100 the voice 2 alone |
| Mix | 0 is your guitar alone, 50 both, 100 the voices alone |
| Level | Loudness |

It is for single notes. Bends and vibrato take the voices with them. A chord is moved as it is and a
little softer: a power chord at the interval of its root, another one at that of its root if it has a
clear one, or of the last note. For other chords choose a fixed scale and a fifth or an octave. It
follows the reference of the tuner. Each voice uses more of the pedal.

## Pitch Glide

One voice of your sound whose pitch slides from where you play to an interval and back, as the
**Bend** knob moves: a footswitch's ramp, a MIDI controller (an expression pedal through one), or
your hand. Put it before the amp and before distortions, delays and reverbs.

| Control | |
|---|---|
| Interval | Where the voice goes at full bend: up to two octaves up or down |
| Bend | How far along the way it is: 0 is the note you play, 100 the interval |
| Mix | 100 is the voice alone, so the bend is all you hear. Lower, your guitar plays beside it, and at rest only your guitar is heard |
| Level | Loudness |

To glide while a switch is held: in Footswitches, choose **Ramp while held** for its hold, the
block Pitch Glide, the knob Bend, 100, and the times up and back. With nothing on the switch's
tap and double press the glide starts at once. To glide up with one press and back with the next,
choose **Ramp on/off** for its tap instead.

It hears the note you play, as the harmonizer does, and is cleanest on single notes and power
chords; full chords move as well, less cleanly. Its sound comes 0.7 ms after your guitar. It uses a
little more of the pedal than the harmonizer with one voice.

## Limits

- Windows only. The program is not signed.
- **No Bluetooth audio and no USB sound card.** Over Bluetooth only the program edits the pedal; there is no app
  for phones and tablets yet. Editing over Bluetooth was tried on one Windows computer with its USB Bluetooth adapter.
- Headphones, charging, very long sessions and a comparison with the original firmware by ear
  were not tried. In the original the pedal switches itself off three minutes after the
  battery is empty; HyperRig does not.
- The global EQ has one channel: in stereo it is mono.
- Of a chain of more than 10 blocks without the amp, the last ten are in stereo in the headphones;
  the first ones are mono. The editor says when a block becomes mono.
- The tuner needs 7 KB of the memory that the effects share. Beside a preset that leaves less it has
  none, and the editor says so.
- A preset that is tried can still be loud, through a block of its own for example: keep a hand on
  the wheel.
- The acoustic block is one sound in stereo. A preset with it is for a HyperRig that has it:
  an older one, and UltraRig, make a room reverb of it.
- Octaver, Swell, Reverse Delay, Vintage Delay, Ensemble and Pitch Glide are one sound in stereo too. An older HyperRig leaves
  them out of a preset and keeps the rest.
- The harmonizer is one sound in stereo. A preset with it is for a
  HyperRig that has it: an older one, and UltraRig, make a pitch shifter of it. In a preset of an
  old UltraRig its first pitch shifter is a harmonizer.
- The first start of HyperRig makes room for its presets where the original has its amp
  models. They come back with the original firmware.
