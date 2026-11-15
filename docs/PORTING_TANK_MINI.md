# Porting HyperRig per TANK MINI

Il target è definito in `firmware/targets/tank-mini.json`. Lo stato reale è
`port-in-progress-not-flashable`: non esiste ancora un binario HyperRig
installabile. I risultati offline consentono di iniziare un port specifico,
non di etichettare un'immagine G/B come compatibile.

## Parti già adattate o ricostruite

1. Parser dell'aggiornamento ufficiale MINI, decodifica SFC e verifiche JLFS.
2. Mappa di memoria specifica, indirizzo di ingresso e copia del codice in RAM.
3. Protocollo USB-MIDI del MINI, distinto dal CDC testuale di UltraRig.
4. Lettura e interpretazione dei suoi 21 preset da 92 byte.
5. CLI per identificare il modello prima delle letture e confrontare due
   copie della banca preset; backup BLE e USB riusciti sul nostro esemplare.
6. Header del SDK AC79 per studiare GPIO, registri ADC e DAC.
7. Modello A2-Lite in Float64 eseguibile sul PC e confrontato con il convertitore
   originale. È un riferimento numerico, non il runtime intero del firmware.
8. Motore capture A2-Lite a tre canali/int32 ricostruito in C e compilato
   pi32v2: caricatore, bias, ingresso, layer dilatati, attivazioni, residuali
   e testa. 7.509 confronti contro le istruzioni interpretate, inclusi tutti
   i 23 layer A2. Memoria verificata con ASan/UBSan. Il parser e scheduler
   originali non sono emulati; il coordinatore C è un'implementazione propria.
9. Percorso audio ALNK0 del MINI, tabella di configurazione, IRQ, callback,
   buffer e task ricostruiti. Vedere [TANK_MINI_AUDIO.md](TANK_MINI_AUDIO.md).
10. Identificazione BLE riuscita: l'esemplare risponde `TANK MINI_009`.
11. Driver ALNK MINI e conversione Q23/QFin/QFout compilati e testati offline:
    [MINI_AUDIO_DRIVER.md](MINI_AUDIO_DRIVER.md). Avvio DMA subordinato a
    clock/codec, IRQ, cache e percorso analogico effettivamente pronti.
12. Startup/linker e due ELF diagnostici con simulazione della copia RAM/BSS:
    [MINI_BOOT.md](MINI_BOOT.md). Validatore ELF/container e dieci test contro
    layout, segmenti e copie incoerenti: [MINI_IMAGE.md](MINI_IMAGE.md).
13. Componenti platform, codec e runtime ricostruiti in parallelo:
    [MINI_PLATFORM.md](MINI_PLATFORM.md), [MINI_CODEC.md](MINI_CODEC.md),
    [MINI_RUNTIME.md](MINI_RUNTIME.md). Il probe `--bringup` collega i tre
    componenti e verifica sul PC il worker con il motore A2 e RAM fittizia.
14. Area applicativa MINI sperimentale composta dall'ELF con CRC verificati,
    preservando directory delle regioni e `cfg_tool.bin`. Non è un FWSC.
15. Backup preset BLE di 1.942 byte acquisito e validato con due letture uguali.
16. **Probe HyperRig eseguito in RAM sul MINI:** 8 vettori delle primitive DSP
    superati con record e CRC verificati. Vedere [MINI_ROM_PROBE.md](MINI_ROM_PROBE.md).
17. Ingresso USB nella ROM e ritorno al firmware stock verificati, con preset
    invariati. Lettore NOR PIO avviato, JEDEC `EB6014`, capacità dichiarata 1 MiB.
    Backup completo acquisito con due letture da 1 MiB identiche, CRC validi
    e prefisso firmware uguale allo stock 009. [MINI_RECOVERY.md](MINI_RECOVERY.md),
    [MINI_FLASH_BACKUP.md](MINI_FLASH_BACKUP.md).
18. Handover del bootloader e varianti XIP, selettore clock e candidato codec
    OSR64 ricostruiti offline. [MINI_HANDOVER.md](MINI_HANDOVER.md),
    [MINI_CLOCK.md](MINI_CLOCK.md). La frequenza audio fisica non è stata misurata.

## Tre ingressi candidati per i footswitch

Nel firmware stock 009, la funzione a indirizzo CPU `0x0200A060` legge tre
volte `0x00050004`. Nell'header `WL82.h`, `PORTA_BASE=0x50000` e il registro
`IN` è a offset 4. Il codice immediatamente successivo estrae:

```c
/* Espressioni ricostruite, NON un driver validato. */
input_0 = (porta_in >> 10) & 1;  /* candidato PA10 */
input_1 = (porta_in << 1) & 2;   /* candidato PA0  */
input_2 = (porta_in >> 1) & 4;   /* candidato PA3  */
```

La funzione `0x02006096` configura anche i pin 10, 0 e 3 tramite `0x02006074`
con argomento 1 e registra la scansione passando intervallo 10. Unità temporale
e semantica del parametro vanno ancora verificate.

Segue una macchina a stati con tre elementi e combinazioni. L'interpretazione
come scansione dei tre footswitch è una **inferenza**. Assegnazione A/B/C,
polarità, pull-up, LED e tempi di debounce restano da confermare. Il profilo
non inventa valori per questi campi.

## Cambiamenti necessari nel firmware

| Parte | Perché il MINI richiede lavoro specifico |
|---|---|
| Board support | Tre footswitch; corrispondenza fisica e LED non verificati |
| Audio | ALNK0, PA4–PA8 e DMA ricostruiti; clock/codec da adattare da 44,1 a 48 kHz, mute da confermare |
| Linker e memoria | Linker MINI e probe verificati offline; handover, budget e avvio fisico restano da provare |
| Storage | BTIF del MINI occupa l'area chiamata OTP nelle immagini G/B |
| DSP | Percorso capture a tre canali/int32 completo nel dominio verificato; restano frontend, altri profili, IR ed effetti |
| Clock e prestazioni | 396 MHz nei metadati UltraRig non certifica il MINI |
| Installazione | Identità, JEDEC e backup totale verificati; recupero da flash corrotta e installazione ancora da validare |

Il formato A2L1 e il convertitore NAM sono già disponibili per lo sviluppo,
ma questo non rende il firmware stock MINI capace di eseguire il motore UltraRig.

## Sequenza concreta di completamento

1. Usare il backup integrale verificato dell'esemplare per progettare e provare
   il recupero indipendente dall'applicazione. Il ritorno dalla RAM allo stock
   integro è riuscito; una flash cancellata o corrotta non è stata ripristinata.
2. Completare GPIO, tasti e mute; verificare sul dispositivo il percorso ALNK
   ricostruito e la sequenza di clock/codec a 48 kHz.
3. Ricostruire le funzioni DSP necessarie o implementarle con sorgenti disponibili;
   validare numericamente risultati, saturazioni e precisione delle capture.
4. Integrare i componenti e i probe già compilati in un'applicazione MINI con
   clock, codec, IRQ e scheduling audio verificati. Poi motore capture/IR e
   catena effetti; gli ELF diagnostici da soli non sono firmware installabili.
5. Misurare underrun, latenza, RAM, clock stabile, consumi e comportamento al boot.
6. Solo dopo questi riscontri, preparare e provare installazione e ripristino.

Sul dispositivo sono riuscite identificazione e lettura dei preset via BLE.
Una nuova connessione ha superato il precedente errore di sottoscrizione e
restituito due banche identiche: 1.942 byte, SHA-256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`.
RtMidi continua a non esporre il MINI; non è stata identificata una sua
interfaccia USB utilizzabile. Il backup completo e il recupero tramite ROM
restano da verificare. Nessun codice HyperRig è stato eseguito sul pedale.

```powershell
python -m hyperrig port-status
```
