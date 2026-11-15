#include "audio_port_v2.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

static uint32_t port[9],before[9],random_state;
static unsigned count,locked,enters,exits;
static char order[8];
static int next_status;
static uint32_t random_word(void)
{
    random_state=random_state*1664525u+1013904223u;
    return random_state;
}
static void begin(char event)
{
    assert(!locked);locked=1;++enters;order[count++]=event;
}
static void end(void){assert(locked);locked=0;++exits;}
void hyperrig_audio_v2_test_digital(unsigned pin,unsigned value)
{
    assert(pin==37 && value==1);begin('D');port[3]|=32;end();
}
void hyperrig_audio_v2_test_output(unsigned pin,unsigned value)
{
    assert(pin==37 && value==1);begin('O');port[0]|=32;port[2]&=~32u;end();
}
void hyperrig_mini_g_pc5_hd_clear(void){begin('H');port[7]&=~32u;end();}
void hyperrig_audio_v2_test_hd0(unsigned pin)
{
    assert(pin==37);begin('h');port[6]&=~32u;end();
}
int hyperrig_mini_g_audio_pre_current_clock_v1(void)
{
    unsigned i;
    assert(count==4 && memcmp(order,"DOHh",4)==0 && !locked && enters==4 && exits==4);
    for(i=0;i<9;++i) {
        uint32_t expected=before[i];
        if(i==0 || i==3)expected|=32;
        if(i==2 || i==6 || i==7)expected&=~32u;
        assert(port[i]==expected);
    }
    order[count++]='V';
    return next_status;
}
int main(void)
{
    static const int statuses[]={0,-1,-2,-3,-4,-5,-37,1,INT_MAX,INT_MIN};
    unsigned i,j,k;
    for(i=0;i<64;++i) for(j=0;j<sizeof(statuses)/sizeof(statuses[0]);++j) {
        random_state=i+1;count=locked=enters=exits=0;
        for(k=0;k<9;++k)port[k]=before[k]=random_word();
        next_status=statuses[j];
        assert(hyperrig_mini_g_audio_pre_current_clock()==next_status);
        assert(count==5 && memcmp(order,"DOHhV",5)==0 && !locked);
    }
    puts("{\"PC5_before_original_pre_cases\":640,\"foreign_GPIO_preserved\":true,\"host_helpers_simulated\":true}");
    return 0;
}
