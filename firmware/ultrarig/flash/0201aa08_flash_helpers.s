; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; flash_helpers: 5 functions, 0x0201aa08..0x0201ab28

; flash_helpers_pool_gap: 0x0201aa08..0x0201aa6a, module flash-helpers (pool_gap)
.type flash_helpers_pool_gap,@function
flash_helpers_pool_gap:
    [--sp] = {rets, r10-r4}
    r4 = r0
    r5 = [r4+0]
    if (r5 == 0) goto L0201aa66
    r8 = 0  #
    r0 = [r4+4]
    r10 = r5 + r0
    r9 = 4038181086
    r7 = r5
    goto L0201aa52
L0201aa22:
    r1_r0 = r5_r4
    call block_pool_block_ok
    if (r0 == 0) goto L0201aa66
    r0 = [r5+4]
    r6 = [r5+0]
    if (r0 != r9) goto L0201aa50
    if (r7 == r5) goto L0201aa44
    r0 = r5 + 16
    r2 = 0
    r1 = r0
    call effect_relocation_relocate  ; @call.xl
    if (r0 == 0) goto L0201aa48
L0201aa44:
    r7 += r6  ; @add.rr
    goto L0201aa50
L0201aa48:
    r0 = r5 - r7
    r7 = r5 + r6
    r8 = umax(r0, r8)
L0201aa50:
    r5 += r6  ; @add.rr
L0201aa52:
    if (r5 < r10) goto L0201aa22
    r0 = r10 - r7
    r1 = umax(r0, r8)
    r0 = r1 + -16
    if (r1 > 16) goto L0201aa68
L0201aa66:
    r0 = 0
L0201aa68:
    {pc, r10-r4} = [sp++]

; flash_helpers_largest_free: 0x0201aa6a..0x0201aac2, module flash-helpers (largest_free)
.type flash_helpers_largest_free,@function
flash_helpers_largest_free:
    [--sp] = {rets, r5, r4}
    r5 = L01c26890
    r0 = r5 + 2452
    call flash_helpers_pool_gap
    r1 = [r5+416]
    r4 = r0
    if (r1 == 0) goto L0201aa88
    r0 = r5 + 2488
    call flash_helpers_pool_gap
    goto L0201aab4
L0201aa88:
    r1 = [r5+436]
    r0 = 0
    if (r1 == 0) goto L0201aab4
    r1 = L01c1f180
    r1 = b[r1+3] (u)
    r2 = b[r5+24] (u)
    r1 |= r2
    if ((r1 & 0xFF) != 0) goto L0201aab4
    r1 = [r5+440]
    if (r1 >= 65) {  ; @if.ge.ri.s12
    r0 = r1 + -31
    r0 = r0 & 0xFFFFFFF0
    }
L0201aab4:
    r4 = umax(r0, r4)
    call console_helpers_heap_largest
    r0 = umax(r0, r4)
    {pc, r5, r4} = [sp++]

; flash_helpers_set_limit: 0x0201aac2..0x0201aace, module flash-helpers (set_limit)
.type flash_helpers_set_limit,@function
flash_helpers_set_limit:
    r1 = L01c26890
    [r1+468] = r0
    rts

; flash_helpers_second_call: 0x0201aace..0x0201aaea, module flash-helpers (second_call)
.type flash_helpers_second_call,@function
flash_helpers_second_call:
    [--sp] = rets
    r2 = L01c26890
    r3 = b[r2+20] (u)
    r2 = r0
    r0 = 0
    if (r3 != 0) goto L0201aae8
    r0 = r2
    call ram_callbacks_post_job  ; @call.xl
L0201aae8:
    pc = [sp++]

; flash_helpers_stall_fatal: 0x0201aaea..0x0201ab28, module flash-helpers (stall_fatal)
.type flash_helpers_stall_fatal,@function
flash_helpers_stall_fatal:
    r3 = r0
    r0 = 1
    if (r1 != 0) goto L0201aaf2
    r0 = r1
L0201aaf2:
    r1 = L01c26890
    r2 = [r1+380]
    r4 = [r1+384]
    r5 = [r1+528]
    r1 = b[r1+26] (u)
    r0 = r0 << 24
    r5 = r5 << 8
    r0 |= r5
    r0 |= r1
    r1 = r2 - r4
    if (r1 >= 255) {  ; @if.ge.ri.s12
    r1 = 255
    }
    r1 = r1 << 16
    r2 = r0 | r1
    r0 = 1
    r1 = r3
    call fault_record_fatal_record
L0201ab26:
    goto L0201ab26
