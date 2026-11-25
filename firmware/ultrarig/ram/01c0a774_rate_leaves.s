; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; rate_leaves: 2 functions, 0x01c0a774..0x01c0a7aa

; rate_leaves_fresh: 0x01c0a774..0x01c0a794, module rate-leaves (fresh)
.type rate_leaves_fresh,@function
rate_leaves_fresh:
    r1 = L01c1f7f0
    r3 = [r1+20]
    r1 = 1
    r2 = 1
    if (r3 == r0) {
    r2 = 0
    }
    r3 += -1
    if (r3 == r0) {
    r1 = 0
    }
    r0 = r2 & r1
    rts

; rate_leaves_saturate: 0x01c0a794..0x01c0a7aa, module rate-leaves (saturate)
.type rate_leaves_saturate,@function
rate_leaves_saturate:
    r2 = r0 >>> 31
    if (r1 != r2) goto L01c0a79c
L01c0a79a:
    rts
L01c0a79c:
    r0 = r1 >> 31
    r0 = r0 << 1
    r1 = 2147483647
    r0 = r0 + r1
    goto L01c0a79a
