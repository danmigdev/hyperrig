; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_command: 1 function, 0x02007976..0x020079bc

; capture_command_status_text: 0x02007976..0x020079bc, module capture-command (status_text)
; HyperRig MINI, product option: the message for a preset that does not fit.
.type capture_command_status_text,@function
capture_command_status_text:
    r1 = r0
.if MINI_PRODUCT
    r2 = L02035810
    if (r1 == -90) {
    r0 = hyperrig_no_room  ; @li.u32
    rts
    }
.else
    r2 = L02035810
.endif
    if (r1 == -110) goto L020079b4
    if (r1 == -100) {
    r0 = r2 + 2208
    rts
    }
    if (r1 == -3) {
    r0 = r2 + 3498
    rts
    }
    if (r1 != -1) goto L020079a0
    r0 = r2 + 3834
    rts
L020079a0:
    r0 = 8274
    r0 += r2  ; @add.rr
    r2 = r2 + 665
    if (r1 != -111) {
    r0 = r2
    rts
    }
    rts
L020079b4:
    r0 = 8968
    r0 += r2  ; @add.rr
    rts
