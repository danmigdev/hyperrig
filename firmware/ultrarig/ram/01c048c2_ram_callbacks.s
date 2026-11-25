; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 2 functions, 0x01c048c2..0x01c04928

; ram_callbacks_take_command: 0x01c048c2..0x01c048da, module ram-callbacks (take_command)
.type ram_callbacks_take_command,@function
ram_callbacks_take_command:
    csync
    r2 = L01c2bff0
    r1 = [r2+8]
    r0 = [r2+28]
    if (r0 != 0) goto L01c048d6
    [r2+8] = 0x0
    csync
L01c048d6:
    r0 = r1
    rts

; ram_callbacks_link_check: 0x01c048da..0x01c04928, module ram-callbacks (link_check)
.type ram_callbacks_link_check,@function
ram_callbacks_link_check:
    [--sp] = {rets, r4}
    r4 = L01c2bff0
    [r4+48] = 0x0
    csync
    [r4+8] = 0xFF
    csync
    r1 = 1
    r3 = 4000000
L01c048f6:
    r0 = r1  #
    r2 = [r4+8]
    if (r2 == 0) goto L01c04902
    r1 = r0 + 1
    if (r0 < r3) goto L01c048f6
L01c04902:
    csync
    r0 = [r4+8]
    r2 = 0
    r1 = 0
    if (r0 != 0) goto L01c0491a
    r0 = [r4+48]
    r1 = r0
    if (r0 != 1) {
    r1 = 0
    }
    if (r0 == 1) goto L01c0491c
L01c0491a:
    [r4+8] = r2
L01c0491c:
    r0 = L01c340cc
    r0 = r1  #
    [r0+52] = r1
    {pc, r4} = [sp++]
