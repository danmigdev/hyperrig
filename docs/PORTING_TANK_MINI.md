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
   copie della banca preset; il trasporto sul nostro esemplare è ancora da provare.
6. Header del SDK AC79 per studiare GPIO, registri ADC e DAC.
7. Modello A2-Lite in Float64 eseguibile sul PC e confrontato con il convertitore
   originale. È un riferimento numerico, non il runtime intero del firmware.

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

Segue una macchina a stati con tre elementi e combinazioni. L'interpretazione
come scansione dei tre footswitch è una **inferenza**. Assegnazione A/B/C,
polarità, pull-up, LED e tempi di debounce restano da confermare. Il profilo
non inventa valori per questi campi.

## Cambiamenti necessari nel firmware

| Parte | Perché il MINI richiede lavoro specifico |
|---|---|
| Board support | Tre footswitch; corrispondenza fisica e LED non verificati |
| Audio | Ingressi ADC, uscita DAC, mute, DMA e sample rate non ancora ricostruiti |
| Linker e memoria | Area applicativa/VM diversa; sezioni RAM vanno dimensionate sul target |
| Storage | BTIF del MINI occupa l'area chiamata OTP nelle immagini G/B |
| DSP | Riferimento A2-Lite Float64 disponibile; runtime intero, saturazioni, IR ed effetti da ricostruire |
| Clock e prestazioni | 396 MHz nei metadati UltraRig non certifica il MINI |
| Installazione | Identità, flash ID, backup totale e recupero del singolo esemplare da validare |

Il formato A2L1 e il convertitore NAM sono già disponibili per lo sviluppo,
ma questo non rende il firmware stock MINI capace di eseguire il motore UltraRig.

## Sequenza concreta di completamento

1. Identificare firmware/revisione e acquisire una lettura completa verificata
   della flash dell'esemplare, quando sarà collegato. Il backup preset della
   CLI non soddisfa questo requisito.
2. Completare la mappa GPIO con letture e prove dei tasti; individuare percorso
   audio, mute e periferiche dal disassembly e dal dispositivo.
3. Ricostruire le funzioni DSP necessarie o implementarle con sorgenti disponibili;
   validare numericamente risultati, saturazioni e precisione delle capture.
4. Compilare un'applicazione MINI con linker e driver dedicati. Prima un percorso
   audio minimale, poi motore capture/IR e catena effetti.
5. Misurare underrun, latenza, RAM, clock stabile, consumi e comportamento al boot.
6. Solo dopo questi riscontri, preparare e provare installazione e ripristino.

In questa sessione il proprietario ha confermato di possedere il pedale, ma
non era al PC. Nessuna delle verifiche hardware elencate è stata eseguita.

```powershell
python -m hyperrig port-status
```
