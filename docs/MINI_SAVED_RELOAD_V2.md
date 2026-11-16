# Continuazione del preset salvato: collegamento nativo

`tools/probe_mini_browser_saved_reload_v2.py` e il relativo guard v2 sono nuovi
file. Mantengono la prova parziale 04 e i precedenti tentativi immutati.
Le sole mutazioni restano un ArrowDown sulla manopola Output originale e un
Enter sulla riga del preset 0, che invia PLOAD 0. Nessun nuovo salvataggio,
cancellazione, upload, modifica del profilo o retry delle mutazioni.

Il bootstrap conserva il ciclo originale di cinque PING da 700 ms nella stessa
apertura. Soltanto una risposta vuota, conclusa dal vero timeout di `Pedal.cmd`,
può ripetersi. Il guard osserva `Log.cmd`, la scrittura nativa dei cinque byte e
la sua promessa completata, tutti i byte RX e le risposte decodificate. Qualunque
byte parziale/tardivo, errore di stream, scrittura pendente o risposta diversa
impedisce la ripetizione. Il parser Python ricontrolla queste prove nel report.
La chiusura prevista tramite reader.cancel dopo guard.stop è distinta dalla
fine inattesa del reader durante la connessione.

La prova `native-open-and-exact-pong` lega `SerialPort.getInfo()` 3654:5155,
una sola apertura nativa e il PONG normale esatto ai byte RX. Non identifica
chi abbia scelto la porta, non deduce il nome COM e non attesta l'hash firmware
dal dispositivo. Un eventuale `selection.json` UIA resta evidenza separata,
opzionale e verificata; la sua assenza non viene sostituita da dati inventati.

Il report indica `automatic_retry=true` esclusivamente per il bootstrap PING,
con numero effettivo di tentativi e timeout vuoti. `mutation_retry_performed`
e `query_retry_performed` restano false. Il qualificatore unisce questa nuova
prova alla precedente prova di salvataggio; non riscrive il risultato parziale.

```powershell
python tools/probe_mini_browser_saved_reload_v2.py --check-only --partial-report build/mini-first-preset-ui-04/report.json --partial-report-sha256 0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff
```

L'esecuzione richiede `--execute --output <nuova-cartella-build>` e rimane
riservata all'operatore. I test automatici usano stream e browser simulati;
nessuna prova fisica deriva dal loro successo. La gestione operativa del tour
resta distinta dal protocollo e non richiede una modifica al vecchio helper.
