# Connessione reale dell'editor MINI: sessione 03

Il **16 novembre 2026 alle 00:08:26 UTC**, l'editor HyperRig aperto in una
finestra Chromium visibile ha comunicato con il MINI tramite WebSerial su
`COM3`, VID/PID `3654:5155`. La prova è separata dai mock e dai tentativi
precedenti; non modifica la manifest frozen dell'app.

La risposta realmente ricevuta è:

```text
PONG tankm_fw M5.71 rel ble Nov 12 2026 16:04:11 safe
```

La snapshot stabile registra una richiesta di porta, un'apertura nativa
completata, **25 scritture readonly completate e 302 righe di risposta**.
L'app è connessa, la demo è disattivata e le letture iniziali `MODEL`, `MEM`,
`FXT`, `FXS`, `PLIST` e `SNAPS` sono terminate. L'interfaccia mostra 37 tipi
di effetti e il modello dichiarato `A2`, 23 layer/3 canali. La catena effetti
è vuota; `PLIST end current=-1` e `SNAPS 0000 current=-1` descrivono lo stato
letto, senza dimostrare salvataggio o modifica dei preset.

Prove conservate:

| File | SHA256 |
|---|---|
| `build/mini-desktop-real-03/connected-proof.json` | `96f5300a17b3d5cb18741c34857d7dda63a30edaf3a7222ee7ca615d8214ded2` |
| `analysis/hardware/mini-desktop-real-03-selection.json` | `30dca427dc997818aa3888af948ee8df63fd5c4f20111e37f3bbce1c64d4dbba` |
| `build/mini-desktop-real-03/connected.png` | `ee8346b83431ed150c21ed3d0fba9fe60ff07e11f4d69dd90676193b4d199890` |
| `research/mini-desktop-readonly-hardware.json` | `7ecc81b7d4ca41a91e5dfd926c873a5b6c19a3c04aba61455765e03b2b5773af` |

La candidata associata resta l'immagine app
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`,
verificata dal readback NOR precedente. Il PONG conferma versione/build, non
misura l'hash dell'immagine sul dispositivo. Il proof contiene righe RX
realmente passate dal reader dell'app, non una cattura USB né un dump dei byte
nativi di ogni trasferimento.

## Selezione del dispositivo

Il chooser WebSerial nativo di Chrome non emetteva l'evento CDP DeviceAccess
atteso. Root ha selezionato tramite **Windows UIAutomation SelectionItem e
Invoke** la riga univoca `Tank-M HyperRig (COM3)` nella sola finestra della
sessione, browser PID `154888`, origine `http://127.0.0.1:2047`.
Il guard ha poi ricontrollato VID/PID prima dell'apertura. Questa selezione
non altera l'allowlist readonly né fabbrica una risposta seriale.

La procedura pertinente per questo browser è: nuova sessione isolata,
verifica del PID/origine, riga COM esatta e univoca nel chooser nativo,
SelectionItem sulla riga e Invoke sul pulsante Connect. Occorre completare
la selezione durante l'attesa del launcher; una sessione già fermata non va
riattivata alterando il guard. Il limite CDP e le fonti Chromium della
revisione osservata sono in [MINI_WEBSERIAL_CHOOSER.md](MINI_WEBSERIAL_CHOOSER.md).

La sessione **01** aveva soltanto il chooser aperto: zero aperture e zero
TX/RX. La **02** si era fermata al preflight per un hash errato, prima del
browser. La **03** è la prova effettiva di comunicazione; i tre risultati non
vanno uniti né contati come tre prove firmware.

## Limiti e diagnostica ottenuta

Il suffisso `safe` è presente nel PONG. `CLKSTATE` riporta nominalmente
`mhz=360` e `safe=1`; `LIFE` registra `boots=2`, `exc=1`, `wdg=0`. La risposta
`CRASH` conservata riporta `reti=0x02076AAE`, `rets=0x020053AA` e il trace ETM
inizia da `0x02076AAC`. Sono dati utili per l'analisi dell'ingresso nello shim
audio; questa prova non attribuisce da sola la causa dell'eccezione.

La comunicazione readonly è provata. Restano separati e non qualificati:
avvio audio normale e stabile, audio analogico, modifica reale dalla UI,
salvataggio/ricaricamento preset, BLE, recupero mediante footswitch e ciclo
di alimentazione a freddo.

Alla snapshot la porta è intenzionalmente aperta (`closes=0`) e la finestra
è lasciata disponibile all'utente. Il report non dichiara una chiusura non
avvenuta. Prima di un futuro diagnostico CLI o trial di modifica occorrerà
la disconnessione e la relativa prova di chiusura. `session.json` è ancora
un report attivo e va letto con il helper shared-delete; il suo hash non è
usato come prova immutabile.

Durante questa sigillatura sono stati letti soltanto file locali. Launcher,
guard, editor e firmware frozen non sono stati modificati.
