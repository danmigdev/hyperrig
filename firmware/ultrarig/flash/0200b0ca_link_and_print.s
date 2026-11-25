; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; link_and_print: 1 function, 0x0200b0ca..0x0200b10e

; link_and_print_ir_select: 0x0200b0ca..0x0200b10e, module link-and-print (ir_select)
.type link_and_print_ir_select,@function
link_and_print_ir_select:
    [--sp] = {rets, r6-r4}
    r4 = r1
    r5 = r0 + 1
    call ir_installation_pending
    if (r0 != r5) goto L0200b0f0
    if (r4 == 0) goto L0200b0e8
    r0 = L01c26890
    r0 = [r0+744]
    if (r0 == r4) goto L0200b0f0
L0200b0e8:
    call ir_reload_and_leaves_ir_reload
    r6 = -100
    if (r0 != 0) goto L0200b10a
L0200b0f0:
    call audio_pause_pause_audio
    r0 = r5
    r1 = r4
    call ir_block_load_block_load  ; @call.xl
    r6 = -100
    if (r0 != 0) goto L0200b106
    r6 = r0
L0200b106:
    call audio_pause_resume_audio
L0200b10a:
    r0 = r6
    {pc, r6-r4} = [sp++]
