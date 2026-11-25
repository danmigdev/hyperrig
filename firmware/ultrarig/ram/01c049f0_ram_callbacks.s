; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 2 functions, 0x01c049f0..0x01c04a7a

; ram_callbacks_link_status: 0x01c049f0..0x01c04a5c, module ram-callbacks (link_status)
.type ram_callbacks_link_status,@function
ram_callbacks_link_status:
    [--sp] = {rets, r4}
    sp += -16
    r4 = r0
    r0 = sp + 0
    call ram_callbacks_clear_record
    r0 = [sp]
    [r4+0] = r0
    r0 = [sp+4]
    [r4+4] = r0
    r0 = [sp+8]
    [r4+8] = r0
    r0 = [sp+12]
    [r4+12] = r0
    r1 = L01c34080
    r0 = [r1+0]
    if (r0 != 0) goto L01c04a1a
    r0 = [r1+32]
    if (r0 == 0) goto L01c04a2a
L01c04a1a:
    r0 = [r1+0]
    [r4+0] = r0
    r0 = [r1+4]
    [r4+4] = r0
    r0 = [r1+32]
    [r4+8] = r0
    r0 = [r1+36]
    [r4+12] = r0
L01c04a2a:
    r1 = L01c2bff0
    r0 = [r1+176]
    [r4+16] = r0
    r0 = [r1+204]
    [r4+20] = r0
    r0 = [r1+8]
    [r4+24] = r0
    r2 = [r1+272]
    r1 = L01c340cc
    r0 = [r1+36]
    r0 = r0 << 8
    r2 |= r0  #
    r1 = [r1+60]
    r0 = r1 << 16
    r0 |= r2
    [r4+28] = r0
    sp += 16
    {pc, r4} = [sp++]

; ram_callbacks_timer_start: 0x01c04a5c..0x01c04a7a, module ram-callbacks (timer_start)
.type ram_callbacks_timer_start,@function
ram_callbacks_timer_start:
    r1 = 67328
    r0 = [r1+0]
    if ((r0 & 0x1) == 0) {
    [r1+0] = 0x4000
    [r1+8] = 0xFFFFFFFF
    [r1+4] = 0x0
    [r1+0] = 0x1
    }
    rts
