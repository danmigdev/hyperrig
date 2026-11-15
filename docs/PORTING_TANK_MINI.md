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
   copie della banca preset; il backup sul nostro esemplare non è riuscito.
6. Header del SDK AC79 per studiare GPIO, registri ADC e DAC.
7. Modello A2-Lite in Float64 eseguibile sul PC e confrontato con il convertitore
   originale. È un riferimento numerico, non il runtime intero del firmware.
8. Tre routine native del G ricostruite in C e compilate pi32v2: due dot e
   testa a tre canali, con 1.660 confronti contro le istruzioni interpretate.
9. Percorso audio ALNK0 del MINI, tabella di configurazione, IRQ, callback,
   buffer e task ricostruiti. Vedere [TANK_MINI_AUDIO.md](TANK_MINI_AUDIO.md).
10. Identificazione BLE riuscita: l'esemplare risponde `TANK MINI_009`.

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
| Linker e memoria | Area applicativa/VM diversa; sezioni RAM vanno dimensionate sul target |
| Storage | BTIF del MINI occupa l'area chiamata OTP nelle immagini G/B |
| DSP | Tre routine intere compilabili e confrontate; parser nativo, layer, attivazioni, IR ed effetti da completare |
| Clock e prestazioni | 396 MHz nei metadati UltraRig non certifica il MINI |
| Installazione | Identità, flash ID, backup totale e recupero del singolo esemplare da validare |

Il formato A2L1 e il convertitore NAM sono già disponibili per lo sviluppo,
ma questo non rende il firmware stock MINI capace di eseguire il motore UltraRig.

## Sequenza concreta di completamento

1. Completare l'identificazione della revisione/flash e acquisire una lettura
   completa verificata dell'esemplare. L'identità BLE e il pacchetto ufficiale
   scaricato non soddisfano questo requisito.
2. Completare GPIO, tasti e mute; verificare sul dispositivo il percorso ALNK
   ricostruito e la sequenza di clock/codec a 48 kHz.
3. Ricostruire le funzioni DSP necessarie o implementarle con sorgenti disponibili;
   validare numericamente risultati, saturazioni e precisione delle capture.
4. Compilare un'applicazione MINI con linker e driver dedicati. Prima un percorso
   audio minimale, poi motore capture/IR e catena effetti.
5. Misurare underrun, latenza, RAM, clock stabile, consumi e comportamento al boot.
6. Solo dopo questi riscontri, preparare e provare installazione e ripristino.

L'identificazione BLE è l'unica verifica riuscita sull'esemplare. Non era
presente un collegamento USB; RtMidi non esponeva la porta BLE. La lettura
identità sul servizio proprietario è riuscita, mentre il tentativo successivo
di backup preset è fallito all'abilitazione delle notifiche. Non è stato
acquisito alcun backup completo, né installato alcun firmware.

```powershell
python -m hyperrig port-status
```
