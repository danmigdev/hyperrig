; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p8: 1 function, 0x02020450..0x0202046c

; phase3_p8_sdfile_flash_addr2cpu_addr: 0x02020450..0x0202046c, module phase3-p8 (sdfile_flash_addr2cpu_addr)
.type phase3_p8_sdfile_flash_addr2cpu_addr,@function
phase3_p8_sdfile_flash_addr2cpu_addr:
    r1 = 559
    r2 = L01c26890
    r3 = 558
    r3 = [r2+r3<<2]
    r1 = [r2+r1<<2]
    r0 = r0 - r3
    r0 += r1  ; @add.rr
    rts
