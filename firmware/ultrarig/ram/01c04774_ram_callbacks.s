; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 2 functions, 0x01c04774..0x01c04862

; ram_callbacks_post_job: 0x01c04774..0x01c047de, module ram-callbacks (post_job)
.type ram_callbacks_post_job,@function
ram_callbacks_post_job:
    [--sp] = {rets, r6-r4}
    csync
    r4 = L01c2bff0
    r6 = r1  #
    r2 = [r4+28]
    r5 = r0
    r3 = 0
    if (r2 == 0) goto L01c047da
    r1 = [r4+24]
    r0 = [r4+20]
    if (r1 != r0) goto L01c047da
    r1 = [r4+16]
    r0 = [r4+24]
    if (r1 == r0) goto L01c047a0
    r1 = [r4+32]
    r0 = [r4+16]
    if (r1 != r0) goto L01c047da
L01c047a0:
    r0 = [r4+8]
    if (r0 == 0) goto L01c047b6
    r1 = L01c3418c
    r0 = [r1+0]
    r0 = r0 + 1
    r3 = -1
    r0 = r3  #
    [r1+0] = r0
    {pc, r6-r4} = [sp++]
L01c047b6:
    r1 = L01c340c4
    r0 = [r1+0]
    r0 = r0 + 1
    [r1+0] = r0
    r0 = 67332
    r0 = [r0+0]
    [r4+44] = r0
    [r4+36] = r5
    [r4+40] = r6
    csync
    [r4+16] += 0x1
    csync
    r3 = 1
L01c047da:
    r0 = r3
    {pc, r6-r4} = [sp++]

; ram_callbacks_wait_job: 0x01c047de..0x01c04862, module ram-callbacks (wait_job)
.type ram_callbacks_wait_job,@function
ram_callbacks_wait_job:
    [--sp] = {rets, r7-r4}
    r4 = L01c2bff0
    r7 = r1  #
    r3 = [r4+16]
    r2 = r0
    if (r7 == 0) goto L01c047f2
    [r7+0] = 0x1
L01c047f2:
    r1 = 0
    r5 = 67332
    r6 = 3000001
L01c04800:
    r0 = [r4+20]
    if (r0 == r3) goto L01c04818
    r0 = [r4+28]
    if (r0 == 0) goto L01c04818
    r0 = [r5+0]
    r0 = r2 - r0
    ifs (r0 < 1) goto L01c04818
    r1 = r1 + 1
    if (r1 < r6) goto L01c04800
L01c04818:
    csync
    r0 = [r4+20]
    r2 = 1
    if (r0 == r3) goto L01c0484c
    [r4+32] = r3
    csync
    r0 = [r4+24]
    if (r0 != r3) goto L01c04850
    r0 = [r4+20]
    if (r0 == r3) goto L01c0484a
    r1 = -1
    r5 = 400000
L01c0483a:
    r1 = r1 + 1
    if (r1 > r5) goto L01c0485a
    r0 = [r4+28]
    if (r0 == 0) goto L01c0485a
    r0 = [r4+20]
    if (r0 != r3) goto L01c0483a
L01c0484a:
    csync
L01c0484c:
    r0 = r2
    {pc, r7-r4} = [sp++]
L01c04850:
    if (r7 == 0) goto L01c0485c
    r2 = 0
    [r7+0] = r2
    r0 = 0
    {pc, r7-r4} = [sp++]
L01c0485a:
    csync
L01c0485c:
    r2 = 0
    r0 = 0
    {pc, r7-r4} = [sp++]
