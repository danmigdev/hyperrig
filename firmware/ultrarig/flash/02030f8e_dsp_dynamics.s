; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_dynamics: 3 functions, 0x02030f8e..0x0203108e

; dsp_dynamics_configure: 0x02030f8e..0x0203104e, module dsp-dynamics (configure), dsp-transition-notification (dynamics_configure)
.type dsp_dynamics_configure,@function
dsp_dynamics_configure:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r0 = r1 >>> 31
    r3 = r0 & r1
    r0 = -200
    ifs (r1 >= -200) {
    r0 = r3
    }
    r5 = L01c1f7f0
    r1 = r2  #
    h[r5+2] = r0
    ifs (r2 >= 2000) {
    r1 = 2000
    }
    r6 = 10
    ifs (r2 >= 10) {
    r6 = r1
    }
    r0 = itof(r0)  #
    h[r5+4] = r6
    r1 = 1092616192
    r0 = r0 / r1 (f)
    call biquad_generator_scaled_exp  ; @call.xl
    r1 = 1258291198
    r0 = r0 * r1 (f)
    r0 = ftoi(r0) (trunc)
    r1 = 8388607
    r7 = smin(r0, r1)
    ifs (r7 <= 1024) {
    r7 = 1024
    }
    r1 = itof(r6)  #
    r0 = [r5+8]
    r0 = utof(r0)
    r0 = r1 * r0 (f)
    r1 = 3329884160
    r0 = r1 / r0 (f)
    call biquad_generator_exp
    r1 = 0x3F800000  #
    [r5+24] = r7
    r0 = r1 - r0 (f)
    r1 = r1 + 0xA000000
    r0 = r0 * r1 (f)
    r1 = 0x3F000000
    r0 = r0 + r1 (f)
    r1 = ftoi(r0) (trunc)
    r0 = 1
    ifs (r1 <= 1) {
    r1 = 1
    }
    [r5+28] = r1
    r1 = L01c32db0
    [r1+108] = 0x0
    if (r4 != 0) goto L02031044
    r0 = r4
L02031044:
    r1 = L01c3448c
    b[r1+0] = r0
    {pc, r7-r4} = [sp++]

; dsp_dynamics_get: 0x0203104e..0x0203106c, module dsp-dynamics (get), dsp-transition-notification (dynamics_get)
.type dsp_dynamics_get,@function
dsp_dynamics_get:
    r3 = L01c3448c
    r3 = b[r3+0] (u)
    [r0+0] = r3
    r0 = L01c1f7f0
    r3 = h[r0+2] (s)
    [r1+0] = r3
    r0 = h[r0+4] (s)
    [r2+0] = r0
    rts

; dsp_dynamics_meter: 0x0203106c..0x0203108e, module dsp-dynamics (meter), dsp-transition-notification (dynamics_meter)
.type dsp_dynamics_meter,@function
dsp_dynamics_meter:
    if (r0 == 0) goto L0203107a
    r2 = L01c32db0
    r2 = [r2+112]
    [r0+0] = r2
L0203107a:
    if (r1 == 0) goto L0203108a
    r0 = L01c1f7f0
    r2 = [r0+32]
    [r1+0] = r2
    [r0+32] = 0x1000000
L0203108a:
    r0 = 48
    rts
