; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 2 functions, 0x02015840..0x020158c2

; flash_helpers_shift_delay: 0x02015840..0x02015858, module flash-helpers (shift_delay)
.type flash_helpers_shift_delay,@function
flash_helpers_shift_delay:
    sp += -4
    r0 = 0
    [sp] = r0
    r0 = sp + 0
    goto L0201584e
L0201584a:
    [r0+0] += 1  ; @rmw.add.s12
L0201584e:
    r1 = [sp]
    ifs (r1 < 120) goto L0201584a
    sp += 4
    rts

; flash_helpers_shift_out: 0x02015858..0x020158c2, module flash-helpers (shift_out)
.type flash_helpers_shift_out,@function
flash_helpers_shift_out:
; HyperRig MINI v4, patch mini_panel_serial_writer_disabled: Replace entry by RAM-cache store and normal return; no PA0..3 access. LED driver is pending.
.if TARGET_MINI
    r1 = L01c1f208  ; @li.u32
    [r1+0] = r0  ; @st.w
    rts  ; @rts
    nop  ; @nop
.else
    [--sp] = {rets, r7-r4}
    r3 = L01c1f180
    r1 = [r3+136]
.endif
    r2 = r0
    r4 = 0x50000
    if (r1 != -1) goto L0201587e
    [r4+16] &= 0xFFFFFFF0
    [r4+20] &= 0xFFFFFFF0
    [r4+0] |= 0xF
    [r4+8] &= 0xFFFFFFF0
L0201587e:
    [r4+0] &= 0xFFFFFFFE
    r5 = 28
    r6 = 1
    goto L020158ae
L02015888:
    r0 &= 4294967291
    r7 = r6 << r5
    [r4+0] = r0
    call flash_helpers_shift_delay
    r0 = [r4+0]
    r1 = r0 | 0x8
    r0 &= 4294967287
    if ((r7 & r2) == 0) {
    r0 = r1
    }
    [r4+0] = r0
    call flash_helpers_shift_delay
    [r4+0] |= 0x4
    call flash_helpers_shift_delay
    call flash_helpers_shift_delay
    r5 += -1
L020158ae:
    r0 = [r4+0]
    ifs (r5 > -1) goto L02015888
    r0 |= 1
    [r4+0] = r0
    [r4+0] &= 0xFFFFFFFD
    [r3+136] = r2
    {pc, r7-r4} = [sp++]
