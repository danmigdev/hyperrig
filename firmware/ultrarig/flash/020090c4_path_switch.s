; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; path_switch: 1 function, 0x020090c4..0x020091c0

; path_switch_switch_path: 0x020090c4..0x020091c0, module path-switch (switch_path)
.type path_switch_switch_path,@function
path_switch_switch_path:
    [--sp] = {rets, r8-r4}
    r5 = r0
    r0 = 1
    if (r5 != 0) goto L020090ce
    r0 = r5
L020090ce:
    r6 = L01c1f180
    r1 = b[r6+3] (u)
    r4 = 0
    if (r0 == r1) goto L02009196
    if (r5 == 0) goto L02009170
    r0 = b[r6+2] (u)
    r7 = L01c26890
    if (r0 == 0) goto L020090fa
    r0 = 516
    r0 = b[r7+r0] (u)
    if ((r0 & 1) != 0) goto L020090fa
    call preset_band_controls_reserve_fits
    if (r0 == 0) goto L02009194
L020090fa:
    call block_pool_maintain
    r4 += -110
    if (r0 != 0) goto L02009196
    r0 = [r7+416]
    if (r0 != 0) goto L0200916a
    r0 = 500
    r0 = b[r7+r0] (u)
    if (r0 != 0) goto L0200916a
    r0 = [r7+280]
    if (r0 != 2) goto L0200916a
    r8 = [r6+24]
    r0 = 1
    call storage_coordination_gate
    r0 = 0
    call mode_and_settings_mode_service
    r0 = 2
    call mode_and_settings_mode_service
    r4 = r0
    if (r4 == 0) goto L0200919a
    r0 = 29
    r1 = 7
    r2 = r4
    call storage_coordination_notify
    r0 = 1
    call mode_and_settings_mode_service
    r0 = [r6+24]
    [r7+204] = r0
    r0 = 0
    call storage_coordination_gate
    r0 = [r6+24]
    r0 = r0 - r8
    r0 = r0 * 0xA00
    r1 = r4.b0 (u)
    r2 = r0 | r1
    r0 = 29
    r1 = 12
    call storage_coordination_notify
    goto L02009196
L0200916a:
    r0 = [r7+416]
    if (r0 != 0) goto L02009196
L02009170:
    r0 = 1
    if (r5 != 0) goto L02009176
    r0 = r5
L02009176:
    b[r6+3] = r0
    r1 = b[r6+2] (u)
    r4 = 0
    r0 = 0
    if (r1 == 0) goto L02009188
    r1 = b[r6+3] (u)
    r0 = 1
    if (r1 != 0) goto L02009188
    r0 = r1
L02009188:
    call preset_band_controls_set_reserve_mode
    call path_switch_count_request  ; @call.xl
    goto L02009196
L02009194:
    r4 = -4
L02009196:
    r0 = r4
    {pc, r8-r4} = [sp++]
L0200919a:
    r0 = [r6+24]
    [r7+204] = r0
    r0 = 0
    call storage_coordination_gate
    r0 = [r6+24]
    r0 = r0 - r8
    r0 = r0 * 0xA00
    r1 = r4.b0 (u)
    r2 = r0 | r1
    r0 = 29
    r1 = 12
    call storage_coordination_notify
    goto L02009170
