; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; panel_inputs: 3 functions, 0x02014578..0x020148ba

; panel_inputs_pedal_pair: 0x02014578..0x02014600, module panel-inputs (pedal_pair)
.type panel_inputs_pedal_pair,@function
panel_inputs_pedal_pair:
    [--sp] = {rets, r5, r4}
    sp += -8
    r0 = 0
    [sp+4] = r0
    [sp] = r0
    r5 = 327760
    [r5+4] |= 0x2
    r0 = sp + 0
    call footswitch_events_pedal_read
    [r5+4] &= 0xFFFFFFFD
    [r5+0] |= 0x2
    r4 = r0
    r0 = sp + 4
    call footswitch_events_pedal_read
    [r5+0] &= 0xFFFFFFFD
    if ((r0 & r4) == 0) goto L020145fc
    r2 = 1023  #
    r0 = [sp+4]
    r1 = r0 & r2  #
    r3 = [sp]
    r4 = r2 + 3
    r0 = L01c26890
    h[r0+r4<<1] = r1
    r2 &= r3
    r3 = r4 + 1
    h[r0+r3<<1] = r2
    if (r1 <= r2) goto L020145d6
    r1 = r1 - r2
    if (r1 < 901) goto L020145d6
    r1 = r3 + 3
    r2 = 1
    goto L020145f8
L020145d6:
    r1 = 2060
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L020145fc
    r1 = 2061
    r2 = b[r0+r1] (u)
    r2 += 1  ; @add.ri.u5
    r3 = r2.b0 (u)
    b[r0+r1] = r2
    if (r3 < 2) goto L020145fc
    r1 = r4 + 4
    r2 = 0
L020145f8:
    h[r0+r1<<1] = r2
L020145fc:
    sp += 8
    {pc, r5, r4} = [sp++]

; panel_inputs_pedal_filter: 0x02014600..0x020146ae, module panel-inputs (pedal_filter)
.type panel_inputs_pedal_filter,@function
panel_inputs_pedal_filter:
    [--sp] = {rets, r5, r4}
    r2 = L01c26890
    if (r0 == 0) goto L0201465c
    r3 = 0
    r0 = r2 + 2048
    r3 = 1023  #
    b[r0+11] = r3
    r1 &= r3
    h[r0+0] = r1
    r3 = b[r0+9] (u)
    if (r3 == 0) goto L020146a8
    r0 = 1025
    r3 = h[r2+r0<<1] (u)
    if (r1 < 1016) goto L0201462e
    if (r3 < 1016) goto L02014678
L0201462e:
    r4 = r3 - r1
    r0 = r1 - r3
    if (r1 <= r3) {
    r0 = r4
    }
    r4 = 1
    r5 = 1
    if (r3 <= 7) {  ; @if.le.ri.s12
    r5 = 0
    }
    if (r1 >= 8) {  ; @if.ge.ri.s12
    r4 = 0
    }
    if ((r4 & r5) != 0) goto L02014678
    if (r0 > 6) goto L02014678
    r0 = 2056
    r1 = 0
    b[r2+r0] = r1
    {pc, r5, r4} = [sp++]
L0201465c:
    r0 = 2059
    r1 = b[r2+r0] (u)
    if (r1 != 255) {  ; @if.ne.ri.s12
    r1 += 1  ; @add.ri.u5
    b[r2+r0] = r1
    }
    r0 = r2 + 2064
    [r0+0] += 1  ; @rmw.add.s12
    {pc, r5, r4} = [sp++]
L02014678:
    r0 = 2056
    r3 = b[r2+r0] (u)
    r3 += 1  ; @add.ri.u5
    r4 = r3.b0 (u)
    b[r2+r0] = r3
    if (r4 < 3) goto L020146a6
    r0 = 0
    r3 = r2 + 2050
    b[r3+6] = r0
    h[r3+0] = r1
    r3 = b[r3+8] (u)
    r0 = r1 >> 3
    if (r0 != r3) {
    r1 = 2058
    b[r2+r1] = r0
    }
L020146a6:
    {pc, r5, r4} = [sp++]
L020146a8:
    call panel_inputs_analog_start
    {pc, r5, r4} = [sp++]

; panel_inputs_switch_scan: 0x020146ae..0x020148ba, module panel-inputs (switch_scan)
.type panel_inputs_switch_scan,@function
panel_inputs_switch_scan:
    [--sp] = {rets, r15-r4}
    sp += -12
    r13 = r2
    r3 = 0
    r10 = L01c26890
    r8 = 1
    r7 = L01c1f180
    r4 = 1567
    r6 = 0
    goto L020146e6
L020146ce:
    r2 = r3 + r7
    r2 = b[r2+116] (u)
    r5 = r8 << r3
    r2 += r10
    r2 = b[r2+r4] (u)
    if (r2 == 0) goto L020146e2
    r2 = r5
L020146e2:
    r6 |= r2
    r3 += 1  ; @add.ri.u5
L020146e6:
    if (r3 != 4) goto L020146ce
    r2 = [r10+280]
    r7 = L01c26888
    if (r2 == 0) goto L02014878
    r14 = 30
    if (r1 != 0) goto L02014700
    r14 = r0
L02014700:
    if (r0 <= 30) {  ; @if.le.ri.s12
    r14 = r0
    }
    r15 = 0
    r11 = L01c1f170
    r8 = 1520
    r12 = 1
    r9 = 836
    r1 = 0
    r5 = 0
    goto L0201481c
L02014720:
    r3 = b[r1+r7] (u)
    r0 = r6 & (1 << r1)
    if (r0 == 0) goto L02014772
    if (r3 == 0) goto L0201478e
    r0 = r1 << 1
    r4 = r0 + r10
    r0 = h[r4+r9<<1] (u)
    r0 += r14
    r2 = r0 >> 5
    if (r2 >= 1875) {
    r0 = 60000
    }
    r2 = r3 + -1
    r2 = r2.b0 (u)
    h[r4+r9<<1] = r0
    if (r2 > 1) goto L02014810
    r0 = r0.l (u)
    if (r0 < 1000) goto L02014810
    ifs (r5 > 5) goto L0201476a
    r0 = r5 << 1
    r2 = sp + 0
    r3 = 2
    b[++r2=r0] = r3
    b[r2+1] = r1
    r5 += 1  ; @add.ri.u5
L0201476a:
    r0 = 3
    b[r1+r7] = r0
    goto L02014810
L02014772:
    if (r3 == 0) goto L02014810
    if (r3 == 4) goto L020147ec
    if (r3 != 1) goto L0201480c
    ifs (r5 > 5) goto L0201480c
    r0 = r5 << 1
    r2 = sp + 0
    b[++r2=r0] = r12
    b[r2+1] = r1
    r5 += 1  ; @add.ri.u5
    goto L0201480c
L0201478e:
    r0 = b[r11+0] (s)
    b[r1+r7] = r12
    r3 = r10 + 1672
    h[r3+r1<<1] = r15
    ifs (r0 > -1) goto L02014810
    r2 = r11
    r11 = r1 + -1
    r4 = r1 + 1
    r3 = 0
    goto L020147b0
L020147ae:
    r3 += 1  ; @add.ri.u5
L020147b0:
    ifs (r3 > 1) goto L02014814
    r8 = r4
    if (r3 != 0) goto L020147ba
    r8 = r11
L020147ba:
    if (r8 > 3) goto L020147ae
    r0 = b[r8+r7] (u)
    r0 += -1
    r0 = r0.b0 (u)
    if (r0 > 1) goto L020147ae
    r0 = r1
    if (r3 != 0) goto L020147d0
    r0 = r11
L020147d0:
    r11 = r2  #
    b[r2+0] = r0
    r0 = 4
    b[r8+r7] = r0
    b[r1+r7] = r0
    h[r10+90] = r15
    r8 = 1520
    b[r10+r8] = r15
    goto L02014810
L020147ec:
    r0 = b[r10+r8] (u)
    if (r0 != 0) goto L0201480c
    ifs (r5 > 5) goto L02014808
    r0 = b[r11+0] (u)
    r2 = r5 << 1
    r3 = sp + 0
    r4 = 3
    b[++r3=r2] = r4
    b[r3+1] = r0
    r5 += 1  ; @add.ri.u5
L02014808:
    b[r10+r8] = r12
L0201480c:
    b[r1+r7] = r15
L02014810:
    r1 += 1  ; @add.ri.u5
    goto L0201481c
L02014814:
    r11 = r2
    r8 = 1520
    goto L02014810
L0201481c:
    if (r1 != 4) goto L02014720
    r0 = b[r11+0] (s)
    ifs (r0 <= -1) goto L0201489e
    r1 = r0 + r7
    r2 = b[r1+0] (u)
    r1 = b[r1+1] (u)
    if (r2 != 4) goto L02014894
    if (r1 != 4) goto L0201489e
    r1 = h[r10+90] (u)
    r1 += r14
    r2 = r1 >> 5
    if (r2 >= 1875) {
    r1 = 60000
    }
    h[r10+90] = r1
    if (r1 < 1000) goto L0201489e
    r1 = r8
    r1 = b[r10+r1] (u)
    r1 ^= 1
    if ((r1 & 1) == 0) goto L0201489e
    ifs (r5 > 5) goto L0201486e
    r1 = r5 << 1
    r2 = sp + 0
    r3 = 4
    b[++r2=r1] = r3
    b[r2+1] = r0
    r5 += 1  ; @add.ri.u5
L0201486e:
    r0 = r8
    r1 = 1
    b[r10+r0] = r1
    goto L0201489e
L02014878:
    call panel_inputs_switches_reset
    r0 = 0
    r1 = 3
    goto L0201488e
L02014882:
    r2 = r6 & (1 << r0)
    if (r2 == 0) goto L0201488c
    b[r0+r7] = r1
L0201488c:
    r0 += 1  ; @add.ri.u5
L0201488e:
    if (r0 != 4) goto L02014882
    goto L020148b6
L02014894:
    if (r1 != 4) {  ; @if.ne.ri.s12
    r0 = 255
    b[r11+0] = r0
    }
L0201489e:
    r4 = 0
    r6 = sp + 0
    goto L020148b2
L020148a4:
    r2 = r13  #
    r1 = b[r6+1] (u)
    r0 = b[r6++=2] (u)
    call footswitch_events_switch_event
    r4 += 1  ; @add.ri.u5
L020148b2:
    ifs (r4 < r5) goto L020148a4
L020148b6:
    sp += 12
    {pc, r15-r4} = [sp++]
