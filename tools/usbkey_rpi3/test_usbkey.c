#define USBKEY_TEST
#include "usbkey.c"
#include <assert.h>

static unsigned cases;
static enum result test_run(struct fake *f, uint64_t timeout, struct telemetry *t)
{
    volatile sig_atomic_t stop = 0;
    struct params p = defaults;
    p.timeout_ns = timeout;
    struct io io = {f, fake_now, fake_wait, fake_set, fake_get, &stop};
    memset(t, 0, sizeof *t);
    enum result r = run_key(&io, &p, t);
    assert(f->released == BOTH);
    /* Every SAMPLE in the complete retained trace must follow BOTH release.
     * The backend additionally rejects a sample if either line is driven. */
    unsigned released = BOTH;
    for (uint64_t i = 0; i < t->events && t->events <= TRACE_CAPACITY; ++i) {
        const struct event *e = &t->trace[i];
        assert((e->mask & ~BOTH) == 0 && (e->bits & ~BOTH) == 0);
        if (e->op == 1) released = (released & ~e->mask) | (e->bits & e->mask);
        if (e->op == 2) assert(released == BOTH);
    }
    cases++;
    return r;
}

int main(void)
{
    struct telemetry *t = calloc(1, sizeof *t);
    assert(t);
    struct fake f = {.now_ns=1, .ack_width=1200000, .released=BOTH};
    assert(test_run(&f, 10000000, t) == ACK_CANDIDATE);
    assert(f.rising_edges == 16 && f.captured_word == KEY_WORD);
    assert(t->frame_count == 1 && t->first_high_ns == 1);
    assert(t->ack_observed_low_ns >= defaults.ack_min_ns);
    assert(t->ack_observed_low_ns <= defaults.ack_max_ns);
    assert(t->min_half_hold_ns == 10000 && t->max_half_hold_ns == 10000);
    assert(t->cleanup_release_ok);
    int normal_calls = f.calls;

    /* Powered-off/clamped LOW is never an ACK and never starts transmission. */
    f = (struct fake){.now_ns=1, .released=BOTH, .never_high=1};
    assert(test_run(&f, 5000000, t) == TIMEOUT);
    assert(t->frame_count == 0 && f.rising_edges == 0 && !t->first_high_ns);

    f = (struct fake){.now_ns=1, .released=BOTH, .no_ack=1};
    assert(test_run(&f, 2000000, t) == TIMEOUT);
    assert(t->frame_count > 1 && !t->ack_observed_low_ns);

    /* High first is necessary but insufficient: a permanently low target
     * after transmission must not be reported as a completed ACK pulse. */
    f = (struct fake){.now_ns=1, .released=BOTH, .stuck=1};
    assert(test_run(&f, 10000000, t) == STUCK_LOW);
    assert(t->frame_count == 1 && !t->ack_observed_low_ns);

    f = (struct fake){.now_ns=1, .released=BOTH, .ack_width=200000};
    assert(test_run(&f, 2000000, t) == TIMEOUT); /* Short glitch. */
    f = (struct fake){.now_ns=1, .released=BOTH, .ack_width=4000000};
    assert(test_run(&f, 10000000, t) == STUCK_LOW);
    f = (struct fake){.now_ns=1, .released=BOTH, .ack_width=1200000, .inject_poll_gap=1};
    assert(test_run(&f, 10000000, t) == ACK_TIMING_AMBIGUOUS);
    assert(t->max_ack_poll_gap_ns > defaults.max_ack_poll_gap_ns);

    /* Operation overhead is logged; the engine never catches up with a
     * shorter half-period after slow GPIO/scheduler operations. */
    f = (struct fake){.now_ns=1, .released=BOTH, .ack_width=1200000,
                      .operation_ns=5000, .wait_jitter_ns=7000};
    assert(test_run(&f, 10000000, t) == ACK_CANDIDATE);
    assert(t->max_gpio_call_ns == 5000 && t->max_wait_lateness_ns == 7000);
    assert(t->min_half_hold_ns == 17000 && t->max_half_hold_ns == 17000);

    /* Inject failures into every command/sample of the normal exchange,
     * including cleanup. An I/O failure cannot become ACK success. */
    for (int point = 1; point <= normal_calls; ++point) {
        f = (struct fake){.now_ns=1, .released=BOTH, .ack_width=1200000, .fail_at=point};
        assert(test_run(&f, 10000000, t) == IO_ERROR);
    }
    for (unsigned timeout_us = 1; timeout_us < 350; timeout_us += 7) {
        f = (struct fake){.now_ns=1, .released=BOTH, .no_ack=1};
        assert(test_run(&f, (uint64_t)timeout_us*1000, t) == TIMEOUT);
        assert(!t->ack_observed_low_ns);
    }
    volatile sig_atomic_t stop = 1;
    f = (struct fake){.now_ns=1, .released=BOTH};
    struct io io = {&f, fake_now, fake_wait, fake_set, fake_get, &stop};
    memset(t, 0, sizeof *t);
    assert(run_key(&io, &defaults, t) == INTERRUPTED);
    assert(f.released == BOTH && t->cleanup_release_ok && !t->frame_count);
    cases++;
    printf("{\"result\":\"PASS\",\"cases\":%u,\"GPIO_access\":false,\"status_name\":\"%s\"}\n",
           cases, result_name(ACK_CANDIDATE));
    free(t);
    return 0;
}
