# The code the MINI image appends

These are copies of the sources in `firmware/mini/` that build the code the
HyperRig MINI image places after the application:

- the audio shim v2: `audio_port_v2/`, `audio_port/g_bindings.c` and
  `codec/`;
- the any-one-footswitch entry guard: `entry_recovery_v2/prefix.S`,
  `entry_recovery_one/check.S` and `entry_recovery/reset.S`.

`tools/build_hyperrig_mini_image.py` compiles them with JieLi's toolchain. It
links them in the same link as the application built from `firmware/ultrarig`.
[`../append.ld`](../append.ld) places them after the application, where the
two linker scripts of the original builds placed them: `audio_port/audio_port.ld`
and `entry_recovery_v2/append.ld` in `firmware/mini/`.

## How the copies differ

The originals in `firmware/mini/` stay as tested. They call functions of the
application and use its data at fixed addresses. When a change to the
application source moves that code, fixed addresses would point at the wrong
place. In these copies the addresses are macros, such as
`HYPERRIG_G_GPIO_DIRECTION_OUTPUT`. The guard's return to the start-up code,
`hyperrig_mini_g_startup_resume`, is a symbol that the build defines for the
link.

`../bindings.json` lists each of them as a symbol of the application source
plus an offset. The build reads the address from the linked application and
gives it to the compiler (`-D`) or to the linker (`--defsym`). With the
unchanged source, every value equals the original one, and the area is the
MINI v4 area byte for byte.

These are the only changes:

| File | Change |
| --- | --- |
| `audio_port/g_bindings.c` | nine addresses are macros |
| `audio_port_v2/pre_pc5.c` | three addresses are macros (target branch only) |
| `audio_port_v2/pc5_hd.S` | the PORTC lock and the IRQ enter and leave functions are macros |
| `entry_recovery_v2/prefix.S` | the two stack tops are macros |

The other files are unchanged copies. The two linker scripts are not copied,
because `../append.ld` does their work in the single link. The guard script
also defined `hyperrig_mini_g_startup_resume = 0x02000196`, which the build
now takes from the application.

## Changing this code

- To use another function or data item of the application, add it to
  `../bindings.json` and use its macro. Do not write an application address
  as a number. The build warns, and lists in
  `unbound_application_constants`, any `li.u32` load in the appended code that
  points into the application at no binding.
- The build reports every binding with its address and the original one. It
  also lists the bindings that moved in `bindings_moved`.
- A changed shim no longer gives the MINI v4 bytes. Like any build from
  source, it is installed only through the installer and its review.
