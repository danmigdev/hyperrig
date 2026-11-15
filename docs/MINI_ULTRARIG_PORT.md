# Port integrale UltraRig G → HyperRig MINI

La candidata conserva **l'intera applicazione UltraRig G v2 M5.71**: 485.772
byte, inclusi motore audio, OS, USB, BLE, gestione preset e driver originali.
Non incorpora l'applicazione stock MINI. Il pacchetto stock e il backup della
singola unità servono a ricostruire hardware, avvio e partizioni.

Il risultato attuale è una candidata **offline incompleta per l'hardware**,
non un firmware installabile o già avviato. Non è stato eseguito alcun
accesso al pedale da questo audit.

```powershell
python -X utf8 tools/audit_mini_ultrarig_port.py
```

Il comando genera:

* `build/mini-ultrarig/hyperrig-mini-g-derived.app.bin`: area applicativa di
  516.096 byte, SHA-256
  `4e74d0c0b1c1f491afdaa92e441d4504efcaff4237b4af1706e57a6e434a20ab`;
* `research/mini-ultrarig-port.json`: provenienza, istruzioni, patch,
  directory, confronti NOR, limiti e verifiche riproducibili.

La candidata contiene la directory MINI, cinque patch di identità/marchio
e una patch alla geometria VM. Ogni patch confronta i byte originali prima
di modificarli. Invertendo queste sole patch si riottiene esattamente
`app.bin` G originale. Tutti i CRC JLFS vengono ricalcolati e verificati
dopo una nuova decodifica SFC. Il report mantiene `flashable=false`,
`board_port_complete=false` e `boot_verified_on_mini=false`.

## Formato e spazio

| Proprietà | UltraRig G v2 | MINI stock 009 |
|---|---:|---:|
| SoC/formato | AC791N, pi32v2, SFC/JLFS | AC791N, pi32v2, SFC/JLFS |
| Chiave applicativa verificata dai CRC | `0x980F` | `0x980F` |
| Area fisica applicazione | `[0x4000,0x7B000)` | `[0x4000,0x82000)` |
| Dimensione area | `0x77000` | `0x7E000` |
| Offset `app.bin` nell'area | `0x120` | `0x120` |
| Entry CPU | `0x02000120` | `0x02000120` |
| `app.bin` | 485.772 byte | 511.032 byte |
| `cfg_tool.bin` | 383 byte | Gli stessi 383 byte |

Il formato e lo spazio sono compatibili; ciò non dimostra compatibilità
elettrica o dei parametri di inizializzazione. L'area MINI offre 28.672 byte
in più della confezione G. Considerando la fine effettiva dei file, il
limite massimo per codice aggiuntivo è **29.653 byte**, prima di eventuali
allineamenti. Il codice può iniziare a `0x02076AAC`; `cfg_tool.bin` viene
spostato dopo di esso e la sua voce JLFS aggiornata. G apre questo file
tramite `mnt/sdfile/app/cfg_tool.bin` nel frammento `0x0201FAB8..1FAF6`.

Questo spazio appartiene all'applicazione da sostituire. Il builder non
occupa flash vuota nelle partizioni dati e non produce un'immagine completa
dell'unità da 1 MiB né un contenitore FWSC.

## Bootloader e RAM

L'installer UltraRig originale distribuisce una **area applicativa**, non
un nuovo bootloader persistente. Il bytecode recuperato `build_target`,
linee sorgente 1623–1652, copia il dump corrente e sostituisce `APP_AREA`.
SPL rimane invariato; USR ha politica predefinita `keep`. Esistono rami
separati di migrazione VM per firmware G97/Tank-B, riparazione e ripristino:
non è corretto affermare che ogni operazione dell'installer scriva soltanto
l'app. Il loader `wl82loader.bin` viene eseguito in RAM. Il pacchetto
originale non dichiara supporto MINI.

Conservare il bootloader factory del MINI è dunque coerente con
l'architettura UltraRig; l'applicazione factory viene sostituita per intero.
La compatibilità completa del passaggio di controllo resta da provare.

| Regione o registro G ricostruito | Valore |
|---|---|
| Copia RAM iniziale | `[0x01C00000,0x01C2030C)` da `0x02056780` |
| BSS | `[0x01C2030C,0x01C38050)` |
| SP / SSP iniziali | `0x01C350B8` / `0x01C360B8` |
| USP / SP CPU1 | `0x01C363B8` / `0x01C373B8` |
| Heap | `[0x01C38060,0x01C7FBA0)`, 293.696 byte |
| Copie/clear esterni richiesti dal reset | Zero byte |
| Copia privata contesto boot G | `0x01C7FD4C` |

Il reset e l'heap rientrano nella RAM interna da 512 KiB. Questo non prova
l'assenza di ogni altro accesso a RAM esterna. Gli slot usati dai probe ROM
non restano liberi: ricadono nelle allocazioni dell'applicazione completa.

Il bootloader MINI passa `r0=0x01C7FE08`. G legge anche otto byte a
`r0+80` e quattro a `r0+88`, ai siti `0x0200045C` e `0x0200046A`.
La corretta inizializzazione di queste estensioni nel percorso MINI senza
SDRAM non è ancora dimostrata. Questo è un controllo di handover residuo,
separato dai CRC validi del bootloader stock.

## Partizioni: directory, geometria e contenuto

| Nome | G originale | Candidata MINI |
|---|---|---|
| VM | `[0x7B000,0xBD000)` | `[0x82000,0xBE000)` |
| PRCT | `[0,0x7B000)` | `[0,0x82000)` |
| BTIF | `[0xBD000,0xBE000)` | `[0xBE000,0xBF000)` |
| OTP | `[0xBE000,0xBF000)` | Voce rimossa, assente nel MINI |
| USR | `[0xBF000,0xFF000)` | Identica |

Le partizioni si ricavano dalle directory originali, con CRC verificati.
Conservare alla cieca la voce OTP G la farebbe sovrapporre a BTIF del MINI.
Il builder usa i soli header di partizione MINI e segnala esplicitamente
la rimozione di OTP. Non copia o riscrive i contenuti VM/BTIF/USR/key_mac.

Le prove di accesso G sono distinte:

* **VM:** il loop `0x02022208..0x0202225A` confronta il nome `vm`
  (`0x02035851`) con le voci JLFS, ne carica offset/dimensione e passa i
  metadati tramite ioctl205. La base non è semplicemente fissata a `0x7B000`.
* **BTIF:** apertura di `mnt/sdfile/app/btif` a `0x0201FB00`, lettura
  dei metadati e accesso a base+512 per la configurazione. La nuova
  posizione viene quindi espressa dalla directory in questo percorso.
* **USR:** `0xBF000` è anche hardcoded; la funzione `0x020026BA` restituisce
  le posizioni degli slot, con casi speciali `0xDD000` e `0xDE000`.
  Questi indirizzi restano invariati.
* **OTP:** nessuna stringa `OTP` compare dentro `app.bin`; la sola occorrenza
  nell'area G è il nome in directory. Questa ricerca **non dimostra**
  l'assenza di accessi indiretti, per indice o a registri security della NOR.
  L'OTP hardware della NOR e la partizione JLFS denominata OTP sono oggetti
  diversi. La compatibilità di tutti i consumatori resta un gate aperto.

La VM fisica dichiarata dalla directory è più grande dei banchi effettivi
usati dal SDK. G limita la parte attiva a 64 KiB, due banchi da 32 KiB;
MINI stock limita NOR a 16 KiB, due banchi da 8 KiB. La candidata modifica
solo la coppia di immediati G:

| CPU | Prima | Dopo |
|---|---|---|
| `0x0202067E` | `20 e9 80 0b`: `if (r0 >= 65536)` | `20 e9 80 0c`: `if (r0 >= 16384)` |
| `0x02020682` | `60 e0 80 0b`: `r0 = 0x10000` | `60 e0 80 0c`: `r0 = 0x4000` |

La modifica viene ricodificata dalla tabella ISA pinned: cambiano solo i
campi immediati, conservando registro, predicato e lunghezza. Il reset MINI
avvia l'inizializzazione VM con limite NOR16384 nel frammento
`0x0201FD72..0x0201FD9C`.

Sul backup congelato SHA-256 `72db5e70…5f8a180`, il banco B a `0x84000`
contiene 134 record con CRC validi; write pointer `0x8531E`, uso 59,7412%.
Altro banco e coda sono cancellati. Il parser ricostruito dalle regole
`vm_state`/`vm_entries` dell'installer non richiede manutenzione con la
geometria MINI. Con la geometria G e la sola nuova base, entrambi gli header
risultano `FF`: verrebbe richiesta formattazione. **Nessuna migrazione VM
è necessaria per correggere questa discrepanza geometrica.**

Questa prova non interpreta il significato di ciascun ID, la calibrazione
radio né il formato dei preset USR. Non rende permanente lo stato del
backup: un futuro candidato dovrà ricontrollare la VM corrente. Il firmware
G conserva la sua guardia contro le scritture fuori USR.

## Driver NOR

Sedici frammenti originali G/MINI coincidono dopo normalizzazione esplicita
di call target, due globali e destinazioni dei salti locali. MMIO, mask,
registri, ordine delle istruzioni e opcodes rimangono nel confronto.
Il report conserva intervalli e hash dei frammenti normalizzati.

| Funzione | G | MINI |
|---|---|---|
| CS PD0 | `0x01C00088` | `0x01C0008A` |
| Letture SPI secondo modalità | `0x01C00290` | `0x01C00288` |
| JEDEC9F + UID4B | `0x01C0044C` | `0x01C00500` |
| Lettura stato05/35 | `0x01C004D0` | `0x01C00678` |
| Attesa busy05 | `0x01C00600` | `0x01C005A4` |
| Erase dispatcher | `0x01C00640` | `0x01C005E4` |
| Scrittura stato01/31 | `0x01C006D2` | `0x01C006B2` |
| Politica aggiornamento stato | `0x01C0079E` | `0x01C0077E` |
| Page program02 | `0x01C00840` | `0x01C00820` |

Il JEDEC osservato fisicamente dal reader separato, `EB6014`, produce
1 MiB anche nell'algoritmo G: byte finale `0x14`, esponente meno16,
potenza di2 e shift16 ai siti `0x02002746..0x02002750`. I frammenti
confrontati non introducono un rifiuto specifico per manufacturer EB.
Anche il bytecode dell'installer originale elenca `EB6014` fra gli
`ALT_FLASH_IDS` accettati; questo non estende il suo supporto al modello MINI.
Sono condivise anche sequenze status/QE; non ne è stata provata sul chip
la programmazione. Gli opcodes sono qui descritti per audit: il tool non
li invia e non espone alcuna interfaccia hardware.

Restano separati: lock/CPU1, invalidazione cache chiamata dal driver,
timing SFC alla politica clock G, provenienza delle richieste di modifica
stato e tutti i percorsi non confrontati. L'equivalenza dei frammenti non
equivale a una prova di erase/program o recupero sul MINI.

## Identità e formatter per l'integrazione

Le stringhe versioni restano `M5.71 rel ble` e data originale, con prefisso
`tankm_fw`. Il formato PONG rimane `PONG %s %s %s%s\n`. I due preimage
versione sono a `0x0203678E` e `0x020370E8`. I brand ASCII sono a
`0x0203614A` e `0x0203A123`; il descrittore USB UTF16 completo a
`0x0203A264` cambia da `Tank-G UltraRig` a `Tank-M HyperRig`, sempre32byte.
I nomi diagnostici interni `tankg_audio`/`tankg_core1` non sono marker MINI.
Le fonti originali e i NOTICE di provenienza vengono conservati.

L'API importabile è:

```python
from audit_mini_ultrarig_port import BinaryPatch, compose_candidate

area, report = compose_candidate(g_original_bytes, mini_fwsc_bytes)
# Per l'integrazione futura di codice board già verificato:
area, report = compose_candidate(
    g_original_bytes, mini_fwsc_bytes,
    additional_patches=tuple(patch_con_preimage_esatti),
    append_code=blob_board,
)
```

Ogni patch aggiuntiva deve stare nella parte originale di `app.bin`, avere
la stessa lunghezza e non sovrapporsi alle patch di base. Il blob aggiunto
mantiene tutti gli indirizzi G, sposta cfg e aggiorna CRC/header. Il
formatter non attribuisce validità semantica alle patch fornite; tutti i
flag di utilizzabilità restano falsi.

Le verifiche comprendono il roundtrip SFC/JLFS, il confronto inverso
dell'intera applicazione, sei rifiuti per input/preimage/overlap/bounds/CRC,
una prova di append con cfg spostato e il rifiuto di un record VM corrotto.
Una sostituzione solo in memoria del backup dimostra inoltre che bootloader
e ogni byte da `0x82000` in poi rimangono identici; quel dump candidato
completo non viene scritto su file.

## Passi residui verso il prodotto

1. Integrare sequenza codec/pin/mute MINI nel firmware G completo, poi
   mappare comandi fisici e LED; usare l'audit board separato come evidenza.
2. Chiudere handover, clock/SFC, consumatori OTP e calibrazioni BTIF/VM.
3. Dimostrare il recupero con applicazione corrotta: il ritorno dallo stato
   ROM allo stock intatto già riuscito non costituisce questa prova.
4. Verificare avvio dell'app completa, PONG USB/BLE, audio, caricamento e
   salvataggio preset, riavvio stabile e funzionamento prolungato.

Ricostruire tutto in C rimane un percorso più ampio: le fonti pubbliche
UltraRig distribuiscono binari; il C decompilato locale è parziale e non è
un sorgente completo ricompilabile. Il port binario conserva subito tutte
le funzioni originali, ma richiede prove puntuali per ciascun cambio board.
