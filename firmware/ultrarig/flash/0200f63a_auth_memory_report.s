; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; auth_memory_report: 1 function, 0x0200f63a..0x0200f8ec

; auth_memory_report_auth_command: 0x0200f63a..0x0200f8ec, module auth-memory-report (auth_command)
.type auth_memory_report_auth_command,@function
auth_memory_report_auth_command:
    [--sp] = {rets, r13-r4}
    sp += -420
    r6 = r0
    r9 = L02035c9e  ; "AUTH ok"
    if (r1 == 0) goto L0200f688
    r0 = b[r6+0] (u)
    r7 = L01c26890
    if (r0 != 63) goto L0200f68e
    r4 = r7 + 1860
    r0 = r4
    call console_helpers_nonce
    r0 = 1
    r1 = r7 + 1260
    b[r1+4] = r0
    r0 = [r1+0]
    r5 = sp + 55
    r0 = r5  #
    [r1+8] = r0
    r1 = r4
    call console_helpers_hex_text
    r4 = r7 + 3668
    r2 = r9 + 1182
    r1 = 80
    r0 = r4
    r3 = r5
    call L0200691e
    goto L0200f7de
L0200f688:
    r4 = r9 + 714
    goto L0200f7de
L0200f68e:
    r1 = sp + 48
    r2 = 10
    r0 = r6
    call capture_command_decimal  ; @call.xl
    r1 = 1264
    r2 = b[r7+r1] (u)
    r13 = r0
    if (r2 == 0) goto L0200f7d4
    r0 = r7 + 1260
    r1 = [r0+8]
    r4 = r9 + 906  #
    r2 = [r0+0]
    r3 = 0
    b[r0+4] = r3
    if (r1 != r2) goto L0200f7de
    r8 = [sp+48]  ; @ld.w.sp.l
    if (r8 == r6) goto L0200f7de
    r1 = b[r8+0] (u)
    if (r1 != 32) goto L0200f7de
    r1 = r8 + 1
    r2 = 0
    goto L0200f722
L0200f6d4:
    r3 = b[r1+r2] (s)
    r6 = r3 + -97
    r5 = r6 + 49
    r5 = r5.b0 (u)
    r3 += -87
    if (r5 > 9) goto L0200f6ec
    r3 += 39
    goto L0200f6fe
L0200f6ec:
    r5 = r6.b0 (u)
    if (r5 <= 5) goto L0200f6fe
    r5 = r6 + 32
    r5 = r5.b0 (u)
    if (r5 > 5) goto L0200f7de
    r3 += 32
L0200f6fe:
    ifs (r3 < 0) goto L0200f7de
    if ((r2 & 1) != 0) goto L0200f712
    r0 = r2 >>> 1
    r3 = r3 << 4
    r5 = sp + 32
    b[r5+r0] = r3
    goto L0200f720
L0200f712:
    r5 = r2 >>> 1
    r6 = sp + 32
    r0 = b[r6+r5] (u)
    r0 |= r3
    b[r6+r5] = r0
L0200f720:
    r2 += 1  ; @add.ri.u5
L0200f722:
    ifs (r2 <= 31) goto L0200f6d4
    r0 = b[r8+33] (u)
    r0 |= 32
    if (r0 != 32) goto L0200f7de
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r7 + 58
L0200f73c:
    testset b[r0]
    ifeq goto L0200f73c
    csync
    r0 = 1228
    r0 = b[r7+r0] (u)
    if (r0 == 0) goto L0200f8d8
    if (r13 > 3) goto L0200f8dc
    r0 = 6968
    r0 = b[r7+r0] (u)
    r0 = r0 & (1 << r13)
    if (r0 == 0) goto L0200f8dc
    r0 = r13 << 4
    r0 += r7  ; @add.rr
    r1 = r0 + 6912
    r2 = sp + 16
    r3 = r2 + 8
    rep 8 {
    r5 = b[r1++=1] (u)
    b[r3++=1] = r5
    }
    r0 = r0 + 6904
    rep 8 {
    r1 = b[r0++=1] (u)
    b[r2++=1] = r1
    }
    csync
    r6 = 0
    b[r7+58] = r6
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r7 + 1860
    r3_r2 = d[r0+8]
    r1_r0 = d[r0+0]
    d[sp+128] = r3_r2
    d[sp+120] = r1_r0
    r0 = sp + 120
    r0 += 16  ; @add.ri.u5
    r1 = r9 + 1196
    rep 13 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = sp + 356
    r0 += 16  ; @add.ri.u5
    r1 = 0
    r2 = 48
    call effect_enable_memset  ; @call.xl
    r1_r0 = d[sp+24]
    r3_r2 = d[sp+16]
    d[sp+364] = r1_r0
    d[sp+356] = r3_r2
    goto L0200f7fa
L0200f7d4:
    r0 = 0
    b[r7+r1] = r0
    r4 = r9 + 906
L0200f7de:
    r0 = r4
    sp += 420
    {pc, r13-r4} = [sp++]
L0200f7e4:
    r0 = sp + 356
    r0 = b[r0+r6] (u)
    r0 = r0 ^ 0x36
    r1 = sp + 292
    b[r1+r6] = r0
    r6 += 1  ; @add.ri.u5
L0200f7fa:
    if (r6 != 64) goto L0200f7e4
    r12 = r9 + 4110
    r0 = sp + 152
    r1 = r12
    r2 = r0
    rep 8 {
    r3 = [r1++=4]
    [r2++=4] = r3
    }
    r6 = 0
    r10 = 0  #
    [sp+248] = r6
    r11 = 0
    d[sp+252] = r11_r10
    r1 = sp + 292
    r2 = 64
    call console_helpers_hash_update
    r1 = sp + 120
    r2 = 29
    call console_helpers_hash_update
    r1 = sp + 260
    call console_helpers_hash_finish
    goto L0200f84e
L0200f838:
    r1 = sp + 356
    r1 = b[r1+r6] (u)
    r1 = r1 ^ 0x5C
    r2 = sp + 292
    b[r2+r6] = r1
    r6 += 1  ; @add.ri.u5
L0200f84e:
    if (r6 != 64) goto L0200f838
    r8 = sp + 152
    r1 = r8
    rep 8 {
    r2 = [r12++=4]
    [r1++=4] = r2
    }
    r6 = 0
    [r0+96] = r6
    d[r0+100] = r11_r10
    r1 = sp + 292
    r2 = 64
    r0 = r8
    call console_helpers_hash_update
    r1 = sp + 260
    r2 = 32
    call console_helpers_hash_update
    r10 = sp + 88
    r1 = r10
    call console_helpers_hash_finish
    r0 = sp + 0
    r1 = r0 + 8
    r2 = r10 + 8
    rep 8 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    rep 8 {
    r1 = b[r10++=1] (u)
    b[r0++=1] = r1
    }
    r0 = 0
    goto L0200f8b8
L0200f8a4:
    r1 = sp + 32
    r1 = b[r1+r0] (u)
    r2 = sp + 0
    r2 = b[r2+r0] (u)
    r1 ^= r2
    r1 = r1.b0 (u)
    r6 |= r1
    r0 += 1  ; @add.ri.u5
L0200f8b8:
    if (r0 != 16) goto L0200f8a4
    if (r6 != 0) goto L0200f7de
    r0 = 1
    r1 = r7 + 1252
    b[r1+0] = r0
    r2 = r13  #
    r0 = [r1+8]
    [r1+4] = r0
    r0 = 32
    r1 = -10
    call storage_coordination_notify
    r4 = r9
    goto L0200f7de
L0200f8d8:
    csync
    goto L0200f8de
L0200f8dc:
    csync
L0200f8de:
    r0 = 0
    b[r7+58] = r0
    call storage_coordination_irq_leave  ; @call.xl
    goto L0200f7de
