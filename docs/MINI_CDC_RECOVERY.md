# MINI: ingresso ROM dal firmware HyperRig

Il comando originale è **`UBOOT\n`**. Il firmware G M5.71 contiene la
risposta **`OK UBOOT\n`** e un percorso di reset che scrive il marker ROM.
L'audit locale conferma che queste istruzioni sono identiche nella candidata
MINI v2 installata, SHA256
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
La nuova procedura è preparata e verificata offline; non è stata eseguita.

## Evidenza originale

Il bytecode recuperato `recovered/installer/tankg_install.dis.txt` mostra:

- `RealPedal.cdc_cmd`, righe originali 3163–3191: apre CDC a115200, invia PING,
  poi il comando richiesto. Il ramo UBOOT tollera la chiusura della porta.
- `_cmd`, riga originale3219: codifica e invia `line + '\n'`.
- flusso update, riga originale5185: chiama `cdc_cmd('UBOOT')`.

L'installer originale restituisce una stringa «OK UBOOT (port closed by the
pedal)» quando intercetta `SerialException`. Questo è un risultato sintetico
dell'installer. Il nuovo helper conserva soltanto un ACK effettivamente ricevuto.

Nel binario G decodificato, SHA256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`:

| Passaggio | Indirizzo / effetto |
|---|---|
| Stringa comando | `0x02035AA3`: `UBOOT\0` |
| Confronto | `0x020116E0..0x020116F2`, strcmp → ramo `0x020140C8` |
| Risposta | `0x02035D77`: `OK UBOOT\n\0`, inviata tramite `0x02006E24` |
| Attesa | `0x020140EA`: 5tick tramite `0x0203FEB8`; durata fisica non assunta |
| Stato retention | `0x020140F2..0x020140FC`: azzera word `0x01C7FDFC` |
| Sezione critica | `0x01C00FB6`: CLI, lock del core, `csync` |
| Marker | `0x02000B80`: copia16byte `usb_update_mode\0` da `0x0203A135` a `0x01C7FD80` |
| Reset | helper P33 `0x01C00F4A(0xA0,4,1,1)`: imposta bit4, poi loop |

I tre predisptach `0x0200B834`, `0x0200D60C`, `0x0200E07A` restituiscono0
per UBOOT. Il confronto principale raggiunge il ramo di recupero. Il verifier
segue quelle istruzioni, modella soltanto strcmp e rifiuta letture di RAM di
stato: **nessuna flag safe viene letta lungo il percorso ricostruito**.
Sono omessi i salvataggi dello stack; non si tratta di una simulazione completa
dell'ABI o delle periferiche. Le funzioni di invio, scheduler, lock e reset
devono comunque funzionare sul dispositivo. Nessuna operazione NOR è presente
nel ramo del comando.

Questa evidenza rende UBOOT un candidato concreto anche dopo il PONG `safe`
osservato, ma non prova ancora il recupero fisico da quella modalità. Un parser
bloccato non può ricevere il comando. ACK o disconnessione da soli non provano
una nuova enumerazione della ROM.

## Procedura WebSerial separata

`tools/enter_mini_rom_webserial.py` non apre browser o dispositivi senza
`--execute`. Non modifica l'editor, il profilo readonly o i manifest congelati.
Usa una pagina di recupero locale separata, Chrome con profilo nuovo e porta
seriale nuova. Non richiede né dichiara una prova con footswitch premuti.

Prima dell'esecuzione il coordinatore deve:

1. Completare e revisionare gli artefatti necessari al successivo upgrade.
2. Chiudere la sessione desktop03 tramite il suo percorso di chiusura; verificare
   il nuovo `session.json` **completato**, `native_close_verified=true`, browser
   e server arrestati. Registrarne l'hash effettivo. Il connected-proof03 resta
   immutato, SHA256 `96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2`.
3. Eseguire prima il preflight qui sotto. Sostituire `CLOSED_SHA` con l'hash del
   report realmente concluso; nessun report di chiusura va costruito a mano.

```powershell
python -X utf8 tools/enter_mini_rom_webserial.py --check-only --connected-proof build/mini-desktop-real-03/connected-proof.json --proof-sha256 96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2 --closed-session build/mini-desktop-real-03/session.json --closed-sha256 CLOSED_SHA
```

L'esecuzione usa gli stessi argomenti, sostituendo `--check-only` con
`--execute --output build/mini-cdc-to-rom-01`. L'output deve essere nuovo.
La finestra mostra esclusivamente la procedura ROM; il titolo è
`HyperRig MINI · recupero ROM`. La sessione vive al massimo120secondi prima
del comando. Il PING è unico e deve produrre la stessa identità reale osservata
nella sessione precedente.

Il coordinatore legge `recovery.json` con l'helper shared-delete, individua
`browser_process_id` e `origin`, seleziona la sola riga
`Tank-M HyperRig (COM3)` nel chooser nativo tramite UIAutomation e pubblica
atomicamente `build/mini-cdc-to-rom-01/selection.json`:

```json
{
  "observed_utc": "TIMESTAMP_REALE_DELLA_SELEZIONE",
  "browser_pid": 123,
  "origin": "http://127.0.0.1:PORTA_REALE",
  "selected_row": "Tank-M HyperRig (COM3)",
  "exact_unique_row_verified": true,
  "no_other_device_selected": true,
  "method": "Windows UIAutomation SelectionItem and Invoke"
}
```

PID, origin e timestamp sono osservazioni reali della nuova finestra. Il
comando non parte senza questo record e un PONG fresco esatto. Il dominio
CDP DeviceAccess non esponeva il chooser WebSerial nel Chrome provato:
vedere `MINI_WEBSERIAL_CHOOSER.md`. Il nuovo helper non presume tale supporto.

Prima di chiamare `enterROM()` pubblica e sincronizza su disco l'intento.
La pagina può trasmettere soltanto `PING\n` e `UBOOT\n`, ciascuno una volta;
non espone un'API di scrittura arbitraria. Il guard consuma il tentativo prima
del write nativo: timeout, errore, ACK perso o disconnessione non consentono
un secondo UBOOT. I byte TX/RX e gli eventi restano nel report. Il cleanup
chiude stream, porta, browser e server; un errore di close viene registrato,
senza attribuire una chiusura nativa che non sia stata osservata.

## Contratto del risultato

`recovery.json` contiene sempre `command="UBOOT"`, `prior_port`,
`automatic_retry=false`, `firmware_write=false`, `ROM_verified=false`.
Campi distinti:

| Campo | Significato |
|---|---|
| `pong` | Linea realmente ricevuta dal nuovo WebSerial, identica alla prova precedente |
| `command_intent_utc` | Timestamp host prima della pubblicazione/fsync e dell'invocazione |
| `command_invocations` | 0 oppure1, nessuna riemissione |
| `command_submitted_once` | Il guard ha consumato l'unico tentativo e registrato il TX nativo |
| `command_submitted_utc` | Timestamp dell'evento TX browser effettivo, distinto dall'intento host |
| `command_write_completed` | Risoluzione del write nativo; non equivale all'esecuzione del reset |
| `ack_observed` | È stata ricevuta davvero la linea `OK UBOOT` dopo il tentativo |
| `native_disconnect_observed` | Evento WebSerial di rimozione di quella porta |
| `native_close_verified`, `serial_port_closed` | `port.close()` risolto senza errore; non inferito dalla rimozione |

Il codice di uscita0 significa che la singola richiesta è stata osservata
dal guard e la procedura è terminata senza errore di orchestrazione; **non**
attesta ROM o reset. Il coordinatore deve verificare nuova enumerazione ROM,
arrival successiva al TX ed effettiva INQUIRY `WL82 / UBOOT1.00`, poi acquisire
un dump completo dell'unità prima di qualsiasi mutazione NOR. Questo helper
non esegue nessuno di quei passi e non richiede privilegi amministrativi.

## Verifica offline

```powershell
python -X utf8 tools/audit_mini_cdc_recovery.py
python -m unittest tests.test_mini_cdc_recovery -v
node tests/mini_rom_webserial_guard_test.js tools/mini_rom_webserial/guard.js
```

Esito:9test Python e61condizioni Node passati. Coprono bytecode originale,
assenza del gate safe sul percorso, prove/chiusura/picker, PONG frammentato,
device errato, duplicati, errore write, ACK realmente ricevuto o assente,
disconnessione, limiti RX e close fallito. Tutti i trasporti dei test sono
fittizi; nessun test ha aperto il pedale o modificato una sessione browser viva.
