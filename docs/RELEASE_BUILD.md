# Building a release

[`tools/build_product_release.py`](../tools/build_product_release.py) makes a release of
HyperRig for the TANK-MINI from a commit; the workflow
[Build release artifacts](https://github.com/danmigdev/hyperrig/actions/workflows/release.yml)
does the same on GitHub. Neither publishes anything. Both refuse a tree with changes and a
version that is not the one in
[`firmware/ultrarig/mini/product/VERSION`](../firmware/ultrarig/mini/product/VERSION).

## What is made

| File | What it is |
|---|---|
| `HyperRig-X.Y.Z-Windows-x64.zip` | The program: the editor, the installer, and in it the firmware and the loader |
| `HyperRig-X.Y.Z-firmware.zip` | The firmware and the loader by themselves, with their records and licences |
| `provenance.json` | The commit, the inputs, the checksums of the firmware, the loader and the archives |
| `SHA256SUMS`, `NOTES.md` | Checksums of the files above, and the text of the release |

The firmware and the loader are compiled from the source of the commit, twice: both times must
give the same bytes. The firmware without the product option must be the MINI v4 area, byte for
byte: that shows that nothing of the application was changed outside the option. The
same commit gives the same firmware and loader on Windows with WSL and on a fresh Linux clone.

The program is not signed. The checksums say that a file is whole, not who made it.

## What it is made from

[`release/product.lock.json`](../release/product.lock.json) pins everything that is not in the
repository; `fetch` downloads it and checks it, and checks what is there already:

- JieLi's compiler for pi32v2 (the archive by its SHA-256);
- [pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa), the assembler and the linker, and
  [m-bootloader](https://github.com/jvitkauskas/m-bootloader), the form of a stored loader
  (by commit);
- the editor's base, sealed in `HyperRig-MINI-v4-inputs-02.zip`, an asset of the draft release
  `build-inputs-mini-v4-02` (by SHA-256, file by file:
  [`release/mini-v4-inputs.lock.json`](../release/mini-v4-inputs.lock.json));
- Electron (by SHA-256, in `tools/build_desktop_editor.py`).

No stock firmware, device dump, preset or signing key is among them. The notices that go with the
files are [`release/NOTICE.md`](../release/NOTICE.md) and the texts it names; the builder refuses a
notice that names what is not there.

TONE3000's publishable key is not in the repository: `--tone3000-key FILE`, or the secret
`TONE3000_PUBLISHABLE_KEY` of the workflow. Without it the program has no Browse TONE3000.

## Here

On Windows, with WSL (Ubuntu) and its `gcc`, Node.js, and Microsoft Edge for the checks:

```
python -m pip install pyelftools==0.33 pillow==12.1.0 pefile==2024.8.26 websocket-client pytest
python -B tools/build_product_release.py fetch --editor-base HyperRig-MINI-v4-inputs-02.zip
python -B tools/build_product_release.py parts --version 0.2.1 --output build/release-parts
python -B tools/build_product_release.py finish --version 0.2.1 --parts build/release-parts --output build/release-0.2.1 --tone3000-key FILE
python -B tools/build_product_release.py verify --output build/release-0.2.1
```

Before a release the checks are run by a person, and the tests:

```
python -B tools/check_mini_panel.py build/release-parts/firmware
python -B tools/check_mini_scenes.py build/release-parts/firmware
python -B tools/check_mini_midi.py build/release-parts/firmware
python -B tools/check_mini_usb.py build/release-parts/firmware
python -B tools/check_mini_library.py build/release-parts/firmware
python -B tools/check_mini_globals.py build/release-parts/firmware
python -B tools/check_mini_effect_block.py build/release-parts/firmware
python -B tools/check_mini_effects.py build/release-parts/firmware
python -B tools/check_mini_harmonizer.py build/release-parts/firmware
python -B tools/check_mini_embedded_capture.py build/release-parts/firmware
python -B tools/check_mini_entry_guard.py build/release-parts/firmware
python -B tools/check_mini_boot_guard.py build/release-parts/firmware
python -B tools/check_mini_stage_target.py build/release-parts/loader
python -B tools/check_installer.py build/release-parts/loader
python -B tools/build_desktop_editor.py --bundle build/release-parts/editor --output build/program --firmware build/release-parts/firmware --loader build/release-parts/loader
python -B tools/check_mini_dev_editor.py --bundle build/release-parts/editor --output build/CHECK-01
python -B tools/check_desktop_editor.py --program build/program --output build/CHECK-02
python -B tools/check_desktop_installer.py --program build/program --loader build/release-parts/loader --output build/CHECK-03
python -B -m pytest -q tests
```

They run the built bytes in a simulator and the program with a simulated pedal. They are no test
of a pedal, and say nothing of the sound.

## On GitHub

**Actions > Build release artifacts > Run workflow**, on `main`, with the version. The files are
in the run. With **Attach the files to a draft release** they are also put into a draft, which
only those who may write to the repository see; a person looks at it and publishes it. A release
or a draft of the same version that is there already is not touched.
