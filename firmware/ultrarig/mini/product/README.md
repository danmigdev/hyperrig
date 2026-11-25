# The HyperRig product option

Every `.c` and `.S` file here is part of a product build of the MINI image
(`tools/build_hyperrig_mini_image.py --product`), under the same rules as
[`mini/c`](../c/README.md), which is part of every build. `VERSION` is the
version the firmware says with `HRID`. The compiler gets `HYPERRIG_VERSION` and
`HYPERRIG_BUILD` from the builder. `acoustic.c` and `harmonizer.c` are blocks of effects, with their
numbers in `acoustic_tables.h` ([docs/MINI_ACOUSTIC.md](../../../../docs/MINI_ACOUSTIC.md)) and `harmonizer_tables.h`
([docs/MINI_HARMONIZER.md](../../../../docs/MINI_HARMONIZER.md)). `effects.c` is the
frame and the list of the effects `fx_*.c`, with their numbers in `effects_tables.h`
([docs/EFFECT_PLUGINS.md](../../../../docs/EFFECT_PLUGINS.md) says how to add one).
`parametric.c` plays captures that keep knobs ([docs/PARAMETRIC_NAM.md](../../../../docs/PARAMETRIC_NAM.md)).
`midi.c` and `midi_usb.h` are MIDI ([docs/MINI_MIDI.md](../../../../docs/MINI_MIDI.md)).
`loudness.c` with `loudness_tables.h` is the measure of loudness ([docs/MINI_LOUDNESS.md](../../../../docs/MINI_LOUDNESS.md)).
See [docs/MINI_PRODUCT.md](../../../../docs/MINI_PRODUCT.md).
