; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p5: 3 functions, 0x02001968..0x02001a08

; phase3_p5_usb_var_init: 0x02001968..0x0200197a, module phase3-p5 (usb_var_init)
.type phase3_p5_usb_var_init,@function
phase3_p5_usb_var_init:
    r1 = L01c25ce8
    [r1+0] = r0
    if (r0 == 0) goto L02001978
    r1 = 0
    rep 26 {
    [r0++=4] = r1
    }
L02001978:
    rts

; phase3_p5_set_descriptor: 0x0200197a..0x020019e2, module phase3-p5 (set_descriptor)
.type phase3_p5_set_descriptor,@function
phase3_p5_set_descriptor:
    [--sp] = {rets, r8-r4}
    sp += -4
    r8 = r0
    r7 = 0
    r4 = r1  #
    [sp] = r7
    r0 = L020350b9
    rep 9 {
    r2 = b[r0++=1] (u)
    b[r1++=1] = r2
    }
    r0 = r8 << 5
    r1 = L01c26890
    r0 += r1  ; @add.rr
    r5 = r0 + 3376
    r6 = r4 + 9
L020019a4:
    ifs (r7 > 7) goto L020019c6
    r3 = [r5+r7<<2]
    if (r3 == 0) goto L020019c6
    r2 = sp + 0
    r0 = r8
    r1 = r6
    call r3
    if (r0 == 0) goto L020019d6
    r6 += r0  ; @add.rr
    r0 = r6 - r4
    r7 += 1  ; @add.ri.u5
    if (r0 <= 768) goto L020019a4
    r0 = 0
    goto L020019d2
L020019c6:
    r0 = r6 - r4
    b[r4+2] = r0
    r1 = r0 >> 8
    b[r4+3] = r1
    r1 = [sp]
    b[r4+4] = r1
L020019d2:
    sp += 4
    {pc, r8-r4} = [sp++]
L020019d6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L020019e0:
    goto L020019e0

; phase3_p5_usb_setup_init: 0x020019e2..0x02001a08, module phase3-p5 (usb_setup_init)
.type phase3_p5_usb_setup_init,@function
phase3_p5_usb_setup_init:
    [--sp] = rets
    r2 = 414
    r3 = L01c26890
    [r3+r2<<2] = r0
    if (r0 == 0) goto L02001a06
    r2 = r0 + 20
    r3 = b[r2+5] (u)
    r3 &= 4294967294
    b[r2+5] = r3
    [r0+4] = r1
    r0 = 2
    b[r2+0] = r0
    r0 = 0
    call phase3_p5_set_descriptor
L02001a06:
    pc = [sp++]
