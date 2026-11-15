/* Include a generated copy of the frozen mock suite. Its output paths are
 * redirected by the builder; the original gate-zero fixtures stay untouched. */
#define main frozen_mock_main
#include "test_writer_reference.c"
#undef main

int main(void)
{
    unsigned i,j,page;uint32_t address;
    if(frozen_mock_main())return 1;
    assert(hyperrig_writer_mutations_enabled==1);
    fresh();init();
    for(j=0;j<2;++j){
        address=j?0x4000:0x5000;arm(address);
        page=j?1:0;stage(address+page*256,page);echo(address+page*256,page);
        assert(f.wren==17*j&&f.erase==j&&f.program==16*j);
        action(0xfc7b,address);assert(!error());
        for(i=0;i<16;++i){
            page=j?(i+1)%16:i;
            if(i){stage(address+page*256,page);echo(address+page*256,page);}
            if(j)for(unsigned b=0;b<256;++b)assert(flash[0x4000+b]==255);
            action(0xfc7d,address+page*256);assert(!error());
            if(j&&i<15)for(unsigned b=0;b<256;++b)assert(flash[0x4000+b]==255);
        }
        action(0xfc80,address);assert(!error()&&!token);
        assert(!memcmp(flash+address,desired,4096));preserved();
    }
    assert(f.wren==34&&f.erase==2&&f.program==32);
    puts("{\"cases\":2,\"multi_sector_without_reload\":true,\"header_page_programmed_last\":true,\"hardware_IO\":false}");
    return 0;
}
