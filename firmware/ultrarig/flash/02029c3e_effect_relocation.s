; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_relocation: 2 functions, 0x02029c3e..0x02029e12

; effect_relocation_refresh_layout: 0x02029c3e..0x02029c66, module effect-relocation (refresh_layout)
.type effect_relocation_refresh_layout,@function
effect_relocation_refresh_layout:
    [--sp] = {rets, r4}
    r4 = r0
    r1 = [r4+36]
    call effect_setup_layout29  ; @call.xl
    r0 = [r4+36]
    if (r0 == 0) {
    r0 = r4 + 1996
    } else {
    r0 = 3091
    r0 = [r4+r0<<2]
    }
    r1 = 3092
    [r4+r1<<2] = r0
    {pc, r4} = [sp++]

; effect_relocation_relocate: 0x02029c66..0x02029e12, module effect-relocation (relocate)
.type effect_relocation_relocate,@function
effect_relocation_relocate:
    [--sp] = {rets, r14-r4}
    r10 = r1
    r13 = r0
    r5 = 0
    if (r0 == 0) goto L02029e0e
    if (r1 == 0) goto L02029e0e
    r8 = L01c2c220
    r14 = r8 + 102
    r6 = r8 + 92
L02029c84:
    r0 = r5 * 0x1E0
    r9 = r0 + r8
    r0 = r9
    r1 = [++r0=48]
    if (r1 == 0) goto L02029c98
    if (r1 == r13) goto L02029ce8
L02029c98:
    r12 = r9
    r0 = [++r12=84]
    if (r0 == 0) goto L02029cb4
    if (r0 != r13) goto L02029cb4
    r0 = [r9+88]
    r0 = r0 << 1
    r0 = r0 + 2
    r11 = r0 & 0xFFFFFFFC
    r0 = 0
    goto L02029cd2
L02029cb4:
    r7 = b[r9+7] (u)
    r0 = 0
    r3 = r6
    r1 = r14
L02029cbe:
    if (r0 >= r7) goto L02029cd6
    r4 = [r3++=4]
    r1 = r1 + 2
    r0 = r0 + 1
    if (r4 != r13) goto L02029cbe
    r1 = h[r1+0] (u)
    r11 = r1 << 2
L02029cd2:
    if (r11 != 0) goto L02029d04
L02029cd6:
    r6 = r6 + 480
    r5 = r5 + 1
    r14 = r14 + 480
    ifs (r5 < 16) goto L02029c84
    r5 = 0
    goto L02029e0e
L02029ce8:
    r5 = 1
    if (r2 == 0) goto L02029e0e
    r1 = L01c32db0
    r2 = [r1+60]
    if (r2 == r13) {
    [r1+60] = r10
    }
    [r0+0] = r10
    goto L02029e0e
L02029d04:
    r5 = 1
    if (r2 == 0) goto L02029e0e  ; @beq.ri
    r1 = r0 << 2
    r1 += r9
    r1 += 88
    if (r0 != 0) goto L02029d14
    r1 = r12
L02029d14:
    [r1+0] = r10
    r8 = b[r9+0] (u)
    r1 = r8 + -31
    if (r1 >= 5) goto L02029d34
L02029d24:
    r4 = [r9+288]
    if (r4 != 0) goto L02029da8
    if (r8 == 7) goto L02029d42
    if (r8 == 29) goto L02029d64
    goto L02029e0e
L02029d34:
    if (r8 == 7) goto L02029d42
    if (r8 == 29) goto L02029d64
    if (r8 == 27) goto L02029d24
    goto L02029e0e
L02029d42:
    r3 = [++r9=288]
    if (r3 == 0) goto L02029e0e
    r0 = r3
    r1 = r13
    r2 = r10
    call effect_relocation_rebase  ; @call.xl
    r6 = r0
    r1 = r3
    call ir_effect_lifecycle_relocate  ; @call.xl
    [r9+0] = r6
    goto L02029e0e
L02029d64:
    if (r0 == 0) goto L02029d78
    r0 = r10
    call effect_relocation_has_layout  ; @call.xl
    if (r0 == 0) goto L02029e0e
    r0 = r10
    call effect_relocation_refresh_layout
    goto L02029e0e
L02029d78:
    r0 = b[r9+7] (u)
    if (r0 != 0) goto L02029e0e
    r1 = [r9+88]
    call effect_parameter_lifecycle_resource_extra_size  ; @call.xl
    r0 = r0 >> 1
    r0 = r0 + 4096
    if (r1 < r0) goto L02029e0e
    r2 = r10 + 0x2000
    r0 = r2
    call effect_relocation_has_layout  ; @call.xl
    if (r0 == 0) goto L02029e0e
    r0 = r2
    call effect_relocation_refresh_layout
    goto L02029e0e
L02029da8:
    r0 = r8
    call effect_setup_object_count
    r9 = r0
    ifs (r0 < 1) goto L02029dd0
    r6 = 0
L02029db6:
    r0 = [r4+r6<<2]
    r1 = r13
    r2 = r11
    r3 = r10
    call effect_relocation_rebase_within  ; @call.xl
    [r4+r6<<2] = r0
    r6 = r6 + 1
    ifs (r6 < r9) goto L02029db6
L02029dd0:
    r4 = r4 + 676
    if (r8 == 31) goto L02029dee
    if (r8 != 34) goto L02029e0e
    r1 = r13  #
    r0 = [r4+0]
    r2 = r11
    r3 = r10
    call effect_relocation_rebase_within  ; @call.xl
    [r4+0] = r0
    goto L02029e0e
L02029dee:
    r1 = r13  #
    r0 = [r4+0]
    r2 = r11
    r3 = r10
    call effect_relocation_rebase_within  ; @call.xl
    r1 = r13  #
    [r4+0] = r0
    r2 = r11  #
    r0 = [r4+4]
    r3 = r10
    call effect_relocation_rebase_within  ; @call.xl
    [r4+4] = r0
L02029e0e:
    r0 = r5
    {pc, r14-r4} = [sp++]
