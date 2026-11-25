; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 1 function, 0x01c04b34..0x01c04bac

; ram_callbacks_link_words: 0x01c04b34..0x01c04bac, module ram-callbacks (link_words)
.type ram_callbacks_link_words,@function
ram_callbacks_link_words:
    [--sp] = {rets, r6-r4}
    sp += -4
    r2 = r1
    r1 = r0 + -1
    r6 = L01c2bff0
    if (r1 < 63) goto L01c04b86
    r5 = r6 + 76
    r1 = 0
    r3_r2 = 0
    r4 = 0
    r0 = r5
    call capture_dispatch_noop_a
    r1 = 0
    r2 = 0
    r0 = r5
    call capture_dispatch_noop_b
    r1 = 0
    r3_r2 = 0
    r0 = r5
    call capture_dispatch_noop_c
    r1 = 0
    r3_r2 = 0  #
    [sp] = r4
    r0 = r5
    call capture_dispatch_noop_d
    r0 = 0
    r1 = 0
    [r6+64] = r0
    [r6+68] = r1
    goto L01c04b9a
L01c04b86:
    r1 = r2 + -1
    [r6+68] = r0
    r4 = r0
    if (r1 <= 62) {
    r4 = r2
    }
    [r6+64] = r4
L01c04b9a:
    r1 = L01c340cc
    [r1+64] = r0
    [r1+68] = r4
    sp += 4
    {pc, r6-r4} = [sp++]
