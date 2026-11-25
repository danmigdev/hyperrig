; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; audio_stats: 1 function, 0x0200ffea..0x020103f8

; audio_stats_audio_stats: 0x0200ffea..0x020103f8, module audio-stats (audio_stats)
.type audio_stats_audio_stats,@function
audio_stats_audio_stats:
    [--sp] = {rets, r15-r4}
    sp += -324
    r14 = L01c26890
    r3 = [r14+280]
    r0 = r14 + 4076
    r8 = [r0+0]
    r9 = [r0+4]
    r10 = [r0+8]
    r11 = [r0+12]
    r6 = [r0+16]
    r7 = [r0+20]
    r4 = [r0+24]
    r1 = [r0+28]
    r2 = [r0+56]
    r5 = 1035  #
    r0 = [r0+60]
    r5 = [r14+r5<<2]
    [sp+40] = r5
    r0 = 8728  #
    [sp+36] = r0
    [sp+32] = r2
    [sp+28] = r1
    [sp+24] = r4
    d[sp+16] = r7_r6
    d[sp+8] = r11_r10
    d[sp] = r9_r8
    r9 = r14 + r0
    r0 = 9534
    r1 = L02035810
    r2 = r1 + r0
    r1 = 512
    r0 = r9
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r9
    call command_services_console_send
    r13 = L01c340cc
    r0 = [r13+0]
    [sp+68] = r0
    r3 = [r13+4]
    r10 = [r13+8]
    r11 = [r13+12]
    r15 = [r13+16]
    r6 = [r13+28]
    r7 = [r13+32]
    r0 = [r13+36]
    r1 = [r13+52]
    r2 = [r13+56]
    r5 = [r13+60]
    r4 = r13
    r8 = [++r4=64]
    r12 = [r4+4]
    [sp+44] = r12  ; @st.w.sp.l
    [sp+40] = r8  ; @st.w.sp.l
    [sp+36] = r5
    [sp+32] = r2
    d[sp+24] = r1_r0
    d[sp+16] = r7_r6
    [sp+12] = r15  ; @st.w.sp.l
    r8 = L02035810
    d[sp+4] = r11_r10
    r0 = 10000  #
    [sp] = r3
    r2 = r8 + r0  #
    r3 = [sp+68]
    r1 = 512
    r0 = r9
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r9
    call command_services_console_send
    r7 = [r4+8]
    r10 = [r4+12]
    r11 = [r4+16]
    r5_r4 = 0  #
    r0 = [r4+8]
    if (r0 == 0) goto L0201012c
    r2 = [r13+160]
    r0 = [r13+84]
    r1 = [r13+72]
    r3 = r2 / r1 (u)
    r3 *= r1
    r6 = r2 - r3
    r2 = 31
    goto L02010128
L0201010a:
    r3 = r0 >> r2
    r3 = r3 & 0x1
    r3 <= insert(r6, p:1, l:31)
    r4 = r4 << 1
    ifs (r6 < 0) goto L02010120
    if (r3 < r1) goto L02010124
L02010120:
    r3 = r3 - r1
    r4 |= 1
L02010124:
    r2 += -1
    r6 = r3
L02010128:
    ifs (r2 >= 0) goto L0201010a
L0201012c:
    r0 = 1030
    r6 = [r14+r0<<2]
    call storage_platform_clock  ; @call.xl
    r1 = r0
    call state_queries_tenfold_word
    r2 = r8 + 7952  #
    [sp+20] = r0
    r1 = 512  #
    [sp+16] = r1
    r0 = r9  #
    [sp+12] = r6
    r3 = r7  #
    [sp+8] = r4
    d[sp] = r11_r10
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r9
    call command_services_console_send
    goto L0201018c
L0201016a:
    r0 = r14 + 2120
    r0 = [r0+r5<<2]
    r1 = sp + 296
    [r1+r5<<2] = r0
    r0 = r14 + 2148
    r0 = [r0+r5<<2]
    r1 = sp + 268
    [r1+r5<<2] = r0
    r5 += 1  ; @add.ri.u5
L0201018c:
    if (r5 != 7) goto L0201016a
    r0 = r14 + 292
    r8 = [r0+0]
    r3 = [r0+4]
    r0 = [r0+8]
    [sp+68] = r0
    r0 = [sp+296]
    [sp+64] = r0
    r9 = [sp+268]
    r10 = [sp+300]
    r11 = [sp+272]
    r12 = [sp+304]
    r15 = [sp+276]
    r4 = [sp+308]
    r5 = [sp+280]
    r6 = [sp+312]
    r7 = [sp+284]
    r2 = [sp+316]
    r13 = [sp+288]
    r1 = [sp+320]
    r0 = [sp+292]
    [sp+60] = r3
    [sp+56] = r8  ; @st.w.sp.l
    r0 = 8728  #
    [sp+52] = r0
    r1 = 512  #
    [sp+48] = r1
    [sp+44] = r13  ; @st.w.sp.l
    r13 = L01c340cc
    [sp+40] = r2
    d[sp+32] = r7_r6
    d[sp+24] = r5_r4
    [sp+20] = r15  ; @st.w.sp.l
    r15 = L02035810
    [sp+16] = r12  ; @st.w.sp.l
    d[sp+8] = r11_r10
    [sp+4] = r9  ; @st.w.sp.l
    r4 = r14 + r0
    r0 = 9716
    r2 = r15 + r0  #
    r0 = [sp+64]
    r0 = r4  #
    [sp] = r0
    r3 = [sp+68]
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
    r3 = [r13+136]
    r0 = [r13+140]
    r1 = 1028
    r1 = [r14+r1<<2]
    d[sp] = r1_r0
    r2 = r15 + 5178
    r1 = 512
    r0 = r4
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r4
    call command_services_console_send
    r0 = L01c1f180
    r1 = [r0+48]
    r3 = 16
    if (r1 <= 15) {  ; @if.le.ri.s12
    r3 = [r0+48]
    }
    r0 = 0
    goto L020102aa
L0201027a:
    r1 = r14 + 3056
    r2 = [r1+r0<<2]
    r4 = sp + 204
    [r4+r0<<2] = r2
    r2 = r1 + 64
    r2 = [r2+r0<<2]
    r4 = sp + 140
    [r4+r0<<2] = r2
    r1 = r1 + 128
    r1 = [r1+r0<<2]
    r2 = sp + 76
    [r2+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L020102aa:
    if (r3 != r0) goto L0201027a
    r0 = [r14+412]
    r0 = r0 << 8
    r0 |= r3
    r4 = r0 >> 8
    call preset_application_rate
    r9 = r0  #
    [sp] = r4
    r0 = 8728
    r10 = r14 + r0
    r2 = r15 + 5308
    r5 = r3.b0 (u)
    r1 = 512
    r0 = r10
    r3 = r5
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r10
    call command_services_console_send
    r0 = 1000
    r6 = r9 / r0 (u)
    r9 = sp + 76
    r4 = sp + 140
    r7 = sp + 204
    goto L02010330
L020102fc:
    r0 = [r9++=4]
    r0 = r0 / r6 (u)  #
    r1 = [r7++=4]
    r2 = [r4++=4]
    r0 = r2 / r6 (u)  #
    [sp+4] = r0
    r3 = r1 / r6 (u)  #
    [sp] = r0
    r2 = r15 + 1393
    r1 = 512
    r0 = r10
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r10
    call command_services_console_send
    r5 += -1
L02010330:
    if (r5 != 0) goto L020102fc
    r0 = 8728
    r12 = r14 + r0
    r2 = r15 + 3
    r1 = 512
    r0 = r12
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r12
    call command_services_console_send
    r0 = sp + 72
    r1 = 0
    r10 = 0
    call dsp_dynamics_meter  ; @call.xl
    r5 = r14 + 4100
    r0 = [r5+0]
    call status_helpers_decibels
    r9 = r0  #
    r1 = [r5+0]
    r0 = r1
    call status_helpers_decibels
    r11 = r0  #
    r1 = [r5+4]
    r0 = r1
    call status_helpers_decibels
    r8 = r0  #
    r1 = [r5+4]
    r0 = r1
    call status_helpers_decibels
    r1 = [r5+44]
    r2 = [r5+48]
    r3 = [r5+52]
    r6 = [r5+56]
    r7 = [sp+72]
    r0 = 0x0 - r0  #
    r4 = [r5+60]
    [sp+32] = r4
    d[sp+24] = r7_r6
    d[sp+16] = r3_r2
    [sp+12] = r1
    r1 = 10
    r2 = r0 / r1 (s)
    r2 = r2 * 0xA
    r0 = r0 - r2
    r0 = r8 / r1 (s)  #
    [sp+8] = r0
    r0 = 0x0 - r11  #
    [sp+4] = r0
    r2 = r0 / r1 (s)
    r2 = r2 * 0xA
    r0 = r0 - r2
    r2 = 10099  #
    [sp] = r0
    r2 += r15
    r3 = r9 / r1 (s)
    r1 = 512
    r0 = r12
    call L0200691e
    call state_queries_clamp_count
    r1 = r0
    r0 = r12
    call command_services_console_send
    [r5+4] = r10
    [r5+0] = r10
    [r13+80] = r10
    sp += 324
    {pc, r15-r4} = [sp++]
