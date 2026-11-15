# Percorso audio TANK MINI 009 e differenze da UltraRig G

La ricostruzione della catena di chiamate identifica **ALNK0/I²S come percorso
audio principale di entrambi i campioni**. I driver ADC/DAC interni presenti
nel firmware MINI non bastano a identificare il percorso realmente usato.
L'identificazione qui deriva da inizializzazione, tabella di configurazione,
IRQ, callback e task che consumano gli stessi buffer.

Questi risultati sono statici. Non sono state misurate frequenze o tensioni,
né modificata la configurazione del pedale collegato.

## Riproduzione delle evidenze

```powershell
python tools/map_audio.py
```

Lo script verifica gli hash originali prima di decodificare, legge le tabelle
e controlla le destinazioni delle chiamate chiave con la tabella ISA. Genera
`analysis/native/audio-map.json`; una copia dei risultati è versionata in
[audio-map.json](../research/audio-map.json). Gli indirizzi citati sono CPU.
Gli header `WL82.h`, `gpio.h` e `iis.h` del SDK sono fissati nel lock.

## Catena del MINI

`0x020071CA` carica il nome `usr_audio_task`; `0x020071D4` passa la funzione
RAM `0x01C03F24` alla creazione del task. `0x020071E6` chiama l'inizializzazione
`0x0200715C`, che passa la configurazione `0x02035E90` a `0x02006F70`.
Quest'ultima azzera/configura ALNK0, base `0x00012E00`, e registra l'IRQ 11
con handler RAM `0x01C0374A`.

La configurazione contiene quattro record di canale da 16 byte, seguiti dai
parametri comuni. I due canali abilitati sono:

| Campo | Canale 0 | Canale 1 |
|---|---|---|
| Direzione ricostruita | uscita | ingresso |
| Codice direzione | 0 | 1 |
| Buffer | `0x01C1B230` | `0x01C1B630` |
| Callback | nullo | `0x01C03EEE` |
| GPIO dati | PA7 | PA8 |

I buffer occupano 1024 byte ciascuno. La callback del canale 1 salva l'indice
della metà pronta e sveglia il task con un semaforo. Il task seleziona gli
offset con `indice << 9`, azzera 512 byte di uscita e chiama `0x01C03A18` con
64 frame. Questo corrisponde a due slot di 32 bit per frame. All'ingresso del
percorso DSP viene osservata anche la trasformazione `word << 8`, poi shift
aritmetico destro di 7: il packing e lo scaling vanno rispettati nel port.

Il gruppo GPIO selezionato dal MINI è l'indice 1 nella propria tabella:
`[4,5,6,7,8,9,10]`, nell'ordine tre clock e quattro dati. G seleziona l'indice
0 nella sua tabella: `[7,8,9,10,4,5,6]`, nell'ordine quattro dati e tre clock.
Quindi i numeri del selettore **non vanno copiati da una struttura all'altra**,
anche se il risultato è lo stesso insieme di pin PA4–PA8 per i canali usati.
La corrispondenza elettrica sulla scheda resta da misurare.

## Frequenza e inizializzazione del codec

| Parametro osservato | MINI stock 009 | UltraRig G M5.71 v2 |
|---|---|---|
| Sample rate nominale | 44100, config +92 | 48000, istruzione `0x0200514C` |
| Registro ALNK LEN | 128 | 128 |
| Periodo elaborato dal task/modello | 64 frame | 64 frame per A2-Lite |
| Buffer DMA per canale | 1024 byte | 128 × 8 byte |
| Canale ingresso / uscita | 1 / 0 | 1 / 0 |

Il setter MINI `0x02006E58` contiene un ramo esplicito per 48000. Il ramo
`0x02006F2E` seleziona la famiglia di clock tramite `0x02006E36` e aggiorna
ALNK CON3. **Questo prova l'esistenza del codice, non che il codec del nostro
esemplare sia già configurato o validato a 48 kHz.** Il port A2-Lite dovrà
ricostruire l'intera sequenza di clock e codec, oppure includere una conversione
di frequenza verificata; cambiare soltanto il campo nominale non è una prova.

Prima del task audio, `0x02006DEC` inizializza il bus e invia 22 record da
4 byte dalla tabella `0x02035E35`. La routine `0x02006DCE` invia prima il byte
di indirizzo `0x36`; i GPIO candidati del bus sono PA1/PA2. Il modello esatto
del codec non è stato identificato. Il report conserva l'hash della tabella;
gli originali restano nei campioni locali.

## Conseguenze per HyperRig

Il port può conservare il confine di elaborazione da 64 frame osservato anche
nel MINI. Richiede un driver ALNK e una configurazione del codec specifici,
con gestione dei due buffer e conversione corretta dei campioni. I tre kernel
C ricostruiti sono indipendenti dalle periferiche e possono essere compilati
per la stessa ISA; manca ancora il motore completo che li colleghi.

Restano aperti mute analogico, livelli, frequenze effettive, ordine di avvio,
concorrenza tra IRQ/task e comportamento in underrun. Nessun indirizzo di
callback o buffer del G viene proposto come indirizzo valido del nuovo port.
