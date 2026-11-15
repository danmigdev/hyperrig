# Contratto di avvio G → MINI

L'audit individua una correzione concreta all'avvio G e un percorso OTA
autonomo già presente nel MINI. Non prova ancora l'avvio dell'applicazione G
completa né il recupero da un'immagine valida che si blocca. Non esegue
operazioni sul pedale e non produce immagini da installare.

Riproduzione, dalla radice del repository:

```powershell
python -X utf8 tools/audit_mini_boot_contract.py
```

Il comando verifica gli input fissati, esegue 1344 casi sul getter clock
originale, compila con l'assembler JieLi la patch di 28 byte, verifica 64
casi di scritture entro i limiti e confronta i lettori syscfg G/MINI.
I risultati sono in [mini-boot-contract.json](../research/mini-boot-contract.json).
La compilazione usa Ubuntu/WSL e la toolchain già fissata nel progetto.
Nessun compilatore o test host viene presentato come esecuzione sul MINI.

## Clock e ABI GPIO per il codec

`0x020057C6` è un getter C senza argomenti. Restituisce in `r0` i MHz
nominali; usa `r1`, non scrive memoria e non acquisisce lock:

```c
if (*(uint8_t *)(0x01C26890 + 680))
    return *(uint32_t *)0x01C1F1AC;
if ((*(uint32_t *)0x00010014 & 15) != 6)
    return 0;
return (((*(uint32_t *)0x000119AC & 4095) * 4) + 8) / 3;
```

Il valore iniziale della cache è 396 MHz, a LMA `0x0207592C`, ma non va
usato come costante del port. Il setter `0x020054F0` aggiorna la cache a
`0x0200557E` oppure `0x0200577C`, chiama la transizione RAM `0x01C0444E`
a `0x0200566A` e abilita il risultato memorizzato a `0x020057B6`.
Il getter esprime un valore nominale intero, non una misura del clock.

Il binding codec può moltiplicare il risultato per 1000000 dopo aver
rifiutato zero e valori maggiori di 2147, limite degli Hz signed usati dal
ritardo. Il getter non impedisce a un altro task di cambiare clock durante
una transazione: clock stabile e proprietà esclusiva di PA1/PA2 restano
precondizioni distinte.

Le API GPIO G già usate dal binding mantengono il lock di banca a
`0x01C25CE0`. L'ingresso critico `0x01C00E2E` disabilita gli interrupt e
incrementa il contatore relativo al core; `0x01C00E46` lo decrementa e
riabilita gli interrupt quando torna a zero. Non aggiungere un lock della
stessa banca intorno alle API: il protocollo non è ricorsivo.

## Contesto SPL e patch delle estensioni

Il MINI passa `r0=0x01C7FE08`. Il blocco base di 24 byte è compatibile con
il lettore G a `0x0200042E`:

| Offset | Campo preservato |
|---:|---|
| 0 | Puntatore all'header flash decodificato |
| 4 | Base fisica dell'area app, `0x4000` |
| 8 | Base logica CPU, `0x02000000` |
| 12 | Chiave/chip ID a 16 bit |
| 14 | Trim a 16 bit |
| 16 | Otto byte per MAC Bluetooth e CRC |

Il G copia inoltre 8 byte da contesto+80 a `0x01C7FD74` e 4 byte da
contesto+88 a `0x01C7FD7C`. I tipi corrispondono a `SDRAM_CFG_INFO` e
`EX_APP_INFO` nel [boot.h SDK fissato](https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/system/boot.h).
L'SDK documenta dimensioni e campi; i punti di copia sono provati dai byte G.

Il MINI dichiara `ENABLE_SDRAM=0` e una sola area applicazione. Nel suo SPL,
`0x01C04F9E..4FCE` salta l'inizializzazione delle estensioni quando manca
il descrittore opzionale. Il trasferimento base a `0x01C051DA` copia solo
24 byte. Non è quindi corretto presumere che i 12 byte aggiuntivi siano zero
perché non vengono usati dallo stock MINI.

La patch sostituisce il tratto G `[0x0200045C,0x02000478)` con:

```asm
r0 = 0x01c7fd74
r1 = 0
[r0+0] = r1
[r0+4] = r1
[r0+8] = r1
; sette nop per conservare tutti gli indirizzi originali
```

Agisce esclusivamente sulle copie private G. Conserva il blocco base,
`r2..r15`, stack, stato interrupt, chiave, trim e la mailbox che comincia
a `0x01C7FD80`. Non modifica il bootloader né i byte del contesto in ingresso.
L'assembler vendor produce esattamente i byte registrati dal verifier.

API per il formatter integrato:

```python
from tools.audit_mini_boot_contract import boot_patches
patches = boot_patches(g_plain)  # tuple[BinaryPatch, ...], una patch
```

L'API richiede il plaintext dell'intera area G originale fissata; la patch
include preimage completo. Non applicarla a un firmware diverso o già
modificato. La verifica delle tre scritture non dimostra l'intero handover
hardware, cache, IRQ o stabilità dell'applicazione.

## VM, BTIF, OTP e calibrazioni

Il lettore syscfg G `0x02024A78..24B10` e quello MINI
`0x02003E3C..3ED2` hanno la stessa sequenza dopo una normalizzazione
esplicita di quattro indirizzi e delle destinazioni locali. Non vengono
ignorati registri, istruzioni o maschere MMIO. Il percorso speciale ID102
verifica il carrier MAC del contesto e il suo CRC prima di usarlo.

L'ordine dei backend è cache RAM, VM, poi configurazione/BTIF. La VM
comprende gli ID 1..255. Nel backup reale, i seguenti record hanno CRC
valido e larghezze uguali a quelle richieste dalle due applicazioni:

| ID | Byte | Richiesta G | Richiesta MINI |
|---:|---:|---|---|
| 106 | 2 | `0x02024B64` | `0x02023B2E` |
| 107 | 7 | `0x02024CB8` | `0x02023B74` |
| 108 | 20 | `0x02024F14` | `0x02023D6C` |
| 109 | 34 | `0x0205366A` | `0x0206873C` |

Il record106 del G parte anche dai campi hardware `0x11930` e applica il
valore VM se la lettura restituisce due byte. Questo rafforza il vincolo di
conservare le calibrazioni del MINI. ID e larghezza non dimostrano da soli
equivalenza di ogni significato radio o di tutti gli altri ID VM.

Il G apre BTIF per nome a `0x0201FB00`; il contenuto deve rimanere quello
del MINI a `[0xBE000,0xBF000)`. Il backend opzionale a BTIF+512 trova una
lunghezza zero nel backup: il codice G la rifiuta a `0x0201FB26`, invece di
trattarla come una tabella valida. I record106..109 sono già presenti nella
VM, che precede questo fallback.

La partizione G chiamata OTP occuperebbe proprio BTIF del MINI. La candidata
usa la directory MINI e la omette. L'app G non contiene una stringa `OTP`
terminata da zero, ma questa ricerca non esclude tutti gli accessi calcolati
o indiretti. OTP di directory, efuse del SoC e registri OTP della NOR sono
oggetti diversi. Il report lascia aperta la verifica completa dei
consumatori OTP e non pubblica i valori MAC/calibrazione del pedale.

## Recupero senza l'applicazione normale

Il backup completo conferma un updater separato dall'app MINI:

| Oggetto | Posizione | Evidenza |
|---|---|---|
| `LOADER.BIN` | `[0xB7000,0xBBDF6)` | 19958 byte, header valido |
| Record richiesta OTA | `0xBCF00`, 80 byte | Marker `0x5441`, CRC16 valido |
| Identità del record | `ota-TANK MINI_007` | Presente nel backup, non inferita dalla versione app |
| Entry decompressa dichiarata | `0x01C0A800` | Header del payload |

Escluso l'header esterno di 32 byte, il loader nel backup è identico a
`ota.bin` del FWSC MINI_009. SHA256 del payload:
`4844e18e5bb70f3ab7d3bfbe26d9f66d3da43e2e181b00f7121218302cda84a0`.
L'header interno dichiara 23324 byte decompressi; questo audit non esegue
il decompressor o l'updater. Il settore `0xBC000..0xBD000` contiene anche
la sua VM/metadata e deve essere conservato per intero.

Lo SPL a `0x01C03310` verifica l'header applicazione. Il fallimento può
azzerare la base app a `0x01C04D68`; prima dell'handover viene percorsa la
scansione di record da `0x01C04E26`, a passi di settore e con lettura degli
80 byte a settore−256. Il record del backup soddisfa quei controlli di
marker/CRC e porta al loader autonomo. Questa è evidenza statica di un
percorso OTA conservato, **non una prova fisica del recupero**.

Il ramo `0x01C0529A` copia il marker USB alla mailbox e richiede reset,
ma non è l'unico esito di un'app danneggiata. Se non trova una richiesta,
`0x01C05322` azzera un campo e richiede reset senza scrivere quel marker.
Non dichiarare quindi “header invalido → ROM” come regola universale.
Anche il bytecode dell'installer UltraRig originale distingue il fallback
M-VAVE OTA dal disco ROM UBOOT. La conservazione di SPL, area OTA e dati
unitari resta compatibile con la sostituzione completa dell'applicazione:
sono infrastruttura di avvio e recupero, non codice DSP MINI innestato.

Il [manuale ufficiale MINI](https://manualf.oss-cn-hongkong.aliyuncs.com/manual/Combined-Effect-Pedals/TANK-MINI.pdf)
non documenta una combinazione di tasti all'accensione per il recupero.
A+B e B+C sono descritti per Bluetooth e accordatore durante l'uso.
Nel profilo SPL mancano `PORT_INPUT` e `BOOT_DELAY`. `RESET=PB01_08_0`
viene convertito in tre byte di metadata a `0x01C03AB6/3AC8/3ADC`: quel
frammento non campiona il pin e non salta in recovery. Non è stata trovata
una catena footswitch→ROM nello SPL; l'assenza di ogni funzione di recovery
del mask ROM non è dimostrata. Il [download ufficiale](https://www.m-vave.com/download)
offre M-UPGRADE e il FWSC MINI, ma non stabilisce un trigger indipendente
per una futura applicazione G valida che si blocca.

## Prova necessaria prima dell'installazione

Il comando software che ha già portato il MINI in ROM richiede un'app
funzionante. I test RAM HYE1 e il ritorno allo stock non coprono un hang
dell'intera candidata. La presenza dell'OTA non basta a raggiungerla se
l'header G è valido e l'app si blocca dopo il salto.

La fonte primaria [m-bootloader §4.3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#43-recovery-independent-of-a-valid-boot-image)
documenta USB_KEY `0x16EF` su AC791N/SMK-37: un trigger del ROM prima del
firmware. Non è ancora provato sul MINI. Prima di usarlo come rollback va
verificato sul MINI integro, osservando l'identità ROM, una lettura RAM
consentita e il ritorno normale con dati invariati. Non occorre corrompere
la flash per questa prima prova del trigger.

Un guard alternativo nella primissima entry G potrebbe scrivere
`usb_update_mode` e armarne il watchdog, cancellando il marker solo dopo
un handshake definito. Non è implementato: lo SPL spegne il WDT e non
possiamo assumere che un hang produca reset. Prima servono una prova RAM
del reset WDT con conservazione mailbox e una verifica del percorso di
entry. Un marker protegge soltanto i guasti successivi alla sua scrittura
seguiti da un reset che conservi RAM; non protegge entry/header invalidi
o perdita della RAM trattenuta.

Le azioni concrete residue sono quindi provare un trigger indipendente sul
MINI integro, verificare separatamente l'ingresso OTA, e predisporre un
writer con allowlist di settori/readback e ripristino esatto da questo
backup. La build completa può avanzare mantenendo questi gate aperti.
Questo audit non autorizza né esegue una scrittura NVM.
