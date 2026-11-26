; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 5 functions, 0x01c1308e..0x01c130b4

; ram_callbacks_clear_pointed: 0x01c1308e..0x01c13098, module ram-callbacks (clear_pointed)
.type ram_callbacks_clear_pointed,@function
ram_callbacks_clear_pointed:
    r0 = [sp+12]
    if (r0 == 0) goto L01c13096
    [r0+0] = 0x0
L01c13096:
    rts

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; ram_callbacks_zero_stub_b: 0x01c13098..0x01c1309c, module ram-callbacks (zero_stub_b)
.type ram_callbacks_zero_stub_b,@function
ram_callbacks_zero_stub_b:
    r0 = 0
    rts

; ram_callbacks_zero_stub_c: 0x01c1309c..0x01c130a0, module ram-callbacks (zero_stub_c)
.type ram_callbacks_zero_stub_c,@function
ram_callbacks_zero_stub_c:
    r0 = 0
    rts

; ram_callbacks_zero_stub_d: 0x01c130a0..0x01c130a4, module ram-callbacks (zero_stub_d)
.type ram_callbacks_zero_stub_d,@function
ram_callbacks_zero_stub_d:
    r0 = 0
    rts
.endif

; ram_callbacks_clear_record: 0x01c130a4..0x01c130b4, module ram-callbacks (clear_record)
.type ram_callbacks_clear_record,@function
ram_callbacks_clear_record:
    r2 = r0
    r0 = 0
    [r2+12] = r0
    [r2+8] = r0
    r1 = 0
    [r2+0] = r0
    [r2+4] = r1
    rts
