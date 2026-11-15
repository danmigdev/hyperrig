# HyperRig

Laboratorio locale per il reverse engineering di UltraRig e lo sviluppo di un
firmware alternativo per M-VAVE TANK-G, TANK-B e TANK MINI.

**Stato: motore capture A2-Lite a tre canali/int32 ricostruito e compilabile;
porting del MINI in corso. Non è ancora un firmware completo installabile sul MINI.** Il nome HyperRig è quello
scelto per questo progetto indipendente.

L'[obiettivo concordato](docs/HYPERRIG_GOAL.md) comprende l'applicazione
UltraRig completa adattata al MINI, in sostituzione dello stock, e copie
locali di firmware e app con strumenti di reverse engineering e modifica.

## Risultati disponibili

- UltraRig alpha 11 / M5.71: quattro immagini G/B, v1/v2, scaricate da GitHub,
  verificate con SHA-256, decodificate e separate in `app.bin` e `cfg_tool.bin`.
- Firmware ufficiale `TANK MINI_009`: contenitore FWSC e applicazione estratti,
  con verifica dei CRC. Confermato AC791N/pi32v2, con una mappa flash diversa.
- Sorgenti originali HTML/JavaScript recuperati dall'editor e dall'APK.
- Bytecode Python dell'installer estratto e disassemblato senza eseguirlo.
- Pseudocodice C generato da Ghidra per tutti e cinque i firmware e listati
  pi32v2 delle aree flash/RAM. Il C è **parziale, inferito e non compilabile**.
- Parser Python utilizzabili per SFC/JLFS/FWSC, capture A2L1 e preset del MINI;
  CLI di identificazione e backup dei preset via MIDI, limitata alle letture.
- Modello A2-Lite in virgola mobile con rendering WAV offline, confrontato
  con il convertitore originale; non riproduce ancora il DSP intero del pedale.
- Motore capture C con caricatore, bias, ingresso mono/tre canali, layer
  dilatati, attivazioni, residuali e testa finale. **7.509 confronti con le
  istruzioni originali interpretate**, inclusi tutti i 23 layer della capture
  A2. Profilo supportato: tre canali/int32 e shift del percorso ottimizzato.
  Orchestrazione portabile propria; IR, effetti e frontend restano da integrare.
  Build UBSan/ASan e oggetto pi32v2 prodotti dalla toolchain JieLi.
- Percorso audio ALNK0 ricostruito per G e MINI: pin, buffer, IRQ e blocchi
  da 64 frame; differenza tra 44,1 kHz stock MINI e 48 kHz UltraRig identificata.
- Driver audio MINI compilato, con conversione campioni e gestione dei mezzi
  buffer DMA verificate sul PC. Codec/clock a 48 kHz, mute e coerenza cache
  restano da verificare sul dispositivo.
- Startup e linker MINI con tre ELF diagnostici, controllo delle aree flash/RAM
  e simulazione della copia dati/azzeramento BSS. Il probe DSP include la
  capture A2 e un'autoverifica numerica; **non è stato avviato sul pedale**.
- Watchdog P33, lettura dei clock, manutenzione cache, bus codec PA1/PA2 e
  coordinamento IRQ/worker ricostruiti; verifiche locali e oggetti pi32v2.
  I contributi sono documentati separatamente con i limiti hardware ancora aperti.
- Compositore dell'area applicativa MINI da ELF: directory e configurazione
  originali conservate, vecchio codice rimosso e CRC verificati. Produce un
  artefatto sperimentale offline, non un aggiornamento FWSC installabile.
- **Primo codice HyperRig eseguito sul MINI in RAM:** 8 casi delle primitive
  DSP superati, con CRC uguali ai kernel originali interpretati. Il probe ROM
  ha restituito un record verificato; motore A2 completo e audio restano da provare.
- **Motore A2L sintetico eseguito sul MINI in RAM:** tre layer, 230 frame,
  sei blocchi e ripetizione dopo reset con CRC corretti; stack privato e arena
  integri. È una prova distinta dalla capture originale a 23 layer e dall'audio.
- Identità `TANK MINI_009` confermata via BLE e USB. Ritorno dalla ROM al
  firmware stock verificato quattro volte, con preset invariati. **Backup completo
  della NOR: due copie da 1 MiB identiche**, CRC validi e firmware corrispondente
  allo stock 009. Nessuna scrittura flash effettuata; recupero da un'applicazione
  corrotta ancora da verificare.
- Handover del bootloader, varianti applicative interamente in flash e selettore
  dei clock ricostruiti. Candidato codec OSR64 preparato, ancora da provare sul pedale.
- Copie HyperRig dei quattro firmware G/B, installer Windows, editor web e
  APK Android `com.hyperrig.app`, ricostruito e firmato localmente. Sono in
  `build/hyperrig/`: **queste copie G/B non sono il port MINI**.

I sorgenti C originali del DSP UltraRig **non sono stati trovati**: il repository,
la sua cronologia e i fork pubblici controllati non li contengono. La
decompilazione non recupera nomi, commenti, tipi e struttura del progetto
originale. Il dettaglio delle ricerche è in [source-audit.json](research/source-audit.json).

## Dove leggere

- [Reverse engineering e risultati verificati](docs/REVERSE_ENGINEERING.md).
- [Porting TANK MINI: profilo, differenze e lavoro restante](docs/PORTING_TANK_MINI.md).
- [C nativo ricostruito e verifiche numeriche](docs/NATIVE_RECONSTRUCTION.md).
- [Percorso audio del MINI e confronto con il G](docs/TANK_MINI_AUDIO.md).
- [Driver audio MINI e conversione dei campioni](docs/MINI_AUDIO_DRIVER.md).
- [Startup, linker e programmi diagnostici MINI](docs/MINI_BOOT.md).
- [Prima esecuzione fisica del probe ROM HyperRig](docs/MINI_ROM_PROBE.md).
- [Motore A2L sintetico verificato sul MINI in RAM](docs/MINI_ROM_ENGINE.md).
- [Diagnostico codec in RAM: NACK e ripristino verificato](docs/MINI_ROM_CODEC.md).
- [Port dell'applicazione UltraRig completa](docs/MINI_ULTRARIG_PORT.md).
- [Editor HyperRig per il target MINI](docs/MINI_APP.md).
- [Protocollo ROM, verifica RAM e ritorno allo stock](docs/MINI_RECOVERY.md).
- [Lettura completa della NOR e verifica del backup](docs/MINI_FLASH_BACKUP.md).
- [Handover stock e varianti XIP](docs/MINI_HANDOVER.md).
- [Clock e vincoli di campionamento del MINI](docs/MINI_CLOCK.md).
- [Validazione ELF e contenitore stock MINI](docs/MINI_IMAGE.md).
- [Watchdog, clock e cache MINI](docs/MINI_PLATFORM.md).
- [Bus codec, mute e vincoli del campionamento](docs/MINI_CODEC.md).
- [Interrupt, worker audio e gestione dei ritardi](docs/MINI_RUNTIME.md).
- [Applicazioni e firmware rinominati HyperRig](docs/REBRANDING.md).
- [Provenienza e licenze](docs/PROVENIENZA.md).
- [Versioni esatte degli strumenti](research/sources.lock.json).

## Riprodurre l'analisi

Python 3.12 è necessario per leggere il bytecode 3.12 dell'installer. I parser
offline usano soltanto la libreria standard.

```powershell
python tools/bootstrap.py
python tools/fetch_artifacts.py
python -m hyperrig analyze
python tools/disassemble.py
python tools/map_audio.py
python -m unittest discover -s tests -v
python -m hyperrig port-status
```

Per la decompilazione, Java 21 o successivo e Ghidra 12.2; il bootstrap opzionale
scarica circa 570 MB e installa il modulo JieLi nella copia locale di Ghidra:

```powershell
python tools/bootstrap.py --decompiler
powershell -NoProfile -ExecutionPolicy Bypass -File tools/decompile.ps1 -Target tank-mini
```

Gli altri target sono `tank-g-v1`, `tank-g-v2`, `tank-b-v1`, `tank-b-v2`.
L'opzione ExecutionPolicy vale per quel processo e non modifica la configurazione
Windows. Gli strumenti di analisi non eseguono gli installer dei pedali.

Per compilare e verificare i componenti C su Windows serve WSL Ubuntu con
GCC e Python 3. Il compilatore JieLi viene scaricato nella directory locale:

```powershell
python tools/bootstrap.py --toolchain
python tools/build_native.py
```

Risultato: `build/native/hyperrig_dsp.pi32v2.o`, oggetto relocatable per il
target, e `analysis/native/verification.json`. Non è un'immagine da flashare.

Per costruire e controllare i programmi diagnostici MINI:

```powershell
python tools/verify_mini_audio.py
python tools/build_mini_boot.py --dsp
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf --elf build/mini-boot/hyperrig-mini-dsp-link-probe.elf
```

Per includere anche i tre componenti MINI e provare il worker con il DSP:

```powershell
python tools/verify_mini_platform.py
python tools/verify_mini_codec.py
python tools/verify_mini_runtime.py
python tools/build_mini_boot.py --bringup
python tools/package_mini_probe.py --elf build/mini-boot/hyperrig-mini-bringup-probe.elf --output build/mini-boot/hyperrig-mini-bringup-probe.app-area.bin --report research/mini-package.json
```

Questi comandi producono ELF, un'area applicativa sperimentale e prove locali.
Non generano un aggiornamento FWSC installabile e non inviano comandi al
dispositivo. Il probe integrato usa RAM fittizia: codec, clock e DMA reali
restano inattivi.

## Materiale locale recuperato

| Percorso | Contenuto |
|---|---|
| `recovered/ultrarig-original/web/` | HTML e JavaScript originali, compreso `nam2chip.js` |
| `recovered/android/` | asset web e configurazione dell'APK |
| `recovered/installer/` | bytecode, disassembly e costanti dell'installer |
| `recovered/ghidra/<target>/decompiled.c` | pseudocodice C e indice delle funzioni |
| `analysis/firmware/<immagine>/` | binari decodificati, stringhe, mappe, assembly, capture A2L |
| `analysis/tank-mini/` | firmware ufficiale MINI estratto e analizzato |
| `analysis/summary.json` | verifica automatica delle cinque immagini |
| `artifacts/` | pacchetti originali scaricati |
| `upstream/` | repository e header SDK usati come riferimento |

Queste directory restano locali e sono escluse da Git. Il repository versiona
strumenti, test, profili e documentazione; conserva le licenze insieme ai file
recuperati. Nessun repository remoto è stato creato.

## Collegamento del MINI

L'esemplare online ha risposto `TANK MINI_009` tramite il servizio BLE proprietario
AE40, caratteristiche AE41/AE42. La prova è registrata in
[hardware-observation.json](research/hardware-observation.json). La CLI qui sotto
usa RtMidi: su questo Windows il pedale Bluetooth non compare fra le sue porte.
La prova BLE è separata dal supporto RtMidi della CLI. Dopo un primo errore
nell'abilitazione delle notifiche, una nuova connessione ha confermato l'identità
e acquisito i 1.942 byte dei preset, con due letture identiche e struttura valida.
Il backup locale è in `artifacts/my-mini-presets/ble-20261115/`; hash e limiti
sono registrati nell'osservazione hardware. Non è un backup completo della flash.

Per un collegamento USB-MIDI, elencare le porte e scegliere gli indici corretti:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[midi]"
.venv\Scripts\python -m hyperrig ports
.venv\Scripts\python -m hyperrig identify --input 0 --output 0
.venv\Scripts\python -m hyperrig backup --input 0 --output 0 --directory artifacts\my-mini-presets
```

`0` è un esempio: usare gli indici restituiti da `ports`. Il programma verifica
l'identità `TANK MINI_...` prima di leggere i dati e confronta due letture della
banca. Questo salva i **preset**, non l'intera flash e non un'immagine di recupero.

Conversione NAM locale con il convertitore originale recuperato:

```powershell
node tools/nam_convert.cjs input.nam output.a2l
```

Il risultato è nel formato UltraRig A2L1; non è un file AM3/AM4 da caricare nel
firmware originale del MINI.

## Riferimento DSP sul PC

Il motore di riferimento legge i pesi quantizzati A2L1 e li interpreta in
virgola mobile. Mantiene convoluzioni causali, dilatazioni, residuali e stato
fra blocchi. Serve per verificare la ricostruzione: non è il DSP intero originale,
non simula le sue saturazioni e non è ottimizzato per il tempo reale.

```powershell
python -m hyperrig render-a2l analysis/firmware/m571_g_app/embedded-0.a2l input.wav output.wav
```

L'ingresso deve essere WAV mono PCM16 a 48 kHz; l'uscita deve essere un file
nuovo. Il comando segnala eventuale clipping. Per il confronto automatico con
il JavaScript originale serve Node.js; i test indicano esplicitamente gli skip
quando mancano Node o gli artefatti.

Validazione locale: **54 test superati, nessuno saltato**, più **7.509 confronti
nativi**, 112 controlli del layout A2L, 4.905 input non validi rifiutati e
6.942 casi con buffer di dimensione esatta e 400 blocchi del motore sotto
ASan/UBSan. Due flussi da 7.001 campioni verificano reset e continuità tra blocchi.
Comprendono CRC e
hash dei campioni, vettori MIDI catturati, trasporto simulato, casi DSP con
risultato analitico e confronto delle 49 misure di calibrazione su tre segnali.
Le prove audio e di avvio del nuovo codice sul pedale restano da eseguire.
