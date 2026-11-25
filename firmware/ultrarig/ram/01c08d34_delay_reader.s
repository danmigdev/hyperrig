; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; delay_reader: 1 function, 0x01c08d34..0x01c08f80

; delay_reader_reader: 0x01c08d34..0x01c08f80, module delay-reader (reader)
.type delay_reader_reader,@function
delay_reader_reader:
    [--sp] = {rets, r15-r4}
    sp += -28
    r14 = r1
    r3 = r0 + 288
    if (r1 > 128) goto L01c08f7c
    r1 = [r3+36]
    [sp+20] = r1
    if (r1 < 146) goto L01c08f7c
    r2 = [r3+32]
    r1 = [r3+4]
    r4 = [r3+0]
    r4 = r0 + 396  #
    [sp+16] = r4
    r11 = [r0+84]
    [sp+4] = r3
    if (r2 == 0) goto L01c08d70
    r0 = [r4+4]
    if (r0 != 0) goto L01c08d70
    r0 = [r4+0]
    if (r0 != 0) goto L01c08d70
    r0 = r2 + 2048
    r1 = r0 >> 12
L01c08d70:
    r5 = [r4+24]
    r0 = L01c1f7f0
    r6 = [r0+20]
    r0 = 1
    r2 = 1
    if (r6 == r5) {
    r2 = 0
    }
    r3 = r6 + -1
    if (r3 == r5) {
    r0 = 0
    }
    r3 = r2 & r0
    [sp] = r3
    r5 = [sp+20]
    r3 = r5 + -1
    if (r1 >= r5) {
    r1 = r3
    }
    r3 = L01c32db0
    r3 = b[r3+9] (u)
    r3 *= r1
    r5 = 200
    r3 = r3 / r5 (u)
    r1 = r1 - r3
    if (r1 <= 144) {
    r1 = 144
    }
    r6 = r1
    if ((r2 & r0) != 0) goto L01c08dd0
    r0 = [r4+20]
    r6 = r0  #
    r2 = [sp+20]
    if (r0 >= r2) {
    r6 = r1
    }
    if (r0 <= 143) {
    r6 = r1
    }
L01c08dd0:
    [sp+8] = r4
    r13 = L01c31a84
    [sp+12] = r1
    if (r1 != r6) goto L01c08e46
    if (r14 == 0) goto L01c08ed2
    r2 = [sp+20]
    r0 = r2 << 1
    r8 = r11 + r0
    r1 = 0
    r0 = r2
    r2 = [sp+12]
    r3 = [sp+16]
    if (r3 >= r2) {
    r0 = 0
    }
    r3 = [sp+16]
    r2 = r3 - r2
    r2 = r2 + r0
L01c08dfe:
    r0 = r14 - r1
    r3 = r2 & 0xF
    r3 = 0x10 - r3
    r6 = umin(r3, r0)
    if (r6 == 0) goto L01c08e32
    r0 = r2 << 1
    r7 = r11 + r0
    r0 = r2 >> 4
    r0 = b[r8+r0] (u)
    r3 = r1 << 2
    r3 += r13
    r5 = 0
L01c08e22:
    r4 = h[r7+r5<<1] (s)
    r4 <<= r0
    [r3+r5<<2] = r4
    r5 = r5 + 1
    if (r5 < r6) goto L01c08e22
L01c08e32:
    r0 = r6 + r2  #
    r3 = [sp+20]
    r2 = 0
    if (r0 != r3) {
    r2 = r0
    }
    r1 = r1 + r6
    if (r1 < r14) goto L01c08dfe
    goto L01c08ed2
L01c08e46:
    if (r14 == 0) goto L01c08ed2
    r2 = [sp+12]
    r0 = r2 - r6
    r0 = r0 << 12
    r15 = r0 / r14 (s)  #
    r0 = [sp+20]
    r1 = r0 << 1
    r7 = r11 + r1
    r1 = r0 << 12
    r8 = r2 << 12
    r6 = r6 << 12
    r2 = 0
L01c08e66:
    r5 = r6 + r15
    r10 = r2 + 1
    r6 = r8
    if (r10 != r14) {
    r6 = r5
    }
    r0 = [sp+16]
    r3 = r2 + r0
    r3 = r3 << 12
    r3 = r3 + r1
    r5 = r3 - r6
L01c08e80:
    r9 = r5
    r5 = r5 - r1
    if (r9 >= r1) goto L01c08e80
    r12 = r9 >> 12  #
    r0 = [sp+20]
    r3 = r12 + 1
    r5 = 0
    if (r3 != r0) {
    r5 = r3
    }
    r3 = h[r11+r5<<1] (s)
    r5 = r5 >> 4
    r5 = b[r7+r5] (u)
    r4 = r9 >> 16
    r4 = b[r7+r4] (u)
    r0 = h[r11+r12<<1] (s)
    r3 <<= r5
    r0 <<= r4
    r3 = r3 - r0
    r4 = 4095
    r4 = r4 & r9
    r5_r4 = r3 * r4 (s)
    r5_r4 >>= 12
    r0 = r0 + r4
    [r13+r2<<2] = r0
    r2 = r10
    if (r2 != r14) goto L01c08e66
L01c08ed2:
    r2 = [sp]
    r3 = [sp+4]
    r1 = r3 + 136
    r0 = r3 + 124
    if (r2 != 0) goto L01c08ee2
    r0 = r1
L01c08ee2:
    r8 = [sp+8]
    r2 = [r8+12]
    r0 = [r0+0]
    r10 = [r3+12]
    [sp+24] = r0
    r9 = L01c1f7f0
    if (r2 == 0) goto L01c08f04
    r3 = sp + 24
    r0 = r13
    r1 = r14
    call sample_leaves_high_pass
    goto L01c08f2a
L01c08f04:
    if (r0 == 0) goto L01c08f2a
    if (r14 == 0) goto L01c08f1c
    r1 = r14
    r2 = r13
L01c08f0e:
    r3 = [r2+0]
    r3 = r3 - r0
    [r2++=4] = r3
    r3 = r0 >>> 9
    r0 = r0 - r3
    if (--r1 != 0) goto L01c08f0e
L01c08f1c:
    r2 = r0 + 511
    r1 = 0
    if (r2 >= 1023) {
    r1 = r0
    }
    [sp+24] = r1
L01c08f2a:
    if (r14 == 0) goto L01c08f68
    r0 = [r9+44]
    r11 = r10 >>> 31
    r1 = 2147483647
    goto L01c08f46
L01c08f3e:
    r2 = r3 >> 31
    r2 = r2 << 1
    r2 = r2 + r1
    goto L01c08f62
L01c08f46:
    r2 = [r13++=4]
    r7_r6 = r2 * r10 (s)  #
    r4 = [r0+0]
    r7_r6 >>>= 16
    r5 = r4 >>> 31
    r2 = r6 + r4
    r3 = r7 + r5 + c
    r4 = r2 >>> 31
    if (r3 != r4) goto L01c08f3e
L01c08f62:
    [r0++=4] = r2
    if (--r14 != 0) goto L01c08f46
L01c08f68:
    r0 = [sp+12]
    [r8+20] = r0
    r0 = [sp+24]
    [r8+28] = r0
    r0 = [r9+20]
    [r8+24] = r0
L01c08f7c:
    sp += 28
    {pc, r15-r4} = [sp++]
