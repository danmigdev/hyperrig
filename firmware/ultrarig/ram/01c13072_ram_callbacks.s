; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ram_callbacks: 4 functions, 0x01c13072..0x01c13080

; ram_callbacks_stub_a: 0x01c13072..0x01c13074, module ram-callbacks (stub_a)
.type ram_callbacks_stub_a,@function
ram_callbacks_stub_a:
    rts

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; ram_callbacks_stub_b: 0x01c13074..0x01c13076, module ram-callbacks (stub_b)
.type ram_callbacks_stub_b,@function
ram_callbacks_stub_b:
    rts

; ram_callbacks_process_call: 0x01c13076..0x01c1307e, module ram-callbacks (process_call)
.type ram_callbacks_process_call,@function
ram_callbacks_process_call:
    [--sp] = rets
    call capture_live_process
    pc = [sp++]

; ram_callbacks_stub_c: 0x01c1307e..0x01c13080, module ram-callbacks (stub_c)
.type ram_callbacks_stub_c,@function
ram_callbacks_stub_c:
    rts
.endif
