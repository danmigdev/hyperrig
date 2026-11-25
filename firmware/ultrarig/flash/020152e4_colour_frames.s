; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; colour_frames: 1 function, 0x020152e4..0x02015326

; colour_frames_hue_colour: 0x020152e4..0x02015326, module colour-frames (hue_colour)
.type colour_frames_hue_colour,@function
colour_frames_hue_colour:
    [--sp] = {rets, r5, r4}
    r4 = r1
    r0 = r0.b0 (u)
    r1 = 85
    r1 = r0 / r1 (u)
    r1 = r1 * 0x55
    r1 = r0 - r1
    r5 = r1 * 0x3
    if (r0 > 84) goto L0201530a
    r1 = 0xFF - r5
    r3 = 0
    r0 = r4
    r2 = r5
    goto L02015320
L0201530a:
    r3 = 0xFF - r5
    if (r0 > 169) goto L0201531c
    r1 = 0
    r0 = r4
    r2 = r3
    r3 = r5
    goto L02015320
L0201531c:
    r2 = 0
    r1_r0 = r5_r4
L02015320:
    call triplet_helpers_clamp_triplet
    {pc, r5, r4} = [sp++]
