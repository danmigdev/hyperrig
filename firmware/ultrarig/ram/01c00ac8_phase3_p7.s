; Required Notice: Copyright (c) 2026 Manuel Aguirre (https://polyformproject.org/licenses/noncommercial/1.0.0)
; See third_party/ultrarig/LICENSE.md and NOTICE.md. Bodies of JieLi AC79 SDK origin are under the Apache
; License 2.0 (third_party/ac79-sdk/LICENSE); docs/PROVENANCE.md gives the origin of each function.

; phase3_p7: 3 functions, 0x01c00ac8..0x01c00ae2

; phase3_p7_norflash_spi_cs: 0x01c00ac8..0x01c00ad2, module phase3-p7 (norflash_spi_cs)
.type phase3_p7_norflash_spi_cs,@function
phase3_p7_norflash_spi_cs:
    [--sp] = rets
    r0 = r0.b0 (u)
    call storage_control_chip_select
    pc = [sp++]

; phase3_p7_norflash_spi_read_byte: 0x01c00ad2..0x01c00ada, module phase3-p7 (norflash_spi_read_byte)
.type phase3_p7_norflash_spi_read_byte,@function
phase3_p7_norflash_spi_read_byte:
    [--sp] = rets
    call storage_control_receive_byte
    pc = [sp++]

; phase3_p7_norflash_spi_write_byte: 0x01c00ada..0x01c00ae2, module phase3-p7 (norflash_spi_write_byte)
.type phase3_p7_norflash_spi_write_byte,@function
phase3_p7_norflash_spi_write_byte:
    [--sp] = rets
    call storage_control_send_byte
    pc = [sp++]
