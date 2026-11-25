; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x0200cf88..0x0200d060

; preset_storage_available: 0x0200cf88..0x0200d060, module preset-storage (available)
; HyperRig MINI, product option: a preset may be packed.
.type preset_storage_available,@function
preset_storage_available:
    [--sp] = {rets, r13-r4}
    sp += -40
    r10 = r0
    r0 = 0
    if (r10 > 31) goto L0200d05c
    r0 = 1
    r9 = r0 << r10
    call preset_storage_preparation_prepare
    r8 = L01c26890
    r0 = [r8+708]
    if ((r0 & r9) == 0) goto L0200cfb2
    r0 = [r8+732]
    goto L0200d054
L0200cfb2:
    r0 = 1
    call tempo_slot_services_priority_nest
    r0 = r10
    call preset_storage_address
    r5 = r0
    r1 = 1363626836
    r3 = sp + 0
.if MINI_PRODUCT
    r2 = 1880
.else
    r2 = 1490
.endif
    call preset_application_header
    if (r0 == 0) goto L0200d03a
    r12 = [sp+4]  ; @ld.w.sp.l
    r11 = r5 + 40
    r4 = 0
    r13 = -1
    r5 = r12
    goto L0200d014
L0200cfe4:
    r0 = r11 + r4
    r6 = r5
    if (r5 >= 256) {  ; @if.ge.ri.s12
    r6 = 256
    }
    r7 = r8 + 5812
    r1 = r7
    r2 = r6
    call storage_control_read
    if (r0 != 0) goto L0200d03a
    r0 = r13
    r1 = r7
    r2 = r6
    call preset_storage_crc_update
    r13 = r0
    r5 = r5 + -256
    r4 = r4 + 256
L0200d014:
    if (r12 > r4) goto L0200cfe4
    r4 = [sp+8]
    r0 = 0
    call tempo_slot_services_priority_nest
    r0 = r8 + 708
    [r0+0] |= r9
    r0 = r13 ^ 0xFFFFFFFF
    if (r4 != r0) goto L0200d048
    r0 = [r8+732]
    r0 = r0 | r9
    goto L0200d050
L0200d03a:
    r0 = 0
    call tempo_slot_services_priority_nest
    r0 = r8 + 708
    [r0+0] |= r9
L0200d048:
    r0 = [r8+732]
    r0 = r0 & ~r9
L0200d050:
    [r8+732] = r0
L0200d054:
    r0 = r0 >> r10
    r0 = r0 & 0x1
L0200d05c:
    sp += 40
    {pc, r13-r4} = [sp++]
