# Applicazione UltraRig integrale per TANK MINI

La candidata corrente in `build/hyperrig-mini-audio-v2/` contiene l'intera
applicazione UltraRig G alpha11 v2/M5.71, adattata attraverso patch con
preimage verificata, uno shim C compilato e la guardia di recupero v2
obbligatoria all'ingresso. Il firmware applicativo stock
MINI non viene incluso. Il [report](../research/mini-integrated-port-v2.json)
elenca ogni cambiamento e verifica che invertendo le patch si recuperi
esattamente l'applicazione G originale.

La composizione con guardia è di 516.096 byte: 20 patch complessive e 2.630 byte
di codice aggiunto, senza nuova BSS. SHA-256:
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
Questa verifica riguarda il file; non certifica ancora avvio o audio fisici.

La versione con shim audio v1 e guardia v2, SHA-256
`639f58864e2b7c29c4312545fe94b345b2f8c8c21eb72eceb0932712bd608f70`,
resta in `build/hyperrig-mini-integrated/`. Il probe HYW1 con scritture
disabilitate è stato eseguito usando una pagina di questa versione;
le evidenze non vengono attribuite alla nuova candidata.

La candidata precedente, SHA-256
`f8835a7fd45b1b324d66c457434c7943d70525ed5eb98b514aaac1095031f068`,
è conservata in `build/hyperrig-mini-integrated-before-guard/` insieme a
manifest firmware, report canonico, report di composizione ed editor. Il file
`archive-manifest.json` registra gli hash degli otto file archiviati prima
della rigenerazione.

| Gruppo | Adattamento |
|---|---|
| Identità e storage | HyperRig, `tankm_fw`, USB `Tank-M HyperRig`, geometria VM MINI |
| Pannello | Tre input, writer LED G incompatibile rimosso, controlli analogici non mappati disabilitati |
| Avvio | Estensioni del contesto G inizializzate senza leggere byte non garantiti dal bootloader MINI |
| Audio | Codec MINI e PA9, mantenendo DSP, RTOS e percorso ALNK G |
| Recupero | Guardia v2 prima della prima chiamata G, tre footswitch input e marker/reset ROM esplicito dopo riconoscimento della combinazione |

Lo shim audio v2 riproduce i 22 record stock senza modificare OSR. Prepara PC5
con i lock G e prosegue dopo NACK secondo la policy del caller stock, distinguendo
i record tentati da quelli riconosciuti. Gli errori di timing o pulizia restano
fatali; il STOP esplicito dopo NACK è una differenza documentata in
[MINI_AUDIO_PORT_V2.md](MINI_AUDIO_PORT_V2.md).
La configurazione a frequenza nominale G e l'audio completo non sono ancora
qualificati in questa applicazione. I risultati dei diagnostici ROM codec,
DSP e tasti/reset hanno evidenze separate; non vengono convertiti
automaticamente in una prova di avvio di questa candidata.

La guardia attuale occupa 298 byte da `0x020773C8` a `0x020774F2`, dopo i 2332
byte dello shim audio. Il builder calcola l'indirizzo dalla lunghezza reale
dello shim, applica l'eventuale padding di allineamento e ricompila la guardia;
non usa un indirizzo fisso quando cambia l'audio. `bind_append` verifica che
il payload effettivo e la branch d'ingresso corrispondano a quell'allocazione.
Il manifest integrato `entry-recovery-manifest.json` conserva i 1280 casi del
modello istruzioni e gli hash dei callable v1 invariati.

La policy applicativa imposta `PORTA.DIR |= 0x409` prima del check. I tre pin
restano input e gli altri bit vengono preservati; il contesto G, compreso R0,
viene ripristinato quando l'avvio prosegue. Non dipende dalla direzione iniziale
lasciata dal cold SPL. Il probe ROM HYK1 conserva la sua diversa policy di
ripristino e non viene modificato. Dettagli in
[MINI_ENTRY_RECOVERY_V2.md](MINI_ENTRY_RECOVERY_V2.md).

## Riproduzione locale

Con originali, estrazioni e toolchain già presenti secondo il README:

```powershell
python -B -X utf8 tools/audit_mini_ultrarig_port.py
python -B -X utf8 tools/audit_mini_panel_port.py
python -B -X utf8 tools/audit_mini_boot_contract.py
python -B -X utf8 firmware/mini/audio_port_v2/verify.py
python -B -X utf8 tools/build_mini_ultrarig.py --audio-manifest build/mini-audio-port-v2/manifest.json --output build/hyperrig-mini-audio-v2 --report research/mini-integrated-port-v2.json
python -B -X utf8 tools/plan_mini_install.py --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --output build/mini-install-plan-v2
python -B -X utf8 tools/build_mini_android.py --firmware-manifest build/hyperrig-mini-audio-v2/firmware-manifest.json --output build/hyperrig-mini-audio-v2/android
```

Questi comandi operano su file e test locali. Non aprono il pedale.
Il builder controlla gli hash dello shim, la sua ELF, i simboli delle chiamate,
la guardia obbligatoria, la disgiunzione delle patch, i limiti della partizione
e i CRC dopo decodifica. Il gruppo `recovery` deve contenere la patch d'entry;
non esiste un'opzione di build per ometterla. L'editor in
`build/hyperrig-mini-audio-v2/app/web/tankmini.html` viene derivato dagli originali
con l'hash esatto del firmware: riconosce `tankm_fw` e abilita le query previste.
Le mutazioni richiedono evidenze fisiche riferite all'immagine e al trasporto;
le build ordinarie non le abilitano. Il builder rigenera il web editor, non
l'APK: l'APK finale deve essere ricostruito dopo l'ultima revisione audio e
firmware. Anche un piano d'installazione precedente deve essere rigenerato e
ricontrollato contro il nuovo hash. L'APK v2 è stato ricostruito: SHA-256
`69273b95adeefe3c865d1e6da8e18fc2bf612fd995e19462a77c7dae6eb1c82b`,
associato all'immagine `3b0eac3b…`. Non è ancora stato provato sul telefono.

## Sostituzione e ripristino

Il piano offline contiene 126 settori da 4 KiB nell'intervallo fisico
`[0x4000,0x82000)`, e `stock-mini-app-area.bin` per il ripristino esatto della
stessa area. Conserva separatamente gli hash prima/dopo di ogni settore.
Non contiene comandi di erase o program e non rende l'aggiornamento atomico.

La ricezione e il confronto dei dati dell'installatore sono stati verificati
sul MINI con il gate di scrittura costantemente disabilitato: lettura del primo
settore uguale al backup, ricezione di 260 byte e restituzione esatta della
pagina congelata di 256 byte. WREN, erase e program restano a zero. Il ritorno
allo stock e i preset invariati sono documentati nel
[report HYW1](../research/mini-writer-observer-hardware.json).
Questa prova non qualifica ancora cancellazione o programmazione reali.

SPL, configurazione di boot, VM, BTIF, USR e dati unitari restano fuori dalla
sostituzione applicativa. Viene conservato anche l'updater di fabbrica nella
regione `0xB7000..0xBD000`. Questa separazione è coerente con l'installer
UltraRig originale: preservare l'infrastruttura di avvio non significa usare
l'applicazione o il DSP MINI come base del port.

Prima di usare un writer servono una lettura corrente della flash, il controllo
del writer per questa NOR e la qualifica del percorso di recupero previsto.
La guardia interviene prima di RTOS/clock/DSP G e può consentire il rientro ROM
quando un'immagine valida si blocca in seguito. Non copre un header, entry o
guardia danneggiati. Una prova fisica dei tasti e del marker/reset tramite HYK1
è distinta dall'esecuzione del prefix XIP a freddo e dal recupero della
candidata effettivamente installata: il builder mantiene questi ultimi flag
a `false`. Il dettaglio del boot è in
[MINI_BOOT_CONTRACT.md](MINI_BOOT_CONTRACT.md).

`boot_verified_on_mini`, `audio_verified_on_mini`, `flashable` e la capacità
di scrittura dell'editor restano `false`. Nessun file target-profile o rapporto
di osservazioni hardware viene alterato dalla composizione.

Il goal resta aperto fino ad avvio stabile, audio reale e lettura/modifica dei
preset attraverso l'app HyperRig sul MINI.
