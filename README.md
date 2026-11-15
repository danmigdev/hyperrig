# HyperRig

Laboratorio locale per il reverse engineering di UltraRig e lo sviluppo di un
firmware alternativo per M-VAVE TANK-G, TANK-B e TANK MINI.

**Stato: quattro routine DSP native e caricatore A2L ricostruiti e compilabili; porting del MINI
in corso. Non è ancora un firmware completo installabile sul MINI.** Il nome HyperRig è quello
scelto per questo progetto indipendente.

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
- Due routine dot, ingresso mono/tre canali e testa A2-Lite ricostruiti dai
  byte del G. Caricatore C con CRC, riordino dei pesi e conversione dei bias:
  **7.089 confronti con le istruzioni originali interpretate**, build con
  UBSan/ASan e oggetto pi32v2 prodotto dalla toolchain JieLi. I layer centrali
  della rete restano da ricostruire.
- Percorso audio ALNK0 ricostruito per G e MINI: pin, buffer, IRQ e blocchi
  da 64 frame; differenza tra 44,1 kHz stock MINI e 48 kHz UltraRig identificata.
- Identità del pedale letto via BLE: `TANK MINI_009`. Backup totale e prova
  del firmware HyperRig sul dispositivo ancora da eseguire.
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
L'identificazione BLE è stata una prova separata, non un supporto BLE già
integrato nella CLI. Il successivo tentativo di backup preset via BLE non è
riuscito ad attivare le notifiche e non ha prodotto un backup.

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

Validazione locale: **40 test superati, nessuno saltato**, più **7.089 confronti
nativi**, 112 controlli del layout A2L, 4.905 input non validi rifiutati e
6.942 casi con buffer di dimensione esatta sotto ASan/UBSan. Comprendono CRC e
hash dei campioni, vettori MIDI catturati, trasporto simulato, casi DSP con
risultato analitico e confronto delle 49 misure di calibrazione su tre segnali.
Le prove audio e di avvio del nuovo codice sul pedale restano da eseguire.
