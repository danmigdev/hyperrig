# Applicazione UltraRig integrale per TANK MINI

La candidata in `build/hyperrig-mini-integrated/` contiene l'intera
applicazione UltraRig G alpha11 v2/M5.71, adattata attraverso patch con
preimage verificata e uno shim C compilato. Il firmware applicativo stock
MINI non viene incluso. Il [report](../research/mini-integrated-port.json)
elenca ogni cambiamento e verifica che invertendo le patch si recuperi
esattamente l'applicazione G originale.

La prima composizione è di 516.096 byte: 19 patch complessive e 2.068 byte
di codice aggiunto, senza nuova BSS. SHA-256:
`f8835a7fd45b1b324d66c457434c7943d70525ed5eb98b514aaac1095031f068`.
Questa verifica riguarda il file; non certifica ancora avvio o audio fisici.

| Gruppo | Adattamento |
|---|---|
| Identità e storage | HyperRig, `tankm_fw`, USB `Tank-M HyperRig`, geometria VM MINI |
| Pannello | Tre input, writer LED G incompatibile rimosso, controlli analogici non mappati disabilitati |
| Avvio | Estensioni del contesto G inizializzate senza leggere byte non garantiti dal bootloader MINI |
| Audio | Codec MINI e PA9, mantenendo DSP, RTOS e percorso ALNK G |

Il codec del primo shim riproduce i 22 record stock senza modificare OSR.
La configurazione a frequenza nominale G non è ancora qualificata. Il
diagnostico ROM ha ottenuto un NACK; timing e precondizioni elettriche sono
in analisi. Le prove RAM DSP non sostituiscono l'avvio di questa applicazione.

## Riproduzione locale

Con originali, estrazioni e toolchain già presenti secondo il README:

```powershell
python -B -X utf8 tools/audit_mini_ultrarig_port.py
python -B -X utf8 tools/audit_mini_panel_port.py
python -B -X utf8 tools/audit_mini_boot_contract.py
python -B -X utf8 firmware/mini/audio_port/verify.py
python -B -X utf8 tools/build_mini_ultrarig.py
python -B -X utf8 tools/plan_mini_install.py --firmware-manifest build/hyperrig-mini-integrated/firmware-manifest.json
```

Questi comandi operano su file e test locali. Non aprono il pedale.
Il builder controlla gli hash dello shim, la sua ELF, i simboli delle chiamate,
la disgiunzione delle patch, i limiti della partizione e i CRC dopo
decodifica. L'editor in `app/web/tankmini.html` viene derivato dagli originali
con l'hash esatto del firmware: riconosce `tankm_fw` e abilita le query previste.
Le mutazioni richiedono evidenze fisiche riferite all'immagine e al trasporto;
le build ordinarie non le abilitano.

## Sostituzione e ripristino

Il piano offline contiene 126 settori da 4 KiB nell'intervallo fisico
`[0x4000,0x82000)`, e `stock-mini-app-area.bin` per il ripristino esatto della
stessa area. Conserva separatamente gli hash prima/dopo di ogni settore.
Non contiene comandi di erase o program e non rende l'aggiornamento atomico.

SPL, configurazione di boot, VM, BTIF, USR e dati unitari restano fuori dalla
sostituzione applicativa. Viene conservato anche l'updater di fabbrica nella
regione `0xB7000..0xBD000`. Questa separazione è coerente con l'installer
UltraRig originale: preservare l'infrastruttura di avvio non significa usare
l'applicazione o il DSP MINI come base del port.

Prima di usare un writer servono un ingresso di recupero indipendente
dall'applicazione, una lettura corrente della flash e il controllo del writer
per questa NOR. Il recupero dal semplice ritorno ROM→stock integro è già
verificato; il recupero da una candidata valida che si blocca non lo è.
Il dettaglio è in [MINI_BOOT_CONTRACT.md](MINI_BOOT_CONTRACT.md).

Il goal resta aperto fino ad avvio stabile, audio reale e lettura/modifica dei
preset attraverso l'app HyperRig sul MINI.
