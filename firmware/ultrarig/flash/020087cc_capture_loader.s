; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; capture_loader: 1 function, 0x020087cc..0x02008972

; capture_loader_load: 0x020087cc..0x02008972, module capture-loader (load)
.type capture_loader_load,@function
capture_loader_load:
    [--sp] = {rets, r13-r4}
    sp += -68
    r4 = r0
    r0 = 0
    [sp+24] = r0
    r0 = 6
    call storage_control_activity
    r0 = 1
    call tempo_slot_services_priority_nest
    r0 = 0xDF000
    r1 = r4
    ifs (r4 >= 8) {  ; @ifs.ge.ri.s12
    r0 = 524280
    r1 = r4 + r0
    r0 = 0xCF000
    }
    r1 = r1 << 13
    r0 += r1  ; @add.rr
    r1 = 1128745812
    r3 = sp + 28
    r2 = 8152
    call preset_application_header
    if (r0 == 0) goto L02008858
    r6 = sp + 28
    r2 = sp + 24
    r0 = r4
    r1 = r6
    call preset_application_asset_resolve
    r7 = r0  #
    r5 = [sp+24]
    r3 = 0
    r0 = r4
    r1 = r6
    r2 = r5
    call capture_metadata_lookup
    r6 = r0
    r0 = 0
    call tempo_slot_services_priority_nest
    r10 = L01c1f180
    r0 = b[r10+9] (u)
    r9 = L01c26890
    if (r0 != r4) goto L02008868
    b[r10+9] = r4
    r0 = 255
    b[r10+18] = r0
    if (r7 != 0) goto L020088b6
    r8 = [sp+32]  ; @ld.w.sp.l
    goto L020088a2
L02008858:
    r0 = 0
    call tempo_slot_services_priority_nest
    r5 = -1
L02008860:
    r0 = 20
    r1 = r4
    r2 = r5
    goto L020088c8
L02008868:
    if (r7 == 0) goto L02008880
L0200886a:
    r1 = sp + 28
    r0 = r4
    call capture_loader_signature
    if (r0 == 0) goto L020088d8
    r0 = 20
    r2 = -111
    r5 = r2
    r1 = r4
    goto L020088c8
L02008880:
    r8 = [sp+32]  ; @ld.w.sp.l
    r1 = 0
    r0 = r9 + 1780  #
    [sp] = r1
    r3 = 0
    r1 = r5
    r2 = r8
    call preset_application_asset_matches
    if (r0 == 0) goto L0200886a
    b[r10+9] = r4
    r0 = 255
    b[r10+18] = r0
L020088a2:
    r0 = 1
    r1 = r9 + 1780
    b[r1+0] = r0
    [r1+4] = r5
    [r1+8] = r8
    r0 = 0
    [r1+12] = r0
    b[r1+1] = r0
L020088b6:
    r1 = 0
    r5 = 0
    r0 = r6
    call capture_loader_apply_metadata
    r1 = r4 | 0x500
    r0 = 20
    r2 = 0
L020088c8:
    call storage_coordination_notify
    r0 = 0
    call storage_control_activity
    r0 = r5
    sp += 68
    {pc, r13-r4} = [sp++]
L020088d8:
    r0 = r9 + 696
    {r11, r8} = [r0+]
    r12 = [r0+8]
    r1 = 1
    r13 = 1
    r0 = r6
    call capture_loader_apply_metadata
    r6 = [sp+32]
    r0 = [sp+36]
    [sp+4] = r4
    [sp+8] = r6
    [sp+12] = r0
    [sp+16] = r5
    if (r7 == 0) goto L02008900
    r13 = 0
L02008900:
    b[sp+20] = r13
    r2 = capture_container_read
    r7 = sp + 4
    r0 = 0
    r1 = r6
    r3 = r7
    call capture_container_install
    r5 = r0
    if (r5 == 0) goto L0200893e
    r0 = r9 + 696
    [r0+0] = r8
    [r0+8] = r12
    [r0+4] = r11
    r1 = 1
    r0 = r8
    call capture_loader_set_gain
    r0 = 1780
    r1 = 0
    b[r9+r0] = r1
    goto L02008860
L0200893e:
    r0 = b[r7+16] (u)
    if (r0 == 0) goto L0200895a
    r2 = r9 + 1780  #
    r0 = [r7+12]
    r1 = 1
    b[r2+0] = r1
    [r2+4] = r0
    [r2+8] = r6
    r0 = 0
    [r2+12] = r0
    b[r2+1] = r0
    goto L02008964
L0200895a:
    r0 = 1780
    r1 = 0
    b[r9+r0] = r1
L02008964:
    b[r10+9] = r4
    r0 = 255
    b[r10+18] = r0
    r5 = 0
    goto L02008860
