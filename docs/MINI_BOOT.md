# Avvio e linker HyperRig per TANK MINI

Sono disponibili **tre ELF di verifica per pi32v2**, con entry, copia RAM,
azzeramento BSS e stack dedicati. Il secondo collega anche il motore capture
HyperRig, la capture A2 originale e l'adattatore audio. Il terzo aggiunge
platform, codec e worker, con un'autoverifica RAM del percorso audio.
Non sono stati avviati sul pedale e non sono pacchetti installabili.
`research/mini-boot.json` mantiene esplicitamente
`boot_validated_on_device=false` e `flashable=false`.

## Contratto osservato nel firmware stock

Campione: `TANK MINI_009`, FWSC SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
La build ricontrolla SHA, CRC FWSC/JLFS e uguaglianza di `app.bin` decodificato.
Il report conserva indirizzi e hash dei frammenti originali usati come prova.

| Elemento | Evidenza stock |
|---|---|
| Entry applicazione | CPU `0x02000120`, primi byte di `app.bin` |
| SP iniziale CPU0 | `0x01C1899C` a `0x02000124` |
| SSP iniziale CPU0 | `0x01C1999C` a `0x0200012A` |
| BSS azzerata | `[0x01C0E018, 0x01C1F414)`, loop `0x02000136` |
| Copia RAM | flash `0x0206ED20` → RAM `0x01C00000`, `0xE018` byte |
| Heap iniziale | `0x01C1F420`, caricamento a `0x02040C52` |
| Limite heap | `0x01C7FD30`, confronto a `0x02040C5A` |
| Informazioni di boot | campi salvati da `0x020001E6` nella regione `0x01C7FD50` |
| Tabella handler IRQ | `0x01C7FE00`, scrittura a `0x02001786` |
| Controller IRQ CPU0/CPU1 | `0x01EEF100` / `0x01EEF300` |
| Slot avvio CPU1 | `0x01C7FFF8`, scritto da `0x0204462C` |
| Entry stock CPU1 | `0x020001B8`: USP `0x01C19C9C`, SP `0x01C1AC9C`, RETI `0x01C020AA`, `rti` |

Sono indirizzi ricavati dal campione software. Non costituiscono una misura
della RAM libera o della geometria fisica dell'esemplare collegato.

L'area applicativa fisica MINI è `[0x4000, 0x82000)` e corrisponde al range
CPU flash `[0x02000000, 0x0207E000)`. L'entry dista `0x120` dall'inizio
dell'area. I primi `0x120` byte appartengono al contenitore JLFS, non al codice
dell'ELF. VM, BTIF e USR restano fuori dal contratto del linker applicativo.

Prima di azzerare la RAM, lo stock conserva dal descrittore in `r0`:
otto byte da `r0+4` a contesto+16, il word a `*(r0)+8` a contesto+24,
il byte a `*(r0)+13` a contesto+0, quattro byte da `r0+12` a contesto+28,
otto byte da `r0+16` a contesto+32. Il nuovo startup conserva gli stessi
campi, senza attribuire significati non dimostrati. Per prove con debugger
ammette anche `r0=0`, saltando la lettura del descrittore.

## Layout nuovo e controlli

`firmware/mini/boot/mini.ld` usa RAM `[0x01C00000, 0x01C7FD30)` e lascia
intatta la regione alta `[0x01C7FD30, 0x01C80000)` destinata a boot/IRQ.
Non incorpora puntatori, task, heap o tabelle callback dell'applicazione stock.

- `.text` parte esattamente da `0x02000120`.
- `.ram` contiene dati inizializzati e eventuale codice RAM, con LMA flash
  esplicito e simboli `__ram_load_start/end`, `__ram_start/end`.
- `.bss` è distinta da `.noinit`; le sezioni `.dma` e `.dma32` sono raccolte
  con allineamento 32. Questo allineamento non dimostra coerenza DMA/cache.
- Stack normale `[0x01C7CD30, 0x01C7ED30)` da 8 KiB e SSP
  `[0x01C7ED30, 0x01C7FD30)` da 4 KiB sono scelte HyperRig. Non derivano
  dalla misura del fabbisogno reale di interrupt o motore.
- Assert del linker impediscono sovrapposizione con stack/riserva alta e
  superamento del limite flash MINI.

Il linker JieLi produceva per default `p_align=0x500`, valore non conforme
al vincolo ELF di potenza di due. La build imposta esplicitamente
`-z max-page-size=0x20 -z common-page-size=0x20`: offset e VMA dei segmenti
ora rispettano l'allineamento e passano il validatore indipendente
`tools/check_mini_image.py`. I segmenti BSS/stack con `p_filesz=0` non sono
interpretati come dati flash.

`startup.S` tiene disabilitati gli IRQ, imposta i due stack, salva il contesto
di boot, azzera BSS, copia `.ram`, esegue `csync` e passa alla funzione C.
I loop software gestiscono anche sezioni di lunghezza zero senza dipendere
dalla semantica di `REP 0`.

La simulazione limitata decodifica **le istruzioni dell'ELF appena collegato**,
inizializza la RAM con un pattern e confronta tutta l'area RAM finale con il
contratto ELF. Controlla copia, zero BSS, conservazione dei campi di boot,
zone non interessate, SP, SSP e IRQ disabilitati. Prova sia descrittore valido
sia descrittore nullo. Si ferma prima dell'entry C: non esegue né simula
boot ROM, periferiche o motore DSP target.

## Probe C e motore capture

Il probe minimo scrive `hyperrig_mini_probe` in `.noinit`: magic, fase,
indirizzo del contesto e risultati dei controlli su un word inizializzato e
un word BSS. Senza applicazione aggiuntiva riporta stato `-100` e resta in
un ciclo con IRQ disabilitati. Il marker è destinato a un eventuale debugger;
non è una segnalazione visibile su LED, USB o Bluetooth.

Con `--dsp`, vengono aggiunti il motore ricostruito, la capture A2, il driver audio e
implementazioni locali freestanding di `memcpy`/`memset`. Non restano simboli
non risolti. Il probe riserva 16 KiB per il modello e 192 KiB per l'arena
runtime e controlla le dimensioni richieste prima dell'inizializzazione.
Queste sono capacità riservate per la prova, non il fabbisogno minimo misurato.

Il self-test è preparato per elaborare 64 zeri dopo reset e confrontare
il CRC32 little-endian dell'uscita con `f10b5e4c`. Il risultato atteso deriva
dall'interpretazione dei kernel originali del G, non dal C HyperRig. Se il
codice verrà eseguito, il mailbox conserverà CRC, frame elaborati e stato;
`-104` indicherebbe un confronto fallito.

Poi il probe azzera lo stato del motore e chiama
`hyperrig_mini_audio_process_half` su due array RAM fittizi da 1024 byte,
allineati a 32 e raccolti in `.dma32`. La callback esegue il motore con
ingresso Q30 e uscita Q31. Verifica il CRC `f0a44a06` sui 128 slot TX della
prima metà, in formato low24 duplicato nei due canali, e controlla che la
seconda metà conservi il pattern iniziale. Non chiama `prepare`, `start`,
codec, IRQ o MMIO. Il mailbox aggiunge `audio_status`, `audio_frames` e
`tx_checksum`; `-105` segnala CRC TX diverso, `-106` una scrittura nell'altra
metà, `-107` prova audio non raggiunta.

La stessa `hyperrig_mini_application_probe` è stata **eseguita sull'host Linux
sotto ASan/UBSan** tramite `probe_host.c`, con capture, motore e adattatore:
stato zero, 64 frame per ciascuna prova e i due CRC attesi. L'harness host
sostituisce soltanto la definizione del mailbox ed esclude il main di boot
e lo startup pi32v2. La simulazione target si ferma prima dell'entry C;
**il self-test C target non è stato eseguito sul MINI**.

Nella build verificata, il probe DSP comprende 11.984 byte caricati dalla
flash (capture inclusa), 216.768 byte BSS, 52 byte `.noinit`, quattro byte di
dati inizializzati e 12 KiB di stack riservati. Restano spazi liberi nel layout,
ma latenza, stack effettivo e comportamento del target non sono misurati.

## Probe integrato del worker audio

`--bringup` aggiunge un terzo ELF, `hyperrig-mini-bringup-probe.elf`, che collega
runtime IRQ/worker, platform e codec. L'autoverifica usa lo stesso ingresso
zero e gli stessi CRC del probe DSP, facendo passare la prova audio attraverso
`hyperrig_mini_runtime_ready` e `hyperrig_mini_runtime_work`. Il motore A2 viene
eseguito nel worker; l'evento simulato non entra nel wrapper hardware IRQ11.

`runtime_probe.c` fornisce callback controllate per esclusione, possesso dei
buffer e sincronizzazione di **array RAM privati senza periferica DMA**.
Verifica un evento, un blocco completato, due transazioni RX/TX, bilanciamento
delle callback e assenza di lavoro pendente. Quelle callback non sono una
soluzione per la coerenza del DMA reale e non possono essere usate per abilitarlo.

Anche questa applicazione C viene eseguita sull'host sotto ASan/UBSan. Il suo
CRC TX atteso resta `f0a44a06`; il risultato e l'hash dell'eseguibile host sono
nel report. Gli oggetti platform e codec vengono collegati, ma nessuna loro
operazione MMIO viene chiamata. PLL, watchdog, codec e percorso analogico non
sono inizializzati dal probe.

La build rifiuta sorgenti o oggetti diversi dagli hash dei report dei
componenti, per evitare una prova host aggiornata accanto a codice target
vecchio. Le unità che attraversano il confine flash/RAM usano
`-mllvm -pi32v2-large-program`: la chiamata ordinaria della toolchain non
copre sempre la distanza fra `0x0200....` e `0x01C0....`. Le chiamate estese
`call.xl` risolvono il link senza spostare arbitrariamente RAM o stack.

Il nuovo ELF contiene funzioni `.ramtext`, copiate dallo startup. La simulazione
verifica i byte copiati, ma non dimostra la visibilità delle nuove istruzioni
alle cache del processore. L'handover cache/MMU e l'esecuzione dalla RAM devono
essere verificati prima di considerare questo programma avviabile sul MINI.

## IRQ e cache: cosa è ricostruito

`irq.c` espone registrazione e rimozione dei soli IRQ fisici 0–65. Il codice
deriva da `0x02001756` e dalla rimozione a `0x020148B4`: handler nella tabella
alta, word controller `index>>3`, nibble `(index&7)*4`, valore
`(priority<<1)|1`. Preserva ICFG al termine, elimina eventuali route precedenti
su entrambe le CPU e richiede serializzazione esterna fra CPU. Il probe non
chiama questi hook e non abilita interrupt. Il numero 126 non viene esposto:
il corrispondente word di tabella coincide con lo slot osservato di avvio CPU1.

Il [linker SFC del SDK AC79 fissato nel riferimento](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/cpu/wl82/sdk_ld_sfc.c)
conferma la separazione RAM/boot-info e l'uso di vie cache come RAM aggiuntiva.
In particolare `0x01F28000` è `.cache_ram_data`, non la tabella IRQ. Il reset
stock configura sette vie D-cache libere e copia lì 32 byte che contengono
callback SDK. HyperRig non usa quella regione e non ricopia tali puntatori.
Il [contratto IRQ del SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/hwi.h)
conferma ALNK all'indice 11; gli handler hardware richiedono l'ABI interrupt
del compilatore pi32v2, non una normale funzione C.

Restano da verificare l'handover del boot ROM, stato cache/MMU, watchdog,
clock, driver GPIO/codec/mute, coerenza DMA, gestione IRQ effettiva e
installazione/ripristino sul singolo esemplare. Il nuovo startup non clona il
scheduler o l'avvio del secondo core stock e non dichiara di sostituirli.

## Riproduzione

```powershell
python tools/build_native.py
python tools/verify_mini_audio.py
python tools/build_mini_boot.py --dsp
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf --elf build/mini-boot/hyperrig-mini-dsp-link-probe.elf
```

Per il terzo probe:

```powershell
python tools/verify_mini_platform.py
python tools/verify_mini_codec.py
python tools/verify_mini_runtime.py
python tools/build_mini_boot.py --bringup
```

Servono WSL Ubuntu, la toolchain JieLi già fissata dal bootstrap, firmware
decodificati e tabella ISA locale. Gli artefatti sono in `build/mini-boot/`;
il report versionato è [mini-boot.json](../research/mini-boot.json).
I comandi non aprono trasporti verso il pedale e non generano file FWSC o
immagini pronte per il flashing.
