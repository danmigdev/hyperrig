# Prove app di modifica e salvataggio MINI

[probe_mini_app_mutation.py](../tools/probe_mini_app_mutation.py) è separato
dal client readonly storico. Il comando predefinito stampa il piano offline:
non enumera dispositivi, non importa pyserial e non apre porte. I test attuali
usano soltanto un pedale simulato. Non attestano un port applicativo avviato,
una connessione desktop reale o una prova Android.

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py
python -B -X utf8 -m unittest tests.test_mini_app_mutation tests.test_mini_app_transport tests.test_mini_app_protocol
```

Sono passati 55 test: 22 nuovi e 33 regressioni. Il simulatore conserva preset
e stato live separatamente, cambia gli ID runtime al caricamento e permette
di simulare timeout, risposte incoerenti, modifiche esterne e mancata
persistenza. Un test esegue anche i parser JavaScript originali in Node.

## Fonti e risposte

Il client verifica gli hash del frontend originale e del firmware G già
fissati da `build_mini_app.py`. I call site originali usano 1,5 secondi per
FXP/FXE/SNAP/SNAPSAVE/PDEL e 8 secondi per PSAVE/PLOAD. Le stringhe di risposta
sono controllate nei byte G, comprese queste posizioni relative ad `app.bin`:

| Operazione | Risposta ordinaria | Offset |
|---|---|---:|
| FXP | `FXP ok <valore effettivo>` | `0x35CD1` |
| FXE | `FXE ok`, con statistiche CPU | `0x35A51`, `0x39ED1` |
| PSAVE | slot, nome, blocchi, riferimenti capture/IR | `0x3704D` |
| PLOAD | slot, nome, `missing`, riferimenti, tempo | `0x37584` |
| SNAP | indice, `missing`, tempo | `0x36B4A` |
| SNAPSAVE | indice e preset modificato | `0x36824` |
| PDEL | indice eliminato | `0x35DE8` |

FXP restituisce il valore effettivo, che può differire da quello richiesto.
FXE non restituisce lo stato on/off: serve FXS. Il client accetta soltanto
le risposte ordinarie ricostruite; `missing`, errori capture o suffissi non
riconosciuti non diventano una prova riuscita. Un errore `ERR … kept …`, una
risposta malformata o un timeout interrompono la sessione senza retry.

## Ciclo live

`live` richiede l'immagine locale verificata dal manifest, versione MINI
esatta, `hardware_verified=true` e capability `read=true`. Questa è la
qualifica della candidata avviata, non l'asserzione che tutte le mutazioni
siano già provate. PONG non legge l'hash dell'immagine dal dispositivo.

Il client acquisisce FXT, FXS, PLIST e SNAPS, salva il backup dello stato
osservato e ripete le letture prima della modifica. FXP usa un parametro
esistente e il suo range FXT; il primo esperimento cambia un solo passo di
`nivel_db`, `ganancia_db` o `mezcla_pct`, escludendo i casi sensibili alle
risorse identificati nel frontend. FXE è un'alternativa esplicita sullo stato
on/off di un blocco realmente presente. Queste restrizioni delimitano la
prova rappresentativa; non descrivono tutti i parametri supportati dall'app.

Dopo ACK e nuovo FXS, il client ripristina il valore iniziale e richiede ACK,
FXS, preset e scena coerenti. Se un ACK FXP valido riporta un valore diverso
ma il readback è coerente e nessun altro stato è cambiato, viene ripristinato
l'originale; la prova non qualifica la richiesta iniziale. Un errore ambiguo
non provoca un tentativo cieco di ripristino. Il report conserva la fase,
la richiesta di ripristino e lo stato della sua verifica.

Esempio operativo, da usare soltanto dopo l'avvio reale della candidata e
sostituendo porta, manifest, ID e indice con quelli osservati:

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py live --port COM8 --firmware-manifest build/mini-app-manifest.json --block 7 --parameter 0 --log build/live-001.jsonl --backup build/live-001-before.json --report build/live-001-proof.json
```

Per FXE usare `--operation FXE --block <id>`, senza `--parameter`. I tre file
di output devono essere nuovi e distinti. L'esempio non è stato eseguito su
hardware. Il backup live copre lo stato osservato, non l'intero banco né lo
storico interno dei delay/reverb.

## Ciclo persistente separato

`save` richiede anche un banco esportato nel formato originale
`ultrarig-preset` o nella variante rinominata `hyperrig-preset`, versione 1,
con hash e lista coerenti con PLIST. Non esegue l'export: quello originale
può caricare preset e scene. Prima di PSAVE controlla che lo stato iniziale
sia rappresentato dal preset/scena del backup, evitando di perdere modifiche
live non rappresentate quando ricarica l'originale.

La prima prova supporta una catena seriale senza blocchi IR o cab IR esterna.
Legge inoltre GAIN, AMPEQ, BPM, PCOLOR, STW, MODEL e SNAPNAME. Non invia comandi
NAM/IR o firmware. Un preset con scene deve avere una scena corrente valida:
il protocollo non offre qui un comando per ripristinare la selezione `-1`
quando esistono scene salvate.

La sequenza concreta è:

1. Nuovo snapshot e PLIST invariata; lo slot scelto deve essere libero.
2. `PSAVE <slot> HyperRig_Test`; controllo di ACK, PLIST e stato live.
3. Modifica live di un parametro come marcatore; `PLOAD <slot>` e selezione
   della scena iniziale provano che i valori salvati sostituiscano il marcatore.
4. `SNAPSAVE 0` sul solo slot temporaneo; verifica dell'indice e del preset
   nella risposta, della nuova scena e dell'assenza di altri cambiamenti.
5. Un secondo marcatore live, seguito da PLOAD e SNAP 0, verifica separatamente
   la persistenza della scena. SNAPSAVE non può mascherare un PSAVE fallito:
   PSAVE è già stato riletto prima di questa fase.
6. PLOAD del preset originale e ripristino della scena iniziale; confronto dei
   valori e delle impostazioni osservate, ammettendo nuovi ID runtime.
7. Una nuova verifica identifica lo slot temporaneo creato da questa prova;
   solo allora PDEL elimina quello slot. PLIST finale e stato devono tornare
   uguali a quelli iniziali.

Esempio, con un hash reale del backup al posto del segnaposto:

```powershell
python -B -X utf8 tools/probe_mini_app_mutation.py save --port COM8 --firmware-manifest build/mini-app-manifest.json --slot 31 --bank-backup artifacts/my-bank.hyperrig.json --bank-sha256 <SHA256> --block 7 --parameter 0 --log build/save-001.jsonl --backup build/save-001-before.json --report build/save-001-proof.json
```

Il client non può cancellare slot preesistenti. Se il nome o l'inventario del
temporaneo cambiano, oppure una risposta è ambigua, non lo elimina e conserva
l'esito incompleto. Il ritorno allo stato logico non annulla l'usura NOR.
Il caricamento dopo salvataggio prova la rilettura da quel percorso firmware;
non è una prova di tenuta dopo spegnimento né un confronto completo di tutti
i contenuti NOR preesistenti.

## Evidenza e app operativa

Il report mantiene il formato `mini-app-command-validation` legato a
immagine, versione, fonti del protocollo, trace e backup. Il campo legacy
`verified_requests` contiene le richieste esatte provate; per il salvataggio
include PSAVE e SNAPSAVE 0, senza concedere i comandi di pulizia.

Il nuovo modello `representative-families-v1` separa `supported_by_protocol`
da `physically_exercised_requests`. Nei test questi ultimi sono vuoti e
`hardware_executed=false`; le richieste simulate stanno in un campo distinto.
Le famiglie operative sono FXP, FXE, PLOAD, PSAVE, SNAP e SNAPSAVE. Le prove
rappresentative non affermano che ogni valore sia stato provato fisicamente.
`all_required_editor_mutations_verified` resta false.

Il gate storico delle richieste esatte non basta per un'app utilizzabile:
blocca altri valori o nomi e il salvataggio originale richiede anche
SNAPSAVE. La nuova revisione del gate deve usare le famiglie qualificate,
con sintassi e range dai dati FXT/FXS/PLIST/SNAPS correnti, mantenendo le
conferme originali per sovrascrivere preset. La candidata e l'APK audio v2
già costruiti non vengono rigenerati da questo probe.

La prova reale desktop richiede ancora avvio del port, CDC `3654:5155`, PONG
MINI coerente e i roundtrip fisici. Android usa il trasporto BluetoothLe/NUS
originale, con pairing/auth e frammentazione distinti: una prova USB non
abilita BLE. Il controllo originale del pairing tramite footswitch richiede
anche il mapping hardware appropriato; HYK1 ha verificato i tre ingressi
insieme, non quella combinazione operativa Android.
