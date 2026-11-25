; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; drive_glide: 1 function, 0x01c06c08..0x01c06c58

; drive_glide_glide: 0x01c06c08..0x01c06c58, module drive-glide (glide)
.type drive_glide_glide,@function
drive_glide_glide:
    [--sp] = {rets, r7-r4}
    r4 = r1 - r0
    ifs (r4 <= 0) {
    r2 = r3
    }
    r3 = [sp+20]
    r2 *= r3
    r5 = r2 >> 7
    r6 = 1048575
    r7 = 0
    r7_r6 += r5 * r4 (s)
    r3 = 2097151
    r2 = 0
    r3 = r6 - r3
    r3 = r7 - r2 - !c
    r6 = psr
    r3 = r1
    if ((r6 & 0x2) != 0) {
    r5_r4 = r5 * r4 (s)
    r5_r4 >>= 20
    r3 = r4 + r0
    }
    r0 = 4467
    if (r3 >= r0) {
    r2 = r3
    }
    if (r1 == 0) goto L01c06c54
    r2 = r3
L01c06c54:
    r0 = r2
    {pc, r7-r4} = [sp++]
