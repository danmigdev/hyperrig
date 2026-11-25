; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 2 functions, 0x0201c23e..0x0201c2d8

; phase3_p4_cdc_desc_config: 0x0201c23e..0x0201c2d2, module phase3-p4 (cdc_desc_config)
.type phase3_p4_cdc_desc_config,@function
phase3_p4_cdc_desc_config:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    r1 = L020350c2
    r2 = 66
    r0 = r6
    call effect_parameter_support_memmove  ; @call.xl
    r0 = [r4+0]
    b[r6+2] = r0
    r0 = [r4+0]
    b[r6+10] = r0
    r0 = [r4+0]
    r0 += 1  ; @add.ri.u5
    r1 = r6 + 26
    b[r1+0] = r0
    r0 = [r4+0]
    b[r1+8] = r0
    r0 = [r4+0]
    r0 += 1  ; @add.ri.u5
    b[r1+9] = r0
    r0 = 134
    b[r1+12] = r0
    r0 = 8
    b[r1+14] = r0
    r0 = 0
    r1 = r6 + 42  #
    b[r1+15] = r0
    if (r5 == 0) goto L0201c286
    r2 = 4
    b[r1+0] = r2
L0201c286:
    r2 = [r4+0]
    r2 += 1  ; @add.ri.u5
    b[r1+3] = r2
    r2 = 2
    b[r1+12] = r2
    r2 = 64
    b[r1+14] = r2
    b[r1+15] = r0
    r1 = 130
    b[++r6=61] = r1
    b[r6+2] = r2
    r0 = r5  #
    b[r6+3] = r0
    r1 = [r4+0]
    r2 = phase3_p4_cdc_setup
    call L0201c202
    r1 = r0  #
    r2 = [r4+0]
    if (r1 != r2) goto L0201c2c6
    r2 = phase3_p4_cdc_reset
    r0 = r5
    call L0201c220
    [r4+0] += 2  ; @rmw.add.s12
    r0 = 66
    {pc, r6-r4} = [sp++]
L0201c2c6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201c2d0:
    goto L0201c2d0

; phase3_p4_usb_device2id: 0x0201c2d2..0x0201c2d8, module phase3-p4 (usb_device2id)
.type phase3_p4_usb_device2id,@function
phase3_p4_usb_device2id:
    r0 = r0 & 0x1
    rts
