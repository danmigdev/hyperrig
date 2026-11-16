/* Reconstructed UltraRig IR convolution construction, not original source.
 * Required Notice: Copyright (c) 2026 Manuel Aguirre
 * https://polyformproject.org/licenses/noncommercial/1.0.0
 * See third_party/ultrarig/LICENSE.md and docs/IR_CONVOLUTION_RECONSTRUCTION.md. */
#ifndef HYPERRIG_IR_CONVOLUTION_H
#define HYPERRIG_IR_CONVOLUTION_H
#include "hyperrig_ir_installation.h"

enum {
    HYPERRIG_IR_CONVOLUTION_WINDOW = 0x02031542,
    HYPERRIG_IR_CONVOLUTION_COPY = 0x020315b8,
    HYPERRIG_IR_CONVOLUTION_BYTES = 73296
};
typedef struct {
    hyperrig_ir_installation installation;
    uint8_t allocation_callbacks[8]; /* Global 0x01c32db0 +52,+56. */
    uint8_t flags[4]; /* 0x01c1fa14. */
    /* Per-effect original +76..+92, then +288..+296. Other bytes remain in
     * earlier runtime views or outside this construction module. */
    uint8_t effects[16][24];
    uint8_t status[64]; /* Original 0x01c343d8, sixteen words. */
} hyperrig_ir_convolution;

typedef uint32_t (*hyperrig_ir_convolution_service)(void *opaque, uint32_t target, uint32_t argument);
typedef struct {
    hyperrig_ir_convolution_service call;
    void *opaque;
    const uint8_t *samples;
    uint32_t sample_capacity, sample_token;
    uint8_t *object;
    uint32_t object_capacity, object_token;
    const uint8_t *copy;
    uint32_t copy_capacity;
} hyperrig_ir_convolution_io;

/* Original size arithmetic accepts every uint32 word, including wraparound. */
uint32_t hyperrig_ir_convolution_size(uint32_t count);
/* All floating values are binary32 words. These recover the original phase
 * polynomials and saturating Q31 conversion, without host floating arithmetic. */
uint32_t hyperrig_ir_convolution_cosine(uint32_t value);
uint32_t hyperrig_ir_convolution_sine(uint32_t value);
uint32_t hyperrig_ir_convolution_q31(uint32_t value);
int hyperrig_ir_convolution_phase(uint32_t index, uint32_t denominator, uint32_t output[2]);
/* Buffer sizes are bytes. FFT128 receives 128 permutation bytes, 64 complex
 * binary32 twiddles and 128 writable complex values. Real256 receives 129
 * twiddles, 256 real inputs, 129 complex outputs and 128 complex scratch words.
 * All spans are disjoint. Data words are little-endian. */
int hyperrig_ir_convolution_fft128(const uint8_t *permutation, uint32_t permutation_capacity,
    const uint8_t *twiddles, uint32_t twiddle_capacity, uint8_t *values, uint32_t capacity);
int hyperrig_ir_convolution_real256(const uint8_t *permutation, uint32_t permutation_capacity,
    const uint8_t *twiddles, uint32_t twiddle_capacity, const uint8_t *real_twiddles,
    uint32_t real_twiddle_capacity, const uint8_t *input, uint32_t input_capacity,
    uint8_t *output, uint32_t output_capacity, uint8_t *scratch, uint32_t scratch_capacity);
/* All public APIs require distinct, nonoverlapping runtime, IO, parameter,
 * result, source, copy, object and destination storage, except that reset
 * deliberately modifies the object previously returned by construct.
 * A source view has <=4076 signed16 samples, matching installation state.
 * Output start/count must fit 0..4096; window parameters are length, fade, mode.
 * Source, output, runtime and IO objects may not overlap. */
int hyperrig_ir_convolution_sample(const hyperrig_ir_convolution *runtime, uint32_t index,
    uint32_t gain, const hyperrig_ir_convolution_io *io, uint32_t *result);
int hyperrig_ir_convolution_resample(const hyperrig_ir_convolution *runtime, uint8_t *output,
    uint32_t capacity, uint32_t start, uint32_t count, uint32_t mode, const hyperrig_ir_convolution_io *io);
int hyperrig_ir_convolution_produce(const hyperrig_ir_convolution *runtime, const uint32_t parameters[3],
    uint8_t *output, uint32_t capacity, uint32_t start, uint32_t count, const hyperrig_ir_convolution_io *io);
int hyperrig_ir_convolution_copy(const uint8_t *source, uint32_t source_capacity,
    uint8_t *output, uint32_t output_capacity, uint32_t start, uint32_t count);
/* Construct stores the original returned address in result: zero on a null
 * object/count/producer, otherwise io->object_token. count <=4096 and callback
 * is WINDOW or COPY. Size returns the required allocation; storage stays live.
 * The copy producer takes io->copy as its original opaque source argument. */
int hyperrig_ir_convolution_construct(hyperrig_ir_convolution *runtime, uint32_t count,
    uint32_t producer, const uint32_t parameters[3], const hyperrig_ir_convolution_io *io, uint32_t *result);
/* Reset accepts coherent constructor layouts only: 1..32 partitions and the
 * original exact history pointers. Histories may not overlap the header. */
int hyperrig_ir_convolution_reset(uint8_t *object, uint32_t capacity, uint32_t token);
/* Complete original 0x0202962a body. Allocation/free target addresses come
 * from runtime; allocation returns zero or io->object_token. Services may
 * synchronously mutate runtime/source/object while preserving mapped spans.
 * Original statuses: 0 published, -3 allocation unavailable, -1 constructor
 * failure or mode zero. New -200 rejects invalid API before effects; -201
 * rejects a service/mapping violation and preserves effects already performed.
 * This constructs state; it does not execute audio or access hardware. */
int hyperrig_ir_convolution_prepare(hyperrig_ir_convolution *runtime, uint32_t effect,
    uint32_t mode, const hyperrig_ir_convolution_io *io);
#endif
