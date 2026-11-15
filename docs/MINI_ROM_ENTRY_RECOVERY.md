# HYK1: verifica del recupero mediante footswitch in RAM

HYK1 qualifica separatamente le funzioni congelate `entry_recovery/check.S` e
`reset.S`. È un plugin diagnostico ROM nei due slot già adottati dal progetto;
non contiene il prefix applicativo G, non modifica clock o flash e non imposta
gli stack dell'applicazione. Il 15 novembre 2026 sono stati verificati sul MINI
i controlli dei tre tasti e il successivo reset esplicito alla ROM. Il rapporto
[mini-entry-recovery-hardware.json](../research/mini-entry-recovery-hardware.json)
conserva l'evidenza fisica separata dal manifest di compilazione. La guardia
durante l'avvio dell'applicazione e lo stato al cold handover restano non provati.

Nel checkout delle dipendenze fissate, i comandi di build offline sono:

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
Il manifest della prova rimane immutato, comprese le bandiere hardware false
che attestano il lavoro offline del builder. Le future revisioni del dispatcher
non cambiano questo pin storico: la copia usata per la verifica è archiviata in
`analysis/hardware/recovery-dispatcher-1d512173.py`, con lo stesso hash.
La sigillatura dei risultati non ricompila né rigenera gli artefatti eseguiti.

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
stack degli interrupt ROM ereditati. Non scrive esplicitamente SSP, ICFG,
IRQ, PLL o SFC; il registro SP attivo viene ripristinato dal trampolino.

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

## Prova fisica del 15 novembre 2026

È stato eseguito HYK1 nello slot A `0x01C20000`: payload di 2.472 byte,
occupazione RAM propria di 6.944 byte, inclusi stack e guardie. Il build tag è
`2348256965`; il prefix applicativo è assente dall'ELF.

| Artefatto della prova | SHA256 |
|---|---|
| Manifest | `eb6673b00dab2a8e0ca2141313b95a6441fb7bf882bb4a4e2076c99dfdd23516` |
| Payload HYK1 A | `02a875e24470c7168a74be3a89ee10be3cf324fb3ebe954302fb64332e48a88b` |
| ELF HYK1 A | `49977d1e7b84c5c20a62e3a6737f87f8e1e1a5a62976a432957f4251578ee3e9` |

Le tre sessioni consecutive di controllo hanno prodotto sei record: ogni
snapshot è seguito da un unico `check`. Il record precedente viene riletto
prima di riprendere la sessione; la catena dei quattro journal conserva gli
hash della fase precedente.

| Condizione | Sequenza check | PORTA.IN | IN & `0x409` | Esito |
|---|---:|---:|---:|---:|
| Tasti rilasciati, baseline | 2 | `0x7FF` | `0x409` | 0 |
| Tutti e tre premuti | 4 | `0x3F6` | `0` | 1 |
| Tasti nuovamente rilasciati | 6 | `0x7FF` | `0x409` | 0 |

Questo qualifica il gruppo PA10/PA0/PA3 attivo basso nel contesto ROM della
prova. Non assegna individualmente i nomi fisici A/B/C ai tre pin. Tutti i
sei record conservano gli otto registri di configurazione GPIO, le dodici
parole clock e le guardie dello stack. L'uso osservato dello stack privato è
60 byte, uguale al limite ricavato dal codice collegato; resta esclusa la
capacità dello stack degli interrupt ROM.

Gli hash dei tre record di controllo sono:

- baseline: `71a8daf5112d06d5a8012822345b0ec765916902a7b43372088f81d5024bd530`;
- premuti: `a3e10f0e0fb7f3b141a8c4249fb9866589fc782a317807c48ba3a4a28bc8335b`;
- rilasciati: `579849e0fec99e15ba565640ba64d76a4bb57d35b6553de2f2d89141949c6408`.

Il report include anche i tre snapshot e tutti i record completi, con CRC,
sequenze e hash. Sono stati ricontrollati offline con il validatore frozen,
insieme a 26 file fissati, all'ELF, al FD07 decodificato, alle nove letture dei
record nel trace e a 34 coppie comando/esito. I 909 casi C, gli 11 test client,
i 99 casi di istruzioni per slot e i controlli negativi restano risultati
già attestati dal manifest; non sono stati ricompilati per questo resoconto.

Il reset è stato una richiesta **esplicita FC81**, dopo il controllo a tasti
rilasciati, non un effetto automatico della pressione. L'unico comando,
associato alla sequenza 6 e al CRC del suo record, è stato inviato alle
`19:59:11.814222Z`. Ha prodotto l'errore di trasporto 121, quindi la sua
risposta non è la prova del completamento. La prova è la nuova enumerazione
della stessa istanza USB, passata dall'arrivo `19:54:53.5112400Z` a
`19:59:12.5150710Z`, seguita da una nuova INQUIRY `WL82 / UBOOT1.00`.
Non è stato riavviato l'hub né ripetuto FC81. Non è stata effettuata una
lettura del mailbox dopo il reset.

Dalla nuova sessione ROM è stato caricato, riletto e avviato una volta il
reset stock separato nello slot B, 26 byte, SHA256
`cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f`.
Anche il salto ha prodotto un errore di trasporto; il ritorno effettivo è
attestato dalla successiva identità `TANK MINI_009` e dai preset invariati:
due letture uguali, 1.942 byte, SHA256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`.
Il journal termina in fase `complete` alle `19:59:37.747148Z`.
È il settimo ritorno allo stock verificato, in questo caso senza riavvio
dell'hub. Nessuna scrittura NOR o variazione dei clock è stata eseguita.

I risultati qualificano il callable dei tasti e il percorso marker/reset
dalla ROM. Non qualificano il prefix applicativo, un avvio a freddo da flash
o il recupero da un'applicazione corrotta; i gate corrispondenti restano chiusi.

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
