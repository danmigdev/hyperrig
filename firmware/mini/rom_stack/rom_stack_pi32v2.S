/* Ordinary C ABI, not a ROM entry point or exception return sequence.
 * r4 holds the incoming save frame across a normal ABI callback. The vendor
 * compiler uses the same saved-frame scheme for dynamic alloca/VLA frames.
 * SP may alias an architectural stack register in the inherited mode: these
 * instructions restore the active SP, without an explicit SSP/USP/ICFG write.
 */
.section .text.hyperrig_mini_rom_run_on_stack,"ax",@progbits
.global hyperrig_mini_rom_run_on_stack
.type hyperrig_mini_rom_run_on_stack,@function
hyperrig_mini_rom_run_on_stack:
    [--sp] = {rets, r4}
    r4 = sp
    r3 = r0
    sp = r2
    r0 = r1
    call r3
    sp = r4
    {rets, r4} = [sp++]
    rts
.size hyperrig_mini_rom_run_on_stack, .-hyperrig_mini_rom_run_on_stack
