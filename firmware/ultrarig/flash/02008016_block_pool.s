; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; block_pool: 5 functions, 0x02008016..0x02008296

; block_pool_maintenance_allowed: 0x02008016..0x02008050, module block-pool (maintenance_allowed)
.type block_pool_maintenance_allowed,@function
block_pool_maintenance_allowed:
    r1 = L01c26890
    r2 = b[r1+20] (u)
    r0 = 0
    if (r2 == 0) goto L0200804e
    r2 = [r1+280]
    if (r2 != 2) goto L0200804c
    r2 = b[r1+21] (u)
    if (r2 == 0) goto L0200804e
    r2 = L01c1f180
    r3 = b[r2+2] (u)
    if (r3 == 0) goto L0200804c
    r2 = b[r2+3] (u)
    if (r2 == 0) goto L0200804c
    r2 = [r1+328]
    if (r2 == 0) goto L0200804e
    r1 = [r1+332]
    if (r1 == 0) goto L0200804e
L0200804c:
    r0 = 1
L0200804e:
    rts

; block_pool_block_ok: 0x02008050..0x02008092, module block-pool (block_ok)
.type block_pool_block_ok,@function
block_pool_block_ok:
    [--sp] = {rets, r4}
    r2 = r0  #
    r3 = [r1+0]
    r0 = 0
    if (r3 < 16) goto L02008090
    if ((r3 & 0xF) != 0) goto L02008090
    {r4, r2} = [r2+]
    r2 += r4  ; @add.rr
    r2 = r2 - r1
    if (r3 > r2) goto L02008090
    r2 = [r1+4]
    r4 = 4042583552
    if (r2 == r4) goto L02008084
    r4 = 4038181086
    if (r2 != r4) goto L02008090
L02008084:
    r2 ^= r3  #
    r1 = [r1+12]
    r0 = 1
    if (r1 != r2) {
    r0 = 0
    }
L02008090:
    {pc, r4} = [sp++]

; block_pool_round_size: 0x02008092..0x020080a0, module block-pool (round_size)
.type block_pool_round_size,@function
block_pool_round_size:
    r1 = r0
    r0 = r1 + 31
    r0 = r0 & 0xFFFFFFF0
    if (r1 != 0) goto L0200809e
    r0 = 32
L0200809e:
    rts

; block_pool_allocate: 0x020080a0..0x02008138, module block-pool (allocate)
.type block_pool_allocate,@function
block_pool_allocate:
    [--sp] = {rets, r11-r4}
    r4 = r0
    r8 = r1  #
    r7 = [r4+0]
    r0 = 0
    if (r7 == 0) goto L0200812e
    r1 = [r4+4]
    if (r1 < r8) goto L0200812e
    r11 = r7 + r1
    r0 = r8
    call block_pool_round_size
    r10 = r0
    r5 = 0
    r9 = 4042583552
    r6 = 0
    goto L020080f0
L020080c8:
    r0 = r4
    r1 = r7
    call block_pool_block_ok
    if (r0 == 0) goto L02008130
    r1_r0 = d[r7+0]
    if (r1 != r9) goto L020080e6
    if (r0 < r10) goto L020080e6
    r1 = r7
    r2 = r0
    if (r5 == 0) goto L020080ea
    if (r0 < r6) goto L020080ea
L020080e6:
    r1 = r5
    r2 = r6
L020080ea:
    r7 += r0  ; @add.rr
    r5 = r1
    r6 = r2
L020080f0:
    if (r7 < r11) goto L020080c8
    if (r5 == 0) goto L02008134
    r0 = r6 - r10
    if (r0 < 32) goto L02008112
    r1 = r5 + r10
    [r1+] = {r9, r0}
    [r1+8] = 0x0
    r0 = r0 ^ r9
    r6 = r10  #
    [r1+12] = r0
L02008112:
    [r5+0] = r6
    r0 = 4038181086
    r0 ^= r6  #
    [r5+4] = r0
    [r5+8] = r8
    [r5+12] = r0
    [r4+8] += r6
    [r4+12] += 1  ; @rmw.add.s12
    r0 = r5 + 16
L0200812e:
    {pc, r11-r4} = [sp++]
L02008130:
    [r4+32] += 1  ; @rmw.add.s12
L02008134:
    r0 = 0
    {pc, r11-r4} = [sp++]

; block_pool_allocate_compacting: 0x02008138..0x02008296, module block-pool (allocate_compacting)
.type block_pool_allocate_compacting,@function
block_pool_allocate_compacting:
    [--sp] = {rets, r15-r4}
    r4 = r1
    r5 = r0
    call block_pool_allocate
    r6 = r0
    if (r6 == 0) goto L02008148
L02008144:
    r0 = r6
    {pc, r15-r4} = [sp++]
L02008148:
    r0 = [r5+0]
    r6 = 0
    if (r0 == 0) goto L02008144
    r0 = [r5+8]
    r1 = [r5+4]
    r2 = r1 - r0
    r0 = r4
    call block_pool_round_size
    if (r2 < r0) goto L02008144
    call block_pool_maintenance_allowed
    r10 = L01c26890
    if (r0 == 0) goto L02008234
    call storage_platform_clock  ; @call.xl
    r8 = r0  #
    r7 = [r5+0]
    if (r7 == 0) goto L02008270
    r13_r12 = 0  #
    r0 = [r5+4]
    r6 = r7 + r0
    r14 = 4042583552
    r15 = r7
    goto L0200822e
L02008184:
    r0 = r5
    r1 = r7
    call block_pool_block_ok
    if (r0 == 0) goto L0200823e
    r0 = [r7+4]
    r11 = [r7+0]
    if (r0 != r14) goto L0200819c
    r7 += r11
    goto L0200822e
L0200819c:
    r9 = r7 + 16
    if (r15 == r7) goto L020081e4
    r10 = r8
    r8 = r13
    r13 = r15 + 16
    r2 = 0
    r0 = r9
    r1 = r13
    call effect_relocation_relocate  ; @call.xl
    if (r0 != 0) goto L020081fc
    r0 = r7 - r15
    [r15+] = {r14, r0}
    r1 = 0
    [r15+8] = r1
    r0 = r0 ^ r14
    [r15+12] = r0
    r7 += r11
    r13 = r8
    r13 = r8 + 1
    r15 = r7
    r8 = r10
    r10 = L01c26890
    goto L0200822e
L020081e4:
    r2 = 0
    r0 = r9
    r1 = r9
    call effect_relocation_relocate  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L020081f6
    r1 = 0
L020081f6:
    r13 += r1
    r7 = r15
    goto L0200822a
L020081fc:
    r0 = r11 >> 2
    r1 = 0
    goto L0200820e
L02008204:
    r2 = [r7+r1<<2]
    [r15+r1<<2] = r2
    r1 += 1  ; @add.ri.u5
L0200820e:
    if (r0 != r1) goto L02008204
    r2 = 1
    r0 = r9
    r1 = r13
    call effect_relocation_relocate  ; @call.xl
    r12 += r11
    r13 = r8
    r8 = r10
    r10 = L01c26890
L0200822a:
    r7 += r11
    r15 += r11
L0200822e:
    if (r7 < r6) goto L02008184
    goto L02008242
L02008234:
    r0 = r10 + 428
    [r0+0] += 1  ; @rmw.add.s12
    goto L02008144
L0200823e:
    [r5+32] += 1  ; @rmw.add.s12
L02008242:
    if (r15 >= r7) goto L0200825a
    r0 = r7 - r15
    [r15+] = {r14, r0}
    [r15+8] = 0x0
    r0 = r0 ^ r14
    [r15+12] = r0
L0200825a:
    [r5+16] += 1  ; @rmw.add.s12
    [r5+20] = r12
    r0 = [r5+24]
    if (r12 > r0) {
    [r5+24] = r12
    }
    [r5+28] = r13
L02008270:
    call storage_platform_clock  ; @call.xl
    r0 = r0 - r8
    [r10+420] = r0
    r1 = [r10+424]
    if (r0 > r1) {
    [r10+424] = r0
    }
    r0 = r5
    r1 = r4
    call block_pool_allocate
    r6 = r0
    goto L02008144
