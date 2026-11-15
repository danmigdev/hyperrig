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

Questa consegna è l'editor web derivato. L'APK già esistente
`build/hyperrig/HyperRig-local-android.apk` rimane la variante G/B: non è stato
ricompilato né dichiarato compatibile con MINI da questo lavoro. Il nuovo
frontend conserva il codice del bridge Capacitor e del trasporto BLE originali;
potrà essere incluso nella variante Android quando il port e la sua identità
saranno verificati. Nessuna installazione o connessione fisica è stata eseguita
per sviluppare questa app.

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

`write=true` richiede invece `hardware_verified=true` e un `write_validation`
con `path`/`sha256` di un report locale che abbia `target=tank-mini`, lo stesso
`image_sha256` e `all_required_editor_mutations_verified=true`. Nessun report
di questo tipo è stato prodotto qui. `panel=true` viene sempre rifiutato
finché non sarà implementata la vera mappa MINI. Questo stato non nasconde
le funzioni UltraRig: distingue ciò che l'interfaccia conserva da ciò che
è già eseguibile sul dispositivo.

## Verifiche offline

```powershell
python -X utf8 -m unittest tests.test_mini_app_protocol -v
```

I 13 test verificano rifiuto stock/G/B, binding della versione, confini tra
identity/read/write/panel, reset dell'identità, niente comandi concatenati,
posizione dei gate prima dell'I/O, sintassi degli script completi, derive
su sorgente cambiato, hash descrittori e copie immutate delle licenze. Un test
esegue anche la coda `Pedal` originale con un trasporto fittizio: sulla linea
arrivano soltanto `PING` e `FXT`; save e pannello non raggiungono `write()`.
La pagina completa è stata anche renderizzata in Edge headless da file locale
con `#demo` e rete bloccata: il DOM mostra `TANK MINI demo` e l'avviso offline.
Lo screenshot è `build/mini-app-browser-check/demo.png`. È una verifica
dell'interfaccia originale adattata, non dell'esecuzione firmware o dell'APK.
