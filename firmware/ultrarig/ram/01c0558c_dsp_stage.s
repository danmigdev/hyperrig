; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; dsp_stage: 1 function, 0x01c0558c..0x01c055a8

; dsp_stage_capability: 0x01c0558c..0x01c055a8, module dsp-stage (capability)
.type dsp_stage_capability,@function
dsp_stage_capability:
    r0 = b[r0+0] (u)
    r2 = effect_stage_capabilities
    r0 = b[r0+r2] (u)
    r2 = 1
    if (r1 != 0) goto L01c0559e
    r2 = r1
L01c0559e:
    r1 = r2 << 1
    r0 >>= r1
    r0 = r0 & 0x3
    rts
