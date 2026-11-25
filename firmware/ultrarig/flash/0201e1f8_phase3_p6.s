; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p6: 2 functions, 0x0201e1f8..0x0201e274

; phase3_p6_usb_get_ep_buffer: 0x0201e1f8..0x0201e260, module phase3-p6 (usb_get_ep_buffer)
.type phase3_p6_usb_get_ep_buffer,@function
phase3_p6_usb_get_ep_buffer:
    r2 = L01c37c28
    if ((r1 & 128) != 0) goto L0201e21a
    r1 = r1 & 0xF
    if (r1 > 3) goto L0201e246
    tbb [r1]
phase3_p6_case_table_0201e20c:
    .byte (L0201e234 - phase3_p6_case_table_0201e20c) / 2, (L0201e210 - phase3_p6_case_table_0201e20c) / 2, (L0201e23c - phase3_p6_case_table_0201e20c) / 2, (L0201e24a - phase3_p6_case_table_0201e20c) / 2
L0201e210:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    r0 += 84
    rts
L0201e21a:
    r1 = r1 & 0xF
    if (r1 > 4) goto L0201e246
    tbb [r1]
phase3_p6_case_table_0201e224:
    .byte (L0201e234 - phase3_p6_case_table_0201e224) / 2, (L0201e22a - phase3_p6_case_table_0201e224) / 2, (L0201e254 - phase3_p6_case_table_0201e224) / 2, (L0201e22a - phase3_p6_case_table_0201e224) / 2, (L0201e23c - phase3_p6_case_table_0201e224) / 2
    .byte 0x00  ; alignment
L0201e22a:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    r0 += 76
    rts
L0201e234:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    rts
L0201e23c:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    r0 += 92
    rts
L0201e246:
    r0 = 0
    rts
L0201e24a:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    r0 += 72
    rts
L0201e254:
    r0 = r0 * 0x160
    r0 += r2  ; @add.rr
    r0 = r0 + 224
    rts

; phase3_p6_usb_alloc_ep_dmabuffer: 0x0201e260..0x0201e274, module phase3-p6 (usb_alloc_ep_dmabuffer)
.type phase3_p6_usb_alloc_ep_dmabuffer,@function
phase3_p6_usb_alloc_ep_dmabuffer:
    [--sp] = rets
    call phase3_p6_usb_get_ep_buffer
    if (r0 == 0) goto L0201e268
    pc = [sp++]
L0201e268:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0201e272:
    goto L0201e272
