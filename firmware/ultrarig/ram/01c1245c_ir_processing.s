; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_processing: 2 functions, 0x01c1245c..0x01c12556

; ir_processing_wait: 0x01c1245c..0x01c124a8, module ir-processing (wait)
.type ir_processing_wait,@function
ir_processing_wait:
    [--sp] = {rets, r5, r4}
    r5 = L01c3449c
    r0 = [r5+0]
    if (r0 == 0) goto L01c124a2
    r4 = 0
    r3 = 32375808
    r2 = 200001
    r1 = 0
L01c12478:
    r0 = [r3+0]
    r0 = r0.b0 (s)
    ifs (r0 < 0) goto L01c12494
    r1 = r1 + 1
    if (r1 < r2) goto L01c12478
    r1 = L01c34498
    r0 = [r1+0]
    r0 = r0 + 1
    [r1+0] = r0
    r4 = -1
L01c12494:
    [r3+0] |= 0x40
    csync
    [r5+0] = 0x0
    r0 = r4
    {pc, r5, r4} = [sp++]
L01c124a2:
    r4 = 0
    r0 = 0
    {pc, r5, r4} = [sp++]

; ir_processing_start: 0x01c124a8..0x01c12556, module ir-processing (start)
.type ir_processing_start,@function
ir_processing_start:
    [--sp] = {rets, r9-r4}
    r7_r6 = r3_r2
    r5 = r1
    r0 = r0 + -256
    r3 = r0 <> 8
    r1 = -1
    if (r3 > 7) goto L01c12552
    r0 = r0 >> 8
    r2 = r0.b0 (u)
    r0 = 139
    r0 >>= r2
    if ((r0 & 1) == 0) goto L01c12552
    r8 = L01c3449c
    r0 = [r8+0]
    r9 = L0203be70
    r4 = 32375808
    if (r0 == 0) goto L01c1250c
    r1 = 0
    r2 = 200001
L01c124e8:
    r0 = [r4+0]
    r0 = r0.b0 (s)
    ifs (r0 < 0) goto L01c12502
    r1 = r1 + 1
    if (r1 < r2) goto L01c124e8
    r1 = L01c34498
    r0 = [r1+0]
    r0 = r0 + 1
    [r1+0] = r0
L01c12502:
    [r4+0] |= 0x40
    csync
    [r8+0] = 0x0
L01c1250c:
    r0 = [r9+r3<<2]
    r3 = 1
    r1 = 1
    if (r5 != 0) goto L01c12518
    r1 = r5
L01c12518:
    r2 = r0 << 3
    r0 = ir_accelerator_commands_and_indices
    r0 = r0 + r2
    r1 = [r0+r1<<2]
    r0 = L01c339d0
    [r0+0] = r1
    [r0+4] = r6
    [r0+8] = r7
    r1 = 0
    [r0+12] = r1
    csync
    [r4+0] = r1
    [r4+4] = r0
    [r8+0] = r3
    r2 = L01c34494
    r0 = [r2+0]
    r0 = r0 + 1
    r0 = 257  #
    [r2+0] = r0
    [r4+0] = r0
L01c12552:
    r0 = r1
    {pc, r9-r4} = [sp++]
