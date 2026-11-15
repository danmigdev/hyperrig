/* Independent wire-state decoder. It observes GPIO edges, not driver helpers. */
#include "read16.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

enum { TX, ACK, RX, MASTER_ACK, WAIT_STOP };
typedef struct {
    unsigned sda, scl, input, phase, bit, active, accum;
    unsigned starts, stops, outputs, samples, delays, received, master_acks;
    unsigned wire_count, wire[8], master_ack[2], strict;
    unsigned nack, fail_delay, fail_delay2, fail_sample;
    int delay_error, sample_error;
    uint16_t data;
} Wire;

static unsigned master_sda(const Wire *w)
{
    return w->input ? 1 : w->sda;
}

static void rising(Wire *w)
{
    w->active = 1;
    if (w->phase == TX) {
        w->accum = (w->accum << 1) | master_sda(w);
    } else if (w->phase == ACK || w->phase == RX) {
        if (w->strict) assert(w->input == 1);
    } else if (w->phase == MASTER_ACK) {
        if (w->strict) {
            assert(w->master_acks < 2);
            assert(master_sda(w) == w->master_acks);
            if (w->master_acks == 1) assert(w->input == 1);
        }
        if (w->master_acks < 2)
            w->master_ack[w->master_acks] = master_sda(w);
        ++w->master_acks;
    }
}

static void falling(Wire *w)
{
    if (!w->active) return;
    w->active = 0;
    if (w->phase == TX) {
        if (++w->bit == 8) {
            if (w->strict) assert(w->wire_count < 4);
            if (w->wire_count < 8) w->wire[w->wire_count] = w->accum;
            ++w->wire_count;
            w->phase = ACK;
            w->bit = w->accum = 0;
        }
    } else if (w->phase == ACK) {
        if (w->wire_count == w->nack) w->phase = WAIT_STOP;
        else w->phase = w->wire_count == 4 ? RX : TX;
    } else if (w->phase == RX) {
        if (++w->bit == 8) {
            w->phase = MASTER_ACK;
            w->bit = 0;
            ++w->received;
        }
    } else if (w->phase == MASTER_ACK) {
        w->phase = w->master_acks < 2 ? RX : WAIT_STOP;
    }
}

static void gpio(void *user, unsigned op, unsigned pin, unsigned value)
{
    Wire *w = user;
    unsigned before = master_sda(w);
    assert(pin == 1 || pin == 2);
    assert(op == HYPERRIG_MINI_CODEC_OUTPUT || op == HYPERRIG_MINI_CODEC_DIRECTION);
    assert(value <= 1);
    ++w->outputs;
    assert(w->outputs < 800);
    if (pin == 2) {
        assert(op == HYPERRIG_MINI_CODEC_OUTPUT);
        if (!w->scl && value) rising(w);
        if (w->scl && !value) falling(w);
        w->scl = value;
    } else {
        if (op == HYPERRIG_MINI_CODEC_OUTPUT) w->sda = value, w->input = 0;
        else w->input = value;
        if (w->scl && before != master_sda(w)) {
            if (!master_sda(w)) {
                ++w->starts;
                w->phase = TX;
                w->bit = w->active = w->accum = 0;
            } else ++w->stops;
        }
    }
}

static int sample(void *user, unsigned pin)
{
    Wire *w = user;
    assert(pin == 1);
    ++w->samples;
    assert(w->samples <= 20);
    if (w->samples == w->fail_sample) return w->sample_error;
    if (w->strict) assert(w->scl && w->input && (w->phase == ACK || w->phase == RX));
    if (w->phase == ACK) return w->wire_count == w->nack;
    if (w->phase == RX && w->received < 2)
        return (w->data >> (15 - 8 * w->received - w->bit)) & 1;
    return 0;
}

static int delay(void *user, unsigned units)
{
    Wire *w = user;
    assert(units == 3 || units == 6);
    ++w->delays;
    assert(w->delays <= 193);
    return (w->delays == w->fail_delay || w->delays == w->fail_delay2) ? w->delay_error : 0;
}

static hyperrig_mini_codec_bus setup(Wire *w, unsigned value, unsigned strict)
{
    hyperrig_mini_codec_bus bus = {gpio, sample, delay, w, 1};
    memset(w, 0, sizeof(*w));
    w->sda = w->scl = 1;
    w->phase = WAIT_STOP;
    w->data = (uint16_t)value;
    w->strict = strict;
    w->delay_error = -37;
    w->sample_error = -41;
    return bus;
}

static void clean(const Wire *w)
{
    assert(w->sda == 1 && w->scl == 1 && w->input == 0);
}

int main(void)
{
    static const uint16_t regs[] = {1,3,0x1c,0x1d,0x2b,0x2c,0x31,0x32,0x58,0x59};
    Wire w;
    hyperrig_mini_codec_bus bus;
    hyperrig_mini_codec_read_result r;
    uint16_t result;
    unsigned value, index, allowed_count = 0, timing_count, faults = 0;
    for (value = 0; value <= 65535; ++value) {
        unsigned allowed = 0;
        for (index = 0; index < sizeof(regs)/sizeof(*regs); ++index)
            allowed |= value == regs[index];
        assert(hyperrig_mini_codec_probe_register_allowed((uint16_t)value) == (int)allowed);
        allowed_count += allowed;
        if (allowed) continue;
        bus = setup(&w, 0, 1);
        result = 0xa55a;
        assert(hyperrig_mini_codec_read16(&bus, (uint16_t)value, &result, &r) == -1);
        assert(result == 0xa55a && !w.outputs && !w.delays && !w.samples && !r.stop_attempted);
    }
    assert(allowed_count == 10);
    for (value = 0; value <= 65535; ++value) {
        uint16_t reg = regs[value % 10];
        bus = setup(&w, value, 1);
        result = (uint16_t)~value;
        assert(hyperrig_mini_codec_read16(&bus, reg, &result, &r) == 0);
        assert(result == value && bus.initialized && r.status == 0 && r.cleanup_status == 0);
        assert(r.acknowledged == 4 && r.received == 2 && r.samples == 20 && r.stop_attempted == 1);
        assert(w.starts == 2 && w.stops == 1 && w.wire_count == 4 && w.received == 2);
        assert(w.wire[0] == 0x36 && w.wire[1] == 0 && w.wire[2] == reg && w.wire[3] == 0x37);
        assert(w.master_acks == 2 && w.master_ack[0] == 0 && w.master_ack[1] == 1);
        clean(&w);
    }
    timing_count = w.delays;
    assert(timing_count == 193);
    for (index = 1; index <= 4; ++index) {
        bus = setup(&w, 0x1234, 1);
        w.nack = index;
        result = 0xbeef;
        assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -2);
        assert(result == 0xbeef && bus.initialized && r.acknowledged == index-1 && !r.received);
        assert(r.stop_attempted && r.cleanup_status == 0 && w.stops == 1);
        assert(w.wire_count == index && !w.master_acks);
        clean(&w);
        ++faults;
    }
    for (index = 1; index <= timing_count; ++index) {
        bus = setup(&w, 0x1234, 0);
        w.fail_delay = index;
        result = 0xbeef;
        assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -37);
        assert(!bus.initialized && result == 0xbeef && r.stop_attempted);
        assert(r.cleanup_status == (index > timing_count-3 ? -37 : 0));
        clean(&w);
        ++faults;
    }
    for (index = 1; index <= 20; ++index) {
        bus = setup(&w, 0x1234, 0);
        w.fail_sample = index;
        /* Even a callback error equal to the NACK code invalidates the bus. */
        w.sample_error = index & 1 ? -2 : -41;
        result = 0xbeef;
        assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == w.sample_error);
        assert(!bus.initialized && result == 0xbeef && r.samples == index && r.stop_attempted);
        clean(&w);
        ++faults;
    }
    for (index = 0; index < 2; ++index) {
        bus = setup(&w, 0x1234, 0);
        if (index) w.fail_sample = 1, w.sample_error = 2;
        else w.fail_delay = 1, w.delay_error = 2;
        result = 0xbeef;
        assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -5);
        assert(!bus.initialized && result == 0xbeef);
        clean(&w);
        ++faults;
    }
    /* First error survives STOP failure, whose own status is still visible. */
    bus = setup(&w, 0, 0); w.nack = 1; w.fail_delay = 33;
    result = 0xbeef;
    assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -2);
    assert(r.cleanup_status == -37 && !bus.initialized && result == 0xbeef);
    clean(&w); ++faults;
    bus = setup(&w, 0, 0); w.fail_delay = 1; w.fail_delay2 = 3;
    result = 0xbeef;
    assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -37);
    assert(r.cleanup_status == -37 && !bus.initialized && result == 0xbeef);
    clean(&w); ++faults;
    bus = setup(&w, 0, 1); bus.initialized = 0;
    assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -4 && !w.outputs);
    assert(hyperrig_mini_codec_read16(0, 0x58, &result, &r) == -1);
    assert(hyperrig_mini_codec_read16(&bus, 0x58, 0, &r) == -1);
    bus = setup(&w, 0x1234, 1);
    assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, 0) == 0 && result == 0x1234);
    bus.gpio = 0;
    assert(hyperrig_mini_codec_read16(&bus, 0x58, &result, &r) == -1);
    printf("{\"wire_values\":65536,\"register_allowlist_cases\":65536,\"fault_cases\":%u,"
           "\"precondition_cases\":5,\"success_sda_samples\":20,\"success_delay_calls\":%u}\n",
           faults, timing_count);
    return 0;
}
