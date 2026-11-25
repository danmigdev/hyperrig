; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; clock_record_and_usb_link: 4 functions, 0x0200205a..0x020021c0

; clock_record_and_usb_link_usb_note: 0x0200205a..0x0200206a, module clock-record-and-usb-link (usb_note)
.type clock_record_and_usb_link_usb_note,@function
clock_record_and_usb_link_usb_note:
    r0 = 1
    r1 = L01c26f44
    b[r1+1] = r0
    [r1+4] += 1  ; @rmw.add.s12
    rts

; clock_record_and_usb_link_usb_event: 0x0200206a..0x02002186, module clock-record-and-usb-link (usb_event)
.type clock_record_and_usb_link_usb_event,@function
clock_record_and_usb_link_usb_event:
    [--sp] = {rets, r5, r4}
    r1 = b[r0+2] (u)
    r4 = 0
    if (r1 != 3) goto L02002158
    r1 = [r0+8]
    r2 = b[r1+0] (u)
    if (r2 != 115) goto L02002158
    r1 = b[r1+2] (u)
    if (r1 != 48) goto L02002158
    r3 = L01c1f180
    r1 = [r3+24]
    r1 = r1 * 0xA
    r2 = L01c26890
    [r2+100] = r1
    r0 = b[r0+4] (u)
    r4 = 1
    if (r0 == 1) goto L020020de
    if (r0 != 0) goto L02002158
    b[r2+1] = r4
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 2
L020020ae:
    testset b[r0]
    ifeq goto L020020ae
    csync
    r5 = 1440
    r1 = b[r2+r5] (u)
    r0 = [r3+24]
    r0 = r0 * 0xA
    r3 = r0 >> 4
    if (r3 > 374) goto L0200210e
    r3 = r1 ^ 0x1
    if ((r3 & 1) == 0) goto L0200210e
    r1 = r5 + 4
    r3 = b[r2+r1] (u)
    if (r3 == 0) goto L02002126
    csync
    goto L0200214e
L020020de:
    r3 = 0
    b[r2+1] = r3
    b[r2+3] = r3
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 2
L020020ee:
    testset b[r0]
    ifeq goto L020020ee
    csync
    r0 = 1444
    b[r2+r0] = r3
    r0 = r2 + 1716
    b[r0+1] = r3
    [r0+4] += 1  ; @rmw.add.s12
    csync
    b[r2+2] = r3
    goto L02002152
L0200210e:
    b[r2+r5] = r4
    r0 = r5 + 4
    r3 = 0
    b[r2+r0] = r3
    if ((r1 & 1) == 0) goto L0200213a
    call clock_record_and_usb_link_usb_note
    csync
    b[r2+2] = r3
    goto L02002152
L02002126:
    b[r2+r1] = r4
    if (r0 != 0) goto L0200212e
    r0 = 1
L0200212e:
    r1 = 362
    [r2+r1<<2] = r0
    csync
    goto L0200214e
L0200213a:
    r0 = r2 + 1716
    b[r0+1] = r4
    r1 = [r0+4]
    r1 += 1  ; @add.ri.u5
    [r0+4] = r1
    [r0+8] = r1
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L0200215c
    csync
L0200214e:
    r0 = 0
    b[r2+2] = r0
L02002152:
    call storage_coordination_irq_leave  ; @call.xl
L02002158:
    r0 = r4
    {pc, r5, r4} = [sp++]
L0200215c:
    r0 = r2 + 1716
    b[r0+0] = r4
    [r0+12] += 1  ; @rmw.add.s12
    csync
    r0 = 0
    b[r2+2] = r0
    call storage_coordination_irq_leave  ; @call.xl
    r0 = 16
    call phase3_p5_usb_device_mode
    r1 = clock_record_and_usb_link_usb_ready
    r0 = 0
    call phase3_p5_cdc_set_wakeup_handler
    goto L02002158

; clock_record_and_usb_link_usb_ready: 0x02002186..0x020021a2, module clock-record-and-usb-link (usb_ready)
.type clock_record_and_usb_link_usb_ready,@function
clock_record_and_usb_link_usb_ready:
    r0 = L01c26890
    r1 = 1
    b[r0+4] = r1
    r1 = L01c1f180
    r1 = [r1+24]
    r1 = r1 * 0xA
    [r0+100] = r1
    rts

; clock_record_and_usb_link_record_refresh: 0x020021a2..0x020021c0, module clock-record-and-usb-link (record_refresh)
.type clock_record_and_usb_link_record_refresh,@function
clock_record_and_usb_link_record_refresh:
    [--sp] = rets
    r1 = 29883900
    r1 = 1023  #
    r2 = [r1+0]
    r1 &= r2
    r2 = uextra(r2, p:11, l:1)
    call boundary_hooks_record_pack
    call boundary_hooks_record_store
    pc = [sp++]
