/* Execute the unchanged writer C with fake NOR and ROM callbacks only.
 * Reuse the frozen harness helpers; its original main is never invoked. */
#define main frozen_writer_reference_main
#include "../firmware/mini/app_writer/test_writer.c"
#undef main

static void prepare_echo(int after_program)
{
    fresh();init();arm(0x5000);stage(0x5000,0);
    if(after_program){
        echo(0x5000,0);action(0xfc7b,0x5000);assert(!error());
        action(0xfc7d,0x5000);assert(!error());stage(0x5100,1);
    }
}

static void compare_only_echo(const uint8_t *before,const uint8_t *after)
{
    unsigned i;
    assert(le32(before+104)==0&&le32(after+104)==1);
    for(i=0;i<128;++i)
        if(!(i>=104&&i<108)&&!(i>=120&&i<124))assert(before[i]==after[i]);
    assert(le32(after+120)==hyw_crc32(after,120));
}

int main(void)
{
    uint8_t before[128],after[128];unsigned i,j,nor_calls,receive_calls;
    unsigned observed=0;
    for(i=0;i<2;++i)for(j=0;j<2;++j){
        prepare_echo((int)i);record();memcpy(before,reply_data,128);
        nor_calls=f.calls;receive_calls=f.receive_calls;
        f.send_result=j?256:0;
        echo(i?0x5100:0x5000,i);record();memcpy(after,reply_data,128);
        compare_only_echo(before,after);
        command(0xfc78,16,0);dispatch(); /* Same identity query used on reopen. */
        record();assert(!memcmp(after,reply_data,128));
        echo(i?0x5100:0x5000,i);record();assert(!memcmp(after,reply_data,128));
        assert(f.calls==nor_calls&&f.receive_calls==receive_calls);
        assert(f.wren==(i?2u:0u)&&f.erase==i&&f.program==i);
        ++observed;
    }

    prepare_echo(0);nor_calls=f.calls;f.send_result=-1;
    echo(0x5000,0);f.send_result=0;assert(error()==HYW_TRANSPORT);
    record();assert(le32(reply_data+100)==0&&le32(reply_data+104)==0);
    assert(le32(reply_data+16)==HYW_FAILED&&f.calls==nor_calls);++observed;

    prepare_echo(0);nor_calls=f.calls;
    command(0xfd87,256,0);putbe32(cbw+17,token);putbe32(cbw+21,seq+1);putbe32(cbw+25,0x5000);
    dispatch();assert(error()==HYW_STATE&&f.calls==nor_calls);++observed;

    prepare_echo(0);nor_calls=f.calls;f.rx_pointer[-1]^=1;
    command(0xfd87,256,0);putbe32(cbw+17,token);putbe32(cbw+21,seq);putbe32(cbw+25,0x5000);
    dispatch();assert(error()==HYW_STATE&&f.calls==nor_calls);++observed;

    prepare_echo(0);record();memcpy(before,reply_data,128);nor_calls=f.calls;
    /* A later alteration of receive RAM cannot change the frozen PP source. */
    f.rx_pointer[0]^=1;echo(0x5000,0);record();compare_only_echo(before,reply_data);
    echo(0x5000,0);assert(f.calls==nor_calls&&!f.wren&&!f.erase&&!f.program);++observed;

    printf("{\"cases\":%u,\"frozen_C_executed\":true,\"fake_NOR_only\":true,\"hardware\":false}\n",observed);
    return 0;
}
