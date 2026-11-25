; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p2: 1 function, 0x02023f16..0x02024a78

; phase3_p2_wf_phy_init: 0x02023f16..0x02024a78, module phase3-p2 (wf_phy_init)
.type phase3_p2_wf_phy_init,@function
phase3_p2_wf_phy_init:
    [--sp] = rets
    call L02055a2a  ; @call.xl
    call L02023ada
    r1 = 37895
    r0 = 776
    call L020559cc  ; @call.xl
    call L02023e32  ; @call.l
    r0 = 0
    r1 = 138
    call L02055a66  ; @call.xl
    r0 = 1
    r1 = 32
    call L02055a66  ; @call.xl
    r0 = 2
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 3
    r1 = 8
    call L02055a66  ; @call.xl
    r0 = 4
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 5
    r1 = 16
    call L02055a66  ; @call.xl
    r0 = 6
    r1 = 176
    call L02055a66  ; @call.xl
    r0 = 7
    r1 = 160
    call L02055a66  ; @call.xl
    r0 = 8
    r1 = 112
    call L02055a66  ; @call.xl
    r0 = 9
    r1 = 50
    call L02055a66  ; @call.xl
    r0 = 10
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 11
    r1 = 224
    call L02055a66  ; @call.xl
    r0 = 12
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 13
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 14
    r1 = 181
    call L02055a66  ; @call.xl
    r0 = 15
    r1 = 145
    call L02055a66  ; @call.xl
    r0 = 16
    r1 = 68
    call L02055a66  ; @call.xl
    r0 = 17
    r1 = 67
    call L02055a66  ; @call.xl
    r0 = 18
    r1 = 68
    call L02055a66  ; @call.xl
    r0 = 19
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 20
    r1 = 127
    call L02055a66  ; @call.xl
    r0 = 21
    r1 = 15
    call L02055a66  ; @call.xl
    r0 = 22
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 23
    r1 = 5
    call L02055a66  ; @call.xl
    r0 = 24
    r1 = 119
    call L02055a66  ; @call.xl
    r0 = 25
    r1 = 128
    call L02055a66  ; @call.xl
    r0 = 26
    r1 = 18
    call L02055a66  ; @call.xl
    r0 = 27
    r1 = 190
    call L02055a66  ; @call.xl
    r0 = 28
    r1 = 53
    call L02055a66  ; @call.xl
    r0 = 29
    r1 = 239
    call L02055a66  ; @call.xl
    r0 = 30
    r1 = 15
    call L02055a66  ; @call.xl
    r0 = 31
    r1 = 15
    call L02055a66  ; @call.xl
    r0 = 32
    r1 = 79
    call L02055a66  ; @call.xl
    r0 = 33
    r1 = 5
    call L02055a66  ; @call.xl
    r0 = 34
    r1 = 5
    call L02055a66  ; @call.xl
    r0 = 35
    r1 = 147
    call L02055a66  ; @call.xl
    r0 = 36
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 37
    r1 = 13
    call L02055a66  ; @call.xl
    r0 = 38
    r1 = 3
    call L02055a66  ; @call.xl
    r0 = 39
    r1 = 132
    call L02055a66  ; @call.xl
    r0 = 40
    r1 = 30
    call L02055a66  ; @call.xl
    r0 = 41
    r1 = 10
    call L02055a66  ; @call.xl
    r0 = 42
    r1 = 148
    call L02055a66  ; @call.xl
    r0 = 48
    r1 = 32
    call L02055a66  ; @call.xl
    r0 = 49
    r1 = 6
    call L02055a66  ; @call.xl
    r0 = 50
    r1 = 63
    call L02055a66  ; @call.xl
    r0 = 51
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 52
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 53
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 54
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 55
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 56
    r1 = 16
    call L02055a66  ; @call.xl
    r0 = 57
    r1 = 16
    call L02055a66  ; @call.xl
    r0 = 58
    r1 = 32
    call L02055a66  ; @call.xl
    r0 = 59
    r1 = 192
    call L02055a66  ; @call.xl
    r0 = 60
    r1 = 240
    call L02055a66  ; @call.xl
    r0 = 61
    r1 = 208
    call L02055a66  ; @call.xl
    r0 = 62
    r1 = 128
    call L02055a66  ; @call.xl
    r0 = 63
    r1 = 208
    call L02055a66  ; @call.xl
    r0 = 64
    r1 = 231
    call L02055a66  ; @call.xl
    r0 = 65
    r1 = 135
    call L02055a66  ; @call.xl
    r0 = 66
    r1 = 24
    call L02055a66  ; @call.xl
    r0 = 67
    r1 = 232
    call L02055a66  ; @call.xl
    r0 = 68
    r1 = 48
    call L02055a66  ; @call.xl
    r0 = 69
    r1 = 48
    call L02055a66  ; @call.xl
    r0 = 70
    r1 = 7
    call L02055a66  ; @call.xl
    r0 = 71
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 72
    r1 = 190
    call L02055a66  ; @call.xl
    r0 = 73
    r1 = 150
    call L02055a66  ; @call.xl
    r0 = 75
    r1 = 112
    call L02055a66  ; @call.xl
    r0 = 76
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 79
    r1 = 140
    call L02055a66  ; @call.xl
    r0 = 80
    r1 = 128
    call L02055a66  ; @call.xl
    r0 = 81
    r1 = 144
    call L02055a66  ; @call.xl
    r0 = 82
    r1 = 255
    call L02055a66  ; @call.xl
    r0 = 83
    r1 = 3
    call L02055a66  ; @call.xl
    r0 = 84
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 85
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 86
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 87
    r1 = 39
    call L02055a66  ; @call.xl
    r0 = 88
    r1 = 3
    call L02055a66  ; @call.xl
    r0 = 89
    r1 = 40
    call L02055a66  ; @call.xl
    r0 = 90
    r1 = 216
    call L02055a66  ; @call.xl
    r0 = 91
    r1 = 12
    call L02055a66  ; @call.xl
    r0 = 92
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 93
    r1 = 5
    call L02055a66  ; @call.xl
    r0 = 94
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 95
    r1 = 128
    call L02055a66  ; @call.xl
    r0 = 96
    r1 = 128
    call L02055a66  ; @call.xl
    r0 = 97
    r1 = 221
    call L02055a66  ; @call.xl
    r0 = 98
    r1 = 32
    call L02055a66  ; @call.xl
    r0 = 99
    r1 = 254
    call L02055a66  ; @call.xl
    r0 = 100
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 101
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 102
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 103
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 104
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 105
    r1 = 100
    call L02055a66  ; @call.xl
    r0 = 106
    r1 = 132
    call L02055a66  ; @call.xl
    r0 = 107
    r1 = 223
    call L02055a66  ; @call.xl
    r0 = 108
    r1 = 71
    call L02055a66  ; @call.xl
    r0 = 109
    r1 = 64
    call L02055a66  ; @call.xl
    r0 = 110
    r1 = 44
    call L02055a66  ; @call.xl
    r0 = 111
    r1 = 112
    call L02055a66  ; @call.xl
    r0 = 112
    r1 = 80
    call L02055a66  ; @call.xl
    r0 = 113
    r1 = 224
    call L02055a66  ; @call.xl
    r0 = 114
    r1 = 1
    call L02055a66  ; @call.xl
    r0 = 115
    r1 = 156
    call L02055a66  ; @call.xl
    r0 = 117
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 118
    r1 = 3
    call L02055a66  ; @call.xl
    r0 = 119
    r1 = 73
    call L02055a66  ; @call.xl
    r0 = 120
    r1 = 0
    call L02055a66  ; @call.xl
    r0 = 121
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 122
    r1 = 208
    call L02055a66  ; @call.xl
    r0 = 0
    r1 = 58
    call L02055a7e  ; @call.xl
    r0 = 4
    r1 = 106
    call L02055a7e  ; @call.xl
    r0 = 5
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 6
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 7
    r1 = 181
    call L02055a7e  ; @call.xl
    r0 = 3
    r1 = 21
    call L02055a7e  ; @call.xl
    r0 = 8
    r1 = 193
    call L02055a7e  ; @call.xl
    r0 = 13
    r1 = 43
    call L02055a7e  ; @call.xl
    r0 = 14
    r1 = 160
    call L02055a7e  ; @call.xl
    r0 = 15
    r1 = 196
    call L02055a7e  ; @call.xl
    r0 = 16
    r1 = 4
    call L02055a7e  ; @call.xl
    r0 = 17
    r1 = 160
    call L02055a7e  ; @call.xl
    r0 = 18
    r1 = 43
    call L02055a7e  ; @call.xl
    r0 = 19
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 20
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 21
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 22
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 23
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 24
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 25
    r1 = 57
    call L02055a7e  ; @call.xl
    r0 = 26
    r1 = 106
    call L02055a7e  ; @call.xl
    r0 = 27
    r1 = 56
    call L02055a7e  ; @call.xl
    r0 = 28
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 24
    r1 = 0
    call L02055a7e  ; @call.xl
    r0 = 0
    r1 = 98
    call L02023ef2
    r0 = 1
    r1 = 88
    call L02023ef2
    r0 = 2
    r1 = 69
    call L02023ef2
    r0 = 3
    r1 = 229
    call L02023ef2
    r0 = 4
    r1 = 0
    call L02023ef2
    r0 = 5
    r1 = 10
    call L02023ef2
    r0 = 6
    r1 = 18
    call L02023ef2
    r0 = 7
    r1 = 4
    call L02023ef2
    r0 = 8
    r1 = 0
    call L02023ef2
    r0 = 9
    r1 = 112
    call L02023ef2
    r0 = 10
    r1 = 52
    call L02023ef2
    r0 = 11
    r1 = 0
    call L02023ef2
    r0 = 12
    r1 = 0
    call L02023ef2
    r0 = 13
    r1 = 154
    call L02023ef2
    r0 = 14
    r1 = 166
    call L02023ef2
    r0 = 15
    r1 = 51
    call L02023ef2
    r0 = 16
    r1 = 154
    call L02023ef2
    r0 = 17
    r1 = 166
    call L02023ef2
    r0 = 18
    r1 = 51
    call L02023ef2
    r0 = 19
    r1 = 154
    call L02023ef2
    r0 = 20
    r1 = 166
    call L02023ef2
    r0 = 21
    r1 = 51
    call L02023ef2
    r0 = 22
    r1 = 154
    call L02023ef2
    r0 = 23
    r1 = 166
    call L02023ef2
    r0 = 24
    r1 = 51
    call L02023ef2
    r0 = 25
    r1 = 154
    call L02023ef2
    r0 = 26
    r1 = 166
    call L02023ef2
    r0 = 27
    r1 = 51
    call L02023ef2
    r0 = 28
    r1 = 8
    call L02023ef2
    r0 = 29
    r1 = 15
    call L02023ef2
    r0 = 30
    r1 = 16
    call L02023ef2
    r0 = 31
    r1 = 16
    call L02023ef2
    r0 = 32
    r1 = 16
    call L02023ef2
    r0 = 33
    r1 = 36
    call L02023ef2
    r0 = 34
    r1 = 37
    call L02023ef2
    r0 = 35
    r1 = 36
    call L02023ef2
    r0 = 36
    r1 = 37
    call L02023ef2
    r0 = 37
    r1 = 37
    call L02023ef2
    r0 = 38
    r1 = 37
    call L02023ef2
    r0 = 39
    r1 = 37
    call L02023ef2
    r0 = 40
    r1 = 37
    call L02023ef2
    r0 = 41
    r1 = 37
    call L02023ef2
    r0 = 42
    r1 = 37
    call L02023ef2
    r0 = 43
    r1 = 37
    call L02023ef2
    r0 = 44
    r1 = 37
    call L02023ef2
    r0 = 45
    r1 = 29
    call L02023ef2
    r0 = 46
    r1 = 37
    call L02023ef2
    r0 = 47
    r1 = 28
    call L02023ef2
    r0 = 48
    r1 = 37
    call L02023ef2
    r0 = 49
    r1 = 10
    call L02023ef2
    r0 = 50
    r1 = 10
    call L02023ef2
    r0 = 51
    r1 = 10
    call L02023ef2
    r0 = 52
    r1 = 10
    call L02023ef2
    r0 = 53
    r1 = 10
    call L02023ef2
    r0 = 54
    r1 = 10
    call L02023ef2
    r0 = 55
    r1 = 10
    call L02023ef2
    r0 = 56
    r1 = 7
    call L02023ef2
    r0 = 57
    r1 = 46
    call L02023ef2
    r0 = 58
    r1 = 8
    call L02023ef2
    r0 = 59
    r1 = 32
    call L02023ef2
    r0 = 60
    r1 = 255
    call L02023ef2
    r0 = 61
    r1 = 8
    call L02023ef2
    r0 = 62
    r1 = 0
    call L02023ef2
    r0 = 63
    r1 = 4
    call L02023ef2
    r0 = 64
    r1 = 0
    call L02023ef2
    r0 = 65
    r1 = 96
    call L02023ef2
    r0 = 66
    r1 = 15
    call L02023ef2
    r0 = 67
    r1 = 0
    call L02023ef2
    r0 = 68
    r1 = 4
    call L02023ef2
    r0 = 69
    r1 = 0
    call L02023ef2
    r0 = 70
    r1 = 0
    call L02023ef2
    r0 = 71
    r1 = 0
    call L02023ef2
    r0 = 0
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 11
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 13
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 15
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 17
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 19
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 21
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 23
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 25
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 27
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 29
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 31
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 33
    r1 = 32
    call L02055a4e  ; @call.xl
    r0 = 12
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 14
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 16
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 18
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 20
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 22
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 24
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 26
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 28
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 30
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 32
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 34
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 35
    r1 = 3
    call L02055a4e  ; @call.xl
    r0 = 36
    r1 = 50
    call L02055a4e  ; @call.xl
    r0 = 37
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 38
    r1 = 63
    call L02055a4e  ; @call.xl
    r0 = 39
    r1 = 229
    call L02055a4e  ; @call.xl
    r0 = 40
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 41
    r1 = 204
    call L02055a4e  ; @call.xl
    r0 = 42
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 43
    r1 = 138
    call L02055a4e  ; @call.xl
    r0 = 44
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 45
    r1 = 202
    call L02055a4e  ; @call.xl
    r0 = 46
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 47
    r1 = 136
    call L02055a4e  ; @call.xl
    r0 = 48
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 49
    r1 = 6
    call L02055a4e  ; @call.xl
    r0 = 50
    r1 = 4
    call L02055a4e  ; @call.xl
    r0 = 51
    r1 = 25
    call L02055a4e  ; @call.xl
    r0 = 52
    r1 = 182
    call L02055a4e  ; @call.xl
    r0 = 53
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 54
    r1 = 153
    call L02055a4e  ; @call.xl
    r0 = 55
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 56
    r1 = 66
    call L02055a4e  ; @call.xl
    r0 = 57
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 58
    r1 = 230
    call L02055a4e  ; @call.xl
    r0 = 59
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 60
    r1 = 175
    call L02055a4e  ; @call.xl
    r0 = 61
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 62
    r1 = 4
    call L02055a4e  ; @call.xl
    r0 = 63
    r1 = 4
    call L02055a4e  ; @call.xl
    r0 = 64
    r1 = 68
    call L02055a4e  ; @call.xl
    r0 = 65
    r1 = 91
    call L02055a4e  ; @call.xl
    r0 = 66
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 67
    r1 = 204
    call L02055a4e  ; @call.xl
    r0 = 68
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 69
    r1 = 138
    call L02055a4e  ; @call.xl
    r0 = 70
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 71
    r1 = 153
    call L02055a4e  ; @call.xl
    r0 = 72
    r1 = 1
    call L02055a4e  ; @call.xl
    r0 = 73
    r1 = 67
    call L02055a4e  ; @call.xl
    r0 = 74
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 75
    r1 = 6
    call L02055a4e  ; @call.xl
    r0 = 76
    r1 = 5
    call L02055a4e  ; @call.xl
    r0 = 80
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 81
    r1 = 79
    call L02055a4e  ; @call.xl
    r0 = 82
    r1 = 164
    call L02055a4e  ; @call.xl
    r0 = 83
    r1 = 144
    call L02055a4e  ; @call.xl
    r0 = 84
    r1 = 237
    call L02055a4e  ; @call.xl
    r0 = 85
    r1 = 218
    call L02055a4e  ; @call.xl
    r0 = 86
    r1 = 84
    call L02055a4e  ; @call.xl
    r0 = 87
    r1 = 107
    call L02055a4e  ; @call.xl
    r0 = 88
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 89
    r1 = 16
    call L02055a4e  ; @call.xl
    r0 = 90
    r1 = 214
    call L02055a4e  ; @call.xl
    r0 = 91
    r1 = 144
    call L02055a4e  ; @call.xl
    r0 = 92
    r1 = 192
    call L02055a4e  ; @call.xl
    r0 = 93
    r1 = 0
    call L02055a4e  ; @call.xl
    r0 = 95
    r1 = 64
    call L02055a4e  ; @call.xl
    r0 = 0
    r1 = 2
    call L02055a4e  ; @call.xl
    r0 = 42
    r1 = 148
    call L02055a66  ; @call.xl
    r0 = 87
    r1 = 39
    call L02055a66  ; @call.xl
    r0 = 25
    r1 = 57
    call L02055a7e  ; @call.xl
    r0 = 55
    r1 = 4
    call L02055a66  ; @call.xl
    r0 = 15
    r1 = 196
    call L02055a7e  ; @call.xl
    r0 = 27
    r1 = 56
    call L02055a7e  ; @call.xl
    r0 = 60
    r1 = 1
    call L02023ef2
    r0 = 106
    r1 = 4
    call L02055a0c  ; @call.xl
    r0 = 84
    r1 = 2
    call L02055a0c  ; @call.xl
    call L02055a2a  ; @call.xl
    pc = [sp++]
