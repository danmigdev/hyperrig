; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p11: 1 function, 0x02025392..0x0202541c

; phase3_p11_lbuf_alloc_btctrler: 0x02025392..0x0202541c, module phase3-p11 (lbuf_alloc_btctrler)
.type phase3_p11_lbuf_alloc_btctrler,@function
phase3_p11_lbuf_alloc_btctrler:
    [--sp] = {rets, r8-r4}
    r3_r2 = r1_r0
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r4 = r2 + 16
L020253a0:
    testset b[r4]
    ifeq goto L020253a0
    r0 = r3 + 16
    r1 = r0 & 0x3
    r3 = 0x4 - r1
    r1 = 0
    if ((r0 & 0x3) != 0) {
    r1 = r3
    }
    csync
    r0 += r1  #  ; @add.rr.p
    r3 = [r2+8]
    r1 = r2 + 8
    goto L020253ca
L020253c2:
    r7 = h[r3+8] (u)
    if (r7 >= r0) goto L020253d4
    r3 = [r3+0]
L020253ca:
    r5 = 0
    if (r3 != r1) goto L020253c2
    r3 = 0
    goto L0202540e
L020253d4:
    r1 = r0 + 12
    if (r7 <= r1) goto L020253f4
    r1 = r3 + r0
    r6 = r7 - r0
    r6 = r3  #
    h[r1+8] = r6
    r8 = [r3+4]
    r7 = [r6++=4]
    [r7+4] = r1
    [r1+] = {r8, r7}
    [r8+0] = r1
    goto L020253fe
L020253f4:
    r6 = r3  #
    r1 = [r3+4]
    r0 = [r6++=4]
    call L0202538c
    r0 = r7
L020253fe:
    [r3+8] = r2
    r1 = 0
    b[r3+14] = r1
    h[r3+12] = r0
    b[r3+15] = r1
    [r3+0] = r3
    [r6+0] = r3
    r3 += 16  ; @add.ri.u5
L0202540e:
    csync
    b[r4+0] = r5
    call storage_coordination_irq_leave  ; @call.xl
    r0 = r3
    {pc, r8-r4} = [sp++]
