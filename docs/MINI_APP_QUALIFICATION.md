# Qualifica USB dell'editor dopo il primo avvio

Il binder [qualify_mini_app.py](../tools/qualify_mini_app.py) usa soltanto file
locali. Non apre porte, browser o dispositivi. Il comando predefinito mostra il
percorso senza leggere prove. Non modifica il manifest, il firmware o l'app
congelati in `build/hyperrig-mini-audio-v2`.

Non esiste ancora una qualifica fisica prodotta da questo lavoro. I test del
binder usano fixture temporanee, eliminate al termine. Tutti i comandi reali
qui sotto sono per il coordinatore, dopo esito positivo dell'installazione e
con il pedale nella stessa sessione applicativa; nessun accesso è concorrente
con ROM, flash o altri client seriali.

## Prove richieste e lettura iniziale

Servono il run definitivo dell'installazione completa, il run con tre tasti
tenuti e quello successivo con tasti rilasciati. I percorsi sono parametri:
non si riusa il risultato di un tentativo di installazione interrotto.
L'inspector indipendente ricontrolla NOR intera, app, regioni esterne, comandi
e riconciliazioni. Entrambi i boot devono essere legati all'hash di quel run.
Il contrasto richiesto è nuova enumerazione ROM/INQUIRY con tasti tenuti e
CDC `3654:5155` con tasti rilasciati. Sono reset attraverso SPL, non una prova
di accensione da alimentazione spenta.

Il manifest congelato consente già letture: non occorre impostare
`hardware_verified` per inviare PING. Il wrapper di boot può eseguire PING
immediatamente; la lettura seguente ripete l'identità e acquisisce lo stato
necessario ai preset. La porta va presa dal run released completato, senza
indovinare un numero COM. Usare percorsi di output nuovi:

```powershell
python -B -X utf8 tools/probe_mini_app.py read --port COM_EFFETTIVA --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --log analysis/hardware/mini-app-qualified-read-01.jsonl --queries MODEL MEM LVL FXT FXS PLIST PSTAT SNAPS SNAPNAME
```

Il binder richiede `session_complete` seguito dalla chiusura della porta,
versione esatta `tankm_fw M5.71 rel ble`, stessa COM e VID/PID osservati al
boot, comandi letterali senza mutazioni e i nove query elencati. Riesegue il
parser readonly sui byte RX conservati e confronta i risultati del journal;
analizza inoltre FXT, FXS, PLIST e SNAPS. Un PING da solo non qualifica queste
letture. I parser non attribuiscono una misura audio al valore LVL.

Sostituire i tre percorsi `RUN_*` con i report completati del tentativo
effettivamente riuscito:

```powershell
python -B -X utf8 tools/qualify_mini_app.py read --install-run RUN_INSTALLAZIONE_COMPLETA --held-run RUN_HELD --released-run RUN_RELEASED --read-log analysis/hardware/mini-app-qualified-read-01.jsonl --output-dir build/hyperrig-mini-usb-qualified-01
```

Soltanto dopo tutti i controlli viene creata la directory nuova, contenente:

- `installation-inspection.json`: verifica indipendente dell'installazione;
- `read-qualification.json`: prove, hash, risposte e limiti della qualifica;
- `firmware-manifest.json`: `hardware_verified=true` con ambito esplicito
  USB boot/letture, `read=true`, `write=false`, `panel=false`, nessuna famiglia;
- `browser-evidence.json`: PONG, COM, timestamp e chiusura seriale realmente
  osservati, nel formato del helper browser già congelato.

L'hash dell'immagine deriva dal legame con installazione e dump. PONG non
attesta crittograficamente il binario; i log non sono autenticazione del
dispositivo. La verifica non prova assenza di un reset o di un altro client
intervenuti dopo la raccolta. Audio, BLE, power-cycle, persistenza e comandi
del pannello restano fuori da questa prima qualifica.

## Primo preset senza sovrascrivere uno slot esistente

Leggere `read-qualification.json` → `read.PLIST`,
`read.FXS`, `read.FXT` e `read.SNAPS`. Il campo `preset_trial_path` indica il
ramo ammesso, ma il probe rilegge tutto prima di agire e non si fida di uno
snapshot precedente.

Con PLIST coerente e `current=-1`, il probe first-preset sceglie il primo slot
libero se `--slot` è omesso. Prima di PSAVE conserva un backup dello stato e
controlla che non sia cambiato. Non serve inventare un export di banca vuota.
Il marcatore `auto` diminuisce un parametro reale entro FXT oppure un gain di
1 dB; se manca una modifica ammessa si ferma prima di PSAVE. Il test verifica
separatamente PSAVE → marcatore → PLOAD e SNAPSAVE → marcatore → PLOAD/SNAP.

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py create --port COM_EFFETTIVA --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --log analysis/hardware/mini-app-first-preset-01.jsonl --backup analysis/hardware/mini-app-first-preset-01-before.json --report analysis/hardware/mini-app-first-preset-01-proof.json
```

Il nuovo `HyperRig_Test` e la scena A rimangono salvati e selezionati. Nessun
PDEL viene inviato. Gli altri slot sono confrontati per metadata PLIST, non
per ogni payload interno. Un capture attivo non persistito, scene RAM non
selezionate non ripristinabili, NACK/errore, incoerenza o timeout interrompono
la prova senza retry o ripristino cieco. Il report incompleto identifica
eventuali scritture già avvenute: non rilanciare automaticamente.

Con `current>=0` **non usare first-preset e non falsificare current=-1**. Una
prova `probe_mini_app_mutation.py live` può verificare un parametro reale e
ripristinarne il valore senza scritture persistenti. ID, indice e valore
devono provenire da FXS/FXT; il probe ricontrolla lo stato prima di inviare.

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py live --port COM_EFFETTIVA --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --operation FXP --block ID_OSSERVATO --parameter INDICE_OSSERVATO --value VALORE_AMMESSO --log analysis/hardware/mini-app-live-01.jsonl --backup analysis/hardware/mini-app-live-01-before.json --report analysis/hardware/mini-app-live-01-proof.json
```

Il percorso persistente `mutation.py save` richiede invece il vero export
banca nel formato originale, corrispondente al preset corrente, oltre a uno
slot libero e un marcatore. Il dump NOR non sostituisce quel documento. L'export
completo del frontend limitato è bloccato perché modifica scene e altre
impostazioni: non abilitarlo implicitamente per aggirare il prerequisito.
Se non c'è un marcatore reale o manca il backup necessario, l'editor resta
readonly per quel ramo; non si cancella o carica un preset arbitrario.

## Famiglie realmente provate e nuova build

Dopo un report fisico completo, il binder deriva l'elenco soltanto da
`physically_exercised_requests`; ignora `supported_by_protocol` come fonte
di autorizzazioni. Il builder esistente verifica tutte le prove e rigioca
integralmente il trace first-preset. Mock, prove incomplete o prove BLE non
abilitano famiglie USB. Con catena vuota il risultato previsto è GAIN, PLOAD,
PSAVE, SNAP e SNAPSAVE; FXP/FXE richiedono rispettive prove reali.

```powershell
python -B -X utf8 tools/qualify_mini_app.py families --manifest build/hyperrig-mini-usb-qualified-01/firmware-manifest.json --reports analysis/hardware/mini-app-first-preset-01-proof.json --output build/hyperrig-mini-usb-qualified-01/firmware-families.json
python -B -X utf8 tools/build_mini_app.py --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-families.json --output build/hyperrig-mini-usb-qualified-01/editor --report build/hyperrig-mini-usb-qualified-01/app-protocol.json
```

Si possono passare più report fisici a `--reports`. Il risultato continua ad
avere `write=false`: sono abilitate le famiglie qualificate entro sintassi,
range FXT e contesto osservato, non qualsiasi comando. Nessuna capacità BLE,
upload NAM/IR, FXAdd, cancellazione generale o export completo viene aggiunta.
Reload/readback non provano persistenza dopo power-cycle o qualità audio.

Per la prova UI readonly, il helper isolato può puntare alla nuova directory
`editor/web`. Calcolare l'hash del `browser-evidence.json` generato e usarlo
come `--evidence-sha256`; la porta deve essere ancora chiusa e la sessione
del pedale invariata. Il helper resta readonly anche se l'app ha famiglie:
prova connessione e visualizzazione, non una scrittura tramite UI.

```powershell
python -B -X utf8 tools/probe_mini_browser_readonly.py --app-dir build/hyperrig-mini-usb-qualified-01/editor/web --output build/mini-browser-qualified-01 --execute-readonly --evidence build/hyperrig-mini-usb-qualified-01/browser-evidence.json --evidence-sha256 HASH_EFFETTIVO --timeout 45
```

Prima delle prove preset si può costruire lo stesso editor da
`firmware-manifest.json` in un'altra directory nuova per il solo collegamento
readonly. L'APK/Android e il trasporto BLE richiedono prove e build separate.

Test del binder, tutti offline:

```powershell
python -B -X utf8 -m unittest tests.test_mini_app_qualification -q
```
