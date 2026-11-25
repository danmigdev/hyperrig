; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_transition: 1 function, 0x02028a34..0x02028b6c

; dsp_transition_request: 0x02028a34..0x02028b6c, module dsp-transition (request), dsp-transition-notification (transition_request)
.type dsp_transition_request,@function
dsp_transition_request:
    [--sp] = {rets, r13-r4}
    sp += -56
    r9 = L01c32db0
    r2 = b[r9+28] (u)
    r8 = r1
    r5 = r0
    if (r2 != 0) goto L02028a4a
    call dsp_initialization_reset_filters
L02028a4a:
    r4 = 0
    r6 = 0
L02028a4e:
    r1 = h[r5+r6<<1] (s)
    r0 = r6
    call dsp_transition_clamp
    r7 = r9 + 218
    r1 = h[r7+r6<<1] (s)
    r2 = sp + 44
    h[r2+r6<<1] = r0
    r2 = r0.l (s)
    r0 = 1
    if (r2 == r1) {
    r0 = 0
    }
    r6 = r6 + 1
    r4 |= r0
    if (r6 != 6) goto L02028a4e
; HyperRig MINI, product option: a capture with knobs came or went (mini/product/parametric.c).
.if MINI_PRODUCT
    r0 = hyperrig_tone_due
    r0 = b[r0+0] (u)
    r4 |= r0
.endif
    if (r4 == 0) goto L02028b66
    call biquad_coefficients_counter  ; @call.xl
    r4 = 0
    b[r9+1] = r4
; HyperRig MINI, product option: the amp's controls that move a knob of the capture leave the filters flat (mini/product/parametric.c).
.if MINI_PRODUCT
    r0 = sp + 44
    r1 = r8
    call hyperrig_tone  ; @call.xl
.else
    r0 = h[sp+54] (u)
    r1 = h[r9+228] (u)
    if (r0 == r1) goto L02028aa0
    r1 = L01c3446c
    r1 = [r1+0]
    if (r1 == 0) goto L02028aa0
    r0 = r0.l (s)
    call r1
L02028aa0:
    r0 = sp + 44
    r0 = h[r0+r4<<1] (u)
    h[r7+r4<<1] = r0
    r4 = r4 + 1
    if (r4 != 6) goto L02028aa0
.endif
    r0 = r8
    ifs (r0 >= 255) {
    r0 = 255
    }
    r1 = 1
    ifs (r8 >= 1) {
    r1 = r0
    }
    r5 = r1 << 2
    ifs (r1 <= 1) {
    r5 = 1
    }
    r8 = L01c32fa0
    r6 = r8 + 144
    r7 = r8 + 320
    r10 = sp + 0
    r12 = 0
    r11 = 488
L02028ae0:
    r13 = r12 + 1
    r0 = sp + 44
    r1 = h[r0+r13<<1] (s)
    r2 = sp + 0
    r0 = r13
    call dsp_initialization_setup
    r0 = r7
    r1 = r6
    r2 = 0
L02028af8:
    r3 = sp + 0
    r3 = [r3+r2<<2]
    [r0+0] = r3
    r4 = 0
    if (r5 >= 2) {
    r4 = [r1+0]
    r3 = r3 - r4
    r4 = r3 / r5 (s)
    }
    [r0+80] = r4
    r0 = r0 + 4
    r2 = r2 + 1
    r1 = r1 + 4
    if (r2 != 5) goto L02028af8
    r0 = b[r10+40] (u)
    r1 = r12 + r8
    b[r1+r11] = r0
    r7 = r7 + 20
    r6 += 44
    r12 = r13
    if (r12 != 4) goto L02028ae0
    r0 = h[sp+44] (s)
    call dsp_initialization_gain
    [r8+480] = r0
    r1 = 0
    if (r5 <= 1) goto L02028b56
    r1 = L01c1f7d4
    r1 = [r1+0]
    r0 = r0 - r1
    r1 = r5 << 5
    r0 = r0 / r1 (s)
    r1 = r0 << 5
L02028b56:
    [r8+484] = r1
    [r8+492] = r5
    r0 = 1
    b[r9+1] = r0
    goto L02028b68
L02028b66:
    r0 = 0
L02028b68:
    sp += 56
    {pc, r13-r4} = [sp++]
