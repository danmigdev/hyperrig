; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage_preparation: 2 functions, 0x02002874..0x020028c2

; preset_storage_preparation_read_forward: 0x02002874..0x0200287a, module preset-storage-preparation (read_forward)
.type preset_storage_preparation_read_forward,@function
preset_storage_preparation_read_forward:
    [--sp] = rets
    call storage_control_read
    pc = [sp++]

; preset_storage_preparation_erased: 0x0200287a..0x020028c2, module preset-storage-preparation (erased)
.type preset_storage_preparation_erased,@function
preset_storage_preparation_erased:
    [--sp] = {rets, r6-r4}
    sp += -256
    r4 = r0
    r6 = 0
    goto L020028b2
L02002884:
    r0 = r6 + r4
    r5 = 0x1000 - r6
    if (r5 >= 256) {  ; @if.ge.ri.s12
    r5 = 256
    }
    r1 = sp + 0
    r2 = r5
    call preset_storage_preparation_read_forward
    if (r0 != 0) goto L020028bc
    r0 = 0
L0200289c:
    if (r0 >= r5) goto L020028ae
    r1 = sp + 0
    r1 = b[r1+r0] (u)
    r0 += 1  ; @add.ri.u5
    if (r1 == 255) goto L0200289c
    goto L020028bc
L020028ae:
    r6 = r6 + 256
L020028b2:
    if (r6 <= 4095) goto L02002884
    r0 = 1
    goto L020028be
L020028bc:
    r0 = 0
L020028be:
    sp += 256
    {pc, r6-r4} = [sp++]
