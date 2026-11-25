; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; boundary_hooks: 3 functions, 0x0201cca2..0x0201cf5e

; boundary_hooks_att_write: 0x0201cca2..0x0201cd9a, module boundary-hooks (att_write)
.type boundary_hooks_att_write,@function
boundary_hooks_att_write:
    [--sp] = {rets, r9-r4}
    r0 = [sp+32]
    r5 = [sp+28]
    r8 = L01c26890
    if (r1 == 15) goto L0201cce8
    if (r1 == 9) goto L0201ccf6
    if (r1 != 6) goto L0201cd96
    r1 = r8 + 1276
    [r1+20] += r0
    r3 = b[r1+0] (u)
    r2 = 0
    if (r3 != 0) goto L0201ccd4
    goto L0201cd20
L0201ccca:
    r4 = b[r5+r3] (u)
    if (r4 == 10) goto L0201ccda
    r2 += 1  ; @add.ri.u5
L0201ccd4:
    r3 = r2.l (u)
    if (r3 < r0) goto L0201ccca
L0201ccda:
    if (r0 != r3) goto L0201cd12
    r1 = r8 + 1300
    [r1+0] += r0
    goto L0201cd96
L0201cce8:
    if (r0 == 0) goto L0201cd96
    r0 = b[r5+0] (u)
    r0 = r0 & 0xFFFFFF02
    b[r8+63] = r0
    goto L0201cd96
L0201ccf6:
    r0 = b[r5+0] (u)
    call L0204d45a  ; @call.xl
    r0 = b[r5+0] (u)
    r0 = r0 & 0xFFFFFF01
    b[r8+62] = r0
    r0 = r8 + 1260
    [r0+0] += 1  ; @rmw.add.s12
    goto L0201cd96
L0201cd12:
    r4 = [r1+24]
    r3 += r4  ; @add.rr
    r3 += 1  ; @add.ri.u5
    [r1+24] = r3
    r3 = 0
    b[r1+0] = r3
    r2 += 1  ; @add.ri.u5
L0201cd20:
    r1 = 320
    r1 = [r8+r1<<2]
    r3 = 326
    r3 = [r8+r3<<2]
    r4 = 0x400 - r1
    r4 += r3  ; @add.rr
    r6 = r2.l (u)
    r3 = r0 - r6
    r7 = r3 + 1
    if (r7 <= r4) goto L0201cd64
    r0 = 1023
    r0 &= r1
    r0 += r8
    r2 = 10912
    r4 = 0
    b[r0+r2] = r4
    r0 = r1 + 1
    r1 = r8 + 1276
    [r1+4] = r0
    [r1+24] += r3
    r0 = 1
    b[r1+0] = r0
    goto L0201cd96
L0201cd64:
    r3 = r5 + r6
    r9 = 1023
    r6 = 10912
    goto L0201cd88
L0201cd70:
    r5 = r1 & r9  #
    r4 = b[r3++=1] (u)
    r7 = r5 + r8
    r5 = 32
    if (r4 == 0) goto L0201cd80
    r5 = r4
L0201cd80:
    b[r7+r6] = r5
    r1 += 1  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L0201cd88:
    r4 = r2.l (u)
    if (r4 < r0) goto L0201cd70
    r0 = 320
    [r8+r0<<2] = r1
L0201cd96:
    r0 = 0
    {pc, r9-r4} = [sp++]

; boundary_hooks_packet_handler: 0x0201cd9a..0x0201cef2, module boundary-hooks (packet_handler)
.type boundary_hooks_packet_handler,@function
boundary_hooks_packet_handler:
    [--sp] = {rets, r7-r4}
    sp += -8
    r3 = r2
    if (r0 != 4) goto L0201ceee
    r0 = b[r3+0] (u)
    r4 = L01c26890
    if (r0 == 5) goto L0201cdd6
    if (r0 == 8) goto L0201ce0e
    if (r0 == 48) goto L0201ce46
    if (r0 == 181) goto L0201ce6e
    if (r0 != 62) goto L0201ceee
    r0 = b[r3+2] (u)
    if (r0 == 1) goto L0201ce90
    if (r0 != 10) goto L0201ceee
    r0 = b[r3+3] (u)
    if (r0 != 0) goto L0201ceee
    call boundary_hooks_activity_note
    goto L0201ce98
L0201cdd6:
    r5 = 0
    r0 = r4 + 56
    h[r0+26] = r5
    b[r0+6] = r5
    b[r0+3] = r5
    r0 = 1276  #
    h[r0+28] = r5
    b[r4+r0] = r5
    r0 = r4 + 1260
    r1 = [r0+20]
    [r0+24] = r1
    [r0+0] += 1  ; @rmw.add.s12
    r3_r2 = 0  #
    [sp+4] = r5
    r0 = 7
    r1 = 4
    [sp] = r5
    call L0204c744  ; @call.xl
    call console_helpers_ble_advertise
    goto L0201ceee
L0201ce0e:
    call boundary_hooks_activity_note
    r0 = h[r4+82] (u)
    if (r0 == 0) goto L0201ceee
    r1 = 3
    r0 = r3
    call L0204cb74  ; @call.xl
    r1 = h[r4+82] (u)
    if (r0 != r1) goto L0201ceee
    r1_r0 = 0  #
    r2 = b[r3+2] (u)
    if (r2 != 0) goto L0201ce38
    r2 = b[r3+5] (u)
    r1 = 1
    if (r2 != 0) goto L0201ce38
    r1 = r2
L0201ce38:
    b[r4+59] = r1
    r1 = 323
    [r4+r1<<2] = r0
    goto L0201ceee
L0201ce46:
    call boundary_hooks_activity_note
    r0 = h[r4+82] (u)
    if (r0 == 0) goto L0201ceee
    r1 = 3
    r0 = r3
    call L0204cb74  ; @call.xl
    r1 = h[r4+82] (u)
    if (r0 != r1) goto L0201ceee
    r0 = b[r3+2] (u)
    if (r0 != 0) goto L0201ceee
    r0 = 1
    b[r4+59] = r0
    goto L0201ceee
L0201ce6e:
    call boundary_hooks_activity_note
    r1 = 4
    r0 = r3
    call L0204cb74  ; @call.xl
    h[r4+84] = r0
    r2 = r0 + -3
    r0 = 8
    r1 = 1
    call L0204c744  ; @call.xl
    goto L0201ceee
L0201ce90:
    r0 = b[r3+3] (u)
    if (r0 != 0) goto L0201ceee
    call boundary_hooks_activity_note
L0201ce98:
    r1 = 4
    r0 = r3
    call L0204cb74  ; @call.xl
    r5 = r4 + 56
    h[r5+26] = r0
    r0 = 23
    h[r5+28] = r0
    r6 = 0
    b[r5+6] = r6
    r0 = 1276  #
    b[r5+3] = r6
    b[r5+7] = r6
    b[r4+r0] = r6
    r4 = r4 + 1260
    r0 = [r4+20]
    [r4+24] = r0
    [r4+28] += 1  ; @rmw.add.s12
    [r4+0] += 1  ; @rmw.add.s12
    r7 = 1459  #
    r2 = h[r5+26] (u)
    r0 = 244
    [sp+4] = r0
    r3 = L01c256dc
    r0 = 7
    r1 = 4
    [sp] = r7
    call L0204c744  ; @call.xl
    [r4+32] = r6
    r0 = 1
    b[r5+8] = r0
L0201ceee:
    sp += 8
    {pc, r7-r4} = [sp++]

; boundary_hooks_ble_task: 0x0201cef2..0x0201cf5e, module boundary-hooks (ble_task)
.type boundary_hooks_ble_task,@function
boundary_hooks_ble_task:
    sp += -8
    r5 = L01c1f180
    r6 = [r5+24]
    r0 = L01c1fa30
    r1 = [r0+0]
    if (r1 != 0) goto L0201cf0a
    [r0+4] = r0
    [r0+0] = r0
L0201cf0a:
    call console_helpers_ble_name
    call L0204ad82  ; @call.xl
    call console_helpers_ble_address
    r4 = sp + 2
    r0 = r4
    call L0204d4fc  ; @call.xl
    r0 = r4
    call L0204a734  ; @call.xl
    call L02041ab0  ; @call.xl
    call L0204d534  ; @call.xl
    r1 = 337  #
    r0 = [r5+24]
    r0 = r0 - r6
    r0 = r0 * 0xA
    r2 = L01c26890
    [r2+r1<<2] = r0
    r0 = 1
    b[r2+65] = r0
L0201cf52:
    r0 = 6000
    call L0203feb8  ; @call.xl
    goto L0201cf52
