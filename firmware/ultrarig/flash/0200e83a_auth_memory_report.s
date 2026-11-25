; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; auth_memory_report: 1 function, 0x0200e83a..0x0200eae6

; auth_memory_report_memory_report: 0x0200e83a..0x0200eae6, module auth-memory-report (memory_report)
.type auth_memory_report_memory_report,@function
auth_memory_report_memory_report:
    [--sp] = {rets, r15-r4}
    sp += -288
    call L0203d862  ; @call.xl
    [sp+188] = r0
    call heap_access_heap_probe
    [sp+184] = r0
    call preset_application_rate
    r12 = L01c26890
    r6 = r12 + 2452
    {r11, r7} = [r6+]
    r8 = r0
    r13 = [r6+8]
    r5 = r7 + r11
    r9 = 0
    r10 = 4042583552
    r4 = r7
    goto L0200e886
L0200e874:
    r1_r0 = d[r4+0]
    if (r1 == r10) {
    r1 = r0 + -16
    r9 = umax(r1, r9)
    }
    r4 += r0  ; @add.rr
L0200e886:
    if (r7 == 0) goto L0200e898
    if (r4 >= r5) goto L0200e898
    r0 = r6
    r1 = r4
    call block_pool_block_ok
    if (r0 != 0) goto L0200e874
    r9 = 0
L0200e898:
    r0 = 617
    r15 = [r12+r0<<2]
    r0 += 9  ; @add.ri.u5
    r10 = [r12+r0<<2]
    if (r8 == 0) goto L0200e8c8
    r0 = [r12+424]
    r1 = [r12+420]
    r0 = r0 * 0x3E8
    r0 = r0 / r8 (u)
    r0 = r1 * 0x3E8  #
    [sp+168] = r0
    r0 = r0 / r8 (u)
    [sp+172] = r0
    goto L0200e8ce
L0200e8c8:
    r0 = 0
    [sp+172] = r0
    [sp+168] = r0
L0200e8ce:
    r0 = 630  #
    r4 = [r6+32]
    r7 = [r12+r0<<2]
    r0 = [r6+28]
    [sp+160] = r0
    r0 = [r6+20]
    [sp+164] = r0
    r0 = [r12+428]
    r0 = r6  #
    [sp+156] = r0
    call console_helpers_pool_check
    r1 = 0x80000000
    if (r0 != 0) goto L0200e902
    r0 = r12 + 2488
    call console_helpers_pool_check
    r1 = 1
    if (r0 != 0) goto L0200e900
    r1 = r0
L0200e900:
    r1 = r1 << 31
L0200e902:
    r0 = 624
    r6 = [r12+r0<<2]
    r0 += -1
    r5 = [r12+r0<<2]
    r2 = r12 + 416
    r0 = [r2+16]
    [sp+148] = r0
    r0 = r7 | r4  #
    r3 = [r2+0]
    r4 = 0
    r14 = 0
    if (r3 != 0) goto L0200e93e
    r2 = [r2+20]
    if (r2 == 0) goto L0200e93e
    r2 = L01c1f180
    r2 = b[r2+3] (u)
    r3 = b[r12+24] (u)
    r2 |= r3
    if ((r2 & 0xFF) == 0) {
    r14 = [r12+440]
    }
L0200e93e:
    r2 = r10 + r15
    r2 = r12 + 444  #
    [sp+144] = r2
    r0 |= r1  #
    r3 = [r2+8]
    r15 = r6  #
    [sp+128] = r3
    r3 = [r2+4]
    [sp+132] = r3
    r2 = [r2+0]
    [sp+136] = r2
    [sp+140] = r0
    [sp+180] = r11  ; @st.w.sp.l
    r11 += r5  #
    [sp+152] = r5
    [sp+176] = r13  ; @st.w.sp.l
    r5 = r6 + r13
    call slot_queries_slots_memory  ; @call.xl
    r8 = r0  #
    r1 = [sp+188]
    r6 = r0 - r5
    r0 = sp + 256
    r12 = r1 - 0x4000
    call console_helpers_memory_buckets
    r7 = r0
    r13 = 0
    goto L0200e994
L0200e988:
    r0 = sp + 256
    r0 = [r0+r4<<2]
    r13 += r0
    r4 += 1  ; @add.ri.u5
L0200e994:
    ifs (r4 < r7) goto L0200e988
    r10 = 0
    b[sp+192] = r10
    if (r8 <= r5) {
    r6 = 0
    }
    r0 = r11 + r14
    r0 += r6  ; @add.rr
    r5 = r12  #
    [sp+124] = r0
    r0 = [sp+188]
    if (r0 <= 16384) {
    r5 = 0
    }
    r4 = 1
    r11 = L02035810
    r12 = L01c26890
    goto L0200ea02
L0200e9c6:
    r0 = r4
    call slot_queries_type_partition  ; @call.xl
    if (r0 == 0) goto L0200ea00
    r1 = sp + 256
    r0 = r4
    r2 = r7
    call slot_queries_type_fits  ; @call.xl
    r3 = r11 + 9  #
    [sp+4] = r0
    [sp] = r4
    if (r10 == 0) {  ; @if.eq.ri.s12
    r3 = r11
    }
    r0 = sp + 192
    r0 += r10
    r1 = 0x40 - r10
    r2 = r11 + 1070
    call L0200691e
    r10 += r0
L0200ea00:
    r4 += 1  ; @add.ri.u5
L0200ea02:
    ifs (r10 > 55) goto L0200ea0a
    ifs (r4 < 40) goto L0200e9c6
L0200ea0a:
    r0 = r11 + 15
    r1 = sp + 192
    if (r10 == 0) {  ; @if.eq.ri.s12
    r1 = r0
    }
    r0 = 1030
    r0 = [r12+r0<<2]
    r2 = [sp+256]
    [sp+120] = r1
    [sp+116] = r13  ; @st.w.sp.l
    if (r7 != 0) goto L0200ea2e
    r2 = r7
L0200ea2e:
    [sp+112] = r2
    r1 = [sp+128]
    [sp+108] = r1
    r1 = [sp+132]
    [sp+104] = r1
    r1 = [sp+136]
    [sp+100] = r1
    [sp+96] = r14  ; @st.w.sp.l
    r1 = [sp+124]
    [sp+92] = r15  ; @st.w.sp.l
    r1 += r5  #  ; @add.rr.p
    r4 = [sp+152]
    [sp+88] = r4
    [sp+84] = r1
    r1 = [sp+148]
    [sp+80] = r1
    r1 = [sp+140]
    [sp+76] = r1
    r1 = [sp+160]
    [sp+72] = r1
    r1 = [sp+156]
    [sp+68] = r1
    r1 = [sp+164]
    [sp+64] = r1
    r1 = [sp+168]
    [sp+60] = r1
    r1 = [sp+172]
    [sp+56] = r1
    r1 = [sp+144]
    [sp+52] = r1
    [sp+48] = r9  ; @st.w.sp.l
    r3 = [sp+176]
    [sp+44] = r3
    r2 = [sp+180]
    [sp+40] = r2
    r1 = ultrarig_bss_size
    [sp+36] = r1
    r1 = ultrarig_ram_image_size
    d[sp+28] = r1_r0
    [sp+24] = r8  ; @st.w.sp.l
    r0 = 0
    [sp+20] = r0
    [sp+16] = r0
    r5 = [sp+184]
    [sp+12] = r5
    r0 = 1
    [sp+8] = r0
    r0 = [sp+188]
    r0 += r2  ; @add.rr
    r0 = r0 - r3
    r0 += r4  ; @add.rr
    r0 = r0 - r15
    r0 = 8728  #
    [sp+4] = r0
    r4 = r12 + r0  #
    [sp] = r5
    r0 = 12695
    r2 = r11 + r0
    r0 = ultrarig_heap_start
    r1 = 29883296
    r3 = r1 - r0
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
    sp += 288
    {pc, r15-r4} = [sp++]
