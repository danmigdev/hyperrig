; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; colour_frames: 1 function, 0x02015688..0x0201582c

; colour_frames_switch_colours: 0x02015688..0x0201582c, module colour-frames (switch_colours)
; HyperRig MINI, product option: the light of a scene, of eight.
.type colour_frames_switch_colours,@function
colour_frames_switch_colours:
    [--sp] = {rets, r9-r4}
    sp += -4
    r6 = r0
    r7 = r3  #
    r0 = b[r6+0] (u)
    r0 += -1
    r4 = r2
    r5 = r1
    if (r0 > 9) goto L020157be
    r8 = L01c26890
    tbb [r0]
switch_colour_cases:
    .byte (L020156de - switch_colour_cases) / 2, (L0201571a - switch_colour_cases) / 2, (L020156ae - switch_colour_cases) / 2, (L020156ae - switch_colour_cases) / 2, (L020156ae - switch_colour_cases) / 2, (L020156ae - switch_colour_cases) / 2, (L0201574a - switch_colour_cases) / 2, (L02015760 - switch_colour_cases) / 2
    .byte (L020157ce - switch_colour_cases) / 2, (L020156c0 - switch_colour_cases) / 2
L020156ae:
    r0 = 160
    b[r5+0] = r0
    b[r5+1] = r0
    b[r5+2] = r0
    r0 = 12
    b[r4+0] = r0
    b[r4+1] = r0
L020156bc:
    b[r4+2] = r0
    goto L020157ea
L020156c0:
    r0 = 255
    b[r5+0] = r0
    r0 = 180
    b[r5+1] = r0
    r0 = 50
    b[r5+2] = r0
    r0 = 5
    b[r4+0] = r0
    r0 = 3
    b[r4+1] = r0
    r0 = 1
    b[r4+2] = r0
    call status_helpers_flags_set
    goto L020157ba
L020156de:
    r0 = sp + 1
    call footswitch_events_colour_word
    if (r0 == 0) goto L020157f0
    r0 = sp + 1
    rep 3 {
    r1 = b[r0++=1] (u)
    b[r5++=1] = r1
    }
    r0 = b[sp+1] (u)
    r0 += 39
    r2 = b[sp+2] (u)
    r3 = 40
    r5 = b[sp+3] (u)
    r1 = r0 / r3 (u)
    r0 = r2 + 39
    r2 = r0 / r3 (u)
    r0 = r5 + 39
    r3 = r0 / r3 (u)
    r0 = r4
    call colour_frames_triplet_set
    goto L02015808
L0201571a:
    r2 = [sp+32]
    r0 = 255
    b[r5+0] = r0
    r0 = 180
    b[r5+1] = r0
    r0 = 50
    b[r5+2] = r0
    r0 = 5
    b[r4+0] = r0
    r0 = 3
    b[r4+1] = r0
    r5 = 1
    b[r4+2] = r5
    r1 = b[r6+1] (u)
    r0 = 2
    if (r1 == r2) goto L020157ec
    r0 = r1
    call preset_storage_available
    if (r0 != 0) goto L02015746
    r5 = r0
L02015746:
    r0 = r5
    goto L020157ec
L0201574a:
    r0 = 140
    b[r5+0] = r0
    r0 = 70
    b[r5+1] = r0
    r0 = 0
    b[r5+2] = r0
    r1 = 6
    b[r4+0] = r1
    r1 = 3
    b[r4+1] = r1
    goto L020156bc
L02015760:
    r0 = r6
    call selection_effect_resolve
    r8 = r0
    ifs (r0 <= -1) goto L020157be
    call preset_application_effect_type  ; @call.xl
; HyperRig MINI, product option: an effect of HyperRig has the light of one of the application.
.if MINI_PRODUCT
    if (r0 <= 39) goto Lhr_light
    call hyperrig_effect_like  ; @call.xl
Lhr_light:
.else
    ifs (r0 >= 40) {  ; @ifs.ge.ri.s12
    r0 = 0
    }
.endif
    r0 = r0 * 0x3
    r1 = L02035810
    r0 += r1  ; @add.rr
    r1 = 10618
    r9 = b[++r0=r1] (u)
    r1 = r9 << 1  #
    r6 = b[r0+2] (u)
    r0 = r5  #
    r7 = b[r0+1] (u)
    r3 = r6 << 1
    r2 = r7 << 1
    call colour_frames_triplet_set
    r0 = 25
    r1 = r9 / r0 (u)
    r3 = r6 / r0 (u)
    r2 = r7 / r0 (u)
    r0 = r4
    call colour_frames_triplet_set
    r0 = r8
    call preset_application_effect_enabled  ; @call.xl
L020157ba:
    r1 = r0
    goto L020157e6
L020157be:
    r0 = 0
    b[r5+0] = r0
    b[r5+1] = r0
    b[r5+2] = r0
    b[r4+0] = r0
    b[r4+1] = r0
    b[r4+2] = r0
    goto L020157ec
L020157ce:
    r0 = 0
    b[r5+0] = r0
    r0 = 200
    b[r5+1] = r0
    r0 = 60
    b[r5+2] = r0
    r0 = 8
    b[r4+0] = r0
    b[r4+1] = r0
    b[r4+2] = r0
    r1 = b[r8+52] (u)
L020157e6:
    r0 = 2
    if (r1 != 0) goto L020157ec
L020157ea:
    r0 = 1
L020157ec:
    sp += 4
    {pc, r9-r4} = [sp++]
L020157f0:
    r0 = 50
    b[r5+0] = r0
    r0 = 190
    b[r5+1] = r0
    r0 = 255
    b[r5+2] = r0
    r0 = 1
    b[r4+0] = r0
    r0 = 4
    b[r4+1] = r0
    r0 = 5
    b[r4+2] = r0
L02015808:
    r1 = b[r6+1] (u)
.if MINI_PRODUCT
    r0 = r1
    call hyperrig_shown_scene  ; @call.xl
    r1 = r0
.endif
    r0 = 2
    if (r1 == r7) goto L020157ec
    r0 = 0
.if MINI_PRODUCT
    if (r1 > 7) goto L020157ec
    r0 = r1 * 0x104
    r1 = hyperrig_scene_base  ; @li.u32
    r0 += r1  ; @add.rr
    r1 = 11936
.else
    if (r1 > 3) goto L020157ec
    r0 = r1 * 0x104
    r0 += r8
    r1 = 11936
.endif
    r1 = b[r0+r1] (u)
    r0 = 1
    if (r1 != 0) goto L020157ec
    r0 = r1
    goto L020157ec
