# Editor MINI nel browser locale

La build `build/hyperrig-mini-audio-v2/app/web/tankmini.html` e stata aperta
nel Chrome installato, versione `157.0.8103.52`, con profilo separato e
server temporaneo limitato a `127.0.0.1`. Non sono stati installati pacchetti
o servizi. Il profilo personale non e stato aperto.

[verify_mini_browser.py](../tools/verify_mini_browser.py) usa il modulo
`websocket-client` gia disponibile e CDP del browser effettivo. La prova
nega seriale, USB, Bluetooth e MIDI tramite `Permissions-Policy`; sostituisce
anche i relativi metodi prima degli script dell'app. Le richieste di accesso
hardware vengono rifiutate, le enumerazioni restituirebbero liste vuote.
Nelle due prove non e stato invocato neppure uno di questi metodi.
Le connessioni esterne sono bloccate. Browser e server vengono fermati
alla fine; il profilo isolato e gli artefatti restano nella nuova cartella
di prova sotto `build/`.

```powershell
python -B -X utf8 tools/verify_mini_browser.py --output build/mini-browser-new-run
```

Il percorso di output deve essere nuovo. L'esito valido e conservato in
`build/mini-browser-readonly-03/report.json`, SHA256
`edb9c1a762fe06ddcdc7c3282aa925e530318d402998eb6ce23ea0be7593db48`.
La pagina verificata ha SHA256
`13d276d50136f9551cf657dae49fff8f0b4d83f0e75b9b831ddb85edcd92a3c4`
ed e legata alla candidata firmware
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.

Esiti controllati con input mouse/tastiera inviato al browser:

- pagina scollegata e demo terminano il bootstrap; titolo e profilo MINI corretti;
- tour iniziale chiudibile, impostazioni apribili e chiudibili;
- catena demo completa, editor TS9, manopola Drive da 55 a 56 con stesso
  valore visualizzato e nel modello JavaScript;
- bypass e riattivazione TS9, selezione della scena Crunch;
- libreria di quattro capture e banco con quattro slot preset;
- layout desktop `1440x1000` e telefono `390x844`, senza overflow orizzontale;
- nessuna eccezione JavaScript non gestita e nessun `console.error`.

Il log browser contiene un `404` per `ctl.json`, endpoint opzionale del
launcher originale per coordinare il possesso della connessione.
Il server statico di prova non lo implementa e l'app gestisce l'assenza.
Non e una richiesta al pedale. Sono conservate schermate della pagina,
dell'editor effetti e della libreria. Il primo run di sviluppo del tester
aveva soltanto cambiato il frammento `#demo` senza ricaricare il documento;
il tester definitivo forza un documento nuovo mediante query diversa.
Questo errore del tester non e attribuito all'app.

Questi risultati riguardano la UI con dati demo. Non attestano audio,
comunicazione seriale, Bluetooth, preset salvati o hardware MINI connesso.
La build verificata mantiene `read=true`, `write=false`, `panel=false`;
una futura app con permessi per comandi verificati richiede una nuova prova.

## Collegamento successivo tramite CDP

Il dominio sperimentale `DeviceAccess` e presente nello schema
`/json/protocol` del browser effettivamente avviato. Lo schema completo
e incluso nel report, senza consultare documentazione di versioni diverse.
Non e stato abilitato un chooser e non e stato concesso alcun permesso.

Sequenza disponibile per un runner successivo esplicitamente autorizzato:

1. Confermare fuori dal browser il CDC `3654:5155` e la risposta
   `PONG tankm_fw ...`, poi chiudere la porta usata per questa verifica.
2. Aprire un nuovo profilo isolato e l'app corretta via localhost con
   una normale policy seriale. Il server del tester descritto sopra
   vieta deliberatamente la connessione e non va riutilizzato a questo scopo.
3. Collegare CDP al target della pagina e inviare `DeviceAccess.enable`.
   Avviare l'ascolto eventi prima di premere il vero pulsante Connect con
   `Input.dispatchMouseEvent`.
4. Attendere `DeviceAccess.deviceRequestPrompted` con parametri
   `{id, devices: [{id, name}, ...]}`. Il `requestPort` dell'editor filtra
   il vendor USB `0x3654`. L'evento CDP non espone VID/PID: non scegliere
   la prima voce se il nome e ambiguo o vi sono dispositivi inattesi.
5. Per una voce identificata in modo univoco, il comando e
   `DeviceAccess.selectPrompt` con `{id: requestId, deviceId: chosenId}`.
   Per annullare: `DeviceAccess.cancelPrompt` con `{id: requestId}`.
6. Verificare stato connesso, identita/versione accettata dal profilo MINI,
   letture completate ed eventuali errori. Il semplice evento di selezione
   non prova che l'app abbia aperto la porta o completato l'handshake.

La presenza del dominio nello schema non prova ancora che la specifica
richiesta Web Serial di questa build produca l'evento su questa macchina.
Questa verifica appartiene alla futura connessione fisica. Nessuna
selezione automatica, richiesta USB o operazione sul pedale e inclusa nel
tester offline.
