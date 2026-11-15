# HYK1: verifica del recupero mediante footswitch in RAM

HYK1 qualifica separatamente le funzioni congelate `entry_recovery/check.S` e
`reset.S`. È un plugin diagnostico ROM nei due slot già adottati dal progetto;
non contiene il prefix applicativo G, non modifica clock o flash e non imposta
gli stack dell'applicazione. Questa versione è verificata offline: l'esecuzione
fisica dei tasti e il ritorno alla ROM richiedono un rapporto hardware distinto.

Il build riproducibile è:

```powershell
python -X utf8 tools/build_mini_rom_entry_recovery.py
python -X utf8 tools/probe_mini_entry_recovery.py
```

Il primo comando compila e testa; il secondo mostra soltanto il protocollo,
senza cercare o aprire dispositivi. Il manifest congelabile è
`research/mini-rom-entry-recovery.json`: include build tag, hash di tutte le
dipendenze e dei due file `build/mini-rom-entry-recovery/*.bin`. Il trasporto
condiviso è vincolato allo SHA256
`1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8`.

## Operazioni esplicite

Ogni CDB privato è di 16 byte, con padding `FF`, direzione IN, LUN 0. Gli interi
negli argomenti CDB sono big endian. L'infrastruttura ROM usa inoltre soltanto
INQUIRY e gli opcode RAM FB06/FD07/FB08 già verificati.

| CDB | Argomenti dopo opcode | Risposta | Effetto |
| --- | --- | --- | --- |
| FC74 | nessuno | 16 byte, `HYK1`, versione 1, slot | Identità; nessuna lettura periferica |
| FC75 | nessuno | 16 byte + record tramite FD77 | Due snapshot passivi di PORTA e clock |
| FC76 | sequenza snapshot + CRC32 record | 16 byte + nuovo record | Un solo controllo esplicito PA10/PA0/PA3 per snapshot valido |
| FD77 | sequenza corrente | record di 256 byte | Espone il record corrente |
| FC81 | sequenza + CRC32 + `ROM!` | nessuna risposta promessa | Richiesta esplicita marker/reset, una sola volta |

Sequenza e CRC impediscono riuso accidentale di uno snapshot precedente;
`ROM!` distingue il comando distruttivo per la sessione. **Non sono
autenticazione.** FC76 non invia FC81, nemmeno quando rileva tutti i tasti
premuti. Nessun errore avvia un reset automatico.

Il record, descritto in `rom_entry_recovery.h`, comprende build tag e sequenza,
esito del controllo, snapshot dei nove registri PORTA e di dodici parole clock,
verifica dei registri ripristinati, guardie dello stack, CRC32 e terminatore
`DONE`. Il parser verifica anche la coerenza interna delle bandiere e degli
esiti; un CRC valido da solo non basta. La variazione del registro IN è ammessa:
i footswitch possono cambiare durante una lettura. Gli altri otto registri
PORTA devono restare identici, anche al di fuori dei tre bit interessati.

Gli esiti del callable sono 0 (combinazione non mantenuta), 1 (tre ingressi
bassi durante tutti i campioni), 2 (direzione iniziale o configurazione non
accettata). Gli status diagnostici sono -3 per esito 2, -6 per configurazione
GPIO cambiata, -7 per guardie stack, -8 per clock cambiati, -9 per un ritorno
imprevisto dal callback reset e -10 per un valore sconosciuto del callable.

## Integrazione del client

`MiniEntryRecoverySession` riusa `MiniRamSession` e il profilo Windows
`ram-entry-recovery`. Il chiamante fornisce trasporto, slot e build tag letti
dal manifest verificato. La procedura autorizzata dal runner è:

1. Provare che lo slot sia libero tramite la cronologia della sessione ROM.
   INQUIRY da sola non dimostra che nessun plugin stia usando quello slot.
2. `upload_only(image, expected_sha256=...)`, poi `verify_and_start(...)`.
   Il secondo metodo confronta FD07 decodificato prima dell'unico FB08 e
   richiede l'identità FC74. Non effettua snapshot o controlli dei tasti.
3. Chiamare `snapshot()`; soltanto uno snapshot valido con i tre pin già input
   abilita `check()`. Ogni `check()` consuma lo snapshot prima dell'I/O, anche
   se la risposta viene persa. Per un nuovo controllo serve `snapshot()`.
4. Salvare record e risultati. Un controllo con tasti rilasciati e uno con i
   tre tasti premuti permettono di distinguere le due condizioni fisiche.
5. Solo per la prova esplicita del ritorno alla ROM, catturare l'arrivo USB
   precedente e chiamare `request_rom_reset_once()`. Questa chiamata rende la
   sessione terminale **prima** dell'I/O. Non ritentare FC81.

`request_rom_reset_once()` non dichiara mai completato il reset: persino una
risposta USB valida potrebbe appartenere alla precedente sessione ROM. Il
runner deve osservare una nuova enumerazione USB con
`DEVPKEY_Device_LastArrivalDate` successiva, poi una nuova INQUIRY
`WL82 / UBOOT1.00`. Un eventuale riavvio dell'hub va registrato separatamente:
non prova che FC81 abbia causato un reset CPU. Un errore di trasporto successivo
all'invio è ambiguo, non autorizza un secondo invio. Il runner conserva i log e
gestisce autonomamente il ritorno successivo al firmware.

## Codice e limiti qualificati

Entrambi gli ELF sono interamente contenuti nel rispettivo slot da 32 KiB,
`0x01C20000` o `0x01C28000`. Il record e tutte le variabili appartengono allo
slot. Lo stack privato è di 4096 byte, con 32 byte di guardia per lato. Il
trampolino preserva lo stack ROM e RETS; le callback di trasmissione sono
chiamate dopo il ritorno allo stack ROM. L'audit delle chiamate del codice
collegato ricava un massimo di 60 byte sullo stack privato, escluso l'eventuale
stack degli interrupt ROM ereditati. Non cambia SSP, ICFG, IRQ, PLL o SFC.

Il callable imposta input/digitale/pull-up solo su PA10/PA0/PA3, rifiuta prima
di scrivere se trova un pin configurato output, poi ripristina la configurazione
selezionata. I ritardi sono cicli di istruzioni conteggiati, senza conversione
in millisecondi: clock ROM e durata reale del comando restano da misurare. Il
reset scrive `usb_update_mode\0` a `0x01C7FD80`, esegue `csync`, imposta tramite
RMW il bit 4 di `RST_CON` a `0x00010000`, esegue `csync` e attende. Se il reset
non viene consegnato rimane in attesa; non esiste un salto arbitrario alla ROM.

Le verifiche sono distinte:

- 909 casi del dispatcher C eseguiti su host con ASan/UBSan e callback simulate;
- 11 test del client su un trasporto simulato, compreso upload/readback/jump,
  perdita di risposta, consumo dei token e impossibilità del retry reset;
- 99 casi per slot sul modello delle istruzioni effettivamente collegate di
  `check.S` e `reset.S`, più controllo del trampolino e dei limiti ELF;
- record malformati e ELF fuori contratto rifiutati.

I test host usano uno stack osservato sintetico solo nei fixture del parser.
Non costituiscono misure di stack, GPIO o reset sull'hardware.

## Handover SPL e futuro prefix applicativo

Nelle interfacce analizzate non è stato trovato un percorso supportato e
verificato per osservare in sola RAM lo stato esatto del GPIO al passaggio
**cold SPL → applicazione**. La ROM USB precede un percorso diverso; le
funzioni USB dell'applicazione stock arrivano dopo l'inizializzazione delle
periferiche. Il punto SPL `call r1` a `0x01C0528C` usa l'entry letta dalla flash;
non è stato identificato un hook RAM di osservazione a quel punto.

Eseguire manualmente una copia SPL dalla ROM richiederebbe qualificare prima
ABI, proprietà della RAM oltre i due slot, SFC/cache e dismissione USB; non
equivarrebbe comunque a un avvio a freddo. Il percorso OTA è un ABI distinto
e non offre di per sé tale osservazione. Questi sono limiti delle evidenze
disponibili, non una prova che nessun altro metodo possa esistere.

Una futura revisione del **prefix applicativo**, separata da questo probe,
può salvare il contesto e poi impostare permanentemente `PORTA.DIR |= 0x409`
prima di richiamare il callable congelato. Nel port completo quei tre pin sono
foot-switch e la successiva inizializzazione li vuole input: il callable
salverà e ripristinerà quindi una direzione già input, senza riattivare output
contro un tasto premuto. Questa policy elimina la dipendenza dalla direzione
iniziale sconosciuta al cold handover; non richiede di fingere che lo stato ROM
sia lo stato SPL. Il probe ROM mantiene invece il rifiuto degli output e il
ripristino completo. La presente build non implementa né collega il prefix.

La futura guardia d'entry può recuperare un'immagine valida che si blocchi dopo
averla eseguita. Danni a header, entry o guardia stessa restano un caso diverso;
la prova HYK1 non dimostra un recupero universale di ogni app corrotta.
