; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 3 functions, 0x0200c89a..0x0200c996

; footswitch_events_colour_line: 0x0200c89a..0x0200c8ee, module footswitch-events (colour_line)
.type footswitch_events_colour_line,@function
footswitch_events_colour_line:
    [--sp] = {rets, r7-r4}
    sp += -20
    r1 = r0
    r0 = r1 * 0x3
    r2 = L01c26890
    r0 += r2  ; @add.rr
    r0 = r0 + 2424
    r4 = 2423  #
    r3 = b[r0+0] (u)
    r4 = b[r2+r4] (u)
    r5 = b[r0+1] (u)
    r2 = b[r0+2] (u)
    r6 = b[r0+12] (u)
    r7 = b[r0+13] (u)
    r0 = b[r0+14] (u)
    [sp+16] = r0
    d[sp+8] = r7_r6
    r0 = 1
    r6 = r0 << r1  #
    [sp+4] = r2
    r0 = L020359f5  ; "auto"
    r2 = r0 + 443  #
    [sp] = r5
    if ((r4 & r6) == 0) {
    r2 = r0
    }
    r0 = r0 + 6190
    call bond_records_and_prints_print_a
    sp += 20
    {pc, r7-r4} = [sp++]

; footswitch_events_hex_colour: 0x0200c8ee..0x0200c956, module footswitch-events (hex_colour)
.type footswitch_events_hex_colour,@function
footswitch_events_hex_colour:
    [--sp] = {rets, r6-r4}
    r3_r2 = 0
    goto L0200c926
L0200c8f4:
    r4 = b[r0+r3] (s)
    r5 = r4 + -97
    r6 = r5 + 49
    r6 = r6.b0 (u)
    r4 += -87
    if (r6 > 9) goto L0200c90c
    r4 += 39
    goto L0200c91c
L0200c90c:
    r6 = r5.b0 (u)
    if (r6 <= 5) goto L0200c91c
    r5 += 32
    r5 = r5.b0 (u)
    if (r5 > 5) goto L0200c952
    r4 += 32
L0200c91c:
    ifs (r4 < 0) goto L0200c952
    r2 = r2 << 4
    r2 |= r4
    r3 += 1  ; @add.ri.u5
L0200c926:
    ifs (r3 <= 5) goto L0200c8f4
    r3 = b[r0+6] (u)
    r0 = r3 + -10
    if (r0 > 22) goto L0200c940
    r4 = 4194313
    r0 = r4 & (1 << r0)
    if (r0 != 0) goto L0200c944
L0200c940:
    r0 = -1
    if (r3 != 0) goto L0200c950
L0200c944:
    r0 = r2 >> 16
    b[r1+0] = r0
    r0 = r2 >> 8
    b[r1+1] = r0
    b[r1+2] = r2
    r0 = 0
L0200c950:
    {pc, r6-r4} = [sp++]
L0200c952:
    r0 = -1
    {pc, r6-r4} = [sp++]

; footswitch_events_name_index: 0x0200c956..0x0200c996, module footswitch-events (name_index)
.type footswitch_events_name_index,@function
footswitch_events_name_index:
    [--sp] = {rets, r7-r4}
    r6 = r2
    r7 = r1
    r5 = r0
    r4 = 0
    goto L0200c972
L0200c962:
    r1 = [r7+r4<<2]
    r0 = r5
    call L02028308  ; @call.xl
    if (r0 == 0) goto L0200c992
    r4 += 1  ; @add.ri.u5
L0200c972:
    ifs (r4 < r6) goto L0200c962
    r0 = b[r5+0] (s)
    r4 = -1
    ifs (r0 < 48) goto L0200c992
    r1 = r6 + 48
    ifs (r0 >= r1) goto L0200c992
    r1 = b[r5+1] (u)
    r0 += -48
    if (r1 == 0) goto L0200c990
    r0 = -1
L0200c990:
    {pc, r7-r4} = [sp++]
L0200c992:
    r0 = r4
    {pc, r7-r4} = [sp++]
