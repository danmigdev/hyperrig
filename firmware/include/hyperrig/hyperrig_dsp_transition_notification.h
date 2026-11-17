/* Reconstructed M5.71 transition notification and borrowed request adapter.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and
 * docs/DSP_TRANSITION_NOTIFICATION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_DSP_TRANSITION_NOTIFICATION_H
#define HYPERRIG_DSP_TRANSITION_NOTIFICATION_H
#include <stdint.h>

typedef uint8_t *(*hyperrig_dsp_transition_notification_map)(void *opaque,
    uint32_t address,uint32_t bytes,int writable);
typedef uint32_t (*hyperrig_dsp_transition_notification_call)(void *opaque,
    uint32_t target,const uint32_t arguments[5],uint32_t count);
typedef struct {
    hyperrig_dsp_transition_notification_map map;
    hyperrig_dsp_transition_notification_call call;
    void *opaque;
} hyperrig_dsp_transition_notification_io;

/* All APIs require IO and result storage, when present, to be disjoint from
 * mapped firmware memory. Mapping preserves original address relationships:
 * overlapping original byte ranges share storage, while distinct firmware
 * windows must not acquire arbitrary host aliases. Parameter tokens may name
 * a subrange of any mapped firmware object. */

/* Complete 0x0201a9ea: signed division by five, clamp, second gain update and
 * real table mixer. All raw uint32 argument/state words are admitted. Native
 * effect is void; return 0 completed, -200 invalid API, -201 missing mapping.
 * The same borrowed 280-byte state prefix is visible to every operation. */
int hyperrig_dsp_transition_notification_notify(uint32_t value,
    const hyperrig_dsp_transition_notification_io *io);
int hyperrig_dsp_transition_notification_mix(uint32_t flag,
    const hyperrig_dsp_transition_notification_io *io);
int hyperrig_dsp_transition_notification_set_gain(uint32_t value,uint32_t flag,
    const hyperrig_dsp_transition_notification_io *io);

/* Borrowed execution of complete 0x02028a34. Map config01c1f7d4/68,
 * control01c32db0/640, callbacks01c34190/768, filters01c33030/176,
 * staged01c330e0/176 and parameter_token/12. The installed notification also
 * maps state01c26890/280. No shared runtime is copied across a callback.
 * result receives native 0/1 only on success. -202 is an inherited-domain or
 * callback guard; guards can follow native partial writes. Disabled-bank
 * stored parameters0..4 retain the previous +/-1280 bound. Input signed16
 * values and duration have their original full domains. Parameter reads occur
 * after reset and before notification; mapped source aliases are supported.
 * Alternate nonzero callback tokens require call, invoked with one signed32
 * bit-pattern argument. Its result is ignored. That service may synchronously
 * mutate mapped state/source bytes, but not IO, result, allocation lifetimes
 * or filter storage types. Mapping must be pure, stable and consistent;
 * filters require aligned hyperrig_biquad_section-compatible storage. No
 * re-entry, concurrency or retained callback pointers. */
int hyperrig_dsp_transition_notification_request(uint32_t parameter_token,
    uint32_t duration,uint32_t *result,const hyperrig_dsp_transition_notification_io *io);
#endif
