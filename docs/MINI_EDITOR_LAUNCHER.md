# Aprire l'editor HyperRig MINI

Dopo la generazione del bundle qualificato in `build/hyperrig-mini-qualified-editor`, aprire con doppio clic `tools/launch_mini_editor.cmd`. Non serve UAC. Selezionare il MINI nel selettore USB del browser.

Si apre una finestra dell'editor originale con un profilo browser separato. Il profilo dell'app abilita esclusivamente le famiglie USB qualificate `GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`: volume, caricamento/salvataggio preset e salvataggio scene. Il launcher non aggiunge un guard di sola lettura o un limite a una singola operazione e non invia comandi di modifica. La barra indica «USB: volume e preset».

Ogni avvio verifica soltanto il sigillo del bundle e i file dell'app. La validazione completa delle prove fisiche avviene durante la creazione del bundle; non è ripetuta all'apertura. Nessun bundle qualificato viene creato dal launcher.

Chiudere la finestra prima di aprire una seconda sessione. Il server localhost termina insieme alla finestra; non viene installato alcun servizio. Per chiedere una chiusura ordinata da terminale, usare la directory della sessione corrente, registrata sotto `build/mini-editor-session-*`:

```powershell
python tools/launch_mini_editor.py --close-session build/mini-editor-session-<identificativo>
```

La richiesta locale lascia finire la coda originale, chiude la porta e poi il browser/server. Una chiusura della finestra che impedisca l'ultima osservazione viene riportata come non osservata; non viene inventata una conferma seriale.

Controllo locale senza browser o dispositivo:

```powershell
python tools/launch_mini_editor.py --check-only --bundle build/hyperrig-mini-qualified-editor
```

Le sessioni conservano i riferimenti al bundle, il PONG effettivo, le osservazioni native di apertura/chiusura e gli eventuali errori. Questi dati non attestano qualità audio o nuove funzioni oltre alla qualifica già presente nel bundle.
