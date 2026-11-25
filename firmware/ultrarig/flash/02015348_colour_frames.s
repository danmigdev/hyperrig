; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; colour_frames: 3 functions, 0x02015348..0x02015458

; colour_frames_ring_idle: 0x02015348..0x0201537a, module colour-frames (ring_idle)
.type colour_frames_ring_idle,@function
colour_frames_ring_idle:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r5 = 0
    goto L0201535c
L02015350:
    r0 = r4 + r5
    r1 = 0
    r3_r2 = 0
    call triplet_helpers_clamp_triplet
    r5 += 3  ; @add.ri.u5
L0201535c:
    if (r5 != 36) goto L02015350
    r0 = r4 + 15
    r1 = 10
    r2 = 10
    r3 = 10
    call triplet_helpers_clamp_triplet
    r0 = r4 + 18
    r1 = 10
    r2 = 10
    r3 = 10
    call triplet_helpers_clamp_triplet
    {pc, r5, r4} = [sp++]

; colour_frames_ring_in_tune: 0x0201537a..0x020153d0, module colour-frames (ring_in_tune)
.type colour_frames_ring_in_tune,@function
colour_frames_ring_in_tune:
    [--sp] = {rets, r5, r4}
    r4 = r0
    r1 += 30  ; @add.ri.u5
    r0 = 0
    if (r1 > 60) goto L020153ce
    r5 = 0
    goto L02015398
L0201538a:
    r0 = r4 + r5
    r1 = 0
    r2 = 18
    r3 = 0
    call triplet_helpers_clamp_triplet
    r5 += 3  ; @add.ri.u5
L02015398:
    if (r5 != 36) goto L0201538a
    r0 = r4 + 12
    r1 = 0
    r2 = 60
    r3 = 0
    call triplet_helpers_clamp_triplet
    r0 = r4 + 21
    r1 = 0
    r2 = 60
    r3 = 0
    call triplet_helpers_clamp_triplet
    r0 = r4 + 15
    r1 = 0
    r2 = 220
    r3 = 30
    call triplet_helpers_clamp_triplet
    r0 = r4 + 18
    r1 = 0
    r2 = 220
    r3 = 30
    call triplet_helpers_clamp_triplet
    r0 = 1
L020153ce:
    {pc, r5, r4} = [sp++]

; colour_frames_ring_strobe: 0x020153d0..0x02015458, module colour-frames (ring_strobe)
.type colour_frames_ring_strobe,@function
colour_frames_ring_strobe:
    [--sp] = {rets, r8-r4}
    sp += -4
    r4 = r3
    r5 = r2
    r6 = r1
    if (r0 == 0) goto L020153f0
    r0 = r4
    call colour_frames_ring_in_tune
    if (r0 != 0) goto L02015454
    ifs (r6 <= -1) goto L020153f6
    r0 = sp + 1
    r1 = 0
    r2 = 70
    r3 = 255
    goto L020153fe
L020153f0:
    r0 = r4
    call colour_frames_ring_idle
    goto L02015454
L020153f6:
    r0 = sp + 1
    r1 = 230
    r2 = 20
    r3 = 0
L020153fe:
    call triplet_helpers_clamp_triplet
    r5 = 0x0 - r5
    r6 = 0
    r7 = 3000
    r8 = 1000
    goto L02015450
L02015412:
    r0 = r5 / r7 (s)
    r0 *= r7
    r0 = r5 - r0
    r0 = r0 + 3000
    r1 = r0 / r7 (s)
    r1 *= r7
    r0 = r0 - r1
    ifs (r0 > 999) goto L02015432
    r1 = 0x3E8 - r0
    goto L0201543c
L02015432:
    r1 = r0 + -2000
    ifs (r0 <= 2000) {  ; @ifs.le.ri.s12
    r1 = 0
    }
L0201543c:
    r0 = r4 + r6
    r1 = r1 << 8
    r2 = r1 / r8 (s)
    r1 = sp + 1
    call triplet_helpers_scale_triplet
    r5 = r5 + 1000
    r6 += 3  ; @add.ri.u5
L02015450:
    if (r6 != 36) goto L02015412
L02015454:
    sp += 4
    {pc, r8-r4} = [sp++]
