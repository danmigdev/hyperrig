; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; control_scan: 1 function, 0x020158c2..0x020176d8

; control_scan_control_scan: 0x020158c2..0x020176d8, module control-scan (control_scan)
.type control_scan_control_scan,@function
control_scan_control_scan:
    [--sp] = {rets, r15-r4}
    sp += -244
    r0 = 820
    r13 = L01c26890
    r0 = b[r13+r0] (u)
    r14 = L01c1f180
    r15 = L02035810
    if (r0 == 0) goto L0201595a
    r10 = [r14+24]
    r0 = [r13+824]
    r0 = r10 - r0
    r0 = r0 * 0xA
    if (r0 < 10) goto L0201756c
    [sp+36] = r0
    [r13+824] = r10
    r0 = b[r13+74] (u)
    if (r0 != 0) goto L02015a44
    r1 = r14
    r2 = [++r1=88]
    r0 = [r1+4]
    r1 = [r1+32]
    if (r0 == r1) goto L02015934
    [r14+120] = r0
    ifs (r0 < 0) goto L02015924
    call footswitch_events_bank_of
    b[r13+76] = r0
L02015924:
    r0 = 836
    r1 = 1
    b[r13+r0] = r1
    r0 = 0
    b[r13+77] = r0
L02015934:
    r0 = [r14+124]
    if (r2 != r0) {
    [r14+124] = r2
    r0 = 836
    r1 = 1
    b[r13+r0] = r1
    }
    r0 = b[r13+77] (u)
    if (r0 == 0) goto L02015a40
    call slot_commands_requested
    if (r0 != 0) goto L02015a3a
    r4 = 0
    goto L02015a34
L0201595a:
    r0 = 0
    r1 = 480
    r2 = 1
    goto L0201599c
L02015964:
    r3 = r15 + 3520
    r3 = [r3+r0<<2]
    r4 = r0 + r15
    r4 = b[r4+r1] (u)
    [r3+12] |= 1 << r4
    [r3+8] |= 1 << r4
    [r3+20] &= ~(1 << r4)
    [r3+16] |= 1 << r4
    r3 += 4  ; @add.ri.u5
    r5 = r13 + 1964
    [r5+r0<<2] = r3
    r3 = r2 << r4
    r4 = r13 + 1984
    [r4+r0<<2] = r3
    r0 += 1  ; @add.ri.u5
L0201599c:
; HyperRig MINI v4, patch mini_panel_init_three: Limit the same loop to three physical MINI switches; retain branch/register fields.
.if TARGET_MINI
    if (r0 != 3) goto L02015964  ; @bne.ri
.else
    if (r0 != 5) goto L02015964
.endif
    r0 = 1
    b[r13+42] = r0
    r1 = r13 + 820
    b[r1+0] = r0
    r0 = [r14+24]
    r0 = r0 * 0xA  #
    [r1+4] = r0
    r4 = r13 + 2048  #
    [r1+8] = r0
    r0 = r4
    call panel_inputs_analog_reset
; HyperRig MINI v4, patch mini_panel_skip_G_analog_init: Skip G PB1/PC6..8 initialization and initial ADC samples; preserve prior RAM initialization and following epilogue.
.if TARGET_MINI
    goto L020159fc  ; @goto.l
.else
    call panel_inputs_pedal_pins
.endif
    call panel_inputs_pedal_pair
    r5 = 0
    r7 = 4
    r6 = 0
    goto L020159e2
L020159d2:
    r0 = sp + 44
    call footswitch_events_pedal_read
    if (r0 == 0) goto L020159e0
    r0 = [sp+44]
    r5 += r0  ; @add.rr
    r6 += 1  ; @add.ri.u5
L020159e0:
    r7 += -1
L020159e2:
    if (r7 != 0) goto L020159d2
    if (r6 == 0) goto L020159f6
    r0 = r6 >> 1
    r0 += r5  ; @add.rr
    r1 = r0 / r6 (u)
    r0 = r4
    call panel_inputs_analog_start
    goto L020159fc
L020159f6:
    r1_r0 = 0
    call panel_inputs_pedal_filter
L020159fc:
    r0 = 832
; HyperRig MINI v4, patch mini_panel_G_analog_scan_disabled: Keep state+832 zero: gates panel ADC/mux block and CE8E -> CDE0 initialization path. Knobs/expression pending.
.if TARGET_MINI
    r1 = 0  ; @li.u8
.else
    r1 = 1
.endif
    b[r13+r0] = r1
    call panel_inputs_pedal_volume
    goto L0201756c
L02015a0e:
    r1 = sp + 50
    r0 = r4
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r6 = 0
L02015a1c:
    ifs (r6 >= r5) goto L02015a32
    r0 = sp + 50
    r0 = b[r0+r6] (u)
    call preset_application_effect_enabled  ; @call.xl
    r6 += 1  ; @add.ri.u5
    if (r0 == 0) goto L02015a1c
    goto L02015a3a
L02015a32:
    r4 += 1  ; @add.ri.u5
L02015a34:
    ifs (r4 <= 1) goto L02015a0e
    goto L02015a40
L02015a3a:
    r0 = 0
    b[r13+77] = r0
L02015a40:
    call panel_inputs_switch_targets
L02015a44:
    r0 = [r13+816]
    r1 = [r13+840]
    r8 = r10 * 0xA
    [sp+40] = r8  ; @st.w.sp.l
    if (r0 != r1) goto L02015ad6
    r8 = 0
    r12 = 480
    r11 = 1567
    r9 = 1552
    r4 = 0
    goto L02015ad0
L02015a6a:
    r0 = r4 + r15
    r0 = b[r0+r12] (u)
    r5 = 1
    r2 = r5 << r0
    r1 = r15 + 3520
    r1 = [r1+r4<<2]
    r1 = [r1+4]
    if ((r2 & r1) != 0) {
    r5 = 0
    }
    r7 = r4 + r13
    r3 = b[r7+r11] (u)
    r2 = r7 + 1562
    if (r5 == r3) goto L02015aca
    r3 = b[r2+0] (u)
    r3 += 1  ; @add.ri.u5
    r6 = r3.b0 (u)  #
    b[r2+0] = r3
    if (r6 < 4) goto L02015ace
    r6 = r1 & (1 << r0)
    r0 = 0
    b[r2+0] = r0
    call storage_platform_clock  ; @call.xl
    r2 = r0  #
    r3 = [sp+40]
    r1_r0 = r5_r4
; HyperRig MINI, product option: two switches together outside the factory layout (mini/product/pairs.c).
.if MINI_PRODUCT
    call hyperrig_transition  ; @call.xl
.else
    call controls_transition
.endif
    r0 = 1
    if (r6 == 0) goto L02015ac2
    r0 = 0
L02015ac2:
    b[r7+r9] = r0
    r2 = r7 + 1557
L02015aca:
    b[r2+0] = r8
L02015ace:
    r4 += 1  ; @add.ri.u5
L02015ad0:
; HyperRig MINI v4, patch mini_panel_poll_three: Limit the same loop to three physical MINI switches; retain branch/register fields.
.if TARGET_MINI
    if (r4 != 3) goto L02015a6a  ; @bne.ri
.else
    if (r4 != 5) goto L02015a6a
.endif
    goto L02015b50
L02015ad6:
    [r13+840] = r0
    goto L02015b2c
L02015adc:
    r1 = r0 & 0xFFFFFF0F
    r1 = r1 * 0xC
    r1 += r13
    r1 = r1 + 4796
    r4 = b[r1+9] (u)
    r6 = b[r1+8] (u)
    r5 = [r1+0]
    r1 = [r1+4]
    r0 += 1  ; @add.ri.u5
    b[r13+44] = r0
    r0 = [r13+828]
    r7 = r1 * 0xA
    r0 = r7 - r0
    ifs (r0 < 1) goto L02015b12
    r1 = 0
    r2 = r8
    call control_actions_tick
    [r13+828] = r7
L02015b12:
    r0 = r6
    r1 = r4
    r2 = r5
    r3 = r7
; HyperRig MINI, product option: two switches together outside the factory layout (mini/product/pairs.c).
.if MINI_PRODUCT
    call hyperrig_transition  ; @call.xl
.else
    call controls_transition
.endif
    r0 = b[r13+74] (u)
    if (r0 != 0) goto L02015b2c
    r1_r0 = 0
    r2 = r8
    call panel_inputs_switch_scan
L02015b2c:
    r0 = b[r13+44] (u)
    r1 = b[r13+43] (u)
    if (r0 != r1) goto L02015adc
    r0 = 0
    r1 = 1562
    r2 = 0
    goto L02015b4c
L02015b42:
    r3 = r2 + r13
    b[r3+r1] = r0
    r2 += 1  ; @add.ri.u5
L02015b4c:
    if (r2 != 5) goto L02015b42
L02015b50:
    r0 = [r13+828]
    r11 = [sp+40]  ; @ld.w.sp.l
    r0 = r11 - r0
    ifs (r0 < 1) goto L02015b6c
    r1 = 1
    r2 = r11
    call control_actions_tick
    [r13+828] = r11
L02015b6c:
; HyperRig MINI, product option: the Bluetooth hold (2.5 s on and pairing, 6 s off) on A and B, as on the stock
; TANK-MINI; B and C held stay the tuner alone.
.if MINI_PRODUCT
    r0 = b[r14+116] (u)
    r1 = b[r14+117] (u)
.else
    r0 = b[r14+117] (u)
    r1 = b[r14+118] (u)
.endif
    r2 = r13 + 1567
    r0 = b[r0+r2] (u)
    r1 = b[r1+r2] (u)
    r2 = b[r13+52] (u)
    r1 += r0  ; @add.rr
    r0 = L01c2685e
    if (r1 == 0) goto L02015bb6
    r3 = h[r13+88] (u)
    r4 = [sp+36]
    r3 += r4  ; @add.rr
    r4 = r3 >> 5
    if (r4 >= 1875) {
    r3 = 60000
    }
    r4 = b[r0+0] (u)
    h[r13+88] = r3
    if (r1 != 1) goto L02015bc0
    if (r4 == 0) goto L02015cba
    r1 = 3
    b[r0+0] = r1
    goto L02015cba
L02015bb6:
    r1 = 0
    h[r13+88] = r1
    b[r0+0] = r1
    goto L02015cba
L02015bc0:
    r1 = L01c26860
    if (r4 == 0) goto L02015bd8
    if (r4 != 1) goto L02015bec
    if (r3 <= 2499) goto L02015bec
    r2 = 5
    r3 = 2
    goto L02015bfc
L02015bd8:
    r4 = 1
    if (r3 >= 1000) {  ; @if.ge.ri.s12
    r4 = 3
    }
    b[r0+0] = r4
    r0 = 0
    h[r13+88] = r0
    b[r1+0] = r2
    goto L02015cba
L02015bec:
    if (r4 != 2) goto L02015cba
    r2 = uextra(r3, p:4, l:12)
    if (r2 < 375) goto L02015cba
    r2 = 6
    r3 = 3
L02015bfc:
    b[r0+0] = r3
    r0 = b[r13+52] (u)
    r1 = b[r1+0] (u)
    if (r0 > r1) {
    r0 = 0
    b[r13+52] = r0
    }
    r0 = L01c26864
    r3 = 0
    b[r0+0] = r3
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r13 + 58
L02015c24:
    testset b[r0]
    ifeq goto L02015c24
    csync
    call console_helpers_now_ms
    if (r2 != 6) goto L02015c48
    r0 = 1536
    r1 = 1
    b[r13+r0] = r1
    r0 += -4
    b[r13+r0] = r3
    r4 = 2
    goto L02015c5a
L02015c48:
    r1 = 1536
    r3 = b[r13+r1] (u)
    call console_helpers_key_open
    r4 = 3
    if (r3 != 0) goto L02015c5a
    r4 = 1
L02015c5a:
    csync
    r0 = 0
    b[r13+58] = r0
    r3 = r4
    if (r4 != 3) {  ; @if.ne.ri.s12
    r3 = 1
    }
    call storage_coordination_irq_leave  ; @call.xl
    r2 = r4
    if (r4 != 2) {  ; @if.ne.ri.s12
    r2 = r3
    }
    r0 = 32
    r1 = -7
    call storage_coordination_notify
    r0 = b[r13+60] (u)
    if (r0 == 0) goto L02015c96
    r0 = h[r13+82] (u)
    if (r4 != 2) goto L02015c9c
    if (r0 == 0) goto L02015ca4
    call console_helpers_ble_drop
    goto L02015cb0
L02015c96:
    if (r4 == 2) goto L02015cb0
    goto L02015cba
L02015c9c:
    if (r0 != 0) goto L02015cba
    call console_helpers_ble_advertise
    goto L02015cba
L02015ca4:
    r0 = 1
    r1 = 1
    r2 = 0
    call L0204c744  ; @call.xl
L02015cb0:
    r0 = 1
    b[r13+45] = r0
    [r13+844] = r11
L02015cba:
; HyperRig MINI, product option: the volume wheel and the battery, once in each turn (mini/product).
.if MINI_PRODUCT
    r0 = r11
    call hyperrig_panel_turn
.endif
    call scene_application_flush
    r0 = 832
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L02016150
    r0 = 327808
    r1 = [r0+0]
    r0 = [r0+8]
    r0 |= r1
    if ((r0 & 0x1C0) != 0) {
    call panel_inputs_pedal_pins
    }
    r0 = b[r13+46] (u)
    r0 += 1  ; @add.ri.u5
    r1 = r0.b0 (u)
    b[r13+46] = r0
    r0 = 0
    if (r1 < 50) goto L02015d00
    b[r13+46] = r0
    call panel_inputs_pedal_pair
    call panel_inputs_pedal_volume
    goto L02015d20
L02015d00:
    [sp+60] = r0
    r0 = sp + 60
    call footswitch_events_pedal_read
    r1 = [sp+60]
    call panel_inputs_pedal_filter
    r0 = 832
    r4 = b[r13+r0] (u)
    call panel_inputs_pedal_volume
    if (r4 == 0) goto L02016150
L02015d20:
    r1 = b[r13+74] (u)
    r0 = 1
    if (r1 == 0) goto L02015d2a
    r0 = 0
L02015d2a:
    r1 = b[r13+75] (u)
    if (r1 != 1) {  ; @if.ne.ri.s12
    r1 = 0
    }
    r2 = 0x0 - r11
    ifs (r2 > 0) goto L02015d40
    r0 &= r1
    if (r0 == 0) goto L02015d66
L02015d40:
    r0 = b[r14+12] (u)
    r1 = 0
    call panel_inputs_analog_scan
    r0 = b[r14+12] (u)
    r1 = 832
    r1 = b[r13+r1] (u)
    r0 += 1  ; @add.ri.u5
    r0 = r0 & 0x7
    b[r14+12] = r0
    if (r1 == 0) goto L02016150
L02015d66:
    r0 = [r13+848]
    r0 = r11 - r0
    ifs (r0 < 0) goto L02015ff6
    r0 = 852
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L02015d8c
    r0 = 72960
    r0 = [r0+0]
    if ((r0 & 0x8000) == 0) goto L02015ff6
L02015d8c:
    r0 = r11 + 1000
    [r13+848] = r0
    call panel_inputs_analog_pins
    r0 = 0
    [sp+64] = r0
    r0 = 7
    call panel_inputs_analog_select
    r2 = 80000
    r3 = sp + 64
    r0 = 8
    r1 = 15
    call footswitch_events_adc_read
    r5 = r0
    r0 = 0
    call panel_inputs_analog_select
    r2 = [sp+64]
    if (r5 == 0) goto L02015e5c
    r3 = r2
    if (r2 >= 1023) {
    r3 = 1023
    }
    r6 = L01c26884
    r7 = b[r6+0] (u)
    r0 = L01c26868
    r4 = L01c26880
    r1 = b[r4+0] (u)
    h[r0+r7<<1] = r3
    r3 = r7 + 1
    r3 = r3 & 0x7
    b[r6+0] = r3
    if (r1 <= 7) {  ; @if.le.ri.s12
    r1 += 1  ; @add.ri.u5
    b[r4+0] = r1
    }
    r3 = r1.b0 (u)
    r4 = 0
    r6 = r3
    goto L02015e00
L02015dfa:
    r7 = h[r0++=2] (u)
    r4 += r7  ; @add.rr
    r6 += -1
L02015e00:
    if (r6 != 0) goto L02015dfa
    r0 = uextra(r1, p:1, l:7)
    r0 += r4  ; @add.rr
    r0 = r0 / r3 (u)
    r1 = L01c26878
    r1 = r0.l (u)  #
    h[r1+0] = r0
    r0 = 1023
    if (r1 >= 1023) {
    r1 = r0
    }
    r3 = 6600
    r1 *= r3
    r3 = r1 + 511
    r1 = r3 / r0 (u)
    r0 = L01c2687c
    h[r0+0] = r1
    r4 = 4296599
    r0 = 100
    if (r3 > r4) goto L02015e7e
    r0 = r15 + 4736
    r3 = 1
    goto L02015e54
L02015e4a:
    r4 = h[r0+-2] (u)
    if (r1 >= r4) goto L02015e66
    r0 += 4  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L02015e54:
    ifs (r3 <= 6) goto L02015e4a
    r0 = 0
    goto L02015e7e
L02015e5c:
    r0 = r13 + 1516
    [r0+0] += 1  ; @rmw.add.s12
    goto L02015eb0
L02015e66:
    r1 = r1 - r4  #
    r3 = b[r0+0] (u)
    r6 = b[r0+-4] (u)
    r6 = r6 - r3  #
    r0 = h[r0+-6] (u)
    r1 *= r6
    r0 = r0 - r4
    r4 = r0 >> 1
    r1 += r4  ; @add.rr
    r0 = r1 / r0 (u)
    r0 += r3  ; @add.rr
L02015e7e:
    r3 = 1512
    r4 = b[r13+r3] (u)
    r1 = L01c26886
    if (r4 == 0) goto L02015ea8
    r6 = b[r1+0] (u)
    r4 = r6 - r0
    r3 = r0 - r6
    if (r0 <= r6) {
    r3 = r4
    }
    if (r3 == 0) goto L02015eb0
    if (r3 > 2) goto L02015eae
    if (r0 == 100) goto L02015eae
    if (r0 == 0) goto L02015eae
    goto L02015eb0
L02015ea8:
    r4 = 1
    b[r13+r3] = r4
L02015eae:
    b[r1+0] = r0
L02015eb0:
    r0 = [r13+856]
    if (r0 != 0) {  ; @if.ne.ri.s12
    r1 = [r13+860]
    r3 = r1 / r0 (u)
    } else {
    r3 = 0
    }
    call tuner_and_control_records_mode_bits
    r6 = 0
    r7 = 0
    r0 = r0 & 0xF
    d[r13+856] = r7_r6
    if (r0 < 2) goto L02015edc
    call tuner_and_control_records_event_reset
    goto L02015fe6
L02015edc:
    r0 = L01c34468
    r0 = [r0+0]
    r4 = [r13+280]
    r1 = b[r13+52] (u)
    if (r5 == 0) goto L02015fe4
    r4 = r4 << 24
    r0 ^= r4
    r1 = r1 << 28
    r0 ^= r1
    r1 = 0
    goto L02015f0c
L02015efa:
    r4 = r1 + r14
    r4 = r4 + 272
    r5 = h[r4+2] (u)
    h[r4+0] = r5
    r5 = h[r4+20] (u)
    h[r4+18] = r5
    r1 += 2  ; @add.ri.u5
L02015f0c:
    if (r1 != 16) goto L02015efa
    if (r2 >= 1023) {
    r2 = 1023
    }
    h[r14+288] = r2
    r1 = 65535
    r3 = umin(r3, r1)
    h[r14+306] = r3
    r4 = 318
    r3 = b[r14+r4] (u)
    if (r3 < 9) {  ; @if.lt.ri.s12
    r3 += 1  ; @add.ri.u5
    b[r14+r4] = r3
    }
    r4 = [r14+308]
    if (r4 != r0) goto L02015fc4
    r0 = 319
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L02015fda
    r3 = r3.b0 (u)
    r0 = 0
    if (r3 < 9) goto L02015fe6
    r3 = 0
    goto L02015f6c
L02015f5a:
    r4 = r14 + 290
    r4 = h[r4+r0<<1] (u)
    r3 = umax(r4, r3)
    r1 = umin(r4, r1)
    r0 += 1  ; @add.ri.u5
L02015f6c:
    if (r0 != 9) goto L02015f5a
    r1 = r3 - r1
    r0 = 0
    if (r1 > 1200) goto L02015fe6
    r6 = 0
    goto L02015f8a
L02015f7e:
    r1 = r14 + 272
    r1 = h[r1+r0<<1] (u)
    r6 += r1  ; @add.rr
    r0 += 1  ; @add.ri.u5
L02015f8a:
    if (r0 != 6) goto L02015f7e
    r1 = h[r14+286] (u)
    r3 = umax(r2, r1)
    r0 = umin(r2, r1)
    r4 = r6 + 3
    r5 = 6
    r1 += r2  ; @add.rr
    r2 = r1 * 0x3
    r7 = r2 - r6
    r2 = r4 / r5 (s)
    ifs (r7 <= 41) goto L02017638
    r4 = r0 * 0x6
    r6 = r4 - r6
    r4 = 0
    r5 = 1
    ifs (r6 <= 29) {  ; @ifs.le.ri.s12
    r5 = 0
    }
    goto L0201764c
L02015fc4:
    [r14+308] = r0
    r1 = 319
    r0 = b[r14+r1] (u)
    if (r0 <= 8) {  ; @if.le.ri.s12
    r0 = 9
    b[r14+r1] = r0
    }
L02015fda:
    r0 += -1
    r1 = 319
    b[r14+r1] = r0
L02015fe4:
    r0 = 0
L02015fe6:
    call tuner_and_control_records_event_notify
    r0 = 832
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L02016150
L02015ff6:
    r0 = [r13+864]
    r0 = r11 - r0
    ifs (r0 < 0) goto L02016150
    r0 = r11 + 250
    [r13+864] = r0
    call tuner_and_control_records_mode_bits
    r0 = r0 & 0xF
    if (r0 < 2) goto L0201602e
    r1 = 788
    r2 = 0
    h[r13+r1<<1] = r2
    r1 = 393
    [r13+r1<<2] = r2
    call tuner_and_control_records_event_reset
    goto L0201614c
L0201602e:
    r5 = 0
    r0 = 0x11800  #
    [sp+76] = r5
    [sp+72] = r5
    [sp+68] = r5
    r0 = [r0+0]
    if ((r0 & 1) == 0) goto L02016120
    r2 = sp + 76
    r0 = 13
    r1 = 2
    call tuner_and_control_records_bus_read
    r4 = r0
    r2 = sp + 72
    r0 = 12
    r1 = 2
    call tuner_and_control_records_bus_read
    if ((r0 & r4) == 0) goto L02016120
    call storage_coordination_irq_enter  ; @call.xl
    r6 = L01c1fa24
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r1 + 1
    [r6+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L02016086
    csync
L0201607e:
    testset b[r8]
    ifeq goto L0201607e
    csync
L02016086:
    r4 = 0x51000
    r7 = [r4+0]
    if ((r7 & 0x40) != 0) goto L02017598
    r0 = r7 & 0xFFFFFF5F
    r0 |= 128
    [r4+0] = r0
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L020160b2
    csync
    r0 = 0
    b[r8+0] = r0
L020160b2:
    call storage_coordination_irq_leave  ; @call.xl
    r2 = sp + 68
    r0 = 13
    r1 = 15
    call tuner_and_control_records_bus_read
    r2 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r6+r0<<2]
    r3 = r1 + 1
    [r6+r0<<2] = r3
    if (r1 != 0) goto L020160e4
    csync
L020160dc:
    testset b[r8]
    ifeq goto L020160dc
    csync
L020160e4:
    r0 = [r4+0]
    r1 = r0 & 0xA0
    r3 = 0
    if (r1 != 128) goto L020160fe
    r1 = r7 & 0xA0
    r0 = r0 & 0xFFFFFF5F
    r0 |= r1
    r3 = r2  #
    [r4+0] = r0
L020160fe:
    r0 = cnum
    r1 = [r6+r0<<2]
    r1 += -1
    [r6+r0<<2] = r1
    if (r1 != 0) goto L02016116
    csync
    r0 = 0
    b[r8+0] = r0
L02016116:
    call storage_coordination_irq_leave  ; @call.xl
    r5 = [sp+68]
    goto L02016122
L02016120:
    r3 = 0
L02016122:
    r1_r0 = d[sp+72]
    r2 = 322
    r4 = b[r14+r2] (u)
    r6 = r13 + 1572
    h[r6+0] = r1
    h[r6+2] = r0
    h[r6+4] = r5
    if (r4 == 0) goto L02016cae
    r0 = r4 + -1
    b[r14+r2] = r0
L02016146:
    r0 = 0
    h[r14+320] = r0
L0201614c:
    call tuner_and_control_records_event_notify
L02016150:
    r0 = b[r13+74] (u)
    if (r0 != 0) goto L02016618
    r0 = b[r13+75] (u)
    if (r0 != 1) goto L02016618
    r0 = b[r13+52] (u)
    if (r0 != 0) goto L02016618
    r0 = 868
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L02016618
    r0 = 836
    r14 = b[r13+r0] (u)
    r4 = 0
    b[r13+r0] = r4
    r0 = sp + 80
    r1 = r0 | 0x3
    r1 = r0 | 0x2  #
    [sp+20] = r1
    [sp+32] = r1
    [sp+24] = r0
    r0 |= 1
    [sp+28] = r0
    r5 = 1
    goto L02016612
L020161a2:
    if ((r14 & 1) == 0) goto L020161b6
    r0 = r5 * 0x28
    r0 += r13
    r1 = 10302
    r2 = 255
    b[r0+r1] = r2
L020161b6:
    r1 = sp + 80
    r0 = r5
    call tuner_and_control_records_control_record
    if (r0 == 0) goto L020162d4
    r0 = r5 * 0x28
    r7 = r0 + r13
    r0 = 10281
    r0 = b[r7+r0] (u)
    if (r0 == 0) goto L020162e2
    r0 = 10284
    r0 = b[r7+r0] (u)
    if (r0 != 0) goto L020162e2
    r0 = 10283
    r0 = b[r7+r0] (u)
    if (r0 > 7) goto L020162e2
    r0 = 10282
    r6 = b[r7+r0] (u)
    r0 = sp + 80
    call tuner_and_control_records_record_value
    r11 = b[sp+80] (u)
    r12 = r0
    r8 = r11 | 0x1
    r9 = 0
    if (r8 != 5) goto L02016270
    r1 = r7
    r2 = 10305
    r3 = b[++r1=r2] (s)
    r2 = 0
    goto L0201621c
L0201621a:
    r2 += 1  ; @add.ri.u5
L0201621c:
    ifs (r2 > 7) goto L02016230
    r4 = r2 + r15
    r0 = 1118
    r4 = b[r4+r0] (u)
    if (r4 <= r6) goto L0201621a
L02016230:
    r4 = r3.b0 (u)
    if (r4 > 8) goto L02016268
    if (r3 == r2) goto L02016268
    ifs (r2 <= r3) goto L02016250
    r4 = r3 + r15
    r0 = 1118
    r4 = b[r4+r0] (u)
    r4 += 2  ; @add.ri.u5
    if (r4 > r6) goto L02016266
L02016250:
    ifs (r2 >= r3) goto L02016268
    r4 = r3 + r15
    r0 = 1117
    r0 = b[r4+r0] (u)
    r4 = r6 + 2
    if (r4 < r0) goto L02016268
L02016266:
    r2 = r3
L02016268:
    r9 = sextra(r2, p:0, l:8)  #
    b[r1+0] = r2
    r4 = 0
L02016270:
    r1 = r7  #
    r3 = [sp+28]
    r2 = 10302  #
    r0 = b[r3+0] (u)
    r2 = b[++r1=r2] (u)
    if (r11 != r2) goto L020162ea
    r2 = b[r1+1] (u)
    if (r0 != r2) goto L020162ea
    r0 = 10304  #
    [sp+16] = r0
    r2 = b[r7+r0] (u)
    r0 = [sp+16]
    r3 = [sp+32]
    r3 = b[r3+0] (u)
    if (r3 != r2) goto L020162ea
    r1 = [sp+24]
    r0 = b[r1+4] (u)
    [sp+12] = r0
    if (r0 == 0) goto L020163c0
L020162a6:
    r0 = 10296
    r2 = r7 + r0
    if (r8 != 5) goto L02016390
    r0 = b[r2+0] (u)
    if (r0 == 0) goto L020163ca
    r0 = 5150
    r0 = h[r7+r0<<1] (s)
    if (r0 != r12) goto L020163de
    r0 = 10298
    r1 = b[r7+r0] (u)
    r0 += 8  ; @add.ri.u5
    r0 += r7  ; @add.rr
    if (r1 == r9) goto L02016400
    goto L02016418
L020162d4:
    r0 = r5 * 0x28
    r0 += r13
    r1 = 10302
    b[r0+r1] = r4
L020162e2:
    r5 += 1  ; @add.ri.u5
    r11 = [sp+40]  ; @ld.w.sp.l
    goto L02016612
L020162ea:
    r2 = [sp+32]
    r2 = b[r2+0] (u)
    b[r1+0] = r11
    r0 = 10296  #
    b[r1+1] = r0
    r4 = r7 + r0
    b[r4+8] = r2
    r1 = 255
    b[r4+10] = r1
    if (r8 != 5) goto L02016312
    r3 = 1
    if (r9 != r12) {
    r3 = 0
    }
    r0 = r4
    r1 = r9
    goto L02016386
L02016312:
    r0 = r6 + -1
    if (r6 != 0) goto L0201631a
    r0 = r6
L0201631a:
    r1 = [sp+20]
    r3 = b[r1+0] (u)
    r1 = [sp+24]
    r7 = h[r1+8] (s)
    r1 = h[r1+6] (s)
    r2 = r7
    call meter_curves_curve_value
    r2 = r6 + 1
    r9 = r0
    r11 = -32768
    if (r6 >= 127) {  ; @if.ge.ri.s12
    r2 = 127
    }
    r0 = r2
    r2 = r7
    call meter_curves_curve_value
    r8 = r0
    if (r3 != 2) goto L02016364
    r3 = 2
    r0 = r6
    r2 = r7
    call meter_curves_curve_value
    if (r12 == r11) goto L0201637a
    if (r0 == r11) goto L0201637a
    if (r9 != r11) {
    r1 = r9
    }
    r9 = r1
L02016364:
    r0 = 1
    r1 = 1
    ifs (r9 > r12) {
    r1 = 0
    }
    ifs (r8 < r12) {
    r0 = 0
    }
    r3 = r0 & r1
    goto L02016382
L0201637a:
    r3 = 1
    if (r0 != r12) {
    r3 = 0
    }
L02016382:
    r0 = r4
    r1 = r6
L02016386:
    r2 = r12
    call triplet_helpers_mark_record
L0201638c:
    r4 = 0
    goto L020162e2
L02016390:
    r0 = [sp+20]
    r0 = b[r0+0] (u)
    [sp+8] = r0
    r1 = [sp+24]
    r0 = h[r1+8] (s)
    [sp+4] = r0
    r0 = b[r2+0] (u)
    r1 = h[r1+6] (s)
    if (r0 == 0) goto L020163d4
    r9 = r3
    r0 = 5150
    r0 = h[r7+r0<<1] (s)
    if (r0 != r12) goto L0201645c
    r0 = r7
    r3 = 10298
    r8 = b[++r0=r3] (u)
    goto L02016492
L020163c0:
    if (r11 == 5) goto L020162a6
    if (r11 == 3) goto L020162a6
    goto L020162e2
L020163ca:
    r0 = 10297
    r0 = b[r7+r0] (u)
    goto L020163f4
L020163d4:
    r0 = 10297
    r0 = b[r7+r0] (u)
    goto L02016474
L020163de:
    r0 = 10297  #
    b[r2+0] = r4
    b[r7+r0] = r9
    r0 = 255
    r1 = 10298
    b[r7+r1] = r0
    r0 = r9
L020163f4:
    r0 = r0.b0 (u)
    if (r0 != r9) goto L02016406
    r0 = 10306
    r0 += r7  ; @add.rr
L02016400:
    r1 = 255
    b[r0+0] = r1
    goto L020162e2
L02016406:
    r0 = 1
    r1 = 10298  #
    b[r2+0] = r0
    r0 = 255
    b[r7+r1] = r0
    r0 = r1 + 8
    r0 += r7  ; @add.rr
L02016418:
    r1 = b[r0+0] (s)
    if (r9 != r1) goto L0201651a
    r6 = r3  #
    r2 = [sp+36]
    r3 = 5154
    r1 = h[r7+r3<<1] (u)
    r1 += r2  ; @add.rr
    r2 = 65520
    r2 &= r1
    h[r7+r3<<1] = r1
    r3 = r6
    if (r2 < 400) goto L020162e2
    r1 = 10298
    b[r7+r1] = r9
    r1 = 255
    b[r0+0] = r1
    call panel_inputs_change_check
    r0 = 1
    r1 = 872
    b[r13+r1] = r0
    goto L020164ae
L0201645c:
    r0 = 10297  #
    b[r2+0] = r4
    b[r7+r0] = r6
    r0 = 255
    r3 = 10298
    b[r7+r3] = r0
    r0 = r6
    r3 = r9
L02016474:
    r0 = r6 - r0
    r0 = abs(r0)
    ifs (r0 < 3) goto L020162e2
    r0 = 1
    r9 = r3  #
    b[r2+0] = r0
    r8 = 255
    r0 = r7
    r3 = 10298
    b[++r0=r3] = r8
L02016492:
    if (r8 == r6) goto L020162e2
    r0 = r6  #
    b[r0+0] = r6
    r3_r2 = d[sp+4]
    call meter_curves_curve_value
    r3 = r9
    r9 = r0
    if (r0 == r12) goto L020162e2
    call panel_inputs_change_check
L020164ae:
    r0 = r11 + -1
    r8 = [sp+40]  ; @ld.w.sp.l
    if (r0 > 4) goto L020165f0
    tbb [r0]
control_scan_record_kinds:
    .byte (L020164c2 - control_scan_record_kinds) / 2, (L02016528 - control_scan_record_kinds) / 2, (L02016566 - control_scan_record_kinds) / 2, (L02016598 - control_scan_record_kinds) / 2, (L020165ac - control_scan_record_kinds) / 2
    .byte 0x00  ; alignment
L020164c2:
    r4 = r3  #
    r0 = [sp+16]
    call preset_application_effect_type  ; @call.xl
    r6 = r4
    if (r4 != 0) goto L020164fe
    if (r0 != 5) goto L020164fe
    r1 = 4
    r0 = [sp+16]
    call preset_application_parameter  ; @call.xl
    if (r0 == 0) goto L020164fe
    r0 = L01c1f7e0
    r1 = 4
    r2 = 0
    r4 = [sp+16]
    r0 = r4  #
    r3 = b[r0+0] (u)
    call dispatch_helpers_parameter_apply
    r0 = 112
    r2 = 4
    r1 = r4
    call panel_inputs_event_queue
L020164fe:
    r0 = L01c1f7e0
    r1 = r6  #
    r4 = [sp+16]
    r0 = r4  #
    r3 = b[r0+0] (u)
    r2 = r9
    call dispatch_helpers_parameter_apply
    r0 = 112
    r1 = r4
    r2 = r6
    goto L020165ec
L0201651a:
    b[r0+0] = r9
    r0 = 5154
    h[r7+r0<<1] = r4
    goto L020162e2
L02016528:
    r6 = r3
    goto L0201653c
L0201652c:
    r0 = r4
    call audio_measurement_control_value  ; @call.xl
    r1 = sp + 92
    h[r1+r4<<1] = r0
    r4 += 1  ; @add.ri.u5
L0201653c:
    if (r4 != 6) goto L0201652c
    r4 = r6
    r0 = r4
    r1 = r9
    call dsp_transition_clamp  ; @call.xl
    r1 = L01c1f7e0
    r1 = b[r1+0] (u)
    r2 = sp + 92
    h[r2+r4<<1] = r0
    r0 = r2
    call dsp_transition_request  ; @call.xl
    r0 = 113
    goto L020165e8
L02016566:
    r0 = -32768
    if (r9 == r0) goto L020165d8
    r1 = 0
    r0 = [sp+16]
    call preset_application_parameter  ; @call.xl
    if (r0 == r9) goto L020165d0
    r0 = L01c1f7e0
    r1 = 0
    r2 = r9  #
    r4 = [sp+16]
    r0 = r4  #
    r3 = b[r0+0] (u)
    call dispatch_helpers_parameter_apply
    r0 = 112
    r2 = 0
    r1 = r4
    goto L020165cc
L02016598:
    if (r9 > 14) goto L020165f0
    r0 = r9
    call capture_loader_load
    if (r0 != 0) goto L020165f0
    r0 = 120
    r1 = 0
    r2 = 0
    goto L020165ec
L020165ac:
    if (r9 == 0) goto L020165d8
    r0 = sp + 80
    call tuner_and_control_records_record_value
    if (r0 == r9) goto L020165c6
    r1 = r9 + -1  #
    r0 = [sp+16]
    call slot_commands_choose_slot_ir
    if (r0 != 0) goto L020165f0
L020165c6:
    r0 = 120
    r1 = 0
    r2 = 0
L020165cc:
    call panel_inputs_event_queue
L020165d0:
    r0 = [sp+12]
    if (r0 != 0) goto L020165f0
    r1 = 1
    goto L020165de
L020165d8:
    r0 = [sp+12]
    if (r0 == 0) goto L020165f0
    r1 = 0
L020165de:
    r4 = [sp+16]
    r0 = r4
    call slot_commands_enable_command
    r0 = 101
L020165e8:
    r2 = 0
    r1 = r4
L020165ec:
    call panel_inputs_event_queue
L020165f0:
    call panel_inputs_change_mark
    r4 = sp + 80
    r0 = r5
    r1 = r4
    call tuner_and_control_records_control_record
    r0 = r4
    call tuner_and_control_records_record_value
    r1 = 5150
    h[r7+r1<<1] = r0
    [r13+812] = r8
    goto L0201638c
L02016612:
    if (r5 != 15) goto L020161a2
L02016618:
    r0 = b[r13+41] (u)
    if (r0 == 0) goto L0201667e
    r0 = 800
    r0 = r11 / r0 (u)
    r4 = r0 & 0x1
    r5 = 0
    goto L0201664c
L0201662e:
    r0 = sp + 155
    r0 += r5  ; @add.rr
    if (r4 != 0) goto L02016642
    r1 = r15 + 41
    rep 3 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    goto L0201664a
L02016642:
    r1 = 0
    r3_r2 = 0
    call triplet_helpers_clamp_triplet
L0201664a:
    r5 += 3  ; @add.ri.u5
L0201664c:
    if (r5 != 36) goto L0201662e
    r0 = r4 ^ 0x1
    b[r13+47] = r0
    r4 = 0
    r5 = sp + 155
    r14 = L01c1f180
    goto L02016676
L02016666:
    r0 = r4  #
    r3 = b[r5+2] (u)
    r2 = b[r5+1] (u)
    r1 = b[r5++=3] (u)
    call triplet_helpers_store_slot
    r4 += 1  ; @add.ri.u5
L02016676:
    if (r4 != 12) goto L02016666
    goto L020171f6
L0201667e:
    call mode_and_settings_block_ensure
    r0 = r13
    r2 = [++r0=880]
    [r0+0] = r11
    r1 = r11 - r2
    r6 = 10
    if (r2 == 0) goto L02016696
    r6 = r1
L02016696:
    r0 = b[r0+4] (u)
    if (r0 != 0) goto L020166b6
    r0 = 64936
    r1 = r13 + 1578
    h[r1+2] = r0
    h[r1+0] = r0
    r0 = 0
    r0 = 884  #
    h[r1+4] = r0
    r1 = 1
    b[r13+r0] = r1
L020166b6:
    r0 = 1041
    r2 = [r13+r0<<2]
    r4 = 0
    [r13+r0<<2] = r4
    r0 = [r13+280]
    r1 = -1440
    r14 = L01c1f180
    if (r2 == 0) goto L02016704
    if (r0 == 0) goto L02016704
    r1 = 32
    r0 = 5418
L020166dc:
    r1 += -1
    r5 = r2 >> r1
    r0 = r0 + -602
    if (r5 == 0) goto L020166dc
    r3 = 0
    r3_r2 <<= 8
    r3_r2 >>= r1
    r1 = r2 * 0x3C
    r1 = r1 - 0x3C00
    r1 = r1 >> 8
    r2 = 10
    r0 = r0 / r2 (s)
    r1 += r0  ; @add.rr
L02016704:
    r8 = r13 + 1578
    r0 = r8
    r2 = r6
    call meter_curves_peak_hold
    [sp+112] = r4
    r0 = sp + 112
    call triplet_helpers_active_flag
    r5 = r0
    if (r5 == 0) goto L0201672c
    r0 = [r13+888]
    r2 = r6  #
    r1 = [sp+112]
    call meter_curves_wrapped_step
    [r13+888] = r0
L0201672c:
    r0 = r14 + 88
    r4 = [r0+40]
    r1_r0 = d[r0+0]
    d[sp+28] = r1_r0
    if (r1 == r4) goto L02016778
    r0 = [sp+32]
    ifs (r0 < 0) goto L0201676e
    if (r4 == -2) goto L0201676e
    r0 = 892
    r1 = 1
    b[r13+r0] = r1
    [r13+896] = r11
    r7 = r13 + 92
    r0 = r7
    call footswitch_events_colour_word
    if (r0 != 0) goto L0201676e
    r1 = r7  #
    r0 = [sp+32]
    r0 = r0 * 0x25
    call colour_frames_hue_colour
L0201676e:
    r0 = [sp+32]
    [r14+128] = r0
    [r13+812] = r11
L02016778:
    r0 = [r14+132]
    r1 = [sp+28]
    if (r1 == r0) goto L02016796
    r0 = [sp+32]
    if (r0 == r4) {
    [r13+900] = r11
    }
    r0 = [sp+28]
    [r14+132] = r0
    [r13+812] = r11
L02016796:
    r0 = [r13+904]
    if (r0 != 0) goto L020167a6
    r0 = r11
    if (r0 != 0) goto L020167a2
    r0 = 1
L020167a2:
    [r13+904] = r0
L020167a6:
    r1 = 908
    r2 = 2422
    r4 = b[r13+r2] (u)
    r1 = b[r13+r1] (u)
    r2 = uextra(r4, p:5, l:1)
    r2 |= r1
    r1 = 912  #
    [sp+20] = r2
    if ((r2 & 1) == 0) goto L020167da
    r2 = b[r13+r1] (u)
    r2 ^= 1
    if ((r2 & 1) == 0) goto L020167da
    r12 = r11 - r0
    if (r12 <= 1499) goto L020167fc
L020167da:
    r0 = 1
    b[r13+r1] = r0
    r0 = b[r13+48] (u)
    if (r0 == 0) goto L020168dc
    r1 = [r13+916]
    r7 = r11 - r1
    if (r7 < 4000) goto L02016886
    r0 = 0
    b[r13+48] = r0
    goto L020168dc
L020167fc:
    r9 = 256
    if (r12 < 1000) goto L02016816
    r1 = 1500
    r1 = r1 - r12
    r1 = r1 << 8
    r2 = 500
    r9 = r1 / r2 (u)
L02016816:
    r0 = r0 << 8
    r1 = r10 * 0xA00
    r14 = r1 - r0
    r4 = r12 >> 2
    r5 = sp + 119
    r8 = 0
    r10 = 200
    r7 = 0
    r6 = r12
    goto L02016878
L02016832:
    if (r12 >= r7) goto L02016842
    r1 = 0
    r3_r2 = 0
    r0 = r5
    call triplet_helpers_clamp_triplet
    goto L0201686c
L02016842:
    r1 = sp + 191
    r0 = r4
    call colour_frames_hue_colour
    r0 = 256
    if (r6 <= 199) {  ; @if.le.ri.s12
    r0 = r14 / r10 (u)
    }
    r0 *= r9
    r0 = r0 >> 8
    r0 = r0 * 0xA0
    r2 = r0 >> 8
    r1 = sp + 191
    r0 = r5
    call triplet_helpers_scale_triplet
L0201686c:
    r7 += 50
    r6 += -50
    r14 = r14 - 0x3200
    r4 += 21  ; @add.ri.u5
    r5 += 3  ; @add.ri.u5
L02016878:
    if (r7 != 600) goto L02016832
    r14 = L01c1f180
    goto L02016ff6
L02016886:
    if (r0 == 2) goto L02016c78
    if (r0 != 1) goto L020168dc
    r0 = 2000
    r0 = r7 / r0 (u)
    r0 = r0 * 0x7D0
    r0 = r7 - r0
    r1 = 0x7D0 - r0
    if (r0 >= 1000) {  ; @if.ge.ri.s12
    r0 = r1
    }
    r1 = r0 * 0x320
    r0 = [r13+888]
    r2 = 1000
    r1 = r1 / r2 (s)
    r5 = r1 + -400
    r1 = r5
    r2 = r6
    call meter_curves_wrapped_step
    r2 = r0
    [r13+888] = r2
    if ((r4 & 0x2) != 0) goto L02016fb8
    r2 = sp + 119
    r0 = 1
    r1 = r5
    call colour_frames_ring_needle
    goto L02016ff4
L020168dc:
    r0 = b[r13+52] (u)
    if (r0 == 0) goto L020168e6
    if ((r4 & 1) != 0) goto L0201690c
L020168e6:
    r0 = 2448
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L0201691e
    if (r0 == 2) goto L02016906
    r0 = [r13+808]
    r0 = r0 - r11
    ifs (r0 > 0) goto L02016906
    r0 = b[r13+17] (u)
    if (r0 == 0) goto L0201691e
L02016906:
    r1 = sp + 119
    r0 = r8
    goto L02016ff0
L0201690c:
    r1 = [sp+112]
    if ((r4 & 0x2) != 0) goto L02016c66
    r2 = sp + 119
    r0 = r5
    call colour_frames_ring_needle
    goto L02016c72
L0201691e:
    r0 = b[r13+74] (u)
    if (r0 == 0) goto L02016d20
    call preset_application_services_tempo  ; @call.xl
    r1 = [r13+928]
    r1 = r11 - r1
    ifs (r0 <= 199) {  ; @ifs.le.ri.s12
    r0 = 1200
    }
    r2 = 600000
    r0 = r2 / r0 (u)
    if (r0 <= 100) {  ; @if.le.ri.s12
    r0 = 100
    }
    r2 = r1 / r0 (u)
    r2 *= r0
    r2 = r1 - r2
    r1 = r0 >> 1
    if (r1 >= 160) {  ; @if.ge.ri.s12
    r1 = 160
    }
    r0 = 255
    r4 = 255
    if (r2 < 40) goto L02016982
    r3 = r1 + 40
    r4 = 0
    if (r2 >= r3) goto L02016982
    r2 = r2 * 0xFF
    r3 = -10200
    r2 += r3  ; @add.rr
    r1 = r2 / r1 (u)
    r4 = 0xFF - r1
L02016982:
    r1 = r4 << 8
    r11 = r1 / r0 (u)  #
    [sp+12] = r4
    r1 = r4 * 0x2D
    r0 = r1 / r0 (u)
    r7 = r0 + 55
    r0 = r14 + 236
    r8 = 0  #
    [sp+36] = r0
    r0 = sp + 210
    [sp+16] = r0
    r0 = sp + 206
    [sp+4] = r0
    r0 = sp + 200
    [sp+8] = r0
    r0 = sp + 214
    [sp+24] = r0
    goto L02016c56
L020169b8:
    r0 = r8 * 0x9  #
    r1 = [sp+32]
    r9 = r0 + r14
    r0 = 2423
    r4 = b[r13+r0] (u)
    r0 = r9
    r2 = b[++r0=236] (u)
    [sp] = r1
    r1 = 1
    if (r2 == 0) goto L020169d8
    r1 = 0
L020169d8:
    r1 = r1 * 0x3  #
    r3 = [sp+28]
    r5 = r0 + r1
    r1 = sp + 214
    r2 = sp + 210
    r0 = r5
    call colour_frames_switch_colours
    r12 = r4 & (1 << r8)
    if (r12 == 0) goto L02016a24
    r1 = r8 * 0x3
    r1 += r13
    r1 = r1 + 2424
    r2 = b[r1+2] (u)
    b[sp+216] = r2
    r2 = b[r1+1] (u)
    r3 = b[r1+0] (u)
    r3 <= insert(r2, p:8, l:24)  #
    r4 = b[r1+14] (u)
    r6 = b[r1+13] (u)
    r1 = b[r1+12] (u)
    h[sp+214] = r3
    b[sp+212] = r4
    r1 <= insert(r6, p:8, l:24)
    h[sp+210] = r1
L02016a24:
    if (r0 == 1) goto L02016a3c
    r1 = 0
    r3_r2 = 0
    if (r0 != 2) goto L02016a46
    r0 = [sp+24]
    r1 = b[r0+2] (u)
    r2 = b[r0+1] (u)
    r3 = b[sp+214] (u)
    goto L02016a46
L02016a3c:
    r0 = [sp+16]
    r1 = b[r0+2] (u)
    r2 = b[r0+1] (u)
    r3 = b[sp+210] (u)
L02016a46:
    r0 = r8 + r15
    r0 = b[r0+202] (u)
    r10 = r0 * 0x3
    r0 = sp + 119
    r4 = r0 + r10
    r0 = 0
    goto L02016a68
L02016a5c:
    r6 = r4
    b[++r6=r0] = r3
    b[r6+1] = r2
    b[r6+2] = r1
    r0 += 3  ; @add.ri.u5
L02016a68:
    if (r0 != 9) goto L02016a5c
    r2 = 0
    r0 = 3
    r1 = [sp+36]
    goto L02016a84
L02016a74:
    r6 = b[r1++=3] (u)
    r3 = 1
    if (r6 != 7) {  ; @if.ne.ri.s12
    r3 = r2
    }
    r0 += -1
    r2 = r3
L02016a84:
    if (r0 != 0) goto L02016a74
    if (r2 == 0) goto L02016b0e
    r0 = 2422
    r0 = b[r13+r0] (u)
    if ((r0 & 4) == 0) goto L02016b0e
    r0 = b[r5+0] (u)
    if (r0 != 7) goto L02016ac0
    r0 = sp + 119
    r5 = r0 + r10
    r14 = 0
    goto L02016aba
L02016aa4:
    r0 = r5 + r14
    r1 = sp + 210
    r2 = sp + 214
    r3 = r11
    call triplet_helpers_blend_triplets
    r14 = r14 + 3
L02016aba:
    if (r14 != 9) goto L02016aa4
    goto L02016b0e
L02016ac0:
    r0 = [sp+12]
    if (r0 == 0) goto L02016b0e
    if (r12 == 0) goto L02016ae6
    r0 = r8 * 0x3
    r0 += r13
    r0 = r0 + 2424
    r1 = b[r0+2] (u)
    r2 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    b[sp+208] = r1
    r0 <= insert(r2, p:8, l:24)
    h[sp+206] = r0
    goto L02016af6
L02016ae6:
    r0 = 140
    b[sp+206] = r0
    r0 = [sp+4]
    r1 = 70
    b[r0+1] = r1
    r1 = 0
    b[r0+2] = r1
L02016af6:
    r5 = sp + 203
    r1 = sp + 206
    r0 = r5
    r2 = r11
    call triplet_helpers_scale_triplet
    r0 = r4 + 3
    r1 = r5
    call triplet_helpers_brighter_triplet
L02016b0e:
    r0 = 2422
    r0 = b[r13+r0] (u)
    r14 = L01c1f180
    if ((r0 & 16) == 0) goto L02016bae
    r0 = r8 + r14
    r0 = b[r0+116] (u)
    r0 += r13
    r1 = 1567
    r0 = b[r0+r1] (u)
    if (r0 == 0) goto L02016bae
    r0 = r8 + r13
    r1 = 932
    r0 = b[r0+r1] (u)
    if (r0 != 0) goto L02016bae
    r0 = b[++r9=239] (u)
    if (r0 == 0) goto L02016bae
    if (r12 == 0) goto L02016b6a
    r0 = r8 * 0x3
    r0 += r13
    r0 = r0 + 2424
    r1 = b[r0+2] (u)
    r2 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    b[sp+202] = r1
    r0 <= insert(r2, p:8, l:24)
    h[sp+200] = r0
    goto L02016b9c
L02016b6a:
    r1 = sp + 200
    r2 = sp + 197
    r0 = [sp+32]
    r0 = r9  #
    [sp] = r0
    r3 = [sp+28]
    call colour_frames_switch_colours
    r2 = [sp+8]
    r0 = b[r2+1] (u)
    r1 = b[sp+200] (u)
    r0 += r1  #  ; @add.rr.p
    r2 = b[r2+2] (u)
    r0 += r2  ; @add.rr
    if (r0 > 59) goto L02016b9c
    r1 = 160
    b[sp+200] = r1
    r0 = [sp+8]
    b[r0+1] = r1
    b[r0+2] = r1
L02016b9c:
    r0 = r13 + 1608
    r0 = h[r0+r8<<1] (u)
    r1 = sp + 200
    r2 = r4
    call colour_frames_bar_fill
L02016bae:
    r0 = r8 + r13
    r1 = 924
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L02016c1a
    r1 = r13 + 1812  #
    r2 = [sp+40]
    r1 = [r1+r8<<2]
    r1 = r2 - r1
    if (r1 > 119) goto L02016c10
    r2 = [sp+24]
    r0 = b[r2+1] (u)
    r1 = b[sp+214] (u)
    r0 += r1  #  ; @add.rr.p
    r3 = b[r2+2] (u)
    r2 = r15 + 50
    r3 = 0x0 - r3
    r1 = sp + 214
    if (r0 == r3) {
    r1 = r2
    }
    r0 = sp + 194
    r3 = 64
    call triplet_helpers_blend_triplets
    r0 = sp + 119
    r4 = r0 + r10
    r5 = 0
    goto L02016c0a
L02016bfe:
    r0 = r4 + r5
    r1 = sp + 194
    call triplet_helpers_brighter_triplet
    r5 += 3  ; @add.ri.u5
L02016c0a:
    if (r5 != 9) goto L02016bfe
    goto L02016c1a
L02016c10:
    r1 = 0
    r2 = 924
    b[r0+r2] = r1
L02016c1a:
    r0 = 2422
    r0 = b[r13+r0] (u)
    if ((r0 & 8) == 0) goto L02016c4c
    r0 = sp + 119
    r6 = r0 + r10
    r4 = 0
    goto L02016c48
L02016c30:
    r5 = 3
    r3 = r6
    goto L02016c42
L02016c36:
    r1 = r7  #
    r0 = b[r3+0] (u)
    call triplet_helpers_percent_of
    b[r3++=1] = r0
    r5 += -1
L02016c42:
    if (r5 != 0) goto L02016c36
    r6 += 3  ; @add.ri.u5
    r4 += 1  ; @add.ri.u5
L02016c48:
    if (r4 != 3) goto L02016c30
L02016c4c:
    r0 = [sp+36]
    r0 += 9  ; @add.ri.u5
    r8 = r8 + 1  #
    [sp+36] = r0
L02016c56:
    if (r8 != 4) goto L020169b8
    r8 = 1
    r11 = [sp+40]  ; @ld.w.sp.l
    goto L02016ff6
L02016c66:
    r2 = [r13+888]
    r3 = sp + 119
    r0 = r5
    call colour_frames_ring_strobe
L02016c72:
    [r13+812] = r11
    goto L02016ff4
L02016c78:
    r0 = 64936
    h[sp+106] = r0
    h[sp+104] = r0
    r4 = 0
    h[sp+108] = r4
    r0 = sp + 104
    if (r7 > 1999) goto L02016fc4
    r0 = r7 * 0x1E0
    r1 = 2000
    r0 = r0 / r1 (u)
    r1 = r0 + -480
    r0 = sp + 104
    r2 = 10
    call meter_curves_peak_hold
    goto L02016fec
L02016cae:
    if (r3 == 0) goto L02016146
    if (r5 < 160) goto L02016cc2
    r2 = r1 + 60
    if (r2 <= r5) goto L02017570
L02016cc2:
    r2 = 1
    r3 = 1
    if (r0 <= 39) {  ; @if.le.ri.s12
    r3 = 0
    }
    r6 = r0 - r1
    r4 = r1 - r0
    if (r1 <= r0) {
    r4 = r6
    }
    if (r4 >= 25) {  ; @if.ge.ri.s12
    r2 = 0
    }
    if (r1 > 299) goto L02017570
    if (r0 > 149) goto L02017570
    r2 &= r3
    if (r2 != 0) goto L02017570
    r3 = 320
    r2 = 0
    r4 = r1 + 30
    b[r14+r3] = r2
    if (r4 <= r5) goto L020175c8
    if (r0 > 20) goto L020175c8
    r4 = r3 + 1
    r2 = b[r14+r4] (u)
    r3 = 1
    if (r2 != 255) {  ; @if.ne.ri.s12
    r2 += 1  ; @add.ri.u5
    b[r14+r4] = r2
    } else {
    r2 = 255
    }
    goto L020175d0
L02016d20:
    r0 = sp + 191
    call footswitch_events_colour_word
    r1 = b[sp+193] (u)
    r0 = r1 + 39  #
    [sp+40] = r0
    r1 = b[sp+192] (u)
    r2 = 40
    r3 = b[sp+191] (u)
    r0 = r0 / r2 (u)
    r0 = r1 + 39  #
    [sp+36] = r0
    r0 = r0 / r2 (u)
    r0 = r3 + 39  #
    [sp+28] = r0
    r0 = r0 / r2 (u)
    r0 = 300  #
    [sp+24] = r0
    r14 = r11 / r0 (u)
    r8 = sp + 224
    r12 = 2422
    r6 = 0
    goto L02016f8c
L02016d6a:
    r0 = 2423
    r0 = b[r13+r0] (u)
    r1 = b[r13+75] (u)
    r0 >>= r6
    r5 = r0 & 0x1
    if (r1 != 1) goto L02016dec
    r0 = 0
    r0 = r6  #
    [sp+220] = r0
    r1 = sp + 220
    call panel_inputs_switch_effect
    r1 = [sp+220]
    r2 = r1 + -1
    if (r2 >= 39) {  ; @if.ge.ri.s12
    r1 = 0
    }
    r1 = r1 * 0x3
    r1 += r15
    r2 = 10618
    r2 = b[++r1=r2] (u)
    r3 = b[r1+1] (u)
    r2 = r2 << 1
    r1 = b[r1+2] (u)
    b[sp+224] = r2
    r2 = r3 << 1
    b[r8+1] = r2
    r1 = r1 << 1
    b[r8+2] = r1
    if (r5 == 0) goto L02016ddc
    r1 = r6 * 0x3
    r1 += r13
    r1 = r1 + 2424
    r2 = b[r1+2] (u)
    r3 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    b[sp+226] = r2
    r1 <= insert(r3, p:8, l:24)
    h[sp+224] = r1
L02016ddc:
    r9 = 0
    r1 = 0
    r3 = 0
    if ((r14 & 1) == 0) goto L02016e7a
    ifs (r0 >= 1) goto L02016e6e
    goto L02016e7a
L02016dec:
    r0 = b[r13+76] (u)
    r1 = [sp+40]
    if (r1 == 0) goto L02016e16
    r1 = b[sp+193] (u)
    r2 = b[sp+192] (u)
    r3 = b[sp+191] (u)
    b[sp+226] = r1
    r3 <= insert(r2, p:8, l:24)
    h[sp+224] = r3
    r7 = [sp+36]
    r4 = [sp+28]
    r10 = [sp+24]  ; @ld.w.sp.l
    goto L02016e30
L02016e16:
    r1 = 255
    b[sp+224] = r1
    r1 = 180
    b[r8+1] = r1
    r1 = 50
    b[r8+2] = r1
    r10 = 5
    r4 = 3
    r7 = 1
L02016e30:
    if (r5 == 0) goto L02016e56
    r1 = r6 * 0x3
    r1 += r13
    r1 = r1 + 2424
    r2 = b[r1+2] (u)
    r3 = b[r1+1] (u)
    r5 = b[r1+0] (u)
    r5 <= insert(r3, p:8, l:24)  #
    r7 = b[r1+14] (u)
    r4 = b[r1+13] (u)
    r10 = b[r1+12] (u)
    b[sp+226] = r2
    h[sp+224] = r5
L02016e56:
    r1 = b[r13+77] (u)
    r9 = 0
    if (r1 == 0) goto L02016e64
    r1 = 0
    r3 = 0
    goto L02016e7a
L02016e64:
; HyperRig MINI, product option: the light of the current preset.
.if MINI_PRODUCT
    r0 = r0 * 0x3
    r0 += r6  #  ; @add.rr.p
.else
    r0 = r0 << 2
    r0 += r6  #  ; @add.rr.p
.endif
    r1 = [sp+32]
    if (r0 != r1) goto L02016f78
L02016e6e:
    r9 = b[r8+2] (u)
    r1 = b[r8+1] (u)
    r3 = b[sp+224] (u)
L02016e7a:
    r0 = r6 + r15
    r0 = b[r0+202] (u)
    r10 = r0 * 0x3
    r0 = sp + 119
    r2 = r0 + r10
    r0 = 0
    goto L02016e9e
L02016e90:
    r4 = r2
    b[++r4=r0] = r3
    b[r4+1] = r1
    b[r4+2] = r9
    r0 += 3  ; @add.ri.u5
L02016e9e:
    if (r0 != 9) goto L02016e90
    r0 = b[r13+r12] (u)
    if ((r0 & 16) == 0) goto L02016ec8
    r0 = L01c26888
    r0 = b[r6+r0] (u)
    if (r0 == 1) {  ; @if.eq.ri.s12
    r0 = r13 + 1672
    r0 = h[r0+r6<<1] (u)
    r1 = r15 + 44
    call colour_frames_bar_fill
    }
L02016ec8:
    r0 = L01c1f180
    r0 = b[r0+13] (s)
    if (r0 != r6) goto L02016f1e
    r0 = [r13+920]
    r0 = r11 - r0
    if (r0 > 1199) goto L02016f1e
    r1 = 70
    r0 = r0 / r1 (u)
    r4 = 0
    r1 = 255
    if ((r0 & 0x1) == 0) {
    r1 = 0
    }
    r2 = sp + 119
    r5 = r2 + r10
    r7 = r0 & 0x1
    goto L02016f18
L02016f00:
    r3 = b[r13+49] (u)
    r0 = r5 + r4
    r2 = 255
    if (r3 != 0) goto L02016f0c
    r2 = r3
L02016f0c:
    if (r7 != 0) goto L02016f10
    r2 = r7
L02016f10:
    r3 = r2
    call colour_frames_triplet_set
    r4 += 3  ; @add.ri.u5
L02016f18:
    if (r4 != 9) goto L02016f00
    goto L02016f74
L02016f1e:
    r0 = r6 + r13
    r1 = 924
    r1 = b[r0+r1] (u)
    if (r1 == 0) goto L02016f74
    r1 = r13 + 1812
    r1 = [r1+r6<<2]
    r1 = r11 - r1
    if (r1 > 119) goto L02016f6a
    r2 = r15 + 47
    r0 = sp + 217
    r1 = sp + 224
    r3 = 64
    call triplet_helpers_blend_triplets
    r0 = sp + 119
    r4 = r0 + r10
    r5 = 0
    goto L02016f64
L02016f58:
    r0 = r4 + r5
    r1 = sp + 217
    call triplet_helpers_brighter_triplet
    r5 += 3  ; @add.ri.u5
L02016f64:
    if (r5 != 9) goto L02016f58
    goto L02016f74
L02016f6a:
    r1 = 0
    r2 = 924
    b[r0+r2] = r1
L02016f74:
    r6 += 1  ; @add.ri.u5
    goto L02016f8c
L02016f78:
    call preset_storage_available
    r1 = 0
    r3 = 0
    if (r0 == 0) goto L02016e7a
    r9 = r7
    r1 = r4
    r3 = r10
    goto L02016e7a
L02016f8c:
    if (r6 != 4) goto L02016d6a
    r14 = L01c1f180
    r0 = b[r14+13] (s)
    ifs (r0 <= -1) goto L02016fb2
    r0 = [r13+920]
    r0 = r11 - r0
    if (r0 >= 1200) {  ; @if.ge.ri.s12
    r0 = 255
    b[r14+13] = r0
    }
L02016fb2:
    r8 = 1
    goto L02016ff6
L02016fb8:
    r3 = sp + 119
    r0 = 1
    r1 = r5
    call colour_frames_ring_strobe
    goto L02016ff4
L02016fc4:
    r5 = r0 | 0x2
    r0 = sp + 104
    r1 = -1440
    r2 = 10
    r6 = 10
    call meter_curves_peak_hold
    r0 = r7 * 0x3
    r0 = r0 + -6000
    r0 = r0 / r6 (u)
    r0 = 0x0 - r0
    h[sp+104] = r0
    h[r5+0] = r4
L02016fec:
    r0 = sp + 104
    r1 = sp + 119
L02016ff0:
    call colour_frames_meter_ring
L02016ff4:
    r8 = 0
L02016ff6:
    r0 = 892
    r1 = b[r13+r0] (u)
    r0 = 0
    if (r1 == 0) goto L02017062
    r0 = [sp+20]
    if ((r0 & 1) == 0) goto L02017014
    r0 = [r13+896]
    r0 = r11 - r0
    if (r0 <= 599) goto L02017020
L02017014:
    r1 = 892
    r0 = 0
    b[r13+r1] = r0
    goto L02017062
L02017020:
    r0 = r0 << 12
    r1 = 600
    r5 = r0 / r1 (u)
    r6 = 0
    goto L02017056
L0201702e:
    if (r5 > 1023) goto L02017050
    r1 = r13 + 92
    r0 = r5 >> 2
    r2 = 0x100 - r0
    r4 = sp + 191
    r0 = r4
    call triplet_helpers_scale_triplet
    r0 = sp + 119
    r0 += r6  ; @add.rr
    r1 = r4
    call triplet_helpers_brighter_triplet
L02017050:
    r5 = r5 + -256
    r6 += 3  ; @add.ri.u5
L02017056:
    if (r6 != 36) goto L0201702e
    r0 = 892
    r0 = b[r13+r0] (u)
L02017062:
    if ((r0 & 1) != 0) goto L0201707e
    r0 = 912
    r0 = b[r13+r0] (u)
    r0 ^= 1
    if ((r0 & 0x1) == 0) {
    r0 = 908
    r1 = 0
    b[r13+r0] = r1
    }
L0201707e:
    r0 = 2421
    r4 = b[r13+r0] (u)
    r0 = 318
    r0 = [r13+r0<<2]
    r1 = 936
    r2 = b[r13+r1] (u)
    if (r2 == 0) goto L020170b2
    r1 = [r13+940]
    if (r0 == r1) goto L020170bc
    [r13+940] = r0
    r0 = 2
    b[r13+45] = r0
    [r13+844] = r11
    r1 = r11
    goto L020170c6
L020170b2:
    [r13+940] = r0
    r0 = 1
    b[r13+r1] = r0
L020170bc:
    r0 = b[r13+45] (u)
    if (r0 == 0) goto L0201710c
    r1 = [r13+844]
L020170c6:
    r1 = r11 - r1
    if (r1 > 1499) goto L0201710c
    r1 = 0
    r2 = 1
    if (r0 != 2) {  ; @if.ne.ri.s12
    r2 = 0
    }
    r3 = 125
    r3 = r11 / r3 (u)
    r3 = r3 & 0x1
    r2 &= r3
    r2 = 0x0 - r2
    if (r0 != 1) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r0 &= r3
    r0 = 0x0 - r0
    r3 = 0
    goto L02017106
L020170fa:
    r4 = sp + 119
    b[++r4=r1] = r0
    b[r4+1] = r2
    b[r4+2] = r3
    r1 += 3  ; @add.ri.u5
L02017106:
    if (r1 != 36) goto L020170fa
    goto L020171dc
L0201710c:
    r0 = 0
    b[r13+45] = r0
    call console_helpers_key_left_locked
    if (r0 == 0) goto L02017158
    r0 = 1200
    r0 = r11 / r0 (u)
    r0 = r0 * 0x4B0
    r0 = r11 - r0
    r1 = 0x4B0 - r0
    if (r0 >= 600) {  ; @if.ge.ri.s12
    r0 = r1
    }
    r0 = r0 * 0xD7
    r1 = 600
    r0 = r0 / r1 (u)
    r0 += 40
    r1 = 0
    r2 = 0
    goto L02017152
L02017146:
    r3 = sp + 119
    b[++r3=r2] = r1
    b[r3+1] = r1
    b[r3+2] = r0
    r2 += 3  ; @add.ri.u5
L02017152:
    if (r2 != 36) goto L02017146
    goto L020171dc
L02017158:
    if (r8 == 0) goto L020171b6
    r0 = 2422
    r0 = b[r13+r0] (u)
    if ((r0 & 64) == 0) goto L020171b6
    r0 = [r13+812]
    r1 = 2449
    r1 = b[r13+r1] (u)
    r0 = r11 - r0
    r1 = r1 * 0x3E8
    if (r0 <= r1) goto L020171b6
    r0 = 4000
    r0 = r11 / r0 (u)
    r0 = r0 * 0xFA0
    r0 = r11 - r0
    r1 = 0xFA0 - r0
    if (r0 >= 2000) {  ; @if.ge.ri.s12
    r0 = r1
    }
    r0 *= r0
    r1 = 2000
    r0 = r0 / r1 (u)
    r0 = r0 * 0x4B
    r0 = r0 / r1 (u)
    r0 += 25  ; @add.ri.u5
    r0 *= r4
    r1 = 100
    r4 = r0 / r1 (u)
L020171b6:
    if (r4 > 99) goto L020171dc
    r3 = 0
    r5 = sp + 119
    goto L020171d8
L020171c0:
    r6 = 3
    r7 = r5
    goto L020171d2
L020171c6:
    r1 = r4  #
    r0 = b[r7+0] (u)
    call triplet_helpers_percent_of
    b[r7++=1] = r0
    r6 += -1
L020171d2:
    if (r6 != 0) goto L020171c6
    r5 += 3  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L020171d8:
    if (r3 != 12) goto L020171c0
L020171dc:
    r4 = 0
    r5 = sp + 119
    goto L020171f2
L020171e2:
    r0 = r4  #
    r3 = b[r5+2] (u)
    r2 = b[r5+1] (u)
    r1 = b[r5++=3] (u)
    call triplet_helpers_store_slot
    r4 += 1  ; @add.ri.u5
L020171f2:
    if (r4 != 12) goto L020171e2
L020171f6:
    r0 = 876
    r0 = b[r13+r0] (u)
    if (r0 == 0) goto L02017210
    call colour_frames_led_send
    if (r0 != 0) goto L02017210
    r0 = 876
    r1 = 0
    b[r13+r0] = r1
L02017210:
    r0 = 0
    r1 = -36
    goto L0201722e
L02017218:
    r2 = r1 + r13
    r2 = r2 + 2560
    r3 = b[r2+0] (u)
    r0 += r3  #  ; @add.rr.p
    r4 = b[r2+1] (u)
    r0 += r4  #  ; @add.rr.p
    r2 = b[r2+2] (u)
    r0 += r2  ; @add.rr
    r1 += 3  ; @add.ri.u5
L0201722e:
    if (r1 != 0) goto L02017218
    r1 = r13 + 856
    [r1+4] += r0
    [r1+0] += 1  ; @rmw.add.s12
    r0 = b[r13+60] (u)
    r8 = 0
    r1 = 0
    if (r0 == 0) goto L02017262
    r0 = 1536
    r0 = b[r13+r0] (u)
    r0 ^= 1
    if ((r0 & 1) == 0) goto L02017262
    r0 = h[r13+82] (u)
    if (r0 == 0) goto L02017260
    call control_actions_clock
    goto L0201726c
L02017260:
    r1 = 1
L02017262:
    call control_actions_clock
    if (r1 == 0) goto L02017270
    if ((r0 & 512) == 0) goto L02017270
L0201726c:
    r8 = 0x2000000
L02017270:
    r0 = b[r13+41] (u)
    if (r0 == 0) goto L02017296
    r1 = b[r13+47] (u)
    r0 = 0x6D0000
    if (r1 != 0) goto L02017284
    r0 = 0x770000
L02017284:
    r1 = [r14+136]
    r0 = r0 | r8
    r0 |= 134217728
    if (r0 != r1) goto L02017568
    goto L0201756c
L02017296:
    r0 = b[r13+52] (u)
    r3 = -1
    if (r0 == 0) goto L020172be
    r0 = 1068
    r0 = b[r13+r0] (u)
    if ((r0 & 1) == 0) goto L020172be
    r0 = 291
    r0 = [r13+r0<<2]
    r1 = 12
    r1 = r0 / r1 (s)
    r1 = r1 * 0xC
    r3 = r0 - r1
L020172be:
    r0 = b[r13+52] (u)
    if (r0 == 0) goto L02017322
    r0 = sp + 228
    call triplet_helpers_active_flag
    r7 = 0x10400000
    ifs (r3 < 0) goto L02017532
    if (r0 == 0) goto L02017532
    r1 = 14000  #
    r0 = [sp+228]
    r0 = r0 * 0x1C
    r0 += r1  ; @add.rr
    r1 = 1000
    r1 = r0 / r1 (s)
    ifs (r1 >= 28) {  ; @ifs.ge.ri.s12
    r1 = 28
    }
    r2 = 0
    ifs (r0 >= -999) {
    r2 = r1
    }
    r0 = r2 >>> 1
    r1 = r2 << 1
    r2 = r3 + r15
    r3 = 1796
    r2 = b[r2+r3] (u)
    r1 = r1 & 0x2
    r1 |= 1
    r0 = r1 << r0
    r1 = r2 << 16
    r0 |= r1
    r7 = r0 | 0x10000000
    goto L02017532
L02017322:
    r0 = b[r13+74] (u)
    if (r0 == 0) goto L02017450
    r11_r10 = 0
    r7_r6 = 0
    r9 = 0
    r12 = 0
    goto L020173b2
L02017334:
    r1 = sp + 50
    r0 = r12
    call preset_application_chain_read  ; @call.xl
    r5 = r0
    r4 = 0
    goto L020173aa
L02017344:
    r0 = sp + 50
    r0 = b[r0+r4] (u)
    call preset_application_effect_enabled  ; @call.xl
    if (r0 == 0) goto L02017394
    r0 = sp + 50
    r0 = b[r0+r4] (u)
    call preset_application_effect_type  ; @call.xl
    r0 += -1
    if (r0 > 38) goto L02017394
    tbb [r0]
control_scan_effect_types:
    .byte (L02017398 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L0201739e - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L020173a4 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2
    .byte (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2
    .byte (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2
    .byte (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2
    .byte (L0201738e - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2, (L0201738e - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017394 - control_scan_effect_types) / 2, (L02017392 - control_scan_effect_types) / 2
    .byte 0x00  ; alignment
L0201738e:
    r7 = 1
    goto L02017394
L02017392:
    r6 = 1
L02017394:
    r4 += 1  ; @add.ri.u5
    goto L020173aa
L02017398:
    r9 = 1
    goto L02017394
L0201739e:
    r10 = 1
    goto L02017394
L020173a4:
    r11 = 1
    goto L02017394
L020173aa:
    ifs (r4 < r5) goto L02017344
    r12 = r12 + 1
L020173b2:
    if (r12 != 2) goto L02017334
    if (r11 != 0) {  ; @if.ne.ri.s12
    r2 = 134217731
    } else {
    r2 = 134217729
    }
    r0 = r2 | 0xC
    if (r7 == 0) goto L020173ce
    r2 = r0
L020173ce:
    r0 = r2 | 0x30
    if (r10 != 0) {  ; @if.ne.ri.s12
    r2 = r0
    }
    r0 = r2 | 0xC0
    if (r6 == 0) goto L020173e0
    r2 = r0
L020173e0:
    r3 = r2 | 0x3F00
    r4 = r14 + 236
    call status_helpers_flags_set
    r1 = 0
    goto L02017402
L020173f0:
    r5 = b[r4++=3] (u)
    r5 += -2
    r6 = r5.b0 (u)
    r5 = 1
    if (r6 >= 3) {  ; @if.ge.ri.s12
    r5 = r1
    }
    r1 = r5
L02017402:
    r5 = r14 + 272
    if (r4 < r5) goto L020173f0
    if (r0 == 0) goto L0201740e
    r2 = r3
L0201740e:
    r0 = r2 | 0x4000
    if (r9 != 0) {  ; @if.ne.ri.s12
    r2 = r0
    }
    r0 = [r14+88]
    r4 = r0 + 1
    if (r0 >= 9) {  ; @if.ge.ri.s12
    r4 = 0
    }
    r0 = [r14+92]
; HyperRig MINI, product option: the bank shown.
.if MINI_PRODUCT
    r3 = 3
    r3 = r0 / r3 (u)
    r3 += 1
.else
    r3 = r0 >>> 2
    r3 += 1  ; @add.ri.u5
.endif
    if (r0 >= 32) {  ; @if.ge.ri.s12
    r3 = 0
    }
    call control_actions_clock
    if (r1 == 0) goto L02017464
    if (r3 != 0) goto L0201743c
    r3 = r4
L0201743c:
    if (r4 == 0) goto L0201746a
    r1 = [r13+900]
    r0 = r0 - r1
    if (r0 >= 1500) goto L0201746a
    r3 = r4 | 0x80
    goto L0201746c
L02017450:
    call control_actions_clock
    r1 = b[r13+77] (u)
    r9 = r0
    if (r1 == 0) goto L0201748e
    r7 = 134217729
    goto L020174f0
L02017464:
    if (r4 != 0) goto L02017468
    r4 = r3
L02017468:
    r3 = r4
L0201746a:
    if (r3 == 0) goto L02017484
L0201746c:
    r0 = r3 & 0xF
    r0 += r15
    r1 = 1443
    r0 = b[r0+r1] (u)
    r1 = r3 & 0x80
    r0 |= r1
    r0 = r0 << 16
    goto L02017488
L02017484:
    r0 = 0x400000
L02017488:
    r7 = r0 | r2
    goto L02017532
L0201748e:
    r0 = 10336
    r6 = r13 + r0
    r0 = 200
    r10 = r9 / r0 (u)
    r12 = sp + 232
    r7 = 134217729
    r4 = 0
    r11 = 2615
    goto L020174ea
L020174ae:
    r4 = r5 + 1
    r1 = sp + 232
    r0 = r4
    call tuner_and_control_records_control_record
    r1 = b[r13+75] (u)
    if (r1 != 1) goto L020174d4
    if (r0 == 0) goto L020174e8
    r0 = b[r12+4] (u)
    if (r0 == 0) goto L020174e8
    if ((r10 & 1) != 0) goto L020174dc
    r0 = b[r6+0] (u)
    if (r0 == 0) goto L020174e8
    goto L020174dc
L020174d4:
    if (r0 == 0) goto L020174e8
    r0 = b[r12+4] (u)
    if (r0 == 0) goto L020174e8
L020174dc:
    r0 = r5 + r15
    r0 = b[r0+r11] (u)
    r7 = r7 | (1 << r0)
L020174e8:
    r6 += 40
L020174ea:
    r5 = r4
    if (r5 != 14) goto L020174ae
L020174f0:
    r2 = b[r13+76] (u)
    r0 = [r14+92]
    r3 = b[r13+75] (u)
    ifs (r0 < 0) goto L02017516
    if (r3 != 0) goto L02017516
    call footswitch_events_bank_of
    if (r2 == r0) goto L02017516
    r0 = 300
    r0 = r9 / r0 (u)
    if ((r0 & 1) != 0) goto L02017532
L02017516:
    r0 = 1
    if (r3 != 1) {  ; @if.ne.ri.s12
    r0 = 0
    }
    r1 = r2 + r15
    r2 = 1444
    r1 = b[r1+r2] (u)
    r0 = r0 << 7
    r0 |= r1
    r0 = r0 << 16
    r7 |= r0
L02017532:
    r0 = b[r13+52] (u)
    if (r0 != 0) goto L0201755c
    call console_helpers_key_left_locked
    if (r0 == 0) goto L0201755c
    call control_actions_clock
    r1 = 400
    r1 = r0 / r1 (u)
    r0 = 0x730000
    if ((r1 & 0x1) == 0) {
    r0 = 0
    }
    r1 = r7 & 0xFF00FFFF
    r7 = r0 | r1
L0201755c:
    r1 = [r14+136]
    r0 = r7 | r8
    if (r0 == r1) goto L0201756c
L02017568:
    call flash_helpers_shift_out
L0201756c:
    sp += 244
    {pc, r15-r4} = [sp++]
L02017570:
    r2 = 321
    r3 = 0
    b[r14+r2] = r3
    r2 += -1
    r4 = b[r14+r2] (u)
    if (r4 == 255) goto L020175c4
    r3 = r4 + 1
    b[r14+r2] = r3
    r4 = r3.b0 (u)
    r2 = 0
    r3 = 1
    if (r4 >= 2) {  ; @if.ge.ri.s12
    r3 = 0
    }
    goto L020175d0
L02017598:
    r0 = cnum
    r1 = [r6+r0<<2]
    r2 = r7 & 0x40
    r1 += -1
    [r6+r0<<2] = r1
    r0 = r2 >> 6
    if (r1 != 0) goto L020175b6
    csync
    r1 = 0
    b[r8+0] = r1
L020175b6:
    r3 = r0 ^ 0x1
    call storage_coordination_irq_leave  ; @call.xl
    goto L02016122
L020175c4:
    r2 = 0
    goto L020175d0
L020175c8:
    r3 += 1  ; @add.ri.u5
    b[r14+r3] = r2
    r3 = 1
L020175d0:
    r4 = 1023
    r1 &= r4
    r4 = r5 << 20
    r5 = 1072693248
    r4 &= r5
    r1 |= r4
    r0 = r0 << 10
    r4 = 324
    r4 = b[r14+r4] (u)
    r5 = 1047552
    r0 &= r5
    r1 |= r0
    if (r3 != 0) goto L02017616
    r0 = 323
    r0 = b[r14+r0] (u)
    if (r0 != 0) goto L02017616
    if (r4 == 1) goto L02017616
    r0 = 1
    r2 = r14 + 312
    b[r2+12] = r0
L0201760e:
    b[r2+13] = r0
    [r2+0] = r1
    goto L0201614c
L02017616:
    r2 = r2.b0 (u)
    r0 = 0
    if (r2 < 2) goto L0201614c
    r2 = 323
    b[r14+r2] = r0
    if (r4 != 1) goto L0201614c
    r2 = r14 + 312
    b[r2+12] = r0
    r0 = 1
    goto L0201760e
L02017638:
    r5_r4 = 0
    ifs (r7 > -42) goto L0201764c
    r4 = -6
    r4 *= r3
    r6 += r4  ; @add.rr
    r4 = 1
    ifs (r6 <= 29) {  ; @ifs.le.ri.s12
    r4 = 0
    }
L0201764c:
    r6 = 324
    r6 = b[r14+r6] (u)
    r0 = r0 << 10
    r0 |= r2
    r2 = r3 << 20
    r2 |= r0
    if (r6 == 2) goto L0201767e
    if (r6 != 0) goto L020176bc
    r0 = 0
    if (r5 == 0) goto L02015fe6
    r0 = 2
    r3 = r14 + 312
    b[r3+12] = r0
    b[r3+13] = r0
    h[r3+4] = r1
    [r3+0] = r2
    r0 = 1
    goto L02015fe6
L0201767e:
    r0 = h[r14+316] (u)
    if (r1 > r0) {
    h[r14+316] = r1
    r0 = r1
    }
    r5 = r0.l (u)
    r6 = r5 - r1
    r1_r0 = 0
    ifs (r6 < 14) goto L020176a2
    r1 = r3 << 1
    r3 = r5 - r1
    r1 = 1
    ifs (r3 <= 9) {  ; @ifs.le.ri.s12
    r1 = 0
    }
L020176a2:
    r1 |= r4
    if (r1 != 1) goto L02015fe6
    r1 = r14 + 312
    b[r1+12] = r0
    r0 = 2
    b[r1+13] = r0
    [r1+0] = r2
    r0 = 1
    goto L02015fe6
L020176bc:
    r0 = 0
    if (r4 == 0) goto L02015fe6
    r1 = r14 + 312
    b[r1+12] = r0
    r0 = 1
    b[r1+11] = r0
    r3 = 2
    b[r1+13] = r3
    [r1+0] = r2
    goto L02015fe6
