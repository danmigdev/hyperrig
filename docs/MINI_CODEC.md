# Bus e controllo codec del TANK MINI

Il componente in `firmware/mini/codec/` ricostruisce il bus del firmware
MINI_009 e compila per pi32v2. Le transazioni riuscite sono confrontate con
le istruzioni originali interpretate sul PC. **Non è stato eseguito sul pedale**:
identità fisica del codec, temporizzazioni elettriche, clock e mute analogico
restano da verificare.

La corrispondenza dei registri identifica una **mappa compatibile con Nuvoton
NAU88L21**. Non basta a certificare il componente montato o la revisione della
scheda. È emersa anche una discrepanza importante: interpretata con questa
mappa, la configurazione stock supera il limite di clock dei convertitori
pubblicato da Nuvoton. Il cambio a 48 kHz non può quindi essere dichiarato
pronto sulla base del solo replay dello script originale.

## Evidenza originale e bus

Campione: `artifacts/tank-mini/TANK-MINI.fwsc`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Il verificatore controlla il contenitore, lo decodifica e confronta l'immagine
con `analysis/tank-mini/app_area.dec.bin`. Gli hash delle regioni e i risultati
sono in [mini-codec.json](../research/mini-codec.json).

| Funzione stock | Indirizzo CPU | Comportamento osservato |
|---|---|---|
| Configurazione GPIO | `0x02006960` | PA1/PA2, ingressi digitali e pull-up abilitati |
| START | `0x020069BC` | SDA scende mentre SCL è alto |
| Lettura GPIO | `0x02006AC4` | Il percorso usato legge PA1 da PORTA IN |
| ACK | `0x02006B8C` | SDA diventa ingresso; livello basso significa ACK |
| Invio byte | `0x02006C6A` | Otto bit, più significativo per primo, quindi ACK |
| Invio buffer | `0x02006D1E` | Si ferma al primo NACK e restituisce il numero di ACK |
| STOP | `0x02006D3A` | SDA sale mentre SCL è alto |
| Invio record | `0x02006DCE` | START, `0x36`, quattro byte, STOP solo se tutti ACK |
| Inizializzazione codec | `0x02006DEC` | Configura i GPIO e tenta tutti i 22 record |

Queste transizioni dimostrano **PA1 = SDA, PA2 = SCL**. I GPIO sono nel banco
PORTA a `0x50000`: OUT `+0`, IN `+4`, DIR `+8`, DIE `+12`, PU `+16`, PD `+20`,
con accessi a 32 bit. Il helper stock `0x02004F86` imposta OUT e seleziona
uscita; il driver conserva gli altri bit del banco. La sequenza iniziale è:

1. PA2: DIR=0, PD=0, DIE=1, OUT=0.
2. PA1: DIR=0, PD=0, DIE=1, OUT=1.
3. PA2 OUT=1; PU=1 per PA2 e PA1.

Lo stock **pilota anche il livello alto** e rilascia SDA solo durante ACK.
Non legge SCL, non gestisce clock stretching, arbitraggio o altri master.
Questa ricostruzione riguarda il bus privato osservato; tensioni, resistenze
esterne e compatibilità elettrica non sono dedotte dal codice.

## Ritardi ricostruiti

Prima di ogni attesa lo stock legge il bit 0 del registro `0x40200` e il valore
globale `0x01C1E32C`. Il secondo è il clock di sistema nominale mantenuto dalle
routine stock; il nuovo codice riceve un valore posseduto dal proprio board
support, senza usare quell'indirizzo RAM del firmware originale.

```text
divisore = (registro_40200 & 1) ? 8.000.000 : 4.000.000
n = divisione_intera(clock_sistema, divisore)
iterazioni = n * unità                  // unità = 3 oppure 6
```

Lo stock moltiplica per -3/-6 e incrementa il contatore fino a zero, eseguendo
`nop` a ogni iterazione. `spin_pi32v2.S` fornisce un callback foglia con la
stessa struttura del ciclo. Le chiamate, i helper GPIO, cache, bus e interrupt
aggiungono tempo: **questi conteggi non sono microsecondi calibrati**, né
dimostrano la frequenza SCL. Anche il significato temporale del bit di modo
non viene inferito oltre la selezione del divisore osservata.

| Fase | Sequenza delle attese, in unità |
|---|---|
| START | SDA=1 → 3; SCL=1 → 6; SDA=0 → 3; SCL=0 → 3 |
| Ogni bit | SDA=dato → 3; SCL=1 → 6; SCL=0 → 3 |
| ACK | SDA ingresso; SCL=0 → 3; SCL=1 → 3; lettura SDA → 3; SCL=0 → 3; SDA uscita a 0 |
| STOP | SDA=0 → 3; SCL=1 → 6; SDA=1 → 3 |

L'adattatore MMIO rilegge modo e clock a ogni attesa. Rifiuta valori di clock
nulli, negativi rappresentati come unsigned, o inferiori al divisore: lo stock
produrrebbe attese nulle o patologiche. Il board support deve mantenere stabili
i clock e garantire proprietà esclusiva del banco GPIO durante la transazione.
Il componente non implementa i lock del sistema operativo stock e non cambia
lo stato degli interrupt.

## Identificazione della mappa codec

La tabella stock a `0x02035E35` contiene 88 byte, SHA-256
`1032b05743d45148e6aecd2bdc6834ab54804d154362c545d9949a49461c415d`.
L'indirizzo sul filo `0x36` corrisponde a indirizzo I²C a 7 bit `0x1B` con
scrittura. La disposizione è registro a 16 bit seguito da valore a 16 bit,
entrambi big-endian, come descritto da Nuvoton nella sezione 7.3 del
[datasheet NAU88L21, rev. 3.5](https://www.nuvoton.com.cn/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.5.pdf).

I registri distintivi `0x34`, `0x35`, `0x4B`, `0x7E` e i valori `0xCFCF`
coincidono con NAU88L21 nel
[driver scritto da Nuvoton, Linux v6.12](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.c)
e nel relativo
[header dei registri](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h).
Non viene incorporato codice del driver Linux; queste fonti corroborano
indirizzi e campi. Il verificatore resta completamente offline e non richiede
una copia locale di questi documenti. URL e hash dei file Linux consultati sono
registrati nel report.

I 22 record sono conservati byte per byte e nello stesso ordine. Per i campi
necessari all'adattamento, l'interpretazione condizionata a NAU88L21 è:

| Registro | Stock | Interpretazione dalla mappa NAU88L21 |
|---|---|---|
| `0x03` | `0x0000` | MCLK esterno diretto; divisori ADC e DAC /1 |
| `0x1D` | `0x0002` | Interfaccia audio slave; il campo divisore BCLK vale 2 |
| `0x1C` | `0x000E` | Formato I²S, parole da 32 bit |
| `0x2B` | `0x0003` | ADC OSR 256 |
| `0x2C` | `0x0081` | DAC OSR 256, con gli altri bit stock conservati |
| `0x31` | `0x1004` | Zero crossing ADC/DAC abilitato; soft mute ADC/DAC disabilitato |
| `0x32` | `0x0000` | Bit mute dell'uscita cuffie a zero |

Le parole a 32 bit del codec non provano l'allineamento elettrico dei 24 bit
significativi nei buffer ALNK: la ricostruzione del packing è descritta nel
[driver audio](MINI_AUDIO_DRIVER.md), ma il frame seriale deve essere misurato.
I restanti valori analogici vengono riproposti come record originali; non
si presume di conoscere guadagno della scheda, sequenza di alimentazione,
eventuali mute esterni o tempi di assestamento.

## Discrepanza stock e candidato a 48 kHz

Per la mappa individuata, MCLK=256×Fs richiede 11.289.600 Hz a 44,1 kHz e
12.288.000 Hz a 48 kHz. Con due slot da 32 bit, BCLK=64×Fs richiede
rispettivamente 2.822.400 e 3.072.000 Hz. Questi sono requisiti del profilo,
**non misure del MINI**.

Con OSR256 e divisori /1, lo script stock implicherebbe un clock ADC/DAC di
11,2896 MHz o 12,288 MHz. Il
[datasheet Nuvoton rev. 3.7, sezione 6, pagina 29](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.7.pdf)
limita CLK_ADC a 6,144 MHz; il driver Nuvoton applica questo limite sia ad ADC
sia a DAC. La discrepanza rimane aperta: servono conferma del componente,
misure e comprensione dell'effettiva configurazione prima di qualificare lo
stock a 44,1 kHz o una modifica a 48 kHz.

`hyperrig_mini_codec_plan_128()` calcola un **candidato**, senza inviare nulla:

| Campo | Candidato derivato |
|---|---|
| `0x03` | `0x0050`: divisori ADC e DAC /2, MCLK esterno diretto |
| `0x2B` | `0x0002`: ADC OSR128 |
| `0x2C` | `0x0082`: DAC OSR128, altro bit stock conservato |
| Clock ADC/DAC | 5.644.800 Hz a 44,1 kHz; 6.144.000 Hz a 48 kHz |

Il piano non contiene una sequenza di cambio frequenza in funzione, non
configura PLL/ALNK e non dichiara il dispositivo pronto. Cambiare OSR modifica
anche filtri e latenza. Il codice non aggiorna automaticamente alcuna readiness
audio, neppure dopo un ACK. Il decoder clock del
[componente platform](MINI_PLATFORM.md) fornisce valori nominali da uno snapshot,
senza provare frequenza MCLK, lock o coerenza fra i clock.

## API, errori e mute

`hyperrig_mini_codec_bind_mmio()` collega puntatori e callback senza leggere
periferiche. `bus_init()` esegue esplicitamente la sequenza GPIO. `write()`
invia un record, riporta il numero di byte riconosciuti e distingue errore
principale da errore durante STOP. `write_adapter()` ha la firma richiesta
dal replay del driver audio e accetta soltanto il byte `0x36`, non `0x1B`.

Le differenze intenzionali rispetto al firmware stock sono:

- Su NACK, HyperRig tenta STOP; lo stock ritorna lasciando la transazione aperta.
- Il replay HyperRig si ferma al primo errore; lo stock tenta tutti i record.
- Un errore di lettura o timing invalida l'inizializzazione del bus. Il cleanup
  tenta di riportare SDA/SCL alti, ma un ritardo fallito non garantisce uno STOP
  elettricamente valido.
- Il numero di record completati non implica che una configurazione parziale
  sia utilizzabile: la responsabilità di interrompere l'avvio resta al board.

Il controllo semantico è disabilitato per la mappa predefinita `OPAQUE`.
Se il chiamante seleziona esplicitamente `NAU88L21`, dopo un replay interamente
riconosciuto viene conservato lo shadow `0x1004` del registro `0x31`.
`soft_mute()` cambia soltanto i bit ADC `0x0002` e DAC `0x0200`, preservando
tutti gli altri. Dopo un errore lo shadow viene invalidato; non si continua
a modificare un valore non più noto. Reset o scritture attraverso un altro
percorso richiedono invalidazione e reinizializzazione da parte del chiamante.

Questa funzione controlla **mute digitale**: non prova il silenzio all'uscita,
il completamento della rampa o l'assenza di transitori analogici. Lo script
stock termina con mute disabilitato e non fornisce una sequenza di accensione
silenziosa verificata. Nessun indirizzo GPIO viene inventato per un mute esterno.

## Verifica riproducibile

```powershell
python tools/verify_mini_codec.py
```

Usa WSL Ubuntu/GCC e la toolchain JieLi già fissata nel progetto. Produce:

- `build/mini-codec/hyperrig_mini_codec.pi32v2.o`, componente C relocatable.
- `build/mini-codec/spin_pi32v2.o`, callback di attesa nativo opzionale.
- `research/mini-codec.json`, evidenze, hash, conteggi e limiti.

L'interprete esegue i byte originali delle funzioni bus, inclusi branch,
predicati then/else, divisioni signed, loop e salvataggi dei registri. Solo i
helper GPIO sono sostituiti con eventi di traccia. I 278 casi ACK coprono
tutti i valori di byte in ogni posizione del payload, i 22 record originali
e diversi valori del clock/mode. Le 110 tracce NACK dimostrano la differenza
di cleanup; altri 110 casi verificano l'interruzione del replay.

Sono verificati anche 148 errori di timing, due errori di lettura, 240 casi
del calcolo ritardi, 128 snapshot GPIO, nove casi mute e 1.536 transazioni
con record di quattro byte esatti sotto ASan/UBSan. I due oggetti sono ELF32
pi32v2 e non hanno simboli funzione irrisolti. Il loop dell'oggetto assembly
è nuovamente decodificato e controllato.

Queste prove verificano sequenze software e memoria host. Non emulano
periferiche, temporizzazioni dei helper, tensioni, comportamento del codec,
readback o audio reale. I tool non aprono collegamenti al pedale e non
trasmettono i record attraverso USB, Bluetooth o GPIO.
