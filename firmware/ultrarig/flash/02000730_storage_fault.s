; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_fault: 9 functions, 0x02000730..0x020009ca

; storage_fault_tag: 0x02000730..0x02000758, module storage-fault (tag)
.type storage_fault_tag,@function
storage_fault_tag:
    r1 = 4293918720
    r1 &= r0
    r2 = 2782920704
    r0 = 1
    if (r1 == r2) goto L02000756
    r2 = r2 + 0x2A800000
    if (r1 == r2) goto L02000756
    r2 = r2 + 0x17600000
    if (r1 != r2) {
    r0 = 0
    }
L02000756:
    rts

; storage_fault_record_count: 0x02000758..0x0200077c, module storage-fault (record_count)
.type storage_fault_record_count,@function
storage_fault_record_count:
    r1 = 29883296
    r0 = [r1+0]
    r2 = r0 >> 16
    r3 = 51109
    r0 = 0
    if (r2 != r3) goto L0200077a
    r2 = [r1+0]
    r2 = r2.l (u)
    if (r2 <= 2) {  ; @if.le.ri.s12
    r0 = [r1+0]
    r0 = r0.l (u)
    }
L0200077a:
    rts

; storage_fault_append: 0x0200077c..0x02000800, module storage-fault (append)
.type storage_fault_append,@function
storage_fault_append:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = [r4+0]
    call storage_fault_tag
    if (r0 == 0) goto L020007fe
    call storage_fault_record_count
    if (r0 == 0) goto L020007aa
    r1 = 0
    r2 = 29883300
L02000792:
    if (r1 > 5) goto L020007a6
    r3 = [r2+r1<<2]
    r5 = [r4+r1<<2]
    r1 += 1  ; @add.ri.u5
    if (r3 == r5) goto L02000792
    goto L020007aa
L020007a6:
    if (r1 == 6) goto L020007fe
L020007aa:
    r1 = 1
    if (r0 >= 2) {  ; @if.ge.ri.s12
    r1 = 0
    }
    r0 += r1  ; @add.rr
    r1 = r0 * 0x18
    r2 = 29883276
    r1 += r2  ; @add.rr
    r2 = r0
    goto L020007d4
L020007c4:
    r3 = 6
    r5 = r1
    goto L020007d0
L020007ca:
    r6 = [r5+-24]
    [r5++=4] = r6
    r3 += -1
L020007d0:
    if (r3 != 0) goto L020007ca
    r1 += -24
L020007d4:
    if (--r2 != 0) goto L020007c4
    r1 = 0
    r2 = 29883300
    goto L020007ec
L020007e2:
    r3 = [r4+r1<<2]
    [r2+r1<<2] = r3
    r1 += 1  ; @add.ri.u5
L020007ec:
    if (r1 != 6) goto L020007e2
    r1 = 3349479424
    r0 |= r1
    r1 = r2 + -4
    [r1+0] = r0
L020007fe:
    {pc, r6-r4} = [sp++]

; storage_fault_checksum: 0x02000800..0x02000830, module storage-fault (checksum)
.type storage_fault_checksum,@function
storage_fault_checksum:
    r3 = 2246822507
    r2 *= r3
    r3 = 2654435761
    r1 *= r3
    r0 ^= r1
    r0 ^= r2
    r1 = 2082409309
    r0 ^= r1
    r1 = r0 >> 15
    r0 ^= r1
    r1 = 739982445
    r0 *= r1
    r1 = r0 >> 12
    r0 ^= r1
    r0 = r0.l (u)
    rts

; storage_fault_decode: 0x02000830..0x0200088e, module storage-fault (decode)
.type storage_fault_decode,@function
storage_fault_decode:
    [--sp] = {rets, r7-r4}
    r1 = 29883348
    r6 = [r1+0]
    r5 = [r1+4]
    r4 = r0  #
    r7 = [r1+8]
    r2 = r7.l (u)
    r0 = r6
    r1 = r5
    call storage_fault_checksum
    r1 = r0
    r2 = r7 >> 16
    r0 = 0
    if (r2 != r1) goto L0200088c
    r1 = r5 >> 25
    if (r1 > 2) goto L0200088c
    if ((r7 & 0xFF) == 0) goto L0200088c
    r1 = r7 & 0xF0
    if (r1 > 15) goto L0200088c
    r0 = 1
    if (r4 == 0) goto L0200088c
    r1 = r5 >> 24
    h[r4+0] = r6
    r2 = r6 >> 16
    h[r4+2] = r2
    b[r4+4] = r5
    r2 = r5 >> 8
    r2 = uextra(r5, p:16, l:4)  #
    b[r4+5] = r2
    r2 = uextra(r5, p:20, l:4)  #
    b[r4+6] = r2
    b[r4+7] = r2
    b[r4+8] = r1
    b[r4+9] = r7
    r1 = r7 >> 8
    b[r4+10] = r1
L0200088c:
    {pc, r7-r4} = [sp++]

; storage_fault_encode: 0x0200088e..0x020008ee, module storage-fault (encode)
.type storage_fault_encode,@function
storage_fault_encode:
    [--sp] = {rets, r10-r4}
    r1 = r0
    r2 = h[r1+2] (u)
    r0 = h[r1+0] (u)
    r0 <= insert(r2, p:16, l:16)  #
    r4 = b[r1+9] (u)
    r9 = b[r1+10] (u)
    r10 = b[r1+7] (u)
    r6 = b[r1+6] (u)
    r7 = b[r1+5] (u)
    r3 = b[r1+8] (u)
    r1 = b[r1+4] (u)
    r8 = 29883348
    [r8+0] = r0
    r2 = r3 << 24
    r5 = 0x5000000
    if (r3 <= 5) {  ; @if.le.ri.s12
    r5 = r2
    }
    r1 <= insert(r7, p:8, l:8)
    r2 = r6 & 0xFFFFFF0F
    r1 <= insert(r2, p:16, l:4)
    r2 = r10 & 0xFFFFFF0F
    r1 <= insert(r2, p:20, l:4)
    r1 |= r5
    [r8+4] = r1
    r4 <= insert(r9, p:8, l:8)
    r2 = r4
    call storage_fault_checksum
    r4 <= insert(r0, p:16, l:16)
    [r8+8] = r4
    {pc, r10-r4} = [sp++]

; storage_fault_update: 0x020008ee..0x02000952, module storage-fault (update)
.type storage_fault_update,@function
storage_fault_update:
    [--sp] = {rets, r5, r4}
    sp += -12
    r5_r4 = r1_r0
    r0 = sp + 0
    call storage_fault_decode
    if (r0 == 0) goto L02000910
    if (r5 == 0) goto L02000914
    r1 = b[sp+7] (u)
    r0 = r1 + 1
    if (r1 >= 15) {  ; @if.ge.ri.s12
    r0 = 15
    }
    b[sp+7] = r0
L0200090c:
    r0 = sp + 0
    call storage_fault_encode
L02000910:
    sp += 12
    {pc, r5, r4} = [sp++]
L02000914:
    if (r4 == 2) goto L0200092e
    if (r4 != 1) goto L02000940
    r1 = b[sp+4] (u)
    r0 = r1 + 1
    if (r1 == 255) {  ; @if.eq.ri.s12
    r0 = -1
    }
    b[sp+4] = r0
    goto L0200090c
L0200092e:
    r1 = b[sp+5] (u)
    r0 = r1 + 1
    if (r1 == 255) {  ; @if.eq.ri.s12
    r0 = -1
    }
    b[sp+5] = r0
    goto L0200090c
L02000940:
    r1 = b[sp+6] (u)
    r0 = r1 + 1
    if (r1 >= 15) {  ; @if.ge.ri.s12
    r0 = 15
    }
    b[sp+6] = r0
    goto L0200090c

; storage_fault_once: 0x02000952..0x0200096e, module storage-fault (once)
.type storage_fault_once,@function
storage_fault_once:
    [--sp] = rets
    r1 = L01c26890
    r2 = b[r1+8] (u)
    if (r2 != 0) goto L0200096c
    r2 = 1
    b[r1+8] = r2
    r1 = [r1+104]
    r1 = uextra(r1, p:11, l:1)
    call storage_fault_update
L0200096c:
    pc = [sp++]

; storage_fault_fatal: 0x0200096e..0x020009ca, module storage-fault (fatal)
.type storage_fault_fatal,@function
storage_fault_fatal:
    r5 = rets
    r6 = cnum
    r4 = 29883864
    r0 = r4
    call storage_fault_append
    r0 = 3
    call storage_fault_once
    r0 = L01c26890
    r0 = [r0+104]
    r0 |= r6
    r1 = 2782920704
    r0 |= r1
    [r4+0] = r0
    r0 = 0
    [r4+8] = r0
    [r4+4] = r0
    [r4+12] = r5
    [r4+16] = r0
    r0 = 1
    if (r6 == 0) goto L020009ac
    r0 = 0
L020009ac:
    r1 = 32436348
    r1 <= insert(r0, p:9, l:1)
    r0 = [r1+0]
    [r4+20] = r0
    r0 = 160
    r1 = 4
    r2 = 1
    r3 = 1
    call storage_fault_masked_register  ; @call.xl
L020009c8:
    goto L020009c8
