; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_reports: 2 functions, 0x0200ef92..0x0200f396

; console_reports_level_record: 0x0200ef92..0x0200f1fa, module console-reports (level_record)
.type console_reports_level_record,@function
console_reports_level_record:
    [--sp] = {rets, r9-r4}
    sp += -16
    r8 = L01c26890
    r0 = r8 + 4100
    r6 = [r0+0]
    r5 = [r0+4]
    r7 = 0
    [r0+4] = r7
    [r0+0] = r7
    call status_helpers_flags_set
    r4 = 0
    if (r0 == 0) goto L0200efb4
    r4 = [r8+512]
L0200efb4:
    call dsp_audio_path_cached  ; @call.xl
    r9 = r0
    r0 = r6
    call status_helpers_decibels
    r6 = r8 + 4284
    r0 = r5  #
    [r6+0] = r0
    call status_helpers_decibels
    r5 = r8 + 4120  #
    [r6+4] = r0
    r0 = [r5+24]
    [r6+8] = r0
    r0 = [r5+28]
    [r6+12] = r0
    call effect_setup_total_cost  ; @call.xl
    [r6+16] = r0
    call preset_application_services_budget  ; @call.xl
    [r6+20] = r0
    call slot_queries_slots_memory  ; @call.xl
    r1 = L01c3445c
    r1 = [r1+0]
    d[r6+24] = r1_r0
    r0 = [r8+280]
    [r6+32] = r0
    r0 = [r5+32]
    [r6+36] = r0
    r0 = [r5+36]
    [r6+40] = r0
    call preset_application_services_tempo  ; @call.xl
    r1 = L01c1f180
    r2 = [r1+88]
    [r6+44] = r0
    [r6+48] = r2
    call slot_commands_requested
    [r6+52] = r0
    r0 = [r6+32]
    if (r0 != 2) {  ; @if.ne.ri.s12
    r4 = 0
    }
    [r6+56] = r4
    [r6+60] = r9
    r3 = r8 + 4348  #
    r0 = [r5+0]
    r2 = L01c34468
    r2 = [r2+0]
    r1 = [r1+92]
    [r3+] = {r2, r0}
    [r3+8] = r1
    r0 = b[r8+52] (u)
    [r3+12] = r0
    r0 = sp + 12
    r1 = sp + 8
    call dsp_dynamics_meter  ; @call.xl
    r2 = [sp+8]
    r0 = L02035810
    ifs (r2 >= 16777216) goto L0200f0be
    ifs (r2 < 1) goto L0200f0ba
    r1 = 4294901760
    goto L0200f078
L0200f072:
    r1 = r1 - 0x10000
    r2 = r2 << 1
L0200f078:
    r3 = r2 >> 23
    if (r3 == 0) goto L0200f072
    r2 = r2 - 0x800000
    r3 = r2 >> 19
    r3 = r3 << 2
    r3 += r0  ; @add.rr
    r4 = 2119
    r4 = [r3+r4<<2]
    r5 = 2120
    r3 = [r3+r5<<2]
    r3 = r3 - r4
    r2 = uextra(r2, p:3, l:16)
    r2 *= r3
    r2 = r2 >> 16
    r2 += r4  ; @add.rr
    r1 += r2  ; @add.rr
    r1 = r1 >>> 4
    r2 = 6021
    r1 *= r2
    r1 = r1 - 0x32000
    r2 = 0x64000
    r7 = r1 / r2 (s)
    goto L0200f0be
L0200f0ba:
    r7 = -1440
L0200f0be:
    r1 = r8 + 4364
    r2 = r8 + 4160  #
    [r1+0] = r7
    r3 = [r2+0]
    r3 = 1023  #
    [r1+4] = r3
    r3 = [r8+r3<<2]
    r4 = L01c34440
    r4 = [r4+0]
    r5 = L01c34418
    r5 = [r5+0]
    [r1+8] = r3
    d[r1+12] = r5_r4
    r4 = [r2+8]
    r5 = 0
    [r2+8] = r5
    if (r4 == 0) goto L0200f196
    r1 = 41
L0200f0f4:
    r2 = r1 + 22
    r6 = r4
    r7 = 0
    r7_r6 >>= r2
    r2 = r6 | r7
    r1 += -1
    if (r2 == 0) goto L0200f0f4
    r2 = r1 + 23
    ifs (r2 < 23) {  ; @ifs.lt.ri.s12
    r1 = 0x0 - r1
    r5_r4 <<= r1
    } else {
    r5_r4 >>= r1
    }
    r1 = r4 >> 17
    r1 = r1 & 0x3C
    r6 = r1 + r0
    r0 = 2119
    r0 = [r6+r0<<2]
    r7 = 2120
    r6 = [r6+r7<<2]
    r6 = r6 - r0
    r4 = uextra(r4, p:3, l:16)
    r5_r4 = r6 * r4 (u)
    r5_r4 >>= 16
    r3 = r2 >>> 31
    r3_r2 <<= 16
    r1 = 0
    r6 = r0 + r2
    r7 = r1 + r3 + c
    r2 = r6 + r4
    r3 = r7 + r5 + c
    r3_r2 <<= 1
    r4 = -1
    r6 = r2 - 0x340000
    r7 = r3 + r4 + c
    r2 = 30103
    r4 = r7 * r2
    r3_r2 = r6 * r2 (u)
    r3 += r4  ; @add.rr
    ifs (r7 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r2 + 0x1F40000
    r5 = r3 + r1 + c
    r0 = 0x3E80000
    } else {
    r4 = 0x1F40000 - r2
    r5 = r1 - r3 - !c
    r0 = 4229431296
    }
    r1_r0 = r5_r4 / r0 (s)
    ifs (r0 > -1440) goto L0200f19a
L0200f196:
    r0 = -1440
L0200f19a:
    r4 = r8 + 4384
    [r4+0] = r0
    r1_r0 = d[r8+700]
    r2 = -30
    r0 = r2 - r0
    if (r1 != 0) goto L0200f1ae
    r0 = -180
L0200f1ae:
    r0 = r8 + 72  #
    [r4+4] = r0
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r3 = b[r0+4] (u)
    r1 = r1 << 4
    r1 |= r2  #
    r0 = b[r0+5] (u)
    r2 = r3 << 8
    r1 |= r2
    r0 = r0 << 12
    r0 |= r1
    r3_r2 = 0  #
    [r4+8] = r0
    r0 = b[r8+14] (u)
    [r4+12] = r0
    r0 = 0
    [sp+4] = r0
    [sp] = r0
    r0 = sp + 4
    r1 = sp + 0
    call status_helpers_status_fields
    if (r0 == 0) {  ; @if.eq.ri.s12
    r0 = -1
    } else {
    r0 = [sp]
    }
    r1 = [sp+4]
    d[r4+16] = r1_r0
    r0 = 0
    call status_helpers_counter_words
    [r4+24] = r0
    sp += 16
    {pc, r9-r4} = [sp++]

; console_reports_level_line: 0x0200f1fa..0x0200f396, module console-reports (level_line)
.type console_reports_level_line,@function
console_reports_level_line:
    [--sp] = {rets, r15-r4}
    sp += -240
    r0 = sp + 200
    r1 = 0
    r2 = 40
    r4 = 0
    call effect_enable_memset  ; @call.xl
    r0 = 1094
    r7 = L01c26890
    r0 = [r7+r0<<2]
    r6 = L02035810
    if (r0 == 0) goto L0200f26a
    r0 = 1095
    r4 = [r7+r0<<2]
    r0 = uextra(r4, p:8, l:8)
    call console_reports_type_name  ; @call.xl
    r3 = r4 >> 24
    r5 = r4 & 0xFF0000  #
    [sp+8] = r3
    r2 = r6 + 214
    r1 = r6 + 32
    if (r5 != 65536) {
    r1 = r2
    }
    d[sp] = r1_r0
    r3 = r4.b0 (u)
    r2 = r6 + 2902
    r5 = sp + 200
    r1 = 40
    r0 = r5
    call L0200691e
    r0 = 1094
    r4 = [r7+r0<<2]
L0200f26a:
    r0 = r7 + 4284
    r14 = r7 + 4348  #
    r1 = [r0+0]
    r2 = r4  #
    [sp+196] = r1
    r1 = [r0+4]
    [sp+192] = r1
    r1 = [r0+8]
    [sp+188] = r1
    r1 = [r0+12]
    [sp+184] = r1
    r1 = [r0+16]
    [sp+180] = r1
    r1 = [r0+20]
    [sp+176] = r1
    r1 = [r0+24]
    [sp+172] = r1
    r1 = [r0+28]
    [sp+168] = r1
    r1 = [r0+32]
    [sp+164] = r1
    r1 = [r0+36]
    [sp+160] = r1
    r1 = [r0+40]
    [sp+156] = r1
    r1 = [r0+44]
    [sp+152] = r1
    r1 = [r0+48]
    [sp+148] = r1
    r1 = [r0+52]
    [sp+144] = r1
    r1 = [r0+56]
    [sp+140] = r1
    r9 = [r0+60]
    r11_r10 = d[r14+0]
    r3 = [r14+8]
    r5 = [r14+12]
    r15 = [r14+16]
    r13 = [r14+20]
    r6 = [r14+24]
    r7 = [r14+36]
    r4 = [r14+40]
    r8 = [r14+44]
    r12 = [r14+48]
    r1 = [r14+52]
    r0 = [r14+56]
    r14 = [r14+60]
    [sp+136] = r14  ; @st.w.sp.l
    r0 = uextra(r8, p:12, l:1)  #
    [sp+132] = r0
    [sp+128] = r1
    [sp+124] = r12  ; @st.w.sp.l
    r0 = uextra(r8, p:8, l:4)  #
    [sp+120] = r0
    r0 += 1  ; @add.ri.u5
    r0 = uextra(r8, p:4, l:4)  #
    [sp+116] = r0
    r0 = r8 & 0xF  #
    [sp+112] = r0
    [sp+108] = r0
    [sp+104] = r4
    [sp+100] = r7
    r0 = sp + 200
    [sp+96] = r0
    [sp+92] = r2
    [sp+88] = r6
    [sp+84] = r13  ; @st.w.sp.l
    [sp+80] = r15  ; @st.w.sp.l
    [sp+76] = r5
    [sp+72] = r3
    d[sp+64] = r11_r10
    [sp+60] = r9  ; @st.w.sp.l
    r0 = [sp+140]
    [sp+56] = r0
    r0 = [sp+144]
    [sp+52] = r0
    r0 = [sp+148]
    [sp+48] = r0
    r0 = [sp+152]
    [sp+44] = r0
    r0 = [sp+156]
    [sp+40] = r0
    r0 = [sp+160]
    [sp+36] = r0
    r0 = [sp+164]
    [sp+32] = r0
    r0 = [sp+168]
    [sp+28] = r0
    r0 = [sp+172]
    [sp+24] = r0
    r0 = [sp+176]
    [sp+20] = r0
    r0 = [sp+180]
    [sp+16] = r0
    r0 = [sp+184]
    [sp+12] = r0
    r0 = [sp+188]
    [sp+8] = r0
    r0 = [sp+192]
    r0 = 8728  #
    [sp+4] = r0
    r1 = L01c26890
    r0 += r1  #  ; @add.rr.p
    r3 = [sp+196]
    r1 = 11847  #
    [sp] = r3
    r4 = L02035810
    r2 = r4 + r1
    r1 = 512
    r3 = r4
    call L0200691e
    call state_queries_clamp_count
    sp += 240
    {pc, r15-r4} = [sp++]
