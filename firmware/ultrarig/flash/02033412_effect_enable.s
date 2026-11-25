; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; effect_enable: 1 function, 0x02033412..0x0203343e

; effect_enable_memset: 0x02033412..0x0203343e, module effect-enable (memset), effect-parameter-support (memset)
.type effect_enable_memset,@function
effect_enable_memset:
    [--sp] = {rets, r4}
    r3 = r0
L02033416:
    if (r2 == 0) goto L0203343c
    .byte 0x33,0xea,0x03,0x40  ; if ((r3 & 0x3) != 0) { (then 2, else 0)
    r2 = r2 - 0x1  #
    b[r3++=1] = r1
    goto L02033416
    r4 = r2 >> 2
    r1 <= insert(r1, p:8, l:8)
    r1 <= insert(r1, p:16, l:16)
L0203342e:
    rep r4 {
    [r3++=4] = r1
    }
    if (r4 != 0) goto L0203342e
    r2 = r2 & 0x3
    rep r2 {
    b[r3++=1] = r1
    }
L0203343c:
    {pc, r4} = [sp++]
