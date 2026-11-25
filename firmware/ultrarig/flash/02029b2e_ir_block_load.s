; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_block_load: 2 functions, 0x02029b2e..0x02029c22

; ir_block_load_block_load: 0x02029b2e..0x02029bfa, module ir-block-load (block_load)
.type ir_block_load_block_load,@function
ir_block_load_block_load:
    [--sp] = {rets, r15-r4}
    r10 = r1
    r13 = r0
    r4 = L01c2c220
    r11 = L01c3441c
    r12 = L01c32db0
    r5 = 0
    r8 = 0
    goto L02029bda
L02029b4c:
    r6 = r7
    r0 = b[++r6=69] (u)
    if (r0 == 0) goto L02029bec
    if (r0 != r13) goto L02029bec
    if (r10 == 0) goto L02029b64
    r0 = [r7+64]
    if (r0 == r10) goto L02029bec
L02029b64:
    r14 = [r7+52]
    r0 = 1
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    r1 = [r12+52]
    if (r1 == 0) goto L02029bb8
    r0 = [r11+0]
    if (r0 == 0) goto L02029bb8
    r0 = r14 << 1
    r0 = r0 + 2
    r0 = r0 & 0xFFFFFFFC
    call r1
    r15 = r0
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
    if (r15 == 0) goto L02029bc0
    r9 = r7
    r1 = [++r9=64]
    r11 = [r11+0]
    r0 = r13
    r2 = r15
    r3 = r14
    call r11
    if (r0 == 0) goto L02029bc6
    r1 = [r12+56]
    r0 = r15
    call r1
    r8 = -1
    goto L02029bd2
L02029bb8:
    r0 = 0
    call effect_parameter_lifecycle_resource_mode_callback  ; @call.xl
L02029bc0:
    r8 = -3
    goto L02029bec
L02029bc6:
    [r7+48] = r15
    r0 = 0
    b[r6+0] = r0
    [r9+0] = r0
L02029bd2:
    r11 = L01c3441c
    goto L02029bec
L02029bda:
    r7 = r5 + r4
    r0 = b[r7+2] (u)
    if (r0 == 0) goto L02029bec
    r0 = b[r5+r4] (u)
    if (r0 != 7) goto L02029bec
    r0 = [r7+48]
    if (r0 == 0) goto L02029b4c
L02029bec:
    r5 = r5 + 480
    if (r5 != 7680) goto L02029bda
    r0 = r8
    {pc, r15-r4} = [sp++]

; ir_block_load_ir_word: 0x02029bfa..0x02029c22, module ir-block-load (ir_word), slot-queries (slot_ir_word)
.type ir_block_load_ir_word,@function
ir_block_load_ir_word:
    [--sp] = {rets, r4}
    r1 = r0
    r0 = 0
    if (r1 > 15) goto L02029c20
    r2 = r1 * 0x1E0
    r3 = L01c2c220
    r1 = r2 + r3
    r4 = b[r1+2] (u)
    if (r4 == 0) goto L02029c20
    r2 = b[r2+r3] (u)
    if (r2 == 7) {
    r0 = [r1+292]
    }
L02029c20:
    {pc, r4} = [sp++]
