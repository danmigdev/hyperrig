; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; console_helpers: 4 functions, 0x0200f396..0x0200f63a

; console_helpers_nonce: 0x0200f396..0x0200f3e0, module console-helpers (nonce)
.type console_helpers_nonce,@function
console_helpers_nonce:
    [--sp] = {rets, r9-r4}
    r1 = 0
    r8 = 80640
    r9 = L01c1f180
    r4 = 2654435761
    r5 = 2027808484
    r6 = 0
    goto L0200f3da
L0200f3b6:
    r7 = [r8+0]
    r2 = [r9+24]
    r7 ^= r1
    r2 *= r4
    r2 ^= r7
    r7 = r0
    b[++r7=r6] = r2
    r3 = r2 >> 8
    b[r7+1] = r3
    r3 = r2 >> 16
    b[r7+2] = r3
    r2 = r2 >> 24
    r1 += r5  #  ; @add.rr.p
    b[r7+3] = r2
    r6 += 4  ; @add.ri.u5
L0200f3da:
    ifs (r6 < 16) goto L0200f3b6
    {pc, r9-r4} = [sp++]

; console_helpers_hex_text: 0x0200f3e0..0x0200f418, module console-helpers (hex_text)
.type console_helpers_hex_text,@function
console_helpers_hex_text:
    [--sp] = {rets, r5, r4}
    r2 = 0
    r3 = L020363ff  ; "0123456789abcdef"
    r4 = r0
    goto L0200f40c
L0200f3ee:
    r5 = b[r1+r2] (u)
    r5 = r5 >> 4
    r5 = b[r5+r3] (u)
    b[r4+0] = r5
    r5 = b[r1+r2] (u)
    r5 = r5 & 0xFFFFFF0F
    r5 = b[r5+r3] (u)
    b[r4+1] = r5
    r4 += 2  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L0200f40c:
    if (r2 != 16) goto L0200f3ee
    r1 = 0
    b[r0+32] = r1
    {pc, r5, r4} = [sp++]

; console_helpers_hash_update: 0x0200f418..0x0200f5c8, module console-helpers (hash_update)
.type console_helpers_hash_update,@function
console_helpers_hash_update:
    [--sp] = {rets, r15-r4}
    sp += -52
    r5_r4 = d[r0+100]
    r3 = 0
    r6 = r4 + r2
    r7 = r5 + r3 + c
    d[r0+100] = r7_r6
    r15 = L01c255dc
    d[sp] = r3_r2
    r8 = r2
    goto L0200f5c0
L0200f43a:
    r9 = r0 + 96  #
    r4 = b[r1++=1] (u)
    r2 = [r9+0]
    r3 = r2 + 1
    [r9+0] = r3
    r2 += r0  ; @add.rr
    b[r2+32] = r4
    r2 = [r9+0]
    r8 = r8 + -1
    if (r2 != 64) goto L0200f5c0
    r10 = [r0+28]
    r11 = [r0+24]
    r12 = [r0+20]
    r13 = [r0+16]
    r14 = [r0+12]
    r2 = [r0+8]
    [sp+48] = r2
    r2 = [r0+4]
    [sp+44] = r2
    r2 = [r0+0]
    [sp+40] = r2
    r4 = 0
    goto L0200f49e
L0200f480:
    r2 = r0 + r4
    r2 += 32
    r3 = b[r2+0] (u)
    r6 = b[r2+1] (u)
    r7 = b[r2+2] (u)
    r3 = r3 << 24
    r3 <= insert(r6, p:16, l:8)  #
    r2 = b[r2+3] (u)
    r3 <= insert(r7, p:8, l:8)
    r2 |= r3
    [r4+r15] = r2
    r4 += 4  ; @add.ri.u5
L0200f49e:
    if (r4 != 64) goto L0200f480
    r2 = 0
    goto L0200f4da
L0200f4a6:
    r4 = r15
    r3 = [++r4=r2]
    r6 = [r4+36]
    r3 += r6  #  ; @add.rr.p
    r7 = [r4+4]
    r6 = r7 >> 3
    r5 = r7 <> 18
    r5 ^= r6  #
    r6 = [r4+56]
    r7 = r7 <> 7
    r5 ^= r7
    r3 += r5  ; @add.rr
    r5 = r6 >> 10
    r7 = r6 <> 19
    r5 ^= r7
    r6 = r6 <> 17
    r5 ^= r6
    r3 += r5  ; @add.rr
    [r4+64] = r3
    r2 += 4  ; @add.ri.u5
L0200f4da:
    if (r2 != 192) goto L0200f4a6
    [sp+28] = r9  ; @st.w.sp.l
    [sp+32] = r8  ; @st.w.sp.l
    r1 = r13  #
    [sp+36] = r1
    r2 = 0
    [sp+12] = r13  ; @st.w.sp.l
    [sp+16] = r12  ; @st.w.sp.l
    r3 = r12
    [sp+20] = r11  ; @st.w.sp.l
    r12 = r11
    [sp+24] = r10  ; @st.w.sp.l
    r9 = r10
    [sp+8] = r14  ; @st.w.sp.l
    r11 = r14
    r10 = [sp+48]  ; @ld.w.sp.l
    r13 = [sp+44]  ; @ld.w.sp.l
    r14 = [sp+40]  ; @ld.w.sp.l
    goto L0200f578
L0200f516:
    r1 = r13 & r10
    r5 = r13 ^ r10
    r5 = r5 & r14
    r1 ^= r5
    r5 = r14 <> 13
    r6 = r14 <> 2
    r5 ^= r6
    r6 = r14 <> 22
    r5 ^= r6
    r5 += r1  ; @add.rr
    r1 = r12 & r3
    r6 = r8 & ~r3
    r1 ^= r6
    r6 = r3 <> 11
    r7 = r3 <> 6
    r6 ^= r7
    r7 = r3 <> 25
    r6 ^= r7
    r4 = L02035124
    r7 = [r4+r2<<2]
    r4 = [r15+r2<<2]
    r6 += r9
    r1 += r6  ; @add.rr
    r1 += r7  ; @add.rr
    r6 = r1 + r4
    r1 = r6 + r11
    r11 = r10
    r10 = r13
    r13 = r14
    r14 = r5 + r6
    r2 += 1  ; @add.ri.u5
    r9 = r8
L0200f578:
    r8 = r12
    r12 = r3
    r3 = r1
    if (r2 != 64) goto L0200f516
    r1 = [sp+40]
    r1 += r14
    [r0+0] = r1
    r1 = [sp+44]
    r1 += r13
    [r0+4] = r1
    r1 = [sp+48]
    r1 += r10
    [r0+8] = r1
    r1 = [sp+8]
    r1 += r11
    [r0+12] = r1
    r1 = [sp+12]
    r1 += r3  ; @add.rr
    [r0+16] = r1
    r1 = [sp+16]
    r1 += r12
    [r0+20] = r1
    r1 = [sp+20]
    r1 += r8
    [r0+24] = r1
    r1 = [sp+24]
    r1 += r9
    [r0+28] = r1
    r3_r2 = d[sp]
    r1 = [sp+28]
    [r1+0] = r3
    r1 = [sp+36]
    r8 = [sp+32]  ; @ld.w.sp.l
L0200f5c0:
    if (r8 != 0) goto L0200f43a
    sp += 52
    {pc, r15-r4} = [sp++]

; console_helpers_hash_finish: 0x0200f5c8..0x0200f63a, module console-helpers (hash_finish)
.type console_helpers_hash_finish,@function
console_helpers_hash_finish:
    [--sp] = {rets, r9-r4}
    sp += -12
    r4 = r1
    r7_r6 = d[r0+100]
    r1 = 128
    b[sp+11] = r1
    r1 = 0
    b[sp+10] = r1
    r1 = sp + 11
    goto L0200f5e4
L0200f5e2:
    r1 = sp + 10
L0200f5e4:
    r2 = 1
    call console_helpers_hash_update
    r1 = [r0+96]
    if (r1 != 56) goto L0200f5e2
    r7_r6 <<= 3
    r1 = sp + 2
    r2 = 56
    goto L0200f608
L0200f5fc:
    r9_r8 = r7_r6
    r9_r8 >>= r2
    b[r1++=1] = r8
    r2 += -8
L0200f608:
    if (r2 != -8) goto L0200f5fc
    r1 = sp + 2
    r2 = 8
    call console_helpers_hash_update
    r1 = 0
    goto L0200f632
L0200f618:
    r2 = r0 + r1
    r5 = r4  #
    r3 = b[r2+3] (u)
    b[++r5=r1] = r3
    r3 = h[r2+2] (u)
    b[r5+1] = r3
    r3 = [r2+0]
    r3 = r3 >> 8
    b[r5+2] = r3
    r2 = [r2+0]
    b[r5+3] = r2
    r1 += 4  ; @add.ri.u5
L0200f632:
    if (r1 != 32) goto L0200f618
    sp += 12
    {pc, r9-r4} = [sp++]
