# Clock audio del TANK MINI

Il ramo stock chiamato **48 kHz non dimostra 48.000 Hz esatti**. Il codice
ricostruito seleziona una famiglia ALNK; le denominazioni dei divisori nel SDK
suggeriscono circa **48.076,923 Hz**. Il bootloader MINI abilita già l'uscita PLL
richiesta da quel ramo. Non serve dedurre una nuova sequenza di programmazione
PLL dalla routine di spegnimento a `0x01C03352`.

Il componente [hyperrig_mini_clock.c](../firmware/mini/clock/hyperrig_mini_clock.c)
calcola piani e analizza valori forniti dal chiamante. **Non accede a MMIO,
non invia record al codec e non concede readiness audio.** Le frequenze in
questo documento sono ipotesi nominali o obiettivi di misura, mai misure del
pedale. Le prove riproducibili sono in [mini-clock.json](../research/mini-clock.json).

## Catena di avvio ricostruita

Il campione è `TANK-MINI.fwsc`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.

1. Il bootloader applica il profilo MINI `OSC=0/24 MHz`, `SYS_CLK=360 MHz`,
   `HSB_DIV=1`, `LSB_DIV=2`, `SDRAM=0`. A `0x01C0434E..435A` compone
   `PLL_CON1 = 0x3F503000 | (480000000/reference - 2)`. A `0x01C0438A/4394`
   abilita i due bit bassi di `PLL_CON0`. Il ramo speciale che evita questa
   sequenza richiede `OSC=3` e reference=1: non è quello del profilo MINI.
   Questo prova la presenza programmata del bit25; non prova il lock analogico.
2. L'entry applicativa `0x02000120` copia il codice RAM e configura le cache;
   `0x02003140` chiama `0x02002D40`. Il tratto `0x02002D76..2EC8` legge i
   clock ereditati e aggiorna i valori nominali in RAM. Le istruzioni successive
   configurano UART/HUSB e altri servizi. Non impostano una nuova frequenza ALNK.
3. Il task applicativo chiama `0x020071FE`. Questa funzione porta **PA9 basso**,
   attende un loop di 100.000 iterazioni, chiama `0x0200717C`, attende un altro
   loop uguale e porta **PA9 alto**. La funzione elettrica di PA9 e la durata
   temporale dei loop restano sconosciute.
4. `0x0200717C` chiama l'inizializzazione dei 22 record codec a `0x02006DEC`,
   scrive il countdown iniziale e poi avvia ALNK tramite `0x0200715C`.
   `0x02006F70` applica la configurazione; `0x02006E58` seleziona il rate;
   `0x02007146` abilita ALNK. La tabella di configurazione stock richiede 44100.

Il payload bootloader ha SHA-256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`.
La configurazione occupa 699 byte in flash a `0x38D0`, con CRC16 `70D5` e SHA-256
`0952afd96f533dd0fba72a8fab9cb4a4336f55424a1a89eecb13ff8a51a0eff0`.
Il profilo e i controlli del passaggio dal bootloader sono documentati separatamente
in [mini-handover.json](../research/mini-handover.json).

`0x01C03352` appartiene alla funzione `0x01C03296..33EC`, richiamata dai percorsi
di sospensione/spegnimento. Attende cache e SFC, disabilita SFC, cambia divisori
e sorgente principale, quindi riabilita SFC. **Non è l'inizializzazione audio**;
non è stata portata né richiamata. Eseguirla da codice XIP interromperebbe il
meccanismo da cui quel codice viene letto.

## Famiglie ALNK e frequenze

La funzione stock `0x02006E36` conserva gli altri bit di `CLK_CON2` a `0x10014`
e modifica il nibble `[11:8]`. Con la configurazione master del MINI:

| Etichetta richiesta | `CLK_CON2 & 0xF00` | `ALNK_CON3` | Comportamento |
|---|---:|---:|---|
| 44100 | `0x000` | `0x83` | Configurazione stock |
| 48000 | `0x500` | `0x83` | Ramo presente nel codice stock |
| Non supportata, anche 96000 | `0x000` | `0x83` | Ripiego silenzioso stock su 44100 |

L'API `hyperrig_mini_clock_stock_plan()` riproduce anche gli altri nove rate
riconosciuti e il comportamento slave, segnalando esplicitamente il ripiego.
Il piano non applica le scritture e non modifica la configurazione del codec.

Nel [SDK AC79 fissato](https://github.com/amitv87/fw-AC79_AIoT_SDK/tree/ffbb2a8d925682ba6880d643a83a63ee0691ec09),
`cpu/wl82/liba/cpu.a` contiene LLVM bitcode recuperabile con il compilatore
JieLi. La funzione originale `iis_set_sample_rate(48000)` in `iis.c.o`
imposta **`PLL_CON1 bit25`** e poi seleziona la famiglia ALNK. Lo stock MINI
modifica solo il mux, quindi dipende dall'uscita PLL già abilitata dal bootloader.
Il verificatore ricava l'IR dal blob fissato; quel codice SDK non viene linkato
nel firmware HyperRig.

Il [clock_hw.h dello stesso SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h)
nomina `192M/17` e `160M/13` (oppure l'equivalente `480M/39`). **Le dichiarazioni
sono nei rami debug/disabilitati**, quindi non sono una prova autonoma della
frequenza fisica. Combinate con la configurazione stock a 256fs danno questa
ipotesi verificabile:

| Famiglia | MCLK nominale, Hz | BCLK nominale, Hz | LRCK nominale, Hz | Scarto dall'etichetta |
|---|---:|---:|---:|---:|
| 44100 | `192000000/17` ≈ 11294117,647 | ≈ 2823529,412 | ≈ 44117,647 | +400,160 ppm |
| 48000 | `160000000/13` ≈ 12307692,308 | ≈ 3076923,077 | ≈ 48076,923 | +1602,564 ppm |

A `0x020071BA` lo stock scrive **44118** a `0x01C1BA50`. Il percorso audio
`0x01C03ADE..3B18` sottrae 64 per blocco e mantiene il guadagno a zero fino
alla scadenza: 690 blocchi, 44160 campioni. È un countdown iniziale di circa
un secondo, **non una variabile di configurazione del sample rate**. Il suo
valore arrotondato corrobora l'ipotesi 44117,647; non sostituisce una misura.

`hyperrig_mini_clock_audit()` distingue configurazione ALNK, bit di controllo
PLL, uscita PLL abilitata e ALNK in funzione. Nessun bit è chiamato “lock”.
`hyperrig_mini_clock_measurement_flags()` confronta frequenze fornite
dall'operatore con:

- la frequenza esatta indicata dall'etichetta;
- l'ipotesi nominale della famiglia SDK;
- i rapporti MCLK/LRCK=256 e BCLK/LRCK=64.

La tolleranza è esplicita e l'incertezza fornita riduce il margine disponibile.
Gli esempi nel report sono sintetici. Per distinguere 44100 da 44117,647 serve
un'incertezza sensibilmente inferiore a 400 ppm; per 48000 vs 48076,923 inferiore
a 1603 ppm. Un conteggio basato su un clock derivato dalla stessa PLL non basta
da solo a verificare la frequenza assoluta.

## Codec: discrepanza ancora da misurare

I record stock sono `R03=0`, `R2B=3`, `R2C=0x81`. La mappa NAU88L21 li interpreta
come ADC/DAC a OSR256 e clock dei convertitori senza divisione. La variante
**NAU88L21C usa gli stessi codici per questi valori**: non risolve la discrepanza
cambiando soltanto il nome del componente. La sua mappa aggiunge altri rate e
filtri, ma la compatibilità dei campi comuni non identifica il chip montato.
La codifica è riportata alle pp. 22, 59, 60 della
[datasheet NAU88L21C rev1.3](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.3.pdf).

Le fonti del produttore sono internamente discordanti: le caratteristiche
iniziali dichiarano 48 kHz/OSR256, mentre il capitolo clock impone 6,144 MHz massimi
per il clock ADC. Anche il [driver Linux scritto da Nuvoton](https://github.com/torvalds/linux/blob/v6.12/sound/soc/codecs/nau8821.c)
applica quel limite. Quindi il precedente conflitto documentato in MINI_CODEC
resta **una contraddizione fra configurazione osservata e limite pubblicato**,
non una dimostrazione che il pedale originale funzioni fuori specifica.
Vedere [NAU88L21 rev3.7](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf)
e [NAU88L21C rev1.6, p30](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.6.pdf).

La ricerca dei riferimenti diretti trova un solo chiamante del writer dei
record, il loop dei 22 record, e un solo chiamante dell'init, lo startup audio.
Non sono emerse scritture OSR successive né puntatori assoluti a queste due
funzioni. La scansione non esclude chiamate calcolate o altre implementazioni
del bus; non è una prova completa dell'assenza di qualsiasi scrittura.

Il vecchio candidato OSR128 richiede attenzione: con l'ipotesi 48076,923 Hz il
clock convertitore sarebbe **6,153846 MHz**, leggermente sopra il limite pubblicato.
Un candidato che conserva 256fs e rimane sotto quel limite è OSR64:

| Registro | Valore da shadow stock | Significato condizionato alla mappa compatibile |
|---|---:|---|
| `0x03` | `0x00A0` | Clock ADC e DAC divisi per 4 |
| `0x2B` | `0x0001` | ADC OSR64 |
| `0x2C` | `0x0080` | DAC OSR64, altri bit conservati |

Questo darebbe circa 3,076923 MHz al convertitore per la famiglia nominale 48k.
`hyperrig_mini_clock_osr64_candidate()` genera solo questi tre record da uno
shadow fornito; rifiuta altri modi clock. **Non li trasmette.** Cambiare OSR cambia
filtri e latenza: il risultato va misurato e non equivale al comportamento stock.

## Percorso minimo di prova

1. Acquisire uno snapshot reale dopo il bootloader e verificare PLL_CON0/1,
   CLK_CON2 e ALNK. Conservare PLL e SFC ereditati. Il solo snapshot non prova
   ancora la frequenza.
2. Accertare la mappa fisica del codec e il controllo analogico di PA9. Conservare
   l'uscita silenziosa durante la configurazione; il codice non presenta PA9
   come un mute già verificato.
3. Dopo questa verifica, valutare il candidato OSR64, I2S slave a 32 bit e ALNK
   master della famiglia 48k, con buffer inizializzati a zero e blocchi da 64.
   Richiedere ACK, IRQ installato, coerenza DMA e controllo analogico prima di abilitarlo.
4. Misurare MCLK, BCLK e LRCK rispetto a un riferimento indipendente. Registrare
   frequenza, incertezza e rapporti, senza sostituire automaticamente “48000”
   al risultato. Solo allora provare il bypass e misurarne rumore/latenza.
5. Collegare A2 dopo il bypass. Se il clock risulta 48076,923 Hz, valutare
   esplicitamente adattamento/resampling o accettazione dello scarto; non
   dichiarare completato un percorso a 48.000 Hz esatto.

Questo documento propone il percorso; questo componente non lo esegue.

## Verifica riproducibile

```powershell
python -B -X utf8 tools/verify_mini_clock.py
```

La dipendenza SDK è fissata in `sources.lock.json`:
`upstream/ac79-sdk-reference/cpu/wl82/liba/cpu.a`, SHA-256
`00cea21d3c8d99487821f2c2b203f2c5a04b2cc8421bc05e9b875a0d70e42c62`.
Il verificatore non richiede il download delle datasheet e non contiene
accesso al dispositivo. Controlla 6080 casi contro le istruzioni originali
del selettore di rate, 2000 confronti di misure con aritmetica intera e 66560
casi ASan/UBSan. Compila `hyperrig_mini_clock.pi32v2.o`: 1152 byte di codice,
nessun simbolo esterno. Il componente non duplica l'inizializzazione bus già
verificata e non abilita clock, codec o audio nei probe esistenti.
