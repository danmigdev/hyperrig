; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_metadata: 3 functions, 0x02007cba..0x02007e62

; capture_metadata_capacity: 0x02007cba..0x02007ce0, module capture-metadata (capacity)
.type capture_metadata_capacity,@function
capture_metadata_capacity:
    r1 = r0
    r2 = 8152
    r0 = 0
    if (r1 > r2) goto L02007cde
    r2 = r1 + 4135
    r3 = -4096
    r2 &= r3
    r1 += 55
    r1 = r1 & 0xFFFFFFF0
    if (r2 > r1) {
    r0 = r2 - r1
    r0 = r0 >> 4
    }
L02007cde:
    rts

; capture_metadata_scan: 0x02007ce0..0x02007dbe, module capture-metadata (scan)
.type capture_metadata_scan,@function
capture_metadata_scan:
    [--sp] = {rets, r15-r4}
    sp += -276
    r10 = r1  #
    r1 = [r1+12]
    r4 = r3
    r6 = [r10+4]
    r12 = r2  #
    [r4+0] = r1
    [r4+4] = 0xFFFFFFFF
    r9 = r0
    r0 = r6
    call capture_metadata_capacity
    r15 = 0  #
    [r4+12] = r0
    r1 = 0
    r1 = r6 + 55  #
    [r4+8] = r1
    r5 = sp + 4
    r1 = r1 & 0xFFFFFFF0
    [sp] = r1
    r13 = 1413958484
    goto L02007da4
L02007d18:
    r0 = r0 - r15
    r1 = r0 << 4
    r14 = 16
    if (r1 <= 256) {  ; @if.le.ri.s12
    r14 = r0
    }
    r0 = [r9+8]
    r6 = [r9+0]
    r3 = r14 << 4  #
    r2 = [sp]
    r1 = r15 << 4
    r1 += r2  ; @add.rr
    r2 = sp + 20
    call r6
    if (r0 != 0) goto L02007dac
    r6 = sp + 20
    r7 = r14
    r11 = r15
    goto L02007d9c
L02007d4a:
    r0 = sp + 4
    r1 = r6
    r2 = r0 + 8
    rep 8 {
    r3 = b[r1++=1] (u)
    b[r0++=1] = r3
    }
    r0 = r6 + 8
    rep 8 {
    r1 = b[r0++=1] (u)
    b[r2++=1] = r1
    }
    r1 = 16
    r0 = r6
    call capture_metadata_erased
    r11 = r8 + 1
    if (r0 != 0) goto L02007d98
    [r4+8] = r11
    r0 = [sp+4]
    if (r0 != r13) goto L02007d98
    r0 = [r5+4]
    if (r0 == r12) goto L02007d84
    r1 = [r10+8]
    if (r0 != r1) goto L02007d98
L02007d84:
    r0 = sp + 4
    r1 = 12
    call capture_metadata_crc
    r1 = [r5+12]
    if (r0 == r1) {
    r0 = [r5+8]
    [r4+] = {r8, r0}
    }
L02007d98:
    r7 += -1
    r6 += 16  ; @add.ri.u5
L02007d9c:
    r8 = r11
    if (r7 != 0) goto L02007d4a
    r15 += r14  #
    r0 = [r4+12]
L02007da4:
    if (r0 > r15) goto L02007d18
    r0 = 0
    goto L02007dba
L02007dac:
    r0 = [r10+12]
    [r4+0] = r0
    r0 = -1
    [r4+4] = r0
    r1 = [r4+12]
    [r4+8] = r1
L02007dba:
    sp += 276
    {pc, r15-r4} = [sp++]

; capture_metadata_lookup: 0x02007dbe..0x02007e62, module capture-metadata (lookup)
.type capture_metadata_lookup,@function
capture_metadata_lookup:
    [--sp] = {rets, r8-r4}
    sp += -32
    r4 = r2
    r5 = r1
    r6 = r0
    r0 = 0xDF000
    r1 = r6
    ifs (r6 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r6 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  ; @add.rr
    [sp+28] = r0
    r0 = capture_metadata_read_adapter
    [sp+16] = r0
    r0 = capture_journal_write_offset
    [sp+20] = r0
    r0 = sp + 28
    [sp+24] = r0
    r8 = L01c2422c
    if (r6 > 14) goto L02007e2e
    if (r3 != 0) goto L02007e2e
    r1 = r6 * 0x14
    r0 = r1 + r8
    r2 = b[r0+16] (u)
    if (r2 == 0) goto L02007e2e
    r1 = [r1+r8]
    r2 = [r5+8]
    if (r1 != r2) goto L02007e2e
    r1 = [r0+4]
    r2 = [r5+4]
    if (r1 != r2) goto L02007e2e
    r1 = [r0+8]
    if (r1 != r4) goto L02007e2e
    r0 = [r0+12]
    goto L02007e5e
L02007e2e:
    r7 = sp + 0
    if (r3 == 0) goto L02007e34
    r7 = r3
L02007e34:
    r0 = sp + 16
    r1 = r5
    r2 = r4
    r3 = r7
    call capture_metadata_scan
    r0 = [r7+0]
    if (r6 > 14) goto L02007e5e
    r2 = r6 * 0x14  #
    r1 = [r5+8]
    [++r2=r8] = r1
    r1 = [r5+4]
    [r2+4] = r1
    [r2+8] = r4
    [r2+12] = r0
    r1 = 1
    b[r2+16] = r1
L02007e5e:
    sp += 32
    {pc, r8-r4} = [sp++]
