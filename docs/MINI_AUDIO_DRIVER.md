# Componente audio HyperRig per TANK MINI

`firmware/mini/audio/hyperrig_mini_audio.c` ricostruisce la configurazione
ALNK0 osservata nel firmware stock TANK MINI_009 e fornisce un adattatore
fra le due metà DMA e un motore mono a punto fisso. È compilabile pi32v2;
**non è stato eseguito sul pedale e non completa l'avvio della scheda**.
Non contiene indirizzi di callback o buffer presi dal TANK-G.

## Evidenza e configurazione

Il campione FWSC ha SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Il verificatore ricontrolla il contenitore e confronta la decodifica con la
copia locale prima di leggere istruzioni o tabelle. Gli hash delle regioni
analizzate sono in [mini-audio-driver.json](../research/mini-audio-driver.json).
La disposizione dei registri è corroborata dall'header SDK `WL82.h` fissato
nel lock, senza incorporare il driver proprietario.

| Elemento | Evidenza nel MINI 009 | Valore ricostruito |
|---|---|---|
| Configurazione globale | `0x02006F70`, tabella `0x02035E90` | ALNK0, gruppo pin 1, master |
| Registri ALNK0 | accessi stock e `WL82.h` | base `0x00012E00`, registri distanziati di 4 byte |
| CON0 prima dell'avvio | campi della tabella +72/+76/+84 | `0x0180` |
| CON1 dopo TX0/RX1 | `0x0200708C` | `0x00D5`, due canali 24 bit |
| CON3 | `0x02006E58` | `0x83` a 44100 e 48000 nominali |
| LEN | `0x02007048` | 128, cioè 1024 byte per canale |
| Indirizzi DMA | tabella `0x0203FED8` | ADR0 a `0x12E10`, ADR1 a `0x12E14` |
| Abilitazione | `0x02007146` | bit 11 di CON0 |
| Multiplexer | `0x02006FC4` | `0x51030`, bit 6–7 impostati a 1 |
| GPIO uscita | `0x02006E08`, helper `0x02004F86` | PA4–PA7: OUT alto, DIR uscita |
| GPIO ingresso | `0x02006E12` | PA8: DIR ingresso, DIE=1, PU=1, PD=0 |

PA4–PA6 sono i tre clock; PA7 è il dato TX0 e PA8 il dato RX1. La tabella
del MINI ha un ordine differente dalla struttura del driver UltraRig.
Il componente conserva gli altri bit di GPIO, mux e clock. Gli accessi
ALNK usano la larghezza stock: 16 bit per CON0/CON1/LEN, 8 bit per CON2/CON3,
32 bit per ADR0/ADR1. Gli offset sono controllati anche in compilazione.

`prepare()` riceve gli indirizzi bus dei buffer scelti dal nuovo linker,
richiede due intervalli distinti di 1024 byte allineati a parola e lascia
DMA disabilitato. Rifiuta una riconfigurazione mentre il bit di avvio è attivo.
Le operazioni sui GPIO sono raggruppate per registro: il risultato statico è
quello osservato, ma non si dichiara l'identità temporale della sequenza stock.
Richiede proprietà esclusiva delle periferiche e IRQ disabilitati durante setup.

## Clock, codec e condizioni di avvio

Il setter stock distingue le due famiglie di clock tramite `0x02006E36`:
preserva tutti i bit di `0x10014` tranne 8–11, che diventano `0x0` a 44100
e `0x5` a 48000. Per entrambe le frequenze, CON3 mantiene il valore `0x83`
nella configurazione master del MINI. Il driver riproduce questi valori;
**non ricostruisce la configurazione precedente del PLL e non misura i clock**.

Prima dell'ALNK, il percorso stock chiama `0x02006DEC`, che invia 22 record
da 4 byte, tabella `0x02035E35`, attraverso `0x02006DCE`. Il byte di indirizzo
del bus è `0x36`; non viene reinterpretato come indirizzo a 7 bit.
`hyperrig_mini_codec_replay_stock()` ripropone i record a un callback di bus
del chiamante e interrompe l'invio al primo errore. I record corrispondono
byte per byte al campione. Nessuna semantica dei registri del codec è inventata.

Il replay riguarda la configurazione stock a 44100 nominali. Non costituisce
una sequenza codec a 48000 verificata. Restano da determinare identità del
codec, clock reali, mute analogico, livelli, temporizzazioni e configurazione
del bus PA1/PA2. Lo script del codec non è inviato da alcun tool di verifica.

`start()` richiede una struttura `hyperrig_mini_audio_readiness` fornita dal
board support con clock e codec alla frequenza richiesta, wrapper IRQ installato,
memoria DMA coerente e percorso analogico/mute predisposto. Il driver controlla
questo contratto ma non può verificare elettricamente ciò che il board support
riporta. **Questi prerequisiti non risultano soddisfatti sul dispositivo reale.**

## IRQ, memoria e deadline

L'handler stock `0x01C0374A` usa IRQ 11, priorità 6, e controlla i bit 4–7
di CON2. La metà appena terminata per il canale `c` è
`(~(CON0 >> (12+c))) & 1`. Segue l'ack tramite read/OR/write del bit `c`
di CON2. Il nuovo handler replica la selezione RX1 e gli ack dei quattro
canali, ma delega l'accodamento dell'evento al callback `ready()`.

Il wrapper hardware deve salvare e ripristinare lo stato interrupt pi32v2;
`hyperrig_mini_audio_irq()` è il corpo C, non un vettore direttamente invocabile
dal processore. La tabella IRQ e l'installazione dipendono dal codice di boot.
Il callback deve segnalare un task; non deve eseguire il DSP dentro l'IRQ.

Ogni buffer contiene 256 parole da 32 bit, divise in due metà da 128 parole:
64 frame con due slot. Il task stock seleziona entrambe le metà RX/TX con
`indice << 9` e invoca il processore con 64 frame (`0x01C03F24`). Anche il
nuovo adattatore usa la stessa metà per RX e TX; la corrispondenza di fase
deve essere verificata sul dispositivo. A 48 kHz il budget di una metà è
circa 1,333 ms, prima di margini per IRQ, scheduler e manutenzione cache.

Sono consigliati buffer a 32 byte di allineamento nella sezione `.dma32`
del nuovo linker. La necessità e l'implementazione di flush/invalidate o
barriere verso ALNK restano responsabilità del board support: le prove host
non stabiliscono la coerenza DMA. Non è implementata una coda condivisa ISR/task;
il chiamante deve gestire sovrascritture, notifiche perse e deadline mancate.

## Conversione campioni e collegamento del motore

I tre opcode a `0x01C03A52` caricano il primo slot, eseguono uno shift sinistro
di 8 con wrap a 32 bit e poi uno shift aritmetico destro di 7. Il risultato
è `sign_extend_24(slot) * 2`: solo i 24 bit inferiori sono significativi.
`hyperrig_mini_audio_stock_rx()` riproduce esattamente questa operazione.

L'adattatore HyperRig usa una convenzione normalizzata: interpreta il campione
24 bit come Q23, lo porta a `model.input_fraction`, converte l'uscita da
`model.output_fraction` a Q23, satura a 24 bit e duplica il mono nei due slot.
Per A2, Q23→Q30 equivale a moltiplicare per 128; Q31→Q23 applica lo shift
destro di 8. Gli shift destri arrotondano verso meno infinito. Il byte alto
dei dati TX è zero; il dato utile sono i 24 bit inferiori.

Questo scaling e la scelta dual-mono sono **adattamenti HyperRig**. Non riproducono
i guadagni, l'elaborazione stereo, il soft mute o la LUT finale del firmware
stock e non sono stati confrontati con il front-end UltraRig G. Non viene
introdotta alcuna conversione di sample rate.

Un task può collegare il componente al motore ricostruito con questo callback:

```c
static int capture_block(void *user, const int32_t *input,
                         int32_t *output, uint32_t frames)
{
    return hyperrig_a2l3_process((hyperrig_a2l3 *)user, input, output, frames);
}

/* Dopo un evento RX valido, cache pronta e verifica della deadline: */
status = hyperrig_mini_audio_process_half(rx_dma, tx_dma, half,
    model.input_fraction, model.output_fraction, capture_block, &engine);
```

`process_half()` richiede circa 512 byte di scratch campioni sullo stack del
task e non alloca heap. Gli errori di elaborazione rendono silenziosa soltanto
la metà TX corrente, senza alterare l'altra. L'applicazione deve verificare
che il sample rate della capture coincida con quello effettivo della periferica.

## Riproduzione delle verifiche

```powershell
python tools/verify_mini_audio.py
```

Il comando usa WSL Ubuntu/GCC per i controlli host e la toolchain JieLi già
fissata nel progetto per `build/mini-audio/hyperrig_mini_audio.pi32v2.o`.
L'oggetto ha ISA ELF32 pi32v2 e nessuna funzione esterna irrisolta; resta un
componente relocatable da collegare all'applicazione. Il suo codice `.text`
misura 948 byte, più 88 byte di tabella codec in `.rodata` in questa build.

Risultati: 520 confronti con il frammento RX originale, 33.280 conversioni
normalizzate, 12 casi di metà DMA, 256 snapshot dei registri, 32 combinazioni
pending/fase IRQ e 259 casi con buffer di dimensione esatta sotto ASan/UBSan.
Sono verificati anche rifiuto degli indirizzi/parametri invalidi, preservazione
degli altri GPIO, blocco dell'avvio senza prerequisiti e propagazione degli
errori del codec/DSP. I test scrivono soltanto in strutture di memoria host:
**non accedono alle periferiche né al Bluetooth/USB del pedale**.

I registri host non emulano il comportamento temporale del DMA o l'autoclear
dei bit di ack. Soltanto la conversione RX a tre istruzioni è confrontata
numericamente con un frammento stock interpretato; la configurazione completa
è una ricostruzione statica verificata attraverso valori e indirizzi.
