; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_ownership: 5 functions, 0x0202eabc..0x0202ec54

; effect_ownership_detach: 0x0202eabc..0x0202eb0c, module effect-ownership (detach), effect-resource-ownership (ownership_detach)
.type effect_ownership_detach,@function
effect_ownership_detach:
    [--sp] = {rets, r8-r4}
    sp += -4
    r1 = sp + 0
    call effect_ownership_lookup
    ifs (r0 < 0) goto L0202eb08
    r4 = L01c32db0
    r8 = r0 + r4  #
    r3 = [sp]
    r2 = b[r8+14] (u)
    r5 = r3 + 1
    ifs (r5 >= r2) goto L0202eb00
    r0 = r0 * 0xA
    r0 = r0 + r4
    r4 = 349
    r5 = 348
L0202eaee:
    r6 = r0 + r3
    r7 = b[r6+r4] (u)
    r1 = r3 + 2
    r3 = r3 + 1
    b[r6+r5] = r7
    ifs (r1 < r2) goto L0202eaee
L0202eb00:
    r0 = r2 + -1
    b[r8+14] = r0
L0202eb08:
    sp += 4
    {pc, r8-r4} = [sp++]

; effect_ownership_capture: 0x0202eb0c..0x0202eb4c, module effect-ownership (capture), effect-resource-ownership (ownership_capture)
.type effect_ownership_capture,@function
effect_ownership_capture:
    [--sp] = {rets, r4}
    r1 = b[r0+0] (u)
    r1 += -27
    if (r1 > 8) goto L0202eb4a
    r2 = 497
    r1 = r2 & (1 << r1)
    if (r1 == 0) goto L0202eb4a
    r1 = [++r0=288]
    if (r1 == 0) goto L0202eb4a
    r1 = L01c32db0
    r2 = b[r1+6] (u)
    r3 = [r0+0]
    r4 = L01c2fa38
    r3 = r3 - r4
    r4 = 888
    r3 = r3 / r4 (s)
    r2 = r2 & ~(1 << r3)
    b[r1+6] = r2
    [r0+0] = 0x0
L0202eb4a:
    {pc, r4} = [sp++]

; effect_ownership_remove: 0x0202eb4c..0x0202ebe2, module effect-ownership (remove), effect-resource-ownership (ownership_remove)
.type effect_ownership_remove,@function
effect_ownership_remove:
    [--sp] = {rets, r9-r4}
    r5 = r0
    call biquad_coefficients_counter  ; @call.xl
    r6 = -1
    if (r5 > 15) goto L0202eb6c
    r0 = r5 * 0x1E0
    r1 = L01c2c220
    r4 = r0 + r1
    r0 = b[r4+2] (u)
    if (r0 != 0) goto L0202eb70
L0202eb6c:
    r0 = r6
    {pc, r9-r4} = [sp++]
L0202eb70:
    r0 = r5
    call dsp_initialization_reset_slot
    r0 = r5
    call effect_ownership_detach
    r9 = r4
    r1 = b[++r9=3] (u)
    r7 = L01c32db0
    if (r1 == 0) goto L0202ebb0
    r8 = 0  #
    r2 = b[r7+8] (u)
    r3 = 0
    if (r2 == 0) goto L0202ebaa
    r6 = 0
L0202eb92:
    r1 = r6 + r7
    r1 = b[r1+88] (u)
    if (r1 != r5) {
    r0 = r3 + r7
    b[r0+88] = r1
    r3 = r3 + 1
    }
    r6 = r6 + 1
    ifs (r6 < r2) goto L0202eb92
L0202ebaa:
    b[r7+8] = r3
    b[r9+0] = r8
L0202ebb0:
    r6 = 0
    b[r4+1] = r6
    h[r4+8] = r6
    b[r4+2] = r6
    csync
    r0 = r4
    call effect_ownership_release
    r5 = r4
    r0 = [++r5=48]
    if (r0 == 0) goto L0202ebce
    r1 = [r7+56]
    if (r1 == 0) goto L0202ebce
    call r1
L0202ebce:
    r0 = r4  #
    [r5+0] = r6
    [r4+52] = r6
    b[r4+69] = r6
    [r4+64] = r6
    [r4+56] = r6
    call effect_ownership_capture
    goto L0202eb6c

; effect_ownership_groups: 0x0202ebe2..0x0202ec30, module effect-ownership (groups)
.type effect_ownership_groups,@function
effect_ownership_groups:
    [--sp] = {rets, r7-r4}
    r2 = L01c32db0
    r1 = r0 + r2
    r1 = b[r1+14] (u)
    if (r1 == 0) goto L0202ec2c
    r0 = r0 * 0xA
    r0 = r0 + r2
    r2 = r0 + 348
    r0 = 0
    r3 = L01c2c220
    r4 = 0
    r7 = 0
L0202ec06:
    r5 = 1
    r6 = 1
    if (r7 == 0) goto L0202ec0e
    r6 = 0
L0202ec0e:
    r7 = b[r2+r4] (u)
    r7 = r7 * 0x1E0
    r7 = r7 + r3
    r7 = b[r7+4] (u)
    if (r7 != 0) goto L0202ec1e
    r5 = r7
L0202ec1e:
    r6 &= r5
    r4 = r4 + 1
    r0 = r0 + r6
    r7 = r5
    ifs (r4 < r1) goto L0202ec06
    {pc, r7-r4} = [sp++]
L0202ec2c:
    r0 = 0
    {pc, r7-r4} = [sp++]

; effect_ownership_refresh: 0x0202ec30..0x0202ec54, module effect-ownership (refresh)
.type effect_ownership_refresh,@function
effect_ownership_refresh:
    [--sp] = rets
    r0 = L01c32db0
    r0 = b[r0+3] (u)
    r1 = L01c34489
    r1 = b[r1+0] (u)
    r0 |= r1
    if ((r0 & 0xFF) == 0) goto L0202ec4c
    pc = [sp++]
L0202ec4c:
    r0 = 0
    call stereo_budget_update_suspension
    pc = [sp++]
