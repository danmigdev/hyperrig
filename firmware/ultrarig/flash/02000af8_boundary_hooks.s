; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; boundary_hooks: 5 functions, 0x02000af8..0x02000b80

; boundary_hooks_record_check: 0x02000af8..0x02000b04, module boundary-hooks (record_check)
.type boundary_hooks_record_check,@function
boundary_hooks_record_check:
    r1 = r0 >> 8
    r0 ^= r1
    r0 = r0.b0 (u)
    r0 = r0 ^ 0xA5
    rts

; boundary_hooks_record_pack: 0x02000b04..0x02000b2c, module boundary-hooks (record_pack)
.type boundary_hooks_record_pack,@function
boundary_hooks_record_pack:
    [--sp] = rets
    r3 = 1
    if (r2 != 0) goto L02000b0c
    r3 = r2
L02000b0c:
    r2 = 1023
    r1 &= r2
    r0 = r0 << 12
    r0 = r0.l (u)
    r2 = r1 | r0
    r2 <= insert(r3, p:11, l:1)
    r0 = r2
    call boundary_hooks_record_check
    r2 <= insert(r0, p:16, l:16)
    r0 = r2 | 0xC1000000
    pc = [sp++]

; boundary_hooks_rate_level: 0x02000b2c..0x02000b4a, module boundary-hooks (rate_level)
.type boundary_hooks_rate_level,@function
boundary_hooks_rate_level:
    [--sp] = {rets, r4}
    r3 = 0
    r2 = L02035c00
L02000b36:
    r1 = r3
    r3 = r1 + 1
    if (r3 > 3) goto L02000b46
    r4 = h[r2+r1<<1] (u)
    if (r4 <= r0) goto L02000b36
L02000b46:
    r0 = r1
    {pc, r4} = [sp++]

; boundary_hooks_rate_level_call: 0x02000b4a..0x02000b50, module boundary-hooks (rate_level_call)
.type boundary_hooks_rate_level_call,@function
boundary_hooks_rate_level_call:
    [--sp] = rets
    call boundary_hooks_rate_level
    pc = [sp++]

; boundary_hooks_record_store: 0x02000b50..0x02000b80, module boundary-hooks (record_store)
.type boundary_hooks_record_store,@function
boundary_hooks_record_store:
    [--sp] = {rets, r4}
    r1 = 29883900
    r1 = 1023  #
    [r1+0] = r0
    r4 = r0 & 0x800
    if ((r0 & r1) == 0) goto L02000b70
    r0 &= r1
    call boundary_hooks_rate_level_call
    r0 = r0 << 5
    r0 += 32
    goto L02000b72
L02000b70:
    r0 = 0
L02000b72:
    r0 |= r4
    r1 = L01c26890
    [r1+104] = r0
    {pc, r4} = [sp++]
