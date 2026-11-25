# The firmware's source

[`firmware/ultrarig/`](../firmware/ultrarig/) holds the UltraRig G alpha11 v2/M5.71 application as
assembly source, and HyperRig's changes of it. Unchanged it builds UltraRig's `app.bin`
(485,772 bytes, SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`), and no image is read for that.
Every address in it is a symbol, so code and data may grow or shrink anywhere after the entry point.

The tree is maintained by hand.

## Build

```
python -B tools/build_ultrarig_app.py --output build/ultrarig-app-NN --expect 4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e
python -B tools/build_hyperrig_mini_image.py --output build/mini-NN --expect d5d6109bc707a6402cbed7506fd53aced23baeb27f6ac7ca8703e3f11d2376a2
python -B tools/build_hyperrig_mini_image.py --output build/product-NN --product
```

The first is UltraRig's application. The second is the MINI v4 application area: `TARGET_MINI`, the
21 changes of the first port under `.if TARGET_MINI` with the original in their `.else`. The third is
HyperRig ([MINI_PRODUCT.md](MINI_PRODUCT.md)): the changes under `.if MINI_PRODUCT` and the code of
`mini/product` as well. [`build_product_release.py`](RELEASE_BUILD.md) makes the second and the third
of every release, so that nothing changes outside the option unnoticed.

Each unit is assembled by [`tools/pi32v2_form_asm.py`](../tools/pi32v2_form_asm.py), which is the
assembler of [pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa) (MIT-0) with the form hints below.
C code is compiled with JieLi's toolchain, under WSL on Windows. The link is made by the upstream linker
and again by JieLi's `ld`; both must give the same bytes. An embedded capture that fails its own CRC
stops the build: the application would never start its engine with it.

The area is 516,096 bytes: the JLFS directory of `mini/area.json`, `app.bin` at `0x120`, `cfg_tool.bin`
after it, the computed sizes and checksums, and `0xFF` up to the end.

## Layout

| Path | Content |
| --- | --- |
| `flash.s`, `flash/` | The flash text, one unit that includes its pieces in address order |
| `ram.s`, `ram/` | The RAM image, run from `0x01C00000` and stored after the flash text; then the bss |
| `tail.s` | The table after the RAM image: 8 zero bytes and 6 code pointers |
| `app.ld` | The linker script: run and load addresses, in `app.bin` order |
| `mini/area.json`, `mini/cfg_tool.hex` | The directory records of the MINI area and the `cfg_tool.bin` in it |
| `mini/append.ld` | The MINI link's second script: the appended code after the trailing table |
| `mini/shims/`, `mini/bindings.json` | The audio shim and the entry guard, and the application addresses they use |
| `mini/c/` | Code for every MINI image (no source file yet) |
| `mini/product/` | HyperRig's own code |

A piece is `<address>_<module>.s`, after its place in the image: a run of functions, or
`_vendor`, `_data`, `_system`, `_mixed` for what is between them. A function is named after its module
and what it does; the comment above gives its range and its module. `sdk_<name>` is a function of JieLi's SDK.
Every other label is `L<address>`. An address that points at a text carries the text in a comment.

## Changing it

- New changes go under `.if MINI_PRODUCT`, new code into `mini/product`, in C or assembly. Assembly calls
  a C function by its name, and C calls an application function, or uses its data, by its name.
- The four routines from `0x02000120` to `0x0200018A` may only change in place, keeping their size: the
  boot loader enters there.
- A line that ends with `#` is half of a pair with the line after it: nothing goes between them.
- For about 5 % of the instructions the original encoding is not the one JieLi's assembler chooses. Such a
  line names its form in a comment (`; @call.xl`), which `pi32v2_form_asm.py` keeps. New code needs no
  hints. When a change moves a target out of reach of a hinted form, the line is assembled without it
  and the build lists it under `form_hint_fallbacks`.
- A function called from flash code and living in the RAM, or the other way round, needs the six-byte
  call: `; @call.xl`.
- When the RAM image grows the heap shrinks, because its end is fixed; the manifest gives its size. The
  application and what is appended must fit the area; the builder refuses one that does not fit.
- The manifest says what moved, what room is left, and which sectors differ from v4.

The build id that the firmware says is over every source file, comments included.

None of this is a test of a pedal.

## Licences

The application is UltraRig's: Required Notice: Copyright (c) 2026 Manuel Aguirre
(https://polyformproject.org/licenses/noncommercial/1.0.0); see
[LICENSE.md](../third_party/ultrarig/LICENSE.md) and [NOTICE.md](../third_party/ultrarig/NOTICE.md).
Code of JieLi's AC79 SDK is under the
[Apache License 2.0](../third_party/ac79-sdk/LICENSE). [PROVENANCE.md](PROVENANCE.md) gives the origin of
every function, including the conditional notice of BlueKitchen's BTstack. Every source file
carries the notice in its header.
