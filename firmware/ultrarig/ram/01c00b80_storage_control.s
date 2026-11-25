; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; storage_control: 1 function, 0x01c00b80..0x01c00bb2

; storage_control_cache_lines: 0x01c00b80..0x01c00bb2, module storage-control (cache_lines)
.type storage_control_cache_lines,@function
storage_control_cache_lines:
    r2 = 32432136
L01c00b86:
    r3 = [r2+0]
    if ((r3 & 16384) == 0) goto L01c00b86
    r1 += 31  ; @add.ri.u5
    r3 = 32
    r1 = r1 / r3 (s)
    r1 = r1 << 5
    r0 = r0 & 0xFFFFFFE0
    goto L01c00bac
L01c00b9c:
    csync
    flushinv [r0]
    csync
L01c00ba2:
    r3 = [r2+0]
    if ((r3 & 16384) == 0) goto L01c00ba2
    r0 += 32
    r1 += -32
L01c00bac:
    ifs (r1 >= 1) goto L01c00b9c
    rts
