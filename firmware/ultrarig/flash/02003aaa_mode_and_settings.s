; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; mode_and_settings: 1 function, 0x02003aaa..0x02003ba0

; mode_and_settings_device_record: 0x02003aaa..0x02003ba0, module mode-and-settings (device_record)
.type mode_and_settings_device_record,@function
mode_and_settings_device_record:
    [--sp] = {rets, r9-r4}
    sp += -100
    r7 = sp + 12
    r5 = 0
    r1 = r7
    rep 21 {
    [r1++=4] = r5
    }
    r1 = 6
    b[sp+12] = r1
    r4 = 1
    b[sp+96] = r4
    r6 = L01c1f180
    r8 = r0  #
    r1 = b[r6+4] (u)
    r2 = b[r6+11] (u)
    r9 = L01c26890
    r3 = b[r9+74] (u)
    b[sp+97] = r1
    b[sp+98] = r2
    r0 = r3 + 1
    b[sp+99] = r0
    r0 = L01c1f7e0
    r0 = b[r0+0] (u)
    r1 = b[r6+8] (u)
    b[sp+92] = r4
    r2 = [r6+96]
    b[sp+94] = r0
    b[sp+93] = r1
    b[sp+88] = r4
    h[sp+90] = r2
    call slot_queries_flag  ; @call.xl
    b[sp+13] = r0
    b[sp+84] = r4
    r0 = 3245
    r0 = [r9+r0<<2]
    b[sp+85] = r0
    r0 = sp + 8
    r1 = sp + 4
    r2 = sp + 0
    call dsp_dynamics_get  ; @call.xl
    r0 = [sp+8]
    r1 = [sp+4]
    r2 = [sp]
    b[sp+76] = r4
    b[sp+77] = r0
    h[sp+78] = r1
    h[sp+80] = r2
    r4 = r7 + 4
    goto L02003b58
L02003b4a:
    r0 = r5
    call biquad_pipeline_parameter  ; @call.xl
    b[r4+r5] = r0
    r5 += 1  ; @add.ri.u5
L02003b58:
    if (r5 != 5) goto L02003b4a
    r0 = sp + 12
    r0 += 9  ; @add.ri.u5
    r1 = 0
    goto L02003b70
L02003b64:
    r2 = r1 + r6
    r2 = b[r2+116] (u)
    b[r0+r1] = r2
    r1 += 1  ; @add.ri.u5
L02003b70:
    if (r1 != 4) goto L02003b64
    r0 = [r6+144]
    r1 = 0
    b[sp+14] = r1
    r0 = ftoi(r0) (trunc)
    h[sp+28] = r0
    r4 = sp + 12
    r0 = r4 + 24
    call preset_loader_snapshot
    r0 = 1
    b[sp+72] = r0
    rep 22 {
    r0 = [r4++=4]
    [r8++=4] = r0
    }
    sp += 100
    {pc, r9-r4} = [sp++]
