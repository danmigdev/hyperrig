# The flash driver of the loader

`nor.c` reads, erases and programs the flash chip for [the loader](../mini_stage/README.md). It knows
eight opcodes (FF 9F 03 05 35 06 20 02): no status write or unlock, no block or chip erase, and no clock,
timer, reset or efuse access. The start-up compares reads by DMA with reads byte by byte at three places,
and reads byte by byte if they differ. It was written for a plugin of the ROM's download mode (HYF1),
which is not used any more; `fast.h` is that plugin's header, of which the driver uses its own part.
[THIRD_PARTY.md](THIRD_PARTY.md) says where the DMA sequence comes from.
