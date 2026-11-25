; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201bafa..0x0201c17c: vendor code (JieLi SDK or library, not reversed), as instructions
L0201bafa:
    [--sp] = rets
    r1 = 10
    call L0201b896
    pc = [sp++]
L0201bb04:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = b[r4+25] (u)
    r5 = r0 & 0xFFFFFF01
    r0 = r5
    call L0201b838
    if ((r0 & 2) != 0) goto L0201bb54
    r6 = h[r4+2] (u)
    if (r6 == 0) goto L0201bb4c
    if (r6 >= 64) {  ; @if.ge.ri.s12
    r6 = 64
    }
    r0 = r5  #
    r1 = [r4+8]
    r2 = r6
    call L0201b966
    [r4+8] += r6
    r0 = h[r4+2] (u)
    r0 = r0 - r6
    r1 = r0.l (u)  #
    h[r4+2] = r0
    if (r1 != 0) goto L0201bb42
    r0 = b[r4+21] (u)
    if (r0 == 0) goto L0201bb4c
L0201bb42:
    r1 = 2
    r0 = r5
    call L0201b896
    {pc, r6-r4} = [sp++]
L0201bb4c:
    r0 = r5
    call L0201bafa
    r0 = 0
    b[r4+1] = r0
L0201bb54:
    {pc, r6-r4} = [sp++]
L0201bb56:
    [--sp] = {rets, r13-r4}
    r7 = r0 + 20
    r12 = r0  #
    r0 = b[r7+5] (u)
    r9 = L01c26890
    r4 = r9 + 1656
    r5 = r0 & 0xFFFFFF01
    r0 = [r4+r5<<2]
    if (r0 == 0) goto L0201c06c
    r1 = b[r7+3] (u)
    if ((r1 & 2) == 0) goto L0201bb92
    r1 = 3
    b[r0+20] = r1
    r1 = b[r12+0] (u)
    r0 = r5
    call L0201b72c
    r0 = b[r7+3] (u)
    r0 &= 4294967293
    b[r7+3] = r0
L0201bb92:
    r0 = r5
    call L0201b838
    r6 = r0
    if ((r6 & 4) != 0) goto L0201bbec
    if ((r6 & 16) != 0) goto L0201bc06
    r0 = b[r12+1] (u)
    if (r0 > 4) goto L0201c06c
    r1 = r0 << 1
    r10 = r12 + 1
    tbh [r1]
L0201bbb4:
    .short (L0201bc42 - L0201bbb4) / 2, (L0201c064 - L0201bbb4) / 2, (L0201bbbe - L0201bbb4) / 2, (L0201c06c - L0201bbb4) / 2, (L0201bc1a - L0201bbb4) / 2
L0201bbbe:
    if ((r6 & 0x1) == 0) goto L0201c06c
    r2 = [r12+16]
    r0 = b[r7+5] (u)
    r5 = r0 & 0xFFFFFF01
    if (r2 == 0) goto L0201bd52
    r0 = [r4+r5<<2]
    r1 = r0 + 28
    r0 = r12
    call r2
    r1 = r0.b0 (u)
    b[r12+1] = r0
    if (r1 == 2) goto L0201bda8
    if (r1 == 0) goto L0201bd58
    {pc, r13-r4} = [sp++]
L0201bbec:
    r1 = 0
    r4 = 0
    r0 = r5
    call L0201b896
    r0 = b[r12+1] (u)
    if (r0 == 4) goto L0201c06c
    b[r12+1] = r4
    {pc, r13-r4} = [sp++]
L0201bc06:
    r1 = 128
    r0 = r5
    call L0201b896
    r0 = b[r12+1] (u)
    r10 = r12 + 1
    if (r0 != 4) goto L0201bc3c
L0201bc1a:
    if ((r6 & 0x1) == 0) goto L0201c06c
    r0 = 0
    b[r10+0] = r0
    if (r5 != 0) goto L0201c06c
    r1 = 0
    call L0201b72c
    r0 = 0x51000
    [r0+0] &= 0xFFFFF6FF
    {pc, r13-r4} = [sp++]
L0201bc3c:
    r0 = 0
    b[r12+1] = r0
L0201bc42:
    if ((r6 & 0x1) == 0) goto L0201c06c
    r5 = 414  #
    r0 = b[r7+5] (u)
    r13 = r0 & 0xFFFFFF01
    r0 = r13 << 2
    r6 = r0 + r9
    r0 = [r6+r5<<2]
    r1 = r0 + 28
    r2 = 8
    r0 = r13
    call L0201b8f2
    r1 = [r6+r5<<2]
    r0 = b[++r1=28] (u)
    r2 = 3
    b[r10+0] = r2
    r2 = [r12+12]
    r6 = r0 & 0xFFFFFF1F
    if (r2 == 0) goto L0201bc88
    r0 = r12
    call r2
    if (r0 == 0) goto L0201bc88
    r6 = -1
L0201bc88:
    r11 = L02035cb0
    if (r6 == 2) goto L0201bcee
    if (r6 == 1) goto L0201bd26
    if (r6 != 0) goto L0201bfec
    r0 = [r4+r13<<2]
    r6 = r0 + 28
    r0 = b[r6+1] (u)
    if (r0 > 9) goto L0201bfec
    r1 = b[r7+5] (u)
    r9 = [r12+4]
    r2 = r0 << 1
    r8 = r1 & 0xFFFFFF01
    tbh [r2]
L0201bcb8:
    .short (L0201bccc - L0201bcb8) / 2, (L0201bdb0 - L0201bcb8) / 2, (L0201bfec - L0201bcb8) / 2, (L0201bdda - L0201bcb8) / 2, (L0201bfec - L0201bcb8) / 2, (L0201be04 - L0201bcb8) / 2, (L0201be36 - L0201bcb8) / 2, (L0201bfec - L0201bcb8) / 2
    .short (L0201be56 - L0201bcb8) / 2, (L0201be6c - L0201bcb8) / 2
L0201bccc:
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L0201bf6a
    r0 = 0
    b[r9+0] = r0
    b[r9+1] = r0
    r0 = b[r7+3] (u)
    if ((r0 & 0x1) != 0) {
    r0 = 2
    b[r9+0] = r0
    }
    r3 = 2
    goto L0201bfe2
L0201bcee:
    r0 = [r4+r13<<2]
    r1 = r0 + 28
    r3 = b[r1+5] (u)
    r0 = b[r1+4] (u)
    r0 <= insert(r3, p:8, l:8)  #
    r2 = b[r1+1] (u)
    r8 = r0 & 0xF  #
    r4 = b[r7+5] (u)
    r6 = r4 & 0xFFFFFF01
    if (r2 == 0) goto L0201bd60
    if (r2 == 3) goto L0201bd92
    if (r2 != 1) goto L0201bfec
    r2 = b[r7+0] (u)
    if (r2 == 2) goto L0201bf6a
    if (r2 == 4) goto L0201bec0
    if (r2 == 3) goto L0201bda2
    goto L0201bfec
L0201bd26:
    r0 = [r4+r13<<2]
    r1 = b[r0+32] (u)
    if (r1 > 7) goto L0201bfec
    r2 = b[r7+5] (u)
    r2 = r2 & 0xFFFFFF01
    r2 = [r4+r2<<2]
    r2 += 36
    r2 = [r2+r1<<2]
    if (r2 == 0) goto L0201bfec
    r1 = r0 + 28
    r0 = r12
    call r2
    goto L0201bfec
L0201bd52:
    r0 = 0
    b[r12+1] = r0
L0201bd58:
    r0 = r5
    call phase3_p13_usb_ep0_RxPktEnd
    {pc, r13-r4} = [sp++]
L0201bd60:
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L0201bf6a
    r2 = [r12+4]
    if (r0 == 4) goto L0201beda
    if (r0 != 3) goto L0201bfec
    if (r8 != 0) goto L0201bf6a
    r0 = 0
    b[r2+0] = r0
    b[r2+1] = r0
    r0 = b[r1+4] (s)
    ifs (r0 > -1) goto L0201bef6
    r0 = r9 + 1372
    r0 = h[r0+r6<<1] (u)
    goto L0201beec
L0201bd92:
    r1 = b[r7+0] (u)
    if (r1 == 2) goto L0201bf6a
    if (r1 == 4) goto L0201befc
    if (r1 != 3) goto L0201bfec
L0201bda2:
    if (r8 != 0) goto L0201bf6a
    goto L0201bfbe
L0201bda8:
    r0 = r5
    call phase3_p13_usb_ep0_ClrRxPktRdy
    {pc, r13-r4} = [sp++]
L0201bdb0:
    r0 = b[r6+2] (u)
    if (r0 == 2) goto L0201bf60
    if (r0 != 1) goto L0201bfec
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L0201bf6a
    if (r0 == 4) goto L0201bdcc
    if (r0 != 3) goto L0201bfec
L0201bdcc:
    r0 = 0
    b[r10+0] = r0
    r0 = b[r7+3] (u)
    r0 &= 4294967294
    b[r7+3] = r0
    goto L0201bfec
L0201bdda:
    r1 = b[r6+3] (u)
    r0 = b[r6+2] (u)
    r0 <= insert(r1, p:8, l:8)
    r1 = r0.b0 (u)
    if (r1 != 1) goto L0201bf20
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L0201bf6a
    if (r0 == 4) goto L0201bdf6
    if (r0 != 3) goto L0201bfec
L0201bdf6:
    r0 = 0
    b[r10+0] = r0
    r0 = b[r7+3] (u)
    r0 |= 1
    b[r7+3] = r0
    goto L0201bfec
L0201be04:
    r0 = b[r7+0] (u)
    if (r0 == 4) goto L0201bf6a
    r8 = b[r6+2] (u)
    if (r8 == 128) goto L0201bf6a
    r0 = b[r6+5] (u)
    r1 = b[r6+4] (u)
    r1 <= insert(r0, p:8, l:8)
    if (r1 != 0) goto L0201be2a
    r0 = b[r6+7] (u)
    r1 = b[r6+6] (u)
    r1 <= insert(r0, p:8, l:8)
    if (r1 == 0) goto L0201c06e
L0201be2a:
    b[r12+0] = r8
    r0 = 4
    b[r10+0] = r0
    goto L0201c01e
L0201be36:
    r1 = b[r6+3] (u)
    r0 = b[r6+2] (u)
    r0 <= insert(r1, p:8, l:8)
    r1 = r0 >> 8
    if (r1 == 3) goto L0201bf72
    if (r1 == 2) goto L0201bf88
    if (r1 != 1) goto L0201bfec
    r0 = r9
    call phase3_p13_get_device_descriptor
    r3 = 18
    goto L0201bfe2
L0201be56:
    r0 = b[r7+0] (u)
    if (r0 == 2) goto L0201bf6a
    r1 = 1
    if (r0 != 4) {  ; @if.ne.ri.s12
    r1 = 0
    }
    b[r9+0] = r1
    r3 = 1
    goto L0201bfe2
L0201be6c:
    r0 = b[r6+5] (u)
    r1 = b[r6+4] (u)
    r1 <= insert(r0, p:8, l:8)
    if (r1 != 0) goto L0201bf6a
    r0 = b[r6+7] (u)
    r1 = b[r6+6] (u)
    r1 <= insert(r0, p:8, l:8)
    if (r1 != 0) goto L0201bf6a
    r0 = [r4+r8<<2]
    r1 = b[++r0=20] (u)
    if (r1 == 2) goto L0201bf6a
    r1 = b[r6+2] (u)
    if (r1 == 1) goto L0201c080
    if (r1 != 0) goto L0201bf6a
    r1 = 0
    b[r10+0] = r1
    r1 = 3
    r0 = r8  #
    b[r0+0] = r1
    r1 = 1
    call phase3_p13_usb_disable_ep
    r1 = 2
    r0 = r8
    call phase3_p13_usb_disable_ep
    r1 = 3
    r0 = r8
    call phase3_p13_usb_disable_ep
    r1 = 4
    r0 = r8
    call phase3_p13_usb_disable_ep
    goto L0201bfec
L0201bec0:
    r1 = b[r1+2] (u)
    if (r1 != 0) goto L0201bfec
    if ((r0 & 128) != 0) goto L0201bfa4
    r2 = 128
    r0 = r6
    r1 = r8
    call L02005d1c
    r0 = r9 + 1368
    goto L0201bfb2
L0201beda:
    r0 = 0
    b[r2+0] = r0
    r0 = r9 + 1372  #
    b[r2+1] = r0
    r0 = h[r0+r6<<1] (u)
    r3 = b[r1+4] (s)
L0201beec:
    r0 = r0 & (1 << r8)
    if (r0 == 0) goto L0201bef6
    r0 = 1
    b[r2+0] = r0
L0201bef6:
    r3 = 2
    r0 = r12
    goto L0201bfe8
L0201befc:
    r3 = 0
    r1 = r6 << 1
    r1 += r9
    r2 = r1 + 1368
    r1 = r1 + 1372
    r0 = r0.b0 (s)
    b[r10+0] = r3
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r1 = r2
    }
    r0 = h[r1+0] (u)
    r0 = r0 | (1 << r8)
    h[r1+0] = r0
    goto L0201bfec
L0201bf20:
    if (r0 != 2) goto L0201bfec
    if (r8 == 0) goto L0201bf6a
    r0 = b[++r6=4] (u)
    if (r0 != 0) goto L0201bfec
    r1 = 72
    r0 = r8
    call L0201b896
    r0 = 1000
    call L02040d68  ; @call.xl
    r0 = 0
    b[r10+0] = r0
    r0 = b[r6+1] (u)
    r0 += -1
    if (r0 > 3) goto L0201c012
    r4 = 90127
    tbb [r0]
L0201bf56:
    .byte (L0201bf5a - L0201bf56) / 2, (L0201c08c - L0201bf56) / 2, (L0201c092 - L0201bf56) / 2, (L0201c098 - L0201bf56) / 2
L0201bf5a:
    r0 = 2
    b[r4+0] = r0
    goto L0201bfec
L0201bf60:
    r0 = b[r7+0] (u)
    r0 += -2
    r0 = r0.b0 (u)
    if (r0 >= 3) goto L0201bfec
L0201bf6a:
    r0 = 3
    b[r10+0] = r0
    goto L0201c004
L0201bf72:
    r0 = r0 & 0xFFFF00FF
    if (r0 > 3) goto L0201bf92
    tbb [r0]
L0201bf7c:
    .byte (L0201bf80 - L0201bf7c) / 2, (L0201bfc6 - L0201bf7c) / 2, (L0201bfce - L0201bf7c) / 2, (L0201bfd6 - L0201bf7c) / 2
L0201bf80:
    r0 = r9
    call L0201b9f6
    goto L0201bfdc
L0201bf88:
    r1_r0 = r9_r8
    call phase3_p5_set_descriptor
    r3 = r0
    goto L0201bfe0
L0201bf92:
    if (r0 == 238) goto L0201bfdc
    r0 = 3
    b[r10+0] = r0
    r0 = 0
    b[r9+0] = r0
    goto L0201bfdc
L0201bfa4:
    r2 = 64
    r0 = r6
    r1 = r8
    call L02006af8
    r0 = r9 + 1372
L0201bfb2:
    r1 = h[r0+r6<<1] (u)
    r1 = r1 & ~(1 << r8)
    h[r0+r6<<1] = r1
L0201bfbe:
    r0 = 0
    b[r10+0] = r0
    goto L0201c012
L0201bfc6:
    r0 = r9
    call phase3_p13_get_manufacture_str
    goto L0201bfdc
L0201bfce:
    r0 = r9
    call phase3_p13_get_product_str
    goto L0201bfdc
L0201bfd6:
    r0 = r9
    call phase3_p13_get_iserialnumber_str
L0201bfdc:
    r3 = b[r9+0] (u)
L0201bfe0:
    if (r3 == 0) goto L0201bfec
L0201bfe2:
    r0 = r12
    r1 = r6
    r2 = r9
L0201bfe8:
    call L0201ba8a
L0201bfec:
    r0 = b[r10+0] (u)
    if (r0 > 4) goto L0201c06c
    tbb [r0]
L0201bff6:
    .byte (L0201c012 - L0201bff6) / 2, (L0201bffc - L0201bff6) / 2, (L0201bffc - L0201bff6) / 2, (L0201c004 - L0201bff6) / 2, (L0201c01a - L0201bff6) / 2
    .byte 0x00  ; alignment
L0201bffc:
    r0 = r13
    call phase3_p13_usb_ep0_ClrRxPktRdy
    goto L0201c05c
L0201c004:
    r0 = 0
    b[r10+0] = r0
    r0 = r13
    call phase3_p13_usb_ep0_Set_Stall
    goto L0201c05c
L0201c012:
    r0 = r13
    call phase3_p13_usb_ep0_RxPktEnd
    goto L0201c05c
L0201c01a:
    r8 = b[r12+0] (u)
L0201c01e:
    if (r13 != 0) goto L0201c056
    r0 = 0
    call phase3_p13_usb_ep0_Set_Stall
L0201c028:
    r0 = 0
    call L0201b838
    if ((r0 & 4) == 0) goto L0201c028
    r0 = [r11+r13<<2]
L0201c036:
    r1 = [r0+0]
    if ((r1 & 0x30000) != 0) goto L0201c036
    r0 = r11 + 8
    r0 = [r0+r13<<2]
    r1 = 2316
    [r0+0] |= r1
    r0 = 0
    r1 = r8
    call L0201b72c
L0201c056:
    r0 = b[r7+3] (u)
    r0 &= 4294967293
    b[r7+3] = r0
L0201c05c:
    r0 = b[r10+0] (u)
    if (r0 != 1) goto L0201c06c
L0201c064:
    r0 = r12
    call L0201bb04
    {pc, r13-r4} = [sp++]
L0201c06c:
    {pc, r13-r4} = [sp++]
L0201c06e:
    b[r12+0] = r8
    r0 = 0
    b[r10+0] = r0
    r0 = b[r7+3] (u)
    r0 |= 2
    b[r7+3] = r0
    goto L0201bfec
L0201c080:
    r1 = 0
    b[r10+0] = r1
    r1 = 4
    b[r0+0] = r1
    goto L0201bfec
L0201c08c:
    r0 = 4
    b[r4+0] = r0
    goto L0201bfec
L0201c092:
    r0 = 1
    b[r4+0] = r0
    goto L0201bfec
L0201c098:
    r1 = r11 + 6085
    r2 = 53
    r0 = r8
    call L0201b966
    r1 = 2
    r0 = r8
    call L0201b896
    r0 = 8
    b[r4+0] = r0
    r0 = 54
    call phase3_p13_unrequest_irq
    r0 = 5
    b[r10+0] = r0
    {pc, r13-r4} = [sp++]
L0201c0be:
    [--sp] = {psr, rets, reti}
    [--sp] = {r8-r0}
    sp += -24
    ssync
    r1 = sp + 20
    r2 = sp + 12
    r3 = sp + 4
    r0 = 0
    call L0201b60a
    r1 = sp + 16
    r2 = sp + 8
    r3 = sp + 0
    r0 = 0
    call L0201b6a2
    r0 = 0
    call L02001e72
    r4 = r0  #
    r1 = [sp+16]
    r2 = [sp+20]
    r1 &= r2  #
    r0 = [sp+8]
    r3 = [sp+12]
    r7 = r3 & r0  #
    r2 = [sp]
    r5 = [sp+4]
    r6 = r5 & r2  #
    [sp+20] = r1
    [sp+12] = r7
    [sp+4] = r6
    if ((r1 & 0x4) != 0) {
    r0 = r4
    call L0201b77e
    }
    r8 = L01c26890
    if ((r7 & 1) == 0) goto L0201c130
    r0 = 640
    r2 = [r8+r0<<2]
    if (r2 == 0) goto L0201c12a
    r1 = 0
    r0 = r4
    call r2
    goto L0201c130
L0201c12a:
    r0 = r4
    call L0201bb56
L0201c130:
    r0 = 0
    goto L0201c14c
L0201c134:
    r5 = r0 + 1
    r1 = r7 & (1 << r5)
    if (r1 == 0) goto L0201c14a
    r1 = r8 + 2604
    r2 = [r1+r0<<2]
    if (r2 == 0) goto L0201c14a
    r1_r0 = r5_r4
    call r2
L0201c14a:
    r0 = r5
L0201c14c:
    if (r0 != 4) goto L0201c134
    r0 = 0
    goto L0201c16c
L0201c154:
    r5 = r0 + 1
    r1 = r6 & (1 << r5)
    if (r1 == 0) goto L0201c16a
    r1 = r8 + 2564
    r2 = [r1+r0<<2]
    if (r2 == 0) goto L0201c16a
    r1_r0 = r5_r4
    call r2
L0201c16a:
    r0 = r5
L0201c16c:
    if (r0 != 4) goto L0201c154
    csync
    sp += 24
    {r8-r0} = [sp++]
    {psr, rets, reti} = [sp++]
    rti
