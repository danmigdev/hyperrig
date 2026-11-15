# Verifica del protocollo app HyperRig MINI via USB CDC

`tools/probe_mini_app.py` prepara la verifica del protocollo originale UltraRig
nel port integrale MINI. La CLI apre una porta soltanto con il sottocomando
esplicito `read`; importazione e comando predefinito non enumerano dispositivi.
Questo lavoro ha usato esclusivamente trasporti simulati. Non dimostra ancora
enumerazione CDC, esecuzione del port, audio o scritture sul MINI.

La fonte delle richieste è
[`tankg.html`](../recovered/ultrarig-original/web/tankg.html), SHA-256
`247d152045a9d8f987281e7e943c1ea359ccc2db1392f6a0cb439587717e88e6`.
Il probe controlla l'hash e le ancore del protocollo prima di preparare una
sessione. Non usa USB-MIDI, SysEx stock o il protocollo della ROM di recupero.
L'evidenza dei descrittori è in
[`MINI_APP.md`](MINI_APP.md) e
[`mini-app-protocol.json`](../research/mini-app-protocol.json).

| Identità USB | Significato per il probe |
|---|---|
| `3654:5155` | Candidata CDC UltraRig; anche G usa questi ID. Serve poi `PONG tankm_fw …`. |
| `4C4A:C755` | Stock MINI USB-MIDI, incompatibile. |
| `4C4A:8057` | ROM di recupero Jieli, incompatibile. |
| `3654:4155` | Solo valore del template prima della modifica runtime del PID; rifiutato. |

L'enumerazione legge soltanto le porte seriali esposte dal sistema operativo.
Un dispositivo MIDI o ROM può quindi non comparire affatto: una lista vuota
non dimostra che il pedale sia scollegato. ID USB mancanti non vengono dedotti
dal nome della porta. Non c'è selezione automatica della prima porta.

## Uso previsto dopo l'avvio del port

Il piano è interamente offline e non richiede pyserial:

```powershell
python -X utf8 tools/probe_mini_app.py
```

Per le future operazioni seriali serve `pyserial`, installabile separatamente
con `python -m pip install pyserial`. La seguente enumerazione non apre porte:

```powershell
python -X utf8 tools/probe_mini_app.py enumerate
```

Preparare un manifest locale riferito all'immagine effettivamente candidata.
Questo esempio è riferito alla candidata baseline locale del formatter, non
certifica che sia installata o completa per la scheda:

```json
{
  "target": "tank-mini",
  "architecture": "standalone-ultrarig-port",
  "firmware_version": "tankm_fw M5.71 rel ble",
  "image_path": "build/mini-ultrarig/hyperrig-mini-g-derived.app.bin",
  "image_sha256": "4e74d0c0b1c1f491afdaa92e441d4504efcaff4237b4af1706e57a6e434a20ab",
  "capabilities": {"read": true, "write": false, "panel": false},
  "hardware_verified": false
}
```

Salvato per esempio come `build/mini-app-read-manifest.json`, può essere usato
sia dal probe sia dall'editor. Sostituire percorso/hash quando cambia candidata;
il caricatore ricalcola l'hash del file locale e rifiuta discrepanze. Per
generare l'editor in una directory separata, senza sovrascrivere la build
predefinita o il suo report:

```powershell
python -X utf8 tools/build_mini_app.py --firmware-manifest build/mini-app-read-manifest.json --output build/hyperrig-mini-read --report build/hyperrig-mini-read/report.json
```

Con il port realmente avviato e la sua porta nota, un primo controllo limita
la sessione al solo `PING` usando `--queries` senza argomenti. Questi comandi
**aprono la porta e inviano richieste**, a differenza del piano precedente:

```powershell
python -X utf8 tools/probe_mini_app.py read --port COM8 --firmware-manifest build/mini-app-read-manifest.json --log build/mini-cdc-ping-001.jsonl --queries
python -X utf8 tools/probe_mini_app.py read --port COM8 --firmware-manifest build/mini-app-read-manifest.json --log build/mini-cdc-read-001.jsonl
```

`COM8` è un esempio da sostituire. La directory del log deve già esistere;
un log esistente viene rifiutato prima di enumerare/aprire la porta. Per una
selezione ridotta usare, per esempio, `--queries MEM PLIST PSTAT`. Ogni sessione
inizia comunque con `PING`, una sola volta.

## Framing, risposte e limiti

Le richieste sono ASCII con terminatore LF, una alla volta. Il trasporto usa
115200 baud, 8N1, nessun flow control, timeout di lettura 50 ms e di scrittura
1 s. La risposta viene ricomposta da chunk arbitrari e decodificata UTF-8 solo
a riga completa; CRLF è ammesso. DTR/RTS sono impostati a false prima
dell'apertura, senza impulsi o cambi successivi. Il comportamento fisico delle
linee all'apertura dipende anche da OS/driver e resta da verificare sul port.
La creazione con `Serial(port=None)` e questo limite del driver sono descritti
nell'[API ufficiale pyserial](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).

I timeout derivano dai call site originali `Pedal.cmd`; i numeri di riga
seguenti si riferiscono al frontend fissato dall'hash, non alla build derivata.

| Richiesta letterale | Completamento | Timeout | Riga |
|---|---|---:|---:|
| `PING` | `PONG …`, poi versione MINI esatta del manifest | 700 ms | 10351 |
| `MODEL` | prefisso `MODEL` | 1500 ms | 5451 |
| `MEM` | prefisso `MEM` | 3000 ms | 5466 |
| `LVL` | prefisso `LVL` | 800 ms | 5413 |
| `FXT` | riga esatta `FXT end` o `FXT fin` | 3000 ms | 5392 |
| `FXS` | `^FXS (peak\|pico)\b` | 2500 ms | 5414, 5506 |
| `FXMIX` | riga esatta `FXMIX end` o `FXMIX fin` | 1500 ms | 5426 |
| `FXXO` | riga esatta `FXXO end` | 1200 ms | 14215 |
| `PLIST` | `PLIST end/fin current/actual=N`, lista coerente | 4000 ms | 12067 |
| `PSTAT` | prefisso `PSTAT` | 2000 ms | 11075 |
| `SNAPS` | prefisso `SNAPS` | 1500 ms | 8380 |
| `SNAPNAME` | prefisso `SNAPNAME end` | 1500 ms | 8388 |
| `CLIST` | prefisso `CLIST end` o `CLIST fin` | 4000 ms | 14089 |

La selezione predefinita dopo PING è `MODEL MEM LVL FXS PLIST PSTAT SNAPS
SNAPNAME`. Non sono accettati argomenti, comandi arbitrari, upload, reset,
abbonamenti a eventi o modifiche. `FXS end` non è il terminatore reale.
Il parser PLIST mantiene i 32 slot UltraRig e il limite originale di 23 unità
UTF-16 per il nome. Rifiuta slot duplicati, disordinati, fuori intervallo,
righe tronche e preset attivo assente. Una lista incoerente non diventa una
lista vuota. Il probe non applica i retry del frontend originale.

`@…`, `NOISE ms=…`, `CALIB …` ed `ERR CALIB stopped…` sono registrati a parte;
non completano una richiesta. Gli altri `ERR`, i timeout, una scrittura
parziale e gli errori di decoding/trasporto chiudono logicamente la sessione:
nessun retry, riconnessione o comando successivo. Prima di ciascuna richiesta
i byte preesistenti vengono registrati e scartati; input che non diventa
inattivo entro 500 ms impedisce l'invio. I limiti sono 8192 byte per riga,
256 KiB per risposta e 4096 righe non vuote. Una risposta arrivata oltre il
timeout rimane nel log e non viene accettata.

Il log JSONL registra tempi UTC/monotonic, contesto manifest, richieste, byte
ricevuti in esadecimale, righe e cause di interruzione; può includere nomi e
contenuto descrittivo dei preset. I byte vengono conservati anche quando il
parser rifiuta la risposta. `PONG` verifica identità/versione, **non legge
l'hash del firmware dal dispositivo**: il campo
`image_hash_attested_by_device` resta false. Completare queste letture non
qualifica audio, stabilità, salvataggi o altri comandi dell'editor.

## Verifiche offline e gate dell'editor

```powershell
python -X utf8 -m unittest tests.test_mini_app_transport -v
```

I 14 test usano porte finte; non importano un driver per aprire dispositivi.
Coprono frammentazione UTF-8/CRLF, risposte asincrone, identità G/B/stock
rifiutate, comandi vietati, dati tardivi, timeout, disconnessione, scritture
parziali, limiti, conservazione dei log e chiusura della porta simulata.
Un test esegue in Node il parser PLIST originale e confronta i risultati.

Un altro genera davvero l'editor in una directory temporanea con l'hash
della candidata locale, `read=true`, `write=false`, `hardware_verified=false`;
esegue poi il gate JavaScript: PONG MINI accettato, PLIST consentito, PSAVE
negato. La lettura non aspetta una qualificazione hardware già completata:
serve proprio a raccoglierla. I file congelati dell'editor e il report
`research/mini-app-protocol.json` non sono stati modificati.

## Proposta per le successive prove di scrittura, non implementata

Il primo ciclo utile riguarda un solo parametro live, dopo aver qualificato
letture, recupero e condizioni audio. Dal frontend originale alle righe
7576–7578: richiesta `FXP <id> <indice> <valore>`, risposta
`FXP ok <valore_effettivo>`. La proposta è:

1. Acquisire FXT, FXS, preset e scena attivi; scegliere un parametro esistente
   con limiti noti e senza effetti strutturali su routing, memoria, risorse o
   modalità audio. Conservare il valore originale e lo stato degli altri blocchi.
2. Applicare un diverso valore ammesso; richiedere ACK con valore effettivo e
   rileggere FXS per verificare quel valore e l'assenza di cambiamenti inattesi.
3. Ripristinare il valore originale con FXP; richiedere ACK e FXS coerenti con
   lo stato semantico iniziale. Un timeout interrompe la prova: non è prova
   di ripristino riuscito e non autorizza un retry cieco.

Questo verifica soltanto quella modifica live. Non dimostra assenza di
scritture NOR automatiche, né ripristina lo storico interno di delay/reverb.
Il profilo completo dell'app abilita le scritture in blocco e richiede un report
con `all_required_editor_mutations_verified=true`, legato allo stesso hash
d'immagine. Un singolo ciclo FXP **non soddisfa quel requisito**: occorre
qualificare le altre famiglie, oppure usare le nuove capabilities per richieste
esatte documentate in [MINI_APP.md](MINI_APP.md). Queste mantengono `write=false`
e richiedono prove soltanto per il subset esplicito: nessuna è abilitata ora.
Non generare il flag di qualifica completa a partire dalle sole letture o dal
solo ciclo live. Questa estensione dell'editor non aggiunge scritture alla CLI.

Per qualificare la persistenza serve una prova separata su uno slot
temporaneo realmente libero e dopo backup: `PSAVE <slot> <nome>` (nome senza
virgolette aggiunte; ACK `PSAVE ok`, timeout originale 8 s), PLIST,
`PLOAD <slot>` (ACK `PLOAD ok`, 8 s) e lettura dello stato; infine ripristino
del preset/scena e delle eventuali modifiche live precedenti, eliminazione
del solo slot temporaneo con `PDEL <slot>` (ACK `PDEL ok`) e nuova PLIST.
PSAVE cambia anche il preset corrente; gli snapshot richiedono ulteriori
verifiche proprie. Il ripristino è logico, non annulla usura o sequenze NOR.
Anche l'export completo originale non è una semplice lettura: le funzioni
`pioReadPreset`/export attraversano scene con SNAP e, in alcuni percorsi,
PLOAD. Il probe non le invoca.
