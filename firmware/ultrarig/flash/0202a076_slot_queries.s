; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; slot_queries: 3 functions, 0x0202a076..0x0202a1be

; slot_queries_type_demand: 0x0202a076..0x0202a13c, module slot-queries (type_demand)
.type slot_queries_type_demand,@function
slot_queries_type_demand:
    [--sp] = {rets, r7-r4}
    r4 = r1
    r6 = r0
    if (r6 != 7) goto L0202a0de
    r1 = L01c32db0
    r2 = [r1+64]
    r0 = 0
    if (r2 == 0) goto L0202a12e
    r2 = [r1+60]
    if (r2 != 0) goto L0202a0a2
    r1 = [r1+72]
    if (r1 == 0) goto L0202a12e
    r1 = L01c3441c
    r1 = [r1+0]
    if (r1 == 0) goto L0202a12e
L0202a0a2:
    r1 = L01c1f7d0
    r1 = [r1+0]
    r6 = 1
    if (r1 != 0) goto L0202a0b0
    r6 = r1
L0202a0b0:
    r5 = 0
    if (r1 == 0) goto L0202a130
    r1 = 21
    r0 = r6
    call ir_convolution_installation_effective
    call ir_convolution_size  ; @call.xl
    r0 = r0 + 3
    r5 = r0 & 0xFFFFFFFC
    r1 = 0
    r0 = r6
    call ir_convolution_installation_effective
    call ir_convolution_size  ; @call.xl
    r0 = r0 + 3
    r0 = r0 & 0xFFFFFFFC
    goto L0202a130
L0202a0de:
    r1 = r6 + -1
    r0 = 0
    r5 = 0
; HyperRig MINI, product option: the memory of an effect of HyperRig is the same whatever its parameters are.
.if MINI_PRODUCT
    if (r1 <= 38) goto Lhr_demand_listed
    r0 = r6
    call effect_setup_demand_by_type
    call ram_callbacks_aligned_size  ; @call.xl
    r5 = r0
    goto L0202a130
Lhr_demand_listed:
.else
    if (r1 > 38) goto L0202a130
.endif
    r0 = r6 * 0x54
    r1 = effect_parameter_metadata
    r7 = r0 + r1
    r1 = h[r7+4] (s)
    r2 = h[r7+76] (s)
    r0 = r6
    call effect_setup_demand_by_type
    call ram_callbacks_aligned_size  ; @call.xl
    r5 = r0  #
    r3 = [r7+8]
    r2 = 0
    r1 = 0
    if (r3 == 0) goto L0202a116
    r1 = h[r7+2] (s)
L0202a116:
    r0 = [r7+80]
    if (r0 == 0) goto L0202a120
    r2 = h[r7+74] (s)
L0202a120:
    r0 = r6
    call effect_setup_demand_by_type
    call ram_callbacks_aligned_size  ; @call.xl
    goto L0202a130
L0202a12e:
    r5 = 0
L0202a130:
    if (r4 == 0) goto L0202a138
    r0 = umax(r0, r5)
    [r4+0] = r0
L0202a138:
    r0 = r5
    {pc, r7-r4} = [sp++]

; slot_queries_slot_memory: 0x0202a13c..0x0202a19a, module slot-queries (slot_memory)
.type slot_queries_slot_memory,@function
slot_queries_slot_memory:
    [--sp] = {rets, r5, r4}
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L0202a198
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r4 = r1 + r2
    r1 = b[r4+2] (u)
    if (r1 == 0) goto L0202a198
    r0 = [r4+84]
    if (r0 == 0) goto L0202a176
    r1 = b[r4+0] (u)
    r0 = 0
    if (r1 != 7) {
    r0 = 16
    }
    r1 = [r4+88]
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    r5 = r1 + r0
    goto L0202a178
L0202a176:
    r5 = 0
L0202a178:
    r0 = r4
    call ram_callbacks_halfword_sum  ; @call.xl
    r0 = r0 + r5  #
    r1 = b[r4+7] (u)
    r1 = r1 << 4
    r0 = r0 + r1  #
    r2 = [r4+48]
    if (r2 == 0) goto L0202a198
    r1 = [r4+52]
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    r0 = r0 + r1
L0202a198:
    {pc, r5, r4} = [sp++]

; slot_queries_slot_parts: 0x0202a19a..0x0202a1be, module slot-queries (slot_parts)
.type slot_queries_slot_parts,@function
slot_queries_slot_parts:
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L0202a1bc
    r1 = r1 * 0x1E0
    r2 = L01c2c220
    r1 = r1 + r2
    r2 = b[r1+2] (u)
    if (r2 == 0) goto L0202a1bc
    r2 = [r1+84]
    if (r2 == 0) goto L0202a1bc
    r0 = b[r1+7] (u)
    r0 = r0 + 1
L0202a1bc:
    rts
