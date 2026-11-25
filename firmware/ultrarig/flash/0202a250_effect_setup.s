; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202a250..0x0202a2a4

; effect_setup_partition_pack: 0x0202a250..0x0202a2a4, module effect-setup (partition_pack)
.type effect_setup_partition_pack,@function
effect_setup_partition_pack:
    [--sp] = {rets, r10-r4}
    r9 = r0
    ifs (r1 < 1) goto L0202a2a0
    r8 = 0
    r0 = 0
L0202a25c:
    r7 = r2 & ~r0
    r10 = -1
    r6 = 0
L0202a266:
    r4 = r7 & (1 << r6)
    if (r4 == 0) goto L0202a286
    r4 = [r9+r6<<2]
    r5 = r4 + r8
    if (r5 > r3) goto L0202a286
    ifs (r10 < 0) goto L0202a284
    r5 = [r9+r10<<2]
    if (r4 <= r5) goto L0202a286
L0202a284:
    r10 = r6
L0202a286:
    r6 = r6 + 1
    if (r1 != r6) goto L0202a266
    ifs (r10 < 0) goto L0202a29e
    r4 = [r9+r10<<2]
    r0 = r0 | (1 << r10)
    r8 += r4
    ifs (r1 > 0) goto L0202a25c
L0202a29e:
    {pc, r10-r4} = [sp++]
L0202a2a0:
    r0 = 0
    {pc, r10-r4} = [sp++]
