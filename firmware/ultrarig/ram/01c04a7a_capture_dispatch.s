; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_dispatch: 2 functions, 0x01c04a7a..0x01c04b34

; capture_dispatch_probe: 0x01c04a7a..0x01c04a8e, module capture-dispatch (probe), capture-live (probe), capture-native (probe)
.type capture_dispatch_probe,@function
capture_dispatch_probe:
    [--sp] = rets
    r2 = L01c344a8
    [r2+0] = 0x1
    call capture_dispatch_size
    r0 = r0 + 16
    pc = [sp++]

; capture_dispatch_load: 0x01c04a8e..0x01c04b34, module capture-dispatch (load), capture-live (load), capture-native (load)
.type capture_dispatch_load,@function
capture_dispatch_load:
    [--sp] = {rets, r7-r4}
    sp += -4
    r4 = L01c344a8
    [r4+0] = 0x1
    r4 = r2  #
    [sp] = r3
    r2 = r1
    r1 = r0
    r6 = L01c2bff0
    r0 = r6 + 76
    r3 = r4
    call capture_dispatch_load_context
    r4 = r0
    r7 = L01c340cc
    [r7+0] = r4
    if (r4 != 0) goto L01c04b2e
    r5 = r6 + 64
    r0 = h[r5+20] (u)
    [r7+4] = r0
    r0 = b[r5+14] (u)
    [r7+8] = r0
    r0 = [r5+44]
    [r7+12] = r0
    r0 = b[r6+240] (u)
    [r7+16] = r0
    r0 = b[r5+22] (s)
    [r7+20] = r0
    r0 = b[r5+25] (s)
    [r7+24] = r0
    r4 = 0
    [r7+40] = r4
    r6 = r5 + 12
    r1 = 0
    r0 = r6  #
    [r7+28] = r4
    call capture_dispatch_select_dot
    r1 = 0
    r3_r2 = 0
    r0 = r6
    call capture_dispatch_noop_a
    r1 = 0
    r2 = 0
    r0 = r6
    call capture_dispatch_noop_b
    r1 = 0
    r3_r2 = 0
    r0 = r6
    call capture_dispatch_noop_c
    r1 = 0
    r3_r2 = 0  #
    [sp] = r4
    r0 = r6
    call capture_dispatch_noop_d
    [r5+0] = r4
    [r5+4] = r4
    [r7+64] = r4
    [r7+68] = r4
    r0 = r6
    call capture_live_reset
L01c04b2e:
    r0 = r4
    sp += 4
    {pc, r7-r4} = [sp++]
