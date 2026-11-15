# Probe ROM HyperRig sul TANK MINI

Il **15 novembre 2026** il TANK MINI ha eseguito il probe HyperRig dalla RAM
tramite la ROM AC791N. L'immagine è stata riletta e verificata prima del salto;
il plugin ha restituito un record di 64 byte con **8 casi DSP riusciti** e CRC
uguali ai risultati ottenuti interpretando i kernel originali del TANK-G.

L'evidenza fisica è riassunta in
[mini-hardware-rom.json](../research/mini-hardware-rom.json). La registrazione
locale originale è `analysis/hardware/mini-ram-bundle-run.json`, campi
`probe_session` e `probe_record`, sessione iniziata alle `17:20:43 UTC`.
Questa prova riguarda il plugin RAM, il ritorno alla ROM e i suoi comandi USB.
Non convalida l'avvio dell'applicazione dalla flash, il motore A2 completo o
l'ingresso/uscita audio. Backup NOR e ritorno al firmware stock hanno evidenze
separate e non sono attestati da questo documento.

## Build e immagine eseguita

I sorgenti sono in [firmware/mini/rom_probe](../firmware/mini/rom_probe/).
Il comando seguente compila e verifica gli artefatti offline; non apre il pedale:

```powershell
python -B -X utf8 tools/build_mini_rom_probe.py
```

Il [manifest di build](../research/mini-rom-probe.json) conserva hash dei
sorgenti, golden ricavati dalle istruzioni originali e risultati host:
33 casi di protocollo, 8 DSP, ASan e UBSan. I suoi campi
`hardware_execution_verified=false` descrivono l'ambito del builder e restano
separati dal rapporto della successiva prova fisica.

| Proprietà della build eseguita | Valore |
|---|---|
| File flat | `build/mini-rom/hyperrig-rom-probe-01c20000.bin` |
| Entry e inizio slot | `0x01C20000` |
| Fine slot esclusiva | `0x01C28000` |
| Payload caricato | 4928 byte |
| Occupazione con BSS | 6672 byte, fino a `0x01C21A10` escluso |
| Record | `0x01C219D0`, 64 byte |
| Build tag interno | `0x498A1779` |
| SHA-256 payload e rilettura ROM | `2f72aa15c30b99a1034ab027d9c92fae369a7dcd4db787e33c9f05360d7e2189` |
| SHA-256 ELF | `f86d34f7b8f66f4aeb69a80e5ae8203e410d59c0292a8431ac9ba06af883c4e8` |
| SHA-256 manifest usato nella sessione | `640e931497bd309ffda1cba2ea057139867abfe08c7bad58df9f9b609a864817` |

Il builder produce anche un'immagine per lo slot `0x01C28000`. L'esito fisico
del probe documentato qui riguarda esclusivamente lo slot `0x01C20000`.

## ABI e durata dei callback

La ROM chiama il primo byte del payload come una normale funzione C.
`r0` punta a tre word da 32 bit: callback di invio, callback di ricezione,
indirizzo della variabile ROM che contiene il puntatore all'handler.
Il probe copia il callback di invio per valore, azzera il proprio stato,
esegue il selftest, pubblica l'handler con `csync` e ritorna zero alla ROM.
Non conserva il puntatore temporaneo alla struttura dei servizi e non cambia
stack, stato degli interrupt o clock della ROM.

L'handler riceve un CBW da 31 byte e un buffer risposta scrivibile da 16 byte.
Restituisce 1 per i comandi gestiti e 0 per lasciarli alla ROM. Il comando
`FC60` riesegue il selftest e invia una risposta `HYR1`; `FD61` legge soltanto
lo slot del plugin, usando il callback ROM in blocchi di massimo 512 byte.
Il probe non inizializza SPI e non contiene operazioni di scrittura flash.
Framing e trasformazione dei trasferimenti sono descritti in
[MINI_RECOVERY.md](MINI_RECOVERY.md).

Nella prova fisica la risposta al salto è stata
`fb080000000000000000000000000000`; la risposta `FC60` è stata
`fc600000000848595231000000000001`: otto casi, stato zero, versione uno.
Il record successivo conferma l'esecuzione delle primitive sul processore.
La prova non determina la semantica dei ritorni d'errore del callback ROM o
il comportamento in presenza di trasferimenti parziali.

## Record verificato sul pedale

Tutte le word del record sono little endian; i marker sono byte ASCII.

| Offset | Dimensione | Campo | Valore osservato |
|---:|---:|---|---|
| 0 | 4 | Magic | `HYR1` |
| 4 | 4 | Versione | 1 |
| 8 | 4 | Base slot | `0x01C20000` |
| 12 | 4 | Dimensione slot | 32768 |
| 16 | 4 | Esecuzioni selftest | 2 |
| 20 | 4 | Errori | 0 |
| 24 | 4 | Casi DSP | 8 |
| 28 | 4 | CRC32 dot | `D4B493B4` |
| 32 | 4 | CRC32 head | `53F332DC` |
| 36 | 4 | CRC32 rechannel | `1910AD87` |
| 40 | 4 | Indirizzo record | `0x01C219D0` |
| 44 | 4 | Dimensione record | 64 |
| 48 | 4 | Build tag | `498A1779` |
| 52 | 4 | Azioni sulle periferiche audio/SPI/clock | 0 |
| 56 | 4 | CRC32 dei byte `[0,56)` | `E9AEFBA2` |
| 60 | 4 | Completamento | `DONE` |

Le due esecuzioni sono il selftest durante l'inizializzazione e quello richiesto
da `FC60`: non indicano due avvii del firmware. L'host ha verificato tutti i
campi, il CRC del record e i tre CRC DSP rispetto al manifest.

SHA-256 dei 64 byte ricevuti:
`7d66f4cc58ba174919f493ab505af478932a12a4706a5cc4288a65e0dd7de585`.

## Portata del risultato

I casi esercitano sei vettori per dot product a 16/32 bit, uno per la head a
tre canali con ring buffer e uno per l'espansione a tre canali. I golden
provengono dall'interprete delle istruzioni originali, non dall'uscita del C
HyperRig sul PC. Il confronto fisico verifica quindi queste primitive, il
codice generato dal compilatore e il percorso di comunicazione del probe.

Non sono stati eseguiti il caricamento e il processing di un modello A2
completo, lo streaming a blocchi di 64 campioni, ALNK/I2S, DMA audio, codec o
mute. Mancano inoltre misure del clock audio, latenza e qualità del segnale.
Il lavoro sui clock è documentato in [MINI_CLOCK.md](MINI_CLOCK.md); questa
prova non modifica i suoi requisiti di misura.

## Passo successivo e memoria

La capture A2 originale a 23 layer non entra negli slot ROM da 32768 byte.
L'ELF esistente `build/mini-boot/hyperrig-mini-dsp-link-probe.elf` contiene
11980 byte di codice e costanti, inclusa la capture da 4892 byte, oltre a
216768 byte BSS, 52 byte di record e 12288 byte riservati agli stack.
Gli arena del [probe DSP](../firmware/mini/boot/dsp_probe.c) sono sovradimensionati;
ridurli non basta. Dal layout pi32v2 di
[hyperrig_a2l.c](../firmware/src/hyperrig_a2l.c) e
[hyperrig_engine.c](../firmware/src/hyperrig_engine.c) risultano:

| Dato, in byte | A2 originale | Fixture sintetico a 3 layer |
|---|---:|---:|
| Capture serializzata | 4892 | 728 |
| Arena modello, risultato di `hyperrig_a2l_size()` | 6503 | 895 |
| Arena motore, risultato di `hyperrig_a2l3_size()` | 115111 | 9135 |
| Somma delle due query | 121614 | 10030 |

Ogni query include 7 byte per un eventuale allineamento iniziale; gli arena
A2 già allineati usano 6496 e 115104 byte. Le sole cronologie di ingresso
dei 23 layer occupano 111300 byte. Questi numeri sono derivati offline dal
layout target, non letti dal pedale; i contesti aggiungono 84 byte per il
modello e 1096 per il motore.

Il candidato ridotto è `synthetic()` in
[verify_engine_native.py](../tools/verify_engine_native.py): kernel/dilatazioni
`1/1`, `6/3`, `15/7`, head di quattro tap e campo ricettivo di 117 campioni.
Attraversa caricamento, rechannel, convoluzioni, attivazione, mix, residui,
somma e head. Il verificatore host lo confronta con le istruzioni originali
su sei blocchi da `1, 63, 64, 7, 31, 64` campioni; controlla anche reset e
ripartizione dei blocchi. Per un nuovo plugin occorre fissare i byte del
fixture e i relativi golden: il generatore riceve uno stato RNG.

Con il plugin esistente, gli oggetti layer/motore aggiuntivi e i suoi buffer,
il budget preliminare è 21118 byte, prima del nuovo wrapper, allineamenti e
stack. Non è la dimensione di un nuovo ELF già collegato. L'assembly esistente
mostra 1228 byte di stack per la catena interna di inizializzazione del motore;
vanno aggiunti chiamanti, ROM e interrupt. Il plugin eredita lo stack ROM e
la sua capacità residua non è ancora dimostrata. Il fixture ridotto non è la
capture A2 originale e non ne dimostra esecuzione completa, tempi reali o audio.
