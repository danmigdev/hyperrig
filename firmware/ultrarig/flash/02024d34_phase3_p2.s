; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p2: 1 function, 0x02024d34..0x02024ece

; phase3_p2_rapp_init: 0x02024d34..0x02024ece, module phase3-p2 (rapp_init)
.type phase3_p2_rapp_init,@function
phase3_p2_rapp_init:
    [--sp] = {rets, r8-r4}
    r0 = 0
    r5 = 0
    call L02024d10
    r8 = L020353e8
    r7 = 0
L02024d44:
    r0 = 92
    call L02055e38  ; @call.xl
    r1 = r0 | 0x10
    r0 = 92
    call L02055a4e  ; @call.xl
    r0 = r5.b0 (s)
    r4 = 127
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r4 = r5
    }
    r0 = 93
    call L02055e38  ; @call.xl
    r0 = r0 & 0xFFFFFF80
    r0 |= r4
    r1 = r0.b0 (u)
    r0 = 93
    call L02055a4e  ; @call.xl
    r6 = [r8+r7<<2]
    if (r6 >= 511) {
    r6 = 511
    }
    r0 = 92
    call L02055e38  ; @call.xl
    r4 = r0
    r1 = r6.b0 (u)
    r0 = 94
    call L02055a4e  ; @call.xl
    r0 = r6 >> 3
    r0 = r0 & 0x20
    r1 = r4 & 0xFFFFFFDF
    r1 |= r0
    r0 = 92
    call L02055a4e  ; @call.xl
    r0 = 92
    call L02055e38  ; @call.xl
    r1 = r0 & 0xFFFFFFEF
    r0 = 92
    call L02055a4e  ; @call.xl
    r7 += 1  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
    if (r7 != 128) goto L02024d44
    r0 = 88
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 89
    r1 = 160
    call L02055a4e  ; @call.xl
    r1 = r4 & 0xFFFFFFF8
    r0 = 88
    call L02055a4e  ; @call.xl
    r0 = 81
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 82
    r1 = 100
    call L02055a4e  ; @call.xl
    r0 = 83
    r1 = 45
    call L02055a4e  ; @call.xl
    r1 = r4 | 0xC
    r0 = 81
    call L02055a4e  ; @call.xl
    r0 = 88
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 90
    r1 = 160
    call L02055a4e  ; @call.xl
    r1 = r4 & 0xFFFFFFC7
    r0 = 88
    call L02055a4e  ; @call.xl
    r0 = 81
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 84
    r1 = 100
    call L02055a4e  ; @call.xl
    r0 = 85
    r1 = 45
    call L02055a4e  ; @call.xl
    r1 = r4 | 0x30
    r0 = 81
    call L02055a4e  ; @call.xl
    r0 = 88
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 92
    call L02055e38  ; @call.xl
    r5 = r0
    r0 = 91
    r1 = 144
    call L02055a4e  ; @call.xl
    r0 = r4 & 0xFFFFFF3F
    r1 = r0 | 0x40
    r0 = 88
    call L02055a4e  ; @call.xl
    r1 = r5 & 0xFFFFFFFE
    r0 = 92
    call L02055a4e  ; @call.xl
    r0 = 81
    call L02055e38  ; @call.xl
    r4 = r0
    r0 = 86
    r1 = 214
    call L02055a4e  ; @call.xl
    r0 = 87
    r1 = 63
    call L02055a4e  ; @call.xl
    r0 = r4 | 0x80
    r1 = r0 & 0xBF
    r0 = 81
    call L02055a4e  ; @call.xl
    r0 = 2
    call L02024d10
    {pc, r8-r4} = [sp++]
