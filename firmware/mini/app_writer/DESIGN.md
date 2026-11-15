# Writer applicazione MINI: progetto sospeso prima della ricezione ROM

Questo folder contiene un contratto proposto, **non un writer eseguibile**.
Non contiene un entry point, un driver NOR o un file ELF/bin. Il builder verifica
il piano e produce soltanto dati di revisione. Il reader HYRN già provato rimane
immutato e non acquisisce comandi di scrittura.

## Blocco osservato nelle fonti

La fonte fissata è `upstream/m-bootloader`, commit
`3ac7651a019fa44daba061b05654278496477b64`. In `src/loader_target.c:19`,
`params[1]` è interpretato come `int receive(void *, uint32_t)`. In
`src/loader.c:14`, il loader chiama la callback con chunk non superiori a512byte,
ignora il valore restituito e avanza comunque il puntatore. Questo dimostra
firma e convenzione usata dal loader; non dimostra una ricezione completa.

`docs/SPEC.md:835` dichiara esplicitamente sconosciuti i valori di ritorno e le
semantiche di trasferimento parziale/errore. Il codice disponibile non risolve
questa lacuna. I nostri plugin hanno provato invio e dispatch sul MINI; nessuna
prova acquisita qualifica `receive` per una pagina da programmare. Assumere
`return >= 0`, `return == 0` o `return == length` come successo sarebbe una scelta
senza evidenza. Un CRC corretto è un controllo sui byte osservati, non una prova
generale della semantica della callback o della fine di un trasferimento asincrono.

Per questa ragione l'implementazione capace di emettere `WREN`, erase o program
è rinviata. Il file `protocol-draft.json` è una proposta, modificabile prima di
qualificare una versione wire. Non viene aggiunto alcun profilo Windows capace
di inviare questi opcode, né un'opzione per ignorare il blocco.

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
3. FC7B consuma token/sequenza, ricontrolla preimage/status, WREN e WEL, poi
   esegue una sola erase20. WIP ha un limite finito e ogni byte del settore
   deve risultare FF. I limiti temporali effettivi restano da qualificare.
4. FB7C riceve una pagina completa più CRC in RAM; **non scrive flash**.
   FC7E deve confermare lo staging prima di FC7D. Solo FC7D può consumare la
   pagina, ricontrollare CRC e pagina ancora cancellata, verificare WREN/WEL
   e programmare una sola PP02 senza attraversare un confine da256byte.
5. Dopo ogni mutazione: WIP finito, WEL/status controllati, CS alto anche
   sull'errore, lettura completa e confronto dei byte. Un errore durante PP
   può aver già programmato parte della pagina: non si dichiara rollback
   automatico, né si ripete PP per nascondere un errore di trasporto.
6. FC80 verifica bitmap delle16pagine e CRC del settore completo. L'host
   rilegge il settore e confronta SHA256, quindi tutta l'area applicazione.
   Il prossimo settore richiede un nuovo arm esplicito.

La risposta OUT non include un pacchetto IN extra: il risultato viene letto
separatamente. Una risposta host fallita dopo un comando distruttivo implica
esito ambiguo, non autorizzazione a ritentare. ROM FB06/FD07/FB08 restano parte
del lifecycle RAM; non si devono esporre genericamente dal client writer.
Rifiuti di comandi legacy non devono ricadere nel gestore flash della ROM.

## Esperimento ricezione da progettare separatamente

Il passo minimo prima del writer è un plugin solo RAM, senza SPI, GPIO o
registri NVM: ricezione OUT di1..260byte in buffer inizializzato a pattern
distinto, canary prima/dopo, record del ritorno grezzo della callback, CRC e
successiva lettura IN di tutti i byte. Usare payload che differiscano dal
pattern iniziale e ripetere con lunghezze1/63/64/65/255/256/260. Servono tracce
host e record target correlati, verificando persistenza dei byte dopo il
ritorno e dopo il successivo comando.

Prove su richieste valide non qualificano da sole timeout, trasferimenti
corti, gestione degli errori o reentrancy. Questi casi richiedono ulteriori
evidenze dalla ROM o un esperimento esplicitamente isolato; non vanno
provocati dentro un writer armato. Questa proposta non esegue l'esperimento.

## Verifiche successive richieste

Quando l'ABI sarà chiarita: mock NOR con traccia di ogni byte SPI e fault
injection su ogni attesa; protezioni SR1/SR2; WEL non impostato; WIP bloccato;
CRC errato; ricezione corta; canary corrotti; token duplicati; limiti esatti
4000/81F00/82000; interruzione in ogni punto di PP; readback errato; CS sempre
rilasciato; nessuna WREN prima della pagina interamente ricevuta. ASan/UBSan
sul modello host e audit ELF di entrambi gli slot da32KiB con stack privato
e callback ROM sullo stack previsto sono richiesti, non ancora eseguiti.

Restano gate distinti: receive qualificata, writer qualificato, recupero
indipendente dimostrato anche con immagine valida che si blocca, codec/board e
immagine esatta approvati. Nessuno di questi gate viene abilitato dal builder
del contratto o dai CRC generati offline.
