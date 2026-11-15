# Primo preset HyperRig sul MINI

Il probe persistente precedente non copre il primo avvio senza preset G:
`validate_saved_baseline()` richiede un preset corrente salvato e il suo
backup; il ciclo finale lo ricarica ed elimina il temporaneo. Con
`PLIST ... current=-1` si ferma prima di PSAVE. Quel probe e il client
readonly restano invariati.

[probe_mini_app_first_preset.py](../tools/probe_mini_app_first_preset.py)
gestisce separatamente questo caso. Crea `HyperRig_Test` in uno slot
osservato libero e lo lascia intenzionalmente salvato, con scena A. Non
invia PDEL e non tenta di ripristinare un preset inesistente. Se esiste già
un preset corrente, questo percorso si ferma prima di scrivere: è il caso
coperto dal probe precedente.

## Sequenza effettiva

Prima di qualsiasi scrittura acquisisce PONG, FXT, FXS, PLIST, SNAPS,
GAIN, AMPEQ, BPM, PCOLOR, STW, MODEL e SNAPNAME. Conserva sia le risposte
sia lo stato interpretato in un file nuovo. Rilegge l'intero stato prima
di PSAVE e richiede che sia rimasto uguale. Non serve un export di un
presunto banco G vuoto; gli eventuali altri slot elencati devono rimanere
presenti con gli stessi metadata e non vengono caricati o cancellati.

1. `PSAVE <slot> HyperRig_Test`, ACK esatto e nuovo PLIST/FXS/stato.
2. Un marcatore live verificato; `PLOAD <slot>` deve ripristinare i valori
   salvati. Se c'è una scena iniziale selezionata viene riapplicata.
3. Solo dopo la prima prova di PSAVE, `SNAPSAVE 0` crea o aggiorna la
   scena A del nuovo slot. ACK, inventario scene e stato devono coincidere.
4. Un secondo marcatore; PLOAD e `SNAP 0` devono ripristinare
   separatamente lo stato della scena appena salvata.
5. Una lettura finale deve essere stabile. Il nuovo preset e la scena A
   rimangono memorizzati e selezionati, con il suono osservato verificato
   tramite il protocollo.

L'originale `sceneAOnSave()` in
[tankg.html](../recovered/ultrarig-original/web/tankg.html) aggiunge
`SNAPSAVE 0` dopo PSAVE quando non esistono scene. La prova separata
impedisce a SNAPSAVE di mascherare un PSAVE non persistito. Le risposte,
gli intervalli FXT, i parser e i timeout sono riusati dal probe precedente.
Gli ID runtime degli effetti possono cambiare con PLOAD: si confrontano
posizione, tipo e valori, non l'identità numerica appena riassegnata.

## Marcatore anche con catena vuota

In modalità `auto` viene preferito un parametro FXP realmente presente,
con un passo verso il basso entro il suo range FXT. Se manca un parametro
adatto, viene diminuito di 1 dB il gain di uscita; se è già a -30 dB si
può diminuire quello d'ingresso. Non si aumenta un gain per fare la prova.
Se entrambi sono al minimo e non esiste un altro marcatore ammesso, non
viene inviato PSAVE. FXE può essere scelto esplicitamente su un blocco
reale; non viene inventato un blocco per superare una catena vuota.

Il frontend originale `buildGains()` usa `GAIN <in> <out>`, con range
`-30..12` dB. Il firmware G effettua il clamp a `0x02008DE2..0x02008E2C`,
richiamato dal ramo `0x02013140`; la stringa di risposta è a offset
`0x365BE` di `app.bin`. Il probe richiede ACK e nuova lettura GAIN,
insieme agli altri campi, prima di tentare PLOAD. Non invia GSAVE.

Un capture attivo che PSAVE dichiara non associato alla libreria non viene
trattato come salvato: la prova si ferma prima del marcatore/reload.
Il protocollo non permette qui di ripristinare una selezione scena -1
quando esistono già scene RAM non selezionate; questo caso si ferma prima
di scrivere. Nessun errore provoca retry, cancellazione o ripristino cieco.
Il report incompleto indica la fase raggiunta e se il nuovo slot era già
comparso nella lista.

## Uso e prove offline

Import e comando predefinito non enumerano dispositivi e non importano
pyserial:

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py
python -B -X utf8 -m unittest tests.test_mini_app_first_preset tests.test_mini_app_families tests.test_mini_app_mutation tests.test_mini_app_transport tests.test_mini_app_protocol
```

Il coordinatore può usare il sottocomando esplicito `create` solo con il
manifest della candidata realmente avviata, con letture qualificate. Gli
output devono essere nuovi, distinti e nella workspace. Esempio da adattare
alla porta e al manifest reali; non è una prova hardware già eseguita:

```powershell
python -B -X utf8 tools/probe_mini_app_first_preset.py create --port COM8 --firmware-manifest build/mini-app-manifest.json --slot 0 --log build/first-001.jsonl --backup build/first-001-before.json --report build/first-001-proof.json
```

Senza `--slot` sceglie il primo slot libero dal PLIST completo. `--operation
GAIN` seleziona il marcatore sui gain; FXP richiede `--block` e `--parameter`,
FXE soltanto `--block`. La prova termina mantenendo il nuovo preset,
anziché simulare un ritorno allo stato di selezione iniziale.

## Evidenza distinta e revisione delle capability app

Il nuovo report è `mini-app-first-preset-validation`, modello
`representative-first-preset-v1`. Dichiara esplicitamente:

- `restoration_verified=false`: non esisteva un preset corrente da ripristinare;
- `preset_intentionally_retained=true` e `final_sound_verified=true` solo
  dopo entrambi i reload e la lettura finale;
- `physically_exercised_requests` soltanto per le operazioni realmente
  eseguite sul trasporto indicato; i mock compilano invece `simulated_requests`.

Il builder accetta questa forma tramite un ramo distinto. Verifica gli
stessi binding di immagine, versione, fonti e trasporto delle prove
precedenti, poi **riesegue il probe offline sul TX/RX grezzo conservato**.
La riproduzione deve consumare tutti i comandi nello stesso ordine e
ottenere esattamente stato iniziale, FXT, risultato finale e osservazioni
dichiarati. È fissato anche l'hash dell'implementazione del nuovo probe.
I flag da soli o il solo ACK non bastano; questa verifica prova coerenza
documentale, non autentica fisicamente un log. La semantica delle vecchie
prove con ripristino e cleanup resta invariata.

La revisione aggiunge la famiglia operativa GAIN. Viene abilitata soltanto
con una prova rappresentativa sullo stesso trasporto; il runtime valida
la sintassi e `-30..12`, e richiede un contesto GAIN o LVL valido. Un ACK
incoerente, PLOAD, SNAP o disconnessione invalidano quel contesto finché
viene riletto. I due knob originali usano la stessa coda e gli stessi
comandi. La prova su una catena vuota può qualificare GAIN, PSAVE, PLOAD,
SNAPSAVE e SNAP; **non qualifica FXP o FXE non eseguiti**. USB non abilita
automaticamente Android/BLE. Non viene attribuito supporto generale a
upload, FXAdd o comandi del pannello.

## Effetti attesi su USR e limiti

La normale gestione G dei preset può ruotare fra i 18 settori fisici del
journal e riscrivere la coppia di preset in un settore. Un salvataggio
intenzionale non promette quindi di cambiare una sola pagina, né di
conservare USR identica byte per byte. Mapper, limiti di scrittura e
distinzione da VM/OTA/BTIF sono documentati in
[MINI_PRESET_STORAGE_REVIEW.md](MINI_PRESET_STORAGE_REVIEW.md).
La conservazione verificata dall'installer riguarda il momento prima
dell'avvio app; non impedisce le successive scritture normali autorizzate
dal salvataggio.

Il confronto degli altri slot copre i loro metadata PLIST, non tutti i
payload nascosti. Il backup di stato copre i campi osservati, non la storia
interna di delay/reverb. Reload e readback non costituiscono prova di
tenuta dopo un'interruzione di alimentazione, né una misura dell'audio.
I test di questa revisione sono mock: non dichiarano avvio G, salvataggio
reale, editor desktop o Android fisicamente qualificati.
