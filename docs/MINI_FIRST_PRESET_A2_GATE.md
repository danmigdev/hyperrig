# Prova UI del primo preset: attività A2

`tools/run_mini_v3_first_preset_a2.py` delega al trial congelato e al lettore di prove di `run_mini_v3_editor.py`. Non modifica quei file, l'applicazione, il profilo, il guard o la sequenza dei sei comandi UI. L'esecuzione resta esplicita; senza argomenti non apre browser o dispositivo.

Ogni snapshot originale viene seguito da una sola `STAT` nella coda originale `Pedal.cmd`, terminata dall'intera riga `NIVEL`. Il parser controlla i formati originali e le `7+n` righe, con `n≤16`. Prima della preparazione della capture e prima delle modifiche UI richiede due `T.nproc` uint32 strettamente crescenti, conservando i controlli originali su identità, A2, stato, `safe=0` e modalità2. Le dimensioni DSP devono corrispondere ad A2 (23 layer, 3 canali). Un reset o overflow del contatore non viene interpretato come progresso.

L'[audit del firmware](../research/mini-a2-activity-audit.json) distingue il completamento A2 dalla mailbox generica rappresentata da `FXS posts/takes`. Questi ultimi restano osservazioni e possono essere zero; la fixture reale contiene `nproc=328986→329126`. `STAT` consuma picchi diagnostici e `T.max`, senza azzerare `nproc` o scrivere configurazione/NOR. Il risultato non prova qualità audio, uscita analogica o persistenza dopo un ciclo di alimentazione.

Il report conserva risposte STAT e RX nativi attraverso il guard originale, oltre ad `A2_gate_extension`, audit/fixture con SHA256 e hash del nuovo driver. La chiusura nativa e il confronto RX restano necessari per promuovere il risultato finale.

Per la sessione desktop già chiusa, il nuovo `validate_mini_webserial_v3_close.py` conserva i controlli del validatore congelato e classifica soltanto l'esatta `WebSocketConnectionClosedException('Connection to remote host was lost.')` della seconda osservazione CDP nel launcher v3. Richiede chiusura seriale nativa riuscita una volta, guard fermo senza errori, richiesta locale di chiusura con hash e cronologia coerente, browser/server terminati e fonti esatte. L'errore originale resta nel contesto e nel report con `desktop_close_observation`; la perdita CDP non costituisce una prova di chiusura seriale. Nessuna prova o SHA precedente viene riscritto.

Usare tre riferimenti reali e chiusi: boot v11, connected-proof della sessione desktop v3 e relativo `session.json` dopo la chiusura verificata. Eseguire prima:

```powershell
python tools/run_mini_v3_first_preset_a2.py --check-only --boot <boot.json> --boot-sha256 <SHA> --connected <connected-proof.json> --connected-sha256 <SHA> --session <session.json> --session-sha256 <SHA>
```

Per la prova autorizzata sostituire `--check-only` con `--execute` e aggiungere `--output build/<directory-nuova>`. Il selettore UIA, `selection.json`, capture/preset conservati, assenza di retry e chiusura finale seguono il [trial originale](MINI_BROWSER_FIRST_PRESET.md). Nessuna prova fisica è stata eseguita durante lo sviluppo di questo adattatore.

Verifica offline: `python -m unittest tests.test_mini_v3_first_preset_a2`.
