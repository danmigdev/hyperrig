; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.


; 0x0204bba8..0x0204bbb0: data
    .fill ((8 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204bba8:
    .byte 0x44,0x32,0x41,0x43
    .long L0204ad94

; 0x0204bbb0..0x0204be96: system layer code (not reversed), as instructions
L0204bbb0:
    r2 = L01c214c4
    r1 = r0
    r0 = r2
    goto L0204bbc8
L0204bbbc:
    r3 = [r0+236]
    if (r3 == r1) goto L0204bbd2
    r0 = r0 + 296
L0204bbc8:
    r3 = r2 + 592
    if (r0 < r3) goto L0204bbbc
    r0 = 0
L0204bbd2:
    rts
L0204bbd4:
    [--sp] = {rets, r9-r4}
    r5 = r0
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L0204bc04
    csync
L0204bbfc:
    testset b[r8]
    ifeq goto L0204bbfc
    csync
L0204bc04:
    r6 = L01c214c4
    r4 = r6
    goto L0204bc30
L0204bc0e:
    r0 = h[r4+228] (u)
    r7 = r4 + 196
    if (r0 == 0) goto L0204bc2c
    r0 = [r7+40]
    if (r0 == 0) goto L0204bc2c
    if (r5 == 0) goto L0204bc5a
    r0 = r7 + 1
    r2 = 6
    r1 = r5
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204bc6e
L0204bc2c:
    r4 = r7 + 100
L0204bc30:
    r0 = r6 + 592
    if (r4 < r0) goto L0204bc0e
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204bc50
    csync
    r0 = 0
    b[r8+0] = r0
L0204bc50:
    call storage_coordination_irq_leave  ; @call.xl
    r4 = 0
    goto L0204bc8c
L0204bc5a:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204bc86
    csync
    goto L0204bc80
L0204bc6e:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204bc86
    csync
L0204bc80:
    r0 = 0
    b[r8+0] = r0
L0204bc86:
    call storage_coordination_irq_leave  ; @call.xl
L0204bc8c:
    r0 = r4
    {pc, r9-r4} = [sp++]
L0204bc90:
    [--sp] = {rets, r6-r4}
    r4 = r0 + 28
    r5 = L01c267e0
L0204bc9a:
    r0 = 0
    r1 = r4
    call phase3_p10_lbuf_alloc  ; @call.xl
    r6 = r0
    if (r6 != 0) goto L0204bcca
    call L01c00e62  ; @call.xl
    r6 = 0
    if (r0 != 0) goto L0204bcd8
    r0 = icfg
    if ((r0 & 0xFF) != 0) goto L0204bcd8
    r1 = 0
    r0 = r5
    call L02040d34  ; @call.xl
    if (r0 == 0) goto L0204bc9a
    goto L0204bcd8
L0204bcca:
    r0 = 0
    r1 = r6
    rep 7 {
    [r1++=4] = r0
    }
    r0 = r6 + 16
    [r6+16] = r0
    [r6+20] = r0
L0204bcd8:
    r0 = r6
    {pc, r6-r4} = [sp++]
L0204bcdc:
    [--sp] = {rets, r6-r4}
    r1 = b[r0+4] (u)
    r4 = r0 - r1  #
    r5 = h[r0+2] (u)
    r0 = rets
    r0 = r4
    call L020269bc  ; @call.xl
    r0 = r4  #
    r6 = [r4+-20]
    call L02026a0c  ; @call.xl
    if (r0 == 0) goto L0204bd18
    r0 = r5 >> 6
    r0 = r0 & 0x4
    r1 = L01c267d8
    r0 += r1  ; @add.rr
    r1 = h[r0+2] (u)
    r1 = r1 - r6
    r2 = r1.l (s)
    ifs (r2 <= 0) {  ; @ifs.le.ri.s12
    r1 = 0
    }
    h[r0+2] = r1
L0204bd18:
    {pc, r6-r4} = [sp++]
L0204bd1a:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = rets
    r0 = r4
    call L020269bc  ; @call.xl
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r2 = [r1+r0<<2]
    r3 = r2 + 1
    [r1+r0<<2] = r3
    r0 = L01c1fa20
    if (r2 != 0) goto L0204bd56
    csync
L0204bd4e:
    testset b[r0]
    ifeq goto L0204bd4e
    csync
L0204bd56:
    r3_r2 = d[r4+16]
    [r2+4] = r3
    [r3+0] = r2
    r2 = cnum
    r3 = [r1+r2<<2]
    r3 += -1
    [r1+r2<<2] = r3
    if (r3 != 0) goto L0204bd74
    csync
    r1 = 0
    b[r0+0] = r1
L0204bd74:
    call storage_coordination_irq_leave  ; @call.xl
    r1 = b[r4+8] (u)
    if (r1 == 0) goto L0204bd8a
    r0 = r4 + r1
    r2 = b[r0+4] (u)
    if (r1 != r2) goto L0204bda6
    call L0204bcdc
    {pc, r4} = [sp++]
L0204bd8a:
    r0 = b[r4+5] (u)
    if ((r0 & 32) != 0) goto L0204bda4
    r0 = r4
    call L02026a0c  ; @call.xl
    r0 = L01c267e0
    call L020403ee  ; @call.xl
L0204bda4:
    {pc, r4} = [sp++]
L0204bda6:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204bdb2:
    goto L0204bdb2
L0204bdb4:
    r1 = r0
    r3 = [r1+0]
    r2 = r3 + -16
    r0 = 0
    if (r3 != r1) {
    r0 = r2
    }
    rts
L0204bdc6:
    [--sp] = {rets, r12-r4}
    r3 = r0 + -32
    r2 = [r3+0]
    r8 = 305419896
    if (r2 != r8) goto L0204be88
    r9 = r8 + 0x11111111  #
    r2 = [r3+24]
    if (r2 != r9) goto L0204be88
    r2 = [r3+16]
    r5 = r3 - r2
    r2 = [r5+0]
    r4 = 2271560481
    if (r2 != r4) goto L0204be88
    r4 = r4 + 0x11111111  #
    r2 = [r5+36]
    if (r2 != r4) goto L0204be88
    r7 = b[r5+21] (u)
    r2 = r1 + 28
    r4 = r7 + -1
    r1 = r4 & r2
    r1 = r7 - r1
    r6 = 0
    if ((r4 & r2) != 0) {
    r6 = r1
    }
    r6 += r2  #  ; @add.rr.p
    r1 = [r3+12]
    if (r1 < r6) goto L0204be88
    if (r1 <= r6) goto L0204be86
    r4 = 131071
    r4 += r7  #  ; @add.rr.p
    r2 = h[r5+22] (u)
    r11 = r2 + 32
    r2 = r4 & r11
    r10 = r7 - r2
    r12 = 0
    if ((r4 & r11) != 0) {
    r12 = r10
    }
    r4 = r1 - r6
    if (r4 < 12) goto L0204be86
    r2 = r11 + r12
    r7 = r2 << 1
    if (r4 < r7) goto L0204be86
    r2 += r6  ; @add.rr
    [r3+12] = r2
    r2 = h[r5+22] (u)
    r0 += r2  ; @add.rr
    r0 += r6  ; @add.rr
    r0 += r12
    r2 = 0
    b[r0+21] = r2
    r2 = 1
    b[r0+20] = r2
    r2 = [r3+12]
    r1 = r1 - r2
    r1 = r0 - r5  #
    [r0+12] = r1
    [r0+16] = r1
    [r0+0] = r8
    [r0+24] = r9
    r1 = r0 + 4
    [r0+4] = r1
    [r0+8] = r1
    r0 += 32
    call L02026a0c  ; @call.xl
L0204be86:
    {pc, r12-r4} = [sp++]
L0204be88:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204be94:
    goto L0204be94

; 0x0204be96..0x0204c3ac: data
    .fill ((22 - (. - ultrarig_flash_start)) & 31), 1, 0  ; keeps the original address modulo 32
L0204be96:
    .byte 0x00,0x00,0x0f,0x00,0x00,0x00
    .long phase3_p12_bt_stub_26bf8
    .long phase3_p12_bt_stub_26bfc
    .long phase3_p12_bt_stub_26c00
    .long phase3_p12_bt_stub_26c04
    .long phase3_p12_bt_stub_26c08
    .byte 0x00,0x00,0x00,0x00
    .long phase3_p12_bt_stub_26bf8
    .long phase3_p12_bt_stub_26bfc
    .long phase3_p12_bt_stub_26c00
    .long phase3_p12_bt_stub_26c04
    .long phase3_p12_bt_stub_26c08
L0204bec8:
    .byte 0x00,0x00,0x00,0x00
    .long L020502a0
    .long L020502b0
    .long L020502e4
    .long L020502e8
    .long L020502e8
    .byte 0x02,0x00,0x00,0x00
    .long L020502a0
    .long L020502b0
    .long L020502e4
    .long L020502e8
    .long L020502e8
L0204bef8:
    .byte 0x01,0x00,0x00,0x00
    .long L020501ee
    .long L0205020a
    .long L0205020c
    .byte 0x00,0x00,0x00,0x00
    .long L0205029a
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long phase3_p12_bt_stub_26c0c
    .long phase3_p12_bt_stub_26c10
    .long phase3_p12_bt_stub_26c12
    .long phase3_p12_bt_stub_26c14
    .long phase3_p12_bt_stub_26c16
    .long phase3_p12_bt_stub_26c18
    .byte 0x01,0x00,0x00,0x00
    .long L02050eb8
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02050ef4
    .long L02050f0c
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02050da6
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02050e8c
    .long L02050ea2
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x00,0x01,0x00
    .long L0204c2e0
    .byte 0x00,0x00,0x00,0x00,0x02,0x00,0x01,0x00
    .long L0204c32f
    .long L020501cc
    .long L020501d0
    .long L020501d4
    .long L02050332
    .long L02050336
    .long L0205033a
    .long L020513b2
    .long L020513b6
    .long L020513ba
    .long L020513be
    .long L020513c2
    .long L020513c6
    .long L020513ca
    .long L020513ce
    .long L020513d2
    .long L0205140c
    .long L02051410
    .long L02051414
    .long L0205148a
    .long L0205148e
    .long L02051492
    .long L02051496
    .long L020514ac
    .long L020514c2
    .long L02052018
    .long L0205201c
    .long L02052020
    .long phase3_p12_bt_sleep_suspend
    .long phase3_p12_bt_sleep_resume
    .long phase3_p12_bt_sleep_release
    .byte 0x00,0x00,0x00,0x00
L0204bffc:
    .byte 0x00,0x00,0x10,0x00,0x80,0x00,0x00,0x80,0x5f,0x9b,0x34,0xfb
L0204c008:
    .byte 0x00,0x00,0xc1,0xc0,0x81,0xc1,0x40,0x01,0x01,0xc3,0xc0,0x03,0x80,0x02,0x41,0xc2
    .byte 0x01,0xc6,0xc0,0x06,0x80,0x07,0x41,0xc7,0x00,0x05,0xc1,0xc5,0x81,0xc4,0x40,0x04
    .byte 0x01,0xcc,0xc0,0x0c,0x80,0x0d,0x41,0xcd,0x00,0x0f,0xc1,0xcf,0x81,0xce,0x40,0x0e
    .byte 0x00,0x0a,0xc1,0xca,0x81,0xcb,0x40,0x0b,0x01,0xc9,0xc0,0x09,0x80,0x08,0x41,0xc8
    .byte 0x01,0xd8,0xc0,0x18,0x80,0x19,0x41,0xd9,0x00,0x1b,0xc1,0xdb,0x81,0xda,0x40,0x1a
    .byte 0x00,0x1e,0xc1,0xde,0x81,0xdf,0x40,0x1f,0x01,0xdd,0xc0,0x1d,0x80,0x1c,0x41,0xdc
    .byte 0x00,0x14,0xc1,0xd4,0x81,0xd5,0x40,0x15,0x01,0xd7,0xc0,0x17,0x80,0x16,0x41,0xd6
    .byte 0x01,0xd2,0xc0,0x12,0x80,0x13,0x41,0xd3,0x00,0x11,0xc1,0xd1,0x81,0xd0,0x40,0x10
    .byte 0x01,0xf0,0xc0,0x30,0x80,0x31,0x41,0xf1,0x00,0x33,0xc1,0xf3,0x81,0xf2,0x40,0x32
    .byte 0x00,0x36,0xc1,0xf6,0x81,0xf7,0x40,0x37,0x01,0xf5,0xc0,0x35,0x80,0x34,0x41,0xf4
    .byte 0x00,0x3c,0xc1,0xfc,0x81,0xfd,0x40,0x3d,0x01,0xff,0xc0,0x3f,0x80,0x3e,0x41,0xfe
    .byte 0x01,0xfa,0xc0,0x3a,0x80,0x3b,0x41,0xfb,0x00,0x39,0xc1,0xf9,0x81,0xf8,0x40,0x38
    .byte 0x00,0x28,0xc1,0xe8,0x81,0xe9,0x40,0x29,0x01,0xeb,0xc0,0x2b,0x80,0x2a,0x41,0xea
    .byte 0x01,0xee,0xc0,0x2e,0x80,0x2f,0x41,0xef,0x00,0x2d,0xc1,0xed,0x81,0xec,0x40,0x2c
    .byte 0x01,0xe4,0xc0,0x24,0x80,0x25,0x41,0xe5,0x00,0x27,0xc1,0xe7,0x81,0xe6,0x40,0x26
    .byte 0x00,0x22,0xc1,0xe2,0x81,0xe3,0x40,0x23,0x01,0xe1,0xc0,0x21,0x80,0x20,0x41,0xe0
    .byte 0x01,0xa0,0xc0,0x60,0x80,0x61,0x41,0xa1,0x00,0x63,0xc1,0xa3,0x81,0xa2,0x40,0x62
    .byte 0x00,0x66,0xc1,0xa6,0x81,0xa7,0x40,0x67,0x01,0xa5,0xc0,0x65,0x80,0x64,0x41,0xa4
    .byte 0x00,0x6c,0xc1,0xac,0x81,0xad,0x40,0x6d,0x01,0xaf,0xc0,0x6f,0x80,0x6e,0x41,0xae
    .byte 0x01,0xaa,0xc0,0x6a,0x80,0x6b,0x41,0xab,0x00,0x69,0xc1,0xa9,0x81,0xa8,0x40,0x68
    .byte 0x00,0x78,0xc1,0xb8,0x81,0xb9,0x40,0x79,0x01,0xbb,0xc0,0x7b,0x80,0x7a,0x41,0xba
    .byte 0x01,0xbe,0xc0,0x7e,0x80,0x7f,0x41,0xbf,0x00,0x7d,0xc1,0xbd,0x81,0xbc,0x40,0x7c
    .byte 0x01,0xb4,0xc0,0x74,0x80,0x75,0x41,0xb5,0x00,0x77,0xc1,0xb7,0x81,0xb6,0x40,0x76
    .byte 0x00,0x72,0xc1,0xb2,0x81,0xb3,0x40,0x73,0x01,0xb1,0xc0,0x71,0x80,0x70,0x41,0xb0
    .byte 0x00,0x50,0xc1,0x90,0x81,0x91,0x40,0x51,0x01,0x93,0xc0,0x53,0x80,0x52,0x41,0x92
    .byte 0x01,0x96,0xc0,0x56,0x80,0x57,0x41,0x97,0x00,0x55,0xc1,0x95,0x81,0x94,0x40,0x54
    .byte 0x01,0x9c,0xc0,0x5c,0x80,0x5d,0x41,0x9d,0x00,0x5f,0xc1,0x9f,0x81,0x9e,0x40,0x5e
    .byte 0x00,0x5a,0xc1,0x9a,0x81,0x9b,0x40,0x5b,0x01,0x99,0xc0,0x59,0x80,0x58,0x41,0x98
    .byte 0x01,0x88,0xc0,0x48,0x80,0x49,0x41,0x89,0x00,0x4b,0xc1,0x8b,0x81,0x8a,0x40,0x4a
    .byte 0x00,0x4e,0xc1,0x8e,0x81,0x8f,0x40,0x4f,0x01,0x8d,0xc0,0x4d,0x80,0x4c,0x41,0x8c
    .byte 0x00,0x44,0xc1,0x84,0x81,0x85,0x40,0x45,0x01,0x87,0xc0,0x47,0x80,0x46,0x41,0x86
    .byte 0x01,0x82,0xc0,0x42,0x80,0x43,0x41,0x83,0x00,0x41,0xc1,0x81
L0204c204:
    .byte 0x81,0x80,0x40,0x40
    .long L0203a221  ; "2D"
    .long L0203a1f8  ; "22"
    .long L02035a4a  ; "2222"
    .long L0203a220  ; "22D"
    .long L0203a21f  ; "222D"
    .long L0203a1f8  ; "22"
    .long L0203a1f8  ; "22"
    .long L0203a222
    .long L0203a222
    .long L0203a1f9
    .long L0203a220  ; "22D"
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .long L02035a4a  ; "2222"
    .long L0203a1f9
    .long L0203a224  ; "22222"
    .long L0203a224  ; "22222"
    .long L0203a1f8  ; "22"
L0204c260:
    .byte 0x10,0x00,0x00,0x00
    .long L02050f24
    .byte 0x31,0x00,0x00,0x00
    .long L02051056
    .byte 0x11,0x00,0x00,0x00
    .long L02051122
    .byte 0x13,0x00,0x00,0x00
    .long L02051198
    .byte 0x30,0x00,0x00,0x00
    .long L020511b0
    .byte 0x20,0x00,0x00,0x00
    .long L020511b4
    .byte 0x14,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
L0204c2a0:
    .byte 0x10,0x01,0x00,0x00
    .long L0205122c
    .byte 0x18,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x31,0x03,0x00,0x00
    .long L020512ae
    .byte 0x50,0x00,0x00,0x00
    .long L02051364
    .byte 0x30,0x01,0x00,0x00
    .long L020513a4
    .byte 0x40,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x41,0x00,0x00,0x00,0x00,0x00,0x00,0x00
    .byte 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
L0204c2e0:
    .byte 0x36,0x00,0x4a,0x09,0x00,0x00,0x0a,0x00,0x01,0x00,0x01,0x09,0x00,0x01,0x36,0x00
    .byte 0x03,0x19,0x11,0x0b,0x09,0x00,0x04,0x36,0x00,0x12,0x36,0x00,0x06,0x19,0x01,0x00
    .byte 0x09,0x00,0x19,0x36,0x00,0x06,0x19,0x00,0x19,0x09,0x01,0x03,0x09,0x00,0x09,0x36
    .byte 0x00,0x09,0x36,0x00,0x06,0x19,0x11,0x0d,0x09,0x01,0x03,0x09,0x03,0x11,0x09,0x00
    .byte 0x01,0x09,0x01,0x00,0x25,0x07,0x4a,0x4c,0x5f,0x41,0x32,0x44,0x50,0x00,0x00
L0204c32f:
    .byte 0x36,0x00,0x41,0x09,0x00,0x00,0x0a,0x00,0x01,0x00,0x02,0x09,0x00,0x01,0x36,0x00
    .byte 0x06,0x19,0x11,0x0e,0x19,0x11,0x0f,0x09,0x00,0x04,0x36,0x00,0x12,0x36,0x00,0x06
    .byte 0x19,0x01,0x00,0x09,0x00,0x17,0x36,0x00,0x06,0x19,0x00,0x17,0x09,0x01,0x04,0x09
    .byte 0x00,0x09,0x36,0x00,0x09,0x36,0x00,0x06,0x19,0x11,0x0e,0x09,0x01,0x06,0x09,0x03
    .byte 0x11,0x09,0x00,0x01,0x00,0x00
L0204c375:
    .byte 0x00,0x00,0x00,0x00,0x00,0x00
L0204c37b:
    .byte 0x06,0x77,0x5f,0x87,0x91,0x8d,0xd4,0x23,0x00,0x5d,0xf1,0xd8,0xcf,0x0c,0x14,0x2b
    .byte 0x00
L0204c38c:
    .byte 0x00,0x00,0x21,0x10,0x42,0x20,0x63,0x30,0x84,0x40,0xa5,0x50,0xc6,0x60,0xe7,0x70
    .byte 0x08,0x81,0x29,0x91,0x4a,0xa1,0x6b,0xb1,0x8c,0xc1,0xad,0xd1,0xce,0xe1,0xef,0xf1

; 0x0204c3ac..0x0204e3c2: system layer code (not reversed), as instructions
L0204c3ac:
    [--sp] = {rets, r4}
    r1 = L01c21b24
    r1 = [r1+0]
    r2 = r1 + 96
    r1 = 0
    r3 = 0
    goto L0204c3ce
L0204c3c0:
    r4 = h[r2++=4] (u)
    r4 = r4 >> 6
    if (r4 == r0) goto L0204c3d4
    r1 += 1  ; @add.ri.u5
    r3 += 1  ; @add.ri.u5
L0204c3ce:
    ifs (r3 <= 7) goto L0204c3c0
    r1 = 255
L0204c3d4:
    r0 = r1.b0 (u)
    {pc, r4} = [sp++]
L0204c3d8:
    [--sp] = {rets, r7-r4}
    r5 = L01c21b24
    r4 = r1  #
    r6 = [r5+0]
    if (r6 == 0) goto L0204c444
    call L0204c3ac
    r2 = 20
    if (r0 <= 7) {  ; @if.le.ri.s12
    r0 = r0 << 2
    r0 += r6  ; @add.rr
    r2 = h[r0+98] (u)
    }
    call storage_coordination_irq_enter  ; @call.xl
    r1 = L01c1fa24
    r0 = cnum
    r3 = [r1+r0<<2]
    r6 = r3 + 1
    [r1+r0<<2] = r6
    r0 = L01c1fa20
    if (r3 != 0) goto L0204c422
    csync
L0204c41a:
    testset b[r0]
    ifeq goto L0204c41a
    csync
L0204c422:
    r3 = [r5+0]
    r5 = [r3+152]
    r3 = [r3+156]
    r6 = r3 - r5
    r3 = 0
    r5 = 0
    if (r6 < 7) goto L0204c45e
    r5 = r2 + 6
    r5 = r5.l (u)
    if (r6 >= r5) goto L0204c448
    r5 = r6 + -6
    goto L0204c45e
L0204c444:
    r3 = 0
    goto L0204c480
L0204c448:
    r7 = r6 / r5 (u)
    r5 *= r7
    r6 = r6 - r5
    r5 = r7 * r2
    if (r6 >= 7) {  ; @if.ge.ri.s12
    r2 = r6 + r5
    r5 = r2 + -6
    }
L0204c45e:
    r6 = cnum
    r2 = [r1+r6<<2]
    r2 += -1
    [r1+r6<<2] = r2
    if (r5 >= r4) {
    r3 = r5
    }
    if (r2 != 0) goto L0204c47a
    csync
    r1 = 0
    b[r0+0] = r1
L0204c47a:
    call storage_coordination_irq_leave  ; @call.xl
L0204c480:
    r0 = r3
    {pc, r7-r4} = [sp++]
L0204c484:
    [--sp] = {rets, r15-r4}
    sp += -8
    r8 = L01c21b24
    r7 = [r8+0]
    r15 = r3
    r10 = r2
    r6 = r0
    if (r7 == 0) goto L0204c55e
    h[sp] = r6
    h[sp+2] = r1
    if (r3 == 0) goto L0204c564
    r0 = [sp+60]
    if (r0 == 0) goto L0204c56a
    r5 = r0 << 12
    h[sp+4] = r5
L0204c4ae:
    r0 = r6
    call L0204c3ac
    r12 = 20
    if (r0 <= 7) {  ; @if.le.ri.s12
    r0 = r0 << 2
    r0 += r7  ; @add.rr
    r12 = h[r0+98] (u)
    }
    call storage_coordination_irq_enter  ; @call.xl
    r11 = L01c1fa24
    r0 = cnum
    r1 = [r11+r0<<2]
    r2 = r1 + 1
    [r11+r0<<2] = r2
    r9 = L01c1fa20
    if (r1 != 0) goto L0204c4f0
    csync
L0204c4e8:
    testset b[r9]
    ifeq goto L0204c4e8
    csync
L0204c4f0:
    r0 = r6
    r1 = r15
    call L0204c3d8
    if (r0 == 0) goto L0204c596
    r13 = sp + 0
    r14 = 4095
    goto L0204c554
L0204c504:
    r4 = r12
    if (r0 <= r4) {
    r4 = r15
    }
    r0 = r5 >> 12
    r5 = r4
    r1 = [r8+0]
    r5 <= insert(r0, p:12, l:20)
    h[r13+4] = r5
    r6 = r4 & r14
    r0 = r1 + 128
    r1 = sp + 0
    r2 = 6
    call L02006970  ; @call.xl
    r1 = [r8+0]
    r7 = r0
    r0 = r1 + 128
    r1 = r10
    r2 = r6
    call L02006970  ; @call.xl
    r1 = r6 + 6
    r0 += r7  ; @add.rr
    r0 = r0.l (u)
    if (r1 != r0) goto L0204c5ba
    r15 = r15 - r4
    r0 = r4.l (u)
    r10 += r0
L0204c554:
    r0 = uextra(r15, p:0, l:16)
    if (r0 != 0) goto L0204c504
    r3 = 0
    goto L0204c59a
L0204c55e:
    r3 = -98
    goto L0204c5dc
L0204c564:
    r3 = -95
    goto L0204c5dc
L0204c56a:
    r1 += 1  ; @add.ri.u5
    r0 = 0
    r1 = r1.l (u)
    r2 = r7
    goto L0204c586
L0204c574:
    r3 = h[r2+2] (u)
    r4 = r3 >> 4
    if (r4 != r6) goto L0204c582
    r4 = h[r2+0] (u)
    if (r4 == r1) goto L0204c5e2
L0204c582:
    r0 += 1  ; @add.ri.u5
    r2 += 4  ; @add.ri.u5
L0204c586:
    ifs (r0 <= 23) goto L0204c574
    r0 = 0
    h[sp+4] = r0
L0204c590:
    r3 = -93
    goto L0204c5dc
L0204c596:
    r3 = -97
L0204c59a:
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L0204c5b2
    csync
    r0 = 0
    b[r9+0] = r0
L0204c5b2:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204c5dc
L0204c5ba:
    r0 = cnum
    r1 = [r11+r0<<2]
    r1 += -1
    [r11+r0<<2] = r1
    if (r1 != 0) goto L0204c5d2
    csync
    r0 = 0
    b[r9+0] = r0
L0204c5d2:
    call storage_coordination_irq_leave  ; @call.xl
    r3 = -97
L0204c5dc:
    r0 = r3
    sp += 8
    {pc, r15-r4} = [sp++]
L0204c5e2:
    r0 = r3 & 0xF
    r5 = r0 << 12
    h[sp+4] = r5
    if ((r3 & 0xF) != 0) goto L0204c4ae
    goto L0204c590
L0204c5f4:
    r0 = L01c21b24
    r0 = [r0+0]
    if (r0 == 0) goto L0204c612
    r0 += 96
    r1 = -1
L0204c602:
    r1 += 1  ; @add.ri.u5
    ifs (r1 > 7) goto L0204c612
    r2 = h[r0++=4] (u)
    r2 = r2 >> 6
    if (r2 == 0) goto L0204c602
    goto L0204c614
L0204c612:
    r2 = 0
L0204c614:
    r0 = r2.l (u)
    rts
L0204c618:
    [--sp] = {rets, r12-r4}
    r8 = L01c21b24
    [r8+0] = 0x0
    r6 = r3
    r11 = r2
    r5 = r1
    r12 = r0
    if (r0 == 0) goto L0204c700
    if (r5 == 0) goto L0204c700
    r0 = r6 + 195
    if (r2 < r0) goto L0204c702
    if (r6 <= 19) goto L0204c702
    call storage_coordination_irq_enter  ; @call.xl
    r10 = L01c1fa24
    r0 = cnum
    r1 = [r10+r0<<2]
    r2 = r1 + 1
    [r10+r0<<2] = r2
    r9 = L01c1fa20
    if (r1 != 0) goto L0204c668
    csync
L0204c660:
    testset b[r9]
    ifeq goto L0204c660
    csync
L0204c668:
    [r8+0] = r5
    r1 = 0
    r2 = 188
    r0 = r5
    call effect_enable_memset  ; @call.xl
    r0 = r5 + 188
    r1 = r5 + 172
    [r1+0] = r0
    h[r1+4] = r6
    r2 = -32
    r3 = 20
    goto L0204c69c
L0204c68a:
    r7 = r5 + r2
    r7 = r7 + 128
    h[r7+2] = r3
    r4 = h[r7+0] (u)
    r4 = r4 | 0x3C
    h[r7+0] = r4
    r2 += 4  ; @add.ri.u5
L0204c69c:
    if (r2 != 0) goto L0204c68a
    r2 = 0
    r3 = r5
    rep 24 {
    [r3++=4] = r2
    }
    r1 = r0 + r6  #
    b[r1+6] = r2
    r0 = r11 + -188
    r0 = r0 - r6
    r2 = r0.l (u)
    r0 = r5 + 128
    call L020012ae  ; @call.xl
    r0 = r12 + -1
    r0 = r0.l (u)
    r1 = 61438
    if (r0 > r1) goto L0204c6e2
    r0 = [r8+0]
    if (r0 == 0) goto L0204c6e2
    r1 = h[r0+96] (u)
    r1 = r1 & 0x3F
    r1 <= insert(r12, p:6, l:16)
    h[r0+96] = r1
L0204c6e2:
    r0 = cnum
    r1 = [r10+r0<<2]
    r1 += -1
    [r10+r0<<2] = r1
    if (r1 != 0) goto L0204c6fa
    csync
    r0 = 0
    b[r9+0] = r0
L0204c6fa:
    call storage_coordination_irq_leave  ; @call.xl
L0204c700:
    {pc, r12-r4} = [sp++]
L0204c702:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204c70e:
    goto L0204c70e
L0204c710:
    [--sp] = rets
    r0 = L02039fa0  ; "btstack"
    r1 = 255
    r3_r2 = 0
    call L02040bae  ; @call.xl
    pc = [sp++]
L0204c724:
    if (r1 == 0) goto L0204c734
L0204c726:
    r2 = r0
    if (r2 == 0) goto L0204c734
    r0 = [r2+0]
    if (r0 != r1) goto L0204c726
    r0 = [r1+0]
    [r2+0] = r0
L0204c734:
    rts
L0204c736:
    [--sp] = rets
    r1 = r0
    r0 = L01c202a4
    call L0204c724
    pc = [sp++]
L0204c744:
    [--sp] = {r3, r2}
    [--sp] = {rets, r11-r4}
    sp += -32
    r7 = r1
    r5 = r0
    r4 = L01c21b7c
    r0 = b[r4+180] (u)
    if (r0 == 0) goto L0204c7c4
    r6 = -99
    ifs (r7 > 5) goto L0204c7c8
    r0 = r7 << 16
    r0 |= r5
    [sp+8] = r0
    call storage_coordination_irq_enter  ; @call.xl
    r9 = L01c1fa24
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    r8 = L01c1fa20
    if (r1 != 0) goto L0204c794
    csync
L0204c78c:
    testset b[r8]
    ifeq goto L0204c78c
    csync
L0204c794:
    r1_r0 = d[r4+36]
    r0 = r1 - r0
    r0 = r0 >> 2
    r1 = r7 + 1
    if (r1 <= r0) goto L0204c7d2
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204c7ba
    csync
    r0 = 0
    b[r8+0] = r0
L0204c7ba:
    call storage_coordination_irq_leave  ; @call.xl
    r6 += -1
    goto L0204c7c8
L0204c7c4:
    r6 = -94
L0204c7c8:
    r0 = r6
    sp += 32
    {rets, r11-r4} = [sp++]
    sp += 8
    rts
L0204c7d2:
    r0 = sp + 68
    [sp+4] = r0
    r0 = 1
    goto L0204c7ea
L0204c7da:
    r2 = [sp+4]
    r3 = r2 + 4
    [sp+4] = r3
    r2 = [r2+0]
    r3 = sp + 8
    [r3+r0<<2] = r2
    r0 += 1  ; @add.ri.u5
L0204c7ea:
    ifs (r0 < r1) goto L0204c7da
    r0 = r5 + -3
    r6 = 0
    if (r0 > 11) goto L0204c81e
    r2 = r0 << 1
    tbh [r2]
L0204c7fc:
    .short (L0204c814 - L0204c7fc) / 2, (L0204c814 - L0204c7fc) / 2, (L0204c84e - L0204c7fc) / 2, (L0204c84e - L0204c7fc) / 2, (L0204c87c - L0204c7fc) / 2, (L0204c84e - L0204c7fc) / 2, (L0204c890 - L0204c7fc) / 2, (L0204c89e - L0204c7fc) / 2
    .short (L0204c84e - L0204c7fc) / 2, (L0204c84e - L0204c7fc) / 2, (L0204c84e - L0204c7fc) / 2, (L0204ca2a - L0204c7fc) / 2
L0204c814:
    r0 = [sp+12]
    r6 += -95
    ifs (r0 <= 31) goto L0204c84e
    goto L0204ca2a
L0204c81e:
    r0 = r5 + -24
    if (r0 > 8) goto L0204c84e
    r7 = L01c21b24
    tbb [r0]
L0204c82e:
    .byte (L0204c838 - L0204c82e) / 2, (L0204c8b2 - L0204c82e) / 2, (L0204c940 - L0204c82e) / 2, (L0204c84e - L0204c82e) / 2, (L0204c95c - L0204c82e) / 2, (L0204c84e - L0204c82e) / 2, (L0204c84e - L0204c82e) / 2, (L0204c84e - L0204c82e) / 2
    .byte (L0204c96c - L0204c82e) / 2
    .byte 0x00  ; alignment
L0204c838:
    r3 = h[sp+20] (u)
    r2 = h[sp+16] (u)
    r1 = [sp+12]
    r0 = 65520
    call L0204c618
    goto L0204ca2a
L0204c84e:
    r0 = r4 + 12
    r2 = r1 << 2
    r1 = sp + 8
    call L02006970  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204c872
    csync
    r0 = 0
    b[r8+0] = r0
L0204c872:
    call storage_coordination_irq_leave  ; @call.xl
    r6 = 0
    goto L0204ca48
L0204c87c:
    r3 = h[sp+24] (u)
    r2 = h[sp+20] (u)
    r1 = [sp+16]
    r0 = h[sp+12] (u)
    call L0204c618
    goto L0204ca2a
L0204c890:
    call L0204c5f4
    r1 = 0
    call L0204c3d8
    r1 = [sp+12]
    goto L0204c968
L0204c89e:
    call L0204c5f4
    r3 = h[sp+20] (u)
    r2 = [sp+16]
    r1 = h[sp+12] (u)
    r6 = b[sp+24] (u)
    goto L0204c952
L0204c8b2:
    r0 = [r7+0]
    if (r0 == 0) goto L0204ca2a
    r3 = [sp+20]
    r6 = [sp+16]
    r10 = [sp+12]  ; @ld.w.sp.l
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L0204c8e0
    csync
L0204c8d8:
    testset b[r8]
    ifeq goto L0204c8d8
    csync
L0204c8e0:
    r11 = [r7+0]
    r1 = r11 + 96
    r7 = 0
    goto L0204c902
L0204c8ec:
    r2 = h[r1+0] (u)
    r0 = r2 & 0x3
    if (r0 != r3) goto L0204c8fe
    r0 = uextra(r2, p:2, l:4)
    if (r0 == r6) goto L0204c9e6
L0204c8fe:
    r1 += 4  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L0204c902:
    ifs (r7 <= 7) goto L0204c8ec
    r0 = uextra(r10, p:0, l:16)
    if (r0 == 0) goto L0204ca0a
    r1 = r11 + 92
    r7 = -1
L0204c912:
    r7 += 1  ; @add.ri.u5
    ifs (r7 > 7) goto L0204ca0a
    r0 = h[++r1=4] (u)
    r0 = r0 & 0x3C
    if (r0 != 60) goto L0204c912
    r0 = r6 << 2
    r2 = r11 + r0
    r6 = 20
    h[r2+98] = r6
    r0 = r0 & 0x3C
    r0 <= insert(r10, p:6, l:26)
    r2 = r3 & 0x3
    r0 |= r2
    goto L0204ca08
L0204c940:
    r3 = h[sp+24] (u)
    r2 = [sp+20]
    r1 = h[sp+16] (u)
    r0 = h[sp+12] (u)
    r6 = b[sp+28] (u)
L0204c952:
    [sp] = r6
    call L0204c484
    r6 = r0
    goto L0204ca2a
L0204c95c:
    r0 = h[sp+12] (u)
    r1 = 0
    call L0204c3d8
    r1 = [sp+16]
L0204c968:
    [r1+0] = r0
    goto L0204ca2a
L0204c96c:
    r0 = [r7+0]
    if (r0 == 0) goto L0204ca2a
    call storage_coordination_irq_enter  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r2 = r1 + 1
    [r9+r0<<2] = r2
    if (r1 != 0) goto L0204c990
    csync
L0204c988:
    testset b[r8]
    ifeq goto L0204c988
    csync
L0204c990:
    r2 = [r7+0]
    b[r2+178] = r6
    call storage_coordination_irq_enter  ; @call.xl
    csync
    r0 = r2 + 128
    r1 = r0 + 32
L0204c9a6:
    testset b[r1]
    ifeq goto L0204c9a6
    csync
    r1 = [r0+0]
    [r0+8] = r1
    [r0+12] = r1
    [r0+16] = r1
    [r0+24] = r6
    [r0+20] = r6
    csync
    b[r2+160] = r6
    call storage_coordination_irq_leave  ; @call.xl
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204c9de
    csync
    r0 = 0
    b[r8+0] = r0
L0204c9de:
    call storage_coordination_irq_leave  ; @call.xl
    goto L0204ca2a
L0204c9e6:
    r0 = r2 & 0x3F
    r0 <= insert(r10, p:6, l:26)
    h[r1+0] = r0
    r0 = r6 << 2
    r0 += r11
    r2 = 20
    r3 = uextra(r10, p:0, l:16)
    h[r0+98] = r2
    if (r3 != 0) goto L0204ca0a
    r0 = r10 << 6
    r0 = r0 | 0x3C
L0204ca08:
    h[r1+0] = r0
L0204ca0a:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204ca22
    csync
    r0 = 0
    b[r8+0] = r0
L0204ca22:
    call storage_coordination_irq_leave  ; @call.xl
    r6 = 0
L0204ca2a:
    r0 = cnum
    r1 = [r9+r0<<2]
    r1 += -1
    [r9+r0<<2] = r1
    if (r1 != 0) goto L0204ca42
    csync
    r0 = 0
    b[r8+0] = r0
L0204ca42:
    call storage_coordination_irq_leave  ; @call.xl
L0204ca48:
    call L0204c710
    if (r5 != 14) goto L0204c7c8
    r0 = [sp+12]
    r1 = b[r4+180] (u)
    if (r1 == 0) goto L0204c7c8
    r0 = r0 & 0xF
    r0 = r0 | 0xA0
    b[r4+180] = r0
    call L0204c710
    goto L0204ca78
L0204ca70:
    r0 = 1
    call L0203feb8  ; @call.xl
L0204ca78:
    r0 = b[r4+180] (u)
    if (r0 != 0) goto L0204ca70
    r0 = r4
    call L0204c736
    goto L0204c7c8
L0204ca86:
    [--sp] = {rets, r4}
    r2 = L01c202e8
    r4 = r0  #
    r2 = b[r2+1] (u)
    r2 = r2 & 0xFFFFFF0F
    r0 = 0
    if (r2 <= r1) goto L0204cabe
    r0 = r1 + 114
    r2 = 52
    r1 = r4
    call bond_records_and_prints_bond_read  ; @call.xl
    if (r0 != 52) goto L0204cabc
    r0 = b[r4+38] (u)
    r1 = r0 & 0xFFFFFF0F
    r0 = 1
    if (r1 == 10) goto L0204cabe
L0204cabc:
    r0 = 0
L0204cabe:
    {pc, r4} = [sp++]
L0204cac0:
    [--sp] = {rets, r5, r4}
    r4 = L01c202e8
    if (r0 == 0) goto L0204cada
    r0 = 113
    r2 = 14
    r1 = r4
    call bond_records_and_prints_bond_write  ; @call.xl
    r5 = 1
    goto L0204cb1a
L0204cada:
    r0 = 113
    r2 = 14
    r1 = r4
    call bond_records_and_prints_bond_read  ; @call.xl
    if (r0 != 14) goto L0204caf8
    r0 = b[r4+0] (u)
    if (r0 != 7) goto L0204caf8
    r0 = b[r4+2] (u)
    r5 = 1
    if (r0 < 11) goto L0204cb1a
L0204caf8:
    r5 = 0
    b[r4+3] = r5
    b[r4+2] = r5
    r0 = 26
    b[r4+1] = r0
    r0 = 7
    b[r4+0] = r0
    r0 = r4 + 4
    r1 = 255
    rep 10 {
    b[r0++=1] = r1
    }
    r0 = 113
    r2 = 14
    r1 = r4
    call bond_records_and_prints_bond_write  ; @call.xl
L0204cb1a:
    r0 = r5
    {pc, r5, r4} = [sp++]
L0204cb1e:
    [--sp] = {rets, r7-r4}
    sp += -52
    r7 = 0
    r6 = L01c202e8
    goto L0204cb52
L0204cb2c:
    r0 = sp + 0
    r1 = r4
    call L0204ca86
    if (r0 == 0) goto L0204cb50
    r5 = sp + 0
    r1 = 255
    r2 = 52
    r0 = r5
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 114
    r2 = 52
    r1 = r5
    call bond_records_and_prints_bond_write  ; @call.xl
L0204cb50:
    r7 += 1  ; @add.ri.u5
L0204cb52:
    r4 = r7.b0 (u)  #
    r0 = b[r6+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r4 < r0) goto L0204cb2c
    r0 = 0
    b[r6+2] = r0
    b[r6+3] = r0
    r0 = r6 + 4
    r1 = 255
    rep 10 {
    b[r0++=1] = r1
    }
    r0 = 1
    call L0204cac0
    sp += 52
    {pc, r7-r4} = [sp++]
L0204cb74:
    r0 += r1  ; @add.rr
    r1 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r1, p:8, l:24)
    r0 = r0.l (u)
    rts
L0204cb82:
    [--sp] = {rets, r4}
    r4 = L01c202e8
    r0 = b[r4+2] (u)
    if (r0 < 11) goto L0204cb96
    r0 = 0
    call L0204cac0
    r0 = b[r4+2] (u)
L0204cb96:
    {pc, r4} = [sp++]
L0204cb98:
    r1 = [r0+0]
    if (r1 == 0) goto L0204cba8
    r1 = [r0+4]
    r1 = [r1+0]
    r0 = [r0+8]
    if (r1 != r0) goto L0204cbac
    goto L0204cbaa
L0204cba8:
    r1 = r0 + 8
L0204cbaa:
    r1 = [r1+0]
L0204cbac:
    r0 = 1
    if (r1 != 0) goto L0204cbb2
    r0 = r1
L0204cbb2:
    rts
L0204cbb4:
    r1 = [r0+0]
    if (r1 == 0) goto L0204cbca
    r1 = [r0+4]
    r1 = [r1+0]
    r2 = [r0+8]
    if (r1 == r2) {
    [r0+4] = r1
    r1 = [r1+0]
    }
    [r0+8] = r1
    goto L0204cbd0
L0204cbca:
    [r0+0] = 0x1
    r1 = [r0+8]
L0204cbd0:
    r0 = r1
    rts
L0204cbd4:
    [--sp] = rets
    sp += -12
    r3 = r0
    r0 = L01c21714
    r1 = [r0+0]
    r2 = 0
    [sp] = r2
    d[sp+4] = r1_r0
L0204cbea:
    r0 = sp + 0
    call L0204cb98
    if (r0 == 0) goto L0204cbfc
    r0 = sp + 0
    call L0204cbb4
    r1 = h[r0+4] (u)
    if (r1 != r3) goto L0204cbea
    goto L0204cbfe
L0204cbfc:
    r0 = 0
L0204cbfe:
    sp += 12
    pc = [sp++]
L0204cc02:
    r3 = r2 >> 8
    b[r0+r1] = r3
    r1 += 1  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    rts
L0204cc12:
    [--sp] = {rets, r4}
    r1 += r2  ; @add.rr
    r1 += -1
    r3 = 0
    goto L0204cc24
L0204cc1c:
    r4 = b[r0+r3] (u)
    b[r1++=-1] = r4
    r3 += 1  ; @add.ri.u5
L0204cc24:
    ifs (r3 < r2) goto L0204cc1c
    {pc, r4} = [sp++]
L0204cc2a:
    [--sp] = rets
    r2 = 16
    call L0204cc12
    pc = [sp++]
L0204cc32:
    [r0+0] = 0x0
    [r0+4] = r1
    r1 = [r1+0]
    [r0+8] = r1
    rts
L0204cc3e:
    [--sp] = rets
    r1 = L01c21714
    call L0204cc32
    pc = [sp++]
L0204cc4a:
    b[r0+r1] = r2
    r2 = r2 >> 8
    r1 += 1  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    rts
L0204cc5a:
    [--sp] = rets
    r2 = 6
    call L0204cc12
    pc = [sp++]
L0204cc62:
    r1 = r0
    r0 = 1
    if (r1 == 0) goto L0204cc6a
    r0 = 0
L0204cc6a:
    rts
L0204cc6c:
    [--sp] = {rets, r4}
    b[r0+r1] = r2
    r3 = r2 >> 8
    r4 = r1 + 1
    r4 = r4.l (u)
    b[r0+r4] = r3
    r3 = r2 >> 16
    r4 = r1 + 2
    r4 = r4.l (u)
    b[r0+r4] = r3
    r2 = r2 >> 24
    r1 += 3  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    {pc, r4} = [sp++]
L0204cc92:
    [--sp] = {rets, r5, r4}
    r1 = L01c21714
    r2 = 0
    r3 = 1238
    r4 = r1
    goto L0204ccb0
L0204cca4:
    r5 = [r4+12]
    if (r5 != 255) {  ; @if.ne.ri.s12
    r5 = b[r4+r3] (u)
    r2 += r5  ; @add.rr
    }
L0204ccb0:
    r4 = [r4+0]
    if (r4 != 0) goto L0204cca4
    r3 = 538
    r3 = b[r1+r3] (u)
    r1 = 0
    r4 = 0
    if (r3 == 0) goto L0204ccc8
    r4 = r3 - r2
    ifs (r4 < 0) goto L0204ccda
L0204ccc8:
    if (r0 == 254) goto L0204ccda
    if (r0 != 255) goto L0204ccd4
    r1 = 1
    goto L0204ccda
L0204ccd4:
    r1 = 1
    if (r3 == 0) goto L0204ccda
    r1 = r4
L0204ccda:
    r0 = r1
    {pc, r5, r4} = [sp++]
L0204ccde:
    [--sp] = rets
    call L0204cbd4
    if (r0 == 0) goto L0204ccf2
    r0 = [r0+12]
    call L0204cc92
    r1 = r0
    r0 = 1
    ifs (r1 > 0) goto L0204ccf4
L0204ccf2:
    r0 = 0
L0204ccf4:
    pc = [sp++]
L0204ccf6:
    [--sp] = rets
    r1 = 533
    r2 = L01c21714
    r2 = b[r2+r1] (u)
    r1 = r0
    r0 = 0
    if (r2 != 0) goto L0204cd10
    r0 = r1
    call L0204ccde
L0204cd10:
    pc = [sp++]
L0204cd12:
    [--sp] = rets
    call L0204ccf6
    pc = [sp++]
L0204cd18:
    r1 = 533
    r2 = L01c21714
    r3 = b[r2+r1] (u)
    r0 = 0
    if (r3 != 0) goto L0204cd30
    r0 = 1
    b[r2+r1] = r0
L0204cd30:
    rts
L0204cd32:
    b[r0+r1] = r2
    r2 = r2 >> 8
    r1 += 1  ; @add.ri.u5
    r1 = r1.l (u)
    b[r0+r1] = r2
    rts
L0204cd42:
    [--sp] = {rets, r14-r4}
    r8 = r0
    r0 = 270
    r5 = L01c21714
    r14 = h[r5+r0<<1] (u)
    r13 = r8 + 1238
    r12 = 267
    r9 = 268
    r10 = 0
    r11 = 57343
L0204cd68:
    r6 = h[r5+r12<<1] (u)
    r0 = h[r5+r9<<1] (u)
    r4 = r0 - r6
    r0 = r6 + -4
    r3 = r0.l (u)
    r7 = smin(r4, r14)
    if (r3 == 0) goto L0204cd96
    r0 = r5  #
    r1 = b[r5+9] (u)
    r2 = b[++r0=8] (u)
    r2 <= insert(r1, p:8, l:24)
    r1 = r2 | 0x1000
    r2 = r1 & r11
    r1 = r3
    call L0204cd32
L0204cd96:
    r0 = r5 + 8
    r2 = r7.l (u)
    r1 = r6 + -2
    r1 = r1.l (u)
    call L0204cd32
    r0 = b[r13+0] (u)
    r0 += 1  ; @add.ri.u5
    b[r13+0] = r0
    ifs (r4 > r14) {
    r0 = h[r5+r12<<1] (u)
    r0 += r7  ; @add.rr
    h[r5+r12<<1] = r0
    } else {
    h[r5+r12<<1] = r10
    h[r5+r9<<1] = r10
    }
    r0 = r3 + r5
    r0 += 8  ; @add.ri.u5
    r1 = r7 + 4
    r1 = r1.l (u)
    call L02042e50  ; @call.xl
    ifs (r4 <= r14) goto L0204cdde
    r0 = h[r8+4] (u)
    call L0204ccde
    if (r0 != 0) goto L0204cd68
    {pc, r14-r4} = [sp++]
L0204cdde:
    r0 = r5 + 533
    r1 = 0
    rep 5 {
    b[r0++=1] = r1
    }
    {pc, r14-r4} = [sp++]
L0204cdea:
    [--sp] = {rets, r7-r4}
    r1 = 533
    r7 = L01c21714
    r1 = b[r7+r1] (u)
    r5 = r0
    r4 = 87
    if (r1 == 0) goto L0204ce4a
    r0 = b[r7+9] (u)
    r0 = r0 << 8
    r0 = r0 & 0xF00  #
    r1 = b[r7+8] (u)
    r6 = r0 | r1
    r0 = r6
    call L0204ccde
    if (r0 == 0) goto L0204ce34
    r0 = r6.l (u)
    call L0204cbd4
    if (r0 == 0) goto L0204ce40
    r1 = 268
    h[r7+r1<<1] = r5
    r1 += -1
    r2 = 4
    h[r7+r1<<1] = r2
    call L0204cd42
    r4 = 0
    goto L0204ce4a
L0204ce34:
    r0 = 533
    r1 = 0
    b[r7+r0] = r1
    goto L0204ce4a
L0204ce40:
    r0 = 533
    r4 = 0
    b[r7+r0] = r4
L0204ce4a:
    r0 = r4
    {pc, r7-r4} = [sp++]
L0204ce4e:
    [--sp] = {rets, r8-r4}
    r3 = 533
    r5 = L01c21714
    r3 = b[r5+r3] (u)
    r4 = r2
    r8 = r1
    r6 = r0
    r7 = 87
    if (r3 == 0) goto L0204ce98
    call L0204ccde
    if (r0 == 0) goto L0204ce98
    r0 = r5 + 8
    r1 = 0
    r2 = r6
    call L0204cc4a
    r1 = r4 + 4
    r2 = r1.l (u)
    r1 = 2
    call L0204cc4a
    r1 = 4
    r2 = r4
    call L0204cc4a
    r1 = 6
    r2 = r8
    call L0204cc4a
    r0 = r4 + 8
    call L0204cdea
    r7 = r0
L0204ce98:
    r0 = r7
    {pc, r8-r4} = [sp++]
L0204ce9c:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    call L0204ccf6
    if (r0 == 0) goto L0204cec6
    call L0204cd18
    r0 = L01c21724
    r1 = r6
    r2 = r4
    call effect_parameter_support_memmove  ; @call.xl
    r1 = 6
    r0 = r5
    r2 = r4
    call L0204ce4e
L0204cec6:
    {pc, r6-r4} = [sp++]
L0204cec8:
    if (r0 == 2) {  ; @if.eq.ri.s12
    r0 = 2
    rts
    }
    if (r0 == 4) goto L0204cede
    if (r0 != 6) {  ; @if.ne.ri.s12
    r0 = -1
    } else {
    r0 = 1
    }
    rts
L0204cede:
    r0 = 0
    rts
L0204cee2:
    [--sp] = rets
    r0 = 533
    r1 = L01c21714
    r1 = b[r1+r0] (u)
    r0 = 0
    if (r1 != 0) goto L0204cf04
    call L0204cc92
    r1 = r0
    r0 = 1
    ifs (r1 <= 0) {  ; @ifs.le.ri.s12
    r0 = 0
    }
L0204cf04:
    pc = [sp++]
L0204cf06:
    [--sp] = {rets, r11-r4}
    sp += -4
    r11 = sp + 0
    r10 = 0
    r4 = L01c2195c
    r8 = 120
    r9 = 2
    r7 = 0
    goto L0204cf6e
L0204cf22:
    r5 = [r4+0]
    if (r5 == 0) goto L0204cf6a
    r6 = r4
    r0 = b[++r6=4] (u)
    if (r0 == 0) goto L0204cf6a
    if (r7 == 2) goto L0204cf6a
    call L0204cee2
    if (r0 == 0) goto L0204cf6a
    b[r6+0] = r10
    if (r7 == 0) goto L0204cf4a
    if (r7 == 2) goto L0204cf4e
    if (r7 != 1) {  ; @if.ne.ri.s12
    r0 = 0
    } else {
    r0 = 6
    }
    goto L0204cf50
L0204cf4a:
    r0 = 4
    goto L0204cf50
L0204cf4e:
    r0 = 2
L0204cf50:
    b[sp] = r8
    b[r11+1] = r9
    b[r11+2] = r0
    b[r11+3] = r10
    r1 = r0.l (u)
    r2 = sp + 0
    r0 = 4
    r3 = 4
    call r5
L0204cf6a:
    r4 += 8  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
L0204cf6e:
    if (r7 != 3) goto L0204cf22
    sp += 4
    {pc, r11-r4} = [sp++]
L0204cf76:
    [--sp] = rets
    call L0204cec8
    ifs (r0 < 0) goto L0204cf8e
    r0 = r0 << 3
    r1 = L01c2195c
    r0 += r1  ; @add.rr
    r1 = 1
    b[r0+4] = r1
    call L0204cf06
L0204cf8e:
    pc = [sp++]
L0204cf90:
    [--sp] = {rets, r4}
    r1 += r2  ; @add.rr
    r1 += -1
    r3 = 0
    goto L0204cfa2
L0204cf9a:
    r4 = b[r0+r3] (u)
    b[r1++=-1] = r4
    r3 += 1  ; @add.ri.u5
L0204cfa2:
    ifs (r3 < r2) goto L0204cf9a
    {pc, r4} = [sp++]
L0204cfa8:
    [--sp] = {rets, r5, r4}
    sp += -8
    r4 = r2
    r5 = r1
    call L0204cbd4
    if (r0 == 0) goto L0204cfd6
    r1 = [r0+24]
    b[r5+0] = r1
    r1 = r0 + 28
    r2 = sp + 0
    rep 4 {
    r3 = b[r1++=1] (u)
    b[r2++=1] = r3
    }
    r1 = b[r0+33] (u)
    r0 = b[r0+32] (u)
    r0 <= insert(r1, p:8, l:24)
    h[sp+4] = r0
    goto L0204cfe2
L0204cfd6:
    r0 = 0
    b[r5+0] = r0
    r0 = sp + 0
    call L0204a6ac  ; @call.xl
L0204cfe2:
    r0 = sp + 0
    r2 = 6
    r1 = r4
    call L0204cf90
    sp += 8
    {pc, r5, r4} = [sp++]
L0204cfee:
    [--sp] = rets
    r0 = r0.l (u)
    call phase3_p13_sys_timeout_del  ; @call.xl
    pc = [sp++]
L0204cffa:
    [--sp] = {rets, r4}
    r4 = r0
    r0 = r1 & 0xF  #
    r2 = [r4+8]
    r1 = r2 & 0xFFF0FFFF
    r1 <= insert(r0, p:16, l:4)
    r2 = r2.l (u)  #
    [r4+8] = r1
    if (r0 == 3) goto L0204d022
    if (r0 == 2) goto L0204d026
    if (r0 != 1) {  ; @if.ne.ri.s12
    r2 = 0
    } else {
    r2 = 10
    }
    goto L0204d026
L0204d022:
    r2 = r2 * 0x3E8
L0204d026:
    r0 = r4  #
    r1 = [r4+12]
    call L0201c95e  ; @call.xl
    [r4+4] = r0
    {pc, r4} = [sp++]
L0204d034:
    r1 += r0  ; @add.rr
    r2 = b[r1+2] (u)
    r0 = b[r1+3] (u)
    r0 <= insert(r2, p:8, l:8)  #
    r3 = b[r1+1] (u)
    r0 <= insert(r3, p:16, l:8)  #
    r1 = b[r1+0] (u)
    r0 <= insert(r1, p:24, l:8)
    rts
L0204d04c:
    [--sp] = rets
    r2 = 7
    call L0204cc12
    pc = [sp++]
L0204d056:
    [--sp] = {rets, r6-r4}
    sp += -28
    r4 = r1  #
    r3 = b[r0+0] (u)
    r5 = r3 & 0xFFFFFFC0
    r3 = r2
    if (r5 != 64) goto L0204d08e
    r5 = sp + 3
    r2 = 6
    r1 = r5
    call L0204cf90
    r6 = sp + 9
    r2 = 16
    r0 = r4
    r1 = r6
    call L0204cf90
    r1 = r5 + 3
    r4 = sp + 25
    r0 = r6
    r2 = r4
    call L0204711c  ; @call.xl
    r2 = 3
    r1_r0 = r5_r4
    goto L0204d092
L0204d08e:
    r2 = 6
    r1 = r3
L0204d092:
    call capture_journal_compare  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L0204d09e
    r1 = 0
L0204d09e:
    r0 = r1
    sp += 28
    {pc, r6-r4} = [sp++]
L0204d0a4:
    [--sp] = {rets, r12-r4}
    sp += -52
    r12 = L01c202e8
    r3 = b[r12+2] (u)
    r8 = r2
    r5 = r1
    r6 = r0
    if (r3 == 0) goto L0204d13c
    r11 = sp + 0
    r7 = r11 + 32
    r9 = r11 + 16
    r4 = 0
    r10 = 0
    goto L0204d12c
L0204d0cc:
    r0 = sp + 0
    call L0204ca86
    if (r0 == 0) goto L0204d12a
    if (r5 == 0) goto L0204d10e
    r1 = sp + 0
    r0 = r6
    r2 = r7
    call L0204d056
    if (r0 != 1) goto L0204d0f0
    r2 = 16
    r0 = r9
    r1 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204d140
L0204d0f0:
    r0 = b[r11+39] (u)
    if ((r0 & 4) != 0) goto L0204d12a
    r2 = 16
    r0 = r9
    r1 = r8
    call capture_journal_compare  ; @call.xl
    r1 = 1
    if (r0 == 0) goto L0204d10a
    r1 = r10
L0204d10a:
    r10 = r1
    goto L0204d12a
L0204d10e:
    r2 = 6
    r0 = r7
    r1 = r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204d12a
    r2 = 16
    r0 = r9
    r1 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204d140
L0204d12a:
    r4 += 1  ; @add.ri.u5
L0204d12c:
    r0 = b[r12+1] (u)
    r1 = r4.b0 (u)
    r0 = r0 & 0xFFFFFF0F
    if (r1 < r0) goto L0204d0cc
    goto L0204d144
L0204d13c:
    r10 = 0
    goto L0204d144
L0204d140:
    r10 = 1
L0204d144:
    r0 = uextra(r10, p:0, l:8)
    sp += 52
    {pc, r12-r4} = [sp++]
L0204d14c:
    [--sp] = rets
    r2 = 8
    call L0204cc12
    pc = [sp++]
L0204d156:
    [--sp] = rets
    call L0204cbd4
    r1 = 0
    if (r0 == 0) goto L0204d17c
    r2 = [r0+24]
    if (r2 == 0) goto L0204d17c
    r1 = b[r0+33] (u)
    r0 = 1
    if (r1 <= 191) {  ; @if.le.ri.s12
    r0 = 2
    }
    r2 = r1 & 0xFFFFFFC0
    r1 = 3
    if (r2 != 64) {  ; @if.ne.ri.s12
    r1 = r0
    }
L0204d17c:
    r0 = r1.b0 (u)
    pc = [sp++]
L0204d180:
    [--sp] = {rets, r5, r4}
    sp += -8
    r4 = r2
    r5 = r1
    call L0204cbd4
    r1 = 0
    b[r5+0] = r1
    if (r0 == 0) goto L0204d1a8
    r3 = sp + 2
    r0 = r3
    call L0204a6ac  ; @call.xl
    r2 = 6
    r0 = r3
    r1 = r4
    call L0204cf90
    goto L0204d1ac
L0204d1a8:
    rep 6 {
    b[r4++=1] = r1
    }
L0204d1ac:
    sp += 8
    {pc, r5, r4} = [sp++]
L0204d1b0:
    [--sp] = {rets, r6-r4}
    sp += -52
    r4 = r0
    if (r4 > 9) goto L0204d212
    r5 = sp + 0
    r1 = 255
    r2 = 52
    r6 = 255
    r0 = r5
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 114
    r2 = 52
    r1 = r5
    call bond_records_and_prints_bond_write  ; @call.xl
    r0 = L01c202e8
    r1 = r0 + 4
    r2 = b[r4+r1] (u)
    b[r4+r1] = r6
    r3 = b[r0+1] (u)
    r3 = r3 & 0xFFFFFF0F
    goto L0204d202
L0204d1f0:
    r4 = b[r1+0] (u)
    if (r4 == 255) goto L0204d1fe
    if (r4 > r2) {
    r4 += -1
    b[r1+0] = r4
    }
L0204d1fe:
    r3 += -1
    r1 += 1  ; @add.ri.u5
L0204d202:
    if (r3 != 0) goto L0204d1f0
    r1 = b[r0+2] (u)
    if (r1 == 0) goto L0204d20c
    r1 += -1
    b[r0+2] = r1
L0204d20c:
    r0 = 1
    call L0204cac0
L0204d212:
    sp += 52
    {pc, r6-r4} = [sp++]
L0204d216:
    [--sp] = {rets, r13-r4}
    sp += -52
    r13 = L01c202e8
    r4 = b[r13+2] (u)
    r8 = r2
    r5 = r1
    r9 = r0
    if (r4 == 0) goto L0204d296
    r10 = sp + 0
    r11 = r3 & 0xFFFFFF04
    r12 = r10 + 32
    r7_r6 = 0
    goto L0204d28a
L0204d23c:
    r4 = r7.b0 (u)
    r0 = sp + 0
    r1 = r4
    call L0204ca86
    if (r0 == 0) goto L0204d286
    if (r5 == 0) goto L0204d256
    if (r11 != 0) goto L0204d266
    r0 = b[r10+39] (u)
    if ((r0 & 4) != 0) goto L0204d266
L0204d256:
    r2 = 6
    r0 = r12
    r1 = r9
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204d286
    goto L0204d282
L0204d266:
    r1 = sp + 0
    r2 = 16
    r0 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204d286
    r0 = r9
    r1 = r8
    r2 = r12
    call L0204d056
    if (r0 != 1) goto L0204d286
L0204d282:
    r0 = r4
    call L0204d1b0
L0204d286:
    r7 += 1  ; @add.ri.u5
    r6 += 1  ; @add.ri.u5
L0204d28a:
    r0 = b[r13+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r6 < r0) goto L0204d23c
L0204d296:
    sp += 52
    {pc, r13-r4} = [sp++]
L0204d29a:
    [--sp] = {rets, r11-r4}
    sp += -52
    r10 = r3  #
    r5 = [sp+92]
    r4 = r2  #
    r6 = b[r5+1] (u)
    r7 = r1
    r8 = r0
    if (r0 == 0) goto L0204d2ba
    r1 = r6 & 0xFFFFFF0C  #
    r0 = b[r5+0] (u)
    r0 = r0 & 0xFFFFFF03
    r6 = r1 | r0
L0204d2ba:
    r9 = sp + 0
    r1 = 255
    r2 = 52
    r0 = r9
    call effect_enable_memset  ; @call.xl
    r3 = r6.b0 (u)
    r0 = r7
    r1 = r4
    r2 = r10
    call L0204d216
    r0 = r4 << 5
    r1 = r0 | 0xDF
    b[sp+38] = r1
    if ((r6 & 8) != 0) goto L0204d2fa
    if (r4 == 0) goto L0204d306
    r1 = b[r7+0] (u)
    r1 = r1 & 0xFFFFFFC0
    if (r1 != 64) goto L0204d306
    r1 = sp + 0
    r1 += 32
    r2 = 255
    rep 6 {
    b[r1++=1] = r2
    }
    goto L0204d312
L0204d2fa:
    r1 = sp + 0
    r1 += 32
    rep 6 {
    r2 = b[r7++=1] (u)
    b[r1++=1] = r2
    }
    goto L0204d312
L0204d306:
    r1 = sp + 0
    r1 += 32
    rep 6 {
    r2 = b[r7++=1] (u)
    b[r1++=1] = r2
    }
    r6 |= 8
L0204d312:
    r3 = r6.b0 (u)
    if ((r6 & 4) != 0) goto L0204d328
    r10 = 0xFFFFFFFF  ; @li.modimm
    r11 = r10
    d[sp+8] = r11_r10
    d[sp] = r11_r10
    goto L0204d33e
L0204d328:
    r1 = sp + 0
    r2 = r10
    r4 = r1 + 8
    rep 8 {
    r7 = b[r2++=1] (u)
    b[r1++=1] = r7
    }
    r1 = r10 + 8
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r4++=1] = r2
    }
L0204d33e:
    r1 = [sp+88]
    r2 = sp + 0
    r2 += 16  ; @add.ri.u5
    if ((r3 & 1) != 0) goto L0204d352
    r3 = 255
    r4 = r2
    rep 16 {
    b[r4++=1] = r3
    }
    goto L0204d35c
L0204d352:
    r3 = r2
    r4 = r1
    rep 16 {
    r7 = b[r4++=1] (u)
    b[r3++=1] = r7
    }
L0204d35c:
    b[sp+39] = r6
    r0 = r0 & 0x20  #
    r3 = b[r5+2] (u)
    r4 = r8 << 4
    r4 = r4 & 0x10
    r0 |= r4
    r0 <= insert(r3, p:6, l:26)
    r0 = r0 | 0xA
    b[r9+38] = r0
    r0 = b[r5+3] (u)
    b[sp+50] = r0
    r0 = b[r5+4] (u)
    r4 = r0 & 0xFFFFFF03  #
    r3 = b[r5+5] (u)
    r4 <= insert(r3, p:4, l:28)
    r3 = r4 | 0xC
    b[sp+51] = r3
    if ((r0 & 2) == 0) goto L0204d3a0
    rep 16 {
    r0 = b[r1++=1] (u)
    b[r2++=1] = r0
    }
L0204d3a0:
    r0 = b[r5+7] (u)
    r1 = b[r5+6] (u)
    r1 <= insert(r0, p:8, l:24)
    h[sp+48] = r1
    r0 = sp + 0
    r0 += 40
    r1 = r5 + 8
    rep 8 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r5 = L01c202e8
    r2 = b[r5+1] (u)
    r0 = r2 & 0xFFFFFF0F  #
    r3 = b[r5+2] (u)
    r1 = 255
    if (r3 < r0) goto L0204d3d4
    r1 = 0
    if ((r2 & 0x30) == 0) goto L0204d422
L0204d3d4:
    r8 = 0
    r7 = 114
    r6 = 0
    r2 = 0
    goto L0204d3ec
L0204d3de:
    r4 = r2 + r5
    r3 = b[r4+4] (u)
    if (r3 == r1) goto L0204d3f2
    r6 += 1  ; @add.ri.u5
    r7 += 1  ; @add.ri.u5
    r2 += 1  ; @add.ri.u5
L0204d3ec:
    ifs (r2 < r0) goto L0204d3de
    goto L0204d424
L0204d3f2:
    if (r1 != 255) {  ; @if.ne.ri.s12
    r0 = r6.b0 (u)
    call L0204d1b0
    }
    r0 = r7.l (u)
    r1 = sp + 0
    r2 = 52
    call bond_records_and_prints_bond_write  ; @call.xl
    ifs (r0 < 1) goto L0204d424
    r8 = 1  #
    b[r5+3] = r6
    r0 = b[r5+2] (u)
    b[r4+4] = r0
    r0 += 1  ; @add.ri.u5
    b[r5+2] = r0
    r0 = 1
    call L0204cac0
    goto L0204d424
L0204d422:
    r8 = 0
L0204d424:
    r0 = r8
    sp += 52
    {pc, r11-r4} = [sp++]
L0204d42a:
    [--sp] = {rets, r4}
    r1 = L01c21b24
    r2 = [r1+0]
    if (r2 == 0) goto L0204d44c
    r1 = 0
    r3 = 0
    goto L0204d446
L0204d43c:
    r4 = h[r2+0] (u)
    if (r4 == r0) goto L0204d450
    r3 += 1  ; @add.ri.u5
    r2 += 4  ; @add.ri.u5
L0204d446:
    ifs (r3 <= 23) goto L0204d43c
    goto L0204d456
L0204d44c:
    r1 = 0
    goto L0204d456
L0204d450:
    r0 = h[r2+2] (u)
    r1 = r0 & 0xF
L0204d456:
    r0 = r1.l (u)
    {pc, r4} = [sp++]
L0204d45a:
    [--sp] = {rets, r4}
    r1 = L01c21b24
    r3 = [r1+0]
    if (r3 == 0) goto L0204d4a4
    r2 = 0
    r1 = r3
    goto L0204d476
L0204d46c:
    r4 = h[r1+0] (u)
    if (r4 == 9) goto L0204d48e
    r2 += 1  ; @add.ri.u5
    r1 += 4  ; @add.ri.u5
L0204d476:
    ifs (r2 <= 23) goto L0204d46c
    if (r0 == 0) goto L0204d4a4
    r1 = 0
    goto L0204d488
L0204d480:
    r2 = h[r3+0] (u)
    if (r2 == 0) goto L0204d4a6
    r1 += 1  ; @add.ri.u5
    r3 += 4  ; @add.ri.u5
L0204d488:
    ifs (r1 <= 23) goto L0204d480
    {pc, r4} = [sp++]
L0204d48e:
    if (r0 == 0) goto L0204d49e
    r0 = r0 & 0xF  #
    r2 = h[r1+2] (u)
    r2 = r2 & 0xFFFFFFF0
    r0 |= r2
    goto L0204d4a2
L0204d49e:
    r0 = 0
    h[r1+0] = r0
L0204d4a2:
    h[r1+2] = r0
L0204d4a4:
    {pc, r4} = [sp++]
L0204d4a6:
    r1 = 9
    r4 = r0 & 0xF  #
    h[r3+0] = r1
    r1 = h[r3+2] (u)
    r0 = r1 & 0xFFFFFFF0
    r0 |= r4
    h[r3+2] = r0
    call L0204c5f4
    r4 <= insert(r0, p:4, l:16)
    h[r3+2] = r4
    {pc, r4} = [sp++]
L0204d4c4:
    [--sp] = {rets, r6-r4}
    r3 = L0204c38c
    goto L0204d4f4
L0204d4ce:
    r5 = uextra(r2, p:12, l:4)  #
    r4 = b[r0++=1] (u)
    r6 = r4 >> 4
    r5 ^= r6
    r5 = h[r3+r5<<1] (u)
    r2 = r2 << 4
    r2 ^= r5
    r5 = uextra(r2, p:12, l:4)
    r4 = r4 & 0xFFFFFF0F
    r4 ^= r5
    r4 = h[r3+r4<<1] (u)
    r2 = r2 << 4
    r2 ^= r4
    r1 += -1
L0204d4f4:
    r4 = r1.l (u)
    if (r4 != 0) goto L0204d4ce
    r0 = r2.l (u)
    {pc, r6-r4} = [sp++]
L0204d4fc:
    [--sp] = {rets, r5, r4}
    sp += -4
    r4 = r0
    r0 = r4 + 3
    r5 = L01c26ec0
    r1 = r5 + 3
    rep 3 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r1 = 6
    r2 = 0
    r0 = r5
    call L0204d4c4
    r2 = r0
    [sp] = r2
    r0 = r2 >> 8
    b[r4+1] = r0
    b[r4+0] = r2
    r5 = b[r5+2] (u)
    r0 = sp + 0
    r1 = 2
    call L0204d4c4
    r0 += r5  ; @add.rr
    b[r4+2] = r0
    sp += 4
    {pc, r5, r4} = [sp++]
L0204d534:
    [--sp] = rets
    r0 = L01c202a0
    r1 = 1
    b[r0+0] = r1
    call L02042e64  ; @call.xl
    goto L0204d550
L0204d548:
    r0 = 2
    call L0203feb8  ; @call.xl
L0204d550:
    call L02042e88  ; @call.xl
    if (r0 == 0) goto L0204d548
    r0 = L0204fe44
    r1 = L02039fa0  ; "btstack"
    call phase3_p3_task_create  ; @call.xl
    pc = [sp++]
L0204d56c:
    r0 = L01c202a0
    r0 = b[r0+0] (u)
    r1 = 1
    r0 = r1 & ~r0
    rts
L0204d57c:
    r2 = r0
L0204d57e:
    r2 = [r2+0]
    if (r2 == 0) goto L0204d588
    if (r2 != r1) goto L0204d57e
    rts
L0204d588:
    r2 = [r0+0]
    [r1+0] = r2
    [r0+0] = r1
    rts
L0204d590:
    [--sp] = {rets, r4}
    [r0+0] = 0x0
    r3 = r2
    r4 = 1
    goto L0204d5a2
L0204d59c:
    call L0204d57c
    r1 += r3  ; @add.rr
    r4 += -1
L0204d5a2:
    if (r4 != 0) goto L0204d59c
    {pc, r4} = [sp++]
L0204d5a6:
    r2 = [r0+0]
    if (r2 == 0) goto L0204d5b2
    r0 = r2
    if (r2 != r1) goto L0204d5a6
    rts
L0204d5b2:
    [r1+0] = 0x0
    [r0+0] = r1
    rts
L0204d5ba:
    [--sp] = rets
    r1 = r0
    r0 = L01c21718
    call L0204d5a6
    pc = [sp++]
L0204d5c8:
    [--sp] = {rets, r10-r4}
    sp += -52
    r0 = 0
    r10 = 0
    call L0204cac0
    r6 = L01c202e8
    if (r0 != 1) goto L0204d642
    r9 = 255
    r7 = 0
    r8 = 0
    goto L0204d634
L0204d5e8:
    r0 = sp + 0
    r1 = r4
    call L0204ca86
    r1 = r4 + r6
    r2 = b[r1+4] (u)
    if (r0 != 1) goto L0204d608
    r0 = b[r6+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r2 >= r0) goto L0204d60e
    r8 = r8 + 1
    goto L0204d632
L0204d608:
    if (r2 == 255) goto L0204d632
    goto L0204d648
L0204d60e:
    b[r1+4] = r9
    r5 = sp + 0
    r1 = 255
    r2 = 52
    r0 = r5
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 114
    r2 = 52
    r1 = r5
    call bond_records_and_prints_bond_write  ; @call.xl
    r10 = r10 | 0x1
L0204d632:
    r7 += 1  ; @add.ri.u5
L0204d634:
    r4 = r7.b0 (u)  #
    r0 = b[r6+1] (u)
    r0 = r0 & 0xFFFFFF0F
    if (r4 < r0) goto L0204d5e8
    goto L0204d650
L0204d642:
    call L0204cb1e
    goto L0204d6d4
L0204d648:
    r0 = 255
    r10 = r10 | 0x2  #
    b[r1+4] = r0
L0204d650:
    r0 = r10 | 0x80  #
    r2 = b[r6+2] (u)
    r1 = uextra(r8, p:0, l:8)
    if (r1 != r2) {
    r10 = r0
    }
    if ((r10 & 0xFF) == 0) goto L0204d6d4
    b[r6+2] = r8
    r0 = b[r6+1] (u)
    r0 = r0 & 0xFFFFFF0F
    r2 = 0
    goto L0204d6a2
L0204d674:
    r4 = 0
L0204d676:
    if (r4 >= r0) goto L0204d686
    r5 = r4 + r6
    r5 = b[r5+4] (u)
    r4 += 1  ; @add.ri.u5
    if (r5 != r3) goto L0204d676
    goto L0204d6a0
L0204d686:
    r4 = r6 + 4
    r5 = r0
    goto L0204d69e
L0204d68c:
    r7 = b[r4+0] (u)
    if (r7 == 255) goto L0204d69a
    if (r7 > r3) {
    r7 += -1
    b[r4+0] = r7
    }
L0204d69a:
    r5 += -1
    r4 += 1  ; @add.ri.u5
L0204d69e:
    if (r5 != 0) goto L0204d68c
L0204d6a0:
    r2 += 1  ; @add.ri.u5
L0204d6a2:
    r3 = r2.b0 (u)
    if (r3 != r1) goto L0204d674
    r1 = r6 + 4
    r3_r2 = 0
    goto L0204d6c6
L0204d6ae:
    r7 = r3.b0 (u)  #
    r5 = b[r1++=1] (u)
    r4 = r2
    if (r5 <= r7) {
    r4 = r3
    }
    if (r5 == 255) {  ; @if.eq.ri.s12
    r4 = r3
    }
    r0 += -1
    r2 += 1  ; @add.ri.u5
    r3 = r4
L0204d6c6:
    if (r0 != 0) goto L0204d6ae
    b[r6+2] = r8
    b[r6+3] = r3
    r0 = 1
    call L0204cac0
L0204d6d4:
    r0 = b[r6+1] (u)
    if ((r0 & 0xF) == 0) {
    r0 = 1
    } else {
    r0 = 0
    }
    call L02053602  ; @call.xl
    sp += 52
    {pc, r10-r4} = [sp++]
L0204d6e8:
    [--sp] = rets
    r2 = r0
    r0 = r1
    call L0204cec8
    ifs (r0 >= 0) {  ; @ifs.ge.ri.s12
    r0 = r0 << 3
    r1 = L01c2195c
    [r1+r0] = r2
    }
    pc = [sp++]
L0204d704:
    [--sp] = {rets, r4}
    r0 = 0
    call L0204cac0
    r4 = L01c202e8
    r0 = b[r4+1] (u)
    r1 = r0 & 0xFFFFFF0F
    if (r1 == 5) goto L0204d722
    call L0204cb1e
    r0 = b[r4+1] (u)
L0204d722:
    r0 = r0 & 0xFFFFFFC0
    r0 = r0 | 0x15
    b[r4+1] = r0
    r0 = 1
    call L0204cac0
    r0 = b[r4+1] (u)
    if ((r0 & 0xF) == 0) {
    r0 = 1
    } else {
    r0 = 0
    }
    call L02053602  ; @call.xl
    {pc, r4} = [sp++]
L0204d744:
    [--sp] = rets
    r0 = L01c21940
    r1 = boundary_hooks_packet_handler
    [r0+4] = r1
    call L0204d5ba
    pc = [sp++]
L0204d75a:
    r0 = L01c21950
    r1 = boundary_hooks_packet_handler
    [r0+0] = r1
    rts
L0204d76a:
    r0 = L01c202a8
    r1 = 1
    b[r0+0] = r1
    rts
L0204d776:
    [--sp] = {rets, r8-r4}
    r4 = L01c21714
    r1 = 0
    r2 = 556
    r5 = 0
    r0 = r4
    call effect_enable_memset  ; @call.xl
    call L0204a9c0  ; @call.xl
    r0 = L01c200c4
    r1 = 16383
    r1 = r1 + 0xC000  #
    h[r0+6] = r1
    h[r0+4] = r1
    h[r0+2] = r1
    h[r0+0] = r1
    call L0204a9d8  ; @call.xl
    r1 = r4 + 538
    h[r1+2] = r0
    call L0204a9e4  ; @call.xl
    r2 = 500  #
    b[r1+0] = r0
    r0 = 6
    r0 = 3200  #
    h[r1+4] = r0
    h[r1+6] = r0
    h[r1+8] = r5
    h[r1+10] = r2
    r2 = 10
    h[r1+12] = r2
    h[r1+14] = r0
    r8 = L01c202f8
    r0 = L01c21b28
    [r8+8] = r0
    r4 = L01c21b6c
    [r8+4] = r4
    r0 = 0
    r1 = 0
    d[r4+8] = r1_r0
    d[r4+0] = r1_r0
    r7 = L01c21948
    r0 = 1240  #
    [r7+0] = r4
    call L0203c15c  ; @call.xl
    r5 = r0
    if (r5 == 0) goto L0204d91c  ; @beq.ri
    r2 = 1240  #
    [r4+8] = r5
    r1 = 0
    r6 = 0
    call effect_enable_memset  ; @call.xl
    r2 = 1240
    r1_r0 = r5_r4
    call L0204d590
    r0 = 128
    call L0203c15c  ; @call.xl
    if (r0 == 0) goto L0204d91c
    r2 = [r7+0]
    [r2+12] = r0
    rep 32 {
    [r0++=4] = r6
    }
    r1 = [r2+12]
    r0 = r2 + 4
    r2 = 128
    call L0204d590
    r0 = [r8+8]
    r1 = r0 + 12
    rep 14 {
    [r1++=4] = r6
    }
    r1 = L01c2194c
    [r1+0] = r0
    r1 = 255
    b[r0+62] = r1
    r1 = 64
    h[r0+64] = r1
    [r0+36] = r6
    [r0+8] = r6
    r1 = L020516fa
    [r0+] = {r6, r1}
    [r0+40] = r6
    r0 = L01c21950
    [r0+0] = r6
    r0 = L01c21954
    r1 = L020500a6
    [r0+4] = r1
    call L0204d5ba
    r4 = L01c21b7c
    r1 = 0
    r2 = 184
    r0 = r4
    call effect_enable_memset  ; @call.xl
    r0 = r4 + 12
    r1 = r4 + 48
    r2 = 128
    call L020012ae  ; @call.xl
    r0 = L02051b04
    r1 = r4  #
    [r4+4] = r0
    [r4+8] = r6
    r0 = L01c202a4
    call L0204d5a6
    r0 = 1
    b[r4+180] = r0
    call L02054430  ; @call.xl
    call phase3_p10_bt_init_calls  ; @call.xl
    r5 = L01c26838
    r0 = [r5+0]
    if (r0 != 0) goto L0204d91a
    r0 = 176
    call L0203c15c  ; @call.xl
    r4 = r0
    [r5+0] = r4
    if (r4 == 0) goto L0204d91c
    r1 = 0
    r2 = 176
    call effect_enable_memset  ; @call.xl
    r0 = phase3_p12_ancs_handle_hci_event
    [r4+136] = r0
    r0 = r4 + 132
    call L0204d5ba
    r0 = [r5+0]
    r1 = 1
    b[r0+174] = r1
    b[r0+175] = r1
L0204d91a:
    {pc, r8-r4} = [sp++]
L0204d91c:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204d928:
    goto L0204d928
L0204d92a:
    [--sp] = {rets, r8-r4}
    r4 = r0
    r8 = L01c21a20
    r7 = 0
    r5 = r8
    goto L0204d958
L0204d93a:
    r2 = 6
    r1_r0 = r5_r4
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204d956
    r6 = [r5+12]
    r0 = r6 & 0x20000000
    r1 = r7
    r1_r0 >>= 29
    if ((r0 & 1) != 0) goto L0204d962
L0204d956:
    r5 += 24  ; @add.ri.u5
L0204d958:
    r0 = r8 + 48
    if (r5 < r0) goto L0204d93a
    goto L0204d964
L0204d962:
    r7 = r5
L0204d964:
    r0 = r7
    {pc, r8-r4} = [sp++]
L0204d968:
    [--sp] = {rets, r5, r4}
    sp += -12
    r4 = 0
    [sp+8] = r4
    r5 = 0
    d[sp] = r5_r4
    if (r0 == 0) goto L0204d982
    r4 = sp + 0
    r4 |= 1
    rep 6 {
    r5 = b[r0++=1] (u)
    b[r4++=1] = r5
    }
L0204d982:
    b[sp] = r2
    r0 = r1  #
    [sp+8] = r3
    r2 = sp + 0
    r1 = r2
    call phase3_p15_bt_event_notify  ; @call.xl
    sp += 12
    {pc, r5, r4} = [sp++]
L0204d998:
    [--sp] = {rets, r13, r12, r10-r4}
    r9 = r2
    r4 = r1
    r5 = r0
    r6 = 170
    r7 = L01c21988
    if (r5 == 0) goto L0204da08
    call L0204d92a
    r10 = r0
    if (r0 == 0) goto L0204da08
    r8 = L01c202b4
    if (r4 == 11) goto L0204d9c0
    if (r4 != 14) goto L0204da20
L0204d9c0:
    r0 = r7 + 244
    r1 = r0
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r8++=1] = r2
    }
L0204d9ce:
    r1 = r5
L0204d9d0:
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
L0204d9d6:
    if (r9 == 0) goto L0204d9f8
L0204d9da:
    r1 = b[r10+16] (u)
    r0 = [r10+12]
    r2 = r0 & 0xF
    r3 = 0
    r2 = r2 ^ 0x5
    if (r2 == 0) goto L0204d9f2
    r9 = 46
L0204d9f2:
    b[r10+11] = r9
    goto L0204da00
L0204d9f8:
    r1 = b[r10+16] (u)
    r0 = [r10+12]
L0204da00:
    r1_r0 >>= 38
    r6 = r0 & 0x1
L0204da08:
    if (r4 == 0) goto L0204da1c
    r0 = 316
    b[r7+r0] = r4
    r1 = 3
    r0 = r5
    r2 = r4
    r3 = r6
    call L0204d968
L0204da1c:
    {pc, r13, r12, r10-r4} = [sp++]
L0204da20:
    r6 = r7 + 164
    r13 = 0
    goto L0204da54
L0204da28:
    r0 = r7 + 244
    r2 = 6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204da52
    r1 = b[r6+4] (u)
    r0 = [r6+0]
    r12 = r0 & 0x20000000
    if (r12 == 0) goto L0204da52
    r0 = r0 & 0xF
    r1 = r13
    r0 = r0 ^ 0x5
    if (r0 == 0) goto L0204da52
    r0 = h[r6+-6] (u)
    if (r0 != 0) goto L0204d9d6
L0204da52:
    r6 += 24  ; @add.ri.u5
L0204da54:
    r0 = r7 + 200
    r1 = r6 + -12
    if (r1 < r0) goto L0204da28
    r1 = r7 + 152
    r3 = 0
    goto L0204da8a
L0204da68:
    r13 = b[r1+16] (u)
    r12 = [r1+12]
    r2 = r12 & 0x20000000
    if (r2 == 0) goto L0204da86
    r12 = r12 & 0xF
    r13 = r3
    r6 = r12 ^ 0x5
    if (r6 == 0) goto L0204da86
    r6 = h[r1+6] (u)
    if (r6 != 0) goto L0204dac2
L0204da86:
    r1 += 12  ; @add.ri.u5
    r1 += 12  ; @add.ri.u5
L0204da8a:
    if (r1 < r0) goto L0204da68
    if (r4 != 0) goto L0204da94
    if (r9 == 45) goto L0204d9da
L0204da94:
    r0 = h[r10+6] (u)
    if (r0 == 0) goto L0204d9d6
    r1 = L0204c375
    r2 = 6
    r0 = r8
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204dac8
    r0 = r7 + 244
    r1 = r8
    rep 6 {
    r2 = b[r1++=1] (u)
    b[r0++=1] = r2
    }
    r0 = 0
    rep 6 {
    b[r8++=1] = r0
    }
    goto L0204d9d6
L0204dac2:
    r0 = r7 + 244
    goto L0204d9d0
L0204dac8:
    r0 = r7 + 244
    goto L0204d9ce
L0204dace:
    r0 = L01c202cd
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r3, p:8, l:8)
    r0 <= insert(r2, p:16, l:16)
    r1 = r0 >> 6
    r0 = r0 >> 25
    r0 |= r1
    r0 = r0 & 0x1
    rts
L0204daf4:
    [--sp] = {rets, r9-r4}
    sp += -32
    r5 = r1
    r6 = r0
    r8 = L01c21ad4
    r0 = r8
    call L02040614  ; @call.xl
    r4 = 0
    r0 = [r4+0]
    call r0
    if (r0 == 0) goto L0204db74
    r0 = sp + 0
    r7 = r0 + 10
    r9 = 255
    goto L0204db46
L0204db1c:
    if (r6 == 0) goto L0204db2c
    r2 = 6
    r1_r0 = r7_r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204db46
    goto L0204db56
L0204db2c:
    r2 = [r4+16]
    r0 = 2
    r1 = 32
    call r2
    r0 = sp + 0
    r1 = r0
    rep 32 {
    b[r1++=1] = r9
    }
    r2 = r5  #
    r3 = [r4+12]
    r1 = 32
    call r3
L0204db46:
    r2 = r5  #
    r3 = [r4+8]
    r0 = sp + 0
    r1 = 32
    call r3
    if (r0 == 32) goto L0204db1c
    goto L0204db70
L0204db56:
    r2 = [r4+16]
    r0 = 2
    r1 = 32
    call r2
    r0 = sp + 0
    r1 = 255
    r2 = r0
    rep 32 {
    b[r2++=1] = r1
    }
    r2 = r5  #
    r3 = [r4+12]
    r1 = 32
    call r3
L0204db70:
    r0 = [r4+4]
    call r0
L0204db74:
    r0 = r8
    call L0204074c  ; @call.xl
    sp += 32
    {pc, r9-r4} = [sp++]
L0204db80:
    r0 = 319
    r1 = L01c21988
    r2 = L01c202bc
    r2 = b[r2+16] (u)
    r0 = b[r1+r0] (u)
    r1 = 1
    if (r2 != 0) goto L0204db9e
    r1 = r2
L0204db9e:
    r0 &= r1
    rts
L0204dba2:
    [--sp] = rets
    call L0204aeec  ; @call.xl
    pc = [sp++]
L0204dbac:
    [--sp] = {rets, r6-r4}
    sp += -12
    r4 = r1
    r5 = r0
    r0 = 0
    r1 = L01c21714
    r2 = [r1+4]
    [sp] = r0
    r0 = r1 + 4
    [sp+4] = r0
    [sp+8] = r2
    goto L0204dbda
L0204dbc8:
    r0 = sp + 0
    call L0204cbb4
    r2 = r5  #
    r6 = [r0+4]
    r0 = 4
    r1 = 0
    r3 = r4
    call r6
L0204dbda:
    r0 = sp + 0
    call L0204cb98
    if (r0 != 0) goto L0204dbc8
    sp += 12
    {pc, r6-r4} = [sp++]
L0204dbe6:
    r0 = L01c202cd
    r1 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r1, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r0 = b[r0+0] (u)
    r0 <= insert(r3, p:8, l:8)
    r0 <= insert(r2, p:16, l:16)
    r0 = uextra(r0, p:23, l:1)
    rts
L0204dc06:
    [--sp] = {rets, r8-r4}
    r8 = 0
    r3 = [r8+0]
    r5 = r2
    r6 = r1
    r4 = r0
    call r3
    if (r0 == 0) goto L0204dc5a
    r7 = r4 + 10
L0204dc1a:
    r3 = [r8+8]
    r1 = 32
    r0 = r4
    r2 = r5
    call r3
    if (r0 != 32) goto L0204dc50
    r2 = 6
    r1_r0 = r7_r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204dc1a
    r0 = b[r4+1] (u)
    r5 = b[r4++=2] (u)
    r5 <= insert(r0, p:8, l:8)
    r1 = 30
    r0 = r4
    call phase3_p11_crc_get_16bit  ; @call.xl
    r4 = 1
    if (r5 == r0) goto L0204dc52
L0204dc50:
    r4 = 0
L0204dc52:
    r0 = [r8+4]
    call r0
    goto L0204dc5c
L0204dc5a:
    r4 = 0
L0204dc5c:
    r0 = r4
    {pc, r8-r4} = [sp++]
L0204dc60:
    [--sp] = {rets, r7-r4}
    sp += -48
    r6 = r2
    r5 = r1
    r7 = r0
    r4 = L01c21ad4
    r0 = r4
    call L02040614  ; @call.xl
    call L0204dbe6
    if (r0 == 0) goto L0204dc8a
    r0 = L0204c37b
    rep 16 {
    r1 = b[r0++=1] (u)
    b[r5++=1] = r1
    }
    goto L0204dcca
L0204dc8a:
    r0 = L01c202ba
    r0 = b[r0+0] (u)
    if (r0 == 0) goto L0204dc9c
    r0 = 0
    rep 16 {
    b[r5++=1] = r0
    }
    goto L0204dcca
L0204dc9c:
    r0 = sp + 0
    r1 = r7
    r2 = r6
    call L0204dc06
    if (r0 == 0) goto L0204dcd8
    r0 = 0
    r1 = 0
    d[sp+40] = r1_r0
    d[sp+32] = r1_r0
    r0 = sp + 0
    r6 = r0 + 16
    r0 = sp + 32
    r2 = 16
    r1 = r6
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204dcd8
    rep 16 {
    r0 = b[r6++=1] (u)
    b[r5++=1] = r0
    }
L0204dcca:
    r0 = r4
    call L0204074c  ; @call.xl
    r0 = 1
L0204dcd4:
    sp += 48
    {pc, r7-r4} = [sp++]
L0204dcd8:
    r0 = r4
    call L0204074c  ; @call.xl
    r0 = 0
    goto L0204dcd4
L0204dce4:
    [--sp] = {rets, r15-r4}
    sp += -124
    r10 = 0
    r2 = [r10+0]
    r4 = r1
    r5 = r0
    call r2
    if (r0 == 0) goto L0204ddce
    r0 = sp + 92
    r6 = r0 | 0x2
    r9 = 65535
    r8 = 0
    goto L0204dd58
L0204dd06:
    r0 = h[r6+0] (u)
    if (r0 == r9) goto L0204dd58
    r7 = h[sp+92] (u)
    r1 = 30
    r0 = r6
    call phase3_p11_crc_get_16bit  ; @call.xl
    if (r7 != r0) goto L0204dd58
    r0 = h[r6+0] (u)
    ifs (r8 >= r0) goto L0204dd30
    r1 = sp + 28
    r2 = sp + 92
    rep 32 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r8 = r0
L0204dd30:
    if (r0 == r9) goto L0204dd58
    r7 = h[sp+92] (u)
    r1 = 30
    r0 = r6
    call phase3_p11_crc_get_16bit  ; @call.xl
    if (r7 != r0) goto L0204dd58
    r0 = h[r6+0] (u)
    ifs (r8 >= r0) goto L0204dd58
    r1 = sp + 28
    r2 = sp + 92
    rep 32 {
    r3 = b[r2++=1] (u)
    b[r1++=1] = r3
    }
    r8 = r0
L0204dd58:
    r3 = [r10+8]
    r0 = sp + 92
    r1 = 32
    r2 = r4
    call r3
    if (r0 == 32) goto L0204dd06
    r0 = [r10+4]
    call r0
    if (r8 == 0) goto L0204ddce
    r0 = r5 + 10
    r1 = sp + 28
    r1 += 10  ; @add.ri.u5
    r2 = 6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204ddce
    r0 = r5 + 16
    r1 = sp + 28
    r1 += 16  ; @add.ri.u5
    r2 = 16
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204ddce
    r0 = b[r5+6] (u)
    r1 = b[sp+34] (u)
    if (r0 != r1) goto L0204ddce
    r0 = b[r5+7] (u)
    r1 = b[sp+35] (u)
    if (r0 != r1) goto L0204ddce
    r0 = b[r5+4] (u)
    r1 = b[sp+32] (u)
    if (r0 != r1) goto L0204ddce
    r0 = b[r5+8] (u)
    r1 = b[sp+36] (u)
    if (r0 != r1) goto L0204ddce
    r0 = b[r5+9] (u)
    r1 = b[sp+37] (u)
    if (r0 != r1) goto L0204ddce
    r0 = b[r5+5] (u)
    r1 = b[sp+33] (u)
    if (r0 == r1) goto L0204df52
L0204ddce:
    r0 = [r10+0]
    call r0
    if (r0 == 0) goto L0204df52
    r0 = sp + 60
    r1 = r0 + 16
    r9 = -1  #
    [sp+4] = r1
    r1 = r5 + 16
    r13_r12 = 0  #
    [sp] = r1
    r1 = r0 + 10
    r15 = 0  #
    [sp+12] = r1
    [sp+20] = r5
    r1 = r5 + 10
    r6 = r0 | 0x2  #
    [sp+8] = r1
    r8 = 65535
    r0 = 0
    r14 = r8  #
    [sp+16] = r0
    [sp+24] = r0
L0204de06:
    r11 = r13
    goto L0204de30
L0204de0a:
    r2 = [r10+16]
    r0 = 2
    r1 = 32
    call r2
    r0 = sp + 60
    r1 = r0
    rep 16 {
    h[r1++=2] = r9
    }
    r3 = [r10+12]
    r1 = 32
    r2 = r4
    call r3
    goto L0204de30
L0204de2a:
    r12 = r12 | 0x2  #
    [sp+24] = r7
L0204de30:
    r0 = [r10+24]
    call r0
    r3 = [r10+8]
    r7 = r0
    r0 = sp + 60
    r1 = 32
    r2 = r4
    call r3
    r0 = r0.l (u)
    if (r0 != 32) goto L0204dee4
    r0 = h[r6+0] (u)
    if (r0 == r8) goto L0204de2a
    r5 = h[sp+60] (u)
    r1 = 30
    r0 = r6
    call phase3_p11_crc_get_16bit  ; @call.xl
    if (r5 != r0) goto L0204de0a
    r13 = h[r6+0] (u)
    r0 = uextra(r14, p:0, l:16)
    if (r0 > r13) {
    r12 = r12 | 0x4
    r14 = r13
    [sp+16] = r7
    }
    r0 = uextra(r11, p:0, l:16)
    if (r0 >= r13) {
    r13 = r11
    }
    r0 = uextra(r15, p:0, l:16)
    if (r0 != 0) goto L0204de06
    r2 = 6
    r1_r0 = d[sp+8]
    call capture_journal_compare  ; @call.xl
    r15 = 0
    if (r0 != 0) goto L0204de06
    r2 = 16
    r1_r0 = d[sp]
    call capture_journal_compare  ; @call.xl
    if (r0 == 0) goto L0204dedc
    r11 = r14  #
    r1 = [sp+20]
    r0 = 255
    b[r1+6] = r0
    b[r1+7] = r0
    r0 = 0
    b[r1+5] = r0
    b[r1+9] = r0
    r0 = L01c202cd
    r14 = b[r0+3] (u)
    r2 = b[r0+2] (u)
    r2 <= insert(r14, p:8, l:8)  #
    r3 = b[r0+1] (u)
    r5 = b[r0+0] (u)
    r5 <= insert(r3, p:8, l:8)
    r5 <= insert(r2, p:16, l:16)
    r0 = 48
    if ((r5 & 0x2000000) == 0) {
    r0 = 3
    }
    r14 = r11  #
    b[r1+8] = r0
L0204dedc:
    r12 = r12 | 0x1
    r15 = r7
    goto L0204de06
L0204dee4:
    r0 = r11 + 1
    r2 = r0.l (u)
    r3 = r8
    r1 = 1
    if (r2 != r3) {
    r1 = r0
    }
    r5 = [sp+20]
    b[r5+2] = r1
    r0 = r1 >> 8
    b[r5+3] = r0
    r0 = r5 + 2
    r1 = 30
    call phase3_p11_crc_get_16bit  ; @call.xl
    r1 = r0 >> 8
    r0 = uextra(r12, p:0, l:16)  #
    b[r5+0] = r0
    b[r5+1] = r1
    if (r0 == 0) goto L0204df26
    if ((r0 & 1) != 0) goto L0204df34
    r15 = [sp+24]  ; @ld.w.sp.l
    if ((r0 & 2) != 0) goto L0204df34
    r15 = [sp+16]  ; @ld.w.sp.l
    if ((r0 & 4) != 0) goto L0204df34
L0204df26:
    r0 = [r10+24]
    call r0
    r1 = r8 + -31
    r15 = r0 + r1
L0204df34:
    r2 = [r10+16]
    r1 = uextra(r15, p:0, l:16)
    r0 = 0
    call r2
    r3 = [r10+12]
    r1 = 32
    r0 = r5
    r2 = r4
    call r3
    r0 = [r10+4]
    call r0
L0204df52:
    sp += 124
    {pc, r15-r4} = [sp++]
L0204df56:
    [--sp] = {rets, r9-r4}
    sp += -32
    r5 = r2
    r6 = r1
    r7 = r0
    r4 = L01c21ad4
    r0 = r4
    call L02040614  ; @call.xl
    call L0204dbe6
    if (r0 != 0) goto L0204dfe6
    r0 = L01c202ba
    r0 = b[r0+0] (u)
    if (r0 != 0) goto L0204dfe6
    r0 = sp + 0
    r1 = r7
    r2 = r5
    call L0204dc06
    if (r0 != 0) goto L0204dfce
    r0 = sp + 0
    r8 = 0
    rep 32 {
    b[r0++=1] = r8
    }
    r0 = 255
    b[sp+7] = r0
    b[sp+6] = r0
    r0 = L01c202cd
    r9 = b[r0+3] (u)
    r3 = b[r0+2] (u)
    r3 <= insert(r9, p:8, l:8)  #
    r1 = b[r0+1] (u)
    r2 = b[r0+0] (u)
    b[sp+5] = r8
    b[sp+9] = r8
    r2 <= insert(r1, p:8, l:8)
    r2 <= insert(r3, p:16, l:16)
    r0 = 48
    if ((r2 & 0x2000000) == 0) {
    r0 = 3
    }
    b[sp+8] = r0
L0204dfce:
    r0 = sp + 0
    r1 = r0 + 10
    rep 6 {
    r2 = b[r7++=1] (u)
    b[r1++=1] = r2
    }
    r1 = r0 + 16
    rep 16 {
    r2 = b[r6++=1] (u)
    b[r1++=1] = r2
    }
    r1 = r5
    call L0204dce4
L0204dfe6:
    r0 = r4
    call L0204074c  ; @call.xl
    sp += 32
    {pc, r9-r4} = [sp++]
L0204dff2:
    [--sp] = {rets, r7-r4}
    sp += -48
    r5 = r1
    r6 = r0
    r4 = L01c21ad4
    r0 = r4
    call L02040614  ; @call.xl
    call L0204dbe6
    if (r0 == 0) goto L0204e01e
L0204e00e:
    r0 = r4
    call L0204074c  ; @call.xl
    r5 = 0
L0204e018:
    r0 = r5.b0 (u)
    sp += 48
    {pc, r7-r4} = [sp++]
L0204e01e:
    r0 = sp + 16
    r2 = 0
    r1 = r6
    call L0204dc06
    if (r0 == 0) goto L0204e03c
    if (r5 != 255) goto L0204e096
    r0 = r4
    call L0204074c  ; @call.xl
    r5 = b[sp+20] (u)
    goto L0204e018
L0204e03c:
    if (r5 == 255) goto L0204e00e
    r0 = 0
    r1 = 0
    d[sp+8] = r1_r0
    d[sp] = r1_r0
    r0 = sp + 16
    r2 = r0 + 10
    rep 32 {
    b[r0++=1] = r1
    }
    r0 = r6
    rep 6 {
    r1 = b[r0++=1] (u)
    b[r2++=1] = r1
    }
    r0 = 255
    r1 = L01c202cd
    r2 = b[r1+3] (u)
    r3 = b[r1+2] (u)
    r3 <= insert(r2, p:8, l:8)  #
    r7 = b[r1+1] (u)
    r1 = b[r1+0] (u)
    b[sp+23] = r0
    b[sp+22] = r0
    r1 <= insert(r7, p:8, l:8)
    r1 <= insert(r3, p:16, l:16)
    r0 = 48
    if ((r1 & 0x2000000) == 0) {
    r0 = 3
    }
    b[sp+24] = r0
    r1 = sp + 0
    r2 = 0
    r0 = r6
    call L0204df56
L0204e096:
    r1 = b[sp+20] (u)
    r0 = sp + 16
    if (r1 == r5) goto L0204e00e
    b[r0+4] = r5
    r0 = sp + 16
    r1 = 0
    r5 = 0
    call L0204dce4
    r0 = r4
    call L0204074c  ; @call.xl
    goto L0204e018
L0204e0b6:
    [--sp] = {rets, r10-r4}
    r3 = L01c2194c
    r10 = [r3+0]
    r8 = r2
    r9 = r1
    r6 = r0
    r4 = r10 + 51
    r5 = 0
    goto L0204e0ee
L0204e0d0:
    r7 = r4 + -7
    r2 = 6
    r1_r0 = r7_r6
    call capture_journal_compare  ; @call.xl
    if (r0 != 0) goto L0204e0ea
    r0 = b[r4+-1] (u)
    r1 = r0 & 0xFFFFFF0F
    if (r1 == 10) goto L0204e11a
L0204e0ea:
    r4 += 9  ; @add.ri.u5
    r5 += 1  ; @add.ri.u5
L0204e0ee:
    ifs (r5 <= 1) goto L0204e0d0
    r0 = r9 | 0x2
    if (r0 != 38) goto L0204e114
    r0 = r10 + 51
    r1 = 0
    goto L0204e110
L0204e102:
    r2 = b[r0+-1] (u)
    r3 = r2 & 0xFFFFFF0F
    if (r3 != 10) goto L0204e12e
    r0 += 9  ; @add.ri.u5
    r1 += 1  ; @add.ri.u5
L0204e110:
    ifs (r1 <= 1) goto L0204e102
L0204e114:
    r8 = 32
    goto L0204e17c
L0204e11a:
    r1 = r9 + -36
    if (r1 > 3) goto L0204e178
    tbb [r1]
L0204e124:
    .byte (L0204e128 - L0204e124) / 2, (L0204e16e - L0204e124) / 2, (L0204e15e - L0204e124) / 2, (L0204e168 - L0204e124) / 2
L0204e128:
    b[r4+0] = r8
    goto L0204e178
L0204e12e:
    r1 = r0 + -7
    rep 6 {
    r3 = b[r6++=1] (u)
    b[r1++=1] = r3
    }
    r1 = r2 & 0xFFFFFFF0
    r1 = r1 | 0xA
    b[r0+-1] = r1
    if (r9 != 36) goto L0204e150
    b[r0+0] = r8
    r1 = 10
    b[r0+-1] = r1
    goto L0204e17c
L0204e150:
    r1 = 32
    b[r0+0] = r1
    r1 = 10
    r1 <= insert(r8, p:4, l:8)
    b[r0+-1] = r1
    goto L0204e17c
L0204e15e:
    r0 = 10
    r0 <= insert(r8, p:4, l:8)
    b[r4+-1] = r0
    goto L0204e178
L0204e168:
    r8 = r0 >> 4
    goto L0204e17c
L0204e16e:
    r0 = 0
    rep 7 {
    b[r7++=1] = r0
    }
    r0 = 32
    b[r4+0] = r0
L0204e178:
    r8 = b[r4+0] (u)
L0204e17c:
    r0 = uextra(r8, p:0, l:8)
    {pc, r10-r4} = [sp++]
L0204e182:
    [--sp] = {rets, r6-r4}
    r4 = r2
    r6 = r1
    r5 = r0
    r1 = 39
    if (r6 == 0) goto L0204e190
    r1 = 38
L0204e190:
    call L0204e0b6
    if (r6 == 0) goto L0204e19e
    if (r4 == 0) goto L0204e19e
    r0 = r5
    r1 = r4
    call L0204dff2
L0204e19e:
    {pc, r6-r4} = [sp++]
L0204e1a0:
    [--sp] = rets
    call L0204adbc  ; @call.xl
    pc = [sp++]
L0204e1aa:
    [--sp] = rets
    call L0204ae52  ; @call.xl
    pc = [sp++]
L0204e1b4:
    [--sp] = {rets, r4}
    r4 = r0
    call L0204bc90  ; @call.xl
    if (r0 != 0) {  ; @if.ne.ri.s12
    h[r0+10] = r4
    r0 += 24  ; @add.ri.u5
    } else {
    r0 = 0
    }
    {pc, r4} = [sp++]
L0204e1ca:
    [--sp] = {rets, r7-r4}
    sp += -4
    r5 = r2  #
    r6 = [sp+28]
    r4 = r0  #
    [sp] = r6
    r2 = r1 | 0x2000
    r1 = 0
    call L0204cd32
    r1 = 6
    r2 = r5
    call L0204cd32
    r0 = [sp+24]
    r1 = L0204c204
    r6 = [r1+r3<<2]
    b[r4+8] = r3
    b[r4+9] = r0
    r3 = 12
    goto L0204e24c
L0204e1fc:
    r1 = r0 + -49
    if (r1 >= 2) goto L0204e228
    r0 = [sp]
    r1 = r0 + 4
    r1 = r3.l (u)  #
    [sp] = r1
    r0 = [r0+0]
    b[r4+r1] = r0
    r2 = b[r6+0] (u)
    r1 = r3 + 1
    if (r2 == 50) {  ; @if.eq.ri.s12
    r1 = r1.l (u)
    r0 = r0 >> 8
    b[r4+r1] = r0
    r3 += 2  ; @add.ri.u5
    } else {
    r3 = r1
    }
    goto L0204e24a
L0204e228:
    if (r0 != 68) goto L0204e24a
    r0 = [sp]
    r1 = r0 + 4
    [sp] = r1
    r1 = [sp]
    r5 = [r0+0]
    r0 = r1 + 4
    r7 = r3.l (u)  #
    [sp] = r0
    r0 = r4 + r7  #
    r1 = [r1+0]
    r2 = r5
    call effect_parameter_support_memmove  ; @call.xl
    r3 = r5 + r7
L0204e24a:
    r6 += 1  ; @add.ri.u5
L0204e24c:
    r0 = b[r6+0] (s)
    if (r0 != 0) goto L0204e1fc
    r0 = r3 + -4
    r2 = r0.l (u)
    r1 = 2
    r0 = r4
    call L0204cd32
    r0 = r3 + -8
    r2 = r0.l (u)
    r1 = 4
    r0 = r4
    call L0204cd32
    r0 = r3 + -12
    r2 = r0.l (u)
    r1 = 10
    r0 = r4
    call L0204cd32
    r0 = r3.l (u)
    sp += 4
    {pc, r7-r4} = [sp++]
L0204e282:
    [--sp] = {rets, r7-r4}
    r4 = r0
    r7 = r1  #
    r0 = b[r4+1] (u)
    r0 = r0 << 8
    r0 = r0 & 0xF00  #
    r2 = b[r4+0] (u)
    r0 |= r2
    call L0204ad96  ; @call.xl
    r6 = r0
    r5 = r4 + -24
    if (r6 == 0) goto L0204e2e0
    r0 = h[r4+-14] (u)
    r7 += -4
    ifs (r7 > r0) goto L0204e2ea
    r0 = r5
    r1 = r7
    call L0204bdc6  ; @call.xl
    r0 = 0
    h[r4+-12] = r0
    h[r4+-14] = r7
    r0 = 11
    b[r4+-21] = r0
    r0 = b[r4+1] (u)
    r1 = r0 & 0xFFFFFFF0
    r0 = 1
    if (r1 != 16) {  ; @if.ne.ri.s12
    r0 = 2
    }
    b[r4+-18] = r0
    r0 = [r6+236]
    r1 = r5
    call L0204ba62  ; @call.xl
    {pc, r7-r4} = [sp++]
L0204e2e0:
    r0 = r5
    call L0204bd1a  ; @call.xl
    {pc, r7-r4} = [sp++]
L0204e2ea:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204e2f6:
    goto L0204e2f6
L0204e2f8:
    [--sp] = {r3}
    [--sp] = {rets, r7-r4}
    sp += -16
    r4 = r1
    r5 = r0
    r0 = sp + 36
    r1 = L0204c204
    r1 = [r1+r4<<2]
    r6 = r2  #
    [sp+8] = r0
    [sp+12] = r0
    r0 = 8
    goto L0204e344
L0204e318:
    r3 = r2 + -49
    if (r3 >= 2) goto L0204e332
    r2 = sp + 12
    [r2+0] += 4  ; @rmw.add.s12
    r3 = b[r1+0] (u)
    r2 = 2
    if (r3 != 50) {  ; @if.ne.ri.s12
    r2 = 1
    }
    goto L0204e340
L0204e332:
    if (r2 != 68) goto L0204e342
    r2 = [sp+12]
    r3 = r2 + 4
    r0 = r0.l (u)  #
    [sp+12] = r3
    r2 = [r2+0]
L0204e340:
    r0 += r2  ; @add.rr
L0204e342:
    r1 += 1  ; @add.ri.u5
L0204e344:
    r2 = b[r1+0] (s)
    if (r2 != 0) goto L0204e318
    r0 = r0.l (u)
    call L0204e1b4
    r7 = r0
    if (r7 == 0) goto L0204e378
    r0 = sp + 36
    r1 = r5  #
    [sp+8] = r0
    r0 = r6.b0 (u)  #
    [sp+4] = r0
    r2 = 1
    r0 = r7  #
    [sp] = r0
    r3 = r4
    call L0204e1ca
    r1 = r0
    r0 = r7
    call L0204e282
    sp += 16
    {rets, r7-r4} = [sp++]
    sp += 4
    rts
L0204e378:
    call L0203e742  ; @call.xl
    call storage_fault_fatal  ; @call.xl
L0204e384:
    goto L0204e384
L0204e386:
    [--sp] = {r3}
    [--sp] = {rets, r6-r4}
    sp += -12
    r6 = r2
    r4 = r1
    r5 = r0
    call L0204ccf6
    if (r0 == 0) goto L0204e3ba
    call L0204cd18
    r0 = sp + 28
    r1 = r6.b0 (u)  #
    [sp+8] = r0
    r3 = r4  #
    [sp+4] = r0
    r0 = L01c2171c
    r2 = 5
    r1 = r5  #
    [sp] = r1
    call L0204e1ca
    call L0204cdea
L0204e3ba:
    sp += 12
    {rets, r6-r4} = [sp++]
    sp += 4
    rts
