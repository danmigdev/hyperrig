# NAM captures that keep knobs

A parametric capture is a NAM model of an amp or pedal over the range of some of its knobs, where an
ordinary capture is of one setting. The pedal plays those of architecture A2-Lite, and the amp's own
controls move the knobs. What follows was shown offline, with a synthetic amp and the simulator. A
pedal has played the synthetic amp; none has played a model of a real one.

## What exists

| | Source |
|---|---|
| A2: 23 layers, kernels 6 and 15, LeakyReLU 0.01, a head of 16, condition = the audio; 8 channels (Full) and 3 (Lite) in one file | [trainer](https://github.com/sdatkinson/neural-amp-modeler) `c3eadd2`, [Core](https://github.com/sdatkinson/NeuralAmpModelerCore) `d3189ed`, file 0.7.0, MIT |
| The trainer and Core have no model with knobs. FiLM, gating and a condition network are options of their WaveNet that A2 does not use | the same |
| `ConcatWaveNet`: the knobs beside the audio, as inputs of the first projection and of every layer's mixer. 8 + 2 x (knobs - 1) channels by default | [neural-amp-modeler-parametric](https://github.com/phillipmself/neural-amp-modeler-parametric) `a368441`, MIT |
| `HyperWaveNet`: a small network makes the weights of the knobs, all but the dilated convolutions. One hidden layer of 16, rank 2; 8 channels | the same |
| `HyperA2`: the same for A2-Full and A2-Lite, in one file. This is parametric A2-Lite | [the fork](https://github.com/DLC86/neural-amp-modeler-parametric) `d1d2bf6` (31 October 2026), `docs/hyper_a2.md`, MIT |
| The knobs in the file: `config.params`, each with name, min, max, default, and `continuous` (given to the network as -1..1) or `switch` (one input for each position); file version 1.0.0 of its own | the same, `_spec.py` |
| Captures: two of a 5153 (`models-5153-v1`, 8 channels or more, no licence stated: not used). On TONE3000 one file that steps through fixed models with the Slim control, which is no conditioned model | [releases](https://github.com/phillipmself/NamParametricPlugin/releases), [71504](https://www.tone3000.com/tones/parametric-nam-a2-preview-use-slim-as-gain-param-71504) |
| The method of captures at chosen knob settings | [arXiv 2507.02109](https://arxiv.org/abs/2507.02109), [2509.26564](https://arxiv.org/abs/2509.26564) |

No public A2-Lite model with knobs was found. The trainer makes one (`nam-capture --hyperwavenet`, Export
HyperA2).

## The idea: with the knobs at rest, it is a plain capture

A knob that rests is a constant, and what it adds can be folded into the numbers of a plain A2-Lite,
which the engine plays unchanged and at no more cost.

- **Knobs beside the audio.** Each mixer adds a constant to the bias of its convolution. The constant of the
  first projection, and the biases of the 1x1 layers, are constants of the residual, and move forward into
  the biases of all later convolutions: `bias(l) += (sum over taps of W(l)) x (constants before l)`. Only
  the 69 biases move, in proportion to the knobs. They are 32-bit words of the engine.
- **Weights made of the knobs** are the plain network of that setting. With the 1x1 biases moved forward too,
  388 numbers move: 69 biases, 69 mixers, 198 of the 1x1 layers (the last one's go nowhere), 3 of the first
  projection, 48 of the head and its bias.
- **FiLM whose condition is the knobs alone** folds as well: scales and shifts before and after the
  convolution, the mixer, the activation (a positive scale passes through LeakyReLU) and the 1x1 layer.
- **Not:** a condition that has the audio in it (it varies with every sample), a negative scale after the
  activation, gating and blended activations, a condition network, weights of the convolutions that
  follow the knobs (there is no room to store how).

| Checked, of float models | Largest difference after the receptive field |
|---|---:|
| ConcatWaveNet, 4 knobs, made-up weights | 4e-16 |
| FiLM at every place, one by one and together | 3e-16 |
| HyperA2-Lite, trained | 3e-16 |

## How it is stored

A slot holds 8,152 bytes, a plain A2-Lite 4,892. Behind it, in the same file, little-endian:

| | Bytes |
|---|---|
| `A2P1`, version, knobs (1 to 5), units (24 at most), directions (8 at most), slope of 1024, 0 | 12 |
| For each knob: the control, name (11), min, max (float), what the network is given at -120, 0 and 120 (Q14) | 26 |
| A shift for each of 71 groups: the biases, the mixer and the 1x1 of a layer; the projection, the head, its bias | 71 |
| The units, then the directions: each a row of a shift (1), a bias and weights of 16 bits | 3 + 2 for each input |
| For each of the 388 numbers, the directions, 8 bits each | 388 x directions |
| The length of all this, `AP`, a CRC-32 of the whole file | 8 |

A row is `(bias x 16384 + sum of weight x input + half) >> shift`. The units take the knobs; what is negative of
them is multiplied by the slope; the directions take the units. Then
`number = plain number + ((sum of direction x byte) >> shift)`. At the middle of the knobs every direction is 0, so
there it is, bit for bit, the plain capture. The file's last word is its identity, as of every capture.

The converter ([`product-parametric.js`](../app/mini/product-parametric.js)) takes the model's own hidden layer
for the units, and the directions that matter most in the output (by the output's derivatives at the middle and the
ends of the knobs), as many as fit: 7 with two knobs, 6 with four.

## What it is worth

Two synthetic amps (gain 0 to 40 dB, a soft clip, and one or three tone knobs) and networks trained on them for 6,000
or 7,000 steps. ESR is against the amp, at places of the knobs that were not trained, corners among them, without the
constant of the output:

| 3 channels | Knobs | Model | In the pedal's numbers | Stored form against the model | Bytes |
|---|---:|---:|---:|---|---:|
| HyperA2-Lite | 2 | 0.0076 | 0.0083 | -34 dB (median), -29 dB (worst) | 8,108 |
| HyperA2-Lite | 4 | 0.0277 (median) | 0.0311 (median) | -20 dB, -11 dB at the corner where all are at 0 | 7,801 |
| ConcatWaveNet | 2 | 0.0525 | 0.0527 | -41 dB, -37 dB | 5,839 |

The whole-number arithmetic alone is 110 to 134 dB below the sound. With three channels the knobs beside the
audio are a poor way to model an amp; HyperA2-Lite is the one to train. Away from its middle a capture may
have a constant of up to -59 dBFS in its output, which nobody hears.

A knob that moves steps the numbers, in 16 steps over the pedal's own time for such changes (42 ms). What is
left against a movement without steps: 64 to 67 dB below the sound for one notch of the editor, 37 to 39 dB
for half the range of Gain and 32 for the whole range, as in a change of scenes.

## On the pedal

`firmware/ultrarig/mini/product/parametric.c`, and four places of the application under `.if MINI_PRODUCT`.

- **The controls.** Gain, Bass, Mid, Treble and Presence of the amp, in the order of the knobs' names
  (Master goes to Presence; Volume stays a volume). A control that moves a knob leaves its filter, or the extra gain,
  flat. The values are those of AMPEQ: -120 is one end, 0 the knob's usual place, 120 the other end. So
  presets, scenes and the commands are as ever, and **nothing of their stored form changes**; 0 changes
  nothing, of a knob as of a filter. Switches, and knobs beyond five, stay at their usual place.
- **A change.** A task works out where every number goes and its step (the sound does not wait). The sound task takes
  the steps in each half block, half of the numbers at a time, where the second core has no work and nobody
  reads them.
- **The cost.** 1,602 bytes of flash; 352 bytes less of heap, and 6.2 KB of heap while a capture with knobs plays;
  1,940 ticks of a block's 154,950 while a knob moves (2,775 instructions in a half block at the 2.1 cycles of
  the application's own costs), 7 instructions at rest. Without the memory it plays as stored, and the controls are filters.
- **`AMPK`** says the knobs: a line for each with its 26 bytes in hexadecimal digits, then `AMPK end`.

HyperRig 0.2.0 refuses such a file (`rc=-1`) and plays on; it cannot use a slot that holds one.

Where a model cannot be folded, what is left is several captures of the same amp, one for each preset:
a scene keeps the knobs of a capture, not another capture.

## In the editor

A `.nam` of one of these forms is converted in the page, in about ten seconds, and loaded like any other. The
amp's panel shows its knobs by name, with their own numbers; the message after loading says how near the pedal's
copy is. Refused in words: more than 3 channels, convolutions that follow the knobs, another rate.

## Limits

- Tried on a pedal with a synthetic amp only, not with a model of a real one. The directions are the limit for many knobs: with four or
  five the copy may be rough, and the message says so. Twelve directions would give -31 dB with four knobs, sixteen
  -36 dB: room for that would be a second slot.
- Training needs captures at some 15 settings a knob (the trainer's advice); there is no such service.
- Stereo, calibration and trim are those of any capture.

## Checks

| | With |
|---|---|
| The arithmetic of the page against a second form of it, the fold, what is refused | `tests/test_mini_parametric.py` |
| On the built firmware, in the simulator: loading, saving, the numbers to the bit, the way there and its cost, the filters, the sound against a plain capture with the same numbers, the place in the sound task, damaged files, no memory | `tools/check_mini_parametric.py` |
| The page, its worker and the panel, with a simulated pedal | `tools/check_mini_dev_editor.py` |
