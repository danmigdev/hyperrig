; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 5 functions, 0x01c05d4a..0x01c05e14

; effect_setup_ir_partition_cost: 0x01c05d4a..0x01c05d6a, module effect-setup (ir_partition_cost)
.type effect_setup_ir_partition_cost,@function
effect_setup_ir_partition_cost:
    r0 += 127
    r2 = r0 >> 7
    r0 = 377
    r0 *= r2
    r0 = r0 + 5950
    if (r2 != 0) goto L01c05d5e
    r0 = 6327
L01c05d5e:
    r2 = 2600
    if (r1 != 0) goto L01c05d66
    r2 = r1
L01c05d66:
    r0 = r0 - r2
    rts

; effect_setup_ir_fallback_cost: 0x01c05d6a..0x01c05d78, module effect-setup (ir_fallback_cost)
.type effect_setup_ir_fallback_cost,@function
effect_setup_ir_fallback_cost:
    r0 += 63
    r0 = r0 >> 6
    r0 = r0 * 0xE6
    r0 = r0 + 6125
    rts

; effect_setup_has_mode: 0x01c05d78..0x01c05d92, module effect-setup (has_mode)
.type effect_setup_has_mode,@function
effect_setup_has_mode:
    r1 = r0 + -3
    r0 = 0
    if (r1 <= 20) {
    r0 = effect_support_selector
    r0 = [r0+r1<<2]
    r0 = r0 >> 31
    r0 ^= 1
    }
    rts

; effect_setup_default_mode: 0x01c05d92..0x01c05dcc, module effect-setup (default_mode)
.type effect_setup_default_mode,@function
effect_setup_default_mode:
    r1 = r0
    r2 = r1 + -3
    r0 = 0
    if (r2 > 20) goto L01c05dca
    r3 = 2089153
    r3 >>= r2
    if ((r3 & 1) == 0) goto L01c05dca
    r0 = effect_support_selector
    r0 = [r0+r2<<2]
    r0 = r0 * 0xC
    r1 = r1 * 0x54
    r0 = r0 + r1
    r1 = effect_parameter_metadata
    r0 = r0 + r1
    r0 = h[r0+4] (s)
L01c05dca:
    rts

; effect_setup_mode_cost: 0x01c05dcc..0x01c05e14, module effect-setup (mode_cost)
.type effect_setup_mode_cost,@function
effect_setup_mode_cost:
    r2 = effect_processing_costs
    r2 = [r2+r0<<2]
    if (r1 != 3) goto L01c05df8
    r1 = r0 + -3
    r0 = r2 << 1
    r0 = r0 + 1875
    r2 = 0
    if (r1 <= 20) {
    r2 = effect_processing_oversampling_costs
    r2 = [r2+r1<<2]
    }
    r0 = r0 + r2
    rts
L01c05df8:
    r0 = 3990
    if (r1 != 2) {
    r0 = 130
    }
    r3 = 1875
    if (r1 != 1) {
    r3 = r0
    }
    r0 = r2 << r1
    r0 = r0 + r3
    rts
