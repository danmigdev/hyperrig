; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_stage: 1 function, 0x01c11f66..0x01c11f76

; dsp_stage_ir_delay: 0x01c11f66..0x01c11f76, module dsp-stage (ir_delay)
.type dsp_stage_ir_delay,@function
dsp_stage_ir_delay:
    if (r0 == 0) goto L01c11f72
    r1 = [r0+0]
    r0 = 0
    if (r1 != 0) goto L01c11f70
    r0 = 34
L01c11f70:
    rts
L01c11f72:
    r0 = 0
    rts
