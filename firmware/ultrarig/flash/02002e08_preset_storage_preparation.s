; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage_preparation: 1 function, 0x02002e08..0x02002e6a

; preset_storage_preparation_erase_block: 0x02002e08..0x02002e6a, module preset-storage-preparation (erase_block)
.type preset_storage_preparation_erase_block,@function
preset_storage_preparation_erase_block:
    [--sp] = {rets, r5, r4}
    r4 = r0
    call preset_storage_block
    r5 = r0
    call storage_coordination_wait_ready
    r1 = 1
    r0 = r5
    call capture_journal_erase
    r1 = r0
    r0 = -1
    if (r1 == 0) goto L02002e24
    {pc, r5, r4} = [sp++]
L02002e24:
    r0 = r5
    call preset_storage_preparation_erased
    r1 = L01c26890
    r1 += r4  ; @add.rr
    if (r0 == 0) goto L02002e48
    r0 = 3440
    r2 = 1
    b[r1+r0] = r2
    r2 = r0 + 18
    r0 = 0
    b[r1+r2] = r0
    {pc, r5, r4} = [sp++]
L02002e48:
    r0 = 3458
    r2 = b[r1+r0] (u)
    r2 += 1  ; @add.ri.u5
    b[r1+r0] = r2
    r2 = r2.b0 (u)
    r0 = -2
    if (r2 >= 3) {  ; @if.ge.ri.s12
    r2 = 3440
    r3 = 5
    b[r1+r2] = r3
    }
    {pc, r5, r4} = [sp++]
