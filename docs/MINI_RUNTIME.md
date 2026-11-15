# Runtime IRQ/audio HyperRig per TANK MINI

Il componente in `firmware/mini/runtime/` collega il callback ALNK al worker
che esegue il motore a blocchi di 64 campioni. Compila per pi32v2 e dispone
di prove host con buffer e registri simulati. **Non è stato eseguito sul
pedale**: ownership DMA, coerenza cache, latenza IRQ e tempo DSP rimangono
requisiti hardware aperti. Il report conserva tutti questi esiti a `false`.

## Evidenze e scelta del protocollo

Il verificatore ricontrolla SHA-256 del FWSC MINI_009, decodifica `flash.bin`
e confronta l'area applicativa locale. Il report registra hash e indirizzi
dei tre frammenti stock:

| Frammento | Comportamento osservato |
|---|---|
| IRQ11 `0x01C0374A..0x01C037DC` | Salva PSR/RETS/RETI e r0..r5, legge pending/half, callback RX, ACK, `csync; rti` |
| Callback `0x01C03EEE..0x01C03F24` | Scrive il byte half a `0x01C1B22C`, chiama post del semaforo a `0x02044D44` |
| Task `0x01C03F24..0x01C03FB4` | Attende a `0x020456F8`, seleziona offset `half<<9`, chiama DSP `0x01C03A18` con 64 frame |

La mappa IRQ ALNK=11 e la tabella ISR `0x01C7FE00` sono confermate anche
dall'[header SDK fissato a commit](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/asm/hwi.h).
HyperRig usa stato e buffer propri; non richiama task, semafori o indirizzi
di dati dello stock.

Ogni nuova metà completata sostituisce la finestra di disponibilità della
precedente. Per questo il runtime mantiene **un solo evento pendente**,
un contatore di sequenza e un worker attivo. Un secondo evento con il primo
ancora pendente segnala overrun; un evento durante il worker segnala deadline
superata. Non viene accodata una metà ormai riutilizzabile dal DMA.

Un half ripetuto dopo un blocco completato produce errore di fase. Il primo
half può essere 0 oppure 1. Un contatore uint32 può passare da `0xffffffff`
a zero: zero resta un token valido. Questa verifica non può rilevare ogni
possibile IRQ perso/coalesciato, in particolare più periodi non osservati.
Occorrono anche misure e controlli del controller nella futura integrazione.

## API e sincronizzazione

`hyperrig_mini_runtime_init()` copia gli hook, controlla dimensioni implicite,
allineamento a 32 byte, assenza di sovrapposizione fra stato/RX/TX e azzera lo
stato. RX e TX hanno ciascuno 256 word, cioè 1024 byte in due metà da 512.
Gli argomenti rifiutati non modificano il contesto. Init/reinit richiede DMA
fermo, IRQ disabilitato e nessun worker attivo.

Configurazione del callback dell'adattatore audio:

```c
device.ready = hyperrig_mini_runtime_ready;
device.user = &runtime;
```

`ready()` aggiorna solo metadati e chiama l'eventuale `wake_from_irq`.
`work()` reclama l'evento, copia RX in staging privato, converte left/Q23
nel Q del modello, chiama `process(process_user, input, output, 64)`, prepara
TX dual-mono privato e pubblica nella metà autorizzata. I due Q sono espliciti
in `ops.input_fraction` e `ops.output_fraction`; non sono calibrazione dello
stock. DSP e copie/cache non vengono eseguiti nell'ISR.

Il worker ritorna `IDLE`, `DONE`, `BUSY`, `FAULT` o `INVALID`.
`inspect()` fornisce una fotografia protetta di sequenza, pending/busy,
primo errore e contatori. Il fault resta presente fino a reinit; gli eventi
successivi vengono conteggiati e ignorati. Dopo un errore non è garantito
silenzio: TX potrebbe ancora contenere un blocco precedente, o essere gia
stato scritto prima del fallimento di cache/end. Il board deve fermare o silenziare
in modo verificato la periferica e reimpostare anche il motore quando la
sua storia temporale non è più valida.

Il contratto è **un solo CPU0, un solo worker, nessun altro ISR che muti
il contesto, nessun accesso CPU1**. Gli hook enter/leave delimitano tutti i
metadati condivisi. L'implementazione target salva ICFG, cancella bit8,
esegue `csync`, poi ripristina esattamente i flag salvati con barriera.
Gli asm hanno clobber `memory`; le chiamate esterne e tali barriere impediscono
al compilatore di mantenere il mailbox fuori dalla regione protetta.
La correttezza non deriva da `volatile`. Queste primitive non sono un lock
fra CPU, non fermano DMA e non escludono eccezioni non mascherabili.
Non cambiare questo contratto introducendo LTO/inlining degli hook senza
riesaminare il codice generato e le barriere.

## Ownership e cache: obblighi del board

Gli hook obbligatori `begin/end(direction,half,sequence)` delimitano solo la
copia/cache, non il DSP. `begin()` deve garantire disponibilità fisica della
metà **per tutta la transazione**, mediante DMA fermo oppure una finestra
temporale dimostrata che comprenda cache, copia e margine. Leggere il bit half
e disabilitare gli IRQ CPU non basta: DMA continuerebbe autonomamente.
Il board deve anche dimostrare l'allineamento di fase fra RX e TX prima di
usare lo stesso numero half su entrambi.

| Transazione | Ordine del worker |
|---|---|
| RX | begin RX, controllo token, `rx_for_cpu`, controllo token, copia 128 word in staging, end RX, controllo token |
| Elaborazione | conversione 64 campioni, DSP, controllo token, preparazione TX privato |
| TX | begin TX, controllo token, copia 128 word, `tx_for_device`, end TX, verifica finale |

Ogni begin riuscito ha un end anche in caso di errore. Un begin fallito non
deve lasciare una lease attiva; end deve rilasciarla anche quando fallisce.
Il controllo software di sequenza impedisce pubblicazioni già riconosciute
come scadute, ma non sostituisce la garanzia fisica della lease. Un fault
osservato dopo una copia non può annullare scritture già avvenute.

`rx_for_cpu` e `tx_for_device` sono hook espliciti, obbligatori anche per
memoria dichiarata coerente, dove servono almeno barriere verificate.
Ricevono indirizzo allineato e 512 byte, cioè 16 linee intere/esclusive.
Una possibile integrazione con `firmware/mini/platform/` è:

- Prima di avviare DMA: inizializzare TX a zero, rendere entrambi i buffer
  coerenti e lasciare RX rigorosamente in sola lettura per la CPU.
- RX: `hyperrig_mini_cache_range(..., HYPERRIG_MINI_CACHE_CLEAN_INVALIDATE, ...)` solo se è
  dimostrato che nessuna linea RX è sporca; un writeback sporco dopo DMA
  sovrascriverebbe i campioni appena ricevuti.
- TX: `hyperrig_mini_cache_range(..., HYPERRIG_MINI_CACHE_CLEAN, ...)` mentre la metà resta di
  proprietà CPU, includendo il costo/cache-timeout nella finestra garantita.

La piattaforma ricostruisce `flush`/`flushinv`, allineamento32 e attesa del
bit14 a `0x01EEE008`. Il runtime non trasforma questa evidenza in coerenza DMA
presunta: mapping, cache mode, esclusione CPU1 e deadline devono essere provati.
Gli hook dei test operano su normali array RAM host; non sono driver board
riutilizzabili come hook vuoti su hardware.

## Wrapper interrupt e limiti dell'ABI

`hyperrig_mini_runtime_irq_bind(device)` associa il device senza leggere
registri. Va chiamato con DMA fermo e IRQ11 disabilitato su entrambi i core;
NULL rimuove l'associazione. Richiede callback e contesto validi e inattivi.
Non installa un vettore e non abilita una sorgente. Il dispatcher usa
`hyperrig_mini_audio_irq()`, che richiede `device.prepared`; il bind può
precedere la preparazione, ma prima di abilitare IRQ entrambi devono essere
completati. Non abilitare un handler scollegato: non potrebbe fare ACK.

Il futuro vettore CPU0 può riferirsi a `hyperrig_mini_irq11_entry` (IRQ11,
priorità 6). Il wrapper salva PSR/RETS/RETI e tutti i 16 GPR, chiama il
dispatcher, ripristina in ordine inverso ed esegue `csync; rti`.
Sono **20 byte di codice, 76 byte di frame**, oltre allo stack delle funzioni
chiamate. Wrapper, dispatcher, mailbox e primitive ICFG sono in `.ramtext.*`;
il driver audio e gli hook futuri richiedono una verifica separata del
posizionamento se la flash non fosse disponibile durante gli IRQ.

Il verificatore compila anche una funzione `__attribute__((interrupt))` con
lo stesso compilatore vendor e la stessa chiamata esterna: questa salva
PSR/RETS/RETI e r0..r3, poi ripristina e fa `rti`. Il nostro set è un
superset del prologo generato e di quello stock. Il decoder indipendente
controlla byte e relocazione della chiamata, e ispeziona il call graph ISR
noto per escludere REP/coproc o ulteriori registri speciali.

Le unita C del componente usano `-mllvm -pi32v2-large-program`: le chiamate
esterne hanno relocation `EXTEND_CALL_32M2` (tipo4, istruzione da 6 byte).
Il salto relativo ordinario tipo2 non copre tutti gli attraversamenti fra
flash `0x0200...` e RAM `0x01C0...`: fra questi ci sono `finish` verso
`fault_locked` e il dispatcher RAM verso il driver audio flash. Il verifier
controlla che l'unica chiamata relativa tipo2 con relocation rimasta sia
quella ASM fra wrapper e dispatcher, entrambi in RAM. La futura applicazione
deve usare chiamate estese o indirette anche quando chiama `ready()` dalla
flash; verificare il solo oggetto relocatable non basta per il link finale.

Questo **non prova consegna e ritorno IRQ sul MINI**, conservazione di stato
hardware nascosto, IRQ durante REP/predicati del foreground, cambio di
modalità o annidamento. Non si introduce un salvataggio arbitrario di
registri speciali la cui semantica non è nota. `wake_from_irq` resta fuori
dall'audit automatico: deve essere breve, seguire l'ABI C, non fare context
switch, attivare nesting o usare REP/DSP/coproc/speciali extra. Le sue
istruzioni vanno riesaminate nell'integrazione board. Un port RTOS richiede
un contratto interrupt dedicato.

## Riproduzione e risultato locale

```powershell
python -X utf8 tools/verify_mini_runtime.py
```

Il comando usa GCC con ASan/UBSan e il toolchain pi32v2 fissato nel progetto;
su Windows li invoca tramite WSL Ubuntu. Produce
`build/mini-runtime/hyperrig_mini_runtime_component.pi32v2.o` e
`research/mini-runtime.json`. Il componente è relocatable, con dipendenze
esplicite `hyperrig_mini_audio_irq`, `hyperrig_mini_audio_rx_q`,
`hyperrig_mini_audio_tx_q` e `memcpy` già fornita dal runtime boot.
L'audio va collegato una volta sola.

Risultati: 512 blocchi alternati, 55 casi di stato/argomenti/dispatch,
7 errori hook, 7 IRQ iniettati nei punti del worker, 256 modelli di
salvataggio/ripristino frame e 256 casi ICFG. Si controllano anche canary,
metà TX non selezionata, ordine cache/copie, rilascio lease, reentrancy,
wrap della sequenza e assenza di DSP nell'ISR. Le prove del frame sono un
modello di stato vincolato ai byte decodificati, non un emulatore del
controller interrupt.

Sul target il contesto occupa 1668 byte (1536 di staging/campioni), gli ops
56 e lo snapshot 64; i due DMA aggiungono 2048 byte, esclusi motore e stack.
Il componente alloca 1180 byte tra codice e dati. A 48 kHz il budget nominale
per metà è 1,333 ms: non è stato misurato né confrontato col costo del DSP.
Nessun comando al pedale, flash o immagine installabile viene prodotto.
