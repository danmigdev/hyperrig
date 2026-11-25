# Third-party material in firmware/mini_stage

`usb_midi.c` and `usb_midi.h` are from `upstream/m-bootloader` (`src/usb_midi.c`,
`include/usb_midi.h`, commit `3ac7651a019fa44daba061b05654278496477b64`) with the
changes named in them. The timer, P33 and efuse sequences of `platform.c`, the
start-up of `start.S` and the place and size of the loader (`stage.ld`) follow
its `src/platform.c`, `src/stage_start.S`, `tools/target.ld.S` and
`docs/SPEC.md`. The form of the stored loader that `tools/build_mini_stage.py`
makes follows its `tools/fwsc.py`.

m-bootloader's own notice says of the USB part: the register sequences were
written from the facts in JieLi's AC79 SDK (Apache-2.0) and felucca-bsp's
`chip/fm1_usb.h` (MPL-2.0); no code was taken from either.

m-bootloader is under the MIT License:

```
MIT License

Copyright (c) 2026 Julius Vitkauskas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
