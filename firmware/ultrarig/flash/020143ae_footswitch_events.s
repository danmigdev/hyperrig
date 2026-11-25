; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; footswitch_events: 2 functions, 0x020143ae..0x0201449a

; footswitch_events_startup_preset: 0x020143ae..0x02014438, module footswitch-events (startup_preset)
.type footswitch_events_startup_preset,@function
footswitch_events_startup_preset:
    [--sp] = {rets, r5, r4}
    sp += -40
    r4 = L01c1f180
    r0 = [r4+100]
    r1 = 740
    r5 = L01c26890
    r2 = 1
    b[r5+r1] = r2
    ifs (r0 <= -1) goto L020143e0
    call preset_storage_available
    if (r0 == 0) goto L020143e0
    r0 = [r4+100]
    call preset_loader_load
    if (r0 == 0) goto L0201441a
L020143e0:
    r4 = 0
    goto L020143f6
L020143e4:
    r0 = r4
    call preset_storage_available
    if (r0 == 0) goto L020143f4
    r0 = r4
    call preset_loader_load
    if (r0 == 0) goto L02014428
L020143f4:
    r4 += 1  ; @add.ri.u5
L020143f6:
    ifs (r4 <= 31) goto L020143e4
    r1 = 1128745812
    r3 = sp + 0
    r0 = 0xDF000
    r2 = 8152
    call preset_application_header
    if (r0 == 0) goto L02014416
    r0 = 0
    call capture_loader_load
L02014416:
    r4 = -1
    goto L02014428
L0201441a:
    r0 = [r4+104]
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    call scene_application_select
    }
    r4 = [r4+100]
L02014428:
    r0 = 740
    r1 = 0
    b[r5+r0] = r1
    r0 = r4
    sp += 40
    {pc, r5, r4} = [sp++]

; footswitch_events_record_id: 0x02014438..0x0201449a, module footswitch-events (record_id)
.type footswitch_events_record_id,@function
footswitch_events_record_id:
    [--sp] = {rets, r6-r4}
    sp += -128
    r4 = r0
    call record_helpers_id_in_use
    r1 = r0
    r0 = 0
    if (r1 != 0) goto L02014496
    r5 = 776
    r6 = L01c26890
    r0 = b[r6+r5] (u)
    if (r0 != 0) goto L02014462
    call mode_and_settings_record_scan
    r0 = 1
    b[r6+r5] = r0
L02014462:
    r0 = sp + 0
    r1 = 0
    call settings_store_global_record
    r0 = r4
    call settings_store_device_word_write
    if (r0 != -9) goto L02014496
    r5 = L01c1f180
    r6 = [r5+224]
    [r5+224] = r4
    r0 = sp + 0
    r1 = 128
    call settings_store_compaction
    r1 = r0
    r0 = 0
    if (r1 == 0) goto L02014496
    [r5+224] = r6
    r0 = r1
L02014496:
    sp += 128
    {pc, r6-r4} = [sp++]
