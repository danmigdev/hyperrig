; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_loader: 2 functions, 0x0200c9f4..0x0200cb3c

; preset_loader_rebind: 0x0200c9f4..0x0200ca7e, module preset-loader (rebind)
.type preset_loader_rebind,@function
preset_loader_rebind:
    [--sp] = {rets, r6-r4}
    sp += -72
    r4 = L01c1f26c
    r0 = r4 + 2
    r5 = 0
    r1 = 0
    goto L0200ca16
L0200ca06:
    r2 = b[r0+-2] (u)
    if (r2 != 8) goto L0200ca12
    r2 = b[r0+0] (u)
    if (r2 == 255) goto L0200ca1c
L0200ca12:
    r0 += 3  ; @add.ri.u5
    r1 += 1  ; @add.ri.u5
L0200ca16:
    ifs (r1 <= 11) goto L0200ca06
    goto L0200ca78
L0200ca1c:
    r0 = sp + 16
    r1 = sp + 0
    call selection_effect_flatten
    r0 = sp + 36
    r2 = 36
    r1 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r6 = 0
    goto L0200ca62
L0200ca34:
    r0 = sp + 36
    r1 = b[r0+r6] (u)
    if (r1 != 8) goto L0200ca60
    r3 = r0 + r6
    r0 = b[++r3=2] (u)
    if (r0 != 255) goto L0200ca60
    r0 = sp + 36
    r2 = r0 + r6
    r1 = b[++r2=1] (u)
    r0 = b[sp+16] (u)
    if (r1 >= r0) goto L0200ca60
    r0 = sp + 16
    call preset_loader_binding
    r5 += 1  ; @add.ri.u5
L0200ca60:
    r6 += 3  ; @add.ri.u5
L0200ca62:
    if (r6 != 36) goto L0200ca34
    if (r5 == 0) goto L0200ca76
    r1 = sp + 36
    r2 = 36
    r0 = r4
    call effect_parameter_support_memmove  ; @call.xl
    goto L0200ca78
L0200ca76:
    r5 = 0
L0200ca78:
    r0 = r5
    sp += 72
    {pc, r6-r4} = [sp++]

; preset_loader_load: 0x0200ca7e..0x0200cb3c, module preset-loader (load)
.type preset_loader_load,@function
preset_loader_load:
    [--sp] = {rets, r11-r4}
    sp += -84
    r4 = r0
    call storage_platform_clock  ; @call.xl
    r5 = r0
    r1 = sp + 8
    r0 = r4
    call preset_preflight_preflight
    r1 = r0
    r0 = -1
    if (r1 != 0) goto L0200cb38
    call storage_platform_clock  ; @call.xl
    r6 = r0
    call preset_application_rate
    r7 = r0
    call storage_platform_clock  ; @call.xl
    r1 = 1023
    r11 = L01c26890
    r9 = [r11+r1<<2]
    r10 = r0
    r1 = sp + 4
    r2 = sp + 0
    r0 = r4
    call preset_application_apply
    r8 = r0
    r0 = L01c1f180
    [r0+92] = r4
    r0 = sp + 48
    call preset_loader_snapshot
    r0 = 736
    r0 = b[r11+r0] (u)
    r1 = r6 - r5
    r2 = 1000
    r2 = r7 / r2 (u)
    r5 = r1 / r2 (u)
    if (r0 == 0) goto L0200cb14
    r6 = r11 + 4012
    r0 = sp + 48
    r2 = 36
    r1 = r6
    call capture_journal_compare  ; @call.xl
    r7 = r0
    call preset_loader_rebind
    if (r7 != 0) goto L0200cb18
    if (r0 == 0) goto L0200cb18
    r0 = r6
    call preset_loader_snapshot
    goto L0200cb18
L0200cb14:
    call preset_loader_rebind
L0200cb18:
    r1_r0 = r5_r4
    r2 = r10
    r3 = r9
    call preset_loader_report
    r0 = 740
    r0 = b[r11+r0] (u)
    if (r0 != 0) goto L0200cb36
    r0 = 6
    r1 = r4
    r2 = r8
    call storage_coordination_notify
L0200cb36:
    r0 = 0
L0200cb38:
    sp += 84
    {pc, r11-r4} = [sp++]
