; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; fault_record: 14 functions, 0x020103f8..0x02010af4

; fault_record_life_text: 0x020103f8..0x0201046e, module fault-record (life_text)
.type fault_record_life_text,@function
fault_record_life_text:
    [--sp] = {rets, r9-r4}
    sp += -48
    r9 = r0
    r0 = sp + 36
    call storage_fault_decode
    r8 = L02035810
    if (r0 == 0) goto L0201045e
    r0 = h[sp+36] (u)
    r2 = b[sp+40] (u)
    r3 = b[sp+41] (u)
    r5 = b[sp+42] (u)
    r6 = b[sp+43] (u)
    r7 = h[sp+38] (u)
    r1 = b[sp+45] (u)
    r4 = b[sp+46] (u)
    [sp+32] = r4
    [sp+28] = r1
    r1 = 10
    r1 = r7 / r1 (u)
    [sp+20] = r1
    [sp+16] = r6
    [sp+12] = r5
    d[sp+4] = r3_r2
    r0 = r1 * 0xA  #
    [sp] = r0
    r0 = r7 - r0
    r1 = 8894  #
    [sp+24] = r0
    r2 = r8 + r1
    r1 = 112
    r3 = 1
    r0 = r9
    call L0200691e
    goto L0201046a
L0201045e:
    r2 = r8 + 1538
    r1 = 112
    r0 = r9
    call L0200691e
L0201046a:
    sp += 48
    {pc, r9-r4} = [sp++]

; fault_record_life_report: 0x0201046e..0x020104a6, module fault-record (life_report)
.type fault_record_life_report,@function
fault_record_life_report:
    [--sp] = {rets, r5, r4}
    sp += -112
    r4 = sp + 0
    r0 = r4
    call fault_record_life_text
    r0 = 8728
    r1 = L01c26890
    r5 = r1 + r0
    r2 = L02039fee  ; "%s"
    r1 = 512
    r0 = r5
    r3 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r5
    call command_services_console_send
    sp += 112
    {pc, r5, r4} = [sp++]

; fault_record_crash_cause: 0x020104a6..0x0201058a, module fault-record (crash_cause)
.type fault_record_crash_cause,@function
fault_record_crash_cause:
    [--sp] = {rets, r10-r4}
    sp += -32
    r8 = r3
    r5 = r2
    r7_r6 = r1_r0
    call storage_fault_tag
    r1 = uextra(r6, p:12, l:8)
    r3 = r0
    if (r3 == 0) goto L020104be
    r3 = r1
L020104be:
    r10 = L01c26890
    r0 = r10 + 7372
    r9 = L02035810
    r2 = r9 + 1062
    r1 = 400
    call L0200691e
    r4 = r0
    if (r4 > 399) goto L02010584
    r0 = 4293918720
    r0 &= r6
    r1 = 3495952384
    if (r0 != r1) goto L02010584
    ifs (r4 < 1) goto L02010584
    r0 = [sp+64]
    r1 = 0
    goto L02010514
L020104fc:
    r2 = r7.b0 (u)
    r3 = r2 + -33
    r2 = r7
    if (r3 >= 94) {  ; @if.ge.ri.s12
    r2 = 0
    }
    r3 = sp + 27
    b[r3+r1] = r2
    r7 = r7 >> 8
    r1 += 1  ; @add.ri.u5
L02010514:
    if (r1 != 4) goto L020104fc
    r1 = 0
    b[sp+31] = r1
    r1 = r9 + 1262
    r2 = sp + 16
    r3 = 1270
    r3 = b[r9+r3] (u)
    rep 4 {
    r6 = h[r1++=2] (u)
    h[r2++=2] = r6
    }
    b[sp+24] = r3
    if (r8 == r0) goto L02010548
    r2 = r9 + 340
    r0 = sp + 16
    r1 = 9
    r3 = r8
    call L0200691e
L02010548:
    r1 = b[sp+27] (u)
    r0 = sp + 16
    [sp+12] = r0
    r0 = 1048575
    r0 &= r5
    r0 = uextra(r5, p:20, l:4)  #
    [sp+8] = r0
    [sp+4] = r0
    r0 = r5 >> 24
    r0 = r9 + 15  #
    [sp] = r0
    r3 = sp + 27
    if (r1 != 0) goto L0201056e
    r3 = r0
L0201056e:
    r0 = r4 + r10
    r0 = r0 + 7372
    r1 = 0x190 - r4
    r2 = r9 + 5407
    call L0200691e
    r4 += r0  ; @add.rr
L02010584:
    r0 = r4
    sp += 32
    {pc, r10-r4} = [sp++]

; fault_record_check_word: 0x0201058a..0x020105a0, module fault-record (check_word)
.type fault_record_check_word,@function
fault_record_check_word:
    r3 = 2654435761
    r1 *= r3
    r0 ^= r1
    r0 ^= r2
    r0 = r0 ^ 0x5D5D5D5D
    if (r0 != 0) goto L0201059e
    r0 = 1
L0201059e:
    rts

; fault_record_status_bits: 0x020105a0..0x02010600, module fault-record (status_bits)
.type fault_record_status_bits,@function
fault_record_status_bits:
    [--sp] = {rets, r5, r4}
    r0 = L01c26890
    r1 = b[r0+20] (u)
    r2 = b[r0+21] (u)
    r3 = r0 + 280
    r2 = r2 << 1
    r1 |= r2  #
    r4 = [r3+48]
    r2 = r4 << 2
    r1 |= r2  #
    r4 = [r3+52]
    r2 = L01c1f180
    r5 = b[r2+2] (u)
    r4 = r4 << 3
    r1 |= r4  #
    r2 = b[r2+3] (u)
    r4 = r5 << 4
    r1 |= r4
    r2 = r2 << 5
    r1 |= r2
    r0 = r0 + 348  #
    r2 = [r3+0]
    r3 = [r0+32]
    r2 = r2 << 6
    r2 = r2.b0 (u)  #
    r4 = [r0+36]
    r1 |= r2
    r2 = r3 - r4
    r2 = r2 << 8
    r2 = r2.l (u)  #
    r3 = [r0+40]
    r1 |= r2
    r2 = r3 << 16
    r2 = r2 & 0xFF0000  #
    r0 = [r0+0]
    r1 |= r2
    r0 = r0 << 24
    r0 |= r1
    {pc, r5, r4} = [sp++]

; fault_record_fatal_record: 0x02010600..0x02010892, module fault-record (fatal_record)
.type fault_record_fatal_record,@function
fault_record_fatal_record:
    sp += -12
    r7 = 29883864
    r4 = 3708  #
    r3 = [r7+0]
    r3 = r3 >> 20
    r5 = r2
    r6 = r1
    if (r3 == r4) goto L0201087c
    r0 = r7  #
    [sp] = r0
    call storage_fault_append
    [r7+4] = r6
    [r7+8] = r5
    r13 = L01c26890
    r0 = [r13+124]
    [r7+12] = r0
    r0 = b[r13+6] (u)
    r2 = b[r13+22] (u)
    r1 = r2 + -1
    r3 = r1.b0 (u)
    r1 = 0
    if (r3 > 3) goto L02010658
    r1 = r2 + r13
    r2 = 391
    r1 = b[r1+r2] (u)
    r1 = r1 << 20
    r1 = r1 & 0xF00000
L02010658:
    r3 = L01c1f180
    r0 = r0 << 24
    r0 |= r1  #
    r2 = [r3+24]
    r1 = r2 * 0xA
    r2 = 1000
    r1 = r1 / r2 (u)
    r2 = 1048575
    r1 = umin(r1, r2)
    r0 |= r1
    [r7+16] = r0
    r0 = [r13+128]
    [r7+20] = r0
    r0 = [r13+376]
    r4 = [r13+356]
    r5 = r7 + -344
    if (r0 == 0) goto L020106c8
    r1 = [r3+24]
    r0 = r1 - r0
    r0 = r0 * 0xA
    r0 = r13 + 4076  #
    [r5+4] = r0
    r2 = r13  #
    r1 = [r0+8]
    r3 = [++r2=352]
    r1 = r1 - r3
    [r5+8] = r1
    r1 = [r2+8]
    r1 = r4 - r1
    [r5+12] = r1
    r1 = [r0+0]
    r3 = [r2+12]
    r1 = r1 - r3
    [r5+16] = r1
    r1 = [r0+12]
    r3 = [r2+16]
    r1 = r1 - r3
    [r5+20] = r1
    r1 = [r0+16]
    r0 = [r2+20]
    goto L020106e0
L020106c8:
    r0 = 0
    r1 = r13 + 4076  #
    [r5+4] = r0
    r2 = [r1+8]
    [r5+8] = r2
    [r5+12] = r4
    r2 = [r1+0]
    [r5+16] = r2
    r2 = [r1+12]
    [r5+20] = r2
    r1 = [r1+16]
L020106e0:
    r0 = r1 - r0
    [r5+24] = r0
    call fault_record_status_bits
    r10 = r4 >> 6  #
    [r5+28] = r0
    r15 = r10  #
    [r5+32] = r4
    if (r10 >= 8) {  ; @if.ge.ri.s12
    r15 = 8
    }
    r12 = sp + 4
    r3 = 0
    r14 = r5 + 40
    goto L020107a2
L02010706:
    r0 = r3 * 0xC
    r7 = r0 + r14
    r2 = 0
    if (r3 >= r15) goto L02010790
    r0 = r10 - r3
    r0 = r0 & 0x7
    r4 = r13 + 2324
    r4 = [r4+r0<<2]
    r5 = r13 + 2356
    r11 = [r5+r0<<2]
    r0 = r4 - 0x1C00000
    r0 = r0 >> 10
    if (r0 > 510) goto L02010796
    if ((r4 & 0x3) != 0) goto L02010796
    r0 = b[r4+12] (u)
    r2 = r4 + 12
    if (r0 != 35) goto L0201075a
    r0 = b[r2+1] (u)
    if (r0 != 67) goto L0201075a
    r4 = b[r2+2] (u)
    r0 = r2 + 3
    r4 += -48
    r4 = r4.b0 (u)
    if (r4 >= 10) {  ; @if.ge.ri.s12
    r0 = r2
    }
    r2 = r0
L0201075a:
    r4 = 0
    r5 = 0
    d[sp+4] = r5_r4
    goto L0201077e
L02010764:
    r8 = r4 & 0xFFFFFFFC
    r9 = sp + 4
    r1 = r9 + r8
    r6 = r5 & 0x18
    r0 <<= r6
    [r1+0] |= r0
    r5 += 8  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0201077e:
    if (r4 > 7) goto L02010788
    r0 = b[r2+r4] (u)
    if (r0 != 0) goto L02010764
L02010788:
    r4 = [r12+4]
    r2 = [sp+4]
    goto L02010798
L02010790:
    r4 = 0
    r11 = 0
    goto L02010798
L02010796:
    r4 = 0
L02010798:
    [r7+0] = r11
    [r7+4] = r2
    [r7+8] = r4
    r3 += 1  ; @add.ri.u5
L020107a2:
    if (r3 != 8) goto L02010706
    r0 = 3495755776
    r0 = r0 | r15
    r6 = r14 + -40
    [r6+0] = r0
    r0 = b[r13+1] (u)
    r3 = 1
    r2 = 1
    if (r0 != 0) goto L020107c2
    r2 = r0
L020107c2:
    call phase3_p4_cdc_ready
    r1 = 1
    r5 = r6 + 344
    if (r0 != 0) goto L020107d0
    r1 = r0
L020107d0:
    r4 = b[r13+4] (u)
    r2 <= insert(r1, p:1, l:1)
    r0 = 1
    if (r4 != 0) goto L020107de
    r0 = r4
L020107de:
    r1 = b[r13+3] (u)
    r2 <= insert(r0, p:2, l:1)
    if (r1 != 0) goto L020107ea
    r3 = r1
L020107ea:
    r2 <= insert(r3, p:3, l:1)  #
    r0 = [r5+36]
    r1 = b[r13+7] (u)
    r0 = r0 >> 8
    r0 = r0 & 0xF0
    r0 |= r2
    r1 = r1 << 8
    r1 = r1 & 0xF00
    r0 |= r1
    r1 = r5 + -208
    [r1+0] = r0
    r0 = L01c1f180
    r0 = [r0+24]
    r2 = [r13+100]
    r0 = r0 * 0xA
    r0 = r0 - r2
    [r1+4] = r0
    r0 = [r13+564]
    [r1+8] = r0
    r0 = [r13+132]
    [r1+12] = r0
    [r6+0] |= 0x8000
    r0 = [r5+4]
    r1 = [r5+16]
    r2 = [r5+20]
    call fault_record_check_word
    r2 = r5 + -440  #
    [r6+36] = r0
    r0 = 0
    r1 = 32436224
    goto L02010862
L02010848:
    r3 = [++r1=452]
    r4 = r2
    [++r4=r0] = r3
    r3 = [r1+4]
    [r4+4] = r3
    r3 = [r1+8]
    [r4+8] = r3
    r3 = [r1+12]
    [r4+12] = r3
    r1 += 60
    r0 += 16  ; @add.ri.u5
L02010862:
    if (r0 != 32) goto L02010848
    r0 = [r13+104]
    r1 = [sp]
    r1 = r1 & 0xF
    r0 |= r1
    r1 = 3495952384
    r0 |= r1
    [r5+0] = r0
L0201087c:
    r0 = 2
    call storage_fault_once
    r0 = 160
    r1 = 4
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
L02010890:
    goto L02010890

; fault_record_radio_wait: 0x02010892..0x020108d4, module fault-record (radio_wait)
.type fault_record_radio_wait,@function
fault_record_radio_wait:
    [--sp] = {rets, r7-r4}
    r4 = 0
    r5 = 1456
    r6 = L01c26890
    r7 = L01c1f180
    goto L020108c0
L020108a8:
    if ((r0 & 1) == 0) goto L020108cc
    r0 = 1
    call L0203feb8  ; @call.xl
    r0 = [r7+24]
    [r6+204] = r0
    call link_and_print_link_report
    r4 += 10  ; @add.ri.u5
L020108c0:
    r0 = b[r6+r5] (u)
    r1 = r4 >> 3
    if (r1 <= 1874) goto L020108a8
L020108cc:
    r1 = 1
    r0 = r1 & ~r0
    {pc, r7-r4} = [sp++]

; fault_record_step_state: 0x020108d4..0x020108f6, module fault-record (step_state)
.type fault_record_step_state,@function
fault_record_step_state:
    [--sp] = {rets, r4}
    r4 = r0
    call record_helpers_leading_ones
    if (r0 >= r1) goto L020108ec
    r0 += r4  ; @add.rr
    r0 = b[r0+1] (u)
    if (r0 >= 7) {  ; @if.ge.ri.s12
    r0 = 0
    }
    {pc, r4} = [sp++]
L020108ec:
    r0 = 1
    if (r1 != 0) goto L020108f4
    r0 = r1
    {pc, r4} = [sp++]
L020108f4:
    {pc, r4} = [sp++]

; fault_record_state_name: 0x020108f6..0x0201091a, module fault-record (state_name)
.type fault_record_state_name,@function
fault_record_state_name:
    if (r0 >= 7) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r1 = L02035836  ; "ok"
    r3 = r1 + 148
    r2 = r1
    if (r0 != 1) {  ; @if.ne.ri.s12
    r2 = r3
    }
    r1 = r1 + 1215
    if (r0 == 0) goto L02010916
    r1 = r2
L02010916:
    r0 = r1
    rts

; fault_record_why_text: 0x0201091a..0x0201092c, module fault-record (why_text)
.type fault_record_why_text,@function
fault_record_why_text:
    if (r0 >= 7) {  ; @if.ge.ri.s12
    r0 = 0
    }
    r1 = L02033bac
    r0 = [r1+r0<<2]
    rts

; fault_record_clock_state: 0x0201092c..0x02010a8c, module fault-record (clock_state)
.type fault_record_clock_state,@function
fault_record_clock_state:
    [--sp] = {rets, r15-r4}
    sp += -188
    r4 = sp + 184
    r0 = r4
    call record_helpers_half_fields
    r0 = 396
    call boundary_hooks_rate_level
    r11 = r0
    r0 = r4
    r1 = r11
    call fault_record_step_state
    r10 = r0
    r5 = 0
    r12 = L02035810
    r6 = 0
    goto L020109b8
L02010958:
    if (r6 > 95) goto L020109bc
    r9 = r12 + 9
    r7 = r12
    if (r5 != 0) goto L02010966
    r9 = r7
L02010966:
    r0 = sp + 184
    r4 = b[r0+r5] (u)
    r0 = sp + 88
    r14 = r7 + 1006
    r8 = r0 + r6
    r0 = r4
    call fault_record_state_name
    r1 = r4 + -2
    r2 = r7 + 1
    r13 = r0
    if (r1 >= 5) {  ; @if.ge.ri.s12
    r2 = r7
    }
    r3 = h[r14+r5<<1] (u)
    r14 = 0x60 - r6
    if (r1 > 4) goto L0201099c
    r0 = r4
    call fault_record_why_text
    r7 = r0
L0201099c:
    r0 = r8  #
    [sp+12] = r7
    r2 = r12 + 1760  #
    [sp+8] = r2
    [sp+4] = r13  ; @st.w.sp.l
    r1 = r14  #
    [sp] = r3
    r3 = r9
    call L0200691e
    r6 += r0  ; @add.rr
    r5 += 1  ; @add.ri.u5
L020109b8:
    if (r5 <= r11) goto L02010958
L020109bc:
    call dsp_audio_path_cached  ; @call.xl
    r5 = L01c1f180
    r1 = [r5+52]
    [sp+76] = r1
    r1 = b[r5+5] (u)
    [sp+68] = r1
    [sp+72] = r0
    call preset_application_services_budget  ; @call.xl
    r8 = r0
    call ir_reload_and_leaves_get_rate
    r0 = r10  #
    [sp+84] = r0
    call fault_record_state_name
    r0 = r10  #
    [sp+80] = r0
    call fault_record_why_text
    r4 = L01c26890
    r13 = b[r4+5] (u)
    r9 = [r4+120]
    r6 = b[r4+9] (u)
    r7 = b[r4+11] (u)
    r10 = [r5+84]
    r1 = 29883864
    r14 = [r1+36]
    r15 = [r1+0]
    r5 = r0
    r0 = sp + 184
    r1 = r11
    call flash_helpers_level_rate
    if (r6 != 0) {  ; @if.ne.ri.s12
    r1 = b[r4+10] (u)
    r2 = r12 + 1006
    r1 = h[r2+r1<<1] (u)
    } else {
    r1 = 0
    }
    r2 = [sp+68]
    [sp+64] = r2
    r2 = [sp+76]
    [sp+60] = r2
    r2 = [sp+72]
    [sp+56] = r2
    [sp+52] = r8  ; @st.w.sp.l
    [sp+48] = r1
    r1 = sp + 88
    d[sp+40] = r1_r0
    d[sp+32] = r15_r14
    [sp+28] = r13  ; @st.w.sp.l
    [sp+24] = r9  ; @st.w.sp.l
    r0 = 396  #
    [sp+20] = r6
    r1 = 512  #
    [sp+16] = r7
    r0 = 8728  #
    [sp+12] = r0
    [sp+8] = r10  ; @st.w.sp.l
    r4 += r0  #  ; @add.rr.p
    [sp+4] = r5
    r0 = 11141
    r2 = r12 + r0  #
    r0 = [sp+80]
    r0 = r4  #
    [sp] = r0
    r3 = [sp+84]
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
    sp += 188
    {pc, r15-r4} = [sp++]

; fault_record_link_check: 0x02010a8c..0x02010aae, module fault-record (link_check)
.type fault_record_link_check,@function
fault_record_link_check:
    [--sp] = rets
    r1 = 29883900
    r2 = r0  #
    r3 = [r1+0]
    r0 = 1023
    r1 = r3 & r0
    r0 = uextra(r3, p:12, l:4)
    call boundary_hooks_record_pack
    call boundary_hooks_record_store
    pc = [sp++]

; fault_record_fault_age: 0x02010aae..0x02010ade, module fault-record (fault_age)
.type fault_record_fault_age,@function
fault_record_fault_age:
    r2 = L01c26890
    r1 = [r2+560]
    r3 = b[r2+29] (u)
    r0 = 0
    if (r3 == 0) goto L02010adc
    r3 = b[r2+26] (u)
    if (r1 == 0) goto L02010adc
    if (r3 != 0) goto L02010adc
    r2 = [r2+280]
    if (r2 == 0) goto L02010adc
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 - r1
    r0 = r0 * 0xA
L02010adc:
    rts

; fault_record_fault_word: 0x02010ade..0x02010af4, module fault-record (fault_word)
.type fault_record_fault_word,@function
fault_record_fault_word:
    r0 = L01c26890
    r1 = [r0+528]
    r0 = [r0+280]
    r0 = r0.b0 (u)
    r0 <= insert(r1, p:8, l:24)
    rts
