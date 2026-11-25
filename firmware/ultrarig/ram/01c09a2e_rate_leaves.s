; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 1 function, 0x01c09a2e..0x01c09a7c

; rate_leaves_ring_write: 0x01c09a2e..0x01c09a7c, module rate-leaves (ring_write)
.type rate_leaves_ring_write,@function
rate_leaves_ring_write:
    [--sp] = {rets, r10-r4}
    r8 = r0
    r0 = r1 << 2
    r9 = [++r8=r0]
    r4 = [r8+160]
    r5 = r3
    r6 = r2
    if (r5 == 0) goto L01c09a76
    r10 = [r8+80]
L01c09a46:
    r0 = r4 << 2
    r0 += r9
    r1 = r10 - r4
    r7 = umin(r1, r5)
    r1 = r6
    r2 = r7
    call dsp_stage_copy  ; @call.xl
    if (r4 != 0) goto L01c09a64
    r0 = [r6+0]
    [r9+r10<<2] = r0
L01c09a64:
    r0 = r7 + r4
    r4 = 0
    if (r0 != r10) {
    r4 = r0
    }
    r5 = r5 - r7
    r0 = r7 << 2
    r6 = r6 + r0
    if (r5 != 0) goto L01c09a46
L01c09a76:
    [r8+160] = r4
    {pc, r10-r4} = [sp++]
