; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_platform: 1 function, 0x020005ac..0x02000604

; storage_platform_register: 0x020005ac..0x02000604, module storage-platform (register)
.type storage_platform_register,@function
storage_platform_register:
    [--sp] = {rets, r5, r4}
    if (r2 == 0) goto L020005ba
    r4 = 29883904
    [r4+r0<<2] = r2
L020005ba:
    r2 = r0 << 2
    r2 = r2 & 0x1C
    r1 = r1 << 1
    r1 = r1 & 0xE
    r4 = r1 | 0x1
    r1 = 15
    r1 <<= r2
    r5 = r0 >> 3
    call storage_platform_gate_disable
    if (r3 != 255) goto L020005da
    r3 = cnum
L020005da:
    r0 = r4 << r2
    r2 = r5 << 2
    r4 = 32436992
    r4 += r2  ; @add.rr
    r5 = 32436480
    r2 += r5  ; @add.rr
    r1 = ~r1
    if ((r3 & 0xFF) != 0) {
    r2 = r4
    }
    r3 = [r2+0]
    r1 &= r3
    r0 |= r1
    [r2+0] = r0
    call storage_platform_gate_enable
    {pc, r5, r4} = [sp++]
