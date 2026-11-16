# Experimental USB_KEY with Raspberry Pi 3

The Raspberry Pi 3 can generate the USB_KEY protocol using two GPIOs and
dedicated wiring. The [usbkey.c](../tools/usbkey_rpi3/usbkey.c) source
builds and has been tested on the development computer with simulated GPIO.
**This is not yet a recovery procedure tested on the Raspberry Pi 3 or
TANK MINI.** The current result does not clear the gate for firmware installation.

USB_KEY is an electrical sequence on the USB lines, used to invoke the
bootloader in the chip's ROM. It is neither a memory stick nor a
normal USB command. Connecting a USB cable between the PC and Raspberry
does not generate this sequence: it requires the Pi's GPIO header and a
breakout exposing D+, D−, and ground on the cable leading to the MINI.

The [original protocol description](https://kagaimiq.github.io/jielie/isp/usb/usb-key.html)
defines the word `0x16EF`, sent most significant bit first, with D+
as the clock and D− as data sampled on the rising edge. The response
pulls both lines low for approximately 1–2 ms. Timing tolerance
is not quantified: approximately 50 kHz is a reference, not a guarantee.

The [pinned m-bootloader SPEC, §4.3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#43-recovery-independent-of-a-valid-boot-image)
reports a working Pico implementation on the SMK-37 Pro: 10 µs half-periods,
a 150 µs pause, external 2.2 kΩ pull-ups to 3.3 V, and independent device
power. This evidence does not cover the MINI. The presence of WL82 ROM
in the MINI makes adaptation plausible; reception of the signal
during startup still requires physical verification.

## Candidate wiring

The program's **BCM** numbers and the header's **physical** pin numbers
are distinct. Their correspondence is verified in the
[official Raspberry Pi pinout](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pin-layout).
Before connecting anything, identify pin 1 on the board and check
the breakout labels and cable continuity; wire colors alone
are not sufficient evidence.

| Raspberry Pi 3 | Physical pin | Connection to USB 2 breakout |
|---|---:|---|
| BCM17 | 11 | D+, clock |
| BCM27 | 13 | D−, data |
| GND | 6 | USB signal GND |
| 3.3 V | 1 | One 2.2 kΩ resistor to D+ and a second 2.2 kΩ resistor to D− |
| 5 V | 2 and 4 | No connection |
| Breakout VBUS | — | Disconnected |

```text
Pi physical 1 (3.3 V) ── 2.2 kΩ ──┬── USB D+
Pi physical 11 (BCM17) ────────────┘

Pi physical 1 (3.3 V) ── 2.2 kΩ ──┬── USB D−
Pi physical 13 (BCM27) ────────────┘

Pi physical 6 (GND) ───────────────── USB GND
                                      USB VBUS: disconnected
```

The Pi uses its own power supply; the MINI uses its own battery. The PC
must not be connected to these lines at the same time. GPIO signals are
3.3 V; do not apply 5 V to them. The two resistors are separate:
do not connect the 3.3 V pin directly to D+ or D−. GPIO characteristics
are documented in the
[official Raspberry Pi white paper](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-006553-WP-2-A%20history%20of%20GPIO%20usage%20on%20Raspberry%20Pi%20devices,%20and%20current%20best%20practices.pdf).

The MINI USB-C connector path, CC/VBUS detection, and startup listening
window have not been measured with this circuit. No additional CC pin
connections or improvised VBUS supply are proposed to work around
a possible detection failure.

## Implementation and behavior

The C program directly uses the
[Linux GPIO character device API v2](https://www.kernel.org/doc/html/latest/userspace-api/gpio/chardev.html),
available since kernel 5.10, and requires no external GPIO library.
Real operation checks the Pi 3 model, the `pinctrl-bcm2835` controller,
offsets 17/27, and that the lines are free. A different controller name
or unsupported configuration causes an error; no alternative access
through `/dev/mem` or sysfs is attempted.

The kernel request is always `OUTPUT | OPEN_DRAIN | BIAS_DISABLED`,
without ACTIVE_LOW inversion. Zero means drive to ground; one
means release the line. Push-pull HIGH output is not requested.
Linux may implement release by switching the GPIO to input; the
[driver contract](https://docs.kernel.org/driver-api/gpio/driver.html#gpio-electrical-configuration)
notes that switching may introduce glitches. The code does not replace
electrical measurement with an oscilloscope or logic analyzer.

Response detection applies this conservative policy, chosen for
the experiment and distinct from the ROM specification:

1. Both released lines must have been read HIGH.
2. At least one complete frame must have been transmitted.
3. Both must become LOW while the program has released them.
4. The LOW must end: observed duration between 0.5 and 3 ms.
5. A gap exceeding 100 µs between samples of a possible response
   makes the result ambiguous.

An unpowered device holding the lines low does not start transmission
and is not declared a response. A line stuck LOW,
an excessively short pulse, or an I/O error does not produce success.
The default requested duration is 20 seconds, limited by the CLI to 60 seconds.
These are software limits: a kernel or scheduling stall can
also delay deadline checking and line release.

The program handles SIGINT/SIGTERM and, when it can perform cleanup,
releases both lines, configures them as inputs, and closes the request.
SIGKILL, Pi power loss, and kernel errors do not guarantee this cleanup.
The log records whether release and reconfiguration succeeded.

## Building and testing without GPIO

To reproduce the checks on the development computer, from the
repository root:

```powershell
python -X utf8 tools/usbkey_rpi3/verify.py
```

The verifier uses the already available Linux compiler, through Ubuntu/WSL
on Windows. It installs no packages and never invokes `--execute`. Tests
cover the 16-bit order, minimum duration, a simulated powered-off pedal,
no response, abnormal pulses, scheduler delay, I/O errors at each step,
deadlines, and interruption. ASan/UBSan and compilation with
`-Wall -Wextra -Werror` are included. The default simulation and refusal
to overwrite an existing log are also verified.

The [mini-usbkey-rpi3.json](../research/mini-usbkey-rpi3.json) report contains
hashes, results, and compiler architecture. The binary produced on
WSL x86_64 **is not an ARM executable for the Raspberry Pi**.

On the Pi, with a C compiler and Linux headers already available, the
local build command from the root of the repository copy is:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror tools/usbkey_rpi3/usbkey.c -o usbkey-rpi3
./usbkey-rpi3 --log simulazione.json
./usbkey-rpi3 --timing-only --timeout-ms 1000 --log timing-pi.json
```

Both runs use simulated lines. `--timing-only` repeats frames until
the deadline and intentionally exits with code 2 (`timeout`).
This measures software waiting and operating-system jitter without measuring
GPIO ioctls or electrical edges. The pedal does not need to be connected.

## Future physical experiment, before replacing the firmware

The following command is documented for future manual execution with
checked wiring; it was not executed during this work:

```sh
sudo ./usbkey-rpi3 --execute --chip /dev/gpiochip0 --timeout-ms 20000 --log usbkey-prova-01.json
```

The filename must be new. An error opening the log stops the program
before the GPIO request. The Pi must already be running; the GPIO
connection must not remain attached while the Pi itself powers on or
reboots, because this program does not control pin configuration during
Pi boot. Reception is attempted by switching on the MINI while the program
is running, initially keeping the original firmware intact.

`ack_candidate` means only that the reads satisfy the stated policy.
After release, physically disconnect the GPIO circuit, including its
pull-ups, and connect the MINI to the PC while keeping it powered.
The confirmation step is independent USB identification:
`4C4A:8057`, SCSI `WL82` / `UBOOT1.00`, through a read-only check.
No firmware write is needed to test this entry method.

The tool does not generate a subsequent 1 ms SOF reference: the original
notes state that some ROMs measure the clock after the response using the
USB bus. Transfer to the PC, its latency, and MINI enumeration therefore
remain parts of the trial even when a valid pulse is observed.
If the result is a timeout or ambiguous, do not replace the application
in reliance on this recovery route.

The log retains `CLOCK_MONOTONIC` timestamps before and after each operation,
the maximum waiting delay, the frame count, and the last 4096 events.
The omitted-event count remains explicit. Waits start after the preceding
operation completes: the program does not try to catch up after a delay by
shortening subsequent pulses. Consequently, the actual frequency may be
below 50 kHz. Process priority, interrupts, clocks, and device memory
are not changed.
