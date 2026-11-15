# Writer applicazione MINI: implementazione con mutazioni target disabilitate

Questo folder contiene il protocollo HYW1, il driver PIO separato e il core
del writer. Il target iniziale ha **gate di mutazione costante zero**: FC7B e
FC7D non possono raggiungere WREN attraverso il dispatch. Il reader HYRN già
provato rimane immutato. I test host abilitano le mutazioni esclusivamente su
una NOR in memoria; la stessa macro è vietata quando si compila il target.

Il comando `python tools/build_mini_app_writer.py --build-locked` compila due
payload RAM da 32 KiB massimi, esegue i test e verifica il gate zero negli ELF.
La CLI predefinita controlla soltanto il piano locale. Non esiste un client
writer hardware, un'opzione force o una modalità target abilitata. Il piano
viene ricontrollato contro candidata, backup completo e rollback prima del
report; gli hash di tutti i 126 settori e i CRC delle 2.016 pagine sono inclusi.

## Evidenza ROM e limite ancora esplicito

La fonte fissata è `upstream/m-bootloader`, commit
`3ac7651a019fa44daba061b05654278496477b64`. In `src/loader_target.c:19`,
`params[1]` è interpretato come `int receive(void *, uint32_t)`. In
`src/loader.c:14`, il loader chiama la callback con chunk non superiori a512byte,
ignora il valore restituito e avanza comunque il puntatore. Questo dimostra
firma e convenzione usata dal loader; non dimostra una ricezione completa.

`docs/SPEC.md:835` dichiara esplicitamente sconosciuti i valori di ritorno e le
semantiche di trasferimento parziale/errore. Il codice disponibile non risolve
questa lacuna generale. Assumere
`return >= 0`, `return == 0` o `return == length` come successo sarebbe una scelta
senza evidenza. Un CRC corretto è un controllo sui byte osservati, non una prova
generale della semantica della callback o della fine di un trasferimento asincrono.

Successivamente HYRX ha osservato sul MINI un singolo OUT da 260 byte,
ritorno grezzo 260, dati esatti e due record stabili con canary integri. I
record acquisiti e il manifest eseguito sono fissati nel rapporto del writer.
I callback osservati sono send `0x01E008E4`, receive `0x01E0089A` e handler slot
`0x01C01264`: l'entry di questo target rifiuta valori diversi prima di SPI.
La prova non qualifica errori, durata generale del buffer o sincronicità.

Per ridurre questa dipendenza il writer riceve in un'arena con guard, esige il
ritorno 260 osservato e copia la pagina in un **secondo buffer congelato**.
Verifica il CRC della copia, espone esattamente quei 256 byte via FD87 e
richiede un comando FC7D separato dopo l'echo. L'host dovrà confrontare tutti
i byte prima di FC7D. PP usa soltanto la copia congelata: scritture tardive
nel precedente buffer RX non cambiano la sorgente programmata. Guard e CRC
della copia sono ricontrollati prima di WREN; ogni esito incoerente rifiuta.

## Limiti del futuro writer

L'unico intervallo fisico ammesso è `[0x4000,0x82000)`: 126settori da4096byte,
16pagine da256byte ciascuno. Un controllo deve precedere qualunque calcolo del
comando a24bit: `address >= start`, `address < end`, lunghezza positiva e
`length <= end-address`. Anche somma con overflow, settore disallineato,
pagina oltre il settore e indirizzi CPU/XIP devono essere rifiutati.

Restano esclusi SPL/configurazione iniziale, VM completa con OTA/request,
BTIF, USR e key_mac. Il piano di rollback deve riferirsi al backup completo di
questa unità, non a un FWSC generico. L'ordine con settore header per ultimo
non rende l'installazione atomica e non sostituisce un recupero indipendente.

Prima del primo accesso distruttivo occorrono JEDEC esatto `EB6014`, capacità
1MiB, stato WIP/WEL coerente e nessuna protezione. La SPEC §3.4 documenta per
questa famiglia SR1 `0x7C` e SR2 `0x40`: il writer deve **rifiutare**, non
azzerare, protezioni attive. Non deve scrivere SR1/SR2, modificare QE o tentare
una sequenza di sblocco. La configurazione volatile PIO va derivata dal reader
MINI; il suo init non va sostituito dall'init generico upstream, che modifica
clock e può modificare registri di stato NOR.

## Sequenza proposta HYW1

Gli opcode e i campi sono descritti esattamente in `protocol-draft.json`.
Tutti i CDB sono da16byte, con interi BE e padding inutilizzato `FF`; il CBW
deve dichiarare direzione e lunghezza esatte. I token sono contatori monouso,
non autenticazione. Un errore rende invalida l'autorizzazione a mutare; nessun
retry automatico, resume implicito o comando che cancella l'errore.

1. Entry/FC78 registrano e identificano il plugin senza MMIO. FC79 è un init
   esplicito, con JEDEC/status letti e nessuna WREN.
2. L'host legge il settore e verifica SHA256 contro il piano. FC7A rilegge
   tutti4096byte e confronta il CRC32 del preimage prima di armare quel solo
   settore. CRC32 non sostituisce il confronto SHA256 dell'host.
3. Prima di qualsiasi WREN, anche dell'erase, occorre già una prima pagina
   ricevuta, congelata ed esposta con FD87 per il confronto dell'host.
   Nel percorso operativo provato sul mock, FC7B consuma token/sequenza,
   ricontrolla preimage/status, WREN e WEL, poi
   esegue una sola erase20. WIP ha un limite finito e ogni byte del settore
   deve risultare FF. I limiti temporali effettivi restano da qualificare.
4. FB7C riceve una pagina completa più CRC in RAM; **non scrive flash**.
   È ammesso anche prima dell'erase, per verificare staging/echo nel target
   bloccato. FC7E deve confermare lo staging e FD87 deve essere confrontato
   byte per byte dall'host prima di FC7D. Solo FC7D può consumare la
   pagina, ricontrollare CRC e pagina ancora cancellata, verificare WREN/WEL
   e programmare una sola PP02 senza attraversare un confine da256byte.
5. Dopo ogni mutazione: WIP finito, WEL/status controllati, CS alto anche
   sull'errore, lettura completa e confronto dei byte. Un errore durante PP
   può aver già programmato parte della pagina: non si dichiara rollback
   automatico, né si ripete PP per nascondere un errore di trasporto.
6. FC80 verifica bitmap delle16pagine e CRC del settore completo. L'host
   rilegge il settore e confronta SHA256, quindi tutta l'area applicazione.
   Il prossimo settore richiede un nuovo token. La sequenza riparte da 1
   soltanto sotto quel nuovo token; FD87 usa la sequenza dello staging,
   mantenuta anche se un successivo erase avanza la sequenza corrente.

Il target iniziale rifiuta erase/program prima di ogni operazione distruttiva.
STAGE/echo dopo ARM restano operazioni reali in RAM, senza simulare un erase.

La risposta OUT non include un pacchetto IN extra: il risultato viene letto
separatamente. Una risposta host fallita dopo un comando distruttivo implica
esito ambiguo, non autorizzazione a ritentare. ROM FB06/FD07/FB08 restano parte
del lifecycle RAM; non si devono esporre genericamente dal client writer.
Rifiuti di comandi legacy non devono ricadere nel gestore flash della ROM.

## Record e stack

FD88 restituisce 128 byte LE di stato già raccolto, senza leggere nuovamente
la NOR. Il record contiene magic HYW1, versione, base/tag, fase/errore,
token/sequenza, settore/pagina, CRC preimage/target/pagina/ultima lettura,
JEDEC, SR1/SR2, contatori WREN/erase/PP/letture/poll, ritorno receive, guard,
bitmap pagine, staged/echoed e guard/uso osservato dello stack. Gate zero a116,
CRC32 dei primi120 byte a120 e DONE a124. FC7E non cancella errori persistenti.

Il lavoro NOR usa lo stack privato da 4 KiB con guard, tramite il bridge
pi32v2 già verificato. Le callback USB rimangono sullo stack originale ROM.
Gli ELF devono avere un solo segmento RAM nello slot, entry al primo byte,
nessun simbolo irrisolto e nessuna sovrapposizione fra codice, stato, record e
stack. L'audit automatico verifica anche i byte esatti del bridge e il gate
zero. La disponibilità dello stack interrupt della ROM resta fuori da questa
prova statica; non viene dichiarata esecuzione hardware del writer.

## Verifiche eseguite e rimanenti

I test C con ASan/UBSan coprono installazione completa di un settore ai due
estremi dell'area, protezioni SR1/SR2, WEL assente/persistente, WIP bloccato,
CRC errato, tutte le 260 lunghezze di ricezione corta, guard corrotti,
token/sequenze duplicati, limiti 4000/81F00/82000, PP parziale, readback errato
e isolamento del buffer congelato. Un modello SPI distinto inietta timeout
su ciascuno dei 544 byte della sequenza init/status/WREN/erase/program/read:
CS viene sempre rilasciato e una transazione fallita non viene ritentata.
Il test con gate zero verifica staging/echo e rifiuto erase senza WREN.

Il limite PIO è 32.768 poll per byte; WIP ha 65.536 campioni massimi, con
256 iterazioni di attesa fra campioni occupati. Sono limiti finiti, non una
misura temporale certificata. La compatibilità con i timeout host e i tempi
fisici di erase/program richiede revisione prima del build abilitato.

Root gestisce i gate attuali: recupero con footswitch scelto dall'utente,
codec/board e candidata esatta, quindi revisione del build abilitato. Non si
aggiungono prerequisiti USB_KEY, cablaggi GPIO o nuove approvazioni di progetto.
Il builder non promuove la readiness hardware e non esegue comandi al MINI.
