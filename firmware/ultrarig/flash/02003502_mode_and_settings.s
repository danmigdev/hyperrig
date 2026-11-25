; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mode_and_settings: 9 functions, 0x02003502..0x02003898

; mode_and_settings_global_check: 0x02003502..0x0200356a, module mode-and-settings (global_check)
.type mode_and_settings_global_check,@function
mode_and_settings_global_check:
    [--sp] = {rets, r6-r4}
    r3 = r1  #
    r2 = b[r0+3] (u)
    r4 = b[r0+2] (u)
    r4 <= insert(r2, p:8, l:8)  #
    r5 = b[r0+1] (u)
    r6 = b[r0+0] (u)
    r6 <= insert(r5, p:8, l:8)
    r6 <= insert(r4, p:16, l:16)
    r1 = 1195854676
    r2 = 0
    if (r6 != r1) goto L02003566
    r4 = b[r0+7] (u)
    r5 = b[r0+6] (u)
    r5 <= insert(r4, p:8, l:8)  #
    r6 = b[r0+5] (u)
    r1 = b[r0+4] (u)
    r1 <= insert(r6, p:8, l:8)
    r1 <= insert(r5, p:16, l:16)
    if (r1 > r3) goto L02003566
    r3 = r1 + 40
    if (r3 > 128) goto L02003566
    r2 = b[r0+11] (u)
    r3 = b[r0+10] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r4 = b[r0+9] (u)
    r5 = b[r0+8] (u)
    r5 <= insert(r4, p:8, l:8)
    r5 <= insert(r3, p:16, l:16)
    r0 += 40
    call capture_metadata_crc
    r2 = 1
    if (r0 != r5) {
    r2 = 0
    }
L02003566:
    r0 = r2
    {pc, r6-r4} = [sp++]

; mode_and_settings_page_check: 0x0200356a..0x020035cc, module mode-and-settings (page_check)
.type mode_and_settings_page_check,@function
mode_and_settings_page_check:
    [--sp] = {rets, r5, r4}
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r4 = b[r0+0] (u)
    r4 <= insert(r3, p:8, l:8)
    r4 <= insert(r2, p:16, l:16)
    r1 = 1481067348
    r2 = 0
    if (r4 != r1) goto L020035c8
    r3 = b[r0+7] (u)
    r4 = b[r0+6] (u)
    r4 <= insert(r3, p:8, l:8)  #
    r5 = b[r0+5] (u)
    r1 = b[r0+4] (u)
    r1 <= insert(r5, p:8, l:8)
    r1 <= insert(r4, p:16, l:16)
    r3 = r1 + 40
    if (r3 > 128) goto L020035c8
    r2 = b[r0+11] (u)
    r3 = b[r0+10] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r4 = b[r0+9] (u)
    r5 = b[r0+8] (u)
    r5 <= insert(r4, p:8, l:8)
    r5 <= insert(r3, p:16, l:16)
    r0 += 40
    call capture_metadata_crc
    r2 = 1
    if (r0 != r5) {
    r2 = 0
    }
L020035c8:
    r0 = r2
    {pc, r5, r4} = [sp++]

; mode_and_settings_record_scan: 0x020035cc..0x02003774, module mode-and-settings (record_scan)
.type mode_and_settings_record_scan,@function
mode_and_settings_record_scan:
    [--sp] = {rets, r15-r4}
    sp += -392
    r7 = L01c1f180
    r0 = 88
    [r7+228] = r0
    r8 = 0xFFFFFFFF  ; @li.modimm
    r9 = 0
    d[r7+204] = r9_r8
    r0 = -1
    [r7+212] = r0
    r12 = sp + 8
    r10 = r12 + 40
    r4 = 0
    r11 = 1111968596
    goto L020036c8
L020035fe:
    r5 = r4 << 7
    r1 = sp + 8
    r2 = 128
    r0 = r5
    call mode_and_settings_record_read
    if (r0 != 0) goto L020036ce
    r0 = sp + 8
    r1 = 128
    call capture_metadata_erased
    if (r0 != 0) goto L020036c6
    r0 = r4 + 1
    [r7+208] = r0
    r0 = sp + 8
    r1 = 88
    call mode_and_settings_global_check
    if (r0 == 0) goto L0200362c
    [r7+204] = r4
    goto L020036c6
L0200362c:
    r0 = sp + 8
    call mode_and_settings_page_check
    if (r0 == 0) goto L02003638
    [r7+212] = r4
    goto L020036c6
L02003638:
    r0 = [sp+8]
    if (r0 != r11) goto L020036c6
    r13 = [r12+4]
    if (r13 > 472) goto L020036c6
    r0 = r13 + 167
    r14 = r0 >> 7
    r0 = r14 + r4
    if (r0 > 30) goto L020036c6
    [sp] = r0
    r0 = [r12+8]
    r0 = r13 + 40  #
    [sp+4] = r0
    if (r0 >= 128) {  ; @if.ge.ri.s12
    r0 = 128
    }
    r2 = r0 + -40
    r0 = -1
    r1 = r10
    call preset_storage_crc_update
    r6 = r0
    r15 = r13 + -88
    r5 = r5 + 128
    r13 = 1
    goto L020036a2
L02003684:
    r2 = r15
    if (r2 >= 128) {  ; @if.ge.ri.s12
    r2 = 128
    }
    r1 = sp + 8
    r0 = r6
    call preset_storage_crc_update
    r6 = r0
    r5 = r5 + 128
    r15 = r15 + -128
    r13 = r13 + 1
L020036a2:
    if (r13 >= r14) goto L020036b4
    r1 = sp + 8
    r2 = 128
    r0 = r5
    call mode_and_settings_record_read
    if (r0 == 0) goto L02003684
    goto L020036c6
L020036b4:
    r0 = ~r6  #
    r1 = [sp+4]
    if (r1 == r0) {
    r0 = [sp]
    [r7+208] = r0
    r4 = r0 + -1
    }
L020036c6:
    r4 += 1  ; @add.ri.u5
L020036c8:
    if (r4 < 30) goto L020035fe
    goto L020036de
L020036ce:
    r0 = r9 + 0xFFFFFFFF  ; @add.modimm.rri
    r1 = 30
    d[r7+204] = r1_r0
    r0 = -1
    [r7+212] = r0
L020036de:
    d[r7+216] = r9_r8
    r4 = 0
    [r7+224] = r4
    r1 = sp + 136
    r0 = 3840
    r2 = 256
    call mode_and_settings_record_read
    if (r0 == 0) goto L0200370a
    r0 = r4 + 0xFFFFFFFF  ; @add.modimm.rri
    r1 = 16
    d[r7+216] = r1_r0
    [r7+224] = r4
    goto L02003770
L0200370a:
    r0 = 1464224596
    r8 = 230166954
    goto L0200376a
L02003718:
    r3 = r2 << 4
    r4 = sp + 136
    r3 += r4  ; @add.rr
    r5 = [r3+0]
    if (r5 == -1) goto L0200374e
    r4 = r2 + 1
    [r7+220] = r4
    if (r5 != r0) goto L0200376a
    r5 = [r3+4]
    r1 = ~r5  #
    r6 = [r3+8]
    if (r6 != r1) goto L0200376a
    r3 = r5 ^ r8  #
    r1 = [r3+12]
    if (r1 == r3) {
    [r7+216] = r2
    [r7+224] = r5
    }
    goto L0200376a
L0200374e:
    r4 = [r3+4]
    if (r4 != -1) goto L02003760
    r4 = [r3+8]
    if (r4 != -1) goto L02003760
    r3 = [r3+12]
    if (r3 == -1) goto L02003768
L02003760:
    r4 = r2 + 1
    [r7+220] = r4
    goto L0200376a
L02003768:
    r4 = r2 + 1
L0200376a:
    r2 = r4
    if (r2 != 16) goto L02003718
L02003770:
    sp += 392
    {pc, r15-r4} = [sp++]

; mode_and_settings_block_defaults: 0x02003774..0x020037cc, module mode-and-settings (block_defaults)
.type mode_and_settings_block_defaults,@function
mode_and_settings_block_defaults:
    [--sp] = {rets, r8-r4}
    r2 = r0 + 4
    r8 = 0
    rep 28 {
    b[r2++=1] = r8
    }
    r2 = 1
    b[r0+0] = r2
    r2 = 100
    b[r0+1] = r2
    r2 = 53
    b[r0+2] = r2
    b[r0+3] = r8
    r2 = r0 + 16
    r3 = L02034fcc
    r4 = 24
    goto L020037ba
L0200379c:
    r5 = 3
    r6 = r3
    r7 = r2
    goto L020037b0
L020037a4:
    r1 = b[r6++=1] (u)
    r1 = r1 / r4 (u)  #
    b[r7+-12] = r1
    b[r7++=1] = r1
    r5 += -1
L020037b0:
    if (r5 != 0) goto L020037a4
    r3 += 3  ; @add.ri.u5
    r2 += 3  ; @add.ri.u5
    r8 = r8 + 1
L020037ba:
    if (r8 != 4) goto L0200379c
    r1 = 1
    b[r0+28] = r1
    r1 = 60
    b[r0+29] = r1
    {pc, r8-r4} = [sp++]

; mode_and_settings_block_clamp: 0x020037cc..0x02003806, module mode-and-settings (block_clamp)
.type mode_and_settings_block_clamp,@function
mode_and_settings_block_clamp:
    r1 = 1
    b[r0+0] = r1
    r1 = b[r0+1] (u)
    if (r1 >= 101) {  ; @if.ge.ri.s12
    r1 = 100
    b[r0+1] = r1
    }
    r1 = b[r0+3] (u)
    r1 = r1 & 0xFFFFFF0F
    b[r0+3] = r1
    r1 = b[++r0=28] (u)
    if (r1 >= 3) {  ; @if.ge.ri.s12
    r1 = 1
    b[r0+0] = r1
    }
    r2 = b[r0+1] (u)
    r1 = 10
    if (r2 < 10) goto L020037fc
    r1 = 250
    if (r2 < 251) goto L020037fe
L020037fc:
    b[r0+1] = r1
L020037fe:
    r1 = 0
    b[r0+3] = r1
    b[r0+2] = r1
    rts

; mode_and_settings_block_import: 0x02003806..0x02003838, module mode-and-settings (block_import)
.type mode_and_settings_block_import,@function
mode_and_settings_block_import:
    [--sp] = {rets, r6-r4}
    r5 = r1
    r6 = r0
    r4 = L01c27204
    r0 = r4
    call mode_and_settings_block_defaults
    if (r6 == 0) goto L02003836
    if (r5 < 4) goto L02003836
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L02003836
    if (r5 >= 32) {  ; @if.ge.ri.s12
    r5 = 32
    }
    r0 = r4
    r1 = r6
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4
    call mode_and_settings_block_clamp
L02003836:
    {pc, r6-r4} = [sp++]

; mode_and_settings_block_ensure: 0x02003838..0x02003854, module mode-and-settings (block_ensure)
.type mode_and_settings_block_ensure,@function
mode_and_settings_block_ensure:
    [--sp] = rets
    r1 = 2420
    r0 = L01c26890
    r1 = b[r0+r1] (u)
    if (r1 != 1) {  ; @if.ne.ri.s12
    r0 = r0 + 2420
    call mode_and_settings_block_defaults
    }
    pc = [sp++]

; mode_and_settings_block_export: 0x02003854..0x02003868, module mode-and-settings (block_export)
.type mode_and_settings_block_export,@function
mode_and_settings_block_export:
    [--sp] = {rets, r4}
    r4 = r0
    call mode_and_settings_block_ensure
    r0 = L01c27204
    rep 32 {
    r1 = b[r0++=1] (u)
    b[r4++=1] = r1
    }
    {pc, r4} = [sp++]

; mode_and_settings_slots_clear: 0x02003868..0x02003898, module mode-and-settings (slots_clear)
.type mode_and_settings_slots_clear,@function
mode_and_settings_slots_clear:
    [--sp] = {rets, r5, r4}
    r4 = L01c26890
    r5 = r4 + 6592
    r0 = r5 + 4
    r1 = 255
    r2 = 376
    call effect_enable_memset  ; @call.xl
    r0 = 0
    r1 = 6968  #
    h[r5+0] = r0
    h[r5+2] = r0
    b[r4+r1] = r0
    r1 += 1  ; @add.ri.u5
    b[r4+r1] = r0
    {pc, r5, r4} = [sp++]
