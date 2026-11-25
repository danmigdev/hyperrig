; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; cpu_clock: 1 function, 0x020054f0..0x020057c6

; cpu_clock_set_clock_rate: 0x020054f0..0x020057c6, module cpu-clock (set_clock_rate)
.type cpu_clock_set_clock_rate,@function
cpu_clock_set_clock_rate:
    [--sp] = {rets, r15-r4}
    r2 = 680
    r11 = L01c26890
    r2 = b[r11+r2] (u)
    r10 = r0
    r12 = L01c1f180
    [r12+84] = r0
    r4 = 0
    if (r2 == 0) goto L02005518
    r0 = [r12+44]
    if (r0 == r10) goto L02005552
L02005518:
    r0 = 1
    if (r1 != 0) goto L0200551e
    r0 = r1
L0200551e:
    r0 |= r2
    if (r0 != 0) goto L02005528
    r0 = [r11+280]
    if (r0 == 0) goto L0200557e
L02005528:
    r8 = [r11+280]
    if (r8 != 0) {  ; @if.ne.ri.s12
    r0 = 0
    call mode_and_settings_mode_service
    }
    r0 = [r11+280]
    if (r0 == 0) goto L02005556
    r0 = 23
    r1 = -1
    r4 = -1
L02005542:
    r2 = r10
    call storage_coordination_notify
L02005548:
    if (r8 != 0) {  ; @if.ne.ri.s12
    r0 = r8
    call mode_and_settings_mode_service
    }
L02005552:
    r0 = r4
    {pc, r15-r4} = [sp++]
L02005556:
    r0 = 65556
    r1 = [r0+0]
    if ((r1 & 0xF) == 0) goto L0200556e
    r0 = [r0+0]
    r0 = r0 & 0xF
    if (r0 != 6) goto L0200567c
L0200556e:
    r0 = r10 + -300
    if (r0 < 101) goto L0200559a
    r0 = 23
    r1 = -3
    r4 = -3
    goto L02005542
L0200557e:
    [r12+44] = r10
    r0 = 6
    r0 = r10 / r0 (u)
    [r12+68] = r0
    call dsp_audio_path_input  ; @call.xl
    call audio_task_set_input  ; @call.xl
    goto L02005552
L0200559a:
    r0 = r10 * 0x3
    r4 = r0 >> 2
    r0 = 1
    call tempo_slot_services_priority_nest
    if (r10 < 360) goto L020055d4
    r0 = 6
    r1 = 0
    r2 = 3
    r3 = 7
    call storage_fault_masked_register  ; @call.xl
    r0 = 1
    call L0203feb8  ; @call.xl
    r0 = 9
    r1 = 0
    r2 = 4
    r3 = 15
    call storage_fault_masked_register  ; @call.xl
    r0 = 1
    call L0203feb8  ; @call.xl
L020055d4:
    r9 = r4 + -2
    call flash_helpers_move_interrupts
    r13 = 0
    r14 = 1000
    r15 = 0
    goto L020055fa
L020055e6:
    r15 = r15 + 1
    if (r15 >= 2) goto L02005684
    r0 = 23
    r1 = 405
    r2 = r15
    call storage_coordination_notify
L020055fa:
    call flash_helpers_park_request
    call preset_application_rate
    r6 = r0
    r7 = r6 * 0x32
    call storage_platform_clock  ; @call.xl
    r4 = r0
L02005610:
    call ram_callbacks_link_check  ; @call.xl
    r5 = r0
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4
    if (r5 != 0) goto L02005650
    if (r0 < r7) goto L02005610
    r5 = r6 / r14 (u)
    if (r6 <= 999) {
    r5 = 1
    }
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r4
    r2 = r0 / r5 (u)
    r0 = 23
    r1 = 403
    call storage_coordination_notify
    r0 = 2
    call L0203feb8  ; @call.xl
    goto L02005668
L02005650:
    r1 = r6 / r14 (u)
    if (r6 <= 999) {
    r1 = 1
    }
    r2 = r0 / r1 (u)
    r0 = 23
    r1 = 402
    call storage_coordination_notify
L02005668:
    r0 = r9
    call ram_callbacks_pll_set  ; @call.xl
    r4 = r0
    [r11+552] = r13
    if (r4 == -1) goto L020055e6
    goto L02005686
L0200567c:
    r0 = 23
    r1 = -2
    r4 = -2
    goto L02005542
L02005684:
    r4 = -1
L02005686:
    call preset_application_rate
    r9 = r0
    r5 = r0 * 0x14
    call storage_platform_clock  ; @call.xl
    r7 = r0
L02005698:
    r0 = b[r11+30] (u)
    if (r0 != 0) goto L020056aa
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r7
    if (r0 < r5) goto L02005698
L020056aa:
    r5 = b[r11+30] (u)
    call storage_platform_clock  ; @call.xl
    r6 = r0
    if (r5 == 0) goto L020056d8
    r5 = 500
    if (r9 >= 1000) {  ; @if.ge.ri.s12
    r0 = r14
    r0 = r9 / r0 (u)
    r5 = r0 * 0x1F4
    }
L020056ca:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r6
    if (r0 < r5) goto L020056ca
    goto L020056f4
L020056d8:
    r0 = r14
    r0 = r9 / r0 (u)
    if (r9 <= 999) {
    r0 = 1
    }
    r1 = r6 - r7
    r2 = r1 / r0 (u)
    r0 = 23
    r1 = 404
    call storage_coordination_notify
L020056f4:
    r0 = 0
    call tempo_slot_services_priority_nest
    if (r4 == -1) goto L020057be
    r0 = 72108
    r2 = [r0+0]
    call storage_coordination_irq_enter  ; @call.xl
    r0 = L01c1fa24
    r1 = cnum
    r3 = [r0+r1<<2]
    r4 = r3 + 1
    [r0+r1<<2] = r4
    r1 = 4095
    r1 &= r2
    r2 = 40000
    r1 *= r2
    r2 = 80000
    r1 += r2  ; @add.rr
    r2 = 3
    r2 = r1 / r2 (u)
    r1 = L01c1fa20
    if (r3 != 0) goto L0200574e
    csync
L02005746:
    testset b[r1]
    ifeq goto L02005746
    csync
L0200574e:
    r3 = 32436464
    [r3+4] = r2
    r4 = [r3+0]
    if (r4 >= r2) {
    [r3+0] = 0x0
    }
    r2 = cnum
    r3 = [r0+r2<<2]
    r3 += -1
    [r0+r2<<2] = r3
    if (r3 != 0) goto L02005776
    csync
    r0 = 0
    b[r1+0] = r0
L02005776:
    call storage_coordination_irq_leave  ; @call.xl
    [r12+44] = r10
    r0 = 6
    r0 = r10 / r0 (u)
    [r12+68] = r0
    call dsp_audio_path_input  ; @call.xl
    call audio_task_set_input  ; @call.xl
    r0 = 29883900
    r1 = [r0+0]
    r0 = uextra(r1, p:12, l:4)
    r2 = uextra(r1, p:11, l:1)
    r1 = r10
    call boundary_hooks_record_pack
    call boundary_hooks_record_store
    r0 = 680
    r1 = 1
    b[r11+r0] = r1
    r4 = 0
    goto L02005548
L020057be:
    r0 = 23
    r1 = -4
    r4 = -4
    goto L02005542
