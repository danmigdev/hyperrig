/* Reuse the frozen v1 wire decoder, not its fail-fast expectations. */
#include "audio_port_v2.h"
#define main hyperrig_audio_v1_test_not_run
#include "../audio_port/test_audio_port.c"
#undef main

static int every_nack, sample_error;
static int v2_sample(void *user,unsigned pin)
{
    Test *t=user;
    int nack=sample(user,pin);
    (void)t;
    return sample_error ? sample_error : every_nack ? 1 : nack;
}
static hyperrig_mini_codec_bus setup_v2(Test *t,hyperrig_mini_audio_port_io *io)
{
    hyperrig_mini_codec_bus bus=setup(t,io);
    bus.sample=v2_sample;
    every_nack=sample_error=0;
    return bus;
}
int main(void)
{
    Test t;
    hyperrig_mini_codec_bus bus;
    hyperrig_mini_audio_port_io io;
    hyperrig_mini_audio_v2_result result;
    unsigned completed,n,rec,j,cursor;
    bus=setup_v2(&t,&io);
    assert(hyperrig_mini_audio_v2_pre(&bus,&io,&completed,&result)==0);
    assert(completed==22 && result.records_attempted==22 && result.records_acknowledged==22);
    assert(result.bytes_acknowledged==110 && !result.records_nacked && !result.fatal_status);
    assert(t.starts==22 && t.stops==22 && t.bytes==110 && t.samples==110);
    assert(hyperrig_mini_audio_port_post(&io)==0 && memcmp(t.order,"LWBGWH",6)==0);
    for(n=1;n<=110;++n) {
        unsigned bad_record=(n-1)/5,bad_length=(n-1)%5+1;
        bus=setup_v2(&t,&io);t.nacks_at=n;
        assert(hyperrig_mini_audio_v2_pre(&bus,&io,&completed,&result)==0);
        assert(completed==21 && result.records_attempted==22 && result.records_acknowledged==21);
        assert(result.records_nacked==1 && result.records_continued_after_nack==1);
        assert(result.bytes_acknowledged==104+bad_length && !result.fatal_status);
        assert(t.bytes==105+bad_length && t.samples==t.bytes && t.starts==22 && t.stops==22);
        cursor=0;
        for(rec=0;rec<22;++rec) {
            unsigned length=rec==bad_record ? bad_length : 5;
            const uint8_t *record=hyperrig_mini_codec_stock_record(rec);
            assert(t.wire[cursor++]==0x36);
            for(j=1;j<length;++j) assert(t.wire[cursor++]==record[j-1]);
        }
        assert(cursor==t.bytes && bus.initialized && t.pa9==0 && !t.g_starts);
        assert(hyperrig_mini_audio_port_post(&io)==0 && t.g_starts==1 && t.pa9==1);
    }
    bus=setup_v2(&t,&io);every_nack=1;
    assert(hyperrig_mini_audio_v2_pre(&bus,&io,&completed,&result)==0);
    assert(!completed && !result.records_acknowledged && !result.bytes_acknowledged);
    assert(result.records_attempted==22 && result.records_nacked==22 && result.records_continued_after_nack==22);
    assert(t.starts==22 && t.stops==22 && t.bytes==22 && t.samples==22);
    for(n=0;n<22;++n) assert(t.wire[n]==0x36);
    assert(hyperrig_mini_audio_port_post(&io)==0); /* Continuation is not an ACK claim. */
    for(n=1;n<=35;++n) {
        bus=setup_v2(&t,&io);every_nack=1;t.delay_fail_at=n;
        assert(hyperrig_mini_audio_v2_pre(&bus,&io,&completed,&result)==-37);
        assert(!completed && result.records_attempted==1 && !result.records_acknowledged);
        assert(!result.records_continued_after_nack && result.fatal_status==-37);
        assert(!t.g_starts && !t.pa9 && !bus.initialized);
        if(n>=33) assert(result.records_nacked==1); /* First error NACK; STOP error remains fatal. */
    }
    bus=setup_v2(&t,&io);sample_error=-41;
    assert(hyperrig_mini_audio_v2_pre(&bus,&io,&completed,&result)==-41);
    assert(!completed && !result.records_continued_after_nack && result.fatal_status==-41);
    for(n=0;n<2;++n) {
        bus=setup_v2(&t,&io);t.start_result=n?1:-41;
        assert(hyperrig_mini_audio_port_post(&io)==(n?-5:-41));
        assert(t.g_starts==1 && !t.spins && !t.pa9_calls);
    }
    bus=setup_v2(&t,&io);
    assert(hyperrig_mini_audio_v2_pre(0,&io,&completed,&result)==-1 && result.fatal_status==-1);
    assert(hyperrig_mini_audio_port_pre(&bus,0,&completed)==-1);
    assert(hyperrig_mini_audio_port_post(0)==-1);
    io.start_original_g_channels=0;
    assert(hyperrig_mini_audio_port_post(&io)==-1 && !t.order_count);
    printf("{\"all_ACK\":1,\"single_NACK_continued\":110,\"all_22_address_NACK_continued_ACK_count_zero\":1,"
           "\"fatal_delay_or_cleanup\":35,\"fatal_sample\":1,\"post_failure\":2,\"invalid\":4,"
           "\"next_record_START_and_bytes_verified\":true,\"physical_equivalence_claimed\":false}\n");
    return 0;
}
