; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; calibration_commands: 1 function, 0x0200e07a..0x0200e146

; calibration_commands_global_save: 0x0200e07a..0x0200e146, module calibration-commands (global_save)
.type calibration_commands_global_save,@function
calibration_commands_global_save:
    [--sp] = {rets, r9-r4}
    sp += -144
    r5 = L020359eb  ; "leds"
    r1 = r5 + 310
    call L02028308  ; @call.xl
    r4 = 0
    if (r0 != 0) goto L0200e128
    r0 = 1
    r4 = 1
    call settings_store_global_save
    if (r0 != 0) goto L0200e11a
; HyperRig MINI, product option: the record of the lights with HyperRig's own settings behind them (mini/product/midi.c).
.if MINI_PRODUCT
    call hyperrig_settings_keep  ; @call.xl
.else
    r6 = sp + 0
    r0 = r6
    call mode_and_settings_block_export
    r1 = 32
    r0 = r6
    call capture_metadata_crc
    r9 = L01c26890
    r1 = [r9+780]
    r8 = r0
    r0 = 0
    if (r8 == r1) goto L0200e118
    r0 = 1481067348
    r1 = 32
    d[sp+32] = r1_r0
    [sp+40] = r8  ; @st.w.sp.l
    r0 = 0
    r7 = sp + 32
    r0 = r7  #
    [sp+44] = r0
    r1 = r5
    call record_helpers_copy_name
    r6 = sp + 72
    r2 = 40
    r1_r0 = r7_r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6 + 40
    r1 = sp + 0
    rep 32 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r6 = 776
    r0 = b[r9+r6] (u)
    if (r0 != 0) goto L0200e108
    call mode_and_settings_record_scan
    r0 = 1
    b[r9+r6] = r0
L0200e108:
    r0 = sp + 72
    r1 = 72
    call settings_store_record_store
    if (r0 != 0) goto L0200e118
    [r9+780] = r8
    r0 = 0
.endif
L0200e118:
    if (r0 == 0) goto L0200e12e
L0200e11a:
    call capture_command_status_text
    r1 = r0
    r0 = r5 + 1859
    call link_and_print_print
L0200e128:
    r0 = r4
    sp += 144
    {pc, r9-r4} = [sp++]
L0200e12e:
    r0 = L01c1f180
    r1 = [r0+204]
    r0 = r5 + 3272
    r1 += 1  ; @add.ri.u5
    r2 = 30
    call link_and_print_print
    goto L0200e128
