; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_container: 1 function, 0x0201acd8..0x0201ad4c

; capture_container_read: 0x0201acd8..0x0201ad4c, module capture-container (read)
.type capture_container_read,@function
capture_container_read:
    [--sp] = {rets, r6-r4}
    sp += -44
    r4 = r1
    r5 = r0  #
    r1 = [r4+0]
    r0 = 0xDF000
    ifs (r1 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 += r0  ; @add.rr
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  #  ; @add.rr.p
    [sp] = r5
    r1 = 1128745812
    r3 = sp + 4
    r2 = 8152
    call preset_storage_record
    r6 = r0
    if (r6 != 0) goto L0201ad46
    r0 = [r4+4]
    r1 = [sp+8]
    r6 = -3
    if (r1 != r0) goto L0201ad46
    r2 = [r4+8]
    r0 = [sp+12]
    if (r0 != r2) goto L0201ad46
    r2 = r5 + r1
    r2 += -4
    if (r1 <= 3) {  ; @if.le.ri.s12
    r2 = r5
    }
    call preset_application_asset_identity
    r1 = b[r4+16] (u)
    if (r1 == 0) goto L0201ad3c
    r1 = [r4+12]
    if (r0 != r1) goto L0201ad46
L0201ad3c:
    [r4+12] = r0
    r0 = 1
    b[r4+16] = r0
    r6 = 0
L0201ad46:
    r0 = r6
    sp += 44
    {pc, r6-r4} = [sp++]
