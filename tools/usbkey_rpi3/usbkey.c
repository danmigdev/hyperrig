/* USB_KEY experiment for Raspberry Pi 3: no USB transfers or flash commands.
 * Default is a virtual-clock simulation. Real GPIO uses Linux GPIO uAPI v2
 * exclusively, OUTPUT|OPEN_DRAIN|BIAS_DISABLED, never push-pull HIGH.
 * Build: cc -std=c11 -O2 -Wall -Wextra -Werror usbkey.c -o usbkey-rpi3
 */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define KEY_WORD 0x16efu
#define DP 1u
#define DM 2u
#define BOTH 3u
#define TRACE_CAPACITY 4096u
#define NS_PER_US UINT64_C(1000)

enum result { ACK_CANDIDATE, TIMEOUT, IO_ERROR, INTERRUPTED, STUCK_LOW,
              ACK_TIMING_AMBIGUOUS };
static const char *result_name(enum result r)
{
    static const char *names[] = {"ack_candidate", "timeout", "io_error",
        "interrupted", "stuck_low_after_high", "ack_timing_ambiguous"};
    return names[r];
}

struct params {
    uint64_t half_ns, gap_ns, poll_ns, timeout_ns;
    uint64_t ack_min_ns, ack_max_ns, max_ack_poll_gap_ns;
};
static const struct params defaults = {10000, 150000, 20000, 20000000000,
                                       500000, 3000000, 100000};
struct event {
    uint64_t sequence, before_ns, after_ns;
    unsigned op, mask, bits;
};
struct telemetry {
    struct event trace[TRACE_CAPACITY];
    uint64_t events, frame_count, samples, operations;
    uint64_t first_high_ns, ack_observed_low_ns;
    uint64_t max_gpio_call_ns, waits, max_wait_lateness_ns;
    uint64_t min_half_hold_ns, max_half_hold_ns, max_ack_poll_gap_ns;
    unsigned released_bits;
    int cleanup_release_ok;
};
struct io {
    void *context;
    uint64_t (*now)(void *);
    void (*wait_until)(void *, uint64_t);
    int (*set)(void *, unsigned mask, unsigned released_bits);
    int (*get)(void *, unsigned *levels);
    volatile sig_atomic_t *stop;
};

static void record(struct telemetry *t, unsigned op, unsigned mask, unsigned bits,
                   uint64_t before, uint64_t after)
{
    struct event *e = &t->trace[t->events % TRACE_CAPACITY];
    e->sequence = t->events++;
    e->before_ns = before;
    e->after_ns = after;
    e->op = op;
    e->mask = mask;
    e->bits = bits;
    if (after-before > t->max_gpio_call_ns) t->max_gpio_call_ns = after-before;
}

static int set_lines(struct io *io, struct telemetry *t, unsigned mask, unsigned bits)
{
    uint64_t before = io->now(io->context);
    int rc;
    if ((mask & ~BOTH) || (bits & ~BOTH)) return -1;
    rc = io->set(io->context, mask, bits);
    record(t, rc ? 3 : 1, mask, bits, before, io->now(io->context));
    t->operations++;
    if (!rc) t->released_bits = (t->released_bits & ~mask) | (bits & mask);
    return rc;
}

static int sample(struct io *io, struct telemetry *t, unsigned *levels)
{
    uint64_t before = io->now(io->context);
    int rc;
    /* ACK is never sampled while this program drives either line LOW. */
    if (t->released_bits != BOTH) return -1;
    rc = io->get(io->context, levels);
    record(t, rc ? 3 : 2, BOTH, rc ? 0 : *levels, before, io->now(io->context));
    t->samples++;
    return rc;
}

static void wait_minimum(struct io *io, struct telemetry *t, uint64_t duration,
                         int half_period)
{
    uint64_t before = io->now(io->context), deadline = before+duration, after;
    io->wait_until(io->context, deadline);
    after = io->now(io->context);
    t->waits++;
    if (after >= deadline && after-deadline > t->max_wait_lateness_ns)
        t->max_wait_lateness_ns = after-deadline;
    if (half_period && after >= before) {
        uint64_t hold = after-before;
        if (!t->min_half_hold_ns || hold < t->min_half_hold_ns) t->min_half_hold_ns = hold;
        if (hold > t->max_half_hold_ns) t->max_half_hold_ns = hold;
    }
}

static enum result run_key(struct io *io, const struct params *p, struct telemetry *t)
{
    uint64_t start = io->now(io->context), low_since = 0, last_sample = 0;
    int seen_high = 0, pending_low = 0, ambiguous = 0;
    enum result result = TIMEOUT;
    if (set_lines(io, t, BOTH, BOTH)) { result = IO_ERROR; goto done; }
    while (io->now(io->context)-start < p->timeout_ns) {
        unsigned levels;
        uint64_t now;
        if (*io->stop) { result = INTERRUPTED; break; }
        if (sample(io, t, &levels)) { result = IO_ERROR; break; }
        now = io->now(io->context);
        if (pending_low) {
            uint64_t gap = now-last_sample;
            if (gap > t->max_ack_poll_gap_ns) t->max_ack_poll_gap_ns = gap;
            if (gap > p->max_ack_poll_gap_ns) ambiguous = 1;
            if (levels != 0) {
                uint64_t duration = now-low_since;
                if (duration >= p->ack_min_ns && duration <= p->ack_max_ns) {
                    t->ack_observed_low_ns = duration;
                    result = ambiguous ? ACK_TIMING_AMBIGUOUS : ACK_CANDIDATE;
                    break;
                }
                pending_low = 0;
                if (duration > p->ack_max_ns) { result = STUCK_LOW; break; }
            } else if (now-low_since > p->ack_max_ns) {
                result = STUCK_LOW;
                break;
            }
        } else if (levels == 0 && seen_high && t->frame_count) {
            pending_low = 1;
            ambiguous = 0;
            low_since = now;
        }
        last_sample = now;
        if (levels == BOTH) {
            if (!seen_high) t->first_high_ns = now;
            seen_high = 1;
        }
        if (pending_low || levels != BOTH) {
            wait_minimum(io, t, p->poll_ns, 0);
            continue;
        }
        /* Data changes while clock is LOW; release D+ for the rising edge.
         * A value1 always means high impedance under the OPEN_DRAIN request. */
        for (unsigned bit = 16; bit-- > 0;) {
            unsigned data = ((KEY_WORD >> bit) & 1u) ? DM : 0;
            if (*io->stop) { result = INTERRUPTED; goto done; }
            if (io->now(io->context)-start >= p->timeout_ns) goto done;
            if (set_lines(io, t, BOTH, data)) { result = IO_ERROR; goto done; }
            wait_minimum(io, t, p->half_ns, 1);
            if (*io->stop) { result = INTERRUPTED; goto done; }
            if (io->now(io->context)-start >= p->timeout_ns) goto done;
            if (set_lines(io, t, DP, DP)) { result = IO_ERROR; goto done; }
            wait_minimum(io, t, p->half_ns, 1);
        }
        t->frame_count++;
        if (set_lines(io, t, BOTH, BOTH)) { result = IO_ERROR; break; }
        /* Monitor the released inter-frame gap. Stop transmitting as soon as
         * a possible ACK is seen, rather than clocking over its LOW pulse. */
        uint64_t gap_start = io->now(io->context);
        while (io->now(io->context)-gap_start < p->gap_ns) {
            if (*io->stop) { result = INTERRUPTED; goto done; }
            if (io->now(io->context)-start >= p->timeout_ns) goto done;
            if (sample(io, t, &levels)) { result = IO_ERROR; goto done; }
            now = io->now(io->context);
            if (levels == 0) {
                pending_low = 1;
                ambiguous = 0;
                low_since = last_sample = now;
                break;
            }
            if (levels == BOTH && !seen_high) t->first_high_ns = now;
            if (levels == BOTH) seen_high = 1;
            last_sample = now;
            wait_minimum(io, t, p->poll_ns, 0);
        }
    }
done:
    t->cleanup_release_ok = set_lines(io, t, BOTH, BOTH) == 0;
    if (!t->cleanup_release_ok) result = IO_ERROR;
    return result;
}

/* Virtual-clock default: one frame followed by a finite1.2ms simulated ACK.
 * Every backend operation is logged through the same engine used on Linux. */
struct fake {
    uint64_t now_ns, ack_begin, ack_width, operation_ns, wait_jitter_ns;
    unsigned released, rising_edges;
    int never_high, no_ack, stuck, fail_at, calls, inject_poll_gap;
    uint64_t gap_injected;
    uint16_t captured_word;
};
static uint64_t fake_now(void *ctx) { return ((struct fake *)ctx)->now_ns; }
static void fake_wait(void *ctx, uint64_t deadline)
{
    struct fake *f = ctx;
    f->now_ns = deadline+f->wait_jitter_ns;
    if (f->inject_poll_gap && f->ack_begin && f->now_ns > f->ack_begin+200000 && !f->gap_injected) {
        f->now_ns += 250000;
        f->gap_injected = 1;
    }
}
static int fake_set(void *ctx, unsigned mask, unsigned bits)
{
    struct fake *f = ctx;
    unsigned next = (f->released & ~mask) | (bits & mask);
    f->now_ns += f->operation_ns;
    if (++f->calls == f->fail_at) return -1;
    if (!(f->released & DP) && (next & DP)) {
        f->captured_word = (uint16_t)((f->captured_word << 1) | !!(next & DM));
        f->rising_edges++;
        if (f->rising_edges == 16 && !f->ack_begin && !f->no_ack)
            f->ack_begin = f->now_ns+30000;
    }
    f->released = next;
    return 0;
}
static int fake_get(void *ctx, unsigned *levels)
{
    struct fake *f = ctx;
    f->now_ns += f->operation_ns;
    if (++f->calls == f->fail_at) return -1;
    if (f->released != BOTH) return -1;
    if (f->never_high) *levels = 0;
    else if (f->ack_begin && f->now_ns >= f->ack_begin &&
             (f->stuck || f->now_ns < f->ack_begin+f->ack_width)) *levels = 0;
    else *levels = BOTH;
    return 0;
}

#ifndef USBKEY_TEST
#include <fcntl.h>
#include <linux/gpio.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>

static volatile sig_atomic_t stopping;
static void stop_handler(int sig) { (void)sig; stopping = 1; }
struct hardware { int chip_fd, request_fd; char model[128], label[GPIO_MAX_NAME_SIZE]; };

static uint64_t real_now(void *unused)
{
    struct timespec t;
    (void)unused;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) abort();
    return (uint64_t)t.tv_sec*UINT64_C(1000000000)+(uint64_t)t.tv_nsec;
}
static void real_wait(void *ctx, uint64_t deadline)
{
    /* Minimum duration after ioctl completion. Never catch up using runt
     * pulses. Busy waits consume a CPU; scheduling/IRQs are not changed. */
    while (!stopping && real_now(ctx) < deadline) { }
}
static uint64_t timing_now(void *ctx)
{
    struct fake *f = ctx;
    f->now_ns = real_now(NULL);
    return f->now_ns;
}
static void timing_wait(void *ctx, uint64_t deadline)
{
    real_wait(NULL, deadline);
    (void)timing_now(ctx);
}
static int real_set(void *ctx, unsigned mask, unsigned bits)
{
    struct hardware *h = ctx;
    struct gpio_v2_line_values v = {.bits = bits, .mask = mask};
    return ioctl(h->request_fd, GPIO_V2_LINE_SET_VALUES_IOCTL, &v);
}
static int real_get(void *ctx, unsigned *levels)
{
    struct hardware *h = ctx;
    struct gpio_v2_line_values v = {.bits = 0, .mask = BOTH};
    if (ioctl(h->request_fd, GPIO_V2_LINE_GET_VALUES_IOCTL, &v)) return -1;
    *levels = (unsigned)v.bits & BOTH;
    return 0;
}

static int hardware_open(struct hardware *h, const char *path)
{
    FILE *f;
    struct stat st;
    struct gpiochip_info chip = {0};
    struct gpio_v2_line_request request = {0};
    h->chip_fd = h->request_fd = -1;
    f = fopen("/proc/device-tree/model", "rb");
    if (!f) return -1;
    size_t n = fread(h->model, 1, sizeof h->model-1, f);
    fclose(f);
    h->model[n] = 0;
    if (strncmp(h->model, "Raspberry Pi 3 Model ", 21)) { errno = ENODEV; return -1; }
    h->chip_fd = open(path, O_RDWR | O_CLOEXEC);
    if (h->chip_fd < 0) return -1;
    if (fstat(h->chip_fd, &st) || !S_ISCHR(st.st_mode)) { errno = ENODEV; return -1; }
    if (ioctl(h->chip_fd, GPIO_GET_CHIPINFO_IOCTL, &chip)) return -1;
    memcpy(h->label, chip.label, sizeof h->label);
    h->label[sizeof h->label-1] = 0;
    /* Exclude Pi3's separate firmware GPIO expander and other board maps. */
    if (strcmp(h->label, "pinctrl-bcm2835") || chip.lines < 28) { errno = ENODEV; return -1; }
    const unsigned pins[] = {17, 27};
    for (unsigned i = 0; i < 2; ++i) {
        struct gpio_v2_line_info info = {.offset = pins[i]};
        if (ioctl(h->chip_fd, GPIO_V2_GET_LINEINFO_IOCTL, &info)) return -1;
        if (info.flags & GPIO_V2_LINE_FLAG_USED) { errno = EBUSY; return -1; }
        char expected[16];
        snprintf(expected, sizeof expected, "GPIO%u", pins[i]);
        if (info.name[0] && strncmp(info.name, expected, sizeof info.name)) { errno = ENODEV; return -1; }
        request.offsets[i] = pins[i];
    }
    strcpy(request.consumer, "hyperrig-usbkey");
    request.num_lines = 2;
    request.config.flags = GPIO_V2_LINE_FLAG_OUTPUT | GPIO_V2_LINE_FLAG_OPEN_DRAIN |
                           GPIO_V2_LINE_FLAG_BIAS_DISABLED;
    request.config.num_attrs = 1;
    request.config.attrs[0].attr.id = GPIO_V2_LINE_ATTR_ID_OUTPUT_VALUES;
    request.config.attrs[0].attr.values = BOTH; /* Released from initial request. */
    request.config.attrs[0].mask = BOTH;
    /* No ACTIVE_LOW, no push-pull retry, no /dev/mem or sysfs fallback. */
    if (ioctl(h->chip_fd, GPIO_V2_GET_LINE_IOCTL, &request)) return -1;
    h->request_fd = request.fd;
    return 0;
}

static int hardware_close(struct hardware *h)
{
    int failed = 0;
    if (h->request_fd >= 0) {
        struct gpio_v2_line_config config = {0};
        if (real_set(h, BOTH, BOTH)) failed = 1;
        config.flags = GPIO_V2_LINE_FLAG_INPUT | GPIO_V2_LINE_FLAG_BIAS_DISABLED;
        if (ioctl(h->request_fd, GPIO_V2_LINE_SET_CONFIG_IOCTL, &config)) failed = 1;
        if (close(h->request_fd)) failed = 1;
        h->request_fd = -1;
    }
    if (h->chip_fd >= 0) { close(h->chip_fd); h->chip_fd = -1; }
    return failed ? -1 : 0;
}

static void json_string(FILE *f, const char *s)
{
    fputc('"', f);
    for (; *s; ++s) {
        unsigned c = (unsigned char)*s;
        if (c == '"' || c == '\\') fprintf(f, "\\%c", c);
        else if (c < 32 || c >= 127) fprintf(f, "\\u%04x", c);
        else fputc((int)c, f);
    }
    fputc('"', f);
}

static void report(FILE *f, const struct params *p, const struct telemetry *t,
                   enum result r, int execute, int input_cleanup, const char *detail)
{
    fprintf(f, "{\n  \"schema\":1,\n  \"mode\":\"%s\",\n  \"result\":\"%s\",\n",
            execute == 1 ? "gpio-experiment" : execute == 2 ? "timing-only" : "simulation", result_name(r));
    fprintf(f, "  \"mini_verified\":false,\n  \"ROM_identity_verified\":false,\n");
    fprintf(f, "  \"pins\":{\"DP_BCM\":17,\"DP_header\":11,\"DM_BCM\":27,\"DM_header\":13},\n");
    fprintf(f, "  \"word\":5871,\n  \"bit_order\":\"MSB-first\",\n  \"drive\":\"OPEN_DRAIN low/release only\",\n");
    fprintf(f, "  \"nominal_half_ns\":%" PRIu64 ",\n  \"nominal_gap_ns\":%" PRIu64 ",\n", p->half_ns, p->gap_ns);
    fprintf(f, "  \"timeout_ns\":%" PRIu64 ",\n  \"ack_policy_ns\":{\"min\":%" PRIu64 ",\"max\":%" PRIu64 ",\"max_poll_gap\":%" PRIu64 "},\n",
            p->timeout_ns, p->ack_min_ns, p->ack_max_ns, p->max_ack_poll_gap_ns);
    fprintf(f, "  \"frames\":%" PRIu64 ",\n  \"first_released_high_ns\":%" PRIu64 ",\n  \"ack_observed_low_ns\":%" PRIu64 ",\n",
            t->frame_count, t->first_high_ns, t->ack_observed_low_ns);
    fprintf(f, "  \"max_gpio_call_ns\":%" PRIu64 ",\n  \"max_wait_lateness_ns\":%" PRIu64 ",\n  \"half_hold_ns\":{\"min\":%" PRIu64 ",\"max\":%" PRIu64 "},\n  \"max_ack_poll_gap_ns\":%" PRIu64 ",\n",
            t->max_gpio_call_ns, t->max_wait_lateness_ns, t->min_half_hold_ns,
            t->max_half_hold_ns, t->max_ack_poll_gap_ns);
    fprintf(f, "  \"release_cleanup_ok\":%s,\n  \"input_cleanup_ok\":%s,\n  \"detail\":",
            t->cleanup_release_ok ? "true" : "false", input_cleanup ? "true" : "false");
    json_string(f, detail);
    uint64_t first = t->events > TRACE_CAPACITY ? t->events-TRACE_CAPACITY : 0;
    fprintf(f, ",\n  \"event_total\":%" PRIu64 ",\n  \"earlier_events_omitted\":%" PRIu64 ",\n  \"trace_clock\":\"%s\",\n  \"trace_columns\":[\"sequence\",\"operation\",\"mask\",\"released_or_sampled_bits\",\"before_ns\",\"after_ns\"],\n  \"trace\":[\n",
            t->events, first, execute == 1 ? "CLOCK_MONOTONIC software ioctl bounds" :
                execute == 2 ? "CLOCK_MONOTONIC fake lines, no GPIO" : "virtual clock");
    for (uint64_t i = first; i < t->events; ++i) {
        const struct event *e = &t->trace[i % TRACE_CAPACITY];
        fprintf(f, "    [%" PRIu64 ",\"%s\",%u,%u,%" PRIu64 ",%" PRIu64 "]%s\n",
                e->sequence, e->op == 1 ? "set_open_drain" : e->op == 2 ? "sample" : "io_error",
                e->mask, e->bits, e->before_ns, e->after_ns, i+1 == t->events ? "" : ",");
    }
    fprintf(f, "  ]\n}\n");
}

static int parse_ms(const char *arg, uint64_t *out)
{
    char *end;
    errno = 0;
    unsigned long value = strtoul(arg, &end, 10);
    if (errno || !*arg || *end || value < 1 || value > 60000) return -1;
    *out = (uint64_t)value*1000000;
    return 0;
}

int main(int argc, char **argv)
{
    struct params p = defaults;
    struct telemetry *t = calloc(1, sizeof *t);
    struct hardware hardware = {.chip_fd = -1, .request_fd = -1};
    struct fake fake = {.now_ns = 1, .ack_width = 1200000, .released = BOTH};
    struct io io = {&fake, fake_now, fake_wait, fake_set, fake_get, &stopping};
    int execute = 0, input_cleanup = 1, rc = 0;
    const char *chip = "/dev/gpiochip0", *log = NULL, *detail = "Simulated ACK; no GPIO device was opened.";
    FILE *output = stdout;
    enum result r;
    if (!t) return 1;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--execute")) execute = 1;
        else if (!strcmp(argv[i], "--dry-run")) execute = 0;
        else if (!strcmp(argv[i], "--timing-only")) execute = 2;
        else if (!strcmp(argv[i], "--chip") && i+1 < argc) chip = argv[++i];
        else if (!strcmp(argv[i], "--log") && i+1 < argc) log = argv[++i];
        else if (!strcmp(argv[i], "--timeout-ms") && i+1 < argc && !parse_ms(argv[++i], &p.timeout_ns)) { }
        else {
            fprintf(stderr, "Usage: %s [--dry-run | --timing-only | --execute] [--chip /dev/gpiochip0] [--timeout-ms 1..60000] [--log NEW.json]\nDefault: simulation, no GPIO access. --timing-only measures host scheduling with fake lines. --execute requires Pi3 wiring; see docs/MINI_USBKEY_RPI3.md.\n", argv[0]);
            free(t);
            return !strcmp(argv[i], "--help") ? 0 : 1;
        }
    }
    if (log) {
        output = fopen(log, "wx");
        if (!output) { perror("new log file"); free(t); return 1; }
    }
    signal(SIGINT, stop_handler);
    signal(SIGTERM, stop_handler);
    if (execute == 2) {
        io.now = timing_now;
        io.wait_until = timing_wait;
        fake.no_ack = 1;
        detail = "Host scheduling check using fake lines until timeout; GPIO ioctl latency and electrical edge timing are not measured.";
    }
    if (execute == 1) {
        if (hardware_open(&hardware, chip)) {
            detail = strerror(errno);
            r = IO_ERROR;
            input_cleanup = hardware_close(&hardware) == 0;
            report(output, &p, t, r, execute, input_cleanup, detail);
            rc = 1;
            goto done;
        }
        io = (struct io){&hardware, real_now, real_wait, real_set, real_get, &stopping};
        fprintf(stderr, "Pi3 GPIO experiment active: BCM17/header11=D+, BCM27/header13=D-. Low/release only; no PC USB host may share the pair.\n");
        detail = "Software timing only; an ACK candidate still requires independent ROM USB identification after disconnecting this GPIO circuit.";
    }
    r = run_key(&io, &p, t);
    if (execute == 1) {
        input_cleanup = hardware_close(&hardware) == 0;
        if (!input_cleanup) r = IO_ERROR;
    }
    report(output, &p, t, r, execute, input_cleanup, detail);
    if (r != ACK_CANDIDATE) rc = r == TIMEOUT ? 2 : 1;
done:
    if (fflush(output)) rc = 1;
    if (output != stdout && fclose(output)) rc = 1;
    free(t);
    return rc;
}
#endif
