# The harmonizer

A block of the product build that hears the note that is played and adds one or two voices at
an interval of a key and a scale. It sits at the effect id 24 of the application,
where an old pitch shifter was that the application turns into a newer one: an empty seat in
every table of the effects. Without the product option the image is MINI v4, byte for byte.

- [`mini/product/harmonizer.c`](../firmware/ultrarig/mini/product/harmonizer.c), the sound;
- [`tools/make_harmonizer_tables.py`](../tools/make_harmonizer_tables.py), its numbers;
- [`tools/harmonizer_model.py`](../tools/harmonizer_model.py), the same block in Python, which
  also makes a WAV file of a WAV file;
- [`tools/check_mini_harmonizer.py`](../tools/check_mini_harmonizer.py), its check.

What follows is measured on made strings, on recordings and in the simulator.

## The controls

| Parameter | | Default | |
|---|---|---:|---|
| `key` | 0..11 | 0 | C to B |
| `scale` | 0..10 | 0 | Major, minor, Dorian, Phrygian, Lydian, Mixolydian, Locrian, harmonic minor, melodic minor; fixed major, fixed minor |
| `voice1` | -7..7 | 2 | Steps of the scale: 2 is a third above, -7 an octave below, 0 off |
| `voice2` | -7..7 | 0 | The same for the second voice |
| `balance_pct` | 0..100 | 50 | 0 only the first voice, 50 both, 100 only the second |
| `mezcla_pct` | 0..100 | 50 | 0 only what is played, 50 both, 100 only the voices |
| `nivel_db` | -12..12 | 0 | Level |

In the editor the first four are lists of names.

## What it does with a note

- **In the scale:** the voice is the note so many steps of the scale away: in C major a third
  above C is E, above D is F. An octave is an octave for every note.
- **Not in the scale:** the voice takes the harmony of the note below or of the one above,
  whichever makes the interval nearer to the usual one; it stays in the scale.
- **A bend** goes from the interval of its first note to that of the next note of the scale: a C
  bent to D takes the E to F. A vibrato of up to half a semitone keeps its interval; the voice
  swings with the note.
- **A note that slides** to another one and stays there for 50 to 200 ms gets that one's interval.
- **Fixed:** every note has the same interval, whatever the key: those of the major or of the
  minor scale from its first note, above and below.
- **A chord** is no note. After 48 ms without one the voices take the whole sound at the interval
  of the last note (at the start, of the key), 4 dB softer.
- **Between notes,** from an attack until the new note is known, the voices are 10 dB softer.

The tuning is A at 440 Hz; up to 30 cents beside it nothing changes.

## How

All of it is in whole numbers, for 32 samples at a time.

- **Listening.** A quarter of the rate, between 30 and 900 Hz, every 128 samples (2.7 ms): for
  every lag of 7 to 169 slow samples, how unlike the last look is to the one a lag ago (the
  difference function of YIN, de Cheveigné and Kawahara, JASA 111, 2002), over one look for
  the short lags and over up to four, fading, for the long ones. The first dip under a tenth
  of the power is the period; one look is enough when it is under a twentieth, two that agree
  otherwise. An attack (four times the power of the last some 13 ms) and a sound that is not
  what it was a period ago start it anew, and a lag counts as soon as there is a little more
  new sound than it.
- **The voices** read the last 43 ms faster or slower, between four samples by a third power, and
  step back or on by whole periods (6 to 14 ms, by the same dips) with a fade of 2.7 ms: the
  pitch of a voice does not depend on how exactly the period is known. Without a note the steps
  are of 14 to 28 ms, where a chord is most like itself, and the fade is 5.3 ms.
- **Reused of the application:** nothing but the form of its products (a halfword and a word of
  memory in one instruction; the form with two halfwords resets the chip and is not used). Its
  pitch shifter looks for a place to step to in a window of 10 to 27 ms and does not know the
  note, its tuner works in the main task at its own pace, and its doubler has fixed delays.

## What the measures say

From the attack of a made string (a sum of partials out of tune, a noise of the pick, random
pluck and pickup), until the right note is known:

| Notes | Median, ms | Nine of ten, ms |
|---|---:|---:|
| E2 to A2 | 22 | 27 |
| A#2 to D#3 | 18 | 20 |
| E3 to A3 | 15 | 18 |
| A#3 to D#4 | 10 | 13 |
| E4 to A4 | 10 | 13 |
| A#4 to D#5 | 8 | 10 |
| above | 7 | 9 |

A new note without an attack (a hammer-on) is known after 8 ms, nine of ten after 12.

- From 40 ms after the attack the voice is within 10 cents of the right harmony all of the time,
  for each of the 14 intervals (made strings, A2 to G#5); its level is that of the note within
  0.2 dB.
- 36 solos of GuitarSet with their notes (an acoustic guitar by its pickup, 2,209 notes), from
  80 ms after the start of a note of the scale that sounds alone to 50 ms before its end: the
  interval is another one for 1.3% of the time, most of it in slides and bends; a wrong note is
  heard for 0.3%, most of it other strings that ring. In 18 of them the pitch of the sounding
  voice is within a quarter of a semitone of the right one for 97% of the time, and it is as
  clear as the guitar's.
- Noise 20 dB under the peaks: the same as without. Distorted before the block: never a wrong
  interval on made strings, but softer for 5 to 12% of the time.
- Chords with the fixed interval: what is not at the right pitch is 15 to 28 dB lower for a power
  chord, a triad and a dyad of a third, 6 to 10 dB for a minor seventh chord.

What is not there: a voice is in full some 10 to 25 ms after the note, and a long pick noise makes
it later; two notes that ring together are a chord, or the root of the two; the voices have the
tone of the note that is played, read faster or slower.

## In the firmware

- The sound code (3.5 KB) is in the RAM, as the application's own sound code is. All of it takes
  4,274 bytes of the application's flash, and the heap is 3,584 bytes smaller.
- Its memory, 12,616 bytes, is given by the application when it is added, cleared, and taken
  back. Without it the sound goes by.
- The words of its parameters are replaced when a knob moves; the gains go there over a few
  milliseconds, an interval glides.
- A block is converted when it is added (`effect_setup_create`), whatever the list of old ids
  says: `preset_preflight_convert_effect` leaves the ids 6 and 24 alone now.
- When it is switched on again the first block of the fade starts it anew, so that nothing old
  is heard.
- In live mode a footswitch turns the first modulation of the chain on and off. The old pitch
  shifter was one, as the doubler and the newer pitch shifter are; so is the harmonizer.
- The application counts 11,000 ticks, and 13,500 with two voices, of the 154,950 of a block of 128
  samples. Beside the A2 amp some 22,700 are left. The compiled code takes 30,100 and 32,700
  instructions at most, some 10,500 and 11,500 ticks at the 2.1 cycles an instruction that the
  application's own costs have. The time on the pedal is not measured. When there is no time the
  application lets the block go by.
- It is a block for one channel: in stereo it has one sound.

## What is saved with it

A preset that has the block is for a HyperRig that has it. An older HyperRig, and UltraRig, read
the id 24 as the first pitch shifter and turn it into the newer one. The other way about, a
preset of an old UltraRig that still has its first pitch shifter has a harmonizer in its place.
The form of a stored preset is the same as before.

## What was tried

Nothing on a pedal yet.
