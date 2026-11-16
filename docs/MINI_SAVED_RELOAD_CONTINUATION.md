# Completare il ricaricamento del preset salvato

Il trial `mini-first-preset-ui-04` ha realmente eseguito GAIN giù/ripristino, PSAVE e SNAPSAVE 0. Il suo report resta un fallimento parziale: l'apertura del pannello Presets aveva chiuso il popup del volume, quindi il controllo del focus ha fermato il marker successivo prima di inviarlo.

`tools/probe_mini_browser_saved_reload.py` accetta quel report verificato da `validate_partial_saved_report`. Una sessione nuova rilegge lo stato completo e due STAT; richiede lo stesso preset/scena/capture, gain salvato, A2 attivo in modalità 2 e safe=0, con T.nproc crescente. Non ripete CSAVE, PSAVE o SNAPSAVE.

Il guard separato consente esattamente due comandi, originati dai controlli originali:

1. Apre il popup meters e invia ArrowDown alla manopola Output: volume salvato meno 1 dB.
2. Apre Presets e invia Enter alla riga già salvata: PLOAD della stessa slot.

Il secondo passaggio deve ripristinare gain, modello, capture e scena 0 salvati. L'attesa dell'aggiornamento UI osserva solo lo stato JavaScript; non ripete comandi o tasti. ACK e risposte devono essere presenti nei byte RX nativi. Il successo viene registrato solo dopo la chiusura nativa della porta; il rapporto precedente non viene alterato e non vengono simulati sei comandi nella nuova sessione.

Controllo offline:

```powershell
python tools/probe_mini_browser_saved_reload.py --check-only --partial-report build/mini-first-preset-ui-04/report.json --partial-report-sha256 0eb9836638dd2025d9e75f380db4cc9c765c53dcc7ff4e0316ab810c3d2479ff
```

L'esecuzione esplicita usa `--execute` al posto di `--check-only` e richiede `--output` nuovo. Il selettore USB deve essere attestato in `selection.json`, come nelle prove precedenti. Il programma non autorizza famiglie generali, non ritenta scritture e non certifica qualità acustica, pannello fisico, BLE o conservazione dopo spegnimento.

I test eseguono le funzioni originali `buildGains` e `loadPreset` con seriale/DOM simulati; verificano ordine, focus, trusted event, ACK/RX, chiusura e il preflight sui file reali. Nessun test software qui apre browser o pedale.

## Tentativi reali del 16 novembre 2026

Le sessioni `mini-saved-reload-ui-01` e `02` non hanno chiamato `requestPort`:
il tour introduttivo copriva Connect dopo un clic troppo precoce su Skip.
Una diagnosi offline con API hardware bloccate ha verificato la sequenza
Skip/Connect tramite eventi trusted. Portare la pagina in primo piano,
acquisire una schermata e verificare il bersaglio del clic permette di
distinguere questo problema dal protocollo USB.

Nella sessione `03`, Skip e Connect reali hanno aperto il selettore nativo,
rimasto su “Finding devices…” fino alla scadenza. Nessuna porta è stata aperta,
nessun comando è stato trasmesso e nessuna modifica al preset è avvenuta.
Alle 06:47–06:48 UTC anche due sessioni seriali dirette, esterne al browser,
hanno fallito: prima nessuna risposta al PING, poi timeout di scrittura.
Entrambe hanno chiuso la porta. Windows continuava a elencare COM3 con
VID `3654` e PID `5155`. Queste osservazioni non identificano la causa del
blocco; la riaccensione fisica è stata richiesta e resta da verificare.

I tre report falliti e i log diretti sono conservati nei percorsi riportati
in `analysis/hardware/CURRENT_STATE.json`. Nessun bundle qualificato è stato
emesso sulla base di questi tentativi.
