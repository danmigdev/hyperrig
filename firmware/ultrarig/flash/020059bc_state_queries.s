; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; state_queries: 3 functions, 0x020059bc..0x020059fc

; state_queries_ready_word: 0x020059bc..0x020059de, module state-queries (ready_word)
.type state_queries_ready_word,@function
state_queries_ready_word:
    r2 = L01c26890
    r3 = b[r2+65] (u)
    r1 = r0
    if (r3 == 0) goto L020059da
    r0 = 1
    if (r1 == 0) goto L020059d8
    r3 = 337
    r2 = [r2+r3<<2]
    [r1+0] = r2
L020059d8:
    rts
L020059da:
    r0 = 0
    rts

; state_queries_state_byte: 0x020059de..0x020059ee, module state-queries (state_byte)
.type state_queries_state_byte,@function
state_queries_state_byte:
    r0 = L01c26890
    r1 = b[r0+60] (u)
    r0 = b[r0+60] (u)
    rts

; state_queries_tenfold_word: 0x020059ee..0x020059fc, module state-queries (tenfold_word)
.type state_queries_tenfold_word,@function
state_queries_tenfold_word:
    r0 = L01c1f180
    r0 = [r0+24]
    r0 = r0 * 0xA
    rts
