# Where everything comes from

HyperRig is not a release of UltraRig, is not affiliated with M-VAVE, and does not claim to have written
UltraRig's code. What is in a release, whose it is and under which licence is in
[the notice](../release/NOTICE.md); this is the origin of the firmware's source.

| Source | What of it is used |
|---|---|
| [UltraRig](https://github.com/manuaguirre9/ultrarig), G alpha11 v2/M5.71 | The application, changed; the editor's page and its capture converter, changed |
| [pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa) | Assembler, linker, instruction tables and the simulator of the checks; MIT-0, its tables and documents CC0 |
| [m-bootloader](https://github.com/jvitkauskas/m-bootloader) | The USB part of the loader, the form of a stored loader, facts about the chip; MIT |
| [AC79 SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK), a mirror of JieLi's | Reference for the SDK functions of the application, named below; Apache License 2.0 |
| [JieLi's toolchain](https://jl-update.oss-cn-shenzhen.aliyuncs.com/jieli-linux-toolchains-20260730.1.tar.xz) | The compiler and a second linker, used as tools |

The code of UltraRig keeps PolyForm Noncommercial 1.0.0 and its Required Notice
([LICENSE.md](../third_party/ultrarig/LICENSE.md), [NOTICE.md](../third_party/ultrarig/NOTICE.md)). The
names of its functions and files are HyperRig's, not its author's. HyperRig's own code
(`firmware/ultrarig/mini/product` but for the descriptors in `midi_usb.h`, `firmware/mini_stage` but for
`usb_midi`, `app`, `tools`, `tests`) is
under the same licence ([LICENSE.md](../LICENSE.md)).

No firmware, software, capture or impulse response of M-VAVE or Sinco is in HyperRig. Facts about the
TANK-MINI (pins, converter channels, the update service, the places in the flash) are about the
hardware only.

## SDK and library code

The UltraRig image links code of the JieLi AC79 SDK and of the toolchain libraries into the application.
Some of its functions are such code: they are not UltraRig's and do not carry its licence. The
comment above a function in the source names the module of the table below.

| Module | SDK or library bodies | Origin | License |
|---|---|---|---|
| Audio link start | `link_start` | AC79 SDK `cpu.a`, `iis.c` (`iis_open`) | Apache License 2.0 |
| Mode and settings | `first_callbacks`, `second_callbacks`, `link_rate`, `link_buffers` | AC79 SDK `cpu.a`, `iis.c` | Apache License 2.0 |
| Storage control | 36 of 45 bodies (four more undecided) | AC79 SDK `cpu.a`, `vm_sfc.c` | Apache License 2.0 |
| Storage platform | 8 of 9 bodies | AC79 SDK `cpu.a`, `vm_sfc.c`; `system.a`, `hwi.c` | Apache License 2.0 |
| Diagnostic records and fatal handling | the six P33 bodies | AC79 SDK `cpu.a`, `p33.c` | Apache License 2.0 |
| Storage coordination | `irq_enter`, `irq_leave` | AC79 SDK symbols `__local_irq_disable`, `__local_irq_enable` | Apache License 2.0 |
| Vendor heap access | `lock_enter`, `lock_leave` | AC79 SDK `sys_local_irq_disable`, `sys_local_irq_enable` | Apache License 2.0 |
| State queries | `parse_decimal`, `append_byte` | AC79 SDK `system.a`, `printf-stdarg.c` (`skip_atoi`, `printchar`) | Apache License 2.0 |
| Capture journal | `compare` | SDK runtime `pi32v2-lib/libc.a` (newlib), `memcmp` | newlib: Red Hat license of `COPYING.NEWLIB` |
| Capture command | `prefix`, `decimal_core`, `decimal` | SDK runtime `pi32v2-lib/libc.a` (newlib), `strncmp`, `_strtol_r`, `strtol` | newlib: Red Hat license (`strncmp`); University of California BSD, 1990 (`strtol`) |
| Parameter support | `memmove`, `signed_divide`, `unsigned_divide` | SDK runtime `pi32v2-lib/libc.a`, `memcpy`; `libcompiler_rt.a`, `__divdi3`, `__udivmoddi4` | not stated (`memcpy`, assembly); NCSA or MIT (compiler-rt) |
| Effect enable | `memset` | SDK runtime `pi32v2-lib/libc.a`, `memset` | not stated (assembly) |
| Effect model construction | `unsigned_quotient` | SDK runtime `pi32v2-lib/libcompiler_rt.a`, `__udivdi3` | NCSA or MIT |
| Phase 3 P1 group | `fopen`, `app_version_check`, `ota_idle_query` | AC79 SDK V1.2.13 `fs.a` (`vfs.c`), `apps/common/system/version.c`, `apps/common/update/update.c` | Apache License 2.0 |
| Phase 3 P2 group | 5 of 7 bodies (the other two are UltraRig code) | AC79 SDK V1.2.13 `wl_rf_common.a` (`wf_phy_mac_init.c`, `wf_rf_cal.c`, `wf_cfr_init.c`), with `cpu.a` `delay.c` (`delay_us`) inlined | Apache License 2.0 |
| Phase 3 P3 group | 21 bodies; the start-up `main` holds two UltraRig fragments | AC79 SDK V1.2.13 `system.a` (`app_core.c`, `task.c`), `cpu.a` (`wdt.c`, `timer.c`, `usb.c`, `clock.c`, `crc16.c`, `power_hw.c`), `cpu/wl82/debug.c`, `cpu/wl82/setup.c`, `apps/common/system/init.c`, `apps/common/system/system_reset_reason.c`, `apps/common/update/update.c` | Apache License 2.0 |
| Phase 3 P4 group | 16 of 17 bodies (the other is an UltraRig function of the product's copy of `cdc.c`); `app_task_handler` holds the product's `app_main` and `cdc_setup` its edit of `SET_CONTROL_LINE_STATE`, both UltraRig | AC79 SDK V1.2.13 `apps/common/system/init.c`, `cpu.a` (`usb.c`, `usb_setup.c`, `power_hw.c`), `system.a` (`app_core.c`), `event.a` (`event.c`), `apps/common/usb/device/` (`cdc.c`, `user_setup.c`), `apps/common/c++/cpp_run_init.c` | Apache License 2.0 |
| Phase 3 P5 group | 23 bodies | AC79 SDK V1.2.13 `event.a` (`event.c`), `cpu.a` (`gpio.c`), `system.a` (`printf-stdarg.c`, `fcvt.c`), `apps/common/usb/device/` (`descriptor.c`, `user_setup.c`, `usb_device.c`, `cdc.c`) | Apache License 2.0 |
| Phase 3 P6 group | 18 bodies | AC79 SDK V1.2.13 `system.a` (`timer.c`), `cpu.a` (`timer.c`, `power_hw.c`, `vm_sfc.c`, `gpio.c`, `usb.c`, `otg.c`), `event.a` (`event.c`, `device_event.c`), `cfg_tool.a` (`cfg_bin.c`), `fs.a` (`vfs.c`), `apps/common/usb/usb_config.c`, `apps/common/usb/device/usb_device.c` | Apache License 2.0 |
| Phase 3 P7 group | 19 bodies | AC79 SDK V1.2.13 `cpu.a` (`vm_sfc.c`, `clock.c`, `power_hw.c`), `apps/common/usb/device/msd_upgrade.c` | Apache License 2.0 |
| Phase 3 P8 group | 26 bodies | AC79 SDK V1.2.13 `fs.a` (`vfs.c`, `sdfile_new.c`), `cfg_tool.a` (`cfg_bin.c`, `cfg_btif.c`, `vm.c`), `cpu.a` (`vm_sfc.c`) | Apache License 2.0 |
| Phase 3 P9 group | 24 bodies | AC79 SDK V1.2.13 `cfg_tool.a` (`vm.c`), `fs.a` (`vfs.c`, `sdfile.c`) | Apache License 2.0 |
| Phase 3 P10 group | 29 bodies | AC79 SDK V1.2.13 `fs.a` (`sdfile_new.c`, `vfs.c`, `sdfile_ext.c`), `cpu.a` (`device_api.c`), `system.a` (`timer.c`, `lbuf.c`), `btctrler.a` (list helpers and a start-up sequence whose name is not established) | Apache License 2.0 |
| Phase 3 P11 group | 21 bodies | AC79 SDK V1.2.13 `btctrler.a` (`lbuf.c`, `hw_dma.c`, `btcontroller_util.c`, `btcontroller_heap.c`, `thread.c`), `cpu.a` (`power_hw.c`, `crc16.c`), copies of the inlines of `include_lib/system/generic/atomic.h` and `list.h` | Apache License 2.0 |
| Phase 3 P12 group | 28 bodies | AC79 SDK V1.2.13 `system.a` (`circular_buf.c`), `event.a` (`event.c`), `btctrler.a` (`lmp_rxtx.c` and operation stubs), `btstack.a` (`bip.c`, `ancs_client.c`, `att_db.c`); SDK runtime `pi32v2-lib/libc.a` (newlib), `atoi.c` | Apache License 2.0; the twelve `btstack.a` bodies also the BlueKitchen BTstack license if they derive from BTstack ([LICENSE](../third_party/btstack/LICENSE)); `atoi` and `_atoi_r`: newlib, Red Hat license of `COPYING.NEWLIB` |
| Phase 3 P13 group | 39 bodies | AC79 SDK V1.2.13 `system.a` (`printf-stdarg.c`, `hwi.c`, `timer.c`), `cpu.a` (`crc16.c`, `gpio.c`, `usb.c`, `timer.c`), `cpu/wl82/iic.c`, `cpu/wl82/key/adc_api.c` of another revision, `fs.a` (`vfs.c`), `apps/common/usb/device/descriptor.c`, `apps/common/c++/cxx_runtime.cpp` | Apache License 2.0 |
| Phase 3 P14 group | 7 bodies | AC79 SDK V1.2.13 `cpu.a` (`startup.S`), `system.a` (`hwi.c`) | Apache License 2.0 |
| Phase 3 P15 group | 2 bodies | AC79 SDK V1.2.13 `system.a` (`printf-stdarg.c`), `event.a` (`bt_event.c`) | Apache License 2.0 |

Library sources and their licences:

- `upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a` (SHA-256
  `00cea21d3c8d99487821f2c2b203f2c5a04b2cc8421bc05e9b875a0d70e42c62`) and
  `cpu/wl82/liba/system.a` of the same mirror commit
  (SHA-256 `b561a1a216097509f62a58c931227b2897826eca75309737cf4b9bace98fb5a5`,
  1,222,474 bytes) are
  distributed under the repository's Apache License 2.0
  ([LICENSE](../third_party/ac79-sdk/LICENSE), SHA-256
  `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`). No
  member states a license of its own.
- The JieLi toolchain archive (SHA-256
  `a1545cddbc451a06bac43eb5cd96d831470c42a97c5c0b1f98879a20fc7647bd`) ships no
  license file. Its `pi32v2/lib/libc.a` is newlib, as the source paths in its
  members show: `memcmp.c` and `strncmp.c` carry no notice of their own, so
  section (1) of newlib's `COPYING.NEWLIB`, the Red Hat license, applies;
  `strtol.c` carries the 1990 University of California BSD license; `memcpy`
  and `memset` are assembly members without a source path and no license is
  stated for them. Its `libcompiler-rt.a` is compiler-rt of LLVM, whose
  `LICENSE.TXT` of the 4.0 release branch dual-licenses it under the University
  of Illinois/NCSA Open Source License and the MIT license; the toolchain's clang
  is version 4.0.
- The SDK symbols `__local_irq_disable`, `__local_irq_enable`,
  `sys_local_irq_disable` and `sys_local_irq_enable` are declared in the SDK's
  `include_lib/driver/cpu/wl82/asm/cpu.h` and called by members of `cpu.a` and
  `system.a`; they are defined in the SDK's application source
  `apps/common/system/init.c`, whose compiled functions equal the image.
- The image was built from the JieLi release AC79NN_SDK_V1.2.13_2026-04-20:
  every library version tag in its version list at `0x0203bec0` equals those of
  that release. Its archives and C sources come from commit
  `64afb30b805af5f5d3c2e6471e970c3fd0ba40ad` of the mirror
  [msr002/fw-AC79_AIoT_SDK](https://github.com/msr002/fw-AC79_AIoT_SDK) (the
  same tag maps to the same commit in two other mirrors), under the same Apache
  License 2.0 file. The release links its own runtime libraries from
  `include_lib/newlib/pi32v2-lib/` (`libc.a`, `libm.a`, `libcompiler_rt.a`); the
  library bodies named above equal both these and the toolchain's copies
  byte for byte, and the SDK copies are the ones the release links. The release
  also contains FreeRTOS V9.0.0 (GNU GPL v2 with the FreeRTOS exception) and micro-ecc (BSD 2-Clause); the source
  files named in the table above are none of theirs.
- `btstack.a` of the release carries the SDK's Apache License 2.0 and no notice
  of its own. The file and function names of the members whose bodies are in the
  phase 3 P12 group (`att_db.c`, `ancs_client.c`, `bip.c`) match those of
  BlueKitchen BTstack (Copyright (C) 2009 BlueKitchen GmbH), so these bodies
  appear to derive from it. If they do, BTstack's license applies as well; it is
  kept verbatim in
  [third_party/btstack/LICENSE](../third_party/btstack/LICENSE), the `LICENSE`
  of [bluekitchen/btstack](https://github.com/bluekitchen/btstack) at commit
  `9edb5d82ea6ec4466a393415d65030929330acdf` (SHA-256
  `10aa5f952979a9fa2f58bf63c1390c9795b41f8eca405ab975ab926e4d14fc5a`; BSD-style,
  redistribution must retain the notice, use solely for personal, non-commercial
  purposes).
- `sdk/lib/libfm1_engine.a` of
  [m-vave/fm1_open](https://github.com/m-vave/fm1_open) at `4c7496da`, a
  symbol-named build of the same release, serves only as a reference for
  functions whose names a V1.2.13 SDK archive or source defines, as the
  JieLi SDK material inside it keeps Apache 2.0 while its other parts are
  licensed only for M-VAVE FM1 firmware. It is not distributed.
