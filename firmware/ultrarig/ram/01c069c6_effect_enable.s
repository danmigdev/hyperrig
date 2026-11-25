; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_enable: 2 functions, 0x01c069c6..0x01c06b2c

; effect_enable_tail_type: 0x01c069c6..0x01c069e4, module effect-enable (tail_type)
.type effect_enable_tail_type,@function
effect_enable_tail_type:
    r1 = r0 + -5
    r0 = 0
    if (r1 <= 30) {
    r0 = r1 & 0x7FFFFFFF
    r1 = 2118123521
    r0 = r1 >> r0
    r0 = r0 & 0x1
    }
    rts

; effect_enable_fade: 0x01c069e4..0x01c06b2c, module effect-enable (fade)
.type effect_enable_fade,@function
effect_enable_fade:
    [--sp] = {rets, r6-r4}
    r4 = r0
    r0 = h[r4+8] (u)
    if (r0 == 0) goto L01c06a0a
    if (r1 == 0) goto L01c06b22
    r0 = b[r4+0] (u)
    r0 += -27
    if (r0 > 8) goto L01c06b22
    r1 = 497
    r0 = r1 & (1 << r0)
    if (r0 == 0) goto L01c06b22
    r0 = 5
    b[r4+10] = r0
    {pc, r6-r4} = [sp++]
L01c06a0a:
    r0 = b[r4+11] (u)
    r2 = b[r4+10] (u)
    if (r1 == 0) goto L01c06a22
    if (r2 != 2) goto L01c06a22
    if (r0 == 0) goto L01c06a28
    r0 = 0x4 - r0
    b[r4+11] = r0
    r0 = 1
    b[r4+10] = r0
    {pc, r6-r4} = [sp++]
L01c06a22:
    if (r1 != 0) goto L01c06a2e
    if (r2 != 3) goto L01c06a2e
L01c06a28:
    r0 = 0
    b[r4+10] = r0
    {pc, r6-r4} = [sp++]
L01c06a2e:
    if (r1 == 0) goto L01c06a86
    r0 = [r4+84]
    r6 = r4 + 288  #
    r1 = b[r4+0] (u)
    if (r0 == 0) goto L01c06ac2
    r1 += -11
    if (r1 > 28) goto L01c06afc
    r2 = L01c34194
    tbb [r1]
effect_enable_fade_branches:
    .byte (L01c06a68 - effect_enable_fade_branches) / 2, (L01c06a68 - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06a68 - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2
    .byte (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2
    .byte (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06aa4 - effect_enable_fade_branches) / 2, (L01c06af4 - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2
    .byte (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06afc - effect_enable_fade_branches) / 2, (L01c06ac6 - effect_enable_fade_branches) / 2, (L01c06a68 - effect_enable_fade_branches) / 2
    .byte 0x00  ; alignment
L01c06a68:
    r1 = [r4+88]
    if (r1 < 1024) goto L01c06a76
    r2 = [r2+0]
    if (r2 != 0) goto L01c06ae8
L01c06a76:
    r1 = r1 + 1
    r1 = r1 >> 1
    if (r1 == 0) goto L01c06afc
    r2 = 0
L01c06a7e:
    [r0++=4] = r2
    if (--r1 != 0) goto L01c06a7e
    goto L01c06afc
L01c06a86:
    if (r2 == 4) goto L01c06a8e
    if (r2 != 1) goto L01c06a9c
L01c06a8e:
    if (r0 == 0) goto L01c06a28
    r0 = 0x4 - r0
    b[r4+11] = r0
    r0 = 2
    b[r4+10] = r0
    {pc, r6-r4} = [sp++]
L01c06a9c:
    r0 = 0
    b[r4+11] = r0
    r1 = 2
    goto L01c06b20
L01c06aa4:
    r2 = [r2+0]
    if (r2 != 0) goto L01c06b24
    r1 = 0
    r2 = 0
L01c06aac:
    [r0+r2<<2] = r1
    r2 = r2 + 1
    if (r2 != 2048) goto L01c06aac
L01c06ab8:
    r0 = r4
    call effect_setup_refresh29  ; @call.xl
    goto L01c06afc
L01c06ac2:
    if (r1 != 38) goto L01c06afc
L01c06ac6:
    r0 = 0
    [r6+12] = r0
    [r6+8] = r0
    r1 = 0
    [r4+288] = r0
    [r4+292] = r1
    [r4+336] = r0
    [r4+340] = r1
    [r4+328] = r0
    [r4+332] = r1
    goto L01c06afc
L01c06ae8:
    r1 = r1 << 1
    r1 = r1 + 2
    r1 = r1 & 0xFFFFFFFC
    call r2
    goto L01c06afc
L01c06af4:
    r0 = r4
    call effect_setup_refresh30  ; @call.xl
L01c06afc:
    r0 = r4
    call effect_enable_duration  ; @call.xl
    r5 = r0  #
    r2 = b[r4+0] (u)
    r1 = 1
    if (r2 != 7) goto L01c06b1a
    r0 = [r6+0]
    if (r0 == 0) goto L01c06b1a
    call effect_enable_ir_reset  ; @call.xl
    r1 = 4
L01c06b1a:
    b[r4+11] = r5
    if (r5 == 0) goto L01c06b20
    r1 = 3
L01c06b20:
    b[r4+10] = r1
L01c06b22:
    {pc, r6-r4} = [sp++]
L01c06b24:
    r1 = 8192
    call r2
    goto L01c06ab8
