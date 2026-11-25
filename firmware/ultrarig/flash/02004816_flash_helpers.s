; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 3 functions, 0x02004816..0x02004904

; flash_helpers_level_rate: 0x02004816..0x02004828, module flash-helpers (level_rate)
.type flash_helpers_level_rate,@function
flash_helpers_level_rate:
    [--sp] = rets
    call record_helpers_leading_ones
    r1 = L02035bfe
    r0 = h[r1+r0<<1] (u)
    pc = [sp++]

; flash_helpers_move_interrupts: 0x02004828..0x020048d2, module flash-helpers (move_interrupts)
.type flash_helpers_move_interrupts,@function
flash_helpers_move_interrupts:
    [--sp] = {rets, r12-r4}
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L02004856
    csync
L0200484e:
    testset b[r8]
    ifeq goto L0200484e
    csync
L02004856:
    r3 = 0
    r2 = 4
    r4 = 16
    r12 = 32436992
    r10 = 15
    r11 = r12 + -512
    goto L020048a4
L0200486c:
    r0 = r2 >>> 3
    r6 = [r12+r0<<2]
    r1 = r4 & 0x1C
    r6 >>= r1
    if ((r6 & 1) == 0) goto L020048a0
    r7 = [r11+r0<<2]
    r5 = r10 << r1
    r7 = r7 & ~r5
    r6 = r6 & 0xF
    r1 = r6 << r1
    r1 |= r7
    [r11+r0<<2] = r1
    r0 = r0 << 2
    r0 += r12
    [r0+0] &= ~r5
    r3 += 1  ; @add.ri.u5
L020048a0:
    r4 += 4  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L020048a4:
    if (r2 != 120) goto L0200486c
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L020048c0
    csync
    r0 = 0
    b[r8+0] = r0
L020048c0:
    call storage_coordination_irq_leave  ; @call.xl
    r0 = L01c278ac
    [r0+0] += r3
    {pc, r12-r4} = [sp++]

; flash_helpers_park_request: 0x020048d2..0x02004904, module flash-helpers (park_request)
.type flash_helpers_park_request,@function
flash_helpers_park_request:
    [--sp] = rets
    r0 = L01c26890
    r1 = 1
    [r0+552] = r1
    csync
    r1 = b[r0+30] (u)
    if (r1 == 0) goto L020048f2
    r0 = r0 + 3588
    call L020403ee  ; @call.xl
L020048f2:
    call L02040850  ; @call.xl
    if (r0 >= 27) {  ; @if.ge.ri.s12
    call L0203ea6e  ; @call.xl
    }
    pc = [sp++]
