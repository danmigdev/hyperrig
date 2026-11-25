; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; colour_frames: 1 function, 0x02015130..0x02015210

; colour_frames_led_send: 0x02015130..0x02015210, module colour-frames (led_send)
.type colour_frames_led_send,@function
colour_frames_led_send:
    [--sp] = {rets, r13-r4}
    sp += -4
    r0 = 944
    r9 = L01c26890
    r1 = b[r9+r0] (u)
    r8 = 72960
    if (r1 != 0) goto L02015172
    r1 = 331808
    [r1+0] |= 0x10
    r1 = r1 + -4000
    [r1+0] &= 0xFFFFFBFF
    [r1+8] &= 0xFFFFFBFF
    [r8+4] = 0x9
    r1 = 16417
    [r8+0] = r1
    r1 = 1
    b[r9+r0] = r1
L02015172:
    r1 = 852
    r0 = b[r9+r1] (u)
    if (r0 == 0) goto L02015186
    r2 = [r8+0]
    r0 = -1
    if ((r2 & 32768) == 0) goto L0201520c
L02015186:
    [r8+0] |= 0x4000
    r0 = 1
    b[r9+r1] = r0
    r1_r0 = 0
    r10 = L01c245a0
    goto L020151a0
L0201519a:
    b[r1+r10] = r0
    r1 += 1  ; @add.ri.u5
L020151a0:
    if (r1 != 36) goto L0201519a
    r11 = r10 + 36
    r4 = sp + 1
    r12 = 0
    r6 = 1
    goto L020151fe
L020151b0:
    r0 = r12 * 0x3
    r0 += r9
    r0 = r0 + 2524
    r1 = b[r0+1] (u)
    r2 = b[r0+0] (u)
    r0 = b[r0+2] (u)
    b[sp+1] = r1
    r1 = r11  #
    b[r4+1] = r2
    b[r4+2] = r0
    r7 = 0
    goto L020151f2
L020151ce:
    r13 = r1 + 8
    r0 = 7
    goto L020151ea
L020151d6:
    r5 = b[r4+r7] (u)
    r2 = r6 << r0
    r3 = 126
    if ((r5 & r2) == 0) {
    r3 = 96
    }
    b[r1++=1] = r3
    r0 += -1
L020151ea:
    if (r0 != -1) goto L020151d6
    r7 += 1  ; @add.ri.u5
    r1 = r13
L020151f2:
    if (r7 != 3) goto L020151ce
    r12 = r12 + 1
    r11 = r11 + 24
L020151fe:
    if (r12 != 12) goto L020151b0
    [r8+12] = r10
    [r8+16] = 0x144
    r0 = 0
L0201520c:
    sp += 4
    {pc, r13-r4} = [sp++]
