# Platform HyperRig per TANK MINI

Sono disponibili driver ricostruiti per il watchdog P33, operazioni cache su
linee intere e lettura/decodifica dello stato clock. Compilano per pi32v2 e
sono verificati sull'host. **Non inizializzano PLL, SFC o MMU e non dimostrano
un avvio sul MINI.** Non impostano flag di readiness audio.

I sorgenti sono in `firmware/mini/platform/`; `tools/verify_mini_platform.py`
genera l'oggetto `build/mini-platform/hyperrig_mini_platform.pi32v2.o` e il
report [mini-platform.json](../research/mini-platform.json).

## Evidenza e confini

Il campione è il firmware originale `TANK MINI_009`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
La verifica riapre il FWSC, verifica i CRC del contenitore e confronta
`app.bin` estratto con la copia usata per il disassemblaggio.

| Funzione osservata | Intervallo CPU, fine esclusa |
|---|---|
| Feed watchdog e OR del controllo | `0x02000974..0x0200098A` |
| Scrittura controllo watchdog | `0x02002B88..0x02002B96` |
| Sequenza watchdog iniziale | `0x02002D42..0x02002D6C` |
| Trasmissione di un byte P33 | `0x01C00FC8..0x01C00FE2` |
| Scrittura P33 | `0x01C0104E..0x01C0108C` |
| OR atomico nel dominio P33 | `0x01C010B4..0x01C010FE` |
| Flush/invalidate cache per intervallo | `0x01C00D80..0x01C00DB2` |
| Manutenzione globale cache, non portata | `0x01C00DB2..0x01C00E8C` |
| Configurazione delle vie cache al reset | `0x01C00E8C..0x01C00F9C` |
| Lettura/decodifica clock ereditati | `0x02002D76..0x02002EC8` |
| Cambio clock protetto tramite SFC, in RAM | `0x01C03352..0x01C033EC` |

Il report conserva gli hash dei frammenti. Il codice nuovo non chiama
indirizzi di funzione stock né accede a lock/globali del suo scheduler.

Gli header [P33](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/p33.h),
[watchdog](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/wdt.h)
e [cache](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/cache.h)
del riferimento SDK AC79 fissano nomi, indirizzi P33 e linea cache da 32 byte.
Le sequenze effettive provengono dai byte MINI. Il riferimento indipendente
[m-bootloader, SPEC §§2–3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md)
corrobora diversi registri AC791N; le sue prove FM1/SMK37 non sono prove sul MINI.

## Watchdog: feed e configurazione separati

Il bridge P33 usa registri word `SPI_CON=0x13E08`, `SPI_DAT=0x13E0C`.
Con CS attivo per tre byte, ogni byte viene scritto in DAT, poi viene
impostato il bit4 del controllo; segue `csync`, attesa del bit1 a zero e
lettura DAT. Per gli indirizzi P33 usati qui il bit8 del controllo resta zero.
Scrittura e OR usano rispettivamente byte comando `0x00` e `0x20`.

`hyperrig_mini_watchdog_feed` invia `20 80 40`: imposta il bit6 del registro
P33 `0x80`, come lo stock. Conserva timeout e abilitazione esistenti. Non
abilita un watchdog spento e non garantisce una durata del self-test DSP.

`hyperrig_mini_watchdog_init_stock_4s` riproduce nell'ordine:

| Operazione | Registro P33 | Dato |
|---|---:|---:|
| write | `0x80` | `0x00` |
| write | `0x80` | `0x0C` |
| OR | `0x80` | `0x20` |
| OR / feed | `0x80` | `0x40` |
| OR | `0x17` | `0x40` |
| OR / enable | `0x80` | `0x10` |

L'header SDK chiama `0x0C` **WDT_4S**; non abbiamo misurato il termine sul
MINI. P33 `0x17` è `P3_VLD_KEEP`, il cui bit6 è dichiarato `WDT_EXPT_EN`.
L'API si ferma al primo errore senza proseguire la sequenza.

Il chiamante deve possedere il bridge, serializzare IRQ/altra CPU e fornire
un limite di polling non nullo. CS già attivo, selezione RTC attiva o bridge
busy producono `-3` senza scritture. Il byte driver MINI eredita i bit di modo
del bridge; il riferimento AC791N indipendente usa bit3:2=`11`. L'API rifiuta
un altro modo (`-4`) senza provare a configurarlo. Questo controllo è una
precondizione conservativa aggiunta, non una nuova istruzione trovata nel MINI.

Un timeout restituisce `-2`, rilascia CS e lascia **incerto** il completamento
del comando: non autorizza retry, DMA o continuazione come se il feed fosse
riuscito. Il limite conta letture del registro, non microsecondi. Il ciclo
di feed e il suo rapporto con il tempo massimo del DSP restano da progettare
e misurare sul target. Nel probe una prova watchdog deve essere un'opzione
esplicita; non appartiene al self-test offline predefinito.

## Clock: conservare l'accesso alla flash

`hyperrig_mini_clock_read_snapshot` legge 17 word: divisori e selettori,
PLL principali/secondari, HUSB, SFC, cache e controlli SDRAM/PSRAM. Non scrive
registri. Il chiamante deve escludere cambi clock durante la lettura; non è
una cattura hardware atomica. Il registro SFC BAUD viene letto dallo stock,
anche se l'header SDK lo etichetta come write-only.

`hyperrig_mini_clock_decode` replica l'aritmetica stock supportata:

- Oscillatore nominale 40 MHz se i bit27:26 di `0x119A0` valgono 2,
  altrimenti 24 MHz.
- PLL secondario: divisione per `(DIVN+2)` prima della moltiplicazione per
  `(FBD+2)`, mantenendo la semantica unsigned32 del processore.
- Selettori sistema 0–4: 192, 137, 320, 480 o 107 MHz, divisi tramite le
  tabelle stock `[1,3,5,7]` e `[1,2,4,8]`.
- Selettori 5–7: derivazione dal PLL secondario; 8–9: derivazione dal
  moltiplicatore HUSB. I selettori 10–15 sono rifiutati: non usiamo il
  fallback nominale a 480 MHz presente nello stock.
- HSB divide sys per `SYS_DIV[17:16]+1`; LSB divide HSB per
  `SYS_DIV[10:8]+1`; SFC divide HSB per `BAUD+1`.

I campi `sys_hz`, `hsb_hz`, `lsb_hz` corrispondono ai globali stock
`0x01C1E32C`, `0x01C1E338`, `0x01C1E334`. Sono **valori nominali calcolati**,
non misure. `main_selector` riporta separatamente il percorso CPU selezionato
in `CLK_CON0`: il calcolo stock non dimostra che la sorgente calcolata stia
effettivamente alimentando la CPU. Non usiamo quei valori per attestare
deadline, ritardi del codec o lock PLL.

La routine stock di cambio clock esegue da RAM: aspetta cache idle
(`0x01EEE008`, bit14), aspetta SFC non busy (`0x40200`, bit31), disabilita
SFC bit0, applica clock/divisori e ritardi, poi ripristina SFC. Anche il campo
di temporizzazione SFC viene ricalcolato. Trasferire solo le scritture clock
in codice eseguito dalla flash può togliere accesso alle istruzioni.
**Questo cambio non è portato né invocato.** Il platform conserva SFC,
PLL, divisori, cifratura XIP, tensioni e pinmux ereditati.

Per ALNK, `alnk_mux=0x500` è la selezione osservata per la famiglia 48 kHz
nei bit11:8 di `CLK_CON2`, già ricostruita dal driver audio. Non prova il
clock sorgente né la frequenza sui pin. Il lavoro codec richiede di verificare
MCLK 12,288 MHz e BCLK 3,072 MHz per il profilo I2S32 a 48 kHz, oltre a LRCLK
48 kHz; profilo codec, clock fisici e percorso analogico devono concordare
prima di abilitare DMA. Non deriviamo `clock_rate=48000` dal solo mux.

## Cache, MMU e ownership DMA

`hyperrig_mini_cache_range` accetta solo linee da 32 byte interamente nel
range `[0x01C00000,0x01C7FD20)`, escludendo la coda riservata di boot.
Non arrotonda dentro allocazioni adiacenti. Per ogni linea attende il bit14
idle, emette `csync; flush/flushinv; csync` e attende di nuovo. Il flush/invalidate
segue il ciclo originale `0x01C00D80`; la variante clean usa l'istruzione
`flush` osservata, fra gli altri, a `0x01C00E1E`. Un timeout dopo una linea
non dimostra completamento dell'intervallo e non imposta readiness.

Il chiamante deve possedere tutte le linee, escludere scritture concorrenti
da entrambe le CPU e sincronizzare la fase DMA. Per RX, fare clean/invalidate
prima di consegnare il buffer al DMA; non scriverlo dalla CPU durante quella
ownership. Un flush/invalidate successivo di una linea CPU sporca e obsoleta
potrebbe sovrascrivere l'RX appena ricevuto. Per TX, pubblicare i campioni
con il clean appropriato prima che il DMA li legga. L'API fornisce primitive,
non risolve automaticamente protocollo producer/consumer o overrun.

La funzione stock di reset cache libera sette vie D-cache, nessuna I-cache,
riscrive i registri delle vie, azzera array interni e usa `0x01F28000` come
RAM aggiuntiva. HyperRig non usa quella regione e non copia i callback stock.
La nuova API non cambia vie o enable bit e non esegue quell'azzeramento.

Le primitive qui esposte riguardano la **D-cache**. Non dimostrano visibilità
delle istruzioni di `.ramtext` dopo la copia flash→RAM: serve un contratto
di handover/I-cache verificato prima di eseguire quel codice. Lo stock ha una
routine globale a `0x01C00DB2` che disabilita cache e SFC, passa i tag D-cache
e invalida tag I-cache a `0x01F08000` cancellandone il bit15, poi ripristina
SFC/cache. Non è stata portata come primitiva generica e non è stata trovata
una distinta routine I-cache per intervallo con prerequisiti provati.

Il linker SDK riserva 8192 byte iniziali quando `CONFIG_MMU_ENABLE` è
attivo. Lo stock MINI copia invece RAM a `0x01C00000`, coerentemente con il
layout SDK senza quella riserva. È evidenza di layout, **non una prova dello
stato MMU di ingresso**, di mapping/alias DMA o della geometria cache reale.
Questi aspetti, inclusa l'ownership del secondo core, restano da verificare.

## Sequenza per una futura integrazione

1. Con IRQ disabilitati, conservare il descrittore boot; impostare stack,
   BSS e copia RAM, compresa `.ramtext`. Il linker MINI già raccoglie la sezione;
   la visibilità delle istruzioni copiate deve ancora essere verificata.
2. Costruire `hyperrig_mini_platform_io` con `target_io`: questa funzione
   assegna callback e non accede ai registri. Conservare SFC/PLL/MMU ereditati.
3. Acquisire lo snapshot clock/cache e conservarlo nel mailbox diagnostico,
   senza trasformare frequenze nominali in attestazioni hardware.
4. Solo con ownership P33 verificata, applicare la policy watchdog scelta:
   feed dello stato esistente oppure inizializzazione stock con un piano di
   feed periodico. Trattare busy/unsupported/timeout come errore esplicito.
5. Preparare buffer e protocollo IRQ/worker. Invocare le primitive cache solo
   dopo avere verificato mapping DMA, allineamento e ownership delle linee.
6. Verificare clock sui pin, profilo codec, mute/percorso analogico e wrapper
   IRQ11 prima di dichiarare readiness e avviare ALNK.

Non è stata eseguita questa sequenza su hardware. Lo stato all'entry C del
probe, il watchdog già attivo/spento, lock PLL e durata delle operazioni sul
MINI non sono ancora osservati.

## Verifica riproducibile

```powershell
python tools/verify_mini_platform.py
```

Richiede il firmware MINI già decodificato, ISA locale e toolchain JieLi
fissata dal progetto; su Windows usa WSL Ubuntu. Non apre trasporti al pedale.

La verifica esegue 640 combinazioni dei registri clock nelle istruzioni
MINI originali, con registri precedenti al primo risultato nelle coppie
parallele, e confronta il decoder C. Esegue inoltre ASan/UBSan sui trace P33,
sull'interruzione della sequenza in ciascuno dei 18 punti di timeout, su 65
punti di timeout cache, sui confini buffer e sull'assenza di scritture durante
lo snapshot. Il bus fittizio non è un modello fisico o temporale del chip.

L'oggetto target verificato contiene 572 byte `.text`, 606 byte `.ramtext` e
20 byte `.rodata`, senza simboli esterni irrisolti. Il listing conferma
`flush`, `flushinv` e il posizionamento delle callback critiche in RAM.
Il report mantiene esplicitamente false tutte le attestazioni hardware.

Le due unità platform target vengono compilate con
`-mllvm -pi32v2-large-program`: le chiamate a simboli da risolvere al link usano la relocation
`R_PI32V2_EXTEND_CALL_32M2` invece della variante limitata a circa ±4 MiB.
Questo copre i confini flash/RAM senza thunk o puntatori artificiali; la
pubblicazione delle istruzioni RAM resta un prerequisito distinto dal link.
Nel platform attuale i confini usano già le callback e le chiamate locali
restano nella stessa sezione: il flag non cambia i byte o il footprint
dell'oggetto verificato, ma fissa il comportamento delle compilazioni future.
