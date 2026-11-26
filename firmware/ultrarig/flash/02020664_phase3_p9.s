; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p9: 9 functions, 0x02020664..0x02020d7a

; phase3_p9_vm_init: 0x02020664..0x02020950, module phase3-p9 (vm_init)
.type phase3_p9_vm_init,@function
phase3_p9_vm_init:
    [--sp] = {rets, r15-r4}
    sp += -36
    r0 = 0
    r1 = 0
    d[sp+12] = r1_r0
    d[sp+4] = r1_r0
    r2 = sp + 4
    r1 = 206
    call storage_control_ioctl
    r0 = [sp+16]
; HyperRig MINI v4, patch mini_vm_geometry: Change G's VM-size clamp from 64 KiB to MINI's 16 KiB: two 8 KiB banks, no VM migration.
.if TARGET_MINI
    if (r0 >= 16384) {  ; @if.ge.ri.modimm
    r0 = 0x4000  ; @li.modimm
.else
    if (r0 >= 65536) {
    r0 = 0x10000
.endif
    }
    r1 = 623
    r10 = L01c26090
    r3 = b[r10+r1] (u)
    if ((r3 & 0x1) != 0) goto L02020944
    if (r0 < 512) goto L02020944
    r2 = b[sp+4] (u)
    r5 = r2.b0 (u)  #
    r1 = [sp+8]
    r8 = 1
    r4 = 1
    if (r5 != 1) {  ; @if.ne.ri.s12
    r4 = 0
    }
    r2 = r4 << 2
    r7 = r0 >> 14
    r6 = 1
    if (r7 != 0) goto L020206be
    r6 = r7
L020206be:
    r7 = 0
    if ((r6 & r4) == 0) {
    r7 = r2
    }
    r2 = r3 & 0xFFFFFFFB
    r2 |= r7
    r3 = 623
    b[r10+r3] = r2
    if (r5 == 1) {  ; @if.eq.ri.s12
    r8 = 0
    }
    if ((r6 & r4) != 0) goto L02020700
    if (r8 != 0) goto L02020700
    r0 += r1  ; @add.rr
    r1 = r1 + 255
    r4 = r1 & 0xFFFFFF00
    r0 = r0 - r4
    r1 = -512
    r5 = r0 & r1
    if (r5 >= 8192) {
    r5 = 8192
    }
    goto L02020720
L02020700:
    r0 += r1  ; @add.rr
    r1 = r1 + 4095
    r2 = -4096
    r4 = r1 & r2
    r0 = r0 - r4
    r1 = -8192
    r5 = r0 & r1
    if (r5 >= 131072) {
    r5 = 0x20000
    }
L02020720:
    r9 = r10 + 24
    r1 = 0
    r2 = 512
    r0 = r9
    call effect_enable_memset  ; @call.xl
    r0 = r5 >> 1
    [r10+4] = r0
    [r10+0] = r4
    [r10+16] = r0
    r0 += r4  ; @add.rr
    [r10+12] = r0
    r0 = 60
    r4 = r10 + 620
    b[r4+0] = r0
    call phase3_p8_vm_update_recover
    r1 = [r10+0]
    r0 = sp + 24
    r2 = 4
    call L02020116
    r1 = [r10+12]
    r0 = sp + 20
    r2 = 4
    call L02020116
    r5 = r10 + 536
    r0 = r5
    call L0203fb92  ; @call.xl
    r0 = r5
    call L02040614  ; @call.xl
    r0 = b[r4+1] (u)
    r0 += 1  ; @add.ri.u5
    b[r4+1] = r0
    call phase3_p8_norflash_protect_suspend
    r1 = [sp+24]
    r0 = r1 + 1
    [sp] = r5
    if (r0 < 2) goto L020207d6
    r0 = 3723405909
    if (r1 == r0) goto L020207fc
    r2 = r0 + 4386
    if (r1 == r2) goto L020207d6
    r2 = 1437248085
    if (r1 != r2) goto L020207f6
    r4 = 623  #
    r1 = [sp+20]
    r2 = b[r10+r4] (u)
    if (r1 != r0) goto L02020818
    r1 = [r10+12]
    r0 = uextra(r2, p:1, l:1)
    [sp+28] = r0
    r0 = sp + 28
    r2 = 4
    call phase3_p8_sfc_write
    r0 = b[r10+r4] (u)
    r0 |= 2
    goto L0202081c
L020207d6:
    r0 = [sp+20]
    if (r0 == -1) goto L020207f6
    r1 = 1437248085
    if (r0 != r1) goto L020207f6
    r0 = 623
    r1 = b[r10+r0] (u)
    r1 |= 2
    b[r10+r0] = r1
    goto L02020822
L020207f6:
    call L020203fe
    goto L02020822
L020207fc:
    r0 = b[r4+3] (u)
    r1 = [r10+0]
    r0 = uextra(r0, p:1, l:1)
    [sp+28] = r0
    r0 = sp + 28
    r2 = 4
    call phase3_p8_sfc_write
    r0 = b[r4+3] (u)
    r0 &= 4294967293
    b[r4+3] = r0
    goto L02020822
L02020818:
    r0 = r2 & 0xFFFFFFFD
L0202081c:
    r1 = r4
    b[r10+r1] = r0
L02020822:
    r4 = 623
    r0 = b[r10+r4] (u)
    r0 = r0 >> 1
    r5 = 1
    r0 = r5 & ~r0
    r0 = r0 * 0xC
    r0 += r10
    r1_r0 = d[r0+0]
    call L0202046c
    if (r0 != 0) goto L02020856
    r0 = b[r10+r4] (u)
    r0 = r0 >> 1
    r0 = r5 & ~r0
    r0 = r0 * 0xC
    r0 += r10
    call L02020376
L02020856:
    r0 = b[r10+r4] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 = r0 * 0xC
    r0 += r10
    r12 = [r0+0]
    r6 = r12 + 4  #
    r0 = [r0+4]
    r13 = r6 + r0
    r14 = sp + 32
L02020876:
    r0 = sp + 32
    r2 = 4
    r1 = r6
    call L02020116
    r8 = b[r14+2] (u)
    r0 = b[r14+3] (u)
    r15 = b[r14+1] (u)
    r11 = b[sp+32] (u)
    r1 = r8
    r1 <= insert(r0, p:8, l:8)
    r7 = r1 >> 4
    r0 = r7
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L020208e4
    r4 = r6 + 4
    r1 = r4
    r2 = r7
    call L02020116
    r0 = r5
    r1 = r7
    call L02001776
    r10 = r0
    r0 = r5
    call L0203d218  ; @call.xl
    r0 = r10 & 0xFFFF00FF
    if (r11 != r0) goto L020208e4
    r0 = r8 << 8
    r0 = r0 & 0xF00
    r0 = r0 | r15
    r1 = r6 - r12
    r6 = r7 + r4
    r2 = r6 + 4
    h[r9+r0<<1] = r1
    if (r2 < r13) goto L02020876
L020208e4:
    r4 = L01c26090
    [r4+616] = r6
    r0 = 623
    r0 = b[r4+r0] (u)
    r0 = uextra(r0, p:1, l:1)
    r0 = r0 * 0xC
    r1 = [++r0=r4]
    r1 = r1 - r6  #
    r0 = [r0+4]
    r1 += r0  ; @add.rr
    r0 = r6
    call L0202046c
    if (r0 != 0) goto L02020914
    call phase3_p8_vm_defrag
L02020914:
    call L02020616
    r5 = [sp]
    if (r0 == 0) goto L02020920
    call phase3_p8_vm_defrag
L02020920:
    call phase3_p8_norflash_protect_resume
    r4 = r4 + 621
    r0 = b[r4+0] (u)
    r0 += -1
    r0 = r5  #
    b[r4+0] = r0
    call L0204074c  ; @call.xl
    r0 = b[r4+2] (u)
    r1 = r0 | 0x1
    r0 = 0
    b[r4+2] = r1
    sp += 36
    {pc, r15-r4} = [sp++]
L02020944:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L0202094e:
    goto L0202094e

; phase3_p9_vm_check_id: 0x02020950..0x0202095e, module phase3-p9 (vm_check_id)
.type phase3_p9_vm_check_id,@function
phase3_p9_vm_check_id:
    r0 += -1
    r1 = r0.l (u)
    r0 = 1
    if (r1 >= 255) {  ; @if.ge.ri.s12
    r0 = 0
    }
    rts

; phase3_p9_vm_init_check: 0x0202095e..0x02020972, module phase3-p9 (vm_init_check)
.type phase3_p9_vm_init_check,@function
phase3_p9_vm_init_check:
    r0 = 623
    r1 = L01c26090
    r0 = b[r1+r0] (u)
    r0 = r0 & 0xFFFFFF01
    rts

; phase3_p9_vm_check_hdl: 0x02020972..0x0202097e, module phase3-p9 (vm_check_hdl)
.type phase3_p9_vm_check_hdl,@function
phase3_p9_vm_check_hdl:
    r1 = r0
    r0 = 1
    if (r1 >= 256) {  ; @if.ge.ri.s12
    r0 = 0
    }
    rts

; phase3_p9_vm_read: 0x0202097e..0x02020a5a, module phase3-p9 (vm_read)
.type phase3_p9_vm_read,@function
phase3_p9_vm_read:
    [--sp] = {rets, r12-r4}
    sp += -4
    r4 = r2
    r7_r6 = r1_r0
    call phase3_p9_vm_init_check
    if (r0 == 0) goto L02020a46
    r0 = r6
    call phase3_p9_vm_check_hdl
    if (r0 == 0) goto L02020a4c
    if (r4 == 0) goto L02020a52
    r9 = L01c26090
    r8 = r9 + 536
    r0 = r8
    call L02040614  ; @call.xl
    r10 = 621
    r0 = b[r9+r10] (u)
    r0 += 1  ; @add.ri.u5
    b[r9+r10] = r0
    r0 = r6 << 1
    r5 = r0 + r9
    r0 = h[++r5=24] (u)
    r6 = -510
    if (r0 == 0) goto L02020a32
    r11 = 623
    r1 = b[r9+r11] (u)
    r1 = uextra(r1, p:1, l:1)
    r1 = r1 * 0xC
    r1 = [r1+r9]
    r1 += r0  ; @add.rr
    r0 = sp + 0
    r2 = 4
    call L02020116
    r0 = b[r9+r11] (u)
    r1 = b[sp+3] (u)
    r2 = b[sp+2] (u)
    r0 = uextra(r0, p:1, l:1)  #
    r3 = h[r5+0] (u)
    r0 = r0 * 0xC
    r0 = [r0+r9]
    r2 <= insert(r1, p:8, l:24)
    r11 = uextra(r2, p:4, l:12)
    r12 = b[sp] (u)
    r0 += r3  ; @add.rr
    r5 = umin(r11, r4)
    r1 = r0 + 4
    r0 = r7
    r2 = r5
    call L02020116
    r0 = r7
    r1 = r5
    call L02001776
    r0 = r0 & 0xFFFF00FF
    if (r12 != r0) goto L02020a32
    r0 = uextra(r11, p:0, l:16)
    if (r0 <= r4) {
    r4 = r11
    }
    r6 = r4.l (u)
L02020a32:
    r0 = b[r9+r10] (u)
    r0 += -1
    b[r9+r10] = r0
    r0 = r8
    call L0204074c  ; @call.xl
    goto L02020a54
L02020a46:
    r6 = -508
    goto L02020a54
L02020a4c:
    r6 = -512
    goto L02020a54
L02020a52:
    r6 = 0
L02020a54:
    r0 = r6
    sp += 4
    {pc, r12-r4} = [sp++]

; phase3_p9_vm_write: 0x02020a5a..0x02020c50, module phase3-p9 (vm_write)
.type phase3_p9_vm_write,@function
phase3_p9_vm_write:
    [--sp] = {rets, r10-r4}
    sp += -4
    r4 = r2
    r9 = r1
    r6 = r0
    call phase3_p9_vm_init_check
    if (r0 == 0) goto L02020c12
    r0 = r6
    call phase3_p9_vm_check_hdl
    if (r0 == 0) goto L02020c18
    r5 = -511
    if (r4 > 4095) goto L02020c1c
    r10 = L01c26090
    r8 = r10 + 536
    r0 = r8
    call L02040614  ; @call.xl
    r0 = 621
    r1 = b[r10+r0] (u)
    r1 += 1  ; @add.ri.u5
    b[r10+r0] = r1
    call phase3_p9_vm_init_check
    if (r0 == 0) goto L02020aec
    r0 = r8
    call L02040614  ; @call.xl
    r5 = r10 + 621
    r0 = b[r5+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r5+0] = r0
    call phase3_p8_norflash_protect_suspend
    r0 = b[r5+2] (u)
    r0 = r0 >> 1
    r1 = 1
    r0 = r1 & ~r0
    r0 = r0 * 0xC
    r0 += r10
    r1 = h[r0+8] (u)
    if (r1 == 0) goto L02020ad2
    call L02020376
L02020ad2:
    call phase3_p8_norflash_protect_resume
    r0 = 621
    r1 = b[r10+r0] (u)
    r1 += -1
    b[r10+r0] = r1
    r0 = r8
    call L0204074c  ; @call.xl
L02020aec:
    call phase3_p9_vm_init_check
    if (r0 == 0) goto L02020b2e
    r0 = r8
    call L02040614  ; @call.xl
    r5 = 621
    r0 = b[r10+r5] (u)
    r0 += 1  ; @add.ri.u5
    b[r10+r5] = r0
    call phase3_p8_norflash_protect_suspend
    call L02020616
    if (r0 == 1) {  ; @if.eq.ri.s12
    call phase3_p8_vm_defrag
    }
    call phase3_p8_norflash_protect_resume
    r0 = b[r10+r5] (u)
    r0 += -1
    b[r10+r5] = r0
    r0 = r8
    call L0204074c  ; @call.xl
L02020b2e:
    r0 = r4
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L02020b60
    r0 = r6
    r1 = r5
    r2 = r4
    call phase3_p9_vm_read
    r0 = r0.l (u)
    if (r0 != r4) goto L02020b58
    r0 = r5
    r1 = r9
    r2 = r4
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L02020c22
L02020b58:
    r0 = r5
    call L0203d218  ; @call.xl
L02020b60:
    call phase3_p8_norflash_protect_suspend
    r0 = r9
    r1 = r4
    call L02001776
    r1 = 623
    r1 = b[r10+r1] (u)
    b[sp] = r0
    b[sp+1] = r6
    r3 = uextra(r6, p:8, l:4)
    r0 = uextra(r1, p:1, l:1)
    r2 = r0 * 0xC
    r0 = [r2+r10]
    r1 = [r10+616]
    r3 <= insert(r4, p:4, l:16)
    b[sp+2] = r3
    r3 = r4 >> 4
    b[sp+3] = r3
    if (r1 <= r0) goto L02020c44
    r2 += r10
    r3 = r1 - r0  #
    r2 = [r2+4]
    if (r3 >= r2) goto L02020c44
    r0 += r2  ; @add.rr
    r0 = r0 - r1
    r7 = r4 + 4
    r5 = -509
    if (r7 > r0) goto L02020bf6
    r0 = sp + 0
    r2 = 4
    call phase3_p8_sfc_write
    if (r4 == 0) goto L02020bd2
    r0 = [r10+616]
    r1 = r0 + 4
    r0 = r9
    r2 = r4
    call phase3_p8_sfc_write
L02020bd2:
    r0 = r10 + 616
    r5 = r4  #
    r1 = b[r0+7] (u)
    r1 = uextra(r1, p:1, l:1)  #
    r2 = [r0+0]
    r1 = r1 * 0xC
    r1 = [r1+r10]
    r1 = r2 - r1
    r2 = r10 + 24
    h[r2+r6<<1] = r1
    [r0+0] += r7
L02020bf6:
    call phase3_p8_norflash_protect_resume
    r0 = 621
    r1 = b[r10+r0] (u)
    r1 += -1
    b[r10+r0] = r1
    r0 = r8
    call L0204074c  ; @call.xl
    goto L02020c1c
L02020c12:
    r5 = -508
    goto L02020c1c
L02020c18:
    r5 = -512
L02020c1c:
    r0 = r5
    sp += 4
    {pc, r10-r4} = [sp++]
L02020c22:
    r0 = r5
    call L0203d218  ; @call.xl
    r0 = 621
    r1 = b[r10+r0] (u)
    r1 += -1
    b[r10+r0] = r1
    r0 = r8
    call L0204074c  ; @call.xl
    r5 = r4
    goto L02020c1c
L02020c44:
    call L0203e742  ; @call.xl
    call storage_fault_fatal
L02020c4e:
    goto L02020c4e

; HyperRig MINI, product option: nothing refers to what follows
.if MINI_PRODUCT
.else
; phase3_p9_fread: 0x02020c50..0x02020ca6, module phase3-p9 (fread)
.type phase3_p9_fread,@function
phase3_p9_fread:
    [--sp] = {rets, r8-r4}
    r4 = r3
    r7 = r2
    r6 = r1
    r8 = r0
    r5 = -1
    if (r4 == 0) goto L02020ca2
    r0 = [r4+0]
    if (r0 == 0) goto L02020ca2
    r0 += 84
    call L02040614  ; @call.xl
    r1 = [r4+0]
    r2 = b[r1+164] (u)
    if (r2 == 0) goto L02020c96
    r5 = 0
    if (r0 != 0) goto L02020ca2
    r0 = [r1+8]
    r3 = [r0+28]
    if (r3 == 0) goto L02020c8a
    r2 = r7 * r6
    r0 = r4
    r1 = r8
    call r3
    r5 = r0  #
    r1 = [r4+0]
L02020c8a:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    goto L02020ca2
L02020c96:
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    r5 = 0
L02020ca2:
    r0 = r5
    {pc, r8-r4} = [sp++]

; phase3_p9_fputc: 0x02020ca6..0x02020d10, module phase3-p9 (fputc)
.type phase3_p9_fputc,@function
phase3_p9_fputc:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r1  #
    [sp] = r0
    r0 = -1
    if (r4 == 0) goto L02020d0c
    r1 = [r4+0]
    if (r1 == 0) goto L02020d0c
    r0 = r1 + 84
    call L02040614  ; @call.xl
    r1 = r0  #
    r2 = [r4+0]
    r3 = b[r2+164] (u)
    if (r3 == 0) goto L02020cf2
    r0 = 0
    if (r1 != 0) goto L02020d0c
    r0 = [r2+8]
    r3 = [r0+36]
    if (r3 == 0) goto L02020d00
    r1 = sp + 0
    r2 = 1
    r0 = r4
    call r3
    r4 = r0  #
    r1 = [r4+0]
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    if (r4 != 1) goto L02020d0a
    r0 = [sp]
    goto L02020d0c
L02020cf2:
    r0 = r2 + 84
    call L0204074c  ; @call.xl
    r0 = 0
    goto L02020d0c
L02020d00:
    r0 = r2 + 84
    call L0204074c  ; @call.xl
L02020d0a:
    r0 = -1
L02020d0c:
    sp += 4
    {pc, r4} = [sp++]

; phase3_p9_fgetc: 0x02020d10..0x02020d7a, module phase3-p9 (fgetc)
.type phase3_p9_fgetc,@function
phase3_p9_fgetc:
    [--sp] = {rets, r4}
    sp += -4
    r4 = r0
    if (r4 == 0) goto L02020d72
    r0 = [r4+0]
    r1 = 255
    if (r0 == 0) goto L02020d74
    r0 += 84
    call L02040614  ; @call.xl
    r2 = [r4+0]
    r1 = b[r2+164] (u)
    if (r1 == 0) goto L02020d5a
    r1 = 0
    if (r0 != 0) goto L02020d74
    r0 = [r2+8]
    r3 = [r0+28]
    if (r3 == 0) goto L02020d68
    r1 = sp + 3
    r2 = 1
    r0 = r4
    call r3
    r4 = r0  #
    r1 = [r4+0]
    r0 = r1 + 84
    call L0204074c  ; @call.xl
    if (r4 != 1) {  ; @if.ne.ri.s12
    r1 = -1
    } else {
    r1 = b[sp+3] (u)
    }
    goto L02020d74
L02020d5a:
    r0 = r2 + 84
    call L0204074c  ; @call.xl
    r1 = 0
    goto L02020d74
L02020d68:
    r0 = r2 + 84
    call L0204074c  ; @call.xl
L02020d72:
    r1 = 255
L02020d74:
    r0 = r1.b0 (s)
    sp += 4
    {pc, r4} = [sp++]
.endif
