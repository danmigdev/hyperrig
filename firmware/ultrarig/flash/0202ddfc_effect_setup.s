; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 1 function, 0x0202ddfc..0x0202de50

; effect_setup_route_insert: 0x0202ddfc..0x0202de50, module effect-setup (route_insert)
.type effect_setup_route_insert,@function
effect_setup_route_insert:
    [--sp] = {rets, r11-r4}
    r8 = L01c32db0
    r9 = r0 + r8
    r10 = b[r9+14] (u)
    r1 = umin(r10, r1)
    ifs (r10 <= r1) goto L0202de36
    r4 = r0 * 0xA
    r6 = r4 + r8
    r11 = 347
    r5 = 348
    r4 = r10
L0202de26:
    r3 = r6 + r4
    r7 = b[r3+r11] (u)
    r4 += -1
    b[r3+r5] = r7
    ifs (r4 > r1) goto L0202de26
L0202de36:
    r0 = r0 * 0xA
    r0 = r0 + r1
    r0 += r8
    r1 = 348
    b[r0+r1] = r2
    r0 = r10 + 1
    b[r9+14] = r0
    {pc, r11-r4} = [sp++]
