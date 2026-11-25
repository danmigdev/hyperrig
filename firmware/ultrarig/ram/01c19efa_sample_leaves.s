; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; sample_leaves: 1 function, 0x01c19efa..0x01c19fba

; sample_leaves_chunk_peaks: 0x01c19efa..0x01c19fba, module sample-leaves (chunk_peaks)
.type sample_leaves_chunk_peaks,@function
sample_leaves_chunk_peaks:
    [--sp] = {r9-r4}
L01c19efc:
    r8 = 0
    r9 = 0
    r4 = [r0+0]
    r5 = [r0+4]
    r6 = [r0+8]
    r7 = [r0+12]
    r8 = smax(r8, r4)
    r9 = smin(r9, r4)
    r8 = smax(r8, r5)
    r9 = smin(r9, r5)
    r8 = smax(r8, r6)
    r9 = smin(r9, r6)
    r8 = smax(r8, r7)
    r9 = smin(r9, r7)
    r4 = [r0+16]
    r5 = [r0+20]
    r6 = [r0+24]
    r7 = [r0+28]
    r8 = smax(r8, r4)
    r9 = smin(r9, r4)
    r8 = smax(r8, r5)
    r9 = smin(r9, r5)
    r8 = smax(r8, r6)
    r9 = smin(r9, r6)
    r8 = smax(r8, r7)
    r9 = smin(r9, r7)
    r4 = [r0+32]
    r5 = [r0+36]
    r6 = [r0+40]
    r7 = [r0+44]
    r8 = smax(r8, r4)
    r9 = smin(r9, r4)
    r8 = smax(r8, r5)
    r9 = smin(r9, r5)
    r8 = smax(r8, r6)
    r9 = smin(r9, r6)
    r8 = smax(r8, r7)
    r9 = smin(r9, r7)
    r4 = [r0+48]
    r5 = [r0+52]
    r6 = [r0+56]
    r7 = [r0+60]
    r8 = smax(r8, r4)
    r9 = smin(r9, r4)
    r8 = smax(r8, r5)
    r9 = smin(r9, r5)
    r8 = smax(r8, r6)
    r9 = smin(r9, r6)
    r8 = smax(r8, r7)
    r9 = smin(r9, r7)
    r4 = abs(r9)
    r5 = r4 >> 31
    r4 = r4 - r5
    r8 = smax(r8, r4)
    [r1++=4] = r8
    r0 += 64
    if (--r2 != 0) goto L01c19efc
    {r9-r4} = [sp++]
    rts
