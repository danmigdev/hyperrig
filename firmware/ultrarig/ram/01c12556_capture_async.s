; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_async: 1 function, 0x01c12556..0x01c12608

; capture_async_submit: 0x01c12556..0x01c12608, module capture-async (submit)
.type capture_async_submit,@function
capture_async_submit:
    [--sp] = {rets, r12-r4}
    r12 = L01c3449c
    r4 = [r12+0]
    r8 = [sp+48]
    r9 = r3  #
    r6 = [sp+44]
    r7 = r2  #
    r5 = [sp+40]
    r10 = r1
    r11 = r0
    r3 = 32375808
    if (r4 == 0) goto L01c125a4
    r1 = 0
    r2 = 200001
L01c12580:
    r0 = [r3+0]
    r0 = r0.b0 (s)
    ifs (r0 < 0) goto L01c1259a
    r1 = r1 + 1
    if (r1 < r2) goto L01c12580
    r1 = L01c34498
    r0 = [r1+0]
    r0 = r0 + 1
    [r1+0] = r0
L01c1259a:
    [r3+0] |= 0x40
    csync
    [r12+0] = 0x0
L01c125a4:
    r1 = L01c339e0
    r0 = 2657
    r0 = 4095  #
    [r1+0] = r0
    r4 = r5 & r0
    r2 = r6 << 12
    r0 = 16773120
    r0 &= r2
    r0 |= r4
    r0 <= insert(r8, p:24, l:8)
    [r1+16] = r0
    r2 = r7 << 10
    r0 = 1047552
    r0 &= r2
    r0 |= 4194304
    [r1+20] = r0
    r0 = 0
    [r1+24] = r0
    [r1+28] = r0
    [r1+4] = r9
    [r1+8] = r10
    [r1+12] = r11
    csync
    [r3+8] = r0
    [r3+4] = r1
    [r12+0] = 0x1
    r1 = L01c34494
    r0 = [r1+0]
    r0 = r0 + 1
    r0 = 329  #
    [r1+0] = r0
    [r3+0] = r0
    {pc, r12-r4} = [sp++]
