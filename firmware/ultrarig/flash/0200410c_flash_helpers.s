; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 1 function, 0x0200410c..0x02004164

; flash_helpers_serial_step: 0x0200410c..0x02004164, module flash-helpers (serial_step)
.type flash_helpers_serial_step,@function
flash_helpers_serial_step:
    [--sp] = {rets, r6-r4}
    sp += -12
    r4 = r2
    r5 = r1
    r6 = r0
    r0 = sp + 0
    call storage_fault_decode
    if (r0 != 0) goto L02004150
    if (r6 == 0) goto L0200413c
    r0 = sp + 0
    r1 = r6
    rep 4 {
    r2 = h[r1++=2] (u)
    h[r0++=2] = r2
    }
    r0 = h[r6+10] (u)
    r1 = h[r6+8] (u)
    r1 <= insert(r0, p:16, l:16)
    [sp+8] = r1
    r0 = 0
    b[sp+8] = r0
    goto L02004150
L0200413c:
    r0 = 0
    b[sp+8] = r0
    r1 = 0
    d[sp] = r1_r0
    b[sp+9] = r5
    b[sp+10] = r4
L02004150:
    r0 = h[sp] (u)
    call record_helpers_next_serial
    h[sp] = r0
    r0 = sp + 0
    call storage_fault_encode
    sp += 12
    {pc, r6-r4} = [sp++]
