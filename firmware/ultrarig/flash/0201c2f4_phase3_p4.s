; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p4: 1 function, 0x0201c2f4..0x0201c442

; phase3_p4_usb_g_ep_config: 0x0201c2f4..0x0201c442, module phase3-p4 (usb_g_ep_config)
.type phase3_p4_usb_g_ep_config,@function
phase3_p4_usb_g_ep_config:
    [--sp] = {rets, r9-r4}
    r7 = r3
    r9 = r2
    r6 = r1
    r4 = r0
    r5 = L01c25ce8
    r8 = L01c1fc4c
    if ((r6 & 128) != 0) goto L0201c33a
    r2 = r7
    call sdk_usb_set_dma_raddr
    r0 = [r5+r4<<2]
    if (r0 == 0) goto L0201c324
    r0 += 88
    r0 += -4
    r1 = 64
    [r0+r6<<2] = r1
L0201c324:
    if (r4 == 0) goto L0201c36c
    r0 = r6 << 4
    r1 = 45186
    r2 = 1023
    h[r0+r1<<1] = r2
    csync
    goto L0201c3b0
L0201c33a:
    r6 = r6 & 0xF
    r1 = r6
    r2 = r7
    call sdk_usb_set_dma_taddr
    r0 = [r5+r4<<2]
    if (r0 == 0) goto L0201c356
    r0 += 72
    r0 += -4
    r1 = 64
    [r0+r6<<2] = r1
L0201c356:
    if (r4 == 0) goto L0201c3e0
    r0 = r6 << 4
    r1 = 45184
    r2 = 1023
    h[r0+r1<<1] = r2
    csync
    goto L0201c424
L0201c36c:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0201c384
    lockset
L0201c384:
    csync
    r0 = r6
    call L02005cb8
    r0 = 19
    r1 = 1023
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0201c3aa
    lockclr
L0201c3aa:
    call storage_coordination_irq_leave  ; @call.xl
L0201c3b0:
    r2 = 144
    r0 = r4
    r1 = r6
    call L02005d1c
    r0 = [r5+r4<<2]
    if (r0 == 0) goto L0201c3c8
    r0 += 56
    r0 += -4
    [r0+r6<<2] = r7
L0201c3c8:
    if (r9 == 0) goto L0201c3d6
    r0 = r4
    r1 = r6
    call L02001df6
    {pc, r9-r4} = [sp++]
L0201c3d6:
    r0 = r4
    r1 = r6
    call L02001c58
    {pc, r9-r4} = [sp++]
L0201c3e0:
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r8+r0<<2]
    r2 = r1 + 1
    [r8+r0<<2] = r2
    if (r1 != 0) goto L0201c3f8
    lockset
L0201c3f8:
    csync
    r0 = r6
    call L02005cb8
    r0 = 16
    r1 = 1023
    call L02001ac0
    csync
    r0 = cnum
    r1 = [r8+r0<<2]
    r1 += -1
    [r8+r0<<2] = r1
    if (r1 != 0) goto L0201c41e
    lockclr
L0201c41e:
    call storage_coordination_irq_leave  ; @call.xl
L0201c424:
    r2 = 72
    r0 = r4
    r1 = r6
    call L02006af8
    r0 = r4
    r1 = r6
    if (r9 == 0) goto L0201c43c
    call L02001d7a
    {pc, r9-r4} = [sp++]
L0201c43c:
    call L02001bca
    {pc, r9-r4} = [sp++]
