; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; ir_reload_and_leaves: 1 function, 0x0200b052..0x0200b0ca

; ir_reload_and_leaves_ir_reload: 0x0200b052..0x0200b0ca, module ir-reload-and-leaves (ir_reload)
.type ir_reload_and_leaves_ir_reload,@function
ir_reload_and_leaves_ir_reload:
    [--sp] = {rets, r7-r4}
    r6 = L01c26890
    r1 = [r6+164]
    r0 = 0
    if (r1 != 0) goto L0200b0c8
    r1 = b[r6+160] (u)
    r1 ^= 1
    if ((r1 & 1) != 0) goto L0200b0c8
    r5 = [r6+152]
    r0 = r5 << 1
    r0 += 2  ; @add.ri.u5
    r0 = r0 & 0xFFFFFFFC
    call L0203c15c  ; @call.xl
    r4 = r0
    if (r4 == 0) goto L0200b0a2
    r0 = L01c3441c
    r7 = [r0+0]
    if (r7 == 0) goto L0200b096
    r1_r0 = d[r6+172]
    r3_r2 = r5_r4
    call r7
    if (r0 == 0) goto L0200b0a8
L0200b096:
    r0 = r4
    call L0203d218  ; @call.xl
    r0 = -1
    {pc, r7-r4} = [sp++]
L0200b0a2:
    r0 = -100
    {pc, r7-r4} = [sp++]
L0200b0a8:
    call audio_pause_pause_audio
    r5 = r6 + 152
    r0 = r4  #
    r3 = [r5+16]
    {r2, r1} = [r5+]
    call ir_installation_configure  ; @call.xl
    call audio_pause_resume_audio
    [r5+12] = r4
    r0 = 0
    [r5+20] = r0
L0200b0c8:
    {pc, r7-r4} = [sp++]
