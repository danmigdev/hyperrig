/* HYRX: observe the ROM receive callback; exclusively private RAM and ROM I/O.
 * Sequence/nonce are accident guards, not authentication. No completion or
 * return-value convention is inferred by this diagnostic. */
#ifndef HYPERRIG_ROM_RECEIVE_H
#define HYPERRIG_ROM_RECEIVE_H
#include <stdint.h>

typedef int (*hyperrig_receive_handler)(const uint8_t *, uint8_t *);
typedef struct {
    int (*send)(const void *, uint32_t);
    int (*receive)(void *, uint32_t);
    hyperrig_receive_handler *handler_slot;
} hyperrig_receive_services;

enum { HYRX_MAX_BYTES = 260, HYRX_RECORD_BYTES = 512 };
enum { HYRX_IDLE = 0, HYRX_ARMED = 1, HYRX_RECEIVING = 2,
       HYRX_RETURNED = 3, HYRX_FAULT = 4 };
enum { HYRX_OK = 0, HYRX_FRAME = 1, HYRX_STATE = 2,
       HYRX_GUARD = 3, HYRX_SEND = 4, HYRX_LATE_CHANGE = 5 };

/* Record is 512 LE bytes, ending CRC32[0:504]@504 and DONE@508:
 * 0 HYRX,4 version,8 base,12 build tag,16 sequence,20 nonce,24 length,
 * 28 state,32 sticky error,36 poison seed,40 expected CRC,44 immediate CRC,
 * 48 current CRC,52 raw signed callback result,56 entered,60 returned,
 * 64 immediate guard mask,68 current guard mask,72 tail poison intact,
 * 76 immediate changed-byte count,80 current changed-byte count,
 * 84 immediate/current data equal,88 receive callback count,92 sample count,
 * 96 send pointer,100 receive pointer,104 handler-slot pointer;108..127 zero;
 * 128 data[260],388 prefix[16],404 suffix[16],420..503 zero.
 * Pointer fields are target u32; host64 tests expose low32 only, not ROM data.
 * "Changed" means different from initial poison, not bytes received.
 * FD85 resamples data; stable samples do not prove synchronous completion.
 */
extern uint8_t hyperrig_receive_record[HYRX_RECORD_BYTES];
int hyperrig_receive_initialize(const hyperrig_receive_services *, uint32_t base);
int hyperrig_receive_dispatch(const uint8_t *, uint8_t *);
#endif
