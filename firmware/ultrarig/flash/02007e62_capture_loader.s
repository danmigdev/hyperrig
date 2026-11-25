; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_loader: 9 functions, 0x02007e62..0x02008016

; capture_loader_valid: 0x02007e62..0x02007e9e, module capture-loader (valid)
.type capture_loader_valid,@function
capture_loader_valid:
    r1 = r0
    r0 = r1 << 24
    r2 = r0 + 0x18000000
    r0 = 0
    if (r2 > 805306368) goto L02007e9c
    r2 = r1 >> 24
    r1 = r1 >> 8
    if (r2 == 1) goto L02007e84
    if (r2 != 0) goto L02007e9c
    r1 = r1.l (u)
    r0 = 1
    if (r1 != 0) goto L02007e9a
    rts
L02007e84:
    r0 = r1 << 16
    r1 = 13172735
    r1 += r0  ; @add.rr
    r2 = 39452671
    r0 = 1
    if (r1 < r2) goto L02007e9c
L02007e9a:
    r0 = 0
L02007e9c:
    rts

; capture_loader_gain_value: 0x02007e9e..0x02007eac, module capture-loader (gain_value)
.type capture_loader_gain_value,@function
capture_loader_gain_value:
    [--sp] = rets
    r3 = r0
    call capture_loader_valid
    r1 = r3.b0 (s)
    if (r0 == 0) goto L02007eaa
    r0 = r1
L02007eaa:
    pc = [sp++]

; capture_loader_aux: 0x02007eac..0x02007ece, module capture-loader (aux)
.type capture_loader_aux,@function
capture_loader_aux:
    [--sp] = {rets, r4}
    r3 = r1
    r4 = r0
    call capture_loader_valid
    r1 = r0
    r2 = r4 & 0xFF000000
    r0 = 0
    if (r2 != 16777216) goto L02007ecc
    if (r1 == 0) goto L02007ecc
    r0 = r4 >> 8
    r0 = r0.l (s)
    [r3+0] = r0
    r0 = 1
L02007ecc:
    {pc, r4} = [sp++]

; capture_loader_clamp: 0x02007ece..0x02007ee2, module capture-loader (clamp), dsp-transition-notification (gain_clamp)
.type capture_loader_clamp,@function
capture_loader_clamp:
    r2 = r0
    ifs (r0 >= 24) {  ; @ifs.ge.ri.s12
    r2 = 24
    }
    r1 = -24
    ifs (r0 >= -24) {
    r1 = r2
    }
    r0 = r1
    rts

; capture_loader_scale: 0x02007ee2..0x02007ef2, module capture-loader (scale), dsp-transition-notification (gain_scale)
.type capture_loader_scale,@function
capture_loader_scale:
    [--sp] = rets
    call capture_loader_clamp
    r1 = L02033c28
    r0 = [r1+r0<<2]
    pc = [sp++]

; capture_loader_mix: 0x02007ef2..0x02007f3a, module capture-loader (mix), dsp-transition-notification (gain_mix)
.type capture_loader_mix,@function
capture_loader_mix:
    [--sp] = {rets, r9, r8, r6-r4}
    r6 = L01c26890
    r1 = [r6+264]
    r5 = [r6+268]
    r3 = r0
    r0 = r1
    call capture_loader_scale
    r4 = r0
    if (r5 == 0) goto L02007f22
    r0 = r5
    call capture_loader_scale
    r8 = 0x800000
    r9 = 0
    r9_r8 += r0 * r4 (s)
    r9_r8 >>= 24
    r4 = r8
L02007f22:
    r0 = r6 + 272
    [r0+0] = r4
    r1 = 1
    if (r3 != 0) goto L02007f2e
    r1 = r3
L02007f2e:
    b[r6+16] = r1
    [r0+4] += 1  ; @rmw.add.s12
    {pc, r9, r8, r6-r4} = [sp++]

; capture_loader_set_gain: 0x02007f3a..0x02007f50, module capture-loader (set_gain), dsp-transition-notification (gain_set_gain)
.type capture_loader_set_gain,@function
capture_loader_set_gain:
    [--sp] = rets
    r3 = r1
    call capture_loader_clamp
    r1 = L01c26890
    [r1+264] = r0
    r0 = r3
    call capture_loader_mix
    pc = [sp++]

; capture_loader_apply_metadata: 0x02007f50..0x02007f7e, module capture-loader (apply_metadata)
.type capture_loader_apply_metadata,@function
capture_loader_apply_metadata:
    [--sp] = {rets, r8-r4}
    r4 = r1
    r6 = r0
    call capture_loader_gain_value
    r8 = L01c26890
    r5 = r0
    r7 = r8
    [++r7=696] = r5
    r1 = r7 + 4
    r0 = r6
    call capture_loader_aux
    [r7+8] = r0
    if (r0 != 0) goto L02007f76
    r0 = 0
    [r8+700] = r0
L02007f76:
    r0 = r5
    r1 = r4
    call capture_loader_set_gain
    {pc, r8-r4} = [sp++]

; capture_loader_signature: 0x02007f7e..0x02008016, module capture-loader (signature)
.type capture_loader_signature,@function
capture_loader_signature:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = 0
    r5 = r1  #
    [sp] = r4
    r1 = 0xDF000
    ifs (r0 >= 8) {  ; @ifs.ge.ri.s12
    r1 = 524280
    r0 += r1  ; @add.rr
    r1 = 0xCF000
    }
    r0 = r0 << 13
    r0 += r1  ; @add.rr
    r0 = r0 | 0x28
    r1 = sp + 0
    r2 = 4
    call storage_control_read
    if (r0 != 0) goto L02008010
    r0 = [r5+4]
    if (r0 < 4) goto L02008010
    r1 = b[sp] (u)
    if (r1 != 65) goto L02007fd4
    r2 = b[sp+1] (u)
    if (r2 != 50) goto L02007fd4
    r2 = b[sp+2] (u)
    if (r2 != 76) goto L02007fd4
    r2 = b[sp+3] (u)
    if (r2 == 49) goto L02008010
L02007fd4:
    r4 = 1
    if (r0 == 6144) goto L02008010
    if (r0 == 7808) goto L02008010
    r4 = 0
    r2 = 1
    if (r1 == 65) {  ; @if.eq.ri.s12
    r2 = 0
    }
    if (r0 < 64) goto L02008010
    if (r2 != 0) goto L02008010
    r0 = b[sp+1] (u)
    if (r0 != 77) goto L02008010
    r0 = b[sp+2] (u)
    r0 += -50
    r0 = r0.b0 (u)
    if (r0 > 2) goto L02008010
    r0 = b[sp+3] (u)
    r4 = 1
    if (r0 == 0) goto L02008010
    r4 = 0
L02008010:
    r0 = r4
    sp += 4
    {pc, r5, r4} = [sp++]
