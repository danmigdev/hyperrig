; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; status_helpers: 4 functions, 0x0200eeba..0x0200ef92

; status_helpers_flags_set: 0x0200eeba..0x0200eed2, module status-helpers (flags_set)
.type status_helpers_flags_set,@function
status_helpers_flags_set:
    r0 = L01c1f180
    r1 = b[r0+2] (u)
    if (r1 == 0) goto L0200eece
    r1 = b[r0+3] (u)
    r0 = 1
    if (r1 != 0) goto L0200eecc
    r0 = r1
L0200eecc:
    rts
L0200eece:
    r0 = 0
    rts

; status_helpers_decibels: 0x0200eed2..0x0200ef12, module status-helpers (decibels)
.type status_helpers_decibels,@function
status_helpers_decibels:
    [--sp] = {rets, r4}
    if (r0 == 0) goto L0200ef0c
    r3 = 32
    r2 = 5418
L0200eedc:
    r3 += -1
    r4 = r0 >> r3
    r2 = r2 + -602
    if (r4 == 0) goto L0200eedc
    r1 = 0
    r1_r0 <<= 8
    r1_r0 >>= r3
    r0 = r0 * 0x3C
    r0 = r0 - 0x3C00
    r1 = 256
    r0 = r0 / r1 (s)
    r1 = 10
    r1 = r2 / r1 (s)
    r0 += r1  ; @add.rr
    {pc, r4} = [sp++]
L0200ef0c:
    r0 = -1440
    {pc, r4} = [sp++]

; status_helpers_status_fields: 0x0200ef12..0x0200ef54, module status-helpers (status_fields)
.type status_helpers_status_fields,@function
status_helpers_status_fields:
    [--sp] = {rets, r4}
    if (r0 == 0) goto L0200ef20
    r4 = L01c2687c
    r4 = h[r4+0] (u)
    [r0+0] = r4
L0200ef20:
    if (r1 == 0) goto L0200ef2c
    r0 = L01c26886
    r0 = b[r0+0] (u)
    [r1+0] = r0
L0200ef2c:
    if (r2 == 0) goto L0200ef38
    r0 = L01c26878
    r0 = h[r0+0] (u)
    [r2+0] = r0
L0200ef38:
    r0 = L01c26890
    if (r3 == 0) goto L0200ef4a
    r1 = 379
    r1 = [r0+r1<<2]
    [r3+0] = r1
L0200ef4a:
    r1 = 1512
    r0 = b[r0+r1] (u)
    {pc, r4} = [sp++]

; status_helpers_counter_words: 0x0200ef54..0x0200ef92, module status-helpers (counter_words)
.type status_helpers_counter_words,@function
status_helpers_counter_words:
    r1 = L01c26890
    if (r0 == 0) goto L0200ef72
    r2 = 0
    goto L0200ef6e
L0200ef60:
    r3 = r1 + 1572
    r3 = h[r3+r2<<1] (u)
    [r0+r2<<2] = r3
    r2 += 1  ; @add.ri.u5
L0200ef6e:
    if (r2 != 3) goto L0200ef60
L0200ef72:
    r0 = 324
    r2 = L01c1f180
    r3 = b[r2+r0] (u)
    r0 = 1
    r2 = 1
    if (r3 != 0) goto L0200ef88
    r2 = r3
L0200ef88:
    r3 = b[r1+1] (u)
    r1 = r2 << 1
    if (r3 != 0) goto L0200ef90
    r0 = r1
L0200ef90:
    rts
