/* Reconstructed M5.71 effect enable/fade and installed clear adapters.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/EFFECT_ENABLE_RECONSTRUCTION.md. No device or audio validation. */
#ifndef HYPERRIG_EFFECT_ENABLE_H
#define HYPERRIG_EFFECT_ENABLE_H
#include <stdint.h>

#define HYPERRIG_EFFECT_ENABLE_DURATION UINT32_C(0x020303f4)
#define HYPERRIG_EFFECT_ENABLE_COMMIT_CORE UINT32_C(0x02030466)
#define HYPERRIG_EFFECT_ENABLE_FINISH UINT32_C(0x02030520)
#define HYPERRIG_EFFECT_ENABLE_COMMIT UINT32_C(0x02030530)
#define HYPERRIG_EFFECT_ENABLE_FAST_CORE UINT32_C(0x0203053a)
#define HYPERRIG_EFFECT_ENABLE_FAST UINT32_C(0x020305f8)
#define HYPERRIG_EFFECT_ENABLE_FAST_UNCHECKED UINT32_C(0x02030602)
#define HYPERRIG_EFFECT_ENABLE_COMMIT_UNCHECKED UINT32_C(0x0203060a)
#define HYPERRIG_EFFECT_ENABLE_TAIL_TYPE UINT32_C(0x01c069c6)
#define HYPERRIG_EFFECT_ENABLE_FADE UINT32_C(0x01c069e4)
#define HYPERRIG_EFFECT_ENABLE_IR_RESET UINT32_C(0x01c11f76)
#define HYPERRIG_EFFECT_ENABLE_COUNTER UINT32_C(0x01c05160)
#define HYPERRIG_EFFECT_ENABLE_CLEAR UINT32_C(0x0201a9dc)
#define HYPERRIG_EFFECT_ENABLE_MEMSET UINT32_C(0x02033412)

typedef uint8_t *(*HyperRigEffectEnableMap)(void *, uint32_t, uint32_t, int);
typedef uint32_t (*HyperRigEffectEnableCall)(void *, uint32_t,
                                            const uint32_t[6], uint32_t);
typedef struct {
    HyperRigEffectEnableMap map;
    HyperRigEffectEnableCall call;
    void *opaque;
    uint32_t call_budget;
    uint32_t bulk_store_budget;
} HyperRigEffectEnableIO;

/* All words are original address tokens or raw 32-bit arguments. Core entries
 * take (slot, enabled, check_limit); wrappers take (slot, enabled); fade takes
 * (effect, enabled); duration/type/finish/reset take one word; counter takes none.
 * Clear takes (buffer, bytes), memset takes (buffer, fill, bytes); both return
 * the original buffer token. The installed clear callback executes internally.
 * Unused argument words are ignored. Native scalar results are separate from
 * API status. Void fade/reset/counter return normalized result zero.
 *
 * Status: 0 success; -200 invalid API; -201 missing/invalid mapping; -202 budget
 * exhausted; -203 missing service callback. Partial native writes are retained
 * on failure. Bulk budget counts each word or byte store in clear/memset loops.
 *
 * The mapper must preserve original address relationships and return stable
 * writable byte storage for each requested span. Aliases at the same native
 * address are supported; unrelated firmware windows must not alias on the host.
 * IO, argument and result storage must be disjoint from mapped firmware memory.
 * The map callback only borrows storage and must not mutate mapped bytes.
 * Service callbacks may synchronously mutate mapped bytes, but cannot change mappings,
 * IO, arguments/result storage or reenter this invocation. Every accessed span
 * must be mapped; no span may straddle the 32-bit address wrap. No alignment of
 * mapped host storage is required. Function-pointer clear services must obey
 * the original (buffer, byte_count) ABI; the installed target is 0x0201a9dc.
 *
 * Remaining services: 0203023c(slot), 02028de8(), 0203033c(effect),
 * 0202def2(effect), 0202ec30(), 0202e328(effect), 0202e3ce(effect).
 * They are explicit platform/effect boundaries, not reconstructed numerical
 * execution. A clear callback receives exactly two words; other unused service
 * argument words are zero. A NULL call pointer is valid if no service is reached.
 */
int hyperrig_effect_enable_execute(uint32_t entry, const uint32_t arguments[3],
                                  uint32_t *result, const HyperRigEffectEnableIO *io);
int hyperrig_effect_enable_ir_reset(uint32_t object_token,
                                   const HyperRigEffectEnableIO *io);
#endif
