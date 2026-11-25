; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_setup: 5 functions, 0x01c06038..0x01c060e6

; effect_setup_pool_full: 0x01c06038..0x01c0604e, module effect-setup (pool_full)
.type effect_setup_pool_full,@function
effect_setup_pool_full:
    r0 = L01c32db0
    r0 = b[r0+6] (u)
    r1 = r0 & 0xFFFFFF0F
    r0 = 1
    if (r1 != 15) {
    r0 = 0
    }
    rts

; effect_setup_group_eligible: 0x01c0604e..0x01c0606e, module effect-setup (group_eligible)
.type effect_setup_group_eligible,@function
effect_setup_group_eligible:
    r2 = r0
    r1 |= 2
    r0 = 0
    if (r1 != 3) goto L01c0606c
    r1 = r2 + -3
    if (r1 <= 20) {
    r0 = 2089153
    r0 >>= r1
    r0 = r0 & 0x1
    }
L01c0606c:
    rts

; effect_setup_group_fixed: 0x01c0606e..0x01c06088, module effect-setup (group_fixed)
.type effect_setup_group_fixed,@function
effect_setup_group_fixed:
    if (r1 != 1) goto L01c06084
    r0 += -9
    if (r0 <= 14) {
    r1 = setup_group_flags
    r0 = [r1+r0<<2]
    rts
    }
L01c06084:
    r0 = 0
    rts

; effect_setup_next_mode: 0x01c06088..0x01c06098, module effect-setup (next_mode)
.type effect_setup_next_mode,@function
effect_setup_next_mode:
    r1 = r0
    r2 = r1 + -1
    r0 = 1
    ifs (r1 <= 1) {
    r0 = r2
    }
    rts

; effect_setup_stereo_extra_cost: 0x01c06098..0x01c060e6, module effect-setup (stereo_extra_cost)
.type effect_setup_stereo_extra_cost,@function
effect_setup_stereo_extra_cost:
    r1 = r0 + -5
    if (r1 > 34) goto L01c060dc
    r0 = 2400
    tbb [r1]
setup_stereo_branches:
    .byte (L01c060d0 - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060de - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2
    .byte (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060de - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2
    .byte (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060d0 - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2
    .byte (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060ca - setup_stereo_branches) / 2, (L01c060ca - setup_stereo_branches) / 2, (L01c060d6 - setup_stereo_branches) / 2, (L01c060d6 - setup_stereo_branches) / 2, (L01c060ca - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2
    .byte (L01c060dc - setup_stereo_branches) / 2, (L01c060dc - setup_stereo_branches) / 2, (L01c060e0 - setup_stereo_branches) / 2
    .byte 0x00  ; alignment
L01c060ca:
    r0 = 1400
    rts
L01c060d0:
    r0 = 1200
    rts
L01c060d6:
    r0 = 700
    rts
L01c060dc:
    r0 = 0
L01c060de:
    rts
L01c060e0:
    r0 = 1140
    rts
