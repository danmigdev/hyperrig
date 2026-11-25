; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 3 functions, 0x02029ed4..0x02029fc8

; effect_setup_object_segment: 0x02029ed4..0x02029f8e, module effect-setup (object_segment)
.type effect_setup_object_segment,@function
effect_setup_object_segment:
    [--sp] = {rets, r4}
    r3 = r1
    r4 = r0
    call effect_model_construction_object_mode  ; @call.xl
    if (r0 != 2) goto L02029f0a
    r0 = model_object2_lengths
    r1 = L01c1f7f0
    r1 = [r1+8]
    r0 = h[r0+r3<<1] (u)
    r1 = r1 >> 2
    r0 *= r1
    r1 = 9999
    r0 = r0 + r1
    r1 = r1 + 1
    r0 = r0 / r1 (u)
    r0 = r0 + 12
    {pc, r4} = [sp++]
L02029f0a:
    if (r3 == 8) goto L02029f68
    if (r0 != 1) goto L02029f32
    ifs (r3 <= 3) goto L02029f70
    ifs (r3 <= 7) goto L02029f82
    r1 = r3 + -9
    r0 = 3
    if (r3 != 12) {
    r0 = r1
    }
    r1 = setup_object1_short_lengths
    r0 = h[r1+r0<<1] (u)
    goto L02029f64
L02029f32:
    r0 = r4
    call effect_model_construction_object_record  ; @call.xl
    ifs (r3 > 7) goto L02029f54
    r1 = b[r0+57] (u)
    r2 = h[r0+r3<<1] (u)
    r3 = r1 & (1 << r3)
    r1 = 0
    if (r3 != 0) goto L02029f88
L02029f4e:
    r0 = r2 + r1
    r0 = r0 + 4
    {pc, r4} = [sp++]
L02029f54:
    ifs (r3 > 11) {
    r0 = r0 + 16
    r0 += -24
    } else {
    r0 += 32
    r0 += -18
    }
    r0 = h[r0+r3<<1] (u)
L02029f64:
    r0 = r0 + 1
    {pc, r4} = [sp++]
L02029f68:
    r0 = r4
    call effect_model_construction_object_limit
    r0 = r0 + 4
    {pc, r4} = [sp++]
L02029f70:
    r0 = -3
    r2 = 17
    if ((r3 & r0) != 0) {
    r2 = 4
    }
    r0 = r3
    call effect_model_construction_object_length
    r0 = r0 + r2
    {pc, r4} = [sp++]
L02029f82:
    r0 = r3
    call effect_model_construction_object_length
    goto L02029f64
L02029f88:
    call effect_model_construction_object_extra
    r1 = r0
    goto L02029f4e

; effect_setup_segment_bytes: 0x02029f8e..0x02029f98, module effect-setup (segment_bytes)
.type effect_setup_segment_bytes,@function
effect_setup_segment_bytes:
    [--sp] = rets
    call effect_setup_object_segment
    r0 = r0 << 2
    r0 = r0 + 4
    pc = [sp++]

; effect_setup_object_total: 0x02029f98..0x02029fc8, module effect-setup (object_total)
.type effect_setup_object_total,@function
effect_setup_object_total:
    [--sp] = {rets, r7-r4}
    r4 = r0
    call effect_setup_object_extra
    r0 = r0 >> 2
    r7 = r0 + 2
    r0 = r4
    call effect_setup_object_count
    r5 = r0
    ifs (r5 >= 1) goto L02029fb4
L02029fb0:
    r0 = r7 << 1
    {pc, r7-r4} = [sp++]
L02029fb4:
    r6 = 0
L02029fb6:
    r0 = r4
    r1 = r6
    call effect_setup_segment_bytes
    r0 = r0 >> 2
    r6 = r6 + 1
    r7 = r7 + r0
    if (r5 != r6) goto L02029fb6
    goto L02029fb0
