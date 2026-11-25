; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; modulation: 2 functions, 0x01c09eaa..0x01c09f22

; modulation_sine: 0x01c09eaa..0x01c09eca, module modulation (sine)
.type modulation_sine,@function
modulation_sine:
    r1 = r0 >>> 31
    r0 ^= r1
    r0 = r0 + 0xC0000000
    r3_r2 = r0 * r0 (s)
    r3_r2 >>= 30
    r1 = r2 >>> 1
    r1 = 0x60000000 - r1
    r1_r0 = r1 * r0 (s)
    r1_r0 >>= 30
    rts

; modulation_modulator: 0x01c09eca..0x01c09f22, module modulation (modulator)
.type modulation_modulator,@function
modulation_modulator:
    [--sp] = {rets, r6-r4}
    r1 = r1 << 2
    r1 = r1 + r0
    r4 = [++r1=512]
    r5 = [r1+16]
    r2 *= r5
    r2 = r2 + r4
    [r1+0] = r2
    r2 = [++r0=576]
    r4 = 1664525
    r2 *= r4
    r4 = 1013904223
    r2 = r2 + r4
    [r0+0] = r2
    r4 = [r1+32]
    r5 = [r1+48]
    r2 = r2 >>> 2
    r2 = r2 - r5
    r2 = r2 >>> 5
    r2 = r2 + r5
    r2 = r2 - r4  #
    [r1+48] = r2
    r2 = r2 >>> 5
    r2 = r2 + r4
    r4 = r3  #
    [r1+32] = r2
    r1 = [r1+0]
    r0 = r1  #
    r5 = [r0+4]
    r6 = r2 >>> 1
    call modulation_sine
    r0 = r0 + r6
    r1_r0 = r0 * r5 (s)
    r1_r0 >>= 30
    [r4+0] = r0
    {pc, r6-r4} = [sp++]
