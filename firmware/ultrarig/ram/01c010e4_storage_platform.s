; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_platform: 4 functions, 0x01c010e4..0x01c01234

; storage_platform_peer_stop: 0x01c010e4..0x01c01108, module storage-platform (peer_stop)
.type storage_platform_peer_stop,@function
storage_platform_peer_stop:
    r1 = 32432128
    if (r0 == 0) goto L01c010fa
    [r1+4] |= 0x4
    csync
L01c010f2:
    r0 = [r1+4]
    if ((r0 & 16) == 0) goto L01c010f2
    rts
L01c010fa:
    [r1+0] |= 0x4
    csync
L01c01100:
    r0 = [r1+0]
    if ((r0 & 16) == 0) goto L01c01100
    rts

; storage_platform_enter: 0x01c01108..0x01c011c2, module storage-platform (enter)
.type storage_platform_enter,@function
storage_platform_enter:
    [--sp] = {rets, r8-r4}
    r2 = r1
    r3 = r0
    r0 = L01c3748d
    r4 = L01c1fc40
    r6 = L01c1fc48
    r7 = 32432136
    r8 = r7 + 4504  #
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L01c01180
    call storage_coordination_irq_enter
    r0 = L01c1fc44
    goto L01c0113c
L01c0113a:
    csync
L01c0113c:
    r1 = b[r0+0] (u)
    if (r1 == 1) goto L01c0113a
    r1 = 0
    b[r0+0] = r1
    csync
    csync
    [r4+0] = r3
    [r6+0] = r2
    csync
    r2 = cnum
    r1 = 16
    if (r2 == 0) goto L01c0115a
    r1 = 32
L01c0115a:
    [r8+0] = r1
    csync
L01c01160:
    r1 = [r7+0]
    if ((r1 & 16384) == 0) goto L01c01160
    goto L01c0116a
L01c01168:
    csync
L01c0116a:
    r1 = b[r0+0] (u)
    if (r1 == 0) goto L01c01168
    r0 = [r4+0]
    if (r0 != 0) goto L01c011c0
    r1 = cnum
    r0 = 1
    if (r1 == 0) goto L01c0117c
    r0 = 0
L01c0117c:
    call storage_platform_peer_stop
    {pc, r8-r4} = [sp++]
L01c01180:
    csync
L01c01182:
    r0 = [r7+0]
    if ((r0 & 16384) == 0) goto L01c01182
    call storage_coordination_irq_enter
    r0 = L01c1fc4c
    r1 = cnum
    r7 = [r0+r1<<2]
    r5 = r7 + 1
    [r0+r1<<2] = r5
    if (r7 != 0) goto L01c011a4
    lockset
L01c011a4:
    csync
    [r4+0] = r3
    [r6+0] = r2
    csync
    r0 = [r4+0]
    if (r0 == 0) goto L01c011c0
    r1 = cnum
    r0 = 32
    if (r1 == 0) goto L01c011ba
    r0 = 16
L01c011ba:
    [r8+0] = r0
    {pc, r8-r4} = [sp++]
L01c011c0:
    {pc, r8-r4} = [sp++]

; storage_platform_peer_resume: 0x01c011c2..0x01c011da, module storage-platform (peer_resume)
.type storage_platform_peer_resume,@function
storage_platform_peer_resume:
    if (r0 != 0) {  ; @if.ne.ri.s12
    r0 = 32432132
    } else {
    r0 = 32432128
    }
    [r0+0] |= 0x8
    csync
    rts

; storage_platform_leave: 0x01c011da..0x01c01234, module storage-platform (leave)
.type storage_platform_leave,@function
storage_platform_leave:
    [--sp] = rets
    r0 = L01c3748d
    r0 = b[r0+0] (u)
    r1 = L01c1fc40
    if (r0 == 0) goto L01c0120e
    csync
    r0 = L01c1fc44
    r2 = 0
    b[r0+0] = r2
    csync
    r0 = [r1+0]
    if (r0 != 0) goto L01c0120a
    r3 = cnum
    r0 = 1
    if (r3 == 0) goto L01c01208
    r0 = 0
L01c01208:
    call storage_platform_peer_resume
L01c0120a:
    [r1+0] = r2
    goto L01c0122c
L01c0120e:
    [r1+0] = 0x0
    csync
    r0 = L01c1fc4c
    r1 = cnum
    r2 = [r0+r1<<2]
    r2 += -1
    [r0+r1<<2] = r2
    if (r2 != 0) goto L01c0122c
    lockclr
L01c0122c:
    call storage_coordination_irq_leave
    csync
    pc = [sp++]
