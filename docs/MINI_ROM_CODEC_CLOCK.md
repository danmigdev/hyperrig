# Clock ROM osservato e diagnostico HYC3

Il 15 novembre 2026 HYC2 ha restituito uno snapshot stabile del TANK MINI,
ma ha correttamente rifiutato il profilo clock con `gate=4`. La sessione non
ha eseguito FC69 né toccato i GPIO; il ritorno al firmware stock e i preset
invariati sono attestati nel resoconto hardware separato. Il record originale
ha SHA256 `d5494ce5fe320b951f1470d0e896ccce214a6dce1fd48c2f138635c4bd225083`.
HYC2, il suo manifest e i suoi binari restano immutabili.

[audit_mini_rom_clock.py](../tools/audit_mini_rom_clock.py) rilegge quel
record, ne verifica il contratto HYC2 e interpreta offline i byte MINI
originali `0x02002D76..0x02002EC8`. Dopo 67 istruzioni il decoder stock
restituisce **48 MHz nominali per SYS, HSB e LSB**, con SDRAM disattivata.
Il frammento ha SHA256
`de019096c01b9801c0e23aea0ffdfe5d993bd25028277fd9a1d63590f896a9d3`.

Il risultato è corroborato dal `clk_early_init` estratto dal `clock.c.o`
del `cpu.a` SDK fissato e dalla [SPEC m-bootloader, §10.4](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#104-clock-dma-and-performance).
Il ramo `CLK_CON2[3:0]=0` usa 192 MHz nominali; i campi divisori selezionano
1 e 4. `SYS_DIV=0` lascia HSB e LSB senza divisioni ulteriori.
L'header SDK attivo identifica `CLK_CON0[8:6]=7` come PLL e `[3:2]=0`
come ingresso normale. Non viene eseguito il codice di accelerazione a
96 MHz descritto nella SPEC e non si modifica il clock USB.

| Registro | Indirizzo | Valore osservato |
|---|---:|---:|
| SYS_DIV | `0x10008` | `0x00000000` |
| CLK_CON0 | `0x1000C` | `0x000001C1` |
| CLK_CON1 | `0x10010` | `0x00010000` |
| CLK_CON2 | `0x10014` | `0x00000080` |
| PLL_CON0 | `0x119A0` | `0x0940022B` |
| PLL_CON1 | `0x119A4` | `0x3F5030EE` |
| PLL2_CON0 | `0x119A8` | `0x00000000` |
| PLL2_CON1 | `0x119AC` | `0x00000000` |
| HUSB_CON0 | `0x16A00` | `0x00000000` |
| HUSB_CON2 | `0x16A08` | `0x00000000` |
| SFC_CON | `0x40200` | `0x01580034` |
| SFC_BAUD | `0x40204` | `0x00000001` |

La configurazione del PLL primario differisce da quella preparata dal
boot applicativo. I campi divisore 12 e moltiplicatore 240 sono compatibili
con 24 MHz / 12 × 240 = 480 MHz; questa compatibilità non è una misura né
la base del nuovo gate. La scorciatoia 24/40 MHz del decoder SDK non viene
estesa al profilo ROM: produce anche un valore aritmetico di 40 MHz per il
PLL secondario disattivato, che **non rappresenta un clock abilitato**.

Il report [mini-rom-clock.json](../research/mini-rom-clock.json) conserva
il record completo, gli hash delle fonti e l'esito dell'interpretazione.
Il record incluso consente di riprodurre l'audit anche senza la cartella
privata `analysis/hardware`; servono le dipendenze SDK/stock già dichiarate
nel repository e il compilatore vendor per rendere leggibile il bitcode.

```sh
python -B tools/audit_mini_rom_clock.py
```

HYC3 è un payload separato in
[rom_codec_rom](../firmware/mini/rom_codec_rom/rom_codec.h). Accetta soltanto
la corrispondenza esatta dei dodici valori sopra; una differenza lascia il
diagnostico alla lettura dello snapshot, senza setup pin. I cinque valori
aggiuntivi cache/SDRAM/PSRAM vengono registrati, ma non sono il criterio di
riconoscimento del clock. `gate=4` significa profilo ROM non riconosciuto.

Il protocollo distinto usa `FC6B` per snapshot, `FC6C` per una lettura
esplicitamente associata alla sequenza dello snapshot e `FD6D` per il
record da 512 byte. Magic `HYC3`, versione 3; gli offset del record sono
documentati nell'header. Sono richiesti CRC, build tag, slot, sequenza e
coerenza dei contatori. Ogni lettura consuma l'autorizzazione dello snapshot,
anche su errore. Non viene eseguito alcun retry automatico.

Il setup PC5/PA9 e il ripristino dei bit PA1/PA2/PA9 e PC5, inclusi HD/HD0,
mantengono le operazioni HYC2 già documentate. Il gate nominale permette la
scala stock `48 MHz / 4 MHz = 12` iterazioni per unità, quindi 36 o 72
iterazioni per le attese da 3 o 6 unità. Il ciclo di assestamento resta
100000 iterazioni. Nessuna di queste cifre misura il tempo degli edge reali,
l'overhead delle callback, gli interrupt o il delay RTOS stock.

```sh
python -B tools/build_mini_rom_codec_rom.py
```

Il builder esegue test host ASan/UBSan, verifica il record e produce due
ELF/payload negli slot RAM da 32 KiB. Il manifest
[mini-rom-codec-rom.json](../research/mini-rom-codec-rom.json) attesta solo
queste verifiche offline. Lo stack privato e le guardie controllano il
percorso sincrono; lo stack ereditato dagli interrupt ROM non è qualificato
dal bound statico. Le callback USB ROM vengono chiamate dopo il ritorno
dallo stack privato. Nessun accesso NOR, modifica PLL/USB o scrittura dati
codec è incluso. Un eventuale ACK non prova da solo identità esclusiva del
codec, 48 kHz audio, mute o avvio del firmware HyperRig completo.

## Esito fisico HYC3

La prova del 15 novembre 2026 è conclusa e conservata separatamente in
[mini-codec-rom-hardware.json](../research/mini-codec-rom-hardware.json).
Upload e rilettura dei 5392 byte sono riusciti. La snapshot ha accettato il
profilo ROM nominale da 48 MHz, con scala 12, e la prima lettura esplicita
ha applicato il setup PC5/PA9 previsto.

Il primo byte `0x36` ha ricevuto NACK: zero byte dati e zero ACK, nessun
valore codec ottenuto. Le altre nove letture sono state omesse senza retry.
I campi GPIO toccati sono stati ripristinati, i clock sono rimasti uguali
e lo stack privato ha mostrato 576 byte modificati, con guard integre.
Il ritorno a MINI_009 e i preset invariati sono verificati.

Il diagnostico ROM non esegue il rilascio dei latch P33 dello startup
SPL/applicativo. Non identifica perciò la causa elettrica del NACK e non
sostituisce l'avvio del port completo. Il manifest offline rimane immutato.
