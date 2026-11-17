/* Joined M5.71 IR lifecycle and numerical construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md. */
#ifndef HYPERRIG_IR_EFFECT_NUMERICAL_H
#define HYPERRIG_IR_EFFECT_NUMERICAL_H
#include "hyperrig_ir_effect_lifecycle.h"
typedef hyperrig_ir_effect_lifecycle_io hyperrig_ir_effect_numerical_io;

/* Accepts the nine lifecycle entries plus native prepare 0202962a (effect,
 * mode) and construct 020318a8 (object, count, producer, producer argument).
 * All arguments are original uint32 words; original defined scalar results
 * are returned through result[0], with result[1]=0. Prepare receives an actual
 * address, not a slot index. Native source counts and pointer arithmetic are
 * preserved; there is no 4076-source or 4096-raw-count API limit.
 *
 * The byte-map and lifetime contract is inherited unchanged. It describes
 * one consistent native address space, with no hidden aliases between
 * distinct addresses. Public source/object/control overlaps and unaligned
 * host backing are supported. Original code and static input data, including
 * the resampling table 0203be2c..0203be50, must remain read-only; they are not
 * writable public object storage. Reads may overlap those immutable bytes.
 * Native private stack remains unavailable to public data.
 * Constructor-owned FFT spans are disjoint by construction and
 * are staged around the unchanged recovered numerical routines; no callback
 * runs during that staging. Full successful states are compared. Arbitrary
 * mapping/work failure prefixes inside staged numerical calls are C-only
 * guards and are not claimed identical to native partial writes.
 *
 * WINDOW 02031542 and COPY 020315b8 execute internally only at constructor
 * producer site 02031a00. Other producer targets remain four-word callbacks.
 * Other indirect callbacks remain external even on token collision. Allocation
 * may return any mapped native token or zero. Services remain synchronous.
 * Work charges mapped accesses, existing gain iterations and each resampling
 * output iteration; no firmware timing meaning is attached to those units.
 * Status and non-resumability are inherited from lifecycle. No hardware,
 * allocator implementation, runtime convolution or audio test is claimed. */
int hyperrig_ir_effect_numerical_execute(uint32_t entry,const uint32_t arguments[12],
    uint32_t result[2],const hyperrig_ir_effect_numerical_io *io);
#endif
