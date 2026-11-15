# Lettore NOR MINI in RAM

`firmware/mini/recovery_reader/` contiene un plugin per il normale callback
USB della ROM AC791N. Legge la NOR con SPI PIO, senza DMA, display, P33,
accesso efuse, cambio clock, reset, programmazione o cancellazione della
flash. **Il caricamento del plugin da solo non accede a periferiche:**
registra il proprio handler e restituisce il controllo alla ROM. L'accesso
SPI avviene soltanto quando il client richiede `FC72`.

Il plugin va usato dopo avere verificato sul MINI l'ABI ROM con un probe
senza SPI. Il report del builder descrive le prove offline; le osservazioni
fisiche sono registrate separatamente.

**Backup completo riuscito il 15 novembre 2026:** due file da 1.048.576 byte
identici, SHA-256
`72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180`.
Tutte le 4.096 letture da 512 byte hanno avuto stato e contatore verificati.
I CRC di boot, configurazione e applicazione sono validi; l'intero prefisso
`[0,0x82000)` coincide byte per byte con lo stock 009. Anche VM, BTIF, USR e
key_mac coincidono tra le due acquisizioni. I file sono in
`artifacts/my-mini-flash/20261115-paced-resume/`, esclusi da Git.
Il pedale è poi tornato a `TANK MINI_009`, con preset invariati.

La prova fisica del 15 novembre 2026 è registrata separatamente in
[mini-hardware-rom.json](../research/mini-hardware-rom.json): il MINI ha
eseguito il reader nello slot `0x01C28000`, risposto `HYRN` e restituito
JEDEC `EB6014` (1 MiB), `SYS_DIV=0` e `CLK_CON2=0x80` nella ROM.
Nel primo tentativo, 260 blocchi da 512 byte coincidevano con lo stock,
per 133.120 byte; il comando successivo, a offset `0x20800`, è fallito con
errore Windows 31. Sono persistiti 131.072 byte di quella lettura parziale.
Il vecchio trace non misura la durata dell'errore, quindi non ne stabilisce
la causa. Il reset RAM successivo ha riportato il pedale a `TANK MINI_009`,
con gli stessi preset. Non è stato inviato alcun comando di scrittura NOR.
Il tentativo completo successivo è riuscito dopo il reset dell'hub per un
nuovo errore di enumerazione e con una pausa di 5 ms prima dei comandi.
La causa del primo errore non è isolata: questi risultati non dimostrano
che il solo pacing l'abbia risolta. Nessun comando è stato ritentato
automaticamente e nessun salto ambiguo è stato ripetuto.

## Compilazione

```
python tools/verify_mini_recovery_reader.py
```

Il comando non apre dispositivi. Compila ed esegue i test host ASan/UBSan,
quindi genera in `build/mini-flash-reader/`:

* `hyperrig-reader-01c20000.{elf,bin,map,asm}`;
* `hyperrig-reader-01c28000.{elf,bin,map,asm}`.

Ogni flat contiene 2.308 byte; codice, dati e stato privato occupano 2.884
byte di un unico slot da 32 KiB. L'entry è il primo byte del flat. Il linker
e l'audit ELF rifiutano simboli irrisolti, relocation runtime e allocazioni
fuori dallo slot. Non viene inizializzata una nuova pila: sono conservati
pila, IRQ e ritorno C della ROM. Solo lo stato privato viene azzerato.

Gli hash esatti e i risultati sono in `research/mini-flash-reader.json`.
Non sono immagini applicative, FWSC o bootloader.

## Protocollo HYRN v1

L'ABI di ingresso è una struttura di tre puntatori target a 32 bit:
`send(data,count)`, `receive(data,count)`, puntatore allo slot handler.
L'handler riceve il CBW USB di 31 byte e un answer di 16 byte; ritorna `1`
per i comandi gestiti. I quattro comandi HYRN sono esclusivamente IN, con
CDB di 16 byte e LUN0. Il client deve verificare identità e slot prima di
abilitare qualsiasi richiesta SPI.

| CDB | Risposta/azione |
|---|---|
| `FC70` | 16 byte: eco op a0..1, `HYRN` a2..5, versione1 a6, flags3=RO\|PIO a7, slot BE32 a8, dimensione slot BE32 a12. Nessun MMIO. |
| `FC72` | Inizializza SPI una sola volta ed esegue JEDEC. Risposta16byte: ecoop, errore a2, inizializzato a3, JEDEC a4..6, baud15 a7, capacità BE32 a8, zero a12..15. |
| `FD71` | Offset NOR BE32 a CDB+2, lunghezza BE16 a CDB+6. Lunghezza richiesta dal CBW identica, tra1 e512. Restituisce esattamente quei byte. |
| `FC73` | Stato16byte: ecoop, primo errore a2, inizializzato a3, snapshot SYS_DIV BE32 a4, CLK_CON2 BE32 a8, contatore byte letti con successo BE32 a12. Nessun nuovo MMIO. |

Gli errori sono persistenti: `1` clock, `2` timeout SPI, `3` JEDEC/capacità,
`4` framing, `5` intervallo, `6` lettore non inizializzato, `7` callback USB,
`8` comando privato proibito. Il plugin non offre un comando per cancellarli.
Un errore durante `FD71` restituisce `FF` per mantenere la fase dati e non
incrementa il contatore. **Il client deve interrogare FC73 dopo ogni blocco,
richiedere errore0 e un incremento del contatore esattamente pari alla
lunghezza richiesta.** I soli byte restituiti non attestano una lettura.

Il ritorno non negativo della callback ROM `send` è accettato; i valori
negativi generano errore7. La semantica esatta del valore positivo/zero
rimane una proprietà della ROM da osservare. Il client verifica comunque
lunghezza, stato e contatore.

Le operazioni SCSI standard e i tre comandi ROM RAM `FB06`, `FD07`, `FB08`
restano alla ROM. Altri comandi privati, inclusi i vecchi comandi di erase,
write e display, vengono consumati e rifiutati: non sono delegati alla ROM.
Il client deve mantenere una allowlist HYRN separata da quella M-Flasher.
Un trasferimento malformato oltre512byte viene gestito solo fino a512byte;
può richiedere recupero BOT/ROM e non va emesso dal client.

## Prerequisiti e transazioni

Prima di qualsiasi scrittura MMIO, `FC72` acquisisce:

* `SYS_DIV`, indirizzo `0x10008`, campi HSB17:16 e LSB10:8, mask`0x30700`;
* `CLK_CON2`, indirizzo `0x10014`, low8.

Accetta soltanto le coppie `(CLK_CON2 low8, SYS_DIV mask)` `(0x80,0)` e
`(0x40,0x100)` riconosciute dal loader ROM AC791N di riferimento. Ogni lettura
successiva ricontrolla che tali campi non siano cambiati. Un caso sconosciuto
è rifiutato prima di scrivere le periferiche. Il reader non applica la
transizione di clock eseguita da `hal_clock_b`; mantiene quanto ereditato.
Il match dei campi non misura una frequenza fisica. Il baud SPI è15 e le
attese sono conteggi di istruzioni, non microsecondi dichiarati.

La sequenza SPI usa i pin attestati da MINI `uboot.boot`:

| Evidenza MINI | Operazione |
|---|---|
| `0x01C02CA6..2CC6` | CS manuale PD0. |
| `0x01C02CD0..2D02` | Buffer SPI0 `0x11C08`, direzione bit12, completion bit15, clear bit14. |
| `0x01C02D48..2DAE` | SFC disabilitata; SPI control`0x28`; mux`0x51020` bit1 e `0x5101C` bit5 cancellati; PD4/5 output, PD4 drive; PD1 input; PD2/3 usati per quad. |

Il reader configura PD0 alto, PD4/5 bassi, PD2/3 alti, PD1 input digitale
senza pull, disabilita SFC/peripheral ENC, abilita SPI0 e pone baud15.
Sono modifiche volatili necessarie per leggere la NOR; l'intero plugin deve
risiedere in RAM. Non vengono toccati cache, MMU, PLL o timer.

Le sole transazioni di comando sono `FF FF` sotto un CS per uscire
dall'eventuale lettura continua, `9F` per JEDEC, `03` seguito dall'indirizzo
a24bit per leggere. Non esistono WREN, program, erase o write-status, neppure
come API pubbliche. La sequenza FF è corroborata dal lettore ROM AC791N di
riferimento; i cicli PIO SPI sono verificabili anche nel bootloader MINI.
Vengono accettati solo ID produttore diversi da00/FF ed esponente capacità20
(1 MiB). Il file FWSC non viene usato per inventare la capacità fisica.

Ogni byte attende al massimo32.768 letture del bit completion. Un timeout
rilascia CS, conserva il primo errore e impedisce ulteriori transazioni.
Il test host copre tutti i522 punti di timeout dell'inizializzazione e di
una lettura512byte, i confini della NOR, cambi clock, framing, risposta USB
negativa e il rifiuto di nove comandi legacy. Controlla inoltre ogni comando
SPI e una allowlist di indirizzi MMIO scrivibili. Queste prove riguardano
sequenze software e terminazione, non simulano il dispositivo fisico.

## Acquisizione del backup

Il client, mantenuto separatamente, deve:

1. verificare USB ROM, ABI/slot e hash del plugin prima del caricamento;
2. controllare FC70 e poi FC72, richiedendo successo, JEDEC plausibile,
   capacità1MiB e baud15;
3. leggere `[0,0x100000)` in blocchi di massimo512byte, verificando FC73 dopo
   ciascuno;
4. salvare l'immagine integrale e ripetere l'intera acquisizione;
5. richiedere due immagini identiche, conservarne hash, JEDEC, clock,
   contatori e identificazione del dispositivo prima di qualsiasi lavoro
   NVM successivo.

Il controllo offline del contenuto è disponibile con:

```powershell
python tools/inspect_mini_backup.py flash-a.bin --second flash-b.bin --report backup-inspection.json
python tools/inspect_mini_backup.py --self-test
```

Richiedere sia `backup_consistency_and_content_validated` sia
`decoded_firmware_matches_stock_009`. Il parser verifica CRC del bootloader
BANKCB, configurazione, prefisso chiave e directory/payload applicativi.
Il pacchetto FWSC copre solo `[0,0x82000)`: VM, BTIF, USR e key_mac vanno
conservati e confrontati tra le due letture, senza inventare un riferimento
stock per quelle aree. I dump contengono dati specifici del pedale e restano
nella cartella locale `artifacts/`, esclusa da Git.

Questo plugin non contiene un comando per installare firmware o tornare
allo stock. Reset e marker RAM sono percorsi distinti da provare e gestire
nel coordinatore, non effetti impliciti del backup.

Riferimento primario per ABI e percorso ROM: [m-bootloader, loader_target.c](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/src/loader_target.c)
e [platform.c](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/src/platform.c).
Il riferimento ha prove hardware FM1/SMK37; la compatibilità fisica MINI non
è dedotta automaticamente da tali prove.
