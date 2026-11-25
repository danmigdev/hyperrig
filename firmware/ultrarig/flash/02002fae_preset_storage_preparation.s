; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage_preparation: 4 functions, 0x02002fae..0x020031be

; preset_storage_preparation_write_forward: 0x02002fae..0x02002fb4, module preset-storage-preparation (write_forward)
.type preset_storage_preparation_write_forward,@function
preset_storage_preparation_write_forward:
    [--sp] = rets
    call capture_journal_write
    pc = [sp++]

; preset_storage_preparation_ordered_write: 0x02002fb4..0x02002ff6, module preset-storage-preparation (ordered_write)
.type preset_storage_preparation_ordered_write,@function
preset_storage_preparation_ordered_write:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r5 = r0
    if (r2 == 0) goto L02002ff2
    if (r2 < 41) goto L02002fd2
    r0 = r5 + 40
    r1 = r4 + 40
    r2 += -40
    call preset_storage_preparation_write_forward
    r1 = r0
    r0 = -3
    if (r1 != 0) goto L02002ff0
L02002fd2:
    r0 = r5 + 4
    r1 = r4 + 4
    r2 = 36
    call preset_storage_preparation_write_forward
    r1 = r0
    r0 = -3
    if (r1 != 0) goto L02002ff0
    r2 = 4
    r0 = r5
    r1 = r4
    call preset_storage_preparation_write_forward
    r1 = r0
    r0 = -3
    if (r1 != 0) goto L02002ff0
    r0 = r1
L02002ff0:
    {pc, r5, r4} = [sp++]
L02002ff2:
    r0 = 0
    {pc, r5, r4} = [sp++]

; preset_storage_preparation_readback: 0x02002ff6..0x02003040, module preset-storage-preparation (readback)
.type preset_storage_preparation_readback,@function
preset_storage_preparation_readback:
    [--sp] = {rets, r10-r4}
    sp += -128
    r10 = r2
    r8 = r1
    r9 = r0
    r6 = 0
    r5 = r10
L02003004:
    if (r6 >= r10) goto L02003038
    r0 = r9 + r6
    r4 = r5
    if (r5 >= 128) {  ; @if.ge.ri.s12
    r4 = 128
    }
    r1 = sp + 0
    r2 = r4
    call preset_storage_preparation_read_forward
    r7 = 0
    if (r0 != 0) goto L0200303a
    r1 = r8 + r6
    r0 = sp + 0
    r2 = r4
    call capture_journal_compare  ; @call.xl
    r5 += -128
    r6 = r6 + 128
    if (r0 == 0) goto L02003004
    goto L0200303a
L02003038:
    r7 = 1
L0200303a:
    r0 = r7
    sp += 128
    {pc, r10-r4} = [sp++]

; preset_storage_preparation_replace_pair: 0x02003040..0x020031be, module preset-storage-preparation (replace_pair)
.type preset_storage_preparation_replace_pair,@function
preset_storage_preparation_replace_pair:
    [--sp] = {rets, r15-r4}
    sp += -32
    r12 = r2
    r14 = r1
    r15 = r0
    r0 = -1
    if (r15 > 15) goto L020031b6
    if (r2 > 1920) goto L020031b6
    r1 = [sp+84]
    [sp+8] = r1
    if (r1 > 1920) goto L020031b6
    r8 = 3496  #
    [sp+4] = r3
    r0 = sp + 24
    r13 = 18  #
    [sp+12] = r0
    r7 = L01c26890
    r9 = 3440
    r10 = 0
L0200307a:
    ifs (r10 > 1) goto L020031ba
    r0 = b[r7+r8] (u)
    r0 += 1  ; @add.ri.u5
    r1 = 0
L02003086:
    if (r1 >= 18) goto L020030a4
    r2 = r0 + r1
    r3 = r2 / r13 (u)
    r3 = r3 * 0x12
    r5 = r2 - r3
    r2 = r5 + r7
    r2 = b[r2+r9] (u)
    r1 += 1  ; @add.ri.u5
    if (r2 != 1) goto L02003086
    goto L020030dc
L020030a4:
    r4 = 1
    goto L020030aa
L020030a8:
    r4 += 1  ; @add.ri.u5
L020030aa:
    r0 = r4 + -1
    if (r0 > 17) goto L020031b4
    r0 = b[r7+r8] (u)
    r0 += r4  ; @add.rr
    r1 = r0 / r13 (u)
    r1 = r1 * 0x12
    r5 = r0 - r1
    r0 = r5 + r7
    r0 = b[r0+r9] (u)
    if (r0 != 2) goto L020030a8
    r0 = r7 + 3504
    [r0+0] += 1  ; @rmw.add.s12
    r0 = r5
    call preset_storage_preparation_erase_block
    if (r0 != 0) goto L020030a8
L020030dc:
    r3 = r7 + 3492
    r0 = r5  #
    b[r3+4] = r5
    call preset_storage_block
    r6 = r0  #
    r1 = [r3+0]
    [sp+24] = r15  ; @st.w.sp.l
    r11 = r14  #
    r0 = [sp+12]
    r2 = r12  #
    [r0+4] = r1
    r0 = 1129335636
    [sp+20] = r0
    r0 = r1 + 1
    r0 = r6  #
    [r3+0] = r0
    r1 = r14
    call preset_storage_preparation_ordered_write
    r4 = r6 + 4080
    if (r0 != 0) goto L0200313c
    r14 = r6 + 2048  #
    r1 = [sp+4]
    r0 = r14  #
    r2 = [sp+8]
    call preset_storage_preparation_ordered_write
    if (r0 != 0) goto L0200313c
    r1 = sp + 24
    r2 = 8
    r0 = r4
    call preset_storage_preparation_write_forward
    if (r0 != 0) goto L0200313c
    r0 = r4 + 12
    r1 = sp + 20
    r2 = 4
    [sp] = r0
    call preset_storage_preparation_write_forward
    if (r0 == 0) goto L0200315a
L0200313c:
    r0 = 0
    [sp+16] = r0
    r0 = r4 + 8
    r1 = sp + 16
    r2 = 4
    call preset_storage_preparation_write_forward
    r0 = r5 + r7
    r1 = 2
    b[r0+r9] = r1
    r10 = r10 + 1
    r14 = r11
    goto L0200307a
L0200315a:
    r0 = r6
    r1 = r11
    r2 = r12
    call preset_storage_preparation_readback
    if (r0 == 0) goto L0200313c
    r0 = r14  #
    r1 = [sp+4]
    r2 = [sp+8]
    call preset_storage_preparation_readback
    if (r0 == 0) goto L0200313c
    r1 = sp + 24
    r2 = 8
    r0 = r4
    call preset_storage_preparation_readback
    if (r0 == 0) goto L0200313c
    r1 = sp + 20
    r2 = 4
    r0 = [sp]
    call preset_storage_preparation_readback
    if (r0 == 0) goto L0200313c
    r1 = r15 + r7
    r2 = 3476
    r0 = b[r1+r2] (s)
    b[r1+r2] = r5
    r2 = r5 + r7
    r1 = r9
    r3 = 3
    b[r2+r1] = r3
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r0 += r7  ; @add.rr
    r2 = 2
    b[r0+r1] = r2
    }
    r0 = 0
    goto L020031b6
L020031b4:
    r0 = -1
L020031b6:
    sp += 32
    {pc, r15-r4} = [sp++]
L020031ba:
    r0 = -3
    goto L020031b6
