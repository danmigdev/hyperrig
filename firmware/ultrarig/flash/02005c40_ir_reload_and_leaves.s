; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_reload_and_leaves: 1 function, 0x02005c40..0x02005c7c

; ir_reload_and_leaves_pool_setup: 0x02005c40..0x02005c7c, module ir-reload-and-leaves (pool_setup)
.type ir_reload_and_leaves_pool_setup,@function
ir_reload_and_leaves_pool_setup:
    [--sp] = {rets, r4}
    r3 = 0
    r4 = r0
    rep 9 {
    [r4++=4] = r3
    }
    if (r1 == 0) goto L02005c7a
    r3 = 0x0 - r1
    r3 = r3 & 0xF
    r4 = r3 | 0x20
    if (r4 > r2) goto L02005c7a
    r1 += r3  ; @add.rr
    r2 = r2 - r3
    r2 = r2 & 0xFFFFFFF0
    [r0+] = {r2, r1}
    [r1+0] = r2
    r0 = 4042583552
    r0 ^= r2  #
    [r1+4] = r0
    [r1+8] = 0x0
    [r1+12] = r0
L02005c7a:
    {pc, r4} = [sp++]
