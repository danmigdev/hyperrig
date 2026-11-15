# HYRX: osservatore della ricezione ROM in sola RAM

HYRX registra un callback e usa soltanto RAM propria e i servizi USB forniti
dalla ROM. Non contiene SPI, GPIO, reset, accesso NOR o scritture di registri.
Non cambia i gate del writer. Entry e handshake non chiamano `receive`.

Il plugin è separato da HYC1/HYC2/HYRN e viene collegato negli slot
`0x01C20000` oppure `0x01C28000`, con estensione massima 32 KiB. Tutto lo stato
privato è inizializzato esplicitamente; non si presume BSS fresca. Le callback
rimangono sullo stack entrante della ROM. Il piccolo uso di stack del codice
generato va distinto dalla capacità e dal consumo interno della ROM, ignoti.

| CDB | Direzione | Campi e risposta |
|---|---|---|
| FC82 + FF14 | IN16 | Echo, HYRX, versione1, flags0, base BE32, span32768 BE32 |
| FC83 | IN16 | seq BE16@2, lunghezza BE16@4, nonce BE32@6, CRC32 BE@10, poison seed@14, FF@15 |
| FB84 | OUT1..260 | seq BE16@2, nonce BE32@4, lunghezza BE16@8, FF6@10; nessuna risposta IN nello stesso comando |
| FD85 + FF14 | IN512 | Record LE descritto in `rom_receive.h`, CRC32 a504 e DONE a508 |

Risposta FC83: echo@0, HYRX@2, seq BE16@6, errore BE32@8,
lunghezza BE16@12, armed boolean@14, versione1@15. Il CBW deve contenere firma
USBC, LUN0, CDB16, direzione esatta e numero di byte esatto. Un comando privato
malformato viene consumato/rifiutato, senza chiamare `receive` per drenarlo:
può restare una fase USB incompleta e richiedere recupero. I comandi legacy
flash non passano alla ROM. Solo FB06/FD07/FB08 e SCSI standard sono delegati.

Gli stati sono idle → armed → receiving → returned, oppure fault persistente.
Sequenza e nonce evitano invii accidentali duplicati; non sono autenticazione.
FB84 consuma l'arm prima della callback. Se questa non ritorna, il plugin non
può imporle un timeout: l'host deve registrare l'ambiguità e non ritentare.

Il buffer è inizializzato al pattern `seed XOR (indice*73+0xA5)` troncato a8bit,
con 16 byte di canary per lato. Il client richiede un payload diverso dal
pattern in ogni posizione. Conserva risultato grezzo della callback, CRC,
conteggio dei byte diversi dal pattern e copia dei dati. Quel conteggio non
è presentato come un numero di byte ricevuti restituito dalla ROM.

FD85 ricampiona i dati, i guard e il CRC. Due record possono differire soltanto
nel contatore campioni a92 e nel CRC finale. Una modifica tardiva rende la
sessione fallita. Due campioni stabili rimangono un'osservazione finita:
non dimostrano che la callback sia sincrona, che DMA/cache siano generalmente
coerenti o che i casi di errore abbiano una particolare convenzione.

A96/100/104 il record contiene i valori dei puntatori `send`, `receive` e
`handler_slot` forniti dalla ROM. Il plugin li converte a u32 senza leggere
altro codice o memoria. Nei test su host a64bit sono soltanto i32bit bassi di
puntatori del processo, non indirizzi ROM. Il parser non presume una mappa
degli indirizzi ROM e non introduce comandi per leggerla.

`MiniReceiveSession.receive_once()` invia FC83, un solo FB84 e, se i dati e il
ritorno non risultano anomali, due FD85. Un ritorno negativo, un valore diverso
da quello atteso esplicitamente, un dato parziale, un record mutato o un errore
di trasporto fermano la sessione. Senza un valore di ritorno atteso derivato da
evidenza precedente, la prima osservazione valida chiude comunque la sessione:
non viene dedotta una convenzione di successo. Una successiva sessione può
usare il valore osservato come controllo di coerenza, senza qualificare il
writer o la semantica generale della callback.

Il builder esegue test C con ASan/UBSan: tutti i prefissi parziali da0a259 byte,
lunghezze1/63/64/65/255/256/260, ritorni grezzi diversi, corruzione dei guard,
scrittura tardiva, comando duplicato/malformato e mancato ritorno simulato con
`longjmp`. Il test non provoca un timeout USB reale. I test Python usano solo
trasporti finti, anche per Windows. Import e CLI predefinita non enumerano
dispositivi né aprono porte. Solo il costruttore esplicito del trasporto apre
un disco ROM già identificato dal chiamante.
