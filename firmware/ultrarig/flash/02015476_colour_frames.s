; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; colour_frames: 5 functions, 0x02015476..0x0201565a

; colour_frames_ring_needle: 0x02015476..0x0201553e, module colour-frames (ring_needle)
.type colour_frames_ring_needle,@function
colour_frames_ring_needle:
    [--sp] = {rets, r8-r4}
    sp += -8
    r4 = r2
    r5 = r1
    if (r0 == 0) goto L020154d2
    r0 = r4
    call colour_frames_ring_in_tune
    if (r0 != 0) goto L0201553a
    ifs (r5 <= -500) {
    r5 = -500
    }
    r6 = 0
    goto L020154a0
L02015494:
    r0 = r4 + r6
    r1 = 0
    r3_r2 = 0
    call triplet_helpers_clamp_triplet
    r6 += 3  ; @add.ri.u5
L020154a0:
    if (r6 != 36) goto L02015494
    r0 = r4 + 15
    r1 = 0
    r2 = 14
    r3 = 0
    call triplet_helpers_clamp_triplet
    r0 = r4 + 18
    r1 = 0
    r2 = 14
    r3 = 0
    call triplet_helpers_clamp_triplet
    ifs (r5 >= 500) {  ; @ifs.ge.ri.s12
    r5 = 500
    }
    ifs (r5 < 0) goto L020154da
    r0 = sp + 5
    r1 = 0
    r2 = 70
    r3 = 255
    goto L020154e2
L020154d2:
    r0 = r4
    call colour_frames_ring_idle
    goto L0201553a
L020154da:
    r0 = sp + 5
    r1 = 230
    r2 = 20
    r3 = 0
L020154e2:
    call triplet_helpers_clamp_triplet
    r0 = r5 * 0xB00
    r1 = 1408000
    r0 += r1  ; @add.rr
    r1 = 1000
    r5 = r0 / r1 (u)
    r8 = uextra(r5, p:0, l:8)
    r2 = 0x100 - r8
    r6 = sp + 2
    r1 = sp + 5
    r0 = r6
    call triplet_helpers_scale_triplet
    r7 = r5 >> 8
    r0 = r7 * 0x3
    r0 += r4  ; @add.rr
    r1 = r6
    call triplet_helpers_brighter_triplet
    if ((r5 & 0xFF) == 0) goto L0201553a
    r7 += 1  ; @add.ri.u5
    if (r7 > 11) goto L0201553a
    r6 = sp + 2
    r1 = sp + 5
    r0 = r6
    r2 = r8
    call triplet_helpers_scale_triplet
    r0 = r7 * 0x3
    r0 += r4  ; @add.rr
    r1 = r6
    call triplet_helpers_brighter_triplet
L0201553a:
    sp += 8
    {pc, r8-r4} = [sp++]

; colour_frames_level_colour: 0x0201553e..0x0201556e, module colour-frames (level_colour)
.type colour_frames_level_colour,@function
colour_frames_level_colour:
    [--sp] = {rets, r4}
    r4 = r1
    ifs (r0 > 6) goto L0201554e
    r1 = 0
    r2 = 150
    r3 = 20
    goto L02015566
L0201554e:
    ifs (r0 > 8) goto L02015558
    r1 = 150
    r2 = 140
    goto L02015564
L02015558:
    if (r0 != 9) {  ; @if.ne.ri.s12
    r1 = 255
    r2 = 0
    } else {
    r1 = 220
    r2 = 80
    }
L02015564:
    r3 = 0
L02015566:
    r0 = r4
    call triplet_helpers_clamp_triplet
    {pc, r4} = [sp++]

; colour_frames_meter_ring: 0x0201556e..0x020155e0, module colour-frames (meter_ring)
.type colour_frames_meter_ring,@function
colour_frames_meter_ring:
    [--sp] = {rets, r10-r4}
    sp += -4
    r4 = r1
    r10 = r0
    r0 = 0
    r9 = -1
    r1 = -480
    goto L02015590
L02015582:
    r2 = h[r10+2] (s)
    ifs (r2 >= r1) {
    r9 = r0
    }
    r1 += 40
    r0 += 1  ; @add.ri.u5
L02015590:
    if (r1 != 0) goto L02015582
    r0 = r9 * 0x3
    r8 = r4 + r0
    r7 = 0
    r5 = -480
    goto L020155da
L020155a2:
    r0 = h[r10+0] (s)
    ifs (r0 >= r5) goto L020155c2
    if (r9 != r7) goto L020155ca
    r6 = sp + 1
    r0 = r9
    r1 = r6
    call colour_frames_level_colour
    r2 = 128
    r0 = r8
    r1 = r6
    call triplet_helpers_scale_triplet
    goto L020155d4
L020155c2:
    r0 = r7
    r1 = r4
    call colour_frames_level_colour
    goto L020155d4
L020155ca:
    r1 = 0
    r3_r2 = 0
    r0 = r4
    call triplet_helpers_clamp_triplet
L020155d4:
    r5 += 40
    r4 += 3  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L020155da:
    if (r5 != 0) goto L020155a2
    sp += 4
    {pc, r10-r4} = [sp++]

; colour_frames_bar_fill: 0x020155e0..0x02015652, module colour-frames (bar_fill)
.type colour_frames_bar_fill,@function
colour_frames_bar_fill:
    [--sp] = {rets, r10-r4}
    sp += -8
    r10 = r2
    r9 = r1
    if (r0 < 150) goto L0201564e
    r8 = 768
    if (r0 <= 999) {
    r0 = r0 * 0x300
    r0 = r0 - 0x1C200
    r1 = 850
    r8 = r0 / r1 (u)
    }
    r5 = 0
    r4 = r8
    goto L02015648
L0201560a:
    r2 = 0
    if (r8 <= r5) goto L0201561a
    r2 = r4
    if (r4 >= 256) {  ; @if.ge.ri.s12
    r2 = 256
    }
L0201561a:
    r6 = sp + 5
    r0 = r6
    r1 = r9
    call triplet_helpers_scale_triplet
    r7 = sp + 2
    r2 = 16
    r0 = r7
    call triplet_helpers_scale_triplet
    r1_r0 = r7_r6
    call triplet_helpers_brighter_triplet
    r0 = r10
    rep 3 {
    r1 = b[r6++=1] (u)
    b[r0++=1] = r1
    }
    r5 = r5 + 256
    r4 = r4 + -256
    r10 = r10 + 3
L02015648:
    if (r5 != 768) goto L0201560a
L0201564e:
    sp += 8
    {pc, r10-r4} = [sp++]

; colour_frames_triplet_set: 0x02015652..0x0201565a, module colour-frames (triplet_set)
.type colour_frames_triplet_set,@function
colour_frames_triplet_set:
    b[r0+0] = r1
    b[r0+1] = r2
    b[r0+2] = r3
    rts
