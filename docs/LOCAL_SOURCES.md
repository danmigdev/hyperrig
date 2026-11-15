# Copie locali e modifiche HyperRig

Il requisito di conservare firmware e app UltraRig è registrato in
[HYPERRIG_GOAL.md](HYPERRIG_GOAL.md). Il comando seguente verifica gli hash degli
originali e inventaria i materiali effettivamente presenti, senza scaricare
né eseguire gli installer:

```powershell
python -B -X utf8 tools/inventory_local_sources.py
```

Il risultato è [local-source-inventory.json](../research/local-source-inventory.json).
Gli originali restano separati dai prodotti HyperRig, con versione, provenienza
e SHA-256. Le cartelle di estrazione e i binari sono locali e ignorati da Git;
le coordinate per riacquisirli sono conservate nel repository.

| Materiale | Percorso locale | Possibilità di modifica |
|---|---|---|
| Firmware originali G/B, v1/v2 e pacchetti app | `artifacts/alpha11/` | Copie di riferimento immutate |
| Editor e convertitore originali | `recovered/ultrarig-original/web/` | HTML/JavaScript distribuito, leggibile |
| Asset originali Android | `recovered/android/assets/` | HTML/JavaScript e configurazione Capacitor |
| Installer Windows estratto | `recovered/installer/` | Bytecode Python 3.12, costanti e disassemblato |
| Decompilazione G/B | `recovered/ghidra/tank-{g,b}-v{1,2}/` | Pseudocodice C inferito e mappa delle funzioni |
| DSP A2 ricostruito | `firmware/src/`, `firmware/include/` | C compilabile, con confronti sui kernel originali |
| Port integrale MINI | `firmware/mini/audio_port/`, `tools/audit_mini_*_port.py`, `tools/audit_mini_boot_contract.py` | Shim C e patch controllate sui byte originali |
| Editor MINI | `app/mini/`, `tools/build_mini_app.py` | Profilo e adattamenti del codice originale |
| Ricostruzione delle copie G/B | `hyperrig/branding.py`, `tools/rebrand.py` | Rebuild firmware, installer e APK HyperRig |

Il firmware MINI integrale contiene l'applicazione UltraRig G, con le patch
di scheda elencate dal compositore. L'applicazione stock MINI non viene usata
come contenitore del DSP. I campioni stock servono per ricostruire la scheda e
per il ripristino.

Non abbiamo recuperato un progetto C originale completo ricompilabile di
UltraRig. Una parte è stata ricostruita in C; il resto è modificabile attraverso
assembly, pseudocodice e patch binarie controllate. Analogamente, il bytecode
dell'installer non equivale ai suoi file Python originali. L'inventario espone
queste differenze senza attribuire al materiale recuperato una completezza
che non è stata raggiunta. Licenze e attribuzioni restano invariate come
descritto in [PROVENIENZA.md](PROVENIENZA.md).
