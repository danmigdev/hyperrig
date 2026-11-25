; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_container: 1 function, 0x02008586..0x020087cc

; capture_container_install: 0x02008586..0x020087cc, module capture-container (install)
.type capture_container_install,@function
capture_container_install:
    [--sp] = {rets, r15-r4}
    sp += -28
    r7 = r3
    r4 = r2
    r5 = r1
    r12 = r0
    r0 = r5 + -1
    r0 = r0 >> 13
    r6 = -1
    if (r0 != 0) goto L0200874c
    r13 = L01c26890
    r15 = embedded_A2_capture
    if (r4 != 0) goto L020085ba
    r11 = 0
    if (r12 == r15) goto L020085ca
    r0 = [r13+676]
    if (r0 == r12) goto L020085ca
L020085ba:
    r0 = r5 + 3
    r0 = r0 & 0xFFFFFFFC
    call L0203c15c  ; @call.xl
    r11 = r0
    if (r0 == 0) goto L02008698
L020085ca:
    r8 = [r13+280]
    r0 = L01c1f180
    r14 = [r0+24]
    r0 = 29
    r1 = 1
    r2 = r5
    call storage_coordination_notify
    r0 = 7
    call storage_control_activity
    r0 = 1
    call storage_coordination_gate
    r0 = 0
    call mode_and_settings_mode_service
    call L02040850  ; @call.xl
    r9 = r0
    if (r0 <= 26) {  ; @if.le.ri.s12
    r0 = 27
    call L020408d6  ; @call.xl
    }
    r0 = 0
    r10 = 0
    call storage_control_activity
    if (r4 == 0) goto L0200861e
    r0 = r11
    r1 = r7
    call r4
    r6 = r0
    r12 = r11
    if (r6 != 0) goto L020086a4
L0200861e:
    if (r5 < 4) goto L0200867c
    if (r12 == 0) goto L0200867c
    r0 = b[r12+0] (u)
    if (r0 != 65) goto L02008646
    r1 = b[r12+1] (u)
    if (r1 != 50) goto L02008646
    r1 = b[r12+2] (u)
    if (r1 != 76) goto L02008646
    r1 = b[r12+3] (u)
    if (r1 == 49) goto L0200867c
L02008646:
    r6 = -2
    if (r5 == 6144) goto L020086a4
    if (r5 == 7808) goto L020086a4
    r1 = 1
    if (r0 == 65) {  ; @if.eq.ri.s12
    r1 = 0
    }
    if (r5 < 64) goto L0200867c
    if (r1 != 0) goto L0200867c
    r0 = b[r12+1] (u)
    if (r0 != 77) goto L0200867c
    r0 = b[r12+2] (u)
    r0 += -50
    r0 = r0.b0 (u)
    if (r0 > 2) goto L0200867c
    r0 = b[r12+3] (u)
    if (r0 == 0) goto L0200869e
L0200867c:
    r0 = r12
    r1 = r5
    call capture_dispatch_probe  ; @call.xl
    r10 = r0
    if (r0 == 0) goto L0200869c
    r0 = [r13+416]
    if (r0 == 0) goto L020086a2
    call block_pool_maintain
    r6 = r0
    goto L020086a4
L02008698:
    r6 += -99
    goto L0200874c
L0200869c:
    r6 = -2
L0200869e:
    r10 = 0
    goto L020086a4
L020086a2:
    r6 = 0
L020086a4:
    if (r6 == 0) goto L020086b0
    r0 = r11
    call L0203d218  ; @call.xl
    goto L020086ee
L020086b0:
    r0 = 500
    r1 = 0
    b[r13+r0] = r1
    r0 = r10
    call capture_dispatch_prepare
    r6 = r0
    if (r6 != 0) goto L020086d8
    r0 = [r13+436]
    r1 = r10
    r2 = r12
    r3 = r5
    call capture_dispatch_load  ; @call.xl
    r6 = r0
    if (r6 == 0) goto L02008752
L020086d8:
    r0 = r11
    call L0203d218  ; @call.xl
    call capture_dispatch_cleanup
    r2 = r0
    r0 = 29
    r1 = 3
    call storage_coordination_notify
L020086ee:
    r1 = L01c1f180
L020086f4:
    r0 = [r1+24]
    [r13+204] = r0
    r0 = [r1+24]
    r0 = r0 - r14
    r0 = r0 * 0xA00
    r1 = r6.b0 (u)
    r2 = r0 | r1
    r0 = 29
    r1 = 2
    call storage_coordination_notify
    r0 = 7
    call storage_control_activity
    if (r9 <= 26) {  ; @if.le.ri.s12
    r0 = r9
    call L020408d6  ; @call.xl
    }
    if (r8 == 0) goto L02008740
    r0 = r8
    call mode_and_settings_mode_service
    r2 = r0
    if (r2 == 0) goto L02008740
    r0 = 29
    r1 = 7
    call storage_coordination_notify
    r0 = 1
    call mode_and_settings_mode_service
L02008740:
    r0 = 0
    call storage_coordination_gate
    r0 = 0
    call storage_control_activity
L0200874c:
    r0 = r6
    sp += 28
    {pc, r15-r4} = [sp++]
L02008752:
    r0 = sp + 11
    r1 = sp + 4
    r2 = sp + 0
    call capture_dispatch_capabilities  ; @call.xl
    if (r0 == 0) goto L02008792
    r0 = 500
    r1 = 1
    b[r13+r0] = r1
    if (r11 == 0) goto L02008796
    if (r11 != r12) {
    r0 = r11
    r1 = r12
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    }
    r4 = r13
    r0 = [++r4=676]
    [r4+0] = r11
    call L0203d218  ; @call.xl
    r0 = [r4+0]
    goto L020087ac
L02008792:
    r6 = -3
    goto L020086d8
L02008796:
    r0 = [r13+676]
    if (r12 != r15) goto L020087ac
    if (r0 == 0) goto L020087ac
    call L0203d218  ; @call.xl
    r0 = 0
    [r13+676] = r0
L020087ac:
    r1 = L01c1f180
    if (r12 != r15) {
    r15 = r0
    }
    [r1+60] = r15
    [r1+64] = r5
    r0 = 1030
    [r13+r0<<2] = r10
    r6 = 0
    goto L020086f4
