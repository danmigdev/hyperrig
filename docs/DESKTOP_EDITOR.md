# The desktop program

A program for Windows with HyperRig's editor and installer for the TANK-MINI: a window, no browser
tab, no server, no administrator rights. It finds the pedal by itself when it is connected by USB.

It is Electron with [the editor's page](MINI_DEV_EDITOR.md) unchanged, so the page reaches the pedal
through the serial interface it uses in a browser.

## Building and checking

    python -B tools/build_desktop_editor.py --bundle build/hyperrig-editor-NN --output build/hyperrig-desktop-NN --firmware build/release-parts/firmware --loader build/release-parts/loader
    python -B tools/check_desktop_editor.py --program build/hyperrig-desktop-NN --output build/CHECK-NN
    python -B tools/check_desktop_installer.py --program build/hyperrig-desktop-NN --loader build/release-parts/loader --output build/CHECK-MM

The builder takes the official release of Electron from `build/electron-cache` (its address and
checksum are in the builder), keeps Chromium's English texts only, adds `app/desktop`, the editor's
files and the installer, and gives the program HyperRig's icon and name.

The checks run the program outside the screens with a profile of its own and `--no-pedal`, so it
never gets the port of a real pedal: its locks, the whole session of the page's check in it, and the
installer with a simulated pedal. They are no test of a pedal.

## The size of everything

By itself it fits the window: the editor is drawn for 1360 by 900 and grows with a larger window,
from 80 to 250 %. The buttons at the top, Ctrl and + or −, and Ctrl with the wheel choose another
size, which is kept; Ctrl 0 or a click on the number fits it again.

## TONE3000

Powered by [TONE3000](https://www.tone3000.com). In the libraries of captures and of cab IRs, *Browse
TONE3000* opens TONE3000's own page in a window of its own. The person signs in there with their own
account and chooses a tone; the program fetches the one file they ask for and the editor loads it as
any other. The creator, the licence and the address stay beside its slot, on this computer.

- The key in the program names HyperRig, not the person: it is TONE3000's *publishable* key, made for
  that. It is not in Git; `--tone3000-key` takes it from a file, and without it the button does not
  appear. A secret key is refused.
- Sign-in with PKCE. The program reads the address the service sends the window to at the end
  (`http://localhost:3001/callback`) and never opens it; nothing listens there.
- The tokens stay on this computer under the system's own protection, and *Sign out of TONE3000* in
  the settings deletes them. They go to TONE3000 only, not along a redirect.
- Captures of architecture A2 only, which is what the pedal plays; one file at a time, nothing
  mirrored, as TONE3000's terms ask.
- `app/desktop/tone3000.js` has the rules; the checks use a simulated TONE3000
  (`tools/simulated_tone3000.py`). No check reaches the real one.

The logos in `app/mini/tone3000` are TONE3000's, from its own page, unchanged.

## Patchstorage

*Browse Patchstorage* shows the presets that other players share on
[Patchstorage](https://patchstorage.com): a list, a search, one preset with its creator and its
licence. *Try it* plays it on the pedal without saving; *Save the file* keeps it with its creator,
licence and address inside. They also stay beside a preset that is kept, on this computer.

- The program reads the public API and nothing else: no account, no password, no cookie. It asks when
  a button is pressed, one question at a time, and fetches one file at a time; nothing is mirrored.
- A file comes from Patchstorage only, not along a redirect elsewhere, up to 4 MB, and must be a
  HyperRig preset. What the service says is shown as plain text.
- Publishing is on Patchstorage's own page, in the person's browser.
- It needs HyperRig's platform there, [number 12712](https://patchstorage.com/platform/hyperrig/):
  `--patchstorage-platform NUMBER` of the builder, which a release always passes
  (`tools/build_product_release.py`). Without it the button does not appear and nothing is asked.
  Its files end in `.json`; a preset that is exported ends in `.hyperrig.json`.
- `app/desktop/patchstorage.js` has the rules; the checks use a simulated Patchstorage
  (`tools/simulated_patchstorage.py`). No check reaches the real one.

## What it may do

- **The page is locked in.** Sandbox, no Node, no preload, no network: only the program's own files
  are answered, each checked against the manifest at the start. A changed file stops the program with
  a message. TONE3000's window is locked in the same way, gets no port and no permission, and cannot
  reach the editor. [The installer](INSTALLER.md) is a page of its own: it may use MIDI, which the
  editor may not, and has neither the editor's data nor inline scripts.
- **One port.** Of the serial ports only the pedal's (USB `4C4A:5155`, or the vendor `3654` of builds
  before the released 0.2.0) is given to the page, without a question. With two pedals connected it
  asks which.
- **Permissions.** Writing the clipboard, keeping the screen on, full screen, reading a file the
  person picks. Camera, microphone, place, MIDI, USB, HID, notifications and reading the clipboard are
  refused.
- **Files.** It saves only what the editor's page made itself, presets in a file, where the person
  chooses; it takes no other download.
- **Outside.** Only HyperRig's own pages on GitHub, TONE3000's and Patchstorage's open in the person's browser.
- **The program file.** Running it as Node, `NODE_OPTIONS` and `--inspect` are off.
- **Nothing is sent** but what *Browse TONE3000* and *Browse Patchstorage* ask for. No updater, no crash reports, no
  telemetry. The page's diagnostic lines stay in `%APPDATA%\HyperRig\logs`, one file per start, the
  last twenty.

A close with changes that are not saved asks first. Alt shows a small menu: size, full screen, the
folder with the logs.

It is not signed: Windows may ask before it starts the first time. The same sources run on macOS and
Linux, untried.
