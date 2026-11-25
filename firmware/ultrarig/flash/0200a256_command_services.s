; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; command_services: 5 functions, 0x0200a256..0x0200a47e

; command_services_effect_snapshot: 0x0200a256..0x0200a312, module command-services (effect_snapshot)
; HyperRig MINI, product option: the records of eight scenes.
.type command_services_effect_snapshot,@function
command_services_effect_snapshot:
    [--sp] = {rets, r11-r4}
    r9 = r0 * 0x104
.if MINI_PRODUCT
    r8 = L01c26890
    r1 = hyperrig_scene_base  ; @li.u32
    r1 = r1 - r8
    r9 = r9 + r1
.else
    r8 = L01c26890
.endif
    r5 = r9 + r8
    r0 = 1
    r1 = 11936
    r11 = r5
    b[++r11=r1] = r0
    r4 = 0
    h[r11+2] = r4
    call slot_commands_requested
    b[r11+1] = r0
    r0 = 1038
    r0 = [r8+r0<<2]
    b[r11+4] = r0
    r0 = 1039
    r0 = [r8+r0<<2]
    b[r11+5] = r0
    r6 = r11 + 246
    goto L0200a2ac
L0200a29e:
    r0 = r4
    call audio_measurement_control_value  ; @call.xl
    h[r6+r4<<1] = r0
    r4 += 1  ; @add.ri.u5
L0200a2ac:
    if (r4 != 6) goto L0200a29e
    r0 = 12194
    r1 = 1
    b[r5+r0] = r1
    r0 = 11958
    r7 = r5 + r0
    r4 = 0
    r10 = 11942
    goto L0200a30c
L0200a2c8:
    r0 = r4
    call preset_application_effect_type  ; @call.xl
    if (r0 == 0) goto L0200a308
    r0 = h[r11+2] (u)
    r0 = r0 | (1 << r4)
    h[r11+2] = r0
    r0 = r9 + r4
    r5 = r0 + r8
    r0 = r4
    call preset_application_effect_enabled  ; @call.xl
    b[r5+r10] = r0
    r5 = 0
    r6 = r7
    goto L0200a304
L0200a2f8:
    r1_r0 = r5_r4
    call preset_application_parameter  ; @call.xl
    h[r6++=2] = r0
    r5 += 1  ; @add.ri.u5
L0200a304:
    if (r5 != 7) goto L0200a2f8
L0200a308:
    r7 += 14  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0200a30c:
    if (r4 != 16) goto L0200a2c8
    {pc, r11-r4} = [sp++]

; command_services_save_slot: 0x0200a312..0x0200a37e, module command-services (save_slot)
; HyperRig MINI, product option: a preset may be packed (mini/product/scenes.c).
.type command_services_save_slot,@function
command_services_save_slot:
    [--sp] = {rets, r6-r4}
    sp += -64
    r4 = r0
    call preset_storage_preparation_prepare
    r5 = -1
    if (r4 > 31) goto L0200a378
    r0 = r4
    call preset_storage_address
    r1 = 1363626836
    r3 = sp + 24
.if MINI_PRODUCT
    r2 = 1880
.else
    r2 = 1490
.endif
    call preset_application_header
    if (r0 == 0) goto L0200a378
    r5 = sp + 24
    r6 = sp + 0
    r0 = r5 + 16
    r1 = r6
    rep 23 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 0
    b[sp+23] = r0
    r0 = r4
    call status_snapshot_status_snapshot
    r0 = r5
    call command_services_record_header
    r0 = r5
    r1 = r6
    call record_helpers_copy_name
    r1_r0 = r5_r4  #
    r3 = [sp+28]
    r2 = L01c24790
    call preset_storage_preparation_preset_write
    r5 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
L0200a378:
    r0 = r5
    sp += 64
    {pc, r6-r4} = [sp++]

; command_services_save_names: 0x0200a37e..0x0200a3f8, module command-services (save_names)
; HyperRig MINI, product option: the names of eight scenes.
.type command_services_save_names,@function
command_services_save_names:
    [--sp] = {rets, r7-r4}
    sp += -64
    r4 = r0
    r1 = sp + 24
    call preset_preflight_preflight
    r2 = r0
    if (r2 != 0) goto L0200a3f2
    r5 = L01c24790
    r0 = b[r5+0] (u)
    r2 = -5
    if (r0 != 5) goto L0200a3f2
.if MINI_PRODUCT
    r0 = 0
    r1 = hyperrig_name_base  ; @li.u32
.else
    r0 = 0
    r1 = L01c26890
.endif
    goto L0200a3ba
L0200a3a6:
    r2 = r0 + r5
    r2 = r2 + 1360
    r3 = r0 + r1
    r3 = r3 + 3248
    rep 16 {
    r6 = b[r3++=1] (u)
    b[r2++=1] = r6
    }
    r0 += 16  ; @add.ri.u5
L0200a3ba:
.if MINI_PRODUCT
    if (r0 != 64) goto L0200a3a6
    call hyperrig_names_more  ; @call.xl
.else
    if (r0 != 64) goto L0200a3a6
.endif
    r6 = sp + 24
    r7 = sp + 0
    r0 = r6 + 16
    r1 = r7
    rep 23 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 0
    b[sp+23] = r0
    r0 = r6
    call command_services_record_header
    r1_r0 = r7_r6
    call record_helpers_copy_name
    r0 = r4  #
    r3 = [sp+28]
    r1 = r6
    r2 = r5
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
L0200a3f2:
    r0 = r2
    sp += 64
    {pc, r7-r4} = [sp++]

; command_services_save_word: 0x0200a3f8..0x0200a45c, module command-services (save_word)
; HyperRig MINI, product option: output gains in place of the colour (mini/product/loudness.c).
.type command_services_save_word,@function
command_services_save_word:
    [--sp] = {rets, r7-r4}
    sp += -64
    r6 = r1
    r4 = r0
    r1 = sp + 24
    call preset_preflight_preflight
    r2 = r0
    if (r2 != 0) goto L0200a456
    r5 = L01c24790
    r0 = b[r5+0] (u)
    r2 = -5
    if (r0 != 5) goto L0200a456
.if MINI_PRODUCT
    call hyperrig_gains  ; @call.xl
    if (r0 != 0) goto Lhr_gains
.endif
    r0 = h[r5+10] (u)
    r2 = 0
    if (r0 == r6) goto L0200a456
    h[r5+10] = r6
.if MINI_PRODUCT
Lhr_gains:
.endif
    r6 = sp + 24
    r7 = sp + 0
    r0 = r6 + 16
    r1 = r7
    rep 23 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = 0
    b[sp+23] = r0
    r0 = r6
    call command_services_record_header
    r1_r0 = r7_r6
    call record_helpers_copy_name
    r0 = r4  #
    r3 = [sp+28]
    r1 = r6
    r2 = r5
    call preset_storage_preparation_preset_write
    r2 = r0
    r0 = r4
    call preset_storage_preparation_invalidate
L0200a456:
    r0 = r2
    sp += 64
    {pc, r7-r4} = [sp++]

; command_services_colour_bytes: 0x0200a45c..0x0200a47e, module command-services (colour_bytes)
.type command_services_colour_bytes,@function
command_services_colour_bytes:
    r2 = r0 >> 11
    r3 = r0 >> 13
    r3 <= insert(r2, p:3, l:5)
    r2 = r0 >> 5
    r3 = uextra(r0, p:9, l:2)  #
    b[r1+0] = r3
    r3 <= insert(r2, p:2, l:11)
    r2 = uextra(r0, p:2, l:3)  #
    b[r1+1] = r3
    r2 <= insert(r0, p:3, l:16)
    b[r1+2] = r2
    rts
