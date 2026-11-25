; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_enable: 8 functions, 0x020303f4..0x02030614

; effect_enable_duration: 0x020303f4..0x02030466, module effect-enable (duration)
.type effect_enable_duration,@function
effect_enable_duration:
    [--sp] = {rets, r4}
    r1 = r0
    r3 = b[r1+0] (u)
    r4 = r3 + -11
    r0 = 0
    r2 = r1 + 304
    if (r4 < 2) goto L02030418
    if (r3 == 39) goto L0203041c
    if (r3 == 25) goto L0203043e
    if (r3 == 29) goto L0203044e
    if (r3 != 15) goto L0203043c
L02030418:
    r3 = [r2+0]
    goto L02030420
L0203041c:
    r3 = [r1+400]
L02030420:
    r2 = [r2+4]
    r2 = r2 + r3
L02030424:
    ifs (r2 < 1) goto L0203043c
    r1 = [r1+84]
    if (r1 == 0) goto L0203043c
    r0 = r2 >> 16
    r0 = r0 + 146
    r0 = r0 >> 7
    if (r0 >= 16) {
    r0 = 16
    }
L0203043c:
    {pc, r4} = [sp++]
L0203043e:
    r3 = [r2+20]
    r4 = [r2+16]
    r3 = smax(r4, r3)  #
    r2 = [r2+28]
    r2 = r2 >>> 1
    r2 = r2 + r3
    goto L02030424
L0203044e:
    r3 = 369
    r3 = b[r1+r3] (u)
    if (r3 != 0) goto L0203043c
    r3 = [r2+4]
    r2 = [r2+0]
    r2 = smax(r2, r3)
    r2 = r2 + 0x800000
    goto L02030424

; effect_enable_commit_core: 0x02030466..0x02030520, module effect-enable (commit_core)
.type effect_enable_commit_core,@function
effect_enable_commit_core:
    [--sp] = {rets, r7-r4}
    r6 = r2
    r4 = r1
    r2 = r0
    call biquad_coefficients_counter  ; @call.xl
    r0 = -1
    if (r2 > 15) goto L020304e2
    r1 = r2 * 0x1E0
    r3 = L01c2c220
    r5 = r1 + r3
    r1 = b[r5+2] (u)
    if (r1 == 0) goto L020304e2
    r3 = b[r5+1] (u)
    if (r4 == 0) goto L0203049a
    if (r3 != 0) goto L02030496
    r0 = h[r5+8] (u)
    r3 = 0
    if (r0 == 0) goto L020304e4
L02030496:
    if (r3 != 0) goto L020304d4
    goto L020304c8
L0203049a:
    if (r3 == 0) goto L020304b6
    r0 = L01c1f7e4
    r0 = [r0+0]
    if (r0 == 0) goto L020304b6
    r0 = b[r5+0] (u)
    call effect_enable_tail_type  ; @call.xl
    if (r0 == 0) goto L020304b6
    r0 = 1500
    h[r5+8] = r0
L020304b6:
    r0 = 1
    r1 = 1
    if ((r3 & 0xFF) == 0) {
    r1 = 0
    }
    if (r4 != 0) goto L020304c4
    r0 = r4
L020304c4:
    r0 ^= r1
    if (r0 == 0) goto L020304d8
L020304c8:
    r0 = r5
    r1 = r4
    call effect_enable_fade  ; @call.xl
L020304d2:
    if (r4 == 0) goto L020304d8
L020304d4:
    r0 = 0
    h[r5+8] = r0
L020304d8:
    r0 = 1
    if (r4 != 0) goto L020304de
    r0 = r4
L020304de:
    b[r5+1] = r0
    r0 = 0
L020304e2:
    {pc, r7-r4} = [sp++]
L020304e4:
    r0 = r2
    call enable_resources_enable_cost
    r7 = r0
    if (r6 != 0) goto L0203050a
L020304ee:
    r0 = r5
    call enable_resources_make_resource
    if (r0 != 0) goto L020304e2
    r0 = 1
    r1 = 1
    if (r4 != 0) goto L020304fe
    r1 = r4
L020304fe:
    r2 = b[r5+1] (u)
    if (r2 != 0) goto L02030504
    r0 = r2
L02030504:
    if (r1 != r0) goto L020304c8
    goto L020304d2
L0203050a:
    call effect_setup_total_cost
    r1 = L01c32db0
    r2 = r0 + r7  #
    r1 = [r1+48]
    r0 = -4
    if (r2 > r1) goto L020304e2
    goto L020304ee

; effect_enable_finish: 0x02030520..0x02030530, module effect-enable (finish)
.type effect_enable_finish,@function
effect_enable_finish:
    [--sp] = {rets, r4}
    r4 = r0
    if (r4 == 0) goto L0203052a
L02030526:
    r0 = r4
    {pc, r4} = [sp++]
L0203052a:
    call effect_ownership_refresh
    goto L02030526

; effect_enable_commit: 0x02030530..0x0203053a, module effect-enable (commit)
.type effect_enable_commit,@function
effect_enable_commit:
    [--sp] = rets
    r2 = 1
    call effect_enable_commit_core
    call effect_enable_finish
    pc = [sp++]

; effect_enable_fast_core: 0x0203053a..0x020305f8, module effect-enable (fast_core)
.type effect_enable_fast_core,@function
effect_enable_fast_core:
    [--sp] = {rets, r6-r4}
    r6 = r2
    r5 = r0
    r0 = -1
    if (r5 > 15) goto L020305c6
    r2 = r5 * 0x1E0
    r3 = L01c2c220
    r4 = r2 + r3
    r2 = b[r4+2] (u)
    if (r2 == 0) goto L020305c6
    if (r1 == 0) goto L0203058c
    r0 = b[r4+1] (u)
    if (r0 != 0) goto L0203056e
    r0 = h[r4+8] (u)
    if (r0 != 0) goto L0203056e
    r0 = b[r4+0] (u)
    if (r0 != 7) goto L020305c8
    r0 = [r4+288]
    if (r0 == 0) goto L020305d6
L0203056c:
    if (r6 != 0) goto L020305da
L0203056e:
    call biquad_coefficients_counter  ; @call.xl
    r0 = b[r4+1] (u)
    if (r0 != 0) goto L02030582
    r1 = 1
    r0 = r4
    call effect_enable_fade  ; @call.xl
L02030582:
    r0 = 1
    b[r4+1] = r0
    r0 = 0
    h[r4+8] = r0
    {pc, r6-r4} = [sp++]
L0203058c:
    call biquad_coefficients_counter  ; @call.xl
    r5 = r4
    r0 = b[++r5=1] (u)
    if (r0 == 0) goto L020305b6
    r1 = L01c1f7e4
    r1 = [r1+0]
    if (r1 == 0) goto L020305b6
    r0 = b[r4+0] (u)
    call effect_enable_tail_type  ; @call.xl
    if (r0 == 0) goto L020305b8
    r0 = 1500
    h[r4+8] = r0
    goto L020305b8
L020305b6:
    if (r0 == 0) goto L020305c2
L020305b8:
    r1 = 0
    r0 = r4
    call effect_enable_fade  ; @call.xl
L020305c2:
    r0 = 0
    b[r5+0] = r0
L020305c6:
    {pc, r6-r4} = [sp++]
L020305c8:
    r0 = r4
    call effect_setup_demand
    if (r0 == 0) goto L0203056c
    r0 = [r4+84]
    if (r0 != 0) goto L0203056c
L020305d6:
    r0 = -6
    {pc, r6-r4} = [sp++]
L020305da:
    call effect_setup_total_cost
    r6 = r0
    r0 = r5
    call enable_resources_enable_cost
    r1 = L01c32db0
    r2 = r0 + r6  #
    r1 = [r1+48]
    r0 = -4
    if (r2 <= r1) goto L0203056e
    {pc, r6-r4} = [sp++]

; effect_enable_fast: 0x020305f8..0x02030602, module effect-enable (fast)
.type effect_enable_fast,@function
effect_enable_fast:
    [--sp] = rets
    r2 = 1
    call effect_enable_fast_core
    call effect_enable_finish
    pc = [sp++]

; effect_enable_fast_unchecked: 0x02030602..0x0203060a, module effect-enable (fast_unchecked)
.type effect_enable_fast_unchecked,@function
effect_enable_fast_unchecked:
    [--sp] = rets
    r2 = 0
    call effect_enable_fast_core
    pc = [sp++]

; effect_enable_commit_unchecked: 0x0203060a..0x02030614, module effect-enable (commit_unchecked)
.type effect_enable_commit_unchecked,@function
effect_enable_commit_unchecked:
    [--sp] = rets
    r2 = 0
    call effect_enable_commit_core
    pc = [sp++]
