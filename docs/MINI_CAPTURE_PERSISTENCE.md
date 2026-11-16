# Persistenza della capture A2 prima del primo preset

La sessione WebSerial reale `build/mini-desktop-real-03/connected-proof.json`
ha risposto `MODEL 'A2' layers=23 channels=3 fused=1 engine=A2L trim=0.0`,
`CLIST end current=-1 slots=15` e `PLIST end current=-1`. La capture è quindi
attiva senza uno slot persistente selezionato. Il codice originale dell'editor
spiega che `current=-1` comprende anche la capture incorporata di fabbrica.
Questa osservazione era in modalità `safe`; non prova audio funzionante.

Non sono stati eseguiti `CSAVE` o `CREAD` reali per questa preparazione.
L'audit offline, gli hash degli input e il piano ricavato dall'osservazione
precedente sono conservati in
[`mini-default-capture-persistence.json`](../research/mini-default-capture-persistence.json).
Il piano deve essere ricavato di nuovo da osservazioni fresche nella sessione
che eseguirà la prova.

## Perché è possibile salvare direttamente

Nel firmware G M5.71 originale, l'handler `CSAVE` a `0x0200C28C` controlla lo
slot `0..14`, il puntatore della capture corrente e la sua lunghezza. Non
richiede un precedente upload né uno slot corrente diverso da `-1`. I dati
iniziali a `0x0207593C` contengono il puntatore `0x02033C8C` e la lunghezza
`4892`. All'esito positivo, `0x0200C532` seleziona lo slot salvato.

Il blob originale è
[`embedded-0.a2l`](../analysis/firmware/m571_g_app/embedded-0.a2l):

- 4.892 byte, formato `A2L1`, nome `A2`, 23 layer, 3 canali;
- SHA256 `86f5ea91f8069180e30612bcaad5820b14a94dd6c2552290ca09253082238c47`;
- CRC32 dell'intero blob `2144df1c`; CRC finale little endian e content ID `77ac505b`;
- stessa sequenza completa, presente una sola volta a `0x02033C8C`, sia nella
  candidata v2 installata sia nella v3 preparata.

`CSAVE` costruisce un header `TKGC` da 40 byte e salva il payload. Lo store
originale confronta header e payload riletti prima di restituire successo.
La prova preparata richiede comunque un secondo confronto indipendente tramite
`CREAD`. Lo slot 0 occupa NOR `[0xDF000,0xE1000)`: il salvataggio è una scrittura
persistente della libreria, non una modifica temporanea. Si usa solo il primo
slot assente da un `CLIST` completo; nessuna capture preesistente viene scelta
come destinazione. La capture nuova viene intenzionalmente mantenuta.

## Contratto del piano e della rilettura

[`mini_capture_persistence.py`](../tools/mini_capture_persistence.py) contiene
solo funzioni pure. Non apre file, browser o dispositivi e non invia comandi.
`plan_capture(answers, blob)` richiede `MODEL` esatto e un `CLIST` completo e
coerente. Se `current=-1`, prepara una sola richiesta `CSAVE <slot> A2`.
Se A2 è già selezionata e i metadati corrispondono, prepara solo la rilettura.
Non sono previsti upload, `CLOAD`, cancellazioni, comandi audio o tentativi
automatici dopo un errore.

Il protocollo originale usa:

| Richiesta | Risposta |
| --- | --- |
| `CSAVE 0 A2` | `CSAVE ok 0 'A2' 4892 B` |
| `CREAD 0` | `CREAD 0 len=4892 crc=2144df1c id=77ac505b aux=0 fs=0 name='A2'` |
| `CREAD 0 <offset>` | `CREAD 0 <offset> <n> <crc8hex> <base64>` |

I chunk sono 51, agli offset `0,96,...,4800`: 50 da 96 byte e l'ultimo da 92.
Non esiste un parametro lunghezza nella richiesta originale. Il verificatore
controlla slot, offset, lunghezza, base64 canonico, ogni CRC e infine tutti i
byte contro il blob originale. Richiede inoltre `MODEL` invariato, lo slot
corrente corretto e i metadati delle altre voci `CLIST` invariati. Non legge
ogni payload preesistente e non lo dichiara verificato.

`aux=0` deriva dal trim zero e dall'assenza del livello di training opzionale:
il formatter `MODEL` e `CSAVE` leggono la stessa struttura a `0x01C26B48`;
`0x0200A5F6` impacchetta quei valori nell'header. Il parser richiede il `MODEL`
esatto senza suffisso `in=`, poi verifica nuovamente `aux` e `CLIST` dopo il
salvataggio. `fs=0` è il valore prodotto dal ramo capture di `CREAD` a
`0x020072CC`. Non è il sample rate 48 kHz contenuto nel file A2L.

## Integrazione con l'editor e limiti della prova

L'editor originale usa `CSAVE` al termine di `captureToSlot`, normalmente dopo
un upload. La libreria non espone un pulsante originale dedicato a salvare il
modello incorporato corrente. Il preambolo diagnostico del trial può usare la
stessa coda dell'editor per un solo `CSAVE` pianificato, conservando richieste
e risposte; non simula una funzione UI già presente.

Il metodo originale `pioSlotHead` invia `CREAD <slot>` e `pioSlotRead` invia
`CREAD <slot> <offset>`. Il pattern `isRead` dell'adapter MINI congelato richiede
invece tre argomenti numerici per `CREAD`, escludendo entrambe queste forme.
Il wrapper sperimentale deve quindi consentire esplicitamente soltanto
l'header e gli offset pianificati. I file congelati rimangono invariati e i
retry del lettore generico originale non vengono importati nel trial.

Il risultato di `verify_capture` attesta il transcript fornito, non la sua
provenienza hardware. Il lifecycle deve aggiungere porta, PONG reale, hash
dell'immagine derivato dall'installazione, trace e chiusura della connessione.
Una `CLOAD` immediata dello stesso slot può riusare il modello già in RAM:
non dimostrerebbe un caricamento a freddo. Neppure il confronto completo di
`CREAD` prova la ritenzione dopo power cycle o la qualità audio.

Verifica offline eseguita: 17 test in
[`test_mini_capture_persistence.py`](../tests/test_mini_capture_persistence.py),
compresi dati originali e candidata v3, slot occupati, risposte incomplete,
metadati alterati, chunk fuori ordine, CRC errati e base64 non canonico.
