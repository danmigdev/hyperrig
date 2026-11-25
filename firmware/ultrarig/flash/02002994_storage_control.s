; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_control: 5 functions, 0x02002994..0x02002bd8

; storage_control_range: 0x02002994..0x020029b0, module storage-control (range)
.type storage_control_range,@function
storage_control_range:
    r2 = r0
    r0 = 0
    if (r2 < 782336) goto L020029ae
    if (r1 > 262144) goto L020029ae
    r1 += r2  ; @add.rr
    r0 = 1
    if (r1 > 1044480) {
    r0 = 0
    }
L020029ae:
    rts

; storage_control_reject: 0x020029b0..0x020029be, module storage-control (reject)
.type storage_control_reject,@function
storage_control_reject:
    r1 = L01c26d54
    [r1+0] += 1  ; @rmw.add.s12
    [r1+4] = r0
    rts

; storage_control_control: 0x020029be..0x02002b80, module storage-control (control)
.type storage_control_control,@function
storage_control_control:
    [--sp] = {rets, r9-r4}
    r6 = r1
    r7 = r0
    r9 = L01c26890
    r4 = r9 + 3748
    r0 = r4
    call L02040614  ; @call.xl
    r0 = b[r9+67] (u)
    r0 += 1  ; @add.ri.u5
    b[r9+67] = r0
    r0 = r7 + -200
    r8 = 0
    r5 = L01c3743c
    if (r0 <= 6) goto L02002a28
    r0 = r7 + -100
    if (r0 <= 3) goto L02002a40
    if (r7 == 11) goto L02002ac2
    if (r7 == 13) goto L02002afa
    if (r7 == 47) goto L02002b0c
    if (r7 != 402) goto L02002a62
    r0 = [r5+28]
    if (r0 != 0) goto L02002a20
    call storage_control_identify  ; @call.xl
    r0 = b[r5+28] (u)
    r0 += -16
    call storage_control_power2
    r0 = r0 << 16
    [r5+24] = r0
L02002a20:
    rep 16 {
    r0 = b[r5++=1] (u)
    b[r6++=1] = r0
    }
    goto L02002b5e
L02002a28:
    tbb [r0]
storage_control200:
    .byte (L02002a32 - storage_control200) / 2, (L02002a32 - storage_control200) / 2, (L02002a62 - storage_control200) / 2, (L02002b5e - storage_control200) / 2, (L02002a32 - storage_control200) / 2, (L02002a68 - storage_control200) / 2, (L02002ab6 - storage_control200) / 2
    .byte 0x00  ; alignment
L02002a32:
    r0 = r7
    r1 = r6
    call storage_control_device_erase  ; @call.xl
    r8 = r0
    goto L02002b5e
L02002a40:
    tbb [r0]
storage_control100:
    .byte (L02002a46 - storage_control100) / 2, (L02002b14 - storage_control100) / 2, (L02002b1a - storage_control100) / 2, (L02002b20 - storage_control100) / 2
L02002a46:
    r3 = [r5+28]
    if (r3 != 0) goto L02002a5e
    call storage_control_identify  ; @call.xl
    r3 = [r5+28]
    r0 = r3.b0 (u)
    r0 += -16
    call storage_control_power2
    r0 = r0 << 16
    [r5+24] = r0
L02002a5e:
    [r6+0] = r3
    goto L02002b5e
L02002a62:
    r8 = -25
    goto L02002b5e
L02002a68:
    if (r6 == 0) goto L02002b74  ; @beq.ri
    r0 = r5 + 32
    r1 = r6
    rep 4 {
    r2 = [r1++=4]
    [r0++=4] = r2
    }
    r1_r0 = d[r6+16]
    d[r5+48] = r1_r0
    r0 = [r6+24]
    [r5+20] = r0
    r6 = 262912
    r0 = b[r6+0] (u)
    r0 &= 4294967293
    b[r6+0] = r0
    r3 = [r5+36]
    r0 = r3
    call storage_control_translate  ; @call.xl
    [r6+12] = r0
    r0 = 134217727
    [r6+8] = r0
    r0 = b[r6+0] (u)
    r0 |= 2
    r0 = r3  #
    b[r6+0] = r0
    r1 = 32
    call storage_control_cache_region  ; @call.xl
    goto L02002b5e
L02002ab6:
    r0 = r5 + 32
    rep 16 {
    r1 = b[r0++=1] (u)
    b[r6++=1] = r1
    }
    goto L02002b5e
L02002ac2:
    r0 = 4105
    [r5+64] = r0
    r0 += 80
    if ((r6 & 4) != 0) goto L02002b40
    r0 += 16  ; @add.ri.u5
    if ((r6 & 8) != 0) goto L02002b40
    r0 += -32
    if ((r6 & 16) != 0) goto L02002b40
    r0 += 48
    if ((r6 & 32) != 0) goto L02002b40
    r0 += -96
    if ((r6 & 64) != 0) goto L02002b40
    r0 = r6.b0 (s)
    ifs (r0 < 0) goto L02002b3c
    r0 = 4153
    if ((r6 & 0x100) != 0) {
    r0 += -48
    }
    goto L02002b40
L02002afa:
    r0 = 0x10000
    if (r6 == 0) goto L02002b02
    r0 = r6
L02002b02:
    call storage_control_status_apply  ; @call.xl
    r8 = r0
    goto L02002b5e
L02002b0c:
    if (r6 == 0) goto L02002b5e
    r0 = [r5+68]
    goto L02002b38
L02002b14:
    [r6+0] = 0x100
    goto L02002b5e
L02002b1a:
    [r6+0] = 0x10000
    goto L02002b5e
L02002b20:
    r0 = [r5+24]
    if (r0 != 0) goto L02002b38
    call storage_control_identify  ; @call.xl
    r0 = b[r5+28] (u)
    r0 += -16
    call storage_control_power2
    r0 = r0 << 16
    [r5+24] = r0
L02002b38:
    [r6+0] = r0
    goto L02002b5e
L02002b3c:
    r0 = 4137
L02002b40:
    [r5+64] = r0
    if ((r6 & 2) == 0) goto L02002b5e
    r1 = 4201
    r2 = r0 & r1
    r1 = r0 | 0x10
    if ((r0 & 0x20) == 0) {
    r1 = r2
    }
    [r5+64] = r1
L02002b5e:
    r0 = b[r9+67] (u)
    r0 += -1
    b[r9+67] = r0
    r0 = r4
    call L0204074c  ; @call.xl
    r0 = r8
    {pc, r9-r4} = [sp++]
L02002b74:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02002b7e:
    goto L02002b7e

; storage_control_ioctl: 0x02002b80..0x02002bcc, module storage-control (ioctl)
.type storage_control_ioctl,@function
storage_control_ioctl:
    [--sp] = {rets, r4}
    r4 = r1
    r0 = r4 + -200
    r3 = r2
    if (r0 > 4) goto L02002b9c
    tbb [r0]
storage_ioctl200:
    .byte (L02002b96 - storage_ioctl200) / 2, (L02002ba6 - storage_ioctl200) / 2, (L02002bc2 - storage_ioctl200) / 2, (L02002bb8 - storage_ioctl200) / 2, (L02002bac - storage_ioctl200) / 2
    .byte 0x00  ; alignment
L02002b96:
    r1 = 4096
    goto L02002bb0
L02002b9c:
    r0 = r4 + -403
    if (r0 < 2) goto L02002bc2
    goto L02002bb8
L02002ba6:
    r1 = 0x10000
    goto L02002bb0
L02002bac:
    r1 = 256
L02002bb0:
    r0 = r3
    call storage_control_range
    if (r0 == 0) goto L02002bc2
L02002bb8:
    r0 = r4
    r1 = r3
    call storage_control_control
    {pc, r4} = [sp++]
L02002bc2:
    r0 = r3
    call storage_control_reject
    r0 = -1
    {pc, r4} = [sp++]

; storage_control_mode: 0x02002bcc..0x02002bd8, module storage-control (mode)
.type storage_control_mode,@function
storage_control_mode:
    [--sp] = rets
    r0 = 0
    r1 = 13
    r2 = 0
    call storage_control_ioctl
    pc = [sp++]
