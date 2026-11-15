# Review del primo flash e avvio MINI

Review offline del 15 novembre 2026, senza comandi al dispositivo, cambi al
piano, alla guardia o agli artefatti congelati. La candidata esaminata è
`build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin`, 516096 byte,
SHA256 `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
Il manifest `firmware-manifest.json` ha SHA256
`f119ab571a6cb04c8ca72513b5d18d614e079e756d209ce5794fbaeb4fe77d12`.
Questo documento non attesta un'installazione o un recupero dall'app già
installata.

Il rilievo principale riguarda un'interruzione durante la sostituzione.
[plan_mini_install.py](../tools/plan_mini_install.py) ordina i settori
modificati da `0x5000` in avanti e lascia `0x4000` per ultimo. Lo SPL verifica
gli header, non il CRC dell'intero corpo applicativo: a `0x01C033E2` il CRC
copre 30 byte, confrontati con i due byte iniziali dell'header. Prima della
scrittura finale rimangono quindi header e entry MINI validi insieme a un
corpo parzialmente G. Un'interruzione può far eseguire codice misto senza
raggiungere la nuova guardia. La dicitura `power_loss_atomicity_proven=false`
è corretta; header-sector-last da solo non elimina questa finestra.

Nel settore finale, l'ordine crescente delle pagine pubblicherebbe inoltre
l'header a `0x4000` prima dell'entry a `0x4120` e dell'hook a `0x418A`.
La decisione per il nuovo installer operativo è programmare prima
`0x4100..0x4F00` e **la pagina `0x4000` per ultima**, con verifica di ogni
pagina e del settore. Lo staging/echo precedente all'erase può usare
`0x4100`. Il core HYW corrente accetta pagine allineate non ancora presenti
nella bitmap e quindi consente questo ordine. La modifica riduce la finestra
finale, ma non risolve la precedente finestra con header vecchio. Alla data
di questa review il nuovo installer deve ancora essere revisionato: non si
attribuisce questa policy al piano congelato.

Non viene aggiunta automaticamente l'invalidazione iniziale. L'installer
UltraRig originale `_write_plan`, nel disassemblato recuperato da riga 29190,
sposta l'header alla fine e scrive prima un settore FF; la chiamata è visibile
ai bytecode offset434..460. È una policy reale dell'originale, ma il suo
fallback sul TANK-G non dimostra il fallback fisico del MINI.

Lo SPL MINI esaminato, SHA256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`, azzera
`app_base` a `0x01C04D68` quando fallisce l'header. Il percorso di scansione
a `0x01C04E26` può selezionare la richiesta OTA a `0xBCF00` del backup
fisico e il suo `LOADER.BIN` a `0xB7000`. Dopo decompressione e CRC, la
chiamata indiretta a `0x01C04F64` entra nel loader a `0x01C0A800`.
Solo se il loader ritorna o fallisce, e `app_base` resta zero, il ramo
`0x01C04F94..4F98` porta al marker/reset ROM a `0x01C0529A`.
Non equivale a «header invalido implica immediatamente disco ROM».

È stata decodificata esclusivamente in memoria la copia locale
`analysis/tank-mini/ota.bin` (SHA256
`9c62bbdfd55f6527a3cffe43abc16c621d0900a8ff47685240abb1ee596eb66e`).
Il payload installato nel backup coincide già con quello del pacchetto, come
verificato da [audit_mini_boot_contract.py](../tools/audit_mini_boot_contract.py).
L'header interno identifica `usb_hid_ota.bin`. La decodifica segue i blocchi
LZ4 con dizionario precedente, come
[core_lz4_block/core_updater_decode](../upstream/m-bootloader/src/core.c):

| Blocco | Byte compressi | Byte prodotti |
|---|---:|---:|
| 1 | 3209 | 4096 |
| 2 | 3550 | 4096 |
| 3 | 3568 | 4096 |
| 4 | 3613 | 4096 |
| 5 | 3464 | 4096 |
| 6 | 2442 | 2844 |

Totale 23324 byte, CRC16 `0x6A00` uguale all'header, SHA256 decompresso
`4758c7452f8527af9d479db9cc766a6c07d592e255633b593363f6ea1de73c97`.
Questo verifica il contenuto e il ramo di caricamento, senza eseguire
l'updater. Nessuna prova esistente mostra l'enumerazione OTA dopo un header
MINI invalidato, un comando OTA→ROM o un ripristino automatico dello stock
senza host. Nel loader sono presenti riferimenti a `flash.bin` e
`uboot.boot`: non va trattato come un writer limitato alla sola app.
Il protocollo di ripresa HYW/ROM non può essere dichiarato applicabile a
quel dispositivo OTA. Perciò l'invalidazione iniziale rimane esclusa e
l'interruzione della scrittura resta un limite dichiarato.

I controlli indipendenti sulla candidata hanno confrontato i byte decodificati
con G e con il payload della guardia, senza richiamare il builder:

| Regione | Risultato |
|---|---|
| Entry G `0x02000120..124` | `14948000`, identica all'originale |
| Hook `0x0200018A..196` | `c3ea1db90000000000000000`, salto alla guardia |
| Guard v2 `0x020773C8..0x020774F2` | 298 byte esatti, SHA256 `fed49e2b7df48f652b791d3bf52c851fae9d02ce3b21363996cd28e75ac99291` |
| Rilascio P33 G `0x02000EE0..0x02000FB6` | Identico all'originale |
| Caller P33 `0x020011C2..0x020011D2` | Identico, include chiamata a `0x02000EE0` |
| Writer P33 RAM, LMA `0x0205768C..0x020576CA` | Identico all'originale |

Il manifest della guardia di questa candidata ha SHA256
`7477a0a10ae9ad7c5459432535873eb05105dc9b1065c76a1eb6f1c7cd4ca729`.
Lo SPL conservato azzera i latch P33 D0..DF/AD..AF prima dell'handover.
Il prefix v2 imposta DIR per PA10/PA0/PA3 prima del callable, conserva il
contesto G sul ramo normale e non dipende da una direzione input ereditata.
Non sono emersi nuovi difetti di bounds/ABI della guardia. La prova HYK1
fisica già registrata copre released→held→released e marker/reset→nuova ROM;
non prova il prefix XIP, il mux al cold boot o l'esecuzione G completa.

La review del writer congelato non ha trovato un percorso NOR fuori
`[0x4000,0x82000)`: `hyw_range` verifica prima gli estremi e poi
`length <= end-address`; erase4K e program256 ricontrollano intervallo e
allineamento nel driver PIO prima di emettere l'indirizzo a24bit. Il core
limita ogni pagina al settore armato e alla bitmap. SPL/config, VM/OTA,
BTIF, USR e key_mac restano esclusi. Il gate target è ancora zero;
questa conclusione non qualifica una futura build abilitata o il suo client.

Il rilievo iniziale sul rollback era che il piano corrente accetta come
preimage il backup stock e come destinazione l'app `tankm`. Dopo una scrittura
completa o parziale quei vincoli non descrivono il verso inverso. Serve un
percorso di ripristino esplicito e separato che acquisisca la preimage corrente
in ROM, la conservi e riscriva i byte stock entro la medesima allowlist.
Non si richiede un rollback automatico su errore; occorre poter eseguire un
ripristino deliberato dopo il ritorno in ROM. La guardia e il solo file di
rollback non costituiscono già tale procedura. Il rilievo è ora coperto da
[restore_mini_stock.py](../tools/restore_mini_stock.py) e da 16 test: la factory
separata accetta anche un'app incompleta, fissa i byte della lettura corrente,
verifica SPL/key_mac e prepara il verso stock senza scrivere le regioni
esterne. API e limiti sono in
[MINI_STOCK_RESTORATION.md](MINI_STOCK_RESTORATION.md).

Sorgenti letti in questa review:

| File | SHA256 |
|---|---|
| `tools/plan_mini_install.py` | `1c99f931789e8ef79feef43ab50472af22f65eb8468f6884aac16c3e7a715a64` |
| `tools/build_mini_app_writer.py` | `39941618458365ca9c151a33e468a8b83e531f700fd7bfb3aedb581dd61c2ec2` |
| `firmware/mini/app_writer/writer.c` | `f43e42b4d0aec8b354ac7f02a1067b22d3e978bd81d4412a9471f01e18086de2` |
| `firmware/mini/app_writer/nor_pio.c` | `a31813c4e71d232b62f0c29f0bd40c4fc923c40f8c672faa7d205f0ee8ec4dab` |

Le verifiche appartengono a fasi diverse:

| Fase | Evidenza richiesta o ottenibile |
|---|---|
| Prima della scrittura | Candidata e sorgenti fissati; backup completo della stessa unità; lettura fresca/preimage; JEDEC/status; writer e host con limiti/rifiuto dei retry ambigui; staging/echo RAM e stack; slot di ritorno distinto e noto non live. HYK1 ha già qualificato tasti e marker/reset. |
| Durante la scrittura | Esito di erase/program, attese WIP, readback esatto delle pagine/settori, area completa uguale alla candidata e regioni esterne preservate. Un errore non autorizza reset dell'app parziale o retry automatico. |
| Dopo l'installazione verificata | Primo reset con i tre tasti tenuti prima del reset: osservare nuova enumerazione ROM e INQUIRY, quindi qualifica del prefix XIP. Solo dopo rilascio e nuovo avvio normale: PONG `tankm_fw`, stabilità, audio, app e preset. |

L'esecuzione della guardia XIP e il recupero da un hang dell'app installata
sono verifiche successive all'installazione; richiederle come prova hardware
già conclusa prima del primo flash sarebbe circolare. Il primo avvio con
tutti i footswitch tenuti permette di provare il ramo di recupero prima di
avviare RTOS, driver e DSP G. Non protegge header/entry/guard danneggiati né
garantisce il successo di un'installazione interrotta. In caso di prova
incompleta, i relativi flag hardware restano falsi.

La successiva review dell'installer operativo
`tools/install_mini_app.py`, SHA256
`4a85b608c052a870a322d1bd57653b167b33223f5a2a65338cbc9b5aa031f22f`,
non ha individuato altri blocker in token/sequenze, staging/echo, limiti,
preimage/readback o journal prima del comando. Il manifest operativo fissato
è `214cbfc3c14d4bc2eff83a9e88ae8b9f9232c211c685e81af9059b182f05031c`.
La derivazione target abilita il gate e aumenta solo il ritardo di polling
WIP da 256 a 768 iterazioni; il writer gate0 rimane immutato. I limiti di polling
sono finiti, ma non sono una qualifica temporale fisica: il timeout host resta
terminale e ambiguo, senza retry o reset automatico.

Anche i runner root `analysis/hardware/run_mini_first_install.py` e
`run_mini_first_boot.py` sono stati letti, senza eseguirli. La sequenza
readerB→writerA→readerB conserva la distinzione fra slot attivo e salto
ambiguo; confronta 1 MiB prima e dopo e lascia ROM attiva. I reset held/released
sono separati, con nuova arrival e INQUIRY per held e osservazione CDC per
released. Quest'ultima osservazione non è ancora un handshake: l'installer
UltraRig originale invia PING appena compare CDC per confermare il boot.
PING/INFO e successiva stabilità devono quindi seguire prontamente
l'enumerazione. Reset software via SPL e vero power-cycle rimangono prove
distinte.
