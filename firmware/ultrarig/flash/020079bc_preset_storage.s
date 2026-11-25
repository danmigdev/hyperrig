; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; preset_storage: 1 function, 0x020079bc..0x020079f6

; preset_storage_record: 0x020079bc..0x020079f6, module preset-storage (record)
.type preset_storage_record,@function
preset_storage_record:
    [--sp] = {rets, r6-r4}
    r4 = r3
    r6 = r0
    call preset_application_header
    if (r0 == 0) goto L020079f2
    r0 = r6 + 40  #
    r5 = [sp+16]
    r1 = r5  #
    r2 = [r4+4]
    call storage_control_read
    r1 = r0
    r0 = -2
    if (r1 != 0) goto L020079f0
    r0 = r5  #
    r1 = [r4+4]
    call preset_storage_checksum
    r1 = r0  #
    r2 = [r4+8]
    r0 = 0
    if (r1 != r2) {
    r0 = -3
    }
L020079f0:
    {pc, r6-r4} = [sp++]
L020079f2:
    r0 = -1
    {pc, r6-r4} = [sp++]
