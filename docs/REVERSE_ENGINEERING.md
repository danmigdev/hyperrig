# Reverse engineering UltraRig e confronto TANK MINI

Ricerca avviata il 15 novembre 2026. Le conclusioni riguardano gli artefatti
identificati dagli hash, non ogni revisione hardware commercializzata.

## Campioni e sorgenti trovati

Repository ufficiale: [manuaguirre9/ultrarig](https://github.com/manuaguirre9/ultrarig).
Campione principale: [release alpha11](https://github.com/manuaguirre9/ultrarig/releases/tag/alpha11),
pubblicata il 12 novembre 2026; versione interna `M5.71`.

Sono stati controllati tutti i commit e tag raggiungibili del repository, i
quattro fork pubblici individuati, i loro branch e l'elenco degli asset delle
release. Il branch `heil-j/ultrarig:feature/ai-tone` contiene un editor web,
non i sorgenti C del firmware. Le release di test successive non sono il
campione di questa analisi. Evidenza: `research/source-audit.json`.

Il [NOTICE originale](https://github.com/manuaguirre9/ultrarig/blob/main/NOTICE.md)
dichiara una distribuzione binaria. Abbiamo effettivamente recuperato:

| Componente | Recupero ottenuto | Limite |
|---|---|---|
| Editor e convertitore NAM | Sorgenti HTML/JS originali, leggibili | Licenza originale conservata |
| APK Android | Asset web, configurazione Capacitor, plugin dichiarati | Parte Java/Dex non decompilata |
| Installer Windows | Moduli Python 3.12, costanti e bytecode disassemblato | Nessun `.py` originale completo recuperato |
| Firmware pi32v2 | Applicazione decodificata, assembly, pseudocodice Ghidra | Nessun sorgente C originale né progetto ricompilabile |
| SDK hardware | Header GPIO/ADC/DAC e mappa registri da un mirror del SDK | Non è il sorgente del DSP UltraRig |

## Integrità e immagini

Gli ZIP e l'APK corrispondono ai digest pubblicati nell'API GitHub. Ogni
`*_app.bin` corrisponde al relativo JSON. I CRC16 di tutte le directory JLFS e
dei file applicativi estratti sono validi.

| Modello | File | Byte nell'area distribuita | Byte del solo `app.bin` |
|---|---|---:|---:|
| TANK-G v2 | `m571_g_app.bin` | 487424 | 485772 |
| TANK-G v1 | `m571_v1_app.bin` | 487424 | 485868 |
| TANK-B v2 | `m571_tb_app.bin` | 487424 | 485772 |
| TANK-B v1 | `m571_tbv1_app.bin` | 487424 | 485772 |
| TANK MINI stock 009 | `TANK-MINI.fwsc` → `flash.bin` | 532480 per `flash.bin` | 511032 |

Gli hash completi, i CRC e le versioni incorporate sono in
`research/input-manifest.json` e nel risultato rigenerabile `analysis/summary.json`.
Il FWSC MINI ha SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Il catalogo del produttore lo identifica come V09; HTTP Last-Modified osservato:
8 luglio 2026. Data di catalogo, compilazione e modifica HTTP non sono equivalenti.

## Piattaforma e indirizzi

I JSON UltraRig indicano AC791N, 396 MHz e chip key `0x980F`. Per il MINI,
AC791N è nel contenitore ufficiale e la stessa chiave decodifica il suo JLFS
con CRC validi. Le istruzioni iniziali di tutti i campioni sono coerenti con
pi32v2. Questo non dimostra che il MINI possa usare il clock di UltraRig.

Bisogna distinguere tre spazi di indirizzi:

- Offset nel file dell'area applicazione: comincia da zero.
- Indirizzo flash fisico: offset precedente + `0x4000`.
- Indirizzo CPU della finestra flash: offset precedente + `0x02000000`.

`app.bin` è a offset `0x120` nell'area, quindi a flash fisica `0x4120` e a
indirizzo CPU `0x02000120`. Non va importato in Ghidra come ARM o RISC-V.

Il codice di reset copia anche codice/dati in RAM:

| Campione | Sorgente CPU flash | Destinazione RAM | Lunghezza |
|---|---|---|---:|
| UltraRig G v2 | `0x02056780` | `0x01C00000` | `0x2030C` |
| MINI stock 009 | `0x0206ED20` | `0x01C00000` | `0xE018` |

Le mappe degli altri campioni sono estratte automaticamente dal relativo
reset in `memory-layout.json`. Le zone di RAM non inizializzate create per
l'analisi Ghidra sono uno spazio di lavoro, non una misura della RAM libera.

## Decodifica SFC e filesystem JLFS

La codifica applicativa è XOR con uno stato a 16 bit, reinizializzato a ogni blocco
di 32 byte. Per un blocco che inizia all'offset `o` dell'area applicazione:

```text
state = 0x980F XOR (o >> 2)
plain_byte = stored_byte XOR (state & 0xFF)
state = ((state << 1) XOR (0x1021 se il bit 15 era uno, altrimenti 0)) & 0xFFFF
```

La base del calcolo è l'inizio dell'area applicativa, non l'inizio dell'intera
flash. Il padding oltre la lunghezza effettiva del contenitore viene conservato.
I CRC usano polinomio `0x1021`, inizializzazione zero.

Ogni directory entry è una struttura little-endian di 32 byte:
`<HHIIBBH16s`: CRC header, CRC dati, indirizzo/offset, lunghezza, flags, byte
riservato, indice/terminatore, nome. I flags `0x82` identificano i file estratti;
`0x83` identifica `app_area_head`. I campi delle aree riservate non sono offset
di payload da leggere nel file applicativo.

Validazioni: i quattro campioni UltraRig e il MINI passano; un byte modificato,
una chiave errata e un FWSC troncato vengono rifiutati dai test.

## Mappe flash: differenza decisiva per il porting

Intervalli semichiusi `[inizio, fine)`:

| Area | UltraRig G/B M5.71 | MINI stock 009 |
|---|---|---|
| SPL/directory iniziale | `0x00000–0x04000` | `0x00000–0x04000` |
| Applicazione riservata | `0x04000–0x7B000` | `0x04000–0x82000` |
| VM dichiarata in JLFS | `0x7B000–0xBD000` | `0x82000–0xBE000` |
| BTIF | `0xBD000–0xBE000` | `0xBE000–0xBF000` |
| Entry OTP | `0xBE000–0xBF000` | Nessuna entry OTP con quel nome |
| USR | `0xBF000–0xFF000` | `0xBF000–0xFF000` |
| key_mac, directory superiore | ultimo settore previsto dall'installer | `0xFF000–0x100000` |

La mancanza di una entry OTP nel MINI non dimostra l'assenza di OTP nel chip.
Il file MINI `flash.bin` termina a `0x82000`: non contiene VM, BTIF, USR e
key_mac del pedale dell'utente. Non è un backup completo da scrivere sul chip.
Il suo header riporta `0xFF000`; la directory riserva anche l'ultimo settore
fino a `0x100000`. La capacità fisica va verificata sul dispositivo.

Per il Tank-B originale, il bytecode dell'installer descrive un'applicazione
fino a `0x7F000` e la migrazione della VM alla posizione UltraRig. Questo è un
risultato ricavato dall'installer, non da un dump originale Tank-B acquisito qui.

## Protocollo UltraRig

Ricostruito dalle chiamate effettive in `tankg.html` e confrontato con le
stringhe presenti nel binario. Non è stato collaudato su hardware in questa
sessione. `analysis/protocol-call-sites.json` conserva le righe di origine.

- USB: Web Serial/CDC, filtro VID `0x3654`, apertura a 115200 baud.
- Messaggi di testo terminati da newline, richieste serializzate.
- Eventi asincroni `@L` e `@K`; gli errori iniziano con `ERR`.
- BLE: servizio NUS `6e400001-b5a3-f393-e0a9-e50e24dcca9e`, RX `...0002`,
  TX `...0003`, caratteristica pairing `...0004`.
- Il client usa linee fino a 190 caratteri sui firmware recenti. Su BLE i
  frammenti iniziali sono da 20 byte, fino a 244 dopo negoziazione MTU.

| Famiglia | Comandi osservati |
|---|---|
| Diagnostica | `PING`, `STAT`, `MEM`, `MODEL`, `EVT`, `LIFE`, `CRASH`, `CLKSTATE` |
| Catena effetti | `FXT`, `FXS`, `FXA`, `FXR`, `FXM`, `FXE`, `FXP`, `FXL`, `FXOS` |
| Routing | `FXMIX`, `FXXO`, `FXIR`, `AMP`, `AMPX`, `AMPEQ` |
| Preset e scene | `PLIST`, `PLOAD`, `PSAVE`, `PNEW`, `SNAP`, `SNAPSAVE`, `SNAPNAME` |
| Capture | `LDBEGIN`, `LDB`, `LDEND`, `CLIST`, `CLOAD`, `CSAVE`, `CREAD` |
| IR | `IRBEGIN`, `IRB`, `IREND`, `ILIST`, `ILOAD`, `ISAVE`, `IREAD` |
| Controlli | `FSA`, `FSMODE`, `FSPRESS`, `FSLED`, `LEDCFG`, `BPM`, `TAP`, `TUNE` |

I trasferimenti verso il pedale usano offset e byte esadecimali; il comando
finale porta il CRC32 IEEE. Gli esempi sono documentazione di protocollo,
non operazioni inviate al dispositivo.

## Capture, IR e preset

È stata estratta e validata la capture incorporata `A2`, di 4892 byte:
23 layer, 3 canali, kernel finale 16, 48 kHz, pesi int16, attivazioni int32,
bias int64, receptive field di 6347 campioni. Il parser è in `hyperrig/a2l.py`.
La capture passa anche `validateBlob()` del convertitore originale.

Header A2L1: 36 byte, little-endian, firma `A2L1`, versione, bit di pesi e
attivazioni, sample rate, layer, canali, kernel, quattro esponenti Q e nome
di 16 byte. Seguono rechannel, layer con kernel/dilatazione/pesi/bias, testa
e CRC32. Il formato è distinto dai file `.nam` JSON e dai formati AM3/AM4
del firmware originale. La release analizzata dichiara `amx=false`.

Il client prepara IR in int16; capacità memorizzabile di 4076 campioni nelle
ranure 0–6 e 2028 nella ranura 7, con gain separato. Il protocollo può allocare
4096 campioni per un upload: capacità temporanea e capacità salvata differiscono.

L'esportazione preset del client è JSON `format="ultrarig-preset"`, versione 1;
può includere allegati con SHA-256. Le scene e gli effetti vengono ricostruiti
con comandi del protocollo. Il MINI originale usa invece record binari da
92 byte, 21 per banca: rinominare un JSON non converte il preset.

## Riferimento DSP ricostruito

`hyperrig/a2l_reference.py` implementa un modello causale in Float64, con
buffer circolari per le convoluzioni dilatate, LeakyReLU, residuali, somma delle
attivazioni e convoluzione finale. I pesi e bias vengono dequantizzati usando
gli esponenti del file. I bias della convoluzione usano `conv_F + previous_F`,
quelli del residuale `linear_F + activation_F`, quello finale `head_F + sum_F`.

Il pre-roll di `receptive_field - 1` zeri conserva l'allineamento temporale
del convertitore. I test confrontano le 49 misure di picco di ogni passaggio
con `measure()` del JavaScript recuperato, usando gli stessi pesi dequantizzati:
silenzio, impulso e un segnale alternato/sinusoidale. Tolleranze:
`rel_tol=1e-11`, `abs_tol=1e-12`. Altri test verificano risultati campione per
campione di una piccola rete calcolabile a mano, scaling dei bias, continuità
fra blocchi e clipping del WAV.

Questo verifica la struttura matematica del riferimento in virgola mobile.
Non è una verifica bit per bit contro il firmware: shift arrotondati,
saturazioni, overflow, precisione delle attivazioni e prestazioni pi32v2
restano da ricostruire. Il modello non comprende IR, effetti o routing audio.

## Decompilazione e limiti

Ghidra 12.2 con `virtualabs/ghidra-jieli`, più un disassembler indipendente
basato su `jvitkauskas/pi32v2-isa`. Versioni e hash sono fissati nel lock file.

| Campione | Funzioni per cui Ghidra ha emesso C | Fallimenti completi |
|---|---:|---:|
| G v1 | 260 | 0 |
| G v2 | 260 | 0 |
| B v1 | 260 | 0 |
| B v2 | 255 | 0 |
| MINI | 662 | 1 |

Questi numeri non sono copertura né prova di correttezza: anche una funzione
esportata può contenere istruzioni non comprese, p-code incompleto e
`halt_baddata`. Il recupero totale è 1697 funzioni esportate, non l'intero DSP.
I listati `.asm` sono scansioni lineari e comprendono dati interpretati come
possibili istruzioni; non sono un grafo di flusso completamente verificato.

Il punto d'ingresso e le copie RAM sono confermati dai byte. Pin, nomi delle
funzioni e algoritmi richiedono ulteriore ricostruzione e verifiche incrociate.
Non è stato installato alcun firmware, modificato alcun pedale o contattato
il servizio di telemetria dell'installer.
