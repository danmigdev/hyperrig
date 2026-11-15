#include "audio_port.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    unsigned sda, scl, input, active, bit, accum, ack_phase, rise;
    unsigned starts, stops, bytes, samples, delays, nacks_at, delay_fail_at;
    unsigned pa9, pa9_calls, spins, g_starts, bus_gpio_calls;
    int start_result;
    unsigned wire[112];
    char order[16];
    unsigned order_count;
} Test;

static void event(Test *t, char kind)
{
    assert(t->order_count < sizeof(t->order));
    t->order[t->order_count++] = kind;
}

static void gpio(void *user, unsigned op, unsigned pin, unsigned value)
{
    Test *t = user;
    unsigned before = t->input ? 1 : t->sda;
    assert(pin == 1 || pin == 2);
    assert(t->pa9_calls == 1 && t->pa9 == 0 && t->spins == 1);
    if (!t->bus_gpio_calls++) event(t, 'B');
    if (op == HYPERRIG_MINI_CODEC_DIRECTION && pin == 1) t->input = value;
    if (op != HYPERRIG_MINI_CODEC_OUTPUT) return;
    if (pin == 1) {
        t->sda = value;
        t->input = 0;
        if (t->scl && before != value) {
            if (!value) {
                ++t->starts;
                t->active = 1;
                t->bit = t->accum = t->ack_phase = t->rise = 0;
            } else {
                ++t->stops;
                t->active = 0;
            }
        }
    } else {
        if (!t->scl && value && t->active) {
            t->rise = 1;
            if (!t->ack_phase) {
                t->accum = (t->accum << 1) | (t->input ? 1 : t->sda);
            }
        }
        if (t->scl && !value && t->active && t->rise) {
            t->rise = 0;
            if (t->ack_phase) t->ack_phase = 0;
            else if (++t->bit == 8) {
                assert(t->bytes < 112);
                t->wire[t->bytes++] = t->accum;
                t->bit = t->accum = 0;
                t->ack_phase = 1;
            }
        }
        t->scl = value;
    }
}

static int sample(void *user, unsigned pin)
{
    Test *t = user;
    assert(pin == 1 && t->scl && t->input && t->ack_phase);
    return ++t->samples == t->nacks_at;
}

static int delay(void *user, unsigned units)
{
    Test *t = user;
    assert(units == 3 || units == 6);
    return ++t->delays == t->delay_fail_at ? -37 : 0;
}

static void pa9(void *user, unsigned value)
{
    Test *t = user;
    assert(value <= 1);
    t->pa9 = value;
    ++t->pa9_calls;
    event(t, value ? 'H' : 'L');
}

static void spin(void *user, uint32_t iterations)
{
    Test *t = user;
    assert(iterations == 100000);
    ++t->spins;
    event(t, 'W');
}

static int start_original(void *user)
{
    Test *t = user;
    ++t->g_starts;
    event(t, 'G');
    return t->start_result;
}

static hyperrig_mini_codec_bus setup(Test *t, hyperrig_mini_audio_port_io *io)
{
    hyperrig_mini_codec_bus bus = {gpio, sample, delay, t, 0};
    memset(t, 0, sizeof(*t));
    io->pa9_output = pa9;
    io->spin_iterations = spin;
    io->start_original_g_channels = start_original;
    io->user = t;
    return bus;
}

int main(void)
{
    Test t;
    hyperrig_mini_codec_bus bus;
    hyperrig_mini_audio_port_io io;
    unsigned completed, n, j;
    bus = setup(&t, &io);
    assert(hyperrig_mini_audio_port_pre(&bus, &io, &completed) == 0);
    assert(completed == 22 && t.starts == 22 && t.stops == 22 && t.bytes == 110 && t.samples == 110);
    assert(t.order_count == 3 && memcmp(t.order, "LWB", 3) == 0);
    for (n = 0; n < 22; ++n) {
        const uint8_t *record = hyperrig_mini_codec_stock_record(n);
        assert(t.wire[n*5] == 0x36);
        for (j = 0; j < 4; ++j) assert(t.wire[n*5+j+1] == record[j]);
    }
    assert(hyperrig_mini_audio_port_post(&io) == 0);
    assert(t.order_count == 6 && memcmp(t.order, "LWBGWH", 6) == 0);
    assert(t.pa9 == 1 && t.pa9_calls == 2 && t.spins == 2 && t.g_starts == 1);
    for (n = 1; n <= 110; ++n) {
        bus = setup(&t, &io);
        t.nacks_at = n;
        completed = 99;
        assert(hyperrig_mini_audio_port_pre(&bus, &io, &completed) == -2);
        assert(completed == (n-1)/5 && t.samples == n && t.bytes == n);
        assert(t.pa9 == 0 && t.pa9_calls == 1 && t.spins == 1 && t.g_starts == 0);
        assert(t.starts == (n-1)/5+1 && t.stops == t.starts);
    }
    /* A failed bus wait cannot progress into the original G channel start. */
    bus = setup(&t, &io);
    t.delay_fail_at = 1;
    assert(hyperrig_mini_audio_port_pre(&bus, &io, &completed) == -37);
    assert(!completed && !t.g_starts && t.pa9 == 0 && t.pa9_calls == 1);
    for (n = 0; n < 2; ++n) {
        bus = setup(&t, &io);
        t.start_result = n ? 1 : -41;
        assert(hyperrig_mini_audio_port_post(&io) == (n ? -5 : -41));
        assert(t.g_starts == 1 && t.spins == 0 && !t.pa9_calls);
    }
    bus = setup(&t, &io);
    assert(hyperrig_mini_audio_port_pre(0, &io, &completed) == -1);
    assert(hyperrig_mini_audio_port_pre(&bus, 0, &completed) == -1);
    assert(hyperrig_mini_audio_port_post(0) == -1);
    io.start_original_g_channels = 0;
    assert(hyperrig_mini_audio_port_post(&io) == -1);
    assert(!t.order_count && !t.bus_gpio_calls);
    printf("{\"stock_sequence_cases\":1,\"nack_abort_cases\":110,"
           "\"timing_abort_cases\":1,\"original_start_failure_cases\":2,\"invalid_cases\":4}\n");
    return 0;
}
