/* Reconstructed M5.71 effect setup, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_EFFECT_SETUP_H
#define HYPERRIG_EFFECT_SETUP_H
#include "hyperrig_effect_parameter_construction.h"

typedef hyperrig_effect_parameter_construction_io hyperrig_effect_setup_io;

/* Complete setup entries use original uint32 ABI words, including both stack
 * words for six-argument neighbor_group. Scalar outputs publish only on API
 * success; native negative creation/allocation results are valid scalar words.
 * Void initializer/refresh/route entries return zero. result[1] is zero.
 *
 * One canonical, pure byte map preserves native aliases. API/IO/result storage
 * is disjoint from mapped firmware bytes; original code/static bytes remain
 * immutable. Callbacks are synchronous and may mutate public mapped fields,
 * but cannot reenter, relocate backing, retain views or alter API objects.
 * Original private stack 30000000..30001020 and inherited transient output
 * 31005000..31005020 are reserved; private allocator arrays are never exposed.
 * Existing reached numerical, alignment and ownership contracts still apply.
 * Raw segment and partition arguments retain native signed tests, wrapped
 * addressing and modulo-32 register-bit indices. During allocation,
 * callback mutations may change the public type, but a later pool attachment
 * must not consume an original private pointer that was never initialized.
 * That reached condition returns -202 after preserving preceding writes.
 * Type30 clears its complete object before reading any parameter values.
 * Failed calls preserve preceding writes/callbacks; stopped calls cannot resume.
 * Budgets charge portable mapped work and actual external services, including
 * nested borrowed calls. They are not original timing measurements.
 *
 * Only explicit direct creation/tempo and five parameter cost/refresh sites
 * join recovered bodies. Equal indirect callback tokens remain external with
 * their call-site arity. Outer preset application is not joined here.
 * Status -200/-201/-202/-203 denotes invalid API, mapping, reached domain or
 * work/service exhaustion; inherited zero-cap behavior is retained.
 * Offline synchronous reconstruction, not a device or audio test. */
int hyperrig_effect_setup_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_effect_setup_io *io);
int hyperrig_effect_setup_parameters_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_effect_setup_io *io);
#endif
