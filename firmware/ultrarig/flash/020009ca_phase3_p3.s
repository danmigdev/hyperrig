; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p3: 3 functions, 0x020009ca..0x020009ee

; phase3_p3_timer_get_ms: 0x020009ca..0x020009d8, module phase3-p3 (timer_get_ms)
.type phase3_p3_timer_get_ms,@function
phase3_p3_timer_get_ms:
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    rts

; phase3_p3_wdt_or_con: 0x020009d8..0x020009e6, module phase3-p3 (wdt_or_con)
.type phase3_p3_wdt_or_con,@function
phase3_p3_wdt_or_con:
    [--sp] = rets
    r1 = r0
    r0 = 128
    call L01c00f72  ; @call.xl
    pc = [sp++]

; phase3_p3_wdt_clear: 0x020009e6..0x020009ee, module phase3-p3 (wdt_clear)
.type phase3_p3_wdt_clear,@function
phase3_p3_wdt_clear:
    [--sp] = rets
    r0 = 64
    call phase3_p3_wdt_or_con
    pc = [sp++]
