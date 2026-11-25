; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0201eba0..0x0201ec16: vendor code (JieLi SDK or library, not reversed), as instructions
L0201eba0:
    [--sp] = {rets, r9-r4}
    r8 = 341
    r9 = L01c26890
    [r9+r8<<2] = r1
    r6 = r9 + 5468
    r7 = 0
    r5_r4 = 0
    goto L0201ebf2
L0201ebba:
    r3 = r6 + -80
    r0 = r3
    rep 25 {
    [r0++=4] = r7
    }
    r0 = [r9+r8<<2]
    r0 = b[r0+0] (u)
    r0 = r0 & (1 << r4)
    if (r0 == 0) goto L0201ebd8
    r0 = r5.b0 (u)
    call phase3_p4_usb_sie_close
    goto L0201ebe4
L0201ebd8:
    r0 = b[r6+0] (u)
    r0 = r0 & 0xFFFFFFF0
    r0 = r0 | 0x7
    b[r6+0] = r0
L0201ebe4:
    r0 = r3
    call L0203fb92  ; @call.xl
    r5 += 1  ; @add.ri.u5
    r6 += 100
    r4 += 1  ; @add.ri.u5
L0201ebf2:
    if (r4 != 2) goto L0201ebba
    r0 = r8
    r0 = [r9+r0<<2]
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L0201ec12
    r3 = b[r0+6] (u)
    r0 = L0203a1b7  ; "sys_timer"
    r2 = phase3_p6_usb_hotplug_detect
    r1 = 0
    call phase3_p6_sys_timer_add_to_task
L0201ec12:
    r0 = 0
    {pc, r9-r4} = [sp++]
