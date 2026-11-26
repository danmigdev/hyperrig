; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 2 functions, 0x01c11f46..0x01c11f56

; ram_callbacks_signed_max: 0x01c11f46..0x01c11f4c, module ram-callbacks (signed_max)
.type ram_callbacks_signed_max,@function
ram_callbacks_signed_max:
    r0 = smax(r0, r1)
    rts

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; ram_callbacks_second_word: 0x01c11f4c..0x01c11f56, module ram-callbacks (second_word)
.type ram_callbacks_second_word,@function
ram_callbacks_second_word:
    if (r0 != 0) {
    r0 = [r0+4]
    } else {
    r0 = 0
    }
    rts
.endif
