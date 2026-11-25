; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_installation: 1 function, 0x0201ad4c..0x0201ade8

; ir_installation_read: 0x0201ad4c..0x0201ade8, module ir-installation (read)
.type ir_installation_read,@function
ir_installation_read:
    [--sp] = {rets, r10-r4}
    sp += -44
    r4 = r3
    r9 = r2
    r8 = r1
    r6 = r0 + -1
    r7 = -1
    if (r6 > 7) goto L0201ade2
    r0 = 1
    r5 = 1
    call tempo_slot_services_priority_nest
    r1 = sp + 4
    r3 = sp + 0
    r2 = 8152
    r0 = r6
    call preset_application_asset_header
    if (r0 == 0) goto L0201ad88
    r0 = [sp+12]
    if (r0 != r8) goto L0201ad88
    r0 = [sp+8]
    r1 = r4 << 1
    if (r0 == r1) {
    r5 = 0
    }
L0201ad88:
    r0 = r6 << 13
    r1 = 978984
    r10 = r0 + r1  #
    r6 = [sp+8]
    r7 = 0x0 - r5
    r5 = 0
    r4 = r6
    goto L0201adc8
L0201ada0:
    if (r6 <= r5) goto L0201adcc
    r0 = r10 + r5
    r1 = r9 + r5
    r2 = r4
    if (r4 >= 2048) {  ; @if.ge.ri.s12
    r2 = 2048
    }
    call storage_control_read
    r7 = r0
    if (r7 == 0) goto L0201adc0
    r7 = -2
L0201adc0:
    r4 = r4 + -2048
    r5 = r5 + 2048
L0201adc8:
    if (r7 == 0) goto L0201ada0
    goto L0201addc
L0201adcc:
    r0 = r9
    r1 = r6
    call preset_storage_checksum
    r7 = 0
    if (r0 != r8) {
    r7 = -3
    }
L0201addc:
    r0 = 0
    call tempo_slot_services_priority_nest
L0201ade2:
    r0 = r7
    sp += 44
    {pc, r10-r4} = [sp++]
