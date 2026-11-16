# Editor desktop MINI con WebSerial reale

`tools/launch_mini_desktop_readonly.py` apre, soltanto con `--execute`, una
finestra Chromium visibile sull'editor completo già presente in
`build/hyperrig-mini-audio-v2/app/web`. Usa un profilo browser nuovo, un server
temporaneo su `127.0.0.1` e il COM osservato nell'avvio normale. Non usa il
profilo personale, non installa dipendenze e non cambia app o manifest frozen.
Il comando senza opzioni stampa il piano senza leggere prove o aprire browser.

Il launcher non richiede né dichiara una prova di recupero con footswitch. La
manifest base conserva `hardware_verified=false`: l'eventuale collegamento
reale viene registrato separatamente, senza promuovere audio, preset, BLE o
recupero al boot.

## Due modalità di identità

- **PONG già verificato:** report normalboot v10 con CDC enumerata e log
  PING-only completo, chiuso, sullo stesso COM. Il parser originale ripete il
  replay dei byte RX e verifica versione, data e interpretazione registrata.
  Il PONG del browser deve poi essere identico a quello del log.
- **Primo handshake WebSerial:** aggiungere `--first-handshake`. Il report
  normalboot deve comunque provare la comparsa della CDC; il log precedente
  può contenere un PING fallito, ma deve provare apertura e chiusura nativa
  della seriale sul medesimo COM, senza altre scritture. Quel log non qualifica
  l'identità. Il guard lascia passare soltanto `PING` finché riceve davvero
  `PONG tankm_fw M5.71 rel ble` con data strutturata. Il report parte con
  `identity_verified=false` e conserva il PONG solo quando arriva.

L'errore PING di v10 resta nel riferimento alle prove originali. Può essere
superato soltanto da un'identità effettivamente ricevuta più tardi; la sola
presenza di `COM3` non abilita le altre letture. Ogni altro programma che usa
la seriale deve essere chiuso prima del launcher.

## Preflight e apertura

Esempio per primo handshake; sostituire i due SHA con quelli dei file
completati e il log con l'ultimo diagnostico chiuso da usare come prova.

```powershell
python -B -X utf8 tools/launch_mini_desktop_readonly.py --check-only --first-handshake `
  --boot-run analysis/hardware/mini-first-boot-v10-released-run.json `
  --boot-sha256 SHA256_REPORT_BOOT_COMPLETATO `
  --ping-log analysis/hardware/mini-first-app-v10-ping.jsonl `
  --ping-sha256 SHA256_LOG_PING_CHIUSO
```

Per aprire davvero la finestra, sostituire `--check-only` con `--execute` e
aggiungere `--output build/mini-desktop-real-01`, scegliendo una directory
nuova. Il processo deve rimanere attivo finché si usa la finestra. È possibile
avviarlo con Python/PowerShell in background con console nascosta: la finestra
dell'app resta visibile. Non serve elevazione Windows per WebSerial.

Per usare un PONG già riuscito, omettere `--first-handshake` e fornire il log
completo del PING riuscito. Non è previsto alcun fallback automatico fra le
due modalità.

Il chooser CDP seleziona solamente il COM attestato, con corrispondenza esatta
e univoca. Prima dell'apertura il guard controlla nuovamente VID/PID
`3654:5155`. È permessa una sola apertura a `115200`; non c'è riconnessione.
Dopo l'identità, l'app deve ricevere risposte reali a `MODEL`, `MEM`, `FXT`,
`FXS`, `PLIST` e `SNAPS` prima del risultato `connected_readonly`.

## Finestra e chiusura

L'editor rimane visibile e le normali letture continuano. Il guard desktop
deriva dalla allowlist readonly frozen; blocca ogni mutazione anche se un
controllo dell'interfaccia tentasse di inviarla. La sessione è limitata a
50.000 query e 90 minuti; al limite viene chiusa la seriale, mentre la finestra
resta disponibile. USB diretto, Bluetooth e MIDI sono bloccati. Gli eventi
serial connect sono disabilitati per impedire riconnessioni automatiche.

Chiudere la finestra termina anche il server locale. Per ottenere prima una
prova esplicita di chiusura nativa, usare il normale Disconnect dell'editor
oppure:

```powershell
python -B -X utf8 tools/launch_mini_desktop_readonly.py --close-session build/mini-desktop-real-01
```

Quest'ultimo comando scrive soltanto una richiesta locale. Il launcher attivo
esegue la disconnessione originale, osserva il ritorno di `port.close()`, poi
chiude browser e server. Se la finestra è stata chiusa prima che tale risultato
fosse osservabile, il report distingue `browser_process_stopped=true` dalla
chiusura nativa non osservata: non inventa `serial_port_closed=true`.

`session.json` è pubblicato atomicamente e può essere monitorato con
`tools.mini_host_journal.read_shared_bytes`. Non leggere il report attivo con
un normale `Get-Content` che potrebbe bloccare una sostituzione su Windows.
`connected-proof.json` e `connected.png` vengono creati una sola volta dopo
le letture riuscite. Il report conserva le prove d'ingresso, gli hash dei
sorgenti, il PONG effettivo, contatori e storico limitato dei comandi/risposte.
Un'eventuale selezione manuale della demo viene registrata come tale e non è
considerata comunicazione reale.

## Verifica locale

```powershell
python -B -X utf8 -m unittest tests.test_mini_desktop_readonly -v
node tests/mini_desktop_readonly_guard_test.js tools/mini_desktop_readonly_guard.js
```

I test usano esclusivamente seriale, prove e browser finti. Verificano le due
modalità di PONG, la chiusura, la finestra configurata senza headless, i limiti
readonly e la rimozione del server in caso di errore di avvio. Non costituiscono
una prova fisica del collegamento WebSerial.
