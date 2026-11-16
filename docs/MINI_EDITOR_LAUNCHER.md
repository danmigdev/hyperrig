# Aprire l'editor HyperRig MINI

Il bundle verificato è disponibile in `build/hyperrig-mini-qualified-editor`.
Con il MINI acceso e collegato tramite USB dati, aprire con doppio clic
`tools/launch_mini_editor.cmd`. Non serve UAC. Su Windows viene usato Microsoft
Edge già installato, con un profilo separato.

Se compare la guida iniziale, premere **Skip**, poi **Connect** e selezionare
**Tank-M HyperRig (COM3)** nel selettore USB. L'apertura nativa su questo PC
ha richiesto anche 15–20 secondi; il timeout dell'editor è esteso a 30 secondi.
Attendere la connessione senza aprire una seconda finestra.

Per regolare il volume, aprire il meter e usare la manopola Output. Nel pannello
Presets, Save salva il preset; selezionare la sua riga per richiamarlo. La prova
reale del 16 novembre ha confermato modifica del volume e ripristino di
“Preset 1A”, capture A2 e scena A.

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
