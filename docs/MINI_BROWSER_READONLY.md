# Collegamento dell'editor MINI con browser isolato

Il nuovo helper [probe_mini_browser_readonly.py](../tools/probe_mini_browser_readonly.py)
prepara una prova del vero editor generato, senza modificare la candidata o
usare il profilo personale. Utilizza Chrome/Edge e `websocket-client` già
installati, un nuovo profilo sotto `build/` e un server temporaneo su localhost.
Browser e server vengono chiusi al termine. Il report viene scritto una volta,
dopo la chiusura, senza sostituire un JSON durante le operazioni sul dispositivo.

La modalità predefinita apre soltanto la UI offline. Web Serial è negato anche
dalla policy HTTP; l'enumerazione restituisce una lista vuota e la richiesta di
una porta è bloccata. USB, Bluetooth e MIDI sono bloccati in entrambe le modalità.
Non viene avviato un chooser in modalità offline.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --output build/mini-browser-offline-new
```

La modalità reale usa `--execute-readonly` e un file di evidenza esplicito,
prodotto dopo avvio e PONG verificati da root. Il file JSON deve contenere:

| Campo | Valore richiesto |
| --- | --- |
| `schema`, `target`, `transport` | `1`, `"tank-mini"`, `"usb-cdc"` |
| `vid`, `pid` | `13908`, `20821`, cioè `3654:5155` |
| `com` | La porta Windows realmente osservata, ad esempio `"COM12"` |
| `pong` | L'intera riga PONG ricevuta, senza terminatore |
| `image_sha256` | `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff` |
| `serial_port_closed` | `true`, dopo avere chiuso il client che ha letto PONG |
| `observed_utc` | Timestamp UTC della verifica fisica |

La riga deve identificare esattamente `tankm_fw M5.71 rel ble` seguito dalla
data originale. Il file deve essere locale e il suo SHA256 deve coincidere
con `--evidence-sha256`. Questo formato raccoglie l'evidenza già verificata dal
runner; non rappresenta autenticazione crittografica del firmware sul pedale.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --output build/mini-browser-live-new --execute-readonly --evidence analysis/hardware/mini-browser-evidence.json --evidence-sha256 HASH_DEL_FILE_VERIFICATO
```

Il percorso live è preparato per il via di root dopo PONG/COM, senza accessi
seriali concorrenti alle prove ROM o all'installazione. In questo task sono
stati eseguiti solo i test con porte simulate; nessuna connessione browser al
MINI è ancora qualificata.

Prima dell'esecuzione reale root deve avere concluso l'installazione e l'avvio
dell'app, osservato `3654:5155` e la porta COM, ricevuto la riga PONG completa e
chiuso il client seriale che l'ha letta. Il pedale deve restare nella stessa
sessione dell'app: niente ROM, reset o altra apertura seriale concorrente.
Il campo `serial_port_closed` attesta quella chiusura; il helper non interroga
altre porte per verificarla. Anche la sola apertura offline del browser in
questa fase attende il via esplicito di root.

Il comando proposto, dopo quei controlli e il pinning del file di evidenza, è:

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --app-dir build/hyperrig-mini-audio-v2/app/web --output build/mini-browser-live-01 --execute-readonly --evidence analysis/hardware/mini-browser-evidence.json --evidence-sha256 SHA256_EVIDENZA_REALE --timeout 45
```

`SHA256_EVIDENZA_REALE` va sostituito con l'hash approvato del file realmente
prodotto, non con un esempio sintetico. La directory di output deve essere
nuova; il helper rifiuta di riusare un profilo precedente. Conserva
`report.json`, `initial.png`, `connected-presets.png` quando ottenibile e lo
stderr di Chromium. Se fallisce non riconnette e non modifica la candidata.

Il helper abilita il dominio `DeviceAccess` dello schema CDP del browser
effettivamente avviato, poi preme il vero pulsante `#connBtn`. Seleziona una
voce soltanto quando il nome contiene un unico token COM corrispondente
all'evidenza. `COM2` non corrisponde a `COM12`; un nome senza COM o una
duplicazione non autorizzano la scelta della prima voce. Liste inizialmente
vuote possono aggiornarsi entro il timeout. Il chooser CDP non espone VID/PID,
quindi una seconda verifica usa `SerialPort.getInfo()` prima di `open()` e
richiede entrambi i valori esatti. Il filtro nativo di `requestPort` include
già VID e PID. Se la richiesta Web Serial non produce l'evento previsto in
questa versione di Chrome, la prova si interrompe senza selezione alternativa.

L'instrumentazione separata
[mini_browser_readonly_guard.js](../tools/mini_browser_readonly_guard.js)
consente una sola richiesta e una sola apertura a 115200 baud. Non riutilizza
porte già autorizzate e non riconnette automaticamente. Prima del PONG esatto
consente soltanto `PING`, fino a cinque tentativi come nell'app originale.
Successivamente `SerialTransport.write` accetta solo una riga di query dalla
lista esplicita, con un budget totale di 1000. Questo controllo è distinto dal
profilo dell'app: PSAVE, PLOAD, FXP, GSAVE, BLEKEY e comandi del pannello non
vengono inviati. Nessun dato di scrittura viene aggiunto ai file dell'app.

La prova live deve completare le letture iniziali MODEL, MEM, FXT, FXS, PLIST e
SNAPS con risposte valide, mostrare l'identità MINI accettata e il banco preset,
registrare una schermata e disconnettersi tramite il percorso dell'app che
attende le letture pendenti. Registra port info, comandi effettivamente inviati,
risposte e stato UI. Il semplice click nel chooser non conta come successo.

I test indipendenti sono eseguibili senza browser o hardware:

```powershell
python -B -X utf8 -m unittest tests.test_mini_browser_readonly -v
```

Cinque test Python includono 47 verifiche JavaScript con una porta simulata:
selezione COM non ambigua, hash e identità, blocco prima del PONG, PID errato,
una sola apertura, rifiuto di comandi di modifica e di più righe, budget PING
e arresto esplicito. La futura verifica delle famiglie di scrittura richiederà
un helper distinto; questo percorso rimane in sola lettura.

Il freeze preparatorio è registrato in
[mini-browser-readonly.json](../research/mini-browser-readonly.json), con gli
hash del helper, dell'instrumentazione, dei test, della dipendenza CDP e dei
cinque file dell'app. La precedente prova UI in Chrome reale è registrata
separatamente in `research/mini-browser.json`: aveva tutte le API hardware
disabilitate e non qualifica il chooser Web Serial o questa futura connessione.
