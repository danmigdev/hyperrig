# Limite del chooser CDP osservato nella sessione desktop 01

La sessione `build/mini-desktop-real-01/session.json`, letta mediante
`read_shared_bytes`, registra `requests=1`, `opens=0`, nessuna riga TX/RX e
nessun evento `chooser_prompts`. Dopo 60 secondi il launcher ha fermato il
guard. **Questa sessione non ha aperto la seriale né provato il firmware via
WebSerial.** Root ha successivamente osservato con UIAutomation, nella sola
finestra Chrome della sessione, il chooser nativo con la riga esatta
`Tank-M HyperRig (COM3)` e il pulsante Connect.

Il Chrome osservato è `157.0.8103.52`; `/json/version` riporta la revisione
`0985600c06a688b9c669e74afde7dacd5aaed047`. Nella sorgente corrispondente,
`SerialChooserController` popola la lista nativa e, in `Select`, concede il
permesso e completa la callback. Non inoltra la richiesta al dominio
DeviceAccess. I nomi delle opzioni includono il componente COM del percorso.
[Sorgente Chromium della revisione osservata](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/chrome/browser/ui/serial/serial_chooser_controller.cc).

Il servizio seriale chiama il chooser tramite `SerialDelegate::RunChooser`;
solo dopo la selezione può risolvere `requestPort`. L'apertura del dispositivo
è un'operazione successiva, distinta. Questo concorda con `requests=1` e
`opens=0` della sessione 01.
[SerialService alla stessa revisione](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/content/browser/serial/serial_service.cc).

Alla stessa revisione è invece il controller Bluetooth a implementare
`BluetoothDeviceRequestPromptInfo` e chiamare esplicitamente
`UpdateDeviceRequestPrompt`. Il dominio CDP disponibile nello schema non
dimostra quindi che anche il chooser WebSerial emetta quel tipo di evento.
[Controller Bluetooth alla stessa revisione](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/content/browser/bluetooth/bluetooth_device_chooser_controller.cc).

Il precedente controllo della sola presenza del dominio CDP era insufficiente
come prova di integrazione. I test Node del guard verificano allowlist,
identità, limiti e chiusura usando una seriale finta; non provano la consegna
degli eventi del chooser nativo. Non è utile aggiungere un altro mock che
presupponga proprio l'evento mancante.

Per una nuova sessione, root può selezionare la riga COM esatta nel chooser
nativo, senza cambiare le capacità del guard. Il launcher frozen non richiede
che la selezione sia avvenuta tramite CDP: prosegue quando `requestPort`
restituisce la porta, ricontrolla VID/PID e permette solo PING prima del PONG.
La sessione 01 è già ferma e non va riattivata manipolando lo stato del guard.

La diagnosi della nuova prova deve distinguere: selettore richiesto, porta
restituita, apertura nativa completata, write completata e PONG ricevuto.
Una riga nella lista TX prima della risoluzione di `write()` non prova che il
firmware abbia letto il comando. Il risultato positivo resta il PONG reale
seguito dalle risposte readonly, non la sola selezione della porta.

Nessun sorgente frozen, browser, dispositivo o finestra è stato modificato
durante questa analisi.
