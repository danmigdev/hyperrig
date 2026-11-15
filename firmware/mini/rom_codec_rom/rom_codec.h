/* HYC3: explicit clock snapshot, then one bounded codec read with board setup.
 * This is a separate payload; HYC1 and HYC2 remain frozen. */
#ifndef HYPERRIG_ROM_CODEC_ROM_H
#define HYPERRIG_ROM_CODEC_ROM_H
#include <stdint.h>
#include "../platform/hyperrig_mini_platform.h"

typedef int (*hyperrig_rom_codec_rom_send)(const void *, uint32_t);
typedef int (*hyperrig_rom_codec_rom_handler)(const uint8_t *, uint8_t *);
typedef struct {
    hyperrig_rom_codec_rom_send send;
    int (*receive)(void *, uint32_t);
    hyperrig_rom_codec_rom_handler *handler_slot;
} hyperrig_rom_codec_rom_services;
typedef struct {
    uint32_t (*read)(uint32_t address);
    void (*write)(uint32_t address, uint32_t value);
    void (*spin)(uint32_t iterations);
} hyperrig_rom_codec_rom_hardware;

enum {
    HYC3_READY = 0, HYC3_TEST_SOURCE = 1, HYC3_MAIN_SOURCE = 2,
    HYC3_PLL_SOURCE = 3, HYC3_ROM_PROFILE = 4, HYC3_FREQUENCY = 5,
    HYC3_CLOCK_CHANGED = 6, HYC3_NOT_ARMED = 7,
    HYC3_RECORD_BYTES = 512
};

/* FC6B: no args; 16-byte reply FC6B,HYC3,version3,gate,baseBE32,seqBE16,512BE16.
 * It captures clocks only and arms exactly one FC6C if the gate permits.
 * FC6C: register BE16 at CBW[17:19], snapshot sequence BE16 at [19:21].
 * Reply: FC6C,HYC3,newseqBE16,statusBE32,regBE16,gate,phase1.
 * FD6D: record512, no args. All unused CDB bytes are FF; IN direction only.
 * A new snapshot is required after every FC6C, including failures.
 * No command performs a codec register DATA write, reset, PLL or NOR access.
 *
 * Record LE32 except ASCII: 0 HYC3,4 version3,8 base,12 tag,16 seq,
 * 20 phase(0=snapshot,1=read),24 reg(FFFF=snapshot),28 status,
 * 32 gate,36 nominal_active_hz,40 main_selector,44 pll_source,
 * 48 iterations/unit,52 SFCbit0,56 delay_calls,60 setup(PC5=1,PA9=2,bus=4),
 * 64 read_status(-4=not attempted),68 value(FFFF on error),72 ACKs,
 * 76 received,80 samples,84 STOP,88 cleanup_status,
 * 92 restoration bits(A=1,C=2;0=not attempted),96 clocks_equal,
 * 100 observed_stack,104 guards_ok,108 total_spin_iterations,
 * 112..179 first clock snapshot (17 words in platform header order),
 * 180..247 last clock snapshot,
 * 248..283 PORTA before,284..319 after,320..355 PORTC before,356..391 after
 *   (each OUT,IN,DIR,DIE,PU,PD,HD0,HD,DIEH),
 * 392 settle_iterations,396 snapshot_sequence_consumed,
 * 400..503 reserved zero,504 CRC32[0:504],508 DONE.
 * status: -3 unsupported clock; -8 changed clock; -6 restore; -7 guards;
 * read16 errors otherwise. Nominal Hz/iterations are not measured time.
 * Gate4 means that the exact twelve-word observed ROM profile does not match.
 */
extern uint8_t hyperrig_rom_codec_rom_record[HYC3_RECORD_BYTES];
unsigned hyperrig_rom_codec_rom_clock_gate(const hyperrig_mini_clock_snapshot *,
                                      uint32_t *active_hz, uint32_t *scale);
int hyperrig_rom_codec_rom_initialize(const hyperrig_rom_codec_rom_services *, uint32_t,
                                 const hyperrig_rom_codec_rom_hardware *);
int hyperrig_rom_codec_rom_dispatch(const uint8_t *, uint8_t *);
#endif
