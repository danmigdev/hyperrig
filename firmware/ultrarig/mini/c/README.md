# New C code for the MINI image

Every `.c` and `.S` file in this directory is part of the MINI image that
`tools/build_hyperrig_mini_image.py` builds. Each file is compiled with
JieLi's clang (`-target pi32v2 -mcpu=r3 -std=c11 -Os -ffreestanding
-fno-builtin -Wall -Wextra -Werror`, with this directory on the include path).
The result goes into the same link as the application. With no source file
here, the build gives the MINI v4 area unchanged.

## Where the code goes

`mini/append.ld` and `app.ld` place each kind of section:

| Section | Placed | Runs from |
| --- | --- | --- |
| `.text`, `.rodata` | after the guard, at the end of the appended code | flash |
| `.data` | at the end of the RAM image, which the start-up code copies | RAM |
| `.bss`, `COMMON` | at the end of the bss, which the start-up code clears | RAM |
| `.ram_text` | at the end of the RAM image | RAM |

Code that must not run from flash, for example while the flash is being
written, goes in `.ram_text`:
`__attribute__((section(".ram_text"))) void f(void) { ... }`.

`.data`, `.bss` and `.ram_text` make the RAM image or the bss longer. The bss
and the heap start then move up, and the heap gets smaller. `heap_bytes` in the
build manifest shows the new size.

## Calling across

- **Application to C.** A function defined here (not `static`) can be called
  from the assembly by its name, for example `call my_function` in a change
  under `.if TARGET_MINI`.
- **C to application.** C code calls an application function, or uses
  application data, by its name in the source:
  `extern void phase3_p5_gpio_set_die(unsigned pin, unsigned value);`. Most
  labels in the source are local to their assembly unit. The build looks up
  each name the C code uses and is missing, in the first link of the
  application, and gives it to the final link. The manifest lists them under
  `imports`. A name found nowhere fails the link as an undefined reference.

Name C symbols so they cannot collide with the source's names, for example
with a `hyperrig_` prefix.

## Checks

The build links everything with the upstream linker and again with JieLi's
`ld`. The two must give the same bytes. Any allocated section that neither
linker script places stops the build, because an orphan section could land
anywhere. The manifest reports:
- the size and SHA-256 of the C part (`appended.c`);
- the files (`c_sources`);
- the room left in the partition;
- the sectors that differ from MINI v4.

None of this tests the code on hardware. A build with C code is installed only
through the installer and its review.
