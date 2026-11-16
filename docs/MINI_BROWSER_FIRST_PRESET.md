# Prova UI del primo preset MINI v3

`tools/probe_mini_browser_first_preset.py` prepara ed esegue, solo con
`--execute`, una prova dell'editor originale in un nuovo Chrome visibile e un
profilo temporaneo. Il profilo firmware/app v3 congelato resta readonly e non
viene modificato. Il guard temporaneo consente soltanto il piano sperimentale
esatto; il risultato non concede automaticamente famiglie di comandi.

Il codice e i test sono pronti per una futura esecuzione. **Questa prova non è
stata eseguita sul pedale.** Il collegamento v2 osservato in safe mode non
soddisfa i prerequisiti v3.

## Prerequisiti

- Installazione v3 completata e verificata: app SHA256
  `9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c`.
- Boot normale v11, vero PONG esatto e sessione WebSerial v3 readonly chiusa,
  verificati da `validate_mini_webserial_v3.py`. Non si inventa una prova con
  footswitch premuti, un hash misurato dal pedale o un PING Python riuscito.
- Nuove risposte complete: PONG senza `safe`, `CLKSTATE safe=0`, `LVL m=2`,
  modello A2 invariato e abilitato, `PLIST current=-1`, `SNAPS 0000 current=-1`,
  output maggiore di −30 dB, un preset libero e nessuna dipendenza IR attiva.
- Due osservazioni mostrano avanzamento dei contatori core1 `posts` e `takes`,
  prima della preparazione capture e prima delle azioni UI. `ci/co` sono
  contatori di clipping e possono valere zero. `run` è una durata; `eng` viene
  registrato, senza usarlo come contatore. Queste osservazioni non provano il
  segnale analogico o la qualità dell'audio.

## Sequenza esatta

1. Il selettore seriale nativo deve scegliere l'unica riga
   `Tank-M HyperRig (COMn)` del browser appena creato. CDP DeviceAccess non viene
   usato per il selettore WebSerial. Il coordinatore scrive `selection.json`
   prima di qualsiasi modifica, con PID, origine e timestamp reali.
2. Se la capture corrente è la A2 incorporata senza slot persistente, un solo
   `CSAVE k A2` la conserva nel primo slot capture libero. È un comando
   diagnostico dichiarato, non un evento UI. Se la A2 corrente ha già uno slot,
   il preambolo non la riscrive. `CREAD k` e 51 richieste `CREAD k offset`
   verificano tutti i 4892 byte contro la A2 originale, CRC e inventario.
   Non viene eseguito upload. `loadModelName()` originale aggiorna la UI da
   una nuova lettura CLIST; nessun campo nascosto `S` viene assegnato.
3. Sulla manopola Output originale: ArrowDown di 1 dB, lettura di verifica,
   ArrowUp per ripristinare, nuova lettura. L'ingresso resta invariato.
4. Click sul pulsante Save della prima riga preset libera, non sul suo nome
   vuoto che avvierebbe `PNEW`. Il nome è quello scelto dall'editor originale,
   normalmente `Preset 1A`. `savePreset` invia `PSAVE` e il suo `sceneAOnSave`
   invia `SNAPSAVE 0`. ACK, inventario e scena vengono verificati.
5. Un secondo ArrowDown su Output lascia un marcatore temporaneo. Enter sul
   nome della riga appena salvata richiama il `loadPreset` originale e un solo
   `PLOAD`. Devono tornare gain salvato, riferimento capture, MODEL, catena,
   parametri e scena A. Non si invia `SNAP 0` per correggere un esito diverso.
6. La coda originale viene svuotata, il polling fermato e la porta nativa
   chiusa. I flag di successo vengono impostati solo dopo verifica dei byte RX
   effettivi, ordine UI/TX/ACK e chiusura. Browser e server locale terminano.

Se una risposta, un inventario o un ACK non coincide, la prova si arresta.
Non ritenta comandi, non ricollega la porta, non invia un ripristino alla cieca
e non elimina capture/preset. Un errore dopo una scrittura può quindi lasciare
la modifica già eseguita: il report conserva l'intento e le osservazioni senza
dichiarare successo. La capture e il nuovo preset rimangono intenzionalmente
memorizzati quando la prova riesce. Il reload non prova persistenza dopo
spegnimento e può utilizzare la cache interna della capture.

## Comando futuro

Sostituire percorsi e SHA con le prove v3 realmente concluse. L'assenza di
`--execute` non avvia browser o dispositivi. `--check-only` legge soltanto i
file di prova; durante il lavoro attuale sono stati eseguiti solo i test.

```powershell
python -X utf8 tools/probe_mini_browser_first_preset.py --check-only `
  --boot analysis/hardware/mini-first-boot-v11-released-run.json --boot-sha256 <SHA-BOOT> `
  --connected build/<SESSIONE-V3>/connected-proof.json --connected-sha256 <SHA-CONNECTED> `
  --session build/<SESSIONE-V3>/session.json --session-sha256 <SHA-CLOSED>
```

Per la prova autorizzata, usare gli stessi argomenti con `--execute` e
`--output build/mini-first-preset-ui-01`, directory ancora inesistente.
Il coordinatore attende `awaiting_exact_UIA_selection` nel report condiviso e
fornisce un sidecar atomico con lo schema già usato nel recupero WebSerial:

```json
{
  "observed_utc": "<UTC reale>",
  "browser_pid": 12345,
  "origin": "http://127.0.0.1:<porta del report>",
  "selected_row": "Tank-M HyperRig (COM3)",
  "exact_unique_row_verified": true,
  "no_other_device_selected": true,
  "method": "Windows UIAutomation SelectionItem and Invoke"
}
```

`report.json` comprende riferimenti di boot/installazione/identità/chiusura,
hash dei sorgenti, snapshot, prova della capture, byte TX/RX, eventi UI trusted,
ACK realmente ricevuti, screenshot e osservazione della chiusura. È un modello
nuovo `mini-browser-first-preset-v3-trial`: non va passato come se fosse il
vecchio `representative-first-preset-v1`, che verifica una sequenza diversa.
Se CDP si interrompe dopo l'intento di apertura senza poter leggere gli eventi
nativi, `hardware_executed` rimane `null` e `execution_status_unknown` è vero:
non è una prova che il dispositivo non sia stato aperto.

## Verifica offline

```powershell
python -X utf8 -m unittest tests.test_mini_browser_first_preset -v
```

Tredici test Python includono il test Node con 69 condizioni: le funzioni
`buildGains`, `savePreset`, `sceneAOnSave`, `loadPreset` sono estratte dall'HTML
v3 originale e vengono eseguite su dipendenze UI/seriali finte. Le regressioni
rifiutano ACK inventati, RX nativo PSAVE/GAIN corrotto, duplicati, ordine
sbagliato, eventi non trusted e chiusura fallita. Nessun test apre browser,
porta seriale o dispositivo; nessun risultato finto viene pubblicato come
qualificazione hardware.
