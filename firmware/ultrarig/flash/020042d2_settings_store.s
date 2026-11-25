; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; settings_store: 9 functions, 0x020042d2..0x02004816

; settings_store_global_record: 0x020042d2..0x02004402, module settings-store (global_record)
.type settings_store_global_record,@function
settings_store_global_record:
    [--sp] = {rets, r6-r4}
    sp += -152
    r4 = r0
    r5 = L01c26890
    if (r1 != 0) goto L020042fa
    r0 = 736
    r0 = b[r5+r0] (u)
    if ((r0 & 1) == 0) goto L020042fa
    r0 = r5 + 3988
    r1 = sp + 64
    rep 22 {
    r2 = [r0++=4]
    [r1++=4] = r2
    }
    goto L02004300
L020042fa:
    r0 = sp + 64
    call mode_and_settings_device_record
L02004300:
    r1 = L01c1f180
    r0 = [r1+224]
    if (r0 != 0) goto L02004310
    r0 = [r5+784]
L02004310:
    r2 = h[r5+80] (u)
    [sp+84] = r0
    b[sp+67] = r2
    r0 = r2 >> 8
    b[sp+77] = r0
    r6 = [r1+100]
    r0 = 1
    b[sp+125] = r0
    r2 = -1
    r3 = -1
    ifs (r6 >= 0) {  ; @ifs.ge.ri.s12
    r3 = r6
    }
    r1 = [r1+104]
    b[sp+126] = r3
    ifs (r1 >= 0) {  ; @ifs.ge.ri.s12
    r2 = r1
    }
    r1 = b[r5+40] (u)
    b[sp+127] = r2
    if (r1 != 0) goto L0200434e
    r0 = r1
L0200434e:
    r1 = b[sp+150] (u)
    r1 &= 4294967167
    r1 <= insert(r0, p:7, l:1)
    b[sp+150] = r1
    r0 = 0
    h[sp+8] = r0
    r1 = 0
    d[sp] = r1_r0
    r0 = sp + 12
    call storage_fault_decode
    if (r0 == 0) goto L02004374
    r0 = sp + 12
    goto L0200437e
L02004374:
    r0 = b[r5+39] (u)
    if (r0 == 0) goto L02004384
    r0 = r5 + 1692
L0200437e:
    r1 = sp + 0
    call record_helpers_copy_record
L02004384:
    r0 = b[sp] (u)
    r1 = b[sp+1] (u)
    r2 = h[sp+2] (u)
    b[sp+78] = r0
    b[sp+79] = r1
    h[sp+82] = r2
    r0 = h[sp+4] (u)
    r1 = h[sp+6] (u)
    r2 = b[sp+8] (u)
    r3 = b[sp+9] (u)
    h[sp+134] = r0
    h[sp+138] = r1
    b[sp+141] = r2
    b[sp+147] = r3
    r0 = 1195854676
    r1 = 88
    d[sp+24] = r1_r0
    r5 = sp + 64
    r0 = r5
    call capture_metadata_crc
    [sp+32] = r0
    r0 = 0
    r6 = sp + 24
    r1 = L0203a024  ; "global"
    r0 = r6  #
    [sp+36] = r0
    call record_helpers_copy_name
    r2 = 40
    r0 = r4
    r1 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r4 + 40
    r2 = 88
    r1 = r5
    call effect_parameter_support_memmove  ; @call.xl
    sp += 152
    {pc, r6-r4} = [sp++]

; settings_store_page_write: 0x02004402..0x02004458, module settings-store (page_write)
.type settings_store_page_write,@function
settings_store_page_write:
    [--sp] = {rets, r8-r4}
    sp += -128
    r4 = r2
    r8 = r1
    r6 = r0
    r7 = -1
    if (r4 > 128) goto L02004452
    r0 = r6 + 0xFE000
    call capture_journal_write
    r1 = L01c26890
    r1 = [r1+280]
    r5 = r0
    if (r1 == 0) goto L02004430
    r0 = 1
    call L0203feb8  ; @call.xl
L02004430:
    r7 = -3
    if (r5 != 0) goto L02004452
    r1 = sp + 0
    r0 = r6
    r2 = r4
    call mode_and_settings_record_read
    if (r0 != 0) goto L02004452
    r0 = sp + 0
    r1 = r8
    r2 = r4
    call capture_journal_compare  ; @call.xl
    r7 = r0
    if (r7 == 0) goto L02004452
    r7 = -3
L02004452:
    r0 = r7
    sp += 128
    {pc, r8-r4} = [sp++]

; settings_store_ring_write: 0x02004458..0x020044b8, module settings-store (ring_write)
.type settings_store_ring_write,@function
settings_store_ring_write:
    [--sp] = {rets, r8-r4}
    r5_r4 = r1_r0
    r7 = -1
    r8 = L01c1f180
L02004464:
    r7 += 1  ; @add.ri.u5
    ifs (r7 > 1) goto L020044b0
    r6 = [r8+208]
    if (r6 > 29) goto L020044b4
    r0 = r6 << 7
    r1 = r4
    r2 = r5
    call settings_store_page_write
    r1 = r6 + 1
    [r8+208] = r1
    if (r0 != 0) goto L02004464
    r0 = b[r4+3] (u)
    r1 = b[r4+2] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r4+1] (u)
    r3 = b[r4+0] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r1 = r8 + 204
    r0 = r8 + 212
    r2 = 1481067348
    if (r3 != r2) {
    r0 = r1
    }
    [r0+0] = r6
    r0 = 0
    {pc, r8-r4} = [sp++]
L020044b0:
    r0 = -3
    {pc, r8-r4} = [sp++]
L020044b4:
    r0 = -9
    {pc, r8-r4} = [sp++]

; settings_store_device_word_write: 0x020044b8..0x02004508, module settings-store (device_word_write)
.type settings_store_device_word_write,@function
settings_store_device_word_write:
    [--sp] = {rets, r6-r4}
    sp += -16
    r4 = r0
    r0 = 1464224596
    r0 = ~r4  #
    [sp] = r0
    [sp+4] = r4
    [sp+8] = r0
    r5 = L01c1f180
    r6 = [r5+220]
    r0 = 230166954
    r0 ^= r4
    [sp+12] = r0
    r0 = -9
    if (r6 > 15) goto L02004504
    r0 = r6 << 4
    r0 = r0 + 3840
    r1 = sp + 0
    r2 = 16
    call settings_store_page_write
    r1 = r6 + 1
    [r5+220] = r1
    if (r0 != 0) goto L02004504
    [r5+216] = r6
    [r5+224] = r4
    r0 = 0
L02004504:
    sp += 16
    {pc, r6-r4} = [sp++]

; settings_store_block_write: 0x02004508..0x020045f6, module settings-store (block_write)
.type settings_store_block_write,@function
settings_store_block_write:
    [--sp] = {rets, r15-r4}
    sp += -12
    r4 = r0
    r0 = -1
    if (r1 < 40) goto L020045f2
    r2 = r1 + 127
    if (r2 > 639) goto L020045f2
    r10 = r2 >> 7  #
    [sp] = r1
    if (r1 >= 128) {  ; @if.ge.ri.s12
    r0 = 128
    [sp] = r0
    }
    r0 = r10 << 7
    r1 = r1 + 128
    r1 = r1 - r0
    r6 = r10 + -1
    r0 += -128
    d[sp+4] = r1_r0
    r14 = 0
    r2 = L01c1f180
    r12 = L01c24520
    goto L020045d8
L0200454e:
    r11 = r2
    [r2+208] = r1
    r1 = r6 + r0
    r9 = r1 << 7
    r7 = r0 << 7
    r8 = 0
    r15 = [sp+8]  ; @ld.w.sp.l
    r13 = [sp+4]  ; @ld.w.sp.l
    r0 = 0
    goto L020045be
L0200456a:
    r5 = r15
    if (r5 >= 128) {  ; @if.ge.ri.s12
    r5 = 128
    }
    if (r8 == 0) goto L02004582
    r0 = r7 + r13
    r1 = r4 + r13
    r2 = r5
    goto L020045ae
L02004582:
    r0 = 0x80 - r5
    r2 = 0
    if (r5 <= 127) {  ; @if.le.ri.s12
    r2 = r0
    }
    r0 = r5 + r12
    r1 = 0
    call effect_enable_memset  ; @call.xl
    r1 = r4 + r13
    r0 = r12
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r2 = 128
    r0 = r9
    r1 = r12
L020045ae:
    call settings_store_page_write
    r15 = r15 + 128
    r8 = r8 + 1
    r13 = r13 + -128
L020045be:
    if (r0 != 0) goto L020045c4
    if (r6 != r8) goto L0200456a
L020045c4:
    if (r0 != 0) goto L020045d2
    r0 = r7  #
    r2 = [sp]
    r1 = r4
    call settings_store_page_write
    if (r0 == 0) goto L020045f0
L020045d2:
    r14 = r14 + 1
    r2 = r11
L020045d8:
    ifs (r14 > 1) goto L020045ec
    r0 = [r2+208]
    r1 = r0 + r10
    if (r1 <= 30) goto L0200454e
    r0 = -9
    goto L020045f2
L020045ec:
    r0 = -3
    goto L020045f2
L020045f0:
    r0 = 0
L020045f2:
    sp += 12
    {pc, r15-r4} = [sp++]

; settings_store_compaction: 0x020045f6..0x0200476e, module settings-store (compaction)
.type settings_store_compaction,@function
settings_store_compaction:
    [--sp] = {rets, r14-r4}
    sp += -16
    r8 = r1
    r14 = r0
    r12 = 0
    r13 = 0
    d[sp+8] = r13_r12
    if (r0 == 0) goto L0200463a
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r3, p:8, l:8)
    r0 <= insert(r2, p:16, l:16)
    r7 = 1
    r2 = 1111968596
    r1 = 1
    if (r0 != r2) {
    r1 = 0
    }
    r1 = r1 << 1
    r2 = r2 + 0x16000000
    if (r0 != r2) {
    r7 = r1
    }
    goto L0200463c
L0200463a:
    r7 = -1
L0200463c:
    r10 = L01c1f180
    r0 = r10
    r1 = [++r0=204]
    r9 = 88  #
    r2 = [r0+8]
    r0 = [r0+24]
    [sp] = r1
    [sp+4] = r2
    if (r0 == 0) goto L02004658
    r9 = r0
L02004658:
    r11 = L01c26890
    r5 = r11 + 6072
    r6 = 0
    goto L020046be
L02004666:
    r0 = sp + 0
    if (r7 == r6) goto L020046b8
    r0 = [r0+r6<<2]
    ifs (r0 < 0) goto L020046b8
    r0 = r0 << 7
    r4 = r5 + -4
    r2 = 128
    r1 = r4
    call mode_and_settings_record_read
    if (r0 != 0) goto L02004768
    if (r6 == 0) goto L02004690
    r0 = r4
    call mode_and_settings_page_check
    if (r0 != 0) goto L0200469a
    goto L020046b8
L02004690:
    r0 = r4
    r1 = r9
    call mode_and_settings_global_check
    if (r0 == 0) goto L020046b8
L0200469a:
    r0 = b[r5+3] (u)
    r1 = b[r5+2] (u)
    r1 <= insert(r0, p:8, l:8)  #
    r2 = b[r5+1] (u)
    r3 = b[r5+0] (u)
    r3 <= insert(r2, p:8, l:8)
    r3 <= insert(r1, p:16, l:16)
    r0 = r3 + 40
    r1 = sp + 8
    [r1+r6<<2] = r0
L020046b8:
    r5 = r5 + 128
    r6 += 1  ; @add.ri.u5
L020046be:
    ifs (r6 <= 1) goto L02004666
    r9 = r14
    r6 = r8
    if (r7 != 2) {  ; @if.ne.ri.s12
    r0 = 310
    r6 = [r11+r0<<2]
    r9 = L01c25438
    }
    r4 = [r10+224]
    call storage_coordination_wait_ready
    r0 = 0xFE000
    r1 = 1
    call capture_journal_erase
    r1 = r0
    r0 = -1
    if (r1 != 0) goto L02004710
    r0 = r0 + 0x0  ; @add.modimm.rri
    r1 = 0
    d[r10+204] = r1_r0
    r1 = r0
    d[r10+212] = r1_r0
    d[r10+220] = r13_r12
    if (r4 == 0) {  ; @if.eq.ri.s12
    r0 = 0
    } else {
    r0 = r4
    call settings_store_device_word_write
    }
L02004710:
    r4 = r11 + 6068
    r5 = 0
    goto L02004730
L02004718:
    r0 = sp + 8
    r1 = [r0+r5<<2]
    if (r1 == 0) {  ; @if.eq.ri.s12
    r0 = 0
    } else {
    r0 = r4
    call settings_store_ring_write
    }
    r4 = r4 + 128
    r5 += 1  ; @add.ri.u5
L02004730:
    if (r0 != 0) goto L02004736
    ifs (r5 < 2) goto L02004718
L02004736:
    if (r7 == 2) goto L02004748
    if (r14 == 0) goto L02004748
    if (r0 != 0) goto L02004748
    r0 = r14
    r1 = r8
    call settings_store_ring_write
L02004748:
    if (r0 != 0) goto L0200476a
    if (r6 == 0) goto L0200476a
    r0 = r9
    r1 = r6
    call settings_store_block_write
    r1 = r0
    if (r7 == 2) goto L0200476a
    r0 = 0
    if (r1 == 0) goto L0200476a
    r1 = r10 + 232
    [r1+0] += 1  ; @rmw.add.s12
    goto L0200476a
L02004768:
    r0 = -2
L0200476a:
    sp += 16
    {pc, r14-r4} = [sp++]

; settings_store_record_store: 0x0200476e..0x02004786, module settings-store (record_store)
.type settings_store_record_store,@function
settings_store_record_store:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call settings_store_ring_write
    if (r0 == -9) {
    r0 = r5
    r1 = r4
    call settings_store_compaction
    }
    {pc, r5, r4} = [sp++]

; settings_store_global_save: 0x02004786..0x020047da, module settings-store (global_save)
.type settings_store_global_save,@function
settings_store_global_save:
    [--sp] = {rets, r6-r4}
    sp += -128
    r4 = r0
    r0 = sp + 0
    r1 = r4
    call settings_store_global_record
    r5 = 776
    r6 = L01c26890
    r0 = b[r6+r5] (u)
    if (r0 != 0) goto L020047ae
    call mode_and_settings_record_scan
    r0 = 1
    b[r6+r5] = r0
L020047ae:
    r0 = sp + 0
    r1 = 128
    call settings_store_record_store
    r5 = r0
    if (r4 == 0) goto L020047d4
    if (r5 != 0) goto L020047d4
    r0 = r6 + 3988
    r1 = sp + 0
    r1 += 40
    r2 = 88
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 736
    r1 = 1
    b[r6+r0] = r1
L020047d4:
    r0 = r5
    sp += 128
    {pc, r6-r4} = [sp++]

; settings_store_select_save: 0x020047da..0x02004816, module settings-store (select_save)
.type settings_store_select_save,@function
settings_store_select_save:
    [--sp] = {rets, r4}
    r0 = r0 & 0xF
    r2 = r2 & 0xF
    r3 = L01c26890
    r4 = h[r3+80] (u)
    r2 <= insert(r0, p:8, l:4)
    r2 <= insert(r1, p:12, l:20)
    r0 = r2.l (u)
    if (r4 != r0) goto L0200480c
    r0 = L01c1f180
    r1 = [r0+204]
    r0 = 0
    ifs (r1 > -1) goto L02004814
L0200480c:
    h[r3+80] = r2
    r0 = 0
    call settings_store_global_save
L02004814:
    {pc, r4} = [sp++]
