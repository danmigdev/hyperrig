# Provenienza del codice e degli artefatti

HyperRig è il repository locale di ricerca scelto dall'utente. Non è una
release di UltraRig, non è affiliato a M-VAVE e non attribuisce al progetto
la paternità del codice recuperato.

| Fonte | Materiale impiegato | Trattamento locale |
|---|---|---|
| [UltraRig](https://github.com/manuaguirre9/ultrarig) | Firmware, installer, editor, convertitore NAM | Originali in `artifacts/`, estratti in `recovered/`; LICENSE/NOTICE conservati |
| [M-VAVE download](https://www.m-vave.com/download) | Aggiornamento TANK MINI 009 | Campione ufficiale, hash fissato; binari esclusi da Git |
| [jl-misctools](https://github.com/kagaimiq/jl-misctools) | Riferimento ENC/SFC/JLFS | Repository MIT conservato in `upstream/`; parser HyperRig ricostruito e verificato sui campioni |
| [pi32v2-isa](https://github.com/jvitkauskas/pi32v2-isa) | Disassembler e tabella ISA | Codice MIT-0, tabella/documentazione CC0; usato dal tool locale |
| [ghidra-jieli](https://github.com/virtualabs/ghidra-jieli) | Specifica processore Ghidra | Apache-2.0; copia nella distribuzione Ghidra locale |
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Decompilatore | Distribuzione 12.2 verificata con il digest GitHub |
| [tankmini-linux](https://github.com/viniciusapl97/tankmini-linux) | Documentazione del protocollo e vettori catturati | MIT; riferimento per la nuova implementazione Python |
| [m-bootloader](https://github.com/jvitkauskas/m-bootloader) | Specifica AC791N/ROM, registri P33 e cache | MIT; solo riferimento SoC, nessun binario FM1/SMK37 usato sul MINI |
| [m-flasher](https://github.com/jvitkauskas/m-flasher) | CDB ROM e riferimento del client USB | Commit fissato; nessun loader per altre schede caricato sul MINI |
| [SDK AC79 mirror](https://github.com/amitv87/fw-AC79_AIoT_SDK) | Header di riferimento e LICENSE, `iis.h` e `cpu.a` per il selettore I2S | Origine ufficiale Gitee non risolvibile dalla rete locale; mirror, commit e hash registrati |
| [Toolchain JieLi](https://jl-update.oss-cn-shenzhen.aliyuncs.com/jieli-linux-toolchains-20260730.1.tar.xz) | Clang, linker e objdump pi32v2 | Usati localmente come strumenti via WSL; archivio verificato e ignorato da Git |
| [Apktool](https://github.com/iBotPeaches/Apktool) | Decodifica risorse/Smali e ricostruzione APK | Versione 3.0.3 verificata con digest della release |
| [Uber APK Signer](https://github.com/patrickfav/uber-apk-signer) | Allineamento, firma e verifica APK | Versione 1.3.0 verificata con checksum pubblicato; chiave di sviluppo locale |

Il codice UltraRig recuperato mantiene la PolyForm Noncommercial 1.0.0 e le
licenze dei componenti dichiarate nel pacchetto. Il nuovo nome del repository
non modifica quelle condizioni. Pseudocodice e assembly derivati non vengono
presentati come una nuova implementazione indipendente o come sorgenti originali.

Il parser A2L1 e il modello numerico `hyperrig/a2l_reference.py` sono ricostruiti
dal convertitore distribuito con UltraRig. Per questi file vengono conservati
il Required Notice e la PolyForm Noncommercial 1.0.0 in
`third_party/ultrarig/LICENSE.md`, insieme al `NOTICE.md` originale. Il riferimento
Float64 non viene presentato come una copia esatta del DSP intero del pedale.

Anche i file `firmware/src/hyperrig_dot.c`, `hyperrig_head.c` e i relativi
header sono ricostruzioni derivate dal firmware UltraRig; mantengono lo stesso
Required Notice e la stessa licenza. L'interprete locale esegue tre regioni
del campione originale, senza ridistribuire il firmware. La nuova struttura
C e i nomi delle funzioni non vengono attribuiti all'autore originale.

Le copie rinominate in `build/hyperrig/` conservano integralmente LICENSE,
NOTICE e THIRD_PARTY_LICENSES degli originali, anche come asset dell'APK.
La firma Android è identificata come HyperRig Local Development. Gli originali
rimangono separati per la verifica delle evidenze; vedere
[REBRANDING.md](REBRANDING.md).

Le coordinate dei repository, i commit, gli URL e gli SHA-256 sono in
`research/sources.lock.json` e `research/input-manifest.json`.
La cartella `upstream/` conserva anche i file LICENSE dei progetti clonati.
Nessun binario o sorgente recuperato è stato pubblicato in remoto.
