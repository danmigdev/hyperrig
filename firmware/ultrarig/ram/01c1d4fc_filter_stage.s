; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; filter_stage: 1 function, 0x01c1d4fc..0x01c1d5cc

; filter_stage_filter_stage: 0x01c1d4fc..0x01c1d5cc, module filter-stage (filter_stage)
.type filter_stage_filter_stage,@function
filter_stage_filter_stage:
    [--sp] = {rets, r15-r4}
    sp += -4
    [sp] = r2
    r13 = r0
    r14 = r1
    r15 = [r0+0]
    r4 = [r2+52]
    r5 = [r2+72]
    r10 = [r2+100]
    r1 = r14 & 0x3
    r14 = r14 + 3
    r14 = r14 >> 2
    if (r1 == 0) goto L01c1d534
    r1 += -1
    if (r1 == 0) goto L01c1d532
    r1 += -1
    if (r1 == 0) goto L01c1d530
    r1 += -1
    goto L01c1d52e
L01c1d52e:
    goto L01c1d556
L01c1d530:
    goto L01c1d578
L01c1d532:
    goto L01c1d59a
L01c1d534:
    r2 = r15 >>> 5
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r10 * r5 (s)
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c1d556:
    r2 = r15 >>> 5
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r10 * r5 (s)
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c1d578:
    r2 = r15 >>> 5
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r10 * r5 (s)
    r1_r0 >>>= 16
    [r13++=4] = r0
L01c1d59a:
    r2 = r15 >>> 5
    r3 = r2 - r10
    r1_r0 = r3 * r4 (s)
    r15 = [r13+4]
    r1_r0 >>>= 16
    r10 += r0
    r1_r0 = r10 * r5 (s)
    r1_r0 >>>= 16
    [r13++=4] = r0
    if (--r14 != 0) goto L01c1d534
    r2 = [sp]
    [r2+100] = r10
    sp += 4
    goto L01c1d5ca
L01c1d5ca:
    {pc, r15-r4} = [sp++]
