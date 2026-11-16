# MINI: eccezione sul codice aggiunto

La prova reale dell'editor del 16 novembre 2026, conservata in
`build/mini-desktop-real-03/connected-proof.json`, ha ricevuto il PONG completo
`tankm_fw M5.71 rel ble` con suffisso `safe`, più stato, modello, preset e
diagnostica. L'applicazione comunica realmente via USB CDC. Questa prova non
qualifica ancora l'audio o le mutazioni dei preset.

Il crash precedente contiene `cpu=0`, `dbg=0x1000`, `emu=0`,
`reti=0x02076AAE`, `rets=0x020053AA`; la traccia ETM comincia da
`0x02076AAC`. Il sorgente SDK primario associa il bit 12 di `DBG_MSG` a
`c0_pc_limit_err_r`. Il PC salvato è all'ingresso dell'adattatore audio v2,
prima delle sue chiamate GPIO/codec; il ritorno coincide con il call originale
modificato a `0x020053A6`. La consegna di un'eccezione può essere ritardata:
RETI non certifica da solo quale sia l'ultima istruzione completata.

Il codice originale `debug_init` imposta i registri condivisi così:

| Registro | Indirizzo | Valore originale |
|---|---:|---:|
| `PC_LIMIT0_H` | `0x01EEE380` | `0x02056780` |
| `PC_LIMIT0_L` | `0x01EEE384` | `0x02000120` |
| `PC_LIMIT1_H` | `0x01EEE388` | `0x01C1F088` |
| `PC_LIMIT1_L` | `0x01EEE38C` | `0x01C00000` |

CPU0 chiama `debug_init` a `0x020011C6`, CPU1 a `0x02000AE6`.
Il ramo CPU1 programma entrambi gli intervalli. L'entry guard aggiunta gira
prima di questa inizializzazione; l'adattatore audio viene chiamato dopo.
Questo spiega perché l'entry guard poteva partire pur trovandosi fuori dal
vecchio intervallo del codice flash.

La correzione proposta modifica una sola istruzione di sei byte a
`0x0200067E` (offset area `0x67E`, NOR `0x467E`):

```text
c1 ff 80 67 05 02   r1 = 0x02056780
c1 ff f2 74 07 02   r1 = 0x020774F2
```

`0x020774F2` è la fine effettiva di `app.bin` per l'append v2, entry guard
compresa. L'API calcola la nuova istruzione dal parametro `executable_end`;
il verificatore richiede che coincida con `0x02000120 + len(app.bin)` nel
contenitore JLFS con CRC validi. Non elimina la protezione PC. Restano
identici il limite inferiore flash, l'intervallo RAM, i controlli stack e
write, e tutti gli enable debug. L'intervallo flash ora comprende anche i
dati iniziali RAM fra il testo originale e l'append: con i due intervalli
esistenti, questo è l'effetto dell'estensione contigua, non una separazione
hardware fra codice e dati.

Nel G originale il valore `0x02056780` compare anche nelle due istruzioni a
`0x020001B8` e `0x020001DC`: lì è la sorgente della copia RAM. Il modulo
controlla tutte e tre le occorrenze letterali e modifica solo quella del
limite PC. Una sostituzione globale romperebbe lo startup.

File nuovi, separati dagli artefatti installati:

- `firmware/mini/pc_limit_port/patches.py`: patch assertiva, inventario dei
  consumer, simulazione delle istruzioni del setter e gate per la candidata.
- `tools/audit_mini_pc_limit.py`: collega PONG/crash fisici ai byte installati
  e al sorgente SDK; produce esclusivamente un rapporto offline.
- `tests/test_mini_pc_limit.py`: casi positivi e negativi per entrambe le CPU,
  bound esatto, copia RAM, enable debug, CRC e identità della prova.
- `research/mini-pc-limit.json`: hash degli input e risultati del modello.

```powershell
C:\Python312\python.exe -B -X utf8 -m unittest tests.test_mini_pc_limit
C:\Python312\python.exe -B -X utf8 tools/audit_mini_pc_limit.py --output research/mini-pc-limit.json
```

La prova offline localizza e corregge il limite errato. Non dimostra che la
nuova immagine abbia eseguito il codec, avviato I²S o prodotto audio; questi
rimangono esiti da osservare dopo una futura installazione separata. Il
modulo non cancella il crash persistente o forza l'uscita dal modo sicuro.

La fonte SDK è
[JieLi AC79 `debug.c`, commit ffbb2a8](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/cpu/wl82/debug.c).
La copia locale e il suo SHA256 sono indicati nel rapporto; attribuzioni e
licenze originali rimangono quelle delle fonti conservate.
