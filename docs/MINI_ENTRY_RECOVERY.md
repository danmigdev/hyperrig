# Recupero mediante footswitch all'ingresso dell'applicazione G

È possibile inserire un guard piccolo prima della prima chiamata del
firmware UltraRig G. Il componente in
[`firmware/mini/entry_recovery`](../firmware/mini/entry_recovery) occupa
**282 byte di codice**, senza BSS, dati da copiare, heap o dipendenze da
RTOS, GPIO helper, clock G e DSP. È assemblato e verificato offline;
**non è inserito nella candidata e non è stato eseguito sul MINI**.

La combinazione scelta è **tutti e tre i footswitch premuti prima
dell'accensione**. Non richiede di assegnare ai pin le etichette fisiche
A/B/C, ancora da confermare, e distingue il recupero dalle combinazioni
operative a due tasti. Se la combinazione viene rilevata, il guard scrive
la mailbox ROM e richiede il reset documentato. Negli altri casi conserva
il contesto e continua lo startup originale.

Questo può recuperare un'applicazione valida che si blocca **dopo** il
guard: si spegne e riaccende il pedale tenendo la combinazione. Non richiede
che il firmware bloccato elabori USB, né che un watchdog sia armato.
Un semplice reset del bus USB non equivale a riavviare la CPU del pedale.

## Punto d'innesto e ABI

| Punto G originale | Evidenza nei byte |
|---|---|
| `0x02000120` | Salto corto a `0x0200018A` |
| `0x0200018A` | `sp = 0x01C350B8`, sei byte |
| `0x02000190` | `ssp = 0x01C360B8`, sei byte |
| `0x02000196` | Prima chiamata, a `0x0200042E` |

Il preimage di dodici byte è:
`eeffb850c301edffb860c301`.
La proposta sostituisce soltanto questi dodici byte con un salto al
prefix e quattro NOP. Conserva entry, vettori e istruzioni vicine a
`0x02000120`, evitando di sovrascriverle per far spazio a un salto lungo.
Il formatter esistente non è stato modificato.

Il prefix ripete esattamente i due setup stack originali, salva i sedici
registri generali, PSR, RETS e RETI, chiama il controllo e, quando prosegue,
li ripristina prima del salto a `0x02000196`. In particolare **r0 torna
identico** e continua a indicare il contesto del bootloader. Le copie delle
estensioni boot assenti restano gestite dalla patch separata già esistente.

Il massimo frame aggiunto è 100 byte: 76 del prefix e 24 del controllo.
Sono considerate entrambe le interpretazioni di SP già discusse in
[MINI_ROM_STACK.md](MINI_ROM_STACK.md): intervallo sotto `0x01C350B8`,
oppure sotto `0x01C360B8` se SP è alias dello stack supervisor. Entrambi
rimangono nella RAM dell'applicazione G e lontani dalla mailbox. Il modello
non determina la modalità fisica attiva; riproduce i setup originali in
entrambe le interpretazioni.

Non vengono cambiate politica interrupt o modalità CPU. Lo SPL originale
esegue `cli` a `0x01C051C2` prima dell'handover `call r1` a `0x01C0528C`.
Il prefix assume questo ingresso SPL, senza supportare un salto arbitrario
da un task o da un IRQ. I GPIO helper G non sono utilizzabili qui: i loro
lock e dati di runtime non sono ancora inizializzati.

## GPIO e possibilità di falso riconoscimento

Il firmware MINI configura PA10, PA0 e PA3 a `0x02006096..60BA`; la
lettura a `0x0200A060` usa PORTA IN (`0x50004`). L'interpretazione active-low
è ricostruita nell'[audit pannello](MINI_PANEL_PORT.md). La disposizione
dei registri è corroborata dall'[header SDK WL82 fissato](../upstream/ac79-sdk-reference/include_lib/driver/cpu/wl82/asm/WL82.h).

Il controllo possiede soltanto la maschera `0x409`:

| Registro | Indirizzo | Operazione temporanea |
|---|---:|---|
| DIR | `0x50008` | Ingresso |
| DIE | `0x5000C` | Ingresso digitale abilitato |
| PU | `0x50010` | Pull-up abilitato |
| PD | `0x50014` | Pull-down disabilitato |

Prima di scrivere verifica che i tre DIR siano già ingressi. Se non lo
sono, ritorna errore senza scrivere GPIO. Questa scelta evita che un
successivo ripristino trasformi un tasto premuto in un'uscita pilotata.
OUT, DIEH, forza di pilotaggio e mux non vengono scritti. Le modifiche
usano read-modify-write; al ritorno vengono ripristinati soltanto i tre
bit posseduti, preservando i bit estranei correnti. Si richiede comunque
che nessun altro esecutore cambi questi pin durante il controllo.

Il codice controlla il readback della configurazione, attende 100000
iterazioni e richiede 32 campioni in cui tutti e tre i bit siano bassi,
separati da altre 100000 iterazioni. Il primo campione con un bit alto
fa proseguire lo startup. Sono contatori software, **non millisecondi
misurati**; non dimostrano un tempo di debounce fisico o continuità del
livello tra campioni. Non vengono usati REP, timer o variazioni del PLL.

Gli esiti della funzione callable sono 0 (combinazione assente), 1
(combinazione osservata), 2 (direzione iniziale o readback non valido).
Il prefix richiede esattamente 1 per il reset. L'esito 2 continua G:
evita una recovery accidentale dovuta a un errore di configurazione, ma
significa che **non si può fare affidamento sul guard in quello stato**.

Una lettura GPIO permanentemente zero può essere indistinguibile da tre
tasti premuti e portare alla ROM. Un ingresso bloccato alto può impedire
il recupero. Le prove dei pin devono quindi comprendere tasti rilasciati,
singoli, coppie e combinazione completa, non soltanto un caso positivo.

Il record HYC1 già persistito in
[mini-codec-hardware.json](../research/mini-codec-hardware.json) riporta in
ROM PORTA IN=`0x7FF`, DIR=DIE=`0xFFFF`, PU=PD=0. È un indizio utile per la
prova RAM: **non misura lo stato dopo lo SPL durante un avvio a freddo**.
Il vincolo sulla direzione e il tempo di assestamento in quel punto restano
da qualificare.

## Marker e reset

`reset.S` è separato dal controllo GPIO. Scrive esattamente i sedici byte
`usb_update_mode\0` a `0x01C7FD80`, esegue `csync`, legge `RST_CON` a
`0x10000`, conserva gli altri bit e imposta il bit 4. Esegue un secondo
`csync` e attende il reset.

La stringa è presente sia nell'app MINI a `0x0203FD2A` sia nello SPL a
`0x01C05710`. Lo SPL la copia a `0x01C0529A`; il suo reset a
`0x01C028F4..28FE` imposta proprio quel bit di RST_CON. Non viene usato un
indirizzo di funzione ROM ipotizzato e non si arma un watchdog.

Questa sequenza combina elementi documentati, ma il nuovo corpo marker +
RST_CON non è ancora stato provato fisicamente. Il soft-key dell'app MINI
utilizza una funzione P33 e i precedenti ritorni da ROM allo stock
cancellavano il marker: sono prove correlate, non una sostituzione della
nuova prova. Anche conservazione della mailbox e visibilità delle scritture
attraverso il reset devono essere confermate sul percorso scelto.

## Verifica e prova RAM proposta

```powershell
python -X utf8 firmware/mini/entry_recovery/verify.py
```

Il comando ricompila con l'assembler vendor e verifica i byte emessi:
636 casi, scritture entro gli intervalli ammessi, GPIO ripristinati,
contesto preservato, rami negativi e ordine marker/barriere/reset. I due
loop di attesa privi di effetti esterni sono conteggiati algebricamente;
non sono simulati clock, silicio, cache o rimbalzi. Il report completo è
[mini-entry-recovery.json](../research/mini-entry-recovery.json).

L'ELF `build/mini-entry-recovery/entry-recovery-audit.elf` è una fixture
XIP a `0x02078000`, **non un'applicazione o un plugin da caricare**. Tale
indirizzo è scelto per l'audit, non costituisce un'allocazione nel formatter.
Il linker accetta `--defsym HYPERRIG_ENTRY_GUARD_ADDRESS=...` per una futura
allocazione verificata dentro `app.bin`; vanno aggiornati CRC e cifratura.

Una successiva prova RAM può incorporare **solo `check.S` e `reset.S`** in
un nuovo plugin negli slot già consentiti, con stack privato e un protocollo
esplicito. `prefix.S` seleziona gli stack G fuori dagli slot ROM e non va
eseguito da un callback ROM.

1. Ingresso plugin senza GPIO; handshake e hash/readback del payload.
2. Comando di sola osservazione dei registri, poi comando separato per
   `hyperrig_mini_entry_recovery_check()`: valori prima/dopo, risultato,
   durata e stack devono essere registrati. La prova manuale dei tasti va
   coordinata con l'utente. Il loop completo può essere lento ai clock ROM:
   la durata va qualificata prima di usarlo in un comando con timeout breve.
3. Solo tramite comando distinto, chiamata deliberata del nuovo corpo
   marker/reset. Una risposta USB persa non prova il successo e non giustifica
   un retry automatico. Serve una nuova enumerazione `4C4A:8057` e identità
   SCSI `WL82` / `UBOOT1.00`.
4. Ritorno allo stock con il percorso già verificato; doppia lettura dei
   preset uguale al riferimento. Nessuna scrittura NVM è necessaria.

La prova RAM qualifica i GPIO e il reset nel contesto ROM. La correttezza
del prefix e del contesto resta coperta dall'audit statico; il cold handover
SPL, compreso DIR=input, richiede evidenza distinta e non va dichiarato
provato da un plugin USB.

## Effetto sul primo port completo

Il guard affronta precisamente il rischio dell'app G valida che entra e
poi si blocca in clock, driver, RTOS o DSP. Una volta qualificato può
offrire un recupero utile senza dover realizzare subito USB_KEY, mantenendo
la sostituzione integrale dell'applicazione MINI con quella G adattata.
L'evidenza offline attuale, da sola, non rimuove quel gate.

Non copre header invalido, entry o prefix corrotti, salto sbagliato,
scrittura NOR interrotta, SPL danneggiato o guasto GPIO. Il backup integrale
consente un ripristino soltanto se si riesce a raggiungere un trasporto
adatto. SPL e OTA conservati aumentano le opzioni ma il loro recupero da
un'app danneggiata non è ancora qualificato fisicamente. USB_KEY rimane
la possibile via indipendente da quei byte.

Prima di affidarsi al guard nel primo aggiornamento occorrono quindi le
prove indicate, integrazione con preimage esatto e validazione/readback
dell'intera area applicazione. La politica del writer, la conservazione
di SPL/OTA/dati e la gestione di un'interruzione rimangono controlli
separati. Questo lavoro non accede al dispositivo e non autorizza né
esegue un flash.
