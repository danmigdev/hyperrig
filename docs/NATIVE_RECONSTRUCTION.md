# Ricostruzione nativa di UltraRig TANK-G

Sono disponibili **tre routine DSP ricostruite in C compilabile** dai byte di
UltraRig alpha11/M5.71 TANK-G v2. Non sono i sorgenti originali recuperati e
non costituiscono ancora il motore A2-Lite completo o un firmware MINI avviabile.
Mantengono il Required Notice e la licenza UltraRig: vedere
[PROVENIENZA.md](PROVENIENZA.md).

## Funzioni ricostruite

| Indirizzo CPU originale | Intervallo esclusivo | Implementazione |
|---|---|---|
| `0x01C12608` | fino a `0x01C126F4` | `hyperrig_dot_i16`: attivazioni int32, pesi int16 |
| `0x01C126F4` | fino a `0x01C127DE` | `hyperrig_dot_i32`: attivazioni e pesi int32 |
| `0x01C130B4` | fino a `0x01C1318E` | `hyperrig_head3_process`: convoluzione finale a tre canali |

I sorgenti sono in `firmware/src/`; gli header pubblici in
`firmware/include/hyperrig/`. Non derivano dall'output incompleto di Ghidra:
ABI, indirizzamento e operazioni sono ricostruiti dal disassembly pi32v2.

Il campione originale ha SHA-256
`2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059`.
Il reset copia `0x2030C` byte da flash CPU `0x02056780` a RAM `0x01C00000`.
Pertanto un indirizzo RAM `a` corrisponde a offset
`0x56780 + (a - 0x01C00000)` nell'area applicativa decodificata, oppure a
quell'offset meno `0x120` nel file estratto `app.bin`.

Le due funzioni dot ricevono output, stride output, input e stride input in
`r0..r3`; pesi, numero di tap, numero di campioni e shift sono sullo stack.
Gli stride contano elementi int32. I pesi restano gli stessi per ogni campione.
L'accumulatore a 64 bit può andare in overflow e avvolgersi: il C lo conserva
con aritmetica unsigned, evitando overflow signed indefinito.

Nel dominio senza overflow, lo shift destro arrotonda al più vicino con i
pareggi lontano da zero; quello sinistro conserva il wrap a 64 bit. Segue la
saturazione int32. I casi di overflow non vengono sostituiti con una formula
matematica idealizzata. Il wrapper C accetta shift `[-62, 62]`, conteggi e
stride non negativi; intervalli e non sovrapposizione dei buffer sono a carico
del chiamante.

## Stadio finale a tre canali

Il preparatore originale `0x01C12CC2` costruisce un contesto da 56 byte e
invoca `0x01C130B4`. La routine scrive ogni terna nel buffer circolare e
duplica i primi 64 frame dopo la fine del ring. Questo permette di leggere
contiguamente la finestra della convoluzione quando attraversa il bordo.

Il MAC parte da `2^(shift-1)-1`, aggiunge la correzione di segno, applica lo
shift aritmetico e satura a int32. Poi aggiunge il bias int64 già convertito
dal caricatore nativo e satura nuovamente. **Quel bias non va identificato
automaticamente con il valore grezzo contenuto nel file A2L1**: la conversione
del caricatore resta da integrare.

L'API ricostruita usa un contesto portabile proprio. Supporta 1–64 frame per
chiamata, shift 1–31, kernel 1–65 frame e un ring di almeno 64 frame e almeno
quanto il kernel. Il contesto reale osservato invoca blocchi di 64 frame.
L'API non riutilizza puntatori RAM del G e non accede a periferiche.

## Compilare e confrontare

Su Windows sono necessari WSL Ubuntu con `gcc`, Python 3 e il runtime UBSan.
Gli artefatti e la tabella ISA si ottengono con il bootstrap e l'analisi
descritti nel README. La toolchain JieLi resta nella directory locale ignorata
da Git; URL, versione `20260730.1` e SHA-256 sono fissati nel lock.

```powershell
python tools/bootstrap.py --toolchain
python tools/build_native.py
```

La build produce:

- `build/native/libhyperrig_dsp.so`: C eseguito sul PC con UBSan;
- `build/native/hyperrig_dsp.pi32v2.o`: oggetto ELF32 pi32v2 relocatable,
  compilato con JieLi clang `-target pi32v2 -mcpu=r3`;
- `analysis/native/verification.json`: hash e risultati dei confronti.

Il compilatore del target è impiegato come strumento, senza estrarne il codice.
L'oggetto contiene ancora rilocazioni; non è un'immagine flash, manca un linker
di applicazione con startup, IRQ, memoria e driver del MINI.

La verifica confronta il C host con un interprete limitato che decodifica ed
esegue **i byte originali delle tre routine**. Prima controlla l'hash del
firmware e che `app.bin` coincida con la sua decodifica. Non accetta istruzioni
sconosciute; le letture di memoria non inizializzata falliscono. Il REP della
testa usa conteggi positivi; il comportamento del conteggio zero è escluso.
La semantica REP è corroborata dal
[resoconto hardware pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/hw/fm1-2026-10-24-v3/README.md).

Risultato locale: **1.660 confronti superati**: 629 per ciascun dot e 402 per
la testa. Comprendono segni, pareggi, saturazione, wrap a 64 bit, stride,
finestre circolari e chiamate consecutive. Per la testa si confrontano anche
tutta la memoria del ring e la posizione finale. Sette test separati verificano
l'interprete con risultati semplici calcolati a mano.

Questa verifica resta dipendente dalla semantica implementata nell'interprete.
Non esegue l'oggetto target appena compilato su un processore reale, non misura
tempi e non dimostra equivalenza dell'intero firmware. Il report versionato è
[native-verification.json](../research/native-verification.json).

## Prossime funzioni identificate

I nomi seguenti sono interpretazioni del codice, non simboli originali:

| Indirizzo | Ruolo ricostruito/inferito |
|---|---|
| `0x02031C64` | parser A2L, verifiche formato/CRC e costruzione del contesto |
| `0x01C12850` | calcolo dello spazio necessario per il modello |
| `0x01C12878` | reset degli stati del modello |
| `0x01C1296C` | inizializzazione e installazione del callback dot |
| `0x01C129DC` | preparazione rechannel specializzato a tre canali |
| `0x01C12A54` | preparazione/dispatch dei kernel di layer |
| `0x01C12C32` | iterazione dei layer per blocchi da 64 frame |
| `0x01C12CC2` | preparazione del contesto della testa |
| `0x01C12D34` | probabile wrapper del percorso di elaborazione |

Restano da ricostruire conversione dei bias, convoluzioni dilatate, attivazioni,
residuali, scaling tra layer, IR ed effetti. Il riferimento Float64 già presente
serve a verificare la struttura matematica, ma non sostituisce questo lavoro.

## Correzione degli indirizzi di salto

Le destinazioni relative pi32v2 si calcolano da **PC + lunghezza effettiva
dell'istruzione + displacement**. Il primo disassembler locale usava sempre
PC+2: le annotazioni di istruzioni da 4/6 byte erano errate. È stato corretto,
i listati rigenerati e tre encodings reali aggiunti ai test, con riscontro
nel disassembler JieLi. La scansione lineare continua a comprendere anche dati:
non diventa per questo un grafo di flusso completo e verificato.
