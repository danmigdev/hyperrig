; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 2 functions, 0x0201c17c..0x0201c202

; phase3_p4_usb_set_setup_phase: 0x0201c17c..0x0201c180, module phase3-p4 (usb_set_setup_phase)
.type phase3_p4_usb_set_setup_phase,@function
phase3_p4_usb_set_setup_phase:
    b[r0+1] = r1
    rts

; phase3_p4_user_setup_filter: 0x0201c180..0x0201c202, module phase3-p4 (user_setup_filter)
.type phase3_p4_user_setup_filter,@function
phase3_p4_user_setup_filter:
    [--sp] = {rets, r4}
    sp += -8
    r2 = b[r1+0] (u)
    r3 = r2 & 0xFFFFFF1F
    if (r3 == 3) goto L0201c1a4
    r2 = 0
    if (r3 != 2) goto L0201c1dc
    r1 = b[r1+4] (u)
    if ((r1 & 0xF) == 0) goto L0201c1dc
; HyperRig MINI, product option: what is asked of the endpoint of the MIDI port is answered as the SDK does.
.if MINI_PRODUCT
    r1 = r1 & 0xF
    if (r1 == 1) goto L0201c1dc
.endif
    r1 = 3
    call phase3_p4_usb_set_setup_phase
L0201c1a0:
    r2 = 1
    goto L0201c1dc
L0201c1a4:
    r2 = 0
    r3 = 0
    d[sp] = r3_r2
    r3 = b[r1+1] (u)
    r2 = 1
    if (r3 != 0) goto L0201c1dc
    r2 = b[r1+3] (u)
    r3 = b[r1+2] (u)
    r3 <= insert(r2, p:8, l:8)
    r2 = 0
    if (r3 != 252) goto L0201c1dc
    r3 = b[r1+5] (u)
    r4 = b[r1+4] (u)
    r4 <= insert(r3, p:8, l:8)
    if (r4 != 254) goto L0201c1dc
    r2 = b[r1+7] (u)
    r3 = b[r1+6] (u)
    r3 <= insert(r2, p:8, l:8)
    if (r3 == 8) goto L0201c1e2
    r2 = 1
    if (r3 == 0) goto L0201c1f6
L0201c1dc:
    r0 = r2
    sp += 8
    {pc, r4} = [sp++]
L0201c1e2:
    r2 = 0xFFFFFFFF  ; @li.modimm
    r3 = r2
    d[sp] = r3_r2
    r2 = sp + 0
    r3 = 8
    call L0201ba8a
    goto L0201c1a0
L0201c1f6:
    r1 = 0
    call phase3_p4_usb_set_setup_phase
    call phase3_p7_go_mask_usb_updata  ; @call.xl
L0201c200:
    goto L0201c200
