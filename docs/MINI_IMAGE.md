# Contratto delle immagini TANK MINI

`tools/check_mini_image.py` valida offline il pacchetto stock e gli ELF prodotti
per il MINI. La validazione controlla formato, CRC, indirizzi e inizializzazione
della memoria. Il report conserva `flashable: false` e
`boot_verified_on_device: false`: un ELF coerente non dimostra l'avvio fisico,
la disponibilità dell'audio o la possibilità di recuperare il dispositivo.

## Pacchetto originale verificato

La fonte fissata è `artifacts/tank-mini/TANK-MINI.fwsc`, versione incorporata
`TANK MINI_009`, SHA-256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Si verificano l'identità del pacchetto, il chip AC791N, il CRC del contenitore
principale `flash.bin`, i CRC dell'area JLFS e dei file applicativi.

| Contenuto | Intervallo/dimensione |
|---|---|
| Pacchetto FWSC | 557.044 byte |
| Payload `flash.bin` | `[0, 0x82000)`, 532.480 byte |
| Prefisso precedente all'applicazione | `[0, 0x4000)` |
| Area applicazione MINI | flash fisica `[0x4000, 0x82000)` |
| Finestra CPU corrispondente | `[0x02000000, 0x0207E000)` |
| Inizio di `app.bin` / entry | offset area `0x120` / CPU `0x02000120` |
| `app.bin` stock | 511.032 byte |
| `cfg_tool.bin` stock | 383 byte |
| VM | `[0x82000, 0xBE000)` |
| BTIF | `[0xBE000, 0xBF000)` |
| USR | `[0xBF000, 0xFF000)` |

Il payload `flash.bin` si interrompe all'inizio della VM. Non contiene la VM,
BTIF o USR dell'esemplare e non costituisce un backup totale. Anche l'area
key/MAC candidata `[0xFF000, 0x100000)` è fuori da quel payload; geometria della
flash e dati individuali restano da verificare con una lettura del dispositivo.
Il report distingue queste prove dal semplice possesso del file del produttore.

Il prefisso `[0, 0x4000)` è identificato separatamente dall'hash
`d9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67`.
Lo strumento non genera né modifica questo prefisso. Le directory G/B hanno
VM a `0x7B000` e BTIF a `0xBD000`: vengono rifiutate anche se il file viene
allungato fino alla dimensione attesa per il MINI.

Tre ausiliari del FWSC (`isd_config.ini`, `script.ver`, `blimit.bin`) non
corrispondono al CRC calcolato sui byte grezzi. Il pacchetto fissato è integro
rispetto al suo SHA; questi record restano opachi e potrebbero usare una
codifica ulteriore. Il validatore non li presenta come corrotti o decodificati.
Il record `ota.bin` contiene il nome `usb_hid_ota.bin`: questo è un indizio
del percorso di aggiornamento, non una verifica del protocollo HID sul pedale.

## ELF per il MINI

Il contratto è condiviso con [MINI_BOOT.md](MINI_BOOT.md). Sono richiesti:

- ELF32 little-endian, macchina pi32v2 `0xF1`, tipo eseguibile e entry
  `0x02000120`. Un oggetto relocatable del solo DSP viene rifiutato.
- Segmenti flash entro `[0x02000120, 0x0207E000)` e segmenti RAM entro
  `[0x01C00000, 0x01C7FD30)`, senza sovrapposizioni o payload troncati.
- Byte iniziali della RAM presenti in flash e descritti dai simboli di copia:
  `__ram_start/end` e `__ram_load_start/end`. Deve essere coperto **ogni byte**
  dello span: aumentare entrambi gli end senza aggiungere payload non passa.
- Simboli di azzeramento `__bss_start/end`, memoria preservata
  `__noinit_start/end` e due stack `__stack_bottom/top`, `__ssp_bottom/top`.
  Ogni sezione allocata NOBITS deve ricadere nella propria regione dichiarata.
- Regione generale `__ram_region_start/end` e riserva boot
  `__boot_reserved_start/end = [0x01C7FD30, 0x01C80000)`. Quest'ultima comprende
  il contesto boot, la tabella degli handler IRQ e lo slot di ingresso CPU1
  identificati dall'analisi stock.
- Nessun simbolo globale o debole irrisolto, nessun interprete/linker dinamico,
  un `__flash_image_end` coerente con i segmenti caricabili.

La prima prova con il linker JieLi ha prodotto `p_align = 0x500`, rifiutato
dal validatore. Il build MINI usa ora `-z max-page-size=0x20` e
`-z common-page-size=0x20`: i segmenti del probe rispettano gli allineamenti
ELF senza alterazioni successive del file.

## Esecuzione e prove

```powershell
python tools/build_mini_boot.py
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf
python -m unittest tests.test_mini_image -v
```

Per conservare insieme le evidenze dei due probe, dopo la build del probe DSP:

```powershell
python tools/check_mini_image.py --elf build/mini-boot/hyperrig-mini-boot-probe.elf --elf build/mini-boot/hyperrig-mini-dsp-link-probe.elf --report research/mini-image.json
```

I dieci test coprono ELF troncati, tipo/CPU/entry errati, uscite dai limiti,
sovrapposizioni, simboli runtime non risolti, copie RAM prive di byte sorgente,
BSS non azzerabile, noinit sovrapposta, CRC stock e uso improprio di immagini G/B.
Il risultato sui file reali, con hash, segmenti e simboli, è in
[mini-image.json](../research/mini-image.json).

## Requisiti ancora aperti per avviare il dispositivo

Il validatore controlla il contratto del file, mentre restano da provare il
passaggio effettivo dal bootloader all'applicazione, la configurazione dei
clock e l'integrazione IRQ/audio/DSP sul dispositivo. Il compositore descritto
sotto copre l'area applicativa; i metadati e il trasporto dell'aggiornamento
richiedono ancora una verifica distinta.

Il bytecode recuperato dell'installer originale (`parse_identify` in
`recovered/installer/tankg_install.constants.json`) ammette TANK-G/TANK-B e
contiene controlli specifici sulle loro revisioni e mappe. La rinomina HyperRig
non introduce supporto MINI in quei percorsi. Il collegamento BLE che ha letto
`TANK MINI_009` non ha verificato un ingresso al bootloader o acquisito un backup
completo. Trasporto di aggiornamento, backup individuale e ripristino richiedono
ancora prove specifiche sul dispositivo.

## Composizione dell'area applicativa sperimentale

`tools/package_mini_probe.py` compone esclusivamente lo slice fisico
`[0x4000,0x82000)` a partire da un ELF che passa il validatore e dal pacchetto
MINI 009 fissato nel manifest. Non contiene il bootloader o i dati del singolo
esemplare e non è un file FWSC. Il layout valido non dimostra avvio o recuperabilità.

```powershell
python tools/package_mini_probe.py --elf build/mini-boot/hyperrig-mini-bringup-probe.elf --output build/mini-boot/hyperrig-mini-bringup-probe.app-area.bin --report research/mini-package.json
```

I byte dei segmenti ELF vengono inseriti agli indirizzi **LMA in flash**, inclusa
la sorgente dei dati inizializzati in RAM. BSS, mailbox noinit e stack non vengono
serializzati. I vuoti e tutta la parte dell'eseguibile stock sostituita sono
riempiti con `FF`, così il vecchio codice non rimane dietro al nuovo programma.

`cfg_tool.bin` rimane all'offset originale `0x7CD58`; i suoi byte e tutti i record
delle regioni MINI sono identici allo stock. Un programma che vi si sovrappone
viene rifiutato. Cambiano soltanto lunghezza/CRC del file applicativo e CRC
dell'area. Il trasformato SFC usa la chiave del pacchetto stock, non una chiave
letta dall'esemplare. Il report riporta esplicitamente questa provenienza.

Il verificatore riapre il file scritto, controlla ogni CRC, confronta tutti i
segmenti con l'ELF e verifica i byte conservati e i riempimenti. Nove test
aggiuntivi coprono indirizzi LMA, NOBITS, padding, corruzione, sovrapposizione
alla configurazione (anche con ELF e CRC formalmente validi) e un eseguibile
alterato che ha comunque CRC validi.
I risultati e gli hash sono in [mini-package.json](../research/mini-package.json).
