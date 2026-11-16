# Tour dell'editor durante la prova di ricaricamento

`tools/activate_mini_editor_ui.py` è un'utilità dell'operatore per la prova
`probe_mini_browser_saved_reload.py` già congelata. Non modifica il probe,
il guard, il qualificatore o i loro report.

Con `--execute` seleziona soltanto la pagina locale esatta attestata dal report
attivo, porta la finestra avanti e salva screenshot. Attende tre hit-test
stabili del pulsante Skip, esegue un clic CDP reale e verifica la scomparsa
di `.coach`. Poi clicca Connect una sola volta, esclusivamente con
`requests=opens=mutations=0`, porta chiusa e stato non connesso/non in connessione.
Verifica il clic trusted e la richiesta del chooser. Non seleziona il dispositivo,
non invia comandi seriali e non certifica una connessione. L'eventuale selezione
successiva resta all'operatore e il flusso originale del probe resta attivo.

```powershell
python tools/activate_mini_editor_ui.py --check-only --report build/mini-saved-reload-ui-NN/report.json
python tools/activate_mini_editor_ui.py --execute --report build/mini-saved-reload-ui-NN/report.json --output build/mini-tour-operation-NN
```

Output nuovo obbligatorio, nessuna ripetizione automatica dopo un clic incerto.
Il default non legge input e non apre il browser. Le prove automatiche usano
solo CDP simulato. Visibilità e focus sono osservazioni: nessuna loro proprietà
viene falsificata. Questa procedura corregge l'intercettazione del clic da parte
del tour; non risolve né diagnostica da sola il successivo chooser senza dispositivi
o l'assenza di risposta USB osservata anche dal client COM.
