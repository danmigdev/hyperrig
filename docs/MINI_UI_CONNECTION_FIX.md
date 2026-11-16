# Nodi introduttivi e sblocco dell'editor

L'adattamento precedente sostituiva `#firstUse ol` e rimuoveva `#fuB` e `#fuC`. Il codice originale aveva già memorizzato i loro testi in `fuTxt`; alla connessione, `setLock()` tentava di aggiornarli e generava un errore prima di rimuovere `inert` dalle manopole. La diagnosi DOM reale e l'errore sono conservati in `analysis/hardware/mini-v3-knob-DOM-01.json` e `mini-v3-setLock-diagnostic-01.json`.

`app/mini/mini-ui-v2.js` conserva i due nodi originali e i loro testi, sostituendo soltanto il passo relativo al firmware. Non modifica `setLock`, `fuTxt`, `S.connected`, `inert` o il guard. Un test Node esegue le funzioni originali `setLock` e `phInert`: riproduce l'errore precedente, verifica la preservazione dei nodi e lo sblocco/blocco normale durante connessione/disconnessione.

`tools/run_mini_v3_first_preset_ui_v3.py` delega al driver A2/guard v2 congelati. La copia in `build/hyperrig-mini-ui-v2/app/web` differisce dall'app precedente solo per `mini-ui.js`. Le prove storiche continuano a essere validate con l'app originale; il nuovo trial dichiara e serve la copia corretta, con hash separati e `ui_compatibility_extension`. Nessuna funzione è qualificata da questa sola correzione.

La copia è costruita/verificata con `--build-ui-copy`. Per il trial usare gli stessi tre riferimenti boot/connected/session del driver precedente e prima `--check-only`, poi l'eventuale `--execute` autorizzato con una nuova directory di risultato. Tutti i controlli di focus e la sequenza di comandi restano invariati.
