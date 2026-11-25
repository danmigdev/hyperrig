; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; drive_glide: 1 function, 0x01c06f3c..0x01c06f84

; drive_glide_post_mix: 0x01c06f3c..0x01c06f84, module drive-glide (post_mix)
.type drive_glide_post_mix,@function
drive_glide_post_mix:
    [--sp] = {rets, r12-r4}
    if (r1 == 0) goto L01c06f82
    r2 = r2 + r3
    r4 = L01c31c94
    r12 = 2147483647
    goto L01c06f5a
L01c06f50:
    r5 = r7 >> 31
    r5 = r5 << 1
    r6 = r5 + r12
    goto L01c06f7a
L01c06f5a:
    r6 = [r4++=4]
    r8 = [r0+0]
    r11_r10 = r6 * r2 (s)
    r11_r10 >>>= 16
    r9 = r8 >>> 31
    r6 = r10 + r8
    r7 = r11 + r9 + c
    r5 = r6 >>> 31
    if (r7 != r5) goto L01c06f50
L01c06f7a:
    r2 = r2 + r3  #
    [r0++=4] = r6
    if (--r1 != 0) goto L01c06f5a
L01c06f82:
    {pc, r12-r4} = [sp++]
