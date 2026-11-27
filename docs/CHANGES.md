# Changes

What is new in each release of HyperRig for the TANK-MINI. To update a pedal that has an older
HyperRig, start the new program and connect the pedal: it offers **Update now**, and the presets
stay ([installation guide](../INSTALLATION.md#update)).

## 0.5.0

- **Editing over Bluetooth.** The program connects to the pedal without the cable: **Connect via
  Bluetooth**, also in the menu of the connection. A computer that was connected once with the cable
  edits at once; another one is let in by holding A and B on the pedal for three seconds and pressing
  **Unlock editing** within a minute. Level volumes and updates still need the cable
  ([manual](MANUAL.md#bluetooth)).
- The pedal ends a Bluetooth link on which nothing came for 90 seconds, and when the editor
  disconnects, so that a computer that keeps the link does not hold the pedal.
- The lights stop pulsing blue as soon as the device that came is let in.
- While it connects over Bluetooth the program says so, with each new try; a lost link is reconnected
  by itself; and the program starts the way it was connected last.
- **Let another device in** and **Forget phones and computers…** in the menu of the connection reach
  the pedal.

## 0.4.0

- **A capture for each scene.** In the amp's panel, **Capture for** says **All scenes** or **This
  scene**; preset files and backups keep it. An older HyperRig shows the place as empty.
- **Another capture, a shorter gap.** A scene or a preset that brings another capture no longer
  pauses the whole sound: the amp fades out and in again, and the cab, delays and reverbs ring on.
  A preset whose cab has an IR of its own loads with a shorter pause.
- **Two new effects:** **Ensemble** (Modulation), three slightly detuned voices as in the string
  machines of the seventies, and **Vintage Delay** (Delay), repeats that grow darker and softer.
- **Presets to start with.** After HyperRig's first install, on a pedal that has none, the editor
  puts **Clean**, **Crunch** and **Lead** in 1A to 1C, with HyperRig's own cab. They are in the
  program's folder `presets` too.
- **Browse Patchstorage** has Patchstorage's logo.
- **Bluetooth.** A phone that connects no longer makes the pedal restart, and the radio is tuned with
  the pedal's own values: before, a computer's Bluetooth could not reach the pedal at all. The
  pedal's Bluetooth address is now a valid one, so it shows once under a new name. Editing over
  Bluetooth comes in a later version; until then the editor does not offer it.

## 0.3.0

- **Cab: Low cut and High cut.** Low cut takes the boom away, High cut the fizz. They can be turned
  while you play, without a pause in the sound; each takes some 3 % of the CPU while it is on. An
  older HyperRig plays such a preset without them.
- **A cab for each scene.** A scene can have a cab of its own; preset files and backups keep it.
  When there is no memory for two cabs at once, the new one takes the place of the old one.
- **Backup and restore of the whole pedal**, in Settings: the presets, the captures and cabs with
  their slots, and the settings, in one file. A restore puts back what you tick.
- **CPU overload.** When the pedal runs out of time it eases a block or switches it off by itself;
  the editor says which, and **Turn it on** switches it on again.
- **Browse Patchstorage:** presets that other players share, heard on the pedal without saving
  them, or saved as a file.
- **The tuner** opens beside heavy presets when the memory it needs is there only in pieces; when
  there is really none, the editor says so.
- **The harmonizer** moves a power chord at the interval of its root, and follows the reference of
  the tuner.
- **The battery** is shown in the editor.
- **Level volumes** says which presets it could not measure.
- **The editor** connects again by itself when the pedal is switched off and on, and its top bar
  fits narrow windows.

## 0.2.1

The first release.
