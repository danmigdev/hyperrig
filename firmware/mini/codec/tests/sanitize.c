#include "hyperrig_mini_codec.h"
#include <assert.h>
#include <stdio.h>

typedef struct { unsigned samples, nack, transitions, delays; } fixture;
static void gpio(void *user, unsigned operation, unsigned pin, unsigned value)
{
    fixture *f = (fixture *)user;
    assert(operation <= HYPERRIG_MINI_CODEC_PULL_DOWN);
    assert(pin == 1 || pin == 2);
    assert(value <= 1);
    ++f->transitions;
}
static int sample(void *user, unsigned pin)
{
    fixture *f = (fixture *)user;
    assert(pin == 1);
    return f->samples++ == f->nack;
}
static int delay(void *user, unsigned units)
{
    fixture *f = (fixture *)user;
    uint32_t count = 0;
    assert(units == 3 || units == 6);
    assert(hyperrig_mini_codec_delay_iterations(240000000, 1, units, &count) == 0);
    assert(count == 30 * units);
    ++f->delays;
    return 0;
}
int main(void)
{
    unsigned value, nack, cases = 0;
    for (value = 0; value < 256; ++value) {
        for (nack = 0; nack < 6; ++nack) {
            /* Exact four-byte object, so ASan catches a fifth-byte access. */
            uint8_t record[4] = {0, (uint8_t)value, 0xA5, 0x5A};
            fixture f = {0, nack, 0, 0};
            hyperrig_mini_codec_bus bus = {gpio, sample, delay, &f, 0};
            hyperrig_mini_codec_result result;
            int status;
            assert(hyperrig_mini_codec_bus_init(&bus) == 0);
            status = hyperrig_mini_codec_write(&bus, record, &result);
            assert(status == (nack < 5 ? HYPERRIG_MINI_CODEC_NACK : 0));
            assert(result.acknowledged == (nack < 5 ? nack : 5));
            assert(f.samples == (nack < 5 ? nack + 1 : 5));
            assert(result.stop_attempted && !result.cleanup_status);
            ++cases;
        }
    }
    assert(hyperrig_mini_codec_write(0, 0, 0) == HYPERRIG_MINI_CODEC_EINVAL);
    assert(!hyperrig_mini_codec_stock_record(22));
    printf("{\"exact_record_cases\":%u,\"asan\":true,\"ubsan\":true}\n", cases);
    return 0;
}
