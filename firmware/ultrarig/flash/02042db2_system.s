; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x02042db2..0x02042ddc: data
    .fill ((18 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L02042db2:
    .byte 0x00,0x00
L02042db4:
    .long L0203a233  ; "H4_Controller"
    .long L0204319a
    .long L0204319c
    .long L020431a0
    .long L020431a4
    .long L020431ae
    .long L020431b2
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00

; 0x02042ddc..0x020431c2: system layer code (not reversed), as instructions
L02042ddc:
    [--sp] = {r3, r2}
    [--sp] = {rets, r6-r4}
    sp += -68
    r4 = r1
    r5 = r0
    if (r4 >= 16) goto L02042e42
    r0 = sp + 84
    [sp] = r0
    r0 = 0
    goto L02042e02
L02042df2:
    r1 = [sp]
    r2 = r1 + 4
    [sp] = r2
    r1 = [r1+0]
    r2 = sp + 4
    [r2+r0<<2] = r1
    r0 += 1  ; @add.ri.u5
L02042e02:
    ifs (r0 < r4) goto L02042df2
    r6 = L02039f94  ; "btctrler"
    goto L02042e28
L02042e0e:
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L02042e3a
    call L01c00e62  ; @call.xl
    if (r0 != 0) goto L02042e3a
    r0 = 2
    call L0203feb8  ; @call.xl
L02042e28:
    r3 = sp + 4
    r0 = r6
    r1 = r5
    r2 = r4
    call L02040bae  ; @call.xl
    if (r0 == 21) goto L02042e0e
L02042e3a:
    sp += 68
    {rets, r6-r4} = [sp++]
    sp += 8
    rts
L02042e42:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02042e4e:
    goto L02042e4e
L02042e50:
    [--sp] = rets
    r2 = L01c21374
    r2 = r1  #
    r3 = [r2+0]
    r1 = r0
    r0 = 2
    call r3
    pc = [sp++]
L02042e64:
    [--sp] = rets
    r0 = L01c21370
    r1 = L02042db4
    [r0+0] = r1
    r0 = L02042fee
    r1 = L02039f94  ; "btctrler"
    call phase3_p3_task_create  ; @call.xl
    pc = [sp++]
L02042e88:
    [--sp] = {rets, r4}
    sp += -4
    r0 = 80
    call L0203c15c  ; @call.xl
    [sp] = r0
    if (r0 == 0) goto L02042ede
    call L0203fdba  ; @call.xl
    r0 = L02039f94  ; "btctrler"
    r1 = 4194316
    r3 = sp + 0
    r2 = 1
    r4 = 1
    call L02040bae  ; @call.xl
    r2 = [sp]
    if (r0 == 0) goto L02042ec6
    r0 = r2
    call L0203d218  ; @call.xl
    r4 = 0
    goto L02042ed8
L02042ec6:
    r1 = 0
    r0 = r2
    call L02040d34  ; @call.xl
    r0 = [sp]
    call L0203d218  ; @call.xl
L02042ed8:
    r0 = r4
    sp += 4
    {pc, r4} = [sp++]
L02042ede:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02042eea:
    goto L02042eea
L02042eec:
    r0 = L01c200c4
    r1 = 12
    b[r0+8] = r1
    b[r0+12] = r1
    rts
L02042efa:
    [--sp] = {rets, r4}
    call L02041abe  ; @call.xl
    r4 = L01c21370
    r0 = [r4+0]
    r1 = L01c200ac
    [r1+0] = r1
    [r1+4] = r1
    if (r0 == 0) goto L02042f34
    r1 = [r0+4]
    if (r1 == 0) goto L02042f20
    r0 = 0
    call r1
    r0 = [r4+0]
L02042f20:
    r1 = [r0+8]
    if (r1 == 0) goto L02042f28
    call r1
    r0 = [r4+0]
L02042f28:
    r1 = [r0+16]
    if (r1 == 0) goto L02042f34
    r0 = L02043090
    call r1
L02042f34:
    call L02047154  ; @call.xl
    {pc, r4} = [sp++]
L02042f3c:
    [--sp] = rets
    r3 = L01c21370
    r3 = [r3+0]
    if (r3 == 0) goto L02042f4e
    r3 = [r3+24]
    if (r3 == 0) goto L02042f4e
    call r3
L02042f4e:
    pc = [sp++]
L02042f50:
    [--sp] = {r3, r2}
    [--sp] = rets
    sp += -264
    b[sp+4] = r0
    r2 = sp + 268
    [sp] = r2
    r0 = sp + 4
    r0 |= 2
    call L0202520a  ; @call.xl
    ifs (r0 >= 256) goto L02042f86
    b[sp+5] = r0
    r0 = b[sp+5] (u)
    r2 = r0 + 2
    r1 = sp + 4
    r0 = 4
    call L02042f3c
    sp += 264
    {rets} = [sp++]
    sp += 8
    rts
L02042f86:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02042f92:
    goto L02042f92
L02042f94:
    [--sp] = {r3, r2}
    [--sp] = {rets, r4}
    sp += -264
    r4 = r0
    r0 = 14
    b[sp+4] = r0
    r2 = sp + 272
    [sp] = r2
    r0 = sp + 4
    r0 += 5  ; @add.ri.u5
    call L0202520a  ; @call.xl
    ifs (r0 >= 256) goto L02042fe0
    r0 += 3  ; @add.ri.u5
    b[sp+5] = r0
    r0 = 1
    b[sp+6] = r0
    b[sp+7] = r4
    r0 = r4 >> 8
    b[sp+8] = r0
    r0 = b[sp+5] (u)
    r2 = r0 + 2
    r1 = sp + 4
    r0 = 4
    call L02042f3c
    sp += 264
    {rets, r4} = [sp++]
    sp += 8
    rts
L02042fe0:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02042fec:
    goto L02042fec
L02042fee:
    sp += -56
    call L02042efa
    r6 = sp + 0
    r9 = r6 + 4
    r7 = 4194317
    r8 = L01c21370
    r5 = L01c200ac
    r4 = r7 + -1
    r10 = r4 + -6
L02043012:
    r0 = sp + 0
    call L02041762  ; @call.xl
    if (r0 != 13) goto L02043012
    r0 = [sp]
    if (r0 == r7) goto L02043036
    if (r0 == r4) goto L0204305c
    if (r0 != r10) goto L02043064
    r0 = r9
    call L0204a742  ; @call.xl
    goto L02043064
L02043036:
    r0 = [r8+0]
    r0 = [r0+12]
    call r0
    call L02048a9e  ; @call.xl
    call L02042cbc  ; @call.xl
    r0 = [r6+4]
    call L020403ee  ; @call.xl
    r0 = 20
    call L0203feb8  ; @call.xl
    goto L02043064
L0204305c:
    r0 = [r6+4]
    call L020403ee  ; @call.xl
L02043064:
    r0 = r5
    call phase3_p11_thread_run  ; @call.xl
    goto L02043012
L0204306e:
    r0 = 0
    rts
L02043072:
    r0 = 0
    rts
L02043076:
    r0 = 0
    rts
L0204307a:
    [--sp] = rets
    r0 = L02039f94  ; "btctrler"
    r1 = 255
    r3_r2 = 0
    call L02040bae  ; @call.xl
    r0 = 0
    pc = [sp++]
L02043090:
    [--sp] = {rets, r6-r4}
    r5 = r2
    r4 = r1
    if (r0 == 2) goto L020430d2
    if (r0 != 1) goto L020430f0
    ifs (r5 >= 255) goto L020430f2
    r0 = 8
    r0 = [r0+0]
    r1 = r5 + 2
    call phase3_p11_lbuf_alloc_btctrler  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L020430f0
    r1 = r4  #
    h[r6+0] = r5
    r0 = r6 + 2
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r6
    call L02025b80  ; @call.xl
    r0 = 24
    call L02025bba  ; @call.xl
    {pc, r6-r4} = [sp++]
L020430d2:
    r1 = 0
    r0 = r4
    call L020259d0  ; @call.xl
    r0 = r0 & 0xFFFF0FFF
    call L0204727c  ; @call.xl
    if (r0 == 0) goto L020430f0
    r0 = r4
    call L0204a996  ; @call.xl
L020430f0:
    {pc, r6-r4} = [sp++]
L020430f2:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020430fe:
    goto L020430fe
L02043100:
    [--sp] = rets
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204310e:
    goto L0204310e
L02043110:
    [--sp] = {r3, r2}
    [--sp] = {rets, r6-r4}
    sp += -24
    r2 = sp + 40
    [sp] = r2
    [sp+20] = r2
    [sp+4] = r0
    r0 = 1
    goto L02043132
L02043122:
    r2 = [sp+20]
    r3 = r2 + 4
    [sp+20] = r3
    r2 = [r2+0]
    r3 = sp + 4
    [r3+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L02043132:
    ifs (r0 <= r1) goto L02043122
    r4 = r1 + 1
    r5 = L02039f94  ; "btctrler"
    r6 = 4194305
    goto L02043170
L02043146:
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L02043182
    call L01c00e62  ; @call.xl
    if (r0 != 0) goto L02043182
    call L0204178c  ; @call.xl
    r1 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L02043182
    r0 = 2
    call L0203feb8  ; @call.xl
L02043170:
    r3 = sp + 4
    r0 = r5
    r1 = r6
    r2 = r4
    call L02040bae  ; @call.xl
    if (r0 == 21) goto L02043146
L02043182:
    sp += 24
    {rets, r6-r4} = [sp++]
    sp += 8
    rts
L0204318a:
    [--sp] = rets
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02043198:
    goto L02043198
L0204319a:
    rts
L0204319c:
    r0 = 0
    rts
L020431a0:
    r0 = 0
    rts
L020431a4:
    r1 = L01c21374
    [r1+0] = r0
    rts
L020431ae:
    r0 = 0
    rts
L020431b2:
    [--sp] = rets
    r0 = r0.b0 (u)
    r2 = r2.l (u)
    call L02052024  ; @call.xl
    r0 = 0
    pc = [sp++]

; 0x020431c2..0x020431ec: data
    .fill ((2 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L020431c2:
    .byte 0x00,0x00
L020431c4:
    .long L0203593e  ; "ble"
    .long L02045f08
    .byte 0x00,0x00,0x00,0x00
    .long L02045fbe
    .long L02046000
    .long L0204609e
    .long L02046222
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00

; 0x020431ec..0x02045234: system layer code (not reversed), as instructions
L020431ec:
    [--sp] = {rets, r8-r4}
    r7 = 195712
    [r7+0] |= 0x1
    r8 = 1
    r6 = 0x28000
    [r6+0] = r8
    r0 = 2305
    [r6+52] = r0
    call L0203e3bc  ; @call.xl
    r4 = r0
    r5 = L01c21450
    [r5+0] = r4
    if (r4 != 0) goto L02043236
    r0 = 5740
    call L0203c15c  ; @call.xl
    r4 = r0
    [r5+0] = r4
    r0 = L01c21455
    b[r0+0] = r8
    if (r4 == 0) goto L0204331a
L02043236:
    r1 = 0
    r2 = 5740
    r0 = r4
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 36
    r0 = r4 + 64  #
    [r4+16] = r0
    r0 = r4 + 700  #
    [r4+20] = r0
    r5 = r4 + 2205  #
    [r4+24] = r0
    [r4+28] = r5
    r1 = r4 + 5740  #
    [r7+4] = r4
    r1 = 1505  #
    [r7+60] = r1
    call L02025038  ; @call.xl
    r1 = 357
    r4 = L01c26890
    [r4+r1<<2] = r0
    r1 = 3535
    r0 = r5
    call L02025038  ; @call.xl
    r1 = 358
    [r4+r1<<2] = r0
    r2 = L02045472
    r0 = 45
    r1 = 2
    r3 = 0
    call storage_platform_register  ; @call.xl
    r2 = L02045cd2
    r0 = 29
    r1 = 2
    r3 = 0
    call storage_platform_register  ; @call.xl
    [r6+0] |= 0x2000
    [r6+0] |= 0x4000
    [r6+0] &= 0xFFFFFFEF
    r1 = -1024  #
    r0 = [r6+8]
    r0 &= r1
    r0 = r0 | 0x46
    [r6+8] = r0
    [r6+8] |= 0xF000
    r0 = [r6+12]
    r0 &= r1
    r0 = r0 | 0x46
    [r6+12] = r0
    r0 = [r6+16]
    r0 = r0 & 0xFFFFFF00
    r0 = r0 | 0x3E
    [r6+16] = r0
    r0 = [r6+16]
    r0 = r0 & 0xFFFF00FF
    r0 = r0 | 0x3E00
    [r6+16] = r0
    r0 = [r6+20]
    r0 = r0 & 0xFFFFFF00
    r0 = r0 | 0x1E
    [r6+20] = r0
    r0 = [r6+24]
    r0 = r0 & 0xFFFFFF00
    r0 = r0 | 0x14
    [r6+24] = r0
    r0 = [r6+24]
    r0 = r0 & 0xFFFF00FF
    r0 = r0 | 0x1400
    [r6+24] = r0
    {pc, r8-r4} = [sp++]
L0204331a:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02043326:
    goto L02043326
L02043328:
    [--sp] = rets
    r1 = r0 + 24
    r0 = 1
    call L0202541c  ; @call.xl
    if (r0 == 0) goto L0204333e
    r1 = 0
    r2 = r0
    rep 5 {
    [r2++=4] = r1
    }
L0204333e:
    pc = [sp++]
L02043340:
    r2 = h[r0+326] (u)
    r0 += 94
    if (r1 == 0) goto L02043358
    r3 = r1 & 0xFFFFFF1F
    r2 = r2 & 0xFFFFE0FF
    r2 <= insert(r3, p:8, l:5)
    h[r0+232] = r2
L02043358:
    if ((r2 & 0x2000) == 0) {
    h[r0+2] = r1
    h[r0+0] = r1
    }
    rts
L02043362:
    [--sp] = {rets, r11-r4}
    sp += -332
    r10 = r1
    r5 = r0
    r0 = 0
    r1 = 0
    d[sp+324] = r1_r0
    d[sp+316] = r1_r0
    r0 = sp + 28
    r2 = 275
    call effect_enable_memset  ; @call.xl
    r7 = r10 + 16
    r0 = h[r7+0] (u)
    r0 = uextra(r0, p:4, l:2)
    b[sp+27] = r0
    r6 = r5 + 432
    r0 = b[r6+1] (u)
    if (r0 == 0) goto L02043476
    call storage_coordination_irq_enter  ; @call.xl
    r8 = L01c1fa24
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    r9 = L01c1fa20
    if (r1 != 0) goto L020433c4
    csync
L020433bc:
    testset b[r9]
    ifeq goto L020433bc
    csync
L020433c4:
    r0 = [r6+4]
    b[sp+303] = r0
    r1 = r0 >> 8
    b[sp+304] = r1
    r1 = r0 >> 16
    b[sp+305] = r1
    r0 = r0 >> 24
    b[sp+306] = r0
    r4 = r5 + 340  #
    r0 = b[r6+2] (u)
    b[sp+307] = r0
    r2 = b[r4+3] (u)
    r1 = sp + 303
    if (r2 == 6) {  ; @if.eq.ri.s12
    r0 |= 128
    b[r1+4] = r0
    }
    r1 = sp + 303
    r0 = r1 + 5
    r2 = r4 + 104
    rep 8 {
    r3 = b[r2++=1] (u)
    b[r0++=1] = r3
    }
    r11 = 0  #
    r0 = b[r7+2] (u)
    [sp+20] = r11  ; @st.w.sp.l
    r2 = 4
    [sp+16] = r2
    r2 = sp + 316
    [sp+12] = r2
    r2 = sp + 28
    [sp+8] = r2
    r5 = r7 + 4
    r0 = r4 + 112  #
    [sp+4] = r0
    r2 = sp + 27
    r3 = 1
    [sp] = r5
    call L02028206  ; @call.xl
    [r4+96] += 1  ; @rmw.add.s12
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L02043448
    csync
    b[r9+0] = r11
L02043448:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = [r6+4]
    if (r0 == -1) goto L0204347a
    r0 = r5  #
    r6 = b[r7+2] (u)
    r1 = sp + 28
    r2 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r10 + r6
    r0 += 20  ; @add.ri.u5
    r1 = sp + 316
    rep 4 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = r6 + 4
    b[r7+2] = r0
L02043476:
    sp += 332
    {pc, r11-r4} = [sp++]
L0204347a:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02043486:
    goto L02043486
L02043488:
    [--sp] = {rets, r4}
    r3 = h[++r1=16] (u)
    r4 = r3 & 0xF
    r3 = r3 >> 2
    r3 = r3 & 0x30
    r3 |= r4
    if (r2 == 0) goto L020434be
    h[r0+24] = r3
    r2 = h[r0+28] (u)
    r2 = r2 & 0x4  #
    r3 = b[r1+2] (u)
    r2 <= insert(r3, p:8, l:24)  #
    r1 = h[r1+0] (u)
    r3 = r1 >> 6
    r3 = r3 & 0x8
    r2 |= r3
    r1 = uextra(r1, p:4, l:2)
    r1 |= r2
    h[r0+28] = r1
    {pc, r4} = [sp++]
L020434be:
    h[r0+22] = r3
    r2 = h[r0+26] (u)
    r2 = r2 & 0x4  #
    r3 = b[r1+2] (u)
    r2 <= insert(r3, p:8, l:24)  #
    r1 = h[r1+0] (u)
    r3 = r1 >> 6
    r3 = r3 & 0x8
    r2 |= r3
    r1 = uextra(r1, p:4, l:2)
    r1 |= r2
    h[r0+26] = r1
    {pc, r4} = [sp++]
L020434e0:
    [--sp] = {rets, r10-r4}
    r9 = r1
    r5 = r0
    r0 = r1 << 2
    r4 = r5 + r0
    r1 = [++r4=392]
    r10 = r5 + 400
    if (r2 == 0) goto L020435c4
    r8 = r5 + 488
    if (r1 == 0) goto L02043520
    r0 = [r8+4]
    if (r0 == 0) goto L0204350c
    r2 = [r0+8]
    if (r2 == 0) goto L0204350c
    r0 = [r8+0]
    call r2
    r1 = [r4+0]
L0204350c:
    r2 = [r1+12]
    if (r2 == 0) goto L02043518
    r0 = [r8+0]
    call r2
    r1 = [r4+0]
L02043518:
    r0 = r1
    call phase3_p11_hw_dma_free  ; @call.xl
L02043520:
    r0 = 521
    r0 = b[r5+r0] (u)
    r6 = 0
    if (r0 != 0) goto L02043538
    r0 = r10 + 16
    call phase3_p11_hw_dma_pop  ; @call.xl
    r6 = r0
L02043538:
    if (r6 != 0) goto L02043550
    r0 = 520
    r0 = b[r5+r0] (u)
    if (r0 != 0) goto L02043550
    r0 = r10 + 24
    call phase3_p11_hw_dma_pop  ; @call.xl
    r6 = r0
L02043550:
    r7 = r5 + 96
    if (r6 == 0) goto L020435ee
    r1 = [r10+24]
    r2 = r10 + 24
    r0 = 1
    if (r1 == r2) {
    r0 = 0
    }
    r1 = h[r6+16] (u)
    r1 &= 4294966783
    r1 <= insert(r0, p:9, l:1)
    r0 = r5  #
    h[r6+16] = r1
    r1 = r6
    call L02043362
    [r4+0] = r6
    r0 = [r10+r9<<2]
    r2 = b[r6+18] (u)
    r0 += 20  ; @add.ri.u5
    r1 = r6 + 20
    call effect_parameter_support_memmove  ; @call.xl
    r0 = r5
    r1 = r6
    r2 = r9
    call L02043488
    r0 = h[r7+2] (u)
    r1 = h[r6+16] (u)
    r0 &= 4294967231
    r1 = r1 >> 3
    r1 = r1 & 0x40
    r2 = r1 | r0
    r1 = r7 + 4
    r0 = r7 + 5
    h[r7+2] = r2
    if (r9 == 0) {  ; @if.eq.ri.s12
    r0 = r1
    }
    r1 = b[r0+0] (u)
    r1 &= 4294967294
    b[r0+0] = r1
    r1 = [r6+8]
    if (r1 == 0) goto L020435ec
    r0 = [r8+0]
    call r1
    {pc, r10-r4} = [sp++]
L020435c4:
    if (r1 == 0) goto L020435ec
    r0 = h[r1+16] (u)
    if ((r0 & 512) != 0) goto L020435ec
    r3 = [r10+24]
    r4 = r10 + 24
    r2 = 1
    if (r3 == r4) {
    r2 = 0
    }
    r0 &= 4294966783
    r0 <= insert(r2, p:9, l:1)
    r0 = r5  #
    h[r1+16] = r0
    r2 = r9
    call L02043488
L020435ec:
    {pc, r10-r4} = [sp++]
L020435ee:
    r0 = h[r7+2] (u)
    r0 &= 4294967231
    h[r7+2] = r0
    [r4+0] = 0x0
    {pc, r10-r4} = [sp++]
L020435fa:
    [--sp] = {rets, r9-r4}
    sp += -4
    r4 = r0
    r6 = [r4+0]
    if (r6 == 0) goto L0204372e
    r0 = 343
    r0 = b[r6+r0] (u)
    r0 &= 4294967294
    if (r0 != 6) goto L0204372e
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    r9 = L01c1fa20
    if (r1 != 0) goto L02043640
    csync
L02043638:
    testset b[r9]
    ifeq goto L02043638
    csync
L02043640:
    csync
    r0 = [r6+512]
    if (r0 != 1) goto L0204366a
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02043662
    csync
    r0 = 0
    b[r9+0] = r0
L02043662:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204372e
L0204366a:
    r8 = r6 + 512
    r1 = 1
    r7 = 1
    r0 = r8
    call phase3_p11_atomic_set  ; @call.xl
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02043692
    csync
    r0 = 0
    b[r9+0] = r0
L02043692:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = r6 + 100  #
    r0 = h[r6+14] (u)
    r0 = r0 & 0x1  #
    r2 = b[r1+0] (u)
    r2 = r2 << 1
    r2 = r2 & 0x2  #
    r3 = b[r1+1] (u)
    r0 |= r2
    r2 = r3 << 2
    r2 = r2 & 0x4
    r0 |= r2
    b[sp+2] = r0
    r2 = h[r6+14] (u)
    r2 = r2 & 0x1  #
    r3 = b[r1+0] (u)
    r3 = r3 << 1
    r3 = r3 & 0x2  #
    r1 = b[r1+1] (u)
    r2 |= r3
    r1 = r1 << 2
    r1 = r1 & 0x4
    r1 |= r2
    r0 ^= r1
    b[sp+3] = r1
    if (r0 > 7) goto L020436ec
    r1 = 138
    r1 = r1 & (1 << r0)
    if (r1 != 0) goto L020436ee
    r1 = 80
    r0 = r1 & (1 << r0)
L020436ec:
    r7 = 0
L020436ee:
    r0 = sp + 2
    r0 |= r7
    r5 = b[r0+0] (u)
    r6 = r5 & 0xFFFFFF01  #
    r0 = [r4+0]
    r1 = r6 + 1
    r1 = r5 >> r1
    r2 = r1 & 0x1
    r1 = r6
    call L020434e0
    r1 = 2
    if ((r5 & 0x1) != 0) {
    r1 = 1
    }
    r1 = r5 >> r1  #
    r0 = [r4+0]
    r2 = r1 & 0x1
    r1 = r6 ^ 0x1
    call L020434e0
    r1 = 0
    r0 = r8
    call phase3_p11_atomic_set  ; @call.xl
L0204372e:
    sp += 4
    {pc, r9-r4} = [sp++]
L02043732:
    r1 = r1 + 352
    if (r0 != 0) goto L0204373e
    r0 = h[r1+0] (u)
    if (r0 >= r2) goto L02043740
L0204373e:
    h[r1+0] = r2
L02043740:
    rts
L02043742:
    [--sp] = {rets, r6-r4}
    sp += -16
    r0 = 0xFFFFFFFF  ; @li.modimm
    r1 = r0
    d[sp+8] = r1_r0
    d[sp] = r1_r0
    r2 = 0
    r3 = L01c20236
    r4 = 0
    r1_r0 = 0
    goto L0204378e
L02043762:
    r5 = r4 + r3
    r5 = b[r5+16] (u)
    if (r5 == 0) goto L0204378a
    r5 = r3 + 64
    r5 = h[r5+r4<<1] (u)
    if (r5 == 0) goto L02043780
    r5 = r1.b0 (u)
    r6 = sp + 0
    b[r6+r5] = r2
    r1 += 1  ; @add.ri.u5
    goto L0204378a
L02043780:
    r5 = r0.b0 (u)
    r6 = sp + 8
    b[r6+r5] = r2
    r0 += 1  ; @add.ri.u5
L0204378a:
    r2 += 1  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L0204378e:
    if (r4 != 8) goto L02043762
    if ((r0 & 0xFF) == 0) goto L0204379e
    if ((r1 & 0xFF) != 0) goto L020437c0
L0204379e:
    r1 = r1.b0 (u)
    if (r1 >= 2) goto L020437c0
    if (r1 != 1) goto L020437ae
    r0 = b[sp] (u)
    goto L020437ba
L020437ae:
    r0 = r0.b0 (u)
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = -1
    } else {
    r0 = b[sp+8] (u)
    }
L020437ba:
    r0 = r0.b0 (u)
    sp += 16
    {pc, r6-r4} = [sp++]
L020437c0:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020437cc:
    goto L020437cc
L020437ce:
    r1 = L01c21450
    r1 = [r1+0]
    r1 = [r1+16]
    r0 = r0 - r1
    r1 = 28
    r0 = r0 / r1 (s)
    r0 = r0.b0 (u)
    rts
L020437e4:
    [--sp] = {rets, r5, r4}
    r3_r2 = r1_r0
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r4 = r1 + 1
    [r5+r0<<2] = r4
    r4 = L01c1fa20
    if (r1 != 0) goto L02043814
    csync
L0204380c:
    testset b[r4]
    ifeq goto L0204380c
    csync
L02043814:
    r3 = r3 << 10
    r0 = r2
    call L020437ce
    r0 = r0 << 4
    r0 |= r3
    r0 |= 2
    r1 = 163868
    [r1+0] = r0
    csync
    r3 = [r1+8]
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02043842
    csync
    r0 = 0
    b[r4+0] = r0
L02043842:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r5, r4} = [sp++]
L0204384c:
    [--sp] = {rets, r7-r4}
    r3 = r1
    r4 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fa24
    r0 = cnum
    r1 = [r6+r0<<2]
    r5 = r1 + 1
    [r6+r0<<2] = r5
    r5 = L01c1fa20
    if (r1 != 0) goto L0204387e
    csync
L02043876:
    testset b[r5]
    ifeq goto L02043876
    csync
L0204387e:
    r7 = 163868
    [r7+4] = r2
    csync
    r2 = r3 << 10
    r0 = r4
    call L020437ce
    r0 = r0 << 4
    r0 |= r2
    r0 = r0 | 0x5
    [r7+0] = r0
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020438ae
    csync
    r0 = 0
    b[r5+0] = r0
L020438ae:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r7-r4} = [sp++]
L020438b6:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = 348  #
    r0 = [r4+0]
    r2 = 1
    b[r0+r1] = r2
    r1 = 2
    r0 = r4
    call L020437e4
    r1 = 63487
    r2 = r0 & r1
    r1 = 2
    r0 = r4
    call L0204384c
    {pc, r4} = [sp++]
L020438de:
    [--sp] = {rets, r5, r4}
    r2 = r0
    r3 = [r2+0]
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r4 = r1 + 1
    [r5+r0<<2] = r4
    r4 = L01c1fa20
    if (r1 != 0) goto L02043910
    csync
L02043908:
    testset b[r4]
    ifeq goto L02043908
    csync
L02043910:
    r0 = 347
    r0 = b[r3+r0] (u)
    if (r0 == 0) goto L02043932
    r0 = r2
    call L020438b6
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02043948
    csync
    goto L02043944
L02043932:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02043948
    csync
L02043944:
    r0 = 0
    b[r4+0] = r0
L02043948:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L02043950:
    [--sp] = {rets, r10-r4}
    r8 = r0  #
    r5 = [r0+0]
    r0 = h[r5+510] (u)
    r9 = r3  #
    r6 = [sp+36]
    r10 = r2
    r4 = r1
    ifs (r0 < r6) goto L020439da
    r0 = 27
    call L02043328
    r7 = r0
    if (r7 == 0) goto L020439da
    r2 = r7  #
    r1 = [sp+32]
    r0 = 0
    rep 5 {
    [r2++=4] = r0
    }
    r0 = r9 << 4  #
    [r7+8] = r4
    [r7+12] = r10
    r0 = r0 & 0x30
    r2 = r6  #
    h[r7+16] = r0
    b[r7+18] = r6
    r0 = r7 + 20
    call effect_parameter_support_memmove  ; @call.xl
    call phase3_p11_low_power_exit_request  ; @call.xl
    r0 = r5 + 416
    r1 = r7
    call phase3_p11_hw_dma_push  ; @call.xl
    r1 = 30
    r0 = r5
    call L02043340
    r0 = r8
    call L020435fa
    r0 = 0
    r2 = 2
    r1 = r5
    call L02043732
    call L02043742
    if (r0 != 255) goto L020439d8
    r0 = 354
    r0 = b[r5+r0] (u)
    if (r0 != 0) goto L020439d8
    r0 = r8
    call L020438de
L020439d8:
    {pc, r10-r4} = [sp++]
L020439da:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020439e6:
    goto L020439e6
L020439e8:
    [--sp] = {rets, r4}
    r3 = h[r0+6] (u)
    r3 |= 8
    h[r0+6] = r3
    r3 = 1
    if (r1 != 0) goto L020439f6
    r3 = r1
L020439f6:
    r1 = 368
    b[r0+r1] = r3
    r1 = r0 + 369
    r3 = r2
    rep 6 {
    r4 = b[r3++=1] (u)
    b[r1++=1] = r4
    }
    r1 = b[r2+1] (u)
    r3 = b[r2+0] (u)
    r3 <= insert(r1, p:8, l:24)
    h[++r0=82] = r3
    r1 = b[r2+3] (u)
    r3 = b[r2+2] (u)
    r3 <= insert(r1, p:8, l:24)
    h[r0+2] = r3
    r1 = b[r2+5] (u)
    r2 = b[r2+4] (u)
    r2 <= insert(r1, p:8, l:24)
    h[r0+4] = r2
    {pc, r4} = [sp++]
L02043a2c:
    [--sp] = {rets, r4}
    r3 = 1
    if (r1 != 0) goto L02043a34
    r3 = r1
L02043a34:
    r1 = 375
    b[r0+r1] = r3
    r1 = r0 + 376
    r3 = r2
    rep 6 {
    r4 = b[r3++=1] (u)
    b[r1++=1] = r4
    }
    r1 = b[r2+1] (u)
    r3 = b[r2+0] (u)
    r3 <= insert(r1, p:8, l:24)
    h[++r0=76] = r3
    r1 = b[r2+3] (u)
    r3 = b[r2+2] (u)
    r3 <= insert(r1, p:8, l:24)
    h[r0+2] = r3
    r1 = b[r2+5] (u)
    r2 = b[r2+4] (u)
    r2 <= insert(r1, p:8, l:24)
    h[r0+4] = r2
    {pc, r4} = [sp++]
L02043a6a:
    [--sp] = {rets, r6-r4}
    r4 = r2  #
    r6 = [r0+0]
    r5 = r1
    r1 = 5
    r2 = r5
    call L0204384c
    h[r6+358] = r5
    r0 = r4 + 1
    r1 = 356
    b[r6+r1] = r0
    {pc, r6-r4} = [sp++]
L02043a8a:
    h[r0+34] = r2
    r3 = r2 >> 16
    h[r0+36] = r3
    h[r0+274] = r1
    [r0+336] = r2
    rts
L02043a9e:
    [--sp] = {rets, r9-r4}
    r9_r8 = 0
    r3 = 0
L02043aa4:
    r5 = r3 << 1
    r6 = r5 + 2
    r5 = r3
L02043aaa:
    ifs (r3 >= 37) goto L02043af6
    if (r3 == 0) goto L02043aba
    if (r3 == 11) {  ; @if.eq.ri.s12
    r9 = 2
    }
    goto L02043abc
L02043aba:
    r9 = 0
L02043abc:
    r2 = r0 + r3
    b[r2+104] = r5
    r7 = r9 + r6
    b[r2+184] = r7
    r2 = r3 >>> 3
    r2 = b[r1+r2] (u)
    r4 = r3 & 0x7
    r5 += 1  ; @add.ri.u5
    r6 += 2  ; @add.ri.u5
    r2 = r2 & (1 << r4)
    r3 += 1  ; @add.ri.u5
    if (r2 == 0) goto L02043aaa
    r2 = r0 + r8
    r4 = r5 + -1
    b[r2+144] = r4
    b[r2+224] = r7
    r8 = r8 + 1
    goto L02043aa4
L02043af6:
    r3 = 0
    r4 = L020357fc
    r5 = 261
    goto L02043b20
L02043b04:
    r2 = b[r3+r4] (u)
    r6 = r0 + r3
    r7 = r3 + 37
    b[r6+141] = r7
    b[r6+221] = r2
    b[r6+181] = r7
    b[r6+r5] = r2
    r3 += 1  ; @add.ri.u5
L02043b20:
    if (r3 != 3) goto L02043b04
    r2 = b[r1+1] (u)
    r3 = b[r1+0] (u)
    r3 <= insert(r2, p:8, l:24)
    r2 = r0 + 46
    h[r2+0] = r3
    r3 = b[r1+3] (u)
    r4 = b[r1+2] (u)
    r4 <= insert(r3, p:8, l:24)
    h[r2+2] = r4
    r1 = b[r1+4] (u)
    r1 = r1 & 0xFFFFFF1F
    r1 <= insert(r8, p:5, l:27)
    h[r2+4] = r1
    r0 = r0 + 612  #
    r1 = h[r2+0] (u)
    h[r0+0] = r1
    r1 = h[r2+2] (u)
    h[r0+2] = r1
    r1 = h[r2+4] (u)
    h[r0+4] = r1
    {pc, r9-r4} = [sp++]
L02043b5a:
    [--sp] = {rets, r6-r4}
    r5_r4 = r1_r0
    r1 = 7
    r2 = 0
    call L0204384c
    r1 = 0
    r2 = 0
    r0 = r4
    call L0204384c
    r1 = 14
    r2 = 0
    r0 = r4
    call L0204384c
    r6 = r5 + -1
    if (r5 != 0) goto L02043b82
    r6 = r5
L02043b82:
    r2 = r6.l (u)
    r1 = 0
    r0 = r4
    call L0204384c
    r0 = r6 >> 16
    r2 = r0 | 0x8000
    r1 = 14
    r0 = r4
    call L0204384c
    {pc, r6-r4} = [sp++]
L02043b9c:
    [--sp] = {rets, r5, r4}
    r4 = [r0+0]
    r4 = r4 + 342
    b[r4+1] = r1
    h[r4+8] = r3
    b[r4+5] = r2
    r5 = 0
    r1 = r1 << 12
    r2 = r2 << 11
    r1 |= r2  #
    b[r4+6] = r5
    r2 = r1 | r3
    r1 = 2
    call L0204384c
    {pc, r5, r4} = [sp++]
L02043bc0:
    [--sp] = rets
    if (r1 == 0) {  ; @if.eq.ri.s12
    r1 = 4
    r2 = 0
    } else {
    r2 = r1 | 0x8000
    r1 = 4
    }
    call L0204384c
    pc = [sp++]
L02043bd6:
    r2 = 625
    r3 = r1 / r2 (s)
    h[r0+72] = r3
    r2 *= r3
    r2 = r1 - r2
    r2 = r2 | 0x5000
    h[r0+74] = r2
    [r0+328] = r1
    rts
L02043bf4:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = [++r4=20]
    if (r5 == 0) goto L02043c6a
    call phase3_p11_low_power_hw_unsleep_lock  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L02043c30
    csync
L02043c28:
    testset b[r0]
    ifeq goto L02043c28
    csync
L02043c30:
    r3_r2 = d[r5+0]
    [r2+4] = r3
    [r3+0] = r2
    [r5+0] = r5
    [r5+4] = r5
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02043c52
    csync
    r1 = 0
    b[r0+0] = r1
L02043c52:
    call storage_coordination_irq_leave  ; @call.xl
    call phase3_p11_low_power_hw_unsleep_unlock  ; @call.xl
    r0 = r5
    call L0203d218  ; @call.xl
    [r4+0] = 0x0
L02043c6a:
    {pc, r5, r4} = [sp++]
L02043c6c:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r0 = 20
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02043cf2
    r0 = L020431c4
    [r5+16] = r0
    [r5+8] = r4
    r0 = 0
    b[r5+12] = r0
    call phase3_p11_low_power_hw_unsleep_lock  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L02043cbc
    csync
L02043cb4:
    testset b[r0]
    ifeq goto L02043cb4
    csync
L02043cbc:
    r2 = L01c1fa30
    r3 = [r2+4]
    [r2+4] = r5
    d[r5+0] = r3_r2
    [r3+0] = r5
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02043ce2
    csync
    r1 = 0
    b[r0+0] = r1
L02043ce2:
    call storage_coordination_irq_leave  ; @call.xl
    call phase3_p11_low_power_hw_unsleep_unlock  ; @call.xl
    [r4+20] = r5
    {pc, r5, r4} = [sp++]
L02043cf2:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02043cfe:
    goto L02043cfe
L02043d00:
    [--sp] = rets
    r1 = 8
    r2 = 0
    call L0204384c
    pc = [sp++]
L02043d0c:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r5 = r2  #
    r0 = [r4+0]
    if (r0 == 0) goto L02043d1a
    [r0+364] = r1
L02043d1a:
    r0 = 625
    r6 = r1 / r0 (s)
    r2 = r6.l (u)
    r1 = 1
    r0 = r4
    call L0204384c
    r0 = r6 >>> 16
    r1 = r5 << 15
    r2 = r1 | r0
    r1 = 15
    r0 = r4
    call L0204384c
    {pc, r6-r4} = [sp++]
L02043d3e:
    [--sp] = {r3, r2}
    [--sp] = {rets, r12-r4}
    sp += -4
    r5 = r0
    r0 = sp + 44
    [sp] = r0
    if (r1 > 23) goto L02044246
    r4 = [r5+0]
    r2 = r1 << 1
    r9 = L01c21450
    r6 = r4 + 60
    r12 = r4 + 340
    r11 = r4 + 356
    r0 = r4 + 432
    r7 = r4 + 608
    tbh [r2]
L02043d70:
    .short (L02043da0 - L02043d70) / 2, (L02043db4 - L02043d70) / 2, (L02043dc8 - L02043d70) / 2, (L02043ef8 - L02043d70) / 2, (L02043de0 - L02043d70) / 2, (L02043e00 - L02043d70) / 2, (L02043f10 - L02043d70) / 2, (L02043ff4 - L02043d70) / 2
    .short (L0204402a - L02043d70) / 2, (L02043e18 - L02043d70) / 2, (L02043e6a - L02043d70) / 2, (L0204403a - L02043d70) / 2, (L02044246 - L02043d70) / 2, (L02044052 - L02043d70) / 2, (L02044246 - L02043d70) / 2, (L0204409a - L02043d70) / 2
    .short (L02044246 - L02043d70) / 2, (L020440a8 - L02043d70) / 2, (L020440ba - L02043d70) / 2, (L02043e82 - L02043d70) / 2, (L02043e9e - L02043d70) / 2, (L020440cc - L02043d70) / 2, (L02043ebe - L02043d70) / 2, (L02043ee4 - L02043d70) / 2
L02043da0:
    r0 = [sp]
    r1 = r0 + 4
    r1 = r12 + 104  #
    [sp] = r1
    r0 = [r0+0]
    rep 8 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    goto L02044246
L02043db4:
    r0 = [sp]
    r1 = r0 + 4
    r1 = r12 + 112  #
    [sp] = r1
    r0 = [r0+0]
    rep 16 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    goto L02044246
L02043dc8:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r2 = [sp]
    r1 = b[r0+0] (u)
    r0 = r2 + 4
    r0 = r4  #
    [sp] = r0
    r2 = [r2+0]
    call L020439e8
    goto L02044246
L02043de0:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r2 = [sp]
    r1 = [r0+0]
    r0 = r2 + 4
    r0 = r5  #
    [sp] = r0
    r2 = [r2+0]
    call L02043a6a
    r1 = 30
    r0 = r4
    call L02043340
    goto L02044246
L02043e00:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r2 = [sp]
    r1 = [r0+0]
    r0 = r2 + 4
    r0 = r4  #
    [sp] = r0
    r2 = [r2+0]
    call L02043a8a
    goto L02044246
L02043e18:
    r1 = [sp]
    r0 = r1 + 4
    [sp] = r0
    r0 = [sp]
    r2 = b[r1+0] (u)
    r1 = r0 + 4
    [sp] = r1
    r1 = 1
    if (r2 != 0) goto L02043e2c
    r1 = r2
L02043e2c:
    r0 = [r0+0]
    r2 = h[r6+0] (u)
    r2 = r2 & 0x7E
    r2 <= insert(r1, p:8, l:1)
    r1 = r2 | 0x1
    h[r6+0] = r1
    r1 = h[r6+0] (u)
    r1 |= 16
    h[r6+0] = r1
    r1 = b[r0+1] (u)
    r2 = b[r0+0] (u)
    r2 <= insert(r1, p:8, l:24)
    h[r6+2] = r2
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:24)
    h[r6+4] = r2
    r1 = b[r0+5] (u)
    r0 = b[r0+4] (u)
    r0 <= insert(r1, p:8, l:24)
    h[r6+6] = r0
    r0 = h[r4+8] (u)
    r0 &= 4294967287
    h[r4+8] = r0
    goto L02044246
L02043e6a:
    r1 = [sp]
    r2 = r1 + 4
    [sp] = r2
    r1 = [r1+0]
    b[r0+1] = r1
    if ((r1 & 0xFF) != 0) goto L02044246
    r1 = 0
    [r0+4] = r1
    b[r0+2] = r1
    goto L02044246
L02043e82:
    r0 = [sp]
    r2 = [r11+52]
    r1 = r0 + 4
    r3 = r12 + 68  #
    [sp] = r1
    r1 = 1
    if (r2 != r3) {
    r1 = 0
    }
    r0 = [r0+0]
    [r0+0] = r1
    goto L02044246
L02043e9e:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = 0x28000  #
    r1 = [r0+0]
    r2 = [r0+0]
    if (r2 == 0) goto L02044246
    r1 = r1.l (u)
    r2 = 1
    r2 <= insert(r1, p:8, l:16)
    [r0+52] = r2
    goto L02044246
L02043ebe:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = r12 + 239  #
    r1 = [r0+0]
    r5 = b[r1++=1] (u)
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 578
    b[r4+r0] = r5
    r0 = b[r7+2] (u)
    r0 |= 2
    b[r7+2] = r0
    goto L02044246
L02043ee4:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = [r0+0]
    h[r12+12] = r0
    r0 = r5
    call L020438de
    goto L02044246
L02043ef8:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r2 = [sp]
    r1 = b[r0+0] (u)
    r0 = r2 + 4
    r0 = r4  #
    [sp] = r0
    r2 = [r2+0]
    call L02043a2c
    goto L02044246
L02043f10:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r10 = [r0+0]
    r0 = L01c20230
    r0 = r4  #
    [r0+0] = r4
    r1 = 28
    call L02043340
    r0 = 0x8000
    h[r4+0] = r0
    r0 = h[r4+14] (u)
    r0 &= 4294967293
    r8 = 0  #
    h[r4+14] = r0
    h[r4+16] = r8
    r1 = 0
    r0 = r10
    call L020259d0  ; @call.xl
    r0 = r10  #
    h[r4+10] = r0
    r1 = 2
    call L020259d0  ; @call.xl
    r0 = r10 + 4  #
    h[r4+12] = r0
    r1 = 0
    call L020259d0  ; @call.xl
    h[r6+8] = r0
    r0 = b[r10+6] (u)
    h[r6+10] = r0
    r0 = h[r4+8] (u)
    r0 |= 4
    h[r4+8] = r0
    r0 = h[r4+8] (u)
    r0 &= 4294966783
    h[r4+8] = r0
    r0 = h[r4+8] (u)
    r0 = r0 | 0xC00
    h[r4+8] = r0
    r0 = h[r4+8] (u)
    r0 |= 4096
    r0 = r4 + 96  #
    h[r4+8] = r0
    r1 = h[r0+2] (u)
    r1 = r1 & 0xFFFFFFCF
    r1 |= 16
    h[r0+2] = r1
    r1 = b[r0+4] (u)
    r1 |= 1
    b[r0+4] = r1
    r1 = b[r0+5] (u)
    r1 |= 1
    b[r0+5] = r1
    r0 = b[r5+14] (u)
    if (r0 != 0) goto L02043fac
    r0 = [r5+0]
    r1 = h[r0+0] (u)
    r1 = r1 & 0x8000
    r1 |= 4
    h[r0+0] = r1
L02043fac:
    r1 = 0
    r2 = 0
    r0 = r5
    call L02043a6a
    b[r11+0] = r8
    r0 = b[r12+3] (u)
    if (r0 != 3) goto L020440f2
    r1 = 4
    r2 = 0
    r0 = r5
    call L0204384c
    r0 = h[r10+8] (u)
    r0 = r0 << 1
    r1 = r0 + 4
    r0 = r5
    call L02043b5a
    r3 = h[r10+12] (u)
    r1 = 6
    r2 = 0
    r0 = r5
    call L02043b9c
    r0 = r5
    call L020437ce
    call L020462de
    goto L0204413e
L02043ff4:
    r2 = 1250  #
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r6 = [r0+0]
    r0 = b[r6+7] (u)
    r1 = b[r12+3] (u)
    r0 *= r2  #
    r7 = h[r6+8] (u)
    r2 = r0 + 625
    if (r1 != 6) goto L020441f4
    r1 = 50
    r0 = r4
    call L02043a8a
    r0 = r5  #
    r3 = h[r6+12] (u)
    r1 = 6
    r2 = 0
    call L02043b9c
    r7 = r7 << 1
    goto L0204422e
L0204402a:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = r4  #
    r1 = [r0+0]
    call L02043a9e
    goto L02044246
L0204403a:
    r1 = [sp]
    r2 = r1 + 4
    [sp] = r2
    r1 = [r1+0]
    b[r0+0] = r1
    if ((r1 & 0xFF) != 0) goto L02044246
    r1 = 0
    [r0+8] = r1
    b[r0+3] = r1
    goto L02044246
L02044052:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r2 = [sp]
    r1 = b[r0+0] (u)
    r0 = r2 + 4
    [sp] = r0
    r0 = [r2+0]
    r2 = h[r4+6] (u)
    r2 &= 4294967287
    h[r4+6] = r2
    r2 = 1
    if (r1 != 0) goto L0204406e
    r2 = r1
L0204406e:
    b[r11+12] = r2
    r1 = r12 + 29
    r2 = r0
    rep 6 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r3 = r0  #
    r1 = h[r4+18] (u)
    r2 = [r9+0]
    r1 += r2  ; @add.rr
    rep 6 {
    r5 = b[r3++=1] (u)
    b[r1++=1] = r5
    }
    r1 = h[r4+20] (u)
    r1 += r2  ; @add.rr
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    goto L02044246
L0204409a:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = [r0+0]
    h[r4+510] = r0
    goto L02044246
L020440a8:
    r0 = [sp]
    r1 = r0 + 4
    r1 = 520  #
    [sp] = r1
    r0 = [r0+0]
    b[r4+r1] = r0
    goto L02044246
L020440ba:
    r0 = [sp]
    r1 = r0 + 4
    r1 = 521  #
    [sp] = r1
    r0 = [r0+0]
    b[r4+r1] = r0
    goto L02044246
L020440cc:
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r0 = r12 + 207  #
    r1 = [r0+0]
    r5 = b[r1++=1] (u)
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r0 = 546
    b[r4+r0] = r5
    r0 = b[r7+2] (u)
    r0 |= 1
    b[r7+2] = r0
    goto L02044246
L020440f2:
    r0 = h[r10+8] (u)
    r1 = 0
    if (r0 == 0) goto L02044100
    r0 = r0 << 1
    r1 = r0 + -1
L02044100:
    r0 = r5
    call L02043bc0
    r0 = [r9+0]
    r0 = b[r0+32] (u)
    if (r0 <= 1) {  ; @if.le.ri.s12
    r8 = h[r10+12] (u)
    }
    r2 = 1
    if (r8 == 0) {  ; @if.eq.ri.s12
    r2 = r8
    }
    r1 = 7
    r0 = r5
    r3 = r8
    call L02043b9c
    r1 = h[r10+22] (u)
    r0 = r4
    call L02043bd6
    r0 = h[r10+22] (u)
    h[r5+12] = r0
    r0 = 6
    h[r12+12] = r0
L0204413e:
    r0 = r5
    call L02043bf4
    r0 = r5
    call L02043c6c
    r0 = r5
    call L02043d00
    r0 = r5  #
    r7 = [r5+0]
    r1 = 3
    r2 = 0
    r6 = 0
    call L0204384c
    h[r7+88] = r6
    r0 = b[r10+7] (u)
    r7 = 1250
    r0 *= r7
    r2 = r0 + 1250
    r1 = 50
    r0 = r4
    call L02043a8a
    r0 = h[r10+10] (u)
    r1 = r0 * r7
    r2 = 1
    r0 = r5
    call L02043d0c
    r0 = h[r10+14] (u)
    r0 = r0 * 0xA
    h[r4+496] = r0
    r1 = r10 + 16
    r0 = r4
    call L02043a9e
    r0 = b[r10+21] (u)
    r0 = r0 & 0xFFFFFF1F
    r0 <= insert(r0, p:8, l:5)
    r2 = r0 | 0x8000
    r1 = 6
    r0 = r5
    call L0204384c
    b[r12+1] = r6
    r0 = h[r4+14] (u)
    r0 = r0 << 2
    r0 = r0 & 0x4  #
    h[r4+22] = r6
    r1 = r0 | 0x1
    h[r4+26] = r1
    r0 = r0 ^ 0x5  #
    h[r4+24] = r6
    h[r4+28] = r0
    r0 = h[r4+18] (u)
    r1 = [r9+0]
    r0 += r1  ; @add.rr
    r0 += -20
    [r12+60] = r0
    r0 = h[r4+20] (u)
    r0 += r1  ; @add.rr
    r0 += -20
    [r11+48] = r0
    r0 = 0
    r1 = 0
    d[r4+392] = r1_r0
    goto L02044246
L020441f4:
    r0 = h[r6+24] (u)
    r2 += r0  ; @add.rr
    r1 = 50
    r0 = r4
    call L02043a8a
    r0 = [r9+0]
    r0 = b[r0+32] (u)
    r3 = 0
    if (r0 <= 1) {  ; @if.le.ri.s12
    r3 = h[r6+12] (u)
    }
    r2 = 1
    if (r3 != 0) goto L02044216
    r2 = r3
L02044216:
    r1 = 7
    r0 = r5
    call L02043b9c
    r0 = r4  #
    r1 = h[r6+22] (u)
    call L02043bd6
    r0 = r7 << 1
    r0 += -1
    if (r7 == 0) goto L0204422e
    r7 = r0
L0204422e:
    r0 = r5
    r1 = r7
    call L02043bc0
    r1 = 1250  #
    r0 = h[r6+10] (u)
    r1 *= r0
    r2 = 1
    r0 = r5
    call L02043d0c
L02044246:
    sp += 4
    {rets, r12-r4} = [sp++]
    sp += 8
    rts
L0204424e:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = 0
    goto L02044260
L02044256:
    r2 = 0
    r0 = r4
    call L0204384c
    r5 += 1  ; @add.ri.u5
L02044260:
    r1 = r5.b0 (u)
    if (r1 != 17) goto L02044256
    {pc, r5, r4} = [sp++]
L02044268:
    [--sp] = {rets, r4}
    r0 = L01c21450
    r1 = [r0+0]
    r0 = 0
    r2 = 0
    goto L0204427c
L02044278:
    r0 += -28
    r2 += 1  ; @add.ri.u5
L0204427c:
    ifs (r2 > 0) goto L0204429e
    r3 = h[r1+r2<<1] (u)
    if (r3 != 0) goto L02044278
    r1 = [r1+16]
    r4 = r1 - r0
    r2 = 0
    r3 = r4
    rep 7 {
    [r3++=4] = r2
    }
    if (r1 == r0) goto L0204429e
    r0 = r4
    call L0204424e
    r0 = r4
    {pc, r4} = [sp++]
L0204429e:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020442aa:
    goto L020442aa
L020442ac:
    [--sp] = {rets, r6-r4}
    r0 = L01c21450
    r2 = -636  #
    r0 = [r0+0]
    r1 = -1
    r3 = 1268
L020442c0:
    r1 += 1  ; @add.ri.u5
    ifs (r1 > 0) goto L020442f6
    r4 = [r0+20]
    r5 = r4 + r2
    r6 = b[r5+r3] (u)
    r5 = r2 + 636
    r2 = r5
    if (r6 != 0) goto L020442c0
    r4 += r5  ; @add.rr
    r1 = 0
    r2 = 636
    r0 = r4
    call effect_enable_memset  ; @call.xl
    r0 = 632
    r1 = 1
    b[r4+r0] = r1
    if (r4 == 0) goto L020442f6
    r0 = r4
    {pc, r6-r4} = [sp++]
L020442f6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02044302:
    goto L02044302
L02044304:
    [--sp] = rets
    r1 = L01c21450
    r1 = [r1+0]
    r0 = r0 - r1
    r1 = 65535
    if (r0 < r1) {
    pc = [sp++]
    }
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02044328:
    goto L02044328
L0204432a:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = r1
    call L02044304
    r1 = L01c21450
    r1 = [r1+0]
    r0 |= 32768
    h[r1+r4<<1] = r0
    {pc, r4} = [sp++]
L02044342:
    [--sp] = rets
    r1 = 14
    r2 = 0
    call L0204384c
    pc = [sp++]
L0204434e:
    [--sp] = {rets, r8-r4}
    r3_r2 = r1_r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r4 = [r0+r1<<2]
    r5 = r4 + 1
    [r0+r1<<2] = r5
    r8 = L01c1fa20
    if (r4 != 0) goto L0204437e
    csync
L02044376:
    testset b[r8]
    ifeq goto L02044376
    csync
L0204437e:
    r4 = 163880
    if (r3 == 0) goto L020443c4
    r6 = r3 & 0xFFFFFF01  #
    r5 = [r4+4]
    r3 = r6 << r2
    r5 = r5 & ~(1 << r2)
    r5 |= r3
    [r4+4] = r5
    r5 = r2 + 8
    r5 = r6 << r5  #
    r7 = [r4+4]
    r6 = 256
    r1 = r6 << r2
    r6 = r7 & ~r1
    r6 |= r5
    [r4+4] = r6
    r6 = [r4+36]
    r6 = r6 & ~r1
    r6 |= r5
    [r4+36] = r6
    r6 = -1
    r6 = r6 ^ (1 << r2)
    r2 = ~r1
    goto L020443d8
L020443c4:
    r3 = -1
    r6 = r3 ^ (1 << r2)
    r3 = 256
    r2 = r3 << r2
    r2 = ~r2
    r5 = 0
    r3 = 0
L020443d8:
    r1 = [r4+0]
    r1 &= r6
    r1 |= r3
    [r4+0] = r1
    r1 = [r4+0]
    r1 &= r2
    r1 |= r5
    [r4+0] = r1
    r1 = [r4+36]
    r1 &= r6
    r1 |= r3
    [r4+36] = r1
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L02044408
    csync
    r0 = 0
    b[r8+0] = r0
L02044408:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r8-r4} = [sp++]
L02044410:
    [--sp] = {rets, r5, r4}
    r5 = L01c21450
    r4 = r0  #
    r2 = [r5+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 33
L02044428:
    testset b[r0]
    ifeq goto L02044428
    csync
    r0 = r4
    call L02044342
    r0 = [r5+0]
    csync
    r1 = 0
    b[r0+33] = r1
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 163896
L0204444a:
    r1 = [r0+0]
    if ((r1 & 2) != 0) goto L0204444a
    r2 = [r5+0]
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 33
L0204445e:
    testset b[r0]
    ifeq goto L0204445e
    csync
    r0 = r4
    call L020437ce
    r1 = 0
    r4 = 0
    call L0204434e
    r0 = [r5+0]
    csync
    b[r0+33] = r4
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r5, r4} = [sp++]
L02044484:
    [--sp] = rets
    r2 = 343  #
    r1 = [r0+0]
    r3 = 0
    b[r1+r2] = r3
    call L02044410
    pc = [sp++]
L02044496:
    [--sp] = {rets, r10-r4}
    sp += -8
    call L02044268
    r10 = r0
    call L020442ac
    r2 = r0
    [r10+0] = r2
    r0 = r10
    call L020437ce
    r1 = r2
    call L0204432a
    r0 = [r10+0]
    r5 = 0
    h[r0+0] = r5
    h[r0+2] = r5
    r1 = 54152
    r1 = r0 + 52  #
    h[r0+4] = r1
    r2 = 20967  #
    h[r1+20] = r5
    h[r1+22] = r2
    r2 = 48854
    h[r0+10] = r2
    r2 = 36489
    r2 = 21845  #
    h[r0+12] = r2
    h[r1+16] = r2
    r2 = 85
    h[r1+18] = r2
    r2 = 40
    r8 = 1  #
    h[r0+8] = r2
    h[r0+18] = r8
    h[r0+20] = r8
    r2 = h[r0+8] (u)
    r2 |= 512
    r3 = r0 + 92  #
    h[r0+8] = r2
    r2 = h[r3+6] (u)
    r2 |= 2
    h[r3+6] = r2
    r2 = h[r3+6] (u)
    r2 |= 4
    h[r3+6] = r2
    r2 = b[r3+10] (u)
    r2 &= 4294967294
    b[r3+10] = r2
    r2 = b[r3+11] (u)
    r2 &= 4294967294
    r6 = r0 + 288  #
    b[r3+11] = r2
    r2 = h[r6+30] (u)
    r2 = h[r6+28] (u)
    r4 = uextra(r2, p:8, l:6)
    r2 = r0 + 476
    b[r2+4] = r4
    r7 = 11
    b[r2+3] = r7
    r9 = L01c1fca8
    r4 = b[r9+3] (u)
    if (r4 <= 10) {  ; @if.le.ri.s12
    r7 = r4.b0 (s)
    b[r2+3] = r4
    }
    r4 = h[r9+0] (u)
    r4 = r4 >> 12
    r4 = smin(r7, r4)
    r2 = r4.b0 (u)  #
    b[r2+3] = r4
    r2 += 16  ; @add.ri.u5
    [r6+0] = r2
    r4 = 24000  #
    [r6+8] = r2
    r2 = h[r9+14] (u)
    r2 = 0x0 - r2
    r2 = r2 << 20
    r2 = r2 / r4 (s)
    r2 = 257  #
    [r6+16] = r2
    h[r3+4] = r2
    h[r3+2] = r8
    h[r0+14] = r5
    h[r0+16] = r5
    h[r0+22] = r5
    h[r0+26] = r8
    h[r0+24] = r5
    h[r0+28] = r8
    r2 = 255
    h[r1+2] = r2
    r4 = 33429
    h[r3+0] = r4
    h[r1+8] = r5
    h[r1+24] = r5
    h[r1+26] = r5
    h[r1+28] = r5
    b[sp+4] = r2
    r1 = -1
    [sp] = r1
    r1 = sp + 0
    call L02043a9e
    r0 = [r10+0]
    if (r0 == 0) goto L020445d4
    r0 = 40
    call L02025c22  ; @call.xl
    r5 = [r10+0]
    [r5+504] = r0
    r0 = L01c21450
    r0 = [r0+0]
    r1 = b[r0+32] (u)
    r1 += 1  ; @add.ri.u5
    b[r0+32] = r1
L020445d4:
    r0 = r5 + 384
    r1 = r0 + 24
    [r0+24] = r1
    r1 = r0 + 40  #
    [r0+28] = r1
    [r0+40] = r1
    r1 = r0 + 32  #
    [r0+44] = r1
    [r0+32] = r1
    [r0+36] = r1
    r2 = 0
    r3 = 0
    d[r0+8] = r3_r2
    d[r0+0] = r3_r2
    r0 = r10
    call L02044484
    r0 = r10
    sp += 8
    {pc, r10-r4} = [sp++]
L02044606:
    [r0+488] = r1
    [r0+492] = r2
    rts
L02044610:
    if (r1 == 3) goto L02044620
    r2 = 0
    if (r1 == 2) goto L02044626
    if (r1 == 1) goto L02044622
    goto L02044628
L02044620:
    r2 = 16
L02044622:
    r1 = 8
    goto L0204462a
L02044626:
    r2 = 16
L02044628:
    r1 = 0
L0204462a:
    r3 = h[++r0=60] (u)
    r3 = r3 & 0xF7
    r1 |= r3
    h[r0+0] = r1
    r1 = h[r0+0] (u)
    r1 = r1 & 0xEF
    r1 |= r2
    h[r0+0] = r1
    rts
L02044642:
    [--sp] = {rets, r4}
    r0 = 0
    r1 = L01c20236
    r2 = 0
    goto L02044660
L02044650:
    r3 = r0 + r1
    r4 = b[r3+8] (u)
    r3 = 1
    if (r4 == 255) {  ; @if.eq.ri.s12
    r3 = 0
    }
    r2 += r3  ; @add.rr
    r0 += 1  ; @add.ri.u5
L02044660:
    if (r0 != 8) goto L02044650
    r0 = r2.b0 (u)
    {pc, r4} = [sp++]
L02044668:
    [--sp] = rets
    r1 = 8
    r2 = 0xC000
    call L0204384c
    pc = [sp++]
L02044676:
    [--sp] = {rets, r7-r4}
    r2 = 0
    r3 = 9472
    r5 = 37
    r6 = 0
    r4 = 0
    goto L020446a2
L02044686:
    r7 = r1 & (1 << r6)
    if (r7 == 0) goto L02044696
    r7 = r5
    if ((r4 & 0xFF) == 0) goto L02044698
    goto L020446a8
L02044696:
    r7 = r4
L02044698:
    r5 += 1  ; @add.ri.u5
    r3 = r3 + 256
    r6 += 1  ; @add.ri.u5
    r4 = r7
L020446a2:
    if (r6 <= 2) goto L02044686
    goto L020446b0
L020446a8:
    r2 = r4 << 8
    r2 = r3 - r2
    r2 = r2 & 0xFF00
L020446b0:
    r3 = r1 << 5
    r3 = r3 & 0x80
    r1 = r1 << 6
    r1 = r1 & 0x40
    r1 |= r3
    r1 ^= 64
    r1 |= r4
    r1 = r1.b0 (u)
    r1 |= r2
    r2 = r1 | 0x4000
    r1 = 6
    call L0204384c
    {pc, r7-r4} = [sp++]
L020446d2:
    [--sp] = rets
    r1 = r0 + 20
    r0 = 0
    call L0202541c  ; @call.xl
    if (r0 == 0) goto L020446e6
    if ((r0 & 0x3) != 0) goto L020446e8
L020446e6:
    pc = [sp++]
L020446e8:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L020446f4:
    goto L020446f4
L020446f6:
    [--sp] = {rets, r5, r4}
    r5 = r2
    r4 = r0
    r0 = r1 + 20
    call L02044304
    if (r5 != 0) {  ; @if.ne.ri.s12
    h[r4+32] = r0
    } else {
    h[r4+30] = r0
    }
    {pc, r5, r4} = [sp++]
L0204470e:
    [--sp] = {rets, r5, r4}
    if (r2 > 6) goto L020447a8
    r0 = r0 + 368
    tbb [r2]
L0204471a:
    .byte (L02044722 - L0204471a) / 2, (L02044762 - L0204471a) / 2, (L02044722 - L0204471a) / 2, (L020447a8 - L0204471a) / 2, (L020447a8 - L0204471a) / 2, (L020447a8 - L0204471a) / 2, (L02044722 - L0204471a) / 2
    .byte 0x00  ; alignment
L02044722:
    r2 = r2 & 0xFFFFFF0F  #
    r4 = h[r1+16] (u)
    r4 = r4 & 0xFFFFFFC0
    r2 |= r4
    h[r1+16] = r2
    r4 = r3 + 6
    b[r1+18] = r4
    r5 = 65423
    r5 &= r2  #
    r4 = b[r0++=1] (u)
    r4 = r4 << 6
    r4 = r4 & 0x40  #
    r2 = [sp+12]
    r4 |= r5
    h[r1+16] = r4
    r4 = r1 + 20
    rep 6 {
    r5 = b[r0++=1] (u)
    b[r4++=1] = r5
    }
    r0 = r1 + 26
    r1 = r2
    r2 = r3
    call effect_parameter_support_memmove  ; @call.xl
    {pc, r5, r4} = [sp++]
L02044762:
    r2 = h[r1+16] (u)
    r2 = r2 & 0xFFFFFFC0
    r2 |= 1
    h[r1+16] = r2
    r3 = 12
    b[r1+18] = r3
    r3 = b[r0+0] (u)
    r3 = r3 << 6
    r3 = r3 & 0x40
    r2 = r2 & 0xFFFFFF81
    r2 |= r3
    h[r1+16] = r2
    r3 = r1 + 20
    r4 = r0 + 1
    rep 6 {
    r5 = b[r4++=1] (u)
    b[r3++=1] = r5
    }
    r4 = 65345
    r2 &= r4  #
    r3 = b[r0+7] (u)
    r3 = r3 << 7
    r3 = r3.b0 (u)
    r2 |= r3
    h[r1+16] = r2
    r1 += 26  ; @add.ri.u5
    r0 += 8  ; @add.ri.u5
    rep 6 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
L020447a8:
    {pc, r5, r4} = [sp++]
L020447aa:
    [--sp] = {rets, r7-r4}
    r7 = r1
    r5 = r0
    r0 = b[r7+18] (u)
    r4 = [r5++=16]
    r6 = r2
    if (r6 == 0) goto L020447c8
    if (r0 == 0) goto L020447d2
    r0 = r7 + 20
    call L02044304
    h[r4+20] = r0
    goto L020447d2
L020447c8:
    if (r0 == 0) goto L020447d2
    r0 = r7 + 20
    call L02044304
    h[r4+18] = r0
L020447d2:
    r0 = r4
    r1 = r7
    r2 = r6
    call L02043488
    r0 = b[r5+8] (u)
    if (r0 == 0) goto L020447f2
    if (r6 == 0) goto L020447f4
    r0 = h[r4+28] (u)
    r1 = b[r5+0] (u)
    r0 &= 4294967279
    r1 = r1 << 4
    r1 = r1 & 0x10
    r0 |= r1
    h[r4+28] = r0
L020447f2:
    {pc, r7-r4} = [sp++]
L020447f4:
    r0 = h[r4+26] (u)
    r1 = b[r5+0] (u)
    r0 &= 4294967279
    r1 = r1 << 4
    r1 = r1 & 0x10
    r0 |= r1
    h[r4+26] = r0
    {pc, r7-r4} = [sp++]
L02044806:
    r1 = h[r0+8] (u)
    r1 &= 4294967279
    h[r0+8] = r1
    rts
L0204480e:
    [--sp] = rets
    call L020437ce
    r1 = 1
    call L0204434e
    pc = [sp++]
L0204481c:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    call L0204480e
    r0 = r5
    r1 = r4
    call L02043b5a
    {pc, r5, r4} = [sp++]
L0204482e:
    [--sp] = {rets, r5, r4}
    r1 = 0
    r2 = 163880
L02044838:
    if (r1 > 7) goto L0204485c
    r0 = [r2+0]
    r4 = r0 & (1 << r1)  #
    r3 = [r2+8]
    r0 = 1
    if ((r4 & r3) != 0) goto L0204485a
    r3 = [r2+36]
    r5 = r0 << r1  #
    r4 = [r2+40]
    r3 &= r5
    r1 += 1  ; @add.ri.u5
    if ((r3 & r4) == 0) goto L02044838
L0204485a:
    {pc, r5, r4} = [sp++]
L0204485c:
    r0 = 0
    {pc, r5, r4} = [sp++]
L02044860:
    [--sp] = {rets, r4}
    r4 = r0
    call L02044342
    r0 = 163896
    r0 = r4  #
    r0 = [r0+0]
    call L020437ce
    r1 = 0
    call L0204434e
    {pc, r4} = [sp++]
L0204487e:
    [--sp] = rets
    r1 = [r0+0]
    r1 = r1 + 344
    r2 = b[r1+0] (u)
    r2 |= 2
    if (r2 != 3) goto L02044890
    pc = [sp++]
L02044890:
    r2 = 1
    b[r1+0] = r2
    r1 = icfg
    if ((r1 & 0xFF) == 0) goto L020448a2
    call L02044860
    pc = [sp++]
L020448a2:
    call L02044410
    pc = [sp++]
L020448a8:
    [--sp] = rets
    r2 = [r0+0]
    r2 = r2 + 344
    r3 = b[r2+0] (u)
    r3 &= 4294967294
    if (r3 != 2) {  ; @if.ne.ri.s12
    r3 = 2
    b[r2+0] = r3
    call L0204481c
    }
    pc = [sp++]
L020448c0:
    [--sp] = {rets, r15-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L020448ee
    csync
L020448e6:
    testset b[r0]
    ifeq goto L020448e6
    csync
L020448ee:
    r8 = L01c21454
    r2 = b[r8+0] (u)
    if (r2 == 0) goto L02044918
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02044910
    csync
    r1 = 0
    b[r0+0] = r1
L02044910:
    call storage_coordination_irq_leave  ; @call.xl
    {pc, r15-r4} = [sp++]
L02044918:
    r2 = 1
    b[r8+0] = r2
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L02044934
    csync
    r1 = 0
    b[r0+0] = r1
L02044934:
    call storage_coordination_irq_leave  ; @call.xl
    r12 = L01c21450
    r0 = [r12+0]
    r0 = b[r0+32] (u)
    if (r0 < 2) goto L02044a66
    r5 = 0
    r14 = -1
    r9 = 343
    r10 = 163896
    r11 = 310
    r7 = 0
    r15 = -1
    r13 = 0
    goto L020449f6
L0204496a:
    r0 = [r12+0]
    r1 = h[r0+r7<<1] (u)
    if (r1 == 0) goto L020449ee
    r6 = [r0+16]
    r4 = r6 + r5
    r0 = [r4+0]
    if (r0 == 0) goto L020449f2
    r1 = b[r0+r9] (u)
    r2 = uextra(r13, p:0, l:8)
    r0 = r1 + -1
    r13 = r2 | (1 << r1)
    if (r0 > 6) goto L020449ee
    tbb [r0]
L02044992:
    .byte (L020449d4 - L02044992) / 2, (L0204499a - L02044992) / 2, (L020449d4 - L02044992) / 2, (L020449ee - L02044992) / 2, (L020449ee - L02044992) / 2, (L0204499a - L02044992) / 2, (L0204499a - L02044992) / 2
    .byte 0x00  ; alignment
L0204499a:
    r0 = [r10+0]
    r15 = 0
    if ((r0 & 2) != 0) goto L020449ee
    call L0204482e
    if (r0 != 0) goto L020449ee
    r1 = 0
    r0 = r4
    call L020437e4
    r6 = r0.l (u)
    r1 = 14
    r0 = r4
    call L020437e4
    r0 = r0 << 16
    r0 = r0 & 0xFF0000
    r1 = r0 | r6
    r0 = r1 + -3
    r1 += 1  ; @add.ri.u5
    if (r1 >= 4) {  ; @if.ge.ri.s12
    r15 = r0
    }
    goto L020449ee
L020449d4:
    r0 = [r10+0]
    if ((r0 & 2) != 0) goto L020449ec
    r0 = r4
    call L0204487e
    r0 = [r6+r5]
    r15 = h[r0+r11<<1] (u)
    goto L020449ee
L020449ec:
    r15 = 0
L020449ee:
    r14 = umin(r14, r15)
L020449f2:
    r5 += 28  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L020449f6:
    if (r7 != 8) goto L0204496a
    if (r14 < 4) goto L02044a66
    r1 = r13 & 0xA
    r0 = L01c20234
    if (r1 == 2) goto L02044a1c
    if (r1 == 8) goto L02044a20
    if (r1 != 10) goto L02044a26
    r1 = b[r0+0] (u)
    r3 = 3
    if (r1 == 1) goto L02044a22
L02044a1c:
    r3 = 1
    goto L02044a22
L02044a20:
    r3 = 3
L02044a22:
    b[r0+0] = r3
    goto L02044a28
L02044a26:
    r3 = b[r0+0] (u)
L02044a28:
    r1 = [r12+0]
    r0 = 0
    r2 = r9
    r3 = r3.b0 (u)
    r4 = 0
    goto L02044a62
L02044a36:
    r5 = h[r1+r4<<1] (u)
    if (r5 == 0) goto L02044a5e
    r5 = [r1+16]
    r6 = [r5+r0]
    if (r6 == 0) goto L02044a5e
    r7 = b[r6+r2] (u)
    if (r7 != r3) goto L02044a5e
    r6 = r6 + 620
    r7 = h[r6+0] (u)
    if (r14 < r7) goto L02044a5e
    if (r3 == 3) goto L02044a6e
    if (r3 == 1) goto L02044a6e
L02044a5e:
    r0 += 28  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02044a62:
    if (r4 <= 7) goto L02044a36
L02044a66:
    r0 = 0
    b[r8+0] = r0
    {pc, r15-r4} = [sp++]
L02044a6e:
    r0 += r5  #  ; @add.rr.p
    r1 = h[r6+2] (u)
    call L020448a8
    goto L02044a66
L02044a78:
    [--sp] = {rets, r10-r4}
    sp += -4
    r8 = r0  #
    r4 = [r0+0]
    r6 = r1
    r1 = 26
    r0 = r4
    call L02043340
    r0 = 21845
    h[r4+68] = r0
    r0 = 85
    h[r4+70] = r0
    r0 = 50
    h[r4+34] = r0
    r1 = 0
    h[r4+36] = r1
    r9 = r4 + 272
    h[r9+2] = r0
    r5 = r4 + 336
    r7 = 625  #
    [r5+0] = r0
    r0 = h[r6+0] (u)
    r1 = r0 * r7
    r2 = 1
    r0 = r8
    call L02043d0c
    r0 = [r8+0]
    r1 = b[r6+6] (u)
    call L02044610
    r0 = h[r6+2] (u)
    r0 *= r7  #
    r1 = b[r6+4] (u)
    r1 = r1 << 14
    r0 |= r1
    h[r4+4] = r0
    r0 = b[r6+7] (u)
    if (r0 == 2) goto L02044afa
    r0 = h[r6+0] (u)
    if (r0 < 11) goto L02044afa
    call L02044642
    if (r0 == 0) goto L02044af4
    r0 = r8
    call L02043d00
    goto L02044afa
L02044af4:
    r0 = r8
    call L02044668
L02044afa:
    r0 = r8  #
    r1 = b[r6+5] (u)
    call L02044676
    r0 = 263
    call L020446d2
    r0 = 263  #
    [r5+48] = r0
    call L020446d2
    [r5+52] = r0
    r7 = -2
    if (r0 == 0) goto L02044c38
    r1 = [r5+48]
    if (r1 == 0) goto L02044c38
    r0 = [r8+0]
    r2 = 0
    call L020446f6
    r0 = [r8+0]
    r1 = [r5+52]
    r2 = 1
    call L020446f6
    r0 = 263
    call L02043328
    r0 = 263  #
    [r5+56] = r0
    call L02043328
    [r5+60] = r0
    if (r0 == 0) goto L02044c38
    r1 = [r5+56]
    if (r1 == 0) goto L02044c38
    r7 = r5 + 210  #
    r2 = b[r6+7] (u)
    r10 = r5 + 211  #
    r3 = b[r7+0] (u)
    [sp] = r10  ; @st.w.sp.l
    r0 = r4
    call L0204470e
    r0 = b[r6+7] (u)
    r1 = [r5+60]
    if (r0 != 1) goto L02044b80
    r0 = r4  #
    r3 = b[r7+0] (u)
    r2 = 1
    [sp] = r10  ; @st.w.sp.l
    call L0204470e
    goto L02044bca
L02044b80:
    r2 = 578  #
    r0 = h[r1+16] (u)
    r2 = b[r4+r2] (u)
    r0 = r0 & 0xFFFFFFC0
    r0 |= 4
    h[r1+16] = r0
    r3 = r2 + 6
    b[r1+18] = r3
    r3 = 368
    r3 = b[r4+r3] (u)
    r7 = 65412
    r0 &= r7
    r3 = r3 << 6
    r3 = r3 & 0x40
    r0 |= r3
    h[r1+16] = r0
    r0 = r1 + 20
    r3 = r9 + 97
    rep 6 {
    r7 = b[r3++=1] (u)
    b[r0++=1] = r7
    }
    r0 = r1 + 26
    r1 = r5 + 243
    call effect_parameter_support_memmove  ; @call.xl
L02044bca:
    r0 = r8  #
    r1 = [r5+56]
    r2 = 0
    r7 = 0
    call L020447aa
    r0 = r8  #
    r1 = [r5+60]
    r2 = 1
    call L020447aa
    r0 = 610
    b[r4+r0] = r7
    r0 = r4
    call L02044806
    call L02044642
    if (r0 != 0) goto L02044bfa
    r0 = r8
    call L02043c6c
L02044bfa:
    r1 = 2
    r3_r2 = 0
    r0 = r8
    call L02043b9c
    r0 = r8
    call L020437ce
    r1 = h[r6+0] (u)
    call L02046282
    call L02044642
    if (r0 != 0) goto L02044c1e
    r1 = 1
    r0 = r8
    call L0204481c
L02044c1e:
    r0 = L01c21450
    r0 = [r0+0]
    r0 = b[r0+32] (u)
    if (r0 >= 2) {  ; @if.ge.ri.s12
    call L020448c0
    }
    r0 = h[r4+6] (u)
    r0 |= 4
    h[r4+6] = r0
L02044c38:
    r0 = r7
    sp += 4
    {pc, r10-r4} = [sp++]
L02044c3e:
    if (r0 == 0) goto L02044c4a
    r1 = 632
    r2 = 0
    b[r0+r1] = r2
L02044c4a:
    rts
L02044c4c:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r5 = [r4+0]
    if (r5 == 0) goto L02044d90
    call L02043bf4
    r0 = r4
    call L02044410
    r5 = r5 + 384
    r0 = [r5+12]
    call phase3_p11_hw_dma_free  ; @call.xl
    r0 = [r5+8]
    call phase3_p11_hw_dma_free  ; @call.xl
    r0 = [r5+16]
    call phase3_p11_hw_dma_free  ; @call.xl
    r0 = [r5+20]
    call phase3_p11_hw_dma_free  ; @call.xl
    r6 = 0
    r7 = 0
    d[r5+8] = r7_r6
    r0 = [r5+4]
    call phase3_p11_hw_dma_free  ; @call.xl
    r0 = [r5+0]
    call phase3_p11_hw_dma_free  ; @call.xl
    d[r5+0] = r7_r6
    r0 = r5 + 40
    call L02025cc4  ; @call.xl
    r0 = r5 + 32
    call L02025cc4  ; @call.xl
    r0 = r5 + 24
    call L02025cc4  ; @call.xl
    r0 = [r4+0]
    r6 = L01c21450
    if (r0 == 0) goto L02044d04
    r0 = r4
    call L0204424e
    r0 = [r4+0]
    r0 = [r0+504]
    call phase3_p11_btctler_nv_memory_free  ; @call.xl
    r0 = r4  #
    r2 = [r6+0]
    call L020437ce
    r5 = 0
    h[r2+r0<<1] = r5
    r0 = b[r2+32] (u)
    r0 += -1
    b[r2+32] = r0
    r0 = r4
    call L020437ce
    r1 = r0
    r0 = r4
    call L020463a0
    r0 = [r4+0]
    call L02044c3e
    [r4+0] = r5
L02044d04:
    call storage_coordination_irq_enter  ; @call.xl
    r5 = L01c1fa24
    r0 = cnum
    r1 = [r5+r0<<2]
    r2 = r1 + 1
    [r5+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L02044d30
    csync
L02044d28:
    testset b[r8]
    ifeq goto L02044d28
    csync
L02044d30:
    r1 = [r6+0]
    r0 = 0
    r2 = 0
    goto L02044d5e
L02044d38:
    r3 = h[r1+r2<<1] (u)
    if (r3 == 0) goto L02044d5a
    r3 = [r1+16]
    r6 = [r3+r0]
    if (r6 == 0) goto L02044d5a
    r7 = r6 + 342
    r4 = b[r7+1] (u)
    if (r4 == 3) goto L02044d54
    if (r4 != 1) goto L02044d5a
L02044d54:
    r4 = b[r7+2] (u)
    if (r4 == 1) goto L02044d64
L02044d5a:
    r0 += 28  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L02044d5e:
    if (r2 <= 7) goto L02044d38
    goto L02044d72
L02044d64:
    r1 = 311
    r1 = h[r6+r1<<1] (u)
    r0 += r3  ; @add.rr
    call L020448a8
L02044d72:
    r0 = cnum
    r1 = [r5+r0<<2]
    r1 += -1
    [r5+r0<<2] = r1
    if (r1 != 0) goto L02044d8a
    csync
    r0 = 0
    b[r8+0] = r0
L02044d8a:
    call storage_coordination_irq_leave  ; @call.xl
L02044d90:
    {pc, r8-r4} = [sp++]
L02044d92:
    [--sp] = {rets, r4}
    r3 = r2 - r1
    ifs (r3 <= 0) {  ; @ifs.le.ri.s12
    r3 = 0
    }
    r0 = r0 + 618
    r4 = r1 + 4
    h[r0+4] = r3
    ifs (r4 <= r2) goto L02044db4
    ifs (r2 <= 4) {  ; @ifs.le.ri.s12
    r1 = 1
    r2 = 5
    } else {
    r1 = r2 + -4
    }
L02044db4:
    h[r0+0] = r1
    h[r0+2] = r2
    {pc, r4} = [sp++]
L02044dba:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r5 = r2  #
    r0 = [r4+0]
    r6 = 625
    r2 = r1 * r6
    r1 = 50
    call L02043a8a
    r1 = r5 * r6
    r2 = 0
    r0 = r4
    call L02043d0c
    {pc, r6-r4} = [sp++]
L02044dde:
    if (r1 == 3) goto L02044de8
    r2 = 0
    if (r1 != 1) goto L02044dea
L02044de8:
    r2 = 8
L02044dea:
    r1 = h[r0+60] (u)
    r1 = r1 & 0xF7
    r1 |= r2
    h[r0+60] = r1
    rts
L02044dfa:
    if (r1 == 0) goto L02044e06
    r1 = 508
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L02044e0c
L02044e06:
    r1 = h[r0+6] (u)
    r1 |= 256
    goto L02044e10
L02044e0c:
    r1 = h[r0+6] (u)
    r1 &= 4294967039
L02044e10:
    h[r0+6] = r1
    rts
L02044e14:
    [--sp] = rets
    r2 = r1 | 0x2100
    r1 = 6
    call L0204384c
    pc = [sp++]
L02044e22:
    [--sp] = {rets, r4}
    r2 = h[r1+16] (u)
    r2 = r2 & 0xFFFFFFC0
    r2 = r2 | 0x3
    h[r1+16] = r2
    r3 = 12
    b[r1+18] = r3
    r3 = 368
    r3 = b[r0+r3] (u)
    r4 = 65411
    r2 &= r4
    r3 = r3 << 6
    r3 = r3 & 0x40
    r2 |= r3
    h[r1+16] = r2
    r2 = r1 + 20
    r0 = r0 + 369
    rep 6 {
    r3 = b[r0++=1] (u)
    b[r2++=1] = r3
    }
    r0 = r1 + 26
    r1 = 0
    rep 6 {
    b[r0++=1] = r1
    }
    {pc, r4} = [sp++]
L02044e66:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r6 = r1  #
    r5 = [r4+0]
    r1 = 17
    r0 = r5
    call L02043340
    r0 = r4
    call L02043d00
    r0 = r5  #
    r2 = h[r6+2] (u)
    r1 = h[r6+4] (u)
    call L02044d92
    r7 = r5 + 616
    r0 = r4  #
    r2 = h[r7+4] (u)
    r1 = h[r7+2] (u)
    call L02044dba
    r0 = r4
    call L020437ce
    r2 = h[r7+2] (u)
    r1 = h[r7+4] (u)
    call L020462ba
    r0 = r5  #
    r1 = b[r6+6] (u)
    call L02044dde
    r1 = b[r6+0] (u)
    call L02044dfa
    r0 = 37
    r7 = r5 + 340
    r0 = r4  #
    b[r7+2] = r0
    r1 = 37
    call L02044e14
    r0 = 263
    call L020446d2
    r0 = 263  #
    [r7+44] = r0
    call L020446d2
    [r7+48] = r0
    r6 = -2
    if (r0 == 0) goto L02044f24
    r1 = [r7+44]
    if (r1 == 0) goto L02044f24
    r0 = [r4+0]
    r2 = 0
    call L020446f6
    r0 = [r4+0]
    r1 = [r7+48]
    r2 = 1
    call L020446f6
    r0 = 20
    call L02043328
    [r7+52] = r0
    r0 = 20
    call L02043328
    [r7+56] = r0
    if (r0 == 0) goto L02044f24
    r1 = [r7+52]
    if (r1 == 0) goto L02044f24
    r0 = r5
    call L02044e22
    r0 = r5  #
    r1 = [r7+56]
    call L02044e22
    r0 = r4  #
    r1 = [r7+52]
    r2 = 0
    r6 = 0
    call L020447aa
    r0 = r4  #
    r1 = [r7+56]
    r2 = 1
    call L020447aa
    r1 = 1
    r3_r2 = 0
    r0 = r4
    call L02043b9c
L02044f24:
    r0 = r6
    {pc, r7-r4} = [sp++]
L02044f28:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r6 = r1  #
    r7 = [r4+0]
    call L02044e66
    r5 = r0
    if (r5 != 0) goto L02044f98
    r0 = h[r7+8] (u)
    r0 &= 4294966783
    h[r7+8] = r0
    r0 = h[r7+8] (u)
    r0 = r0 | 0xC00
    r0 = r7 + 468  #
    h[r7+8] = r0
    r1 = b[r6+0] (u)
    b[r0+0] = r1
    if (r1 == 0) goto L02044f5c
    r1 = 0
    b[r0+1] = r1
    r2 = 1
    h[r0+2] = r2
    h[r0+4] = r2
    h[r0+6] = r2
    h[r0+8] = r1
L02044f5c:
    call L02044642
    if (r0 != 0) goto L02044f68
    r0 = r4
    call L02043c6c
L02044f68:
    call L02044642
    r5 = 0
    if (r0 != 0) goto L02044f98
    r0 = L01c21450
    r0 = [r0+0]
    r1 = b[r0+32] (u)
    r0 = r7 + 344
    if (r1 != 1) goto L02044f90
    r0 = r4  #
    b[r0+0] = r5
    r1 = 1
    call L0204481c
    goto L02044f98
L02044f90:
    r1 = 1
    b[r0+0] = r1
    call L020448c0
L02044f98:
    r0 = r5
    {pc, r7-r4} = [sp++]
L02044f9c:
    [--sp] = {rets, r6-r4}
    r3 = h[r2+16] (u)
    r3 = r3 & 0xFFFFFFC0
    r3 = r3 | 0x5
    r0 = r0 + 368  #
    h[r2+16] = r3
    r4 = 34
    b[r2+18] = r4
    r4 = b[r0+0] (u)
    r4 = r4 << 6
    r4 = r4 & 0x40
    r3 = r3 & 0xFFFFFF85
    r3 |= r4
    h[r2+16] = r3
    r4 = r2 + 20
    r5 = r0 + 1
    rep 6 {
    r6 = b[r5++=1] (u)
    b[r4++=1] = r6
    }
    r5 = 65349
    r3 &= r5  #
    r4 = b[r0+7] (u)
    r4 = r4 << 7
    r4 = r4.b0 (u)
    r3 |= r4
    h[r2+16] = r3
    r3 = r2 + 26
    r0 += 8  ; @add.ri.u5
    rep 6 {
    r4 = b[r0++=1] (u)
    b[r3++=1] = r4
    }
    r0 = r2 + 32
    r1 += 8  ; @add.ri.u5
    rep 22 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    {pc, r6-r4} = [sp++]
L02044ff8:
    [--sp] = rets
    r1 = 9
    r2 = 1
    call L0204384c
    pc = [sp++]
L02045004:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r8 = r1  #
    r6 = [r4+0]
    r1 = 26
    r0 = r6
    call L02043340
    r1 = h[r8+2] (u)
    r2 = h[r8+0] (u)
    r0 = r6
    call L02044d92
    r5 = r6 + 616
    r0 = r4  #
    r2 = h[r5+4] (u)
    r1 = h[r5+2] (u)
    call L02044dba
    r0 = r4
    call L020437ce
    r5 = r6 + 340  #
    r2 = h[r5+2] (u)
    r1 = [r5+24]
    call L020462cc
    r0 = 37
    r0 = r4  #
    b[r5+2] = r0
    r1 = 37
    call L02044e14
    r0 = 508
    r0 = b[r6+r0] (u)
    if (r0 == 0) goto L02045066
    r0 = h[r6+8] (u)
    r0 |= 16
    h[r6+8] = r0
    r0 = 0
    [r6+500] = r0
    goto L0204506c
L02045066:
    r0 = r6
    call L02044806
L0204506c:
    r0 = 263
    call L020446d2
    r0 = 263  #
    [r5+44] = r0
    call L020446d2
    [r5+48] = r0
    r7 = -2
    if (r0 == 0) goto L0204511a
    r1 = [r5+44]
    if (r1 == 0) goto L0204511a
    r0 = [r4+0]
    r2 = 0
    call L020446f6
    r0 = [r4+0]
    r1 = [r5+48]
    r2 = 1
    call L020446f6
    r0 = 263
    call L02043328
    r0 = 263  #
    [r5+52] = r0
    call L02043328
    [r5+56] = r0
    if (r0 == 0) goto L0204511a
    r2 = [r5+52]
    if (r2 == 0) goto L0204511a
    r0 = r6
    r1 = r8
    call L02044f9c
    r0 = r6  #
    r2 = [r5+56]
    r1 = r8
    call L02044f9c
    r0 = r4  #
    r1 = [r5+52]
    r2 = 0
    call L020447aa
    r0 = r4  #
    r1 = [r5+56]
    r2 = 1
    call L020447aa
    r1 = 3
    r3_r2 = 0
    r0 = r4
    call L02043b9c
    call L02044642
    if (r0 != 0) goto L020450f0
    r0 = r4
    call L02043c6c
L020450f0:
    call L02044642
    if (r0 != 0) goto L02045112
    r0 = L01c21450
    r0 = [r0+0]
    r0 = b[r0+32] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = 0
    b[r5+4] = r0
    }
    r1 = 1
    r0 = r4
    call L0204481c
L02045112:
    r0 = r4
    call L02044ff8
    r7 = 0
L0204511a:
    r0 = r7
    {pc, r8-r4} = [sp++]
L0204511e:
    [--sp] = {rets, r6-r4}
    r4 = L01c21450
    r0 = [r4+0]
    if (r0 == 0) goto L0204519e
    r5 = 0
    r6 = 0
    goto L02045144
L02045130:
    r0 = [r4+0]
    r1 = h[r0+r6<<1] (u)
    if (r1 == 0) goto L02045140
    r0 = [r0+16]
    r0 += r5  ; @add.rr
    call L02044c4c
L02045140:
    r5 += 28  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L02045144:
    if (r6 != 8) goto L02045130
    r5 = L01c26890
    r0 = 358
    r0 = [r5+r0<<2]
    if (r0 == 0) goto L02045176
    r1 = 357
    r1 = [r5+r1<<2]
    if (r1 == 0) goto L02045176
    call L02025d30  ; @call.xl
    r0 = 357
    r0 = [r5+r0<<2]
    call L02025d30  ; @call.xl
L02045176:
    r5 = L01c21455
    r1 = b[r5+0] (u)
    r0 = [r4+0]
    if (r1 == 0) goto L0204518e
    call L0203e658  ; @call.xl
    r0 = 0
    b[r5+0] = r0
    goto L02045194
L0204518e:
    call L0203d218  ; @call.xl
L02045194:
    r0 = 0
    r1 = 0x28000  #
    [r4+0] = r0
    [r1+0] = r0
L0204519e:
    {pc, r6-r4} = [sp++]
L020451a0:
    [--sp] = {rets, r9-r4}
    r8 = r0  #
    r5 = [r0+0]
    r0 = h[r5+510] (u)
    r7 = r3
    r9 = r2
    r4 = r1
    ifs (r0 < r7) goto L02045226
    r0 = [sp+28]
    call L02043328
    r6 = r0
    if (r6 == 0) goto L02045226
    r0 = 0
    r1 = r6
    rep 5 {
    [r1++=4] = r0
    }
    r0 = r4 << 4
    r0 = r0 & 0x30
    h[r6+16] = r0
    b[r6+18] = r7
    ifs (r7 >= 256) goto L02045226
    r0 = r6 + 20
    r1 = r9
    r2 = r7
    call effect_parameter_support_memmove  ; @call.xl
    call phase3_p11_low_power_exit_request  ; @call.xl
    r0 = r5 + 424
    r1 = r6
    call phase3_p11_hw_dma_push  ; @call.xl
    r1 = 28
    r0 = r5
    call L02043340
    r0 = r8
    call L020435fa
    r0 = 0
    r2 = 2
    r1 = r5
    call L02043732
    call L02043742
    if (r0 != 255) goto L02045224
    r0 = 354
    r0 = b[r5+r0] (u)
    if (r0 != 0) goto L02045224
    r0 = r8
    call L020438de
L02045224:
    {pc, r9-r4} = [sp++]
L02045226:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L02045232:
    goto L02045232
