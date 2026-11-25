; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x0200704e..0x020070a4

; preset_storage_checksum: 0x0200704e..0x020070a4, module preset-storage (checksum)
.type preset_storage_checksum,@function
preset_storage_checksum:
    [--sp] = {rets, r12-r4}
    r9_r8 = r1_r0
    r12 = r1 ^ 0xFFFFFFFF
    r5 = 0
    r4 = -1
    r10 = -257
    r6 = r9
    r11 = -1
    goto L0200709a
L02007066:
    r0 = umax(r12, r10)
    r7 = r4 - r0
    r1 = r8 + r5
    r2 = r6
    if (r6 >= 256) {  ; @if.ge.ri.s12
    r2 = 256
    }
    r0 = r11
    call preset_storage_crc_update
    r11 = r0
    if (r7 < r9) {
    call storage_control_poll
    }
    r6 = r6 + -256
    r12 = r12 + 256
    r4 = r4 + 256
    r5 = r5 + 256
L0200709a:
    if (r5 < r9) goto L02007066
    r0 = r11 ^ 0xFFFFFFFF
    {pc, r12-r4} = [sp++]
