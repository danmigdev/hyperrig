# HyperRig MINI: editor completo per il port UltraRig

L'app derivata mantiene l'editor originale UltraRig alpha11: catene e routing
parallelo, preset e quattro scene, librerie capture/IR, conversione NAM/A2-Lite,
EQ, metering, tuner e controlli audio. Il target è **UltraRig adattato al MINI
come firmware autonomo**, che sostituisce interamente l'applicazione stock.
Non usa i sei moduli né i 21 preset del firmware M-VAVE come architettura del
prodotto. Non contiene un bridge USB-MIDI/SysEx stock.

## Prova locale dell'interfaccia

```powershell
python -X utf8 tools/build_mini_app.py
python -m http.server 8765 --bind 127.0.0.1 --directory build/hyperrig-mini/web
```

Aprire <http://127.0.0.1:8765/tankmini.html#demo>. La demo originale rimane
completa ed è indicata come **offline, nessun pedale collegato**. Non genera
audio nel MINI. L'editor conserva otto banchi da quattro slot e quattro scene:
la compatibilità di questa memoria persistente dovrà essere verificata nel
port, senza sostituirla silenziosamente con il layout stock da 21 × 92 byte.

Senza `#demo`, la build predefinita può inviare soltanto `PING`; non dichiara
una connessione a un firmware funzionante. Il riconoscimento atteso è
`PONG tankm_fw M5.xx ...`, con il resto del formato UltraRig invariato. Le
identità `tankg_fw`, `tankb_fw` e `TANK MINI_009` vengono rifiutate prima delle
query iniziali e delle modifiche. Il nome Bluetooth o il VID USB da soli non
identificano un port MINI valido.

L'APK già esistente
`build/hyperrig/HyperRig-local-android.apk` rimane la variante G/B: non è stato
modificato. Ora esiste anche la variante separata
[`HyperRig-MINI-local-android.apk`](../build/hyperrig-mini-integrated/android/HyperRig-MINI-local-android.apk),
derivata con il manifest della candidata integrata. Conserva Capacitor, BLE,
bridge file/share e licenze originali. Nessuna installazione sul telefono o
connessione fisica è stata eseguita per sviluppare questa app.

## APK MINI locale

```powershell
python -X utf8 tools/build_mini_android.py --check-only
python -X utf8 tools/build_mini_android.py
python -X utf8 -m unittest tests.test_mini_android -v
```

Il builder usa per default
`build/hyperrig-mini-integrated/firmware-manifest.json`; accetta anche
`--firmware-manifest` e `--output`. La candidata associata alla consegna
attuale è `f8835a7fd45b1b324d66c457434c7943d70525ed5eb98b514aaac1095031f068`.
L'APK prodotto ha SHA-256
`194431db62554d0d286de9bb1e2b27b863f8593efbf16193192ab5565b4597cc`;
hash di input, toolchain, asset, log e controlli sono in
[`android-report.json`](../build/hyperrig-mini-integrated/android/android-report.json).
Le ricompilazioni possono cambiare l'hash dell'APK: usare il report della
build effettiva.

`assets/public/index.html` nell'APK UltraRig originale è **byte-identico** al
frontend web fissato. Viene quindi usata la stessa derivazione MINI, senza
sostituire un frontend Android diverso. Gli otto DEX del pacchetto HyperRig
locale già rebrandizzato e cinque asset Capacitor/Cordova/converter vengono
conservati byte per byte. Apktool 3.0.3 e uber-apk-signer 1.3.0 sono verificati
contro gli hash locali fissati; il manifest finale viene decodificato di nuovo.
I sei test offline verificano provenienza, gate BLE, conservazione dei bridge,
label, certificato e comportamento del piano senza build.

Il pacchetto usa il nome visualizzato **HyperRig MINI**, namespace
`com.hyperrig.app` e la chiave locale HyperRig esistente; firma v2/v3 e
allineamento sono verificati. Un'eventuale installazione sostituirebbe quindi
l'app HyperRig G/B con lo stesso namespace, non le installerebbe affiancate.
Il builder non avvia adb, installazioni, server o trasporti.

Il trasporto Android originale è il plugin nativo Capacitor **BluetoothLe**;
gli altri componenti sono App e `HyperRigNative` per file/condivisione.
Non è presente un plugin seriale USB nativo e non ne è stato aggiunto uno.
USB CDC/Web Serial appartiene al percorso desktop. Il profilo dell'APK
consente query dopo PONG MINI corretto, con scritture e pannello disabilitati;
le eventuali prove USB scoped non autorizzano BLE. Il pairing originale può
salvare bond indipendentemente dal gate dei comandi, quindi "query consentite"
non significa assenza di ogni scrittura persistente del trasporto. Avvio
Android, pairing, NUS e funzionamento del firmware restano da verificare sul
dispositivo reale.

## Provenienza e trasformazioni

`tools/build_mini_app.py` deriva direttamente
`recovered/ultrarig-original/web/tankg.html`, SHA-256
`247d152045a9d8f987281e7e943c1ea359ccc2db1392f6a0cb439587717e88e6`.
Il convertitore `nam2chip.js` originale ha SHA-256
`af584a732fa8a0b03a388871947d490a383c5094d9391fed0f48b6336f255183`.
Il builder verifica questi hash e l'unicità di ogni modifica ancorata; una
nuova versione del frontend richiede una revisione, non un patch permissivo.
`LICENSE.md`, `NOTICE.md` e `THIRD_PARTY_LICENSES.md` sono copiati invariati.
Il rebranding usa il modulo locale già esistente; i link esterni di update,
telemetria e supporto originali rimangono sostituiti con `hyperrig.invalid`.

`app/mini/mini-profile.js` aggiunge identità e capabilities, senza sostituire
le implementazioni originali dei comandi o dei trasporti. Il controllo è
inserito all'inizio di `Pedal.cmd`, prima della coda e di ogni scrittura.
`ERR MINI_APP ...` è un rifiuto locale, chiaramente distinguibile da una
risposta firmware. Gli stati di connessione e le chiavi Bluetooth hanno uno
spazio separato da G/B. La perdita della connessione cancella l'identità
verificata; il nuovo collegamento deve rifare il controllo PONG.

Il pannello fisico è un profilo MINI a **tre switch**, con pin, LED e manopole
ancora sconosciuti. Non viene riciclato il disegno G/B da 15 manopole e quattro
switch. I comandi `FSA`, `FSMODE`, `FSPRESS`, `FSDO`, `FSLED`, `LEDCFG` e le
viste che assumono il pannello G/B rimangono bloccati. Questo non converte le
quattro scene software in tre scene: sono due concetti distinti.

Il gate dell'app impedisce comandi host; non spegne i task del firmware. In
particolare, l'audit audio del port ha individuato il writer G
`0x02015858..0x020158C2` su PA0..PA3, sovrapposto a PA1/PA2 del codec MINI.
La sua rimozione o rimappatura resta un requisito del firmware anche quando
l'editor opera soltanto in lettura. Un profilo app corretto non rende da solo
avviabile un'immagine G sul MINI.

## Contratto firmware necessario

Le fonti primarie locali sono il frontend originale e i byte di
`analysis/firmware/m571_g_app/app.bin` (SHA-256
`4005315c3d58e20beb8e8f5c33e6a65d34f9512051ccf6b43ef2c5eb6a9c604e`).
Il progetto upstream è fissato in `research/sources.lock.json` al commit
`658c89c2bcb2743c19c5caf0fb9704a8ce68212c` di
[UltraRig](https://github.com/manuaguirre9/ultrarig/tree/658c89c2bcb2743c19c5caf0fb9704a8ce68212c).
`research/mini-app-protocol.json` conserva **168 call site**, le espressioni
esatte di richiesta, predicato di completamento, timeout e riga originale.
68 nomi di comando si risolvono direttamente; 102 call site hanno argomenti
dinamici, dei quali 14 non risolvono staticamente il nome. L'inventario non
spaccia queste espressioni JavaScript per comandi completamente risolti.

| Funzione | Richieste UltraRig | Completamento richiesto dal frontend |
|---|---|---|
| Identità | `PING` | `PONG <versione> <data> <ora>...`; token MINI `tankm_fw` |
| Catalogo effetti | `FXT` | righe tipo/parametri, poi `FXT end` (`fin` legacy) |
| Catena e risorse | `FXS`, `MEM`, `MODEL`, `LVL` | `FXS peak=...` termina la catena; le altre risposte iniziano col nome comando |
| Modifiche effetti | `FXA`, `FXR`, `FXM`, `FXE`, `FXP`, `FXL`, `FXOS` | prefissi/predicati originali, errori `ERR`; non un ACK binario MINI |
| Routing e capture EQ | `FXMIX`, `FXXO`, `FXIR`, `AMP`, `AMPX`, `AMPEQ` | terminatori `FXMIX end`, `FXXO end`; `AMPEQ volume=` o `gain=` |
| Preset e scene | `PLIST`, `PLOAD`, `PSAVE`, `PNEW`, `PDEL`, `PNAME`, `SNAP*` | `PLIST end current=...`; `SNAPS dddd current=...`; risposte save/load originali |
| Capture NAM/A2-Lite | `LDBEGIN n`, `LDB off hex`, `LDEND crc32`, `CLIST/CLOAD/CSAVE/CREAD/CDEL` | `OK LDBEGIN`, `OK LDB off n`, `LOAD ...`; `CLIST end` |
| IR | `IRBEGIN samples gain rate`, `IRB off hex`, `IREND crc32`, `ILIST/ILOAD/ISAVE/IREAD/IDEL` | `OK IRBEGIN`, `OK IRB off n`, `IR ok ...`; `ILIST end` |
| Audio e globali | `AUDIO`, `GEQ`, `GAIN`, `HPF`, `LIM`, `SPUR`, `GLIDE`, `SPILL`, `STW`, `GSAVE` | query e modifiche distinte dagli argomenti; `GSAVE` persiste |
| Tempo/accordatore | `BPM`, `TAP`, `TUNER`, `TUNE` | protocollo originale; nessun sostituto stock |
| Eventi e diagnostica | `EVT`, `CRASH`, `LIFE`, `CLKSTATE`, `LVLSUB` | terminatori propri; `@L` e `@K` sono asincroni |
| Bluetooth | `BLE`, `AUTH` | bonding/MTU/chiavi originali; modifiche non abilitate nel profilo di sola lettura |
| Pannello fisico | `FSA`, `FSMODE`, `FSPRESS`, `FSDO`, `FSLED`, `LEDCFG` | richiede una mappa MINI nuova; bloccato |

Tutte le richieste sono testo terminato da `\n`; il client accetta anche
risposte CRLF. Una sola richiesta ordinaria è in attesa per volta. Le righe
`@L`/`@K` non completano una richiesta. `NOISE ms=`, `CALIB` ed
`ERR CALIB stopped` hanno percorsi asincroni speciali già presenti nel frontend.
Il limite USB è 31 caratteri fino a M4.82, 190 da M4.83, escluso newline.
I blocchi capture/IR usano offset, dati esadecimali e CRC32 IEEE al termine.
Le funzioni parser e upload originali sono mantenute, incluso il loro diverso
comportamento su timeout: questo lavoro non certifica il recupero di tutte
le transazioni originali in caso di perdita del collegamento.

Il port deve conservare i gestori e le semantiche originali, non soltanto le
stringhe della tabella. Per una prima connessione di sola lettura servono
almeno PING, FXT, MODEL, CLIST, MEM, FXXO, LVL, FXS, PLIST, SNAPS,
SNAPNAME e le query di EQ/globali. `LVLSUB` resta disabilitato nel profilo
readonly; il frontend ripiega sul polling `LVL`. Upload, modifica e salvataggio
richiedono un successivo collaudo della memoria e del motore sul MINI.

## Evidenza USB e BLE nel firmware originale

Il template USB a `0x02035085` contiene VID `3654`, PID `4155`. Il codice a
`0x0201B9E2` copia 18 byte, poi le istruzioni a `0x0201B9F0` (`51 31 89 4B`)
scrivono `0x51` al byte 11: il **PID restituito è `5155`**. Il solo template
statico avrebbe dato una conclusione sbagliata. Il prodotto UTF-16 originale
è `Tank-G UltraRig` a `0x0203A264`; il rebranding/targeting della nuova immagine
deve verificarlo separatamente.

Il template configurazione a `0x020350B9` descrive CDC ACM: interfaccia
controllo 0, classe 02/sottoclasse 02/protocollo 01, interrupt IN `82` da
8 byte; interfaccia dati 1, classe 0A, bulk OUT `02` e IN `83` da 64 byte.
La lunghezza totale e il numero interfacce sono riempiti dal firmware.
L'editor originale apre Web Serial a 115200 baud e filtra VID `3654`.

I quattro UUID NUS sono verificati anche nei byte del firmware:

- servizio `6e400001-b5a3-f393-e0a9-e50e24dcca9e`;
- RX `6e400002-b5a3-f393-e0a9-e50e24dcca9e`;
- TX `6e400003-b5a3-f393-e0a9-e50e24dcca9e`;
- pairing `6e400004-b5a3-f393-e0a9-e50e24dcca9e`.

Il frammento BLE iniziale è 20 byte; il frontend aumenta fino a 244 dopo
la risposta MTU del firmware. Il bridge Android usa il plugin Capacitor
già presente, la pagina desktop usa Web Bluetooth. L'app stock MINI AE40 e
USB-MIDI `4C4A:C755` non sostituiscono questi trasporti. Avere lo stesso SoC
rende questi byte pertinenti all'audit, ma non prova che stack USB/BLE,
clock, IRQ, buffer o radio funzionino dopo il port. Nessuna enumerazione
CDC/NUS di una build MINI è stata dichiarata qui.

## Profili progressivi, senza attesa circolare

La build base è `identity=true, read=false, write=false, panel=false`.
Quando esiste un'immagine standalone da verificare, il builder accetta
`--firmware-manifest <file.json>` con questo contratto:

```json
{
  "target": "tank-mini",
  "architecture": "standalone-ultrarig-port",
  "firmware_version": "tankm_fw M5.71 rel ble",
  "image_path": "build/percorso-della-build-da-verificare.bin",
  "image_sha256": "SHA256_REALE_DELL_ARTEFATTO",
  "capabilities": {"read": true, "write": false, "panel": false},
  "hardware_verified": false
}
```

Il builder controlla il file e il suo hash; la stringa PONG deve corrispondere
esattamente a `firmware_version`. **Le letture non richiedono una precedente
prova hardware**: servono proprio a validare la nuova build. Il PONG non
trasporta SHA-256: questo è un vincolo della configurazione distribuita e
della procedura di test, non un'attestazione crittografica del pedale.

Il vecchio profilo completo `write=true` richiede `hardware_verified=true` e un `write_validation`
con `path`/`sha256` di un report locale che abbia `target=tank-mini`, lo stesso
`image_sha256` e `all_required_editor_mutations_verified=true`. Nessun report
di questo tipo è stato prodotto qui. Per qualificare il primo preset è ora
disponibile il profilo limitato descritto sotto: non richiede di qualificare
prima upload NAM/IR o tutte le altre funzioni. `panel=true` viene sempre rifiutato
finché non sarà implementata la vera mappa MINI. Questo stato non nasconde
le funzioni UltraRig: distingue ciò che l'interfaccia conserva da ciò che
è già eseguibile sul dispositivo.

## Scritture qualificate per richieste esatte

Il manifest può mantenere `write=false` e aggiungere `command_capabilities`.
Ogni chiave è un comando originale e ogni valore è una lista di richieste
complete: qualificare `FXP 1 0 50` non autorizza un altro valore, indice o ID;
`PSAVE 31 Scratch` non autorizza un altro slot o nome. Non esistono wildcard,
prefissi, intervalli o abilitazioni implicite. Il profilo distribuito resta
`command_capabilities={}`, senza prove hardware o scritture abilitate.

| Comando supportato | Ambito | Evidenza necessaria per la richiesta specifica |
|---|---|---|
| `FXP id indice valore` | Parametro live di un blocco esistente | ACK col valore effettivo, FXS e ripristino |
| `FXE id 0/1` | Bypass/attivazione di un blocco | ACK, FXS e ripristino; facoltativo per la prima prova |
| `PLOAD slot` | Caricamento, modifica ciò che suona | ACK, stato riletto, ritorno allo stato precedente |
| `PSAVE slot nome` | Salvataggio preset e selezione dello slot | ACK, PLIST, PLOAD e stato riletto |
| `PDEL slot` | Eliminazione dello slot temporaneo | ACK e PLIST coerente senza lo slot |
| `SNAP 0..3` | Selezione scena | ACK, SNAPS/FXS, ripristino della scena precedente |
| `SNAPSAVE 0..3` | Salvataggio della scena nel preset corrente | ACK con preset atteso, ricaricamento e stato riletto |

Gli ID del blocco e il preset corrente non sono proprietà immutabili. La
lista di richieste limita il protocollo trasmesso; non blocca cambiamenti di
scena dal pannello e non attesta automaticamente lo stesso parametro in un
altro tipo di effetto. La prova deve registrare e verificare anche quel
contesto. Non vengono abilitate operazioni in base al solo nome del comando
o all'identità USB/PONG.

Per esempio, **dopo le prove reali**, un manifest potrà richiedere:

```json
{
  "command_capabilities": {
    "FXP": ["FXP 1 0 50", "FXP 1 0 51"],
    "PLOAD": ["PLOAD 0", "PLOAD 31"],
    "PSAVE": ["PSAVE 31 Scratch"],
    "PDEL": ["PDEL 31"],
    "SNAP": ["SNAP 0"],
    "SNAPSAVE": ["SNAPSAVE 0"]
  },
  "command_validation": {"path": "research/prova-reale-specifica.json", "sha256": "HASH_REALE_DEL_REPORT"}
}
```

È un frammento illustrativo, non un report valido né una build abilitata.
Le liste devono corrispondere **esattamente** a `verified_requests` del report.
Il builder verifica `hardware_verified=true`, `read=true`, `write=false` e:

- `schema=1`, `kind=mini-app-command-validation`, `target=tank-mini`, versione
  e hash dell'immagine identici al manifest;
- `editor_source_sha256` uguale al frontend originale fissato,
  `hardware_executed=true`, `transport=usb-cdc`;
- riferimenti `trace` e `backup`, ciascuno con `path` e `sha256` di file locali
  non vuoti conservati; l'hash del report stesso è controllato separatamente;
- `restoration_verified=true` e un'osservazione per ogni richiesta esatta,
  con `request`, `ack_verified=true`, `readback_verified=true`;
- per PSAVE/PDEL/SNAPSAVE, anche `persistence_readback_verified=true`, attestato
  dopo ricaricamento o verifica dell'eliminazione, non dal solo ACK.

Questi campi sono asserzioni di una prova revisionata. Il builder controlla
vincoli e integrità dei file, non trasforma un log simulato in una misura
hardware. I test usano fixture temporanee esplicitamente sintetiche; nessuna
di esse è pubblicata come prova reale. Non è ancora consentito usare questo
schema per BLE: le sue prove di trasporto devono essere aggiunte separatamente.
Il gate controlla il trasporto sia quando accetta PONG sia prima di ciascun
comando; BLE, trasporto sconosciuto e cambiamento di trasporto non ereditano
i permessi USB. Le query documentate restano disponibili dopo l'identità.

Il gate si applica nella coda originale prima della scrittura. Pannello,
caricamento capture/NAM, IR, globali e comandi non elencati restano negati.
L'app mostra le operazioni limitate abilitate dal profilo. Il preflight di
`savePreset` richiede anche `SNAPSAVE 0` per la creazione automatica della
scena A e, se necessario, SNAPSAVE della scena corrente. Il Save della barra
controlla analogamente tutti i comandi previsti prima di iniziare. Il flusso
"All scenes" e l'export completo, che possono usare TUNER, attraversare scene
e ricaricare preset, rimangono esclusi dal profilo limitato. Il codice e la
demo originali restano disponibili. Il preflight evita un rifiuto locale
prevedibile dopo PSAVE, non rende atomici i cambiamenti sul dispositivo.

### Primo ciclo minimo per app, persistenza e ripristino

Prima della prova conservare un backup revisionato del firmware/dati del
port e lo stato del preset/scena di partenza. Una lettura PLIST/FXS da sola
non è un backup di tutte le scene e delle risorse. Scegliere un preset
salvato senza modifiche live pendenti e con un parametro semplice già
identificato; uno slot temporaneo deve risultare libero in una PLIST completa.

1. Registrare identità, FXT, FXS, SNAPS, PLIST, PSTAT e riferimenti capture/IR.
   Provare PLOAD del preset di partenza e SNAP della scena da ripristinare,
   verificando che lo stato rimanga quello atteso.
2. Eseguire FXP col valore di prova e rileggere FXS; provare anche il valore
   originale, poi riapplicare quello di prova. Ogni richiesta deve avere
   ACK e stato coerente, senza cambiamenti inattesi agli altri blocchi.
3. Usare il vero salvataggio dell'app verso lo slot temporaneo, includendo i
   suoi SNAPSAVE necessari. Rileggere PLIST/SNAPS, cambiare solo in RAM il
   parametro e ricaricare con PLOAD/SNAP: deve tornare il valore salvato.
   Questo esercita il ricaricamento, non prova ancora persistenza dopo power cycle.
4. Tornare al preset/scena iniziali e verificare l'intero stato acquisito;
   eliminare soltanto lo slot temporaneo con PDEL e verificare PLIST. Un
   errore o timeout non è una prova di ripristino e non autorizza retry ciechi.

Per questo ciclo bastano FXP, PLOAD, PSAVE, SNAP, SNAPSAVE e PDEL con gli
argomenti effettivamente provati. Non servono FXA/FXR, import, IRBEGIN,
LDBEGIN, CSAVE, GSAVE o comandi di aggiornamento. Il ripristino è logico:
non annulla usura o sequenze della memoria NOR. Il report può abilitare
queste sole richieste senza impostare `all_required_editor_mutations_verified`.

## Verifiche offline

```powershell
python -X utf8 -m unittest tests.test_mini_app_protocol -v
```

I 19 test verificano rifiuto stock/G/B, binding della versione, confini tra
identity/read/write/panel, reset dell'identità, niente comandi concatenati,
posizione dei gate prima dell'I/O, sintassi degli script completi, derive
su sorgente cambiato, hash descrittori e copie immutate delle licenze. Un test
esegue anche la coda `Pedal` originale con un trasporto fittizio: sulla linea
arrivano soltanto `PING` e `FXT`; save e pannello non raggiungono `write()`.
I test del profilo limitato controllano variazioni di parametri/slot/nome,
prove mancanti o alterate, hash trace/backup, readback persistente e ripristino.
La funzione originale `savePreset` viene inoltre eseguita con un pedale finto:
senza SNAPSAVE non invia PSAVE; con i grant esatti invia `PSAVE 31 Scratch`,
`SNAPS` e `SNAPSAVE 0`. La CLI CDC ha altri 14 test in
[`MINI_APP_PROTOCOL_PROBE.md`](MINI_APP_PROTOCOL_PROBE.md).
La pagina completa è stata anche renderizzata in Edge headless da file locale
con `#demo` e rete bloccata: il DOM mostra `TANK MINI demo` e l'avviso offline.
Lo screenshot è `build/mini-app-browser-check/demo.png`. È una verifica
dell'interfaccia originale adattata, non dell'esecuzione firmware o dell'APK.
