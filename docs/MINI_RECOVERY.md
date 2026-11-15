# Recupero ROM e primo codice RAM sul TANK MINI

Il firmware ufficiale `TANK MINI_009` contiene un comando USB MIDI per
richiedere la modalità download ROM. Il comando è stato ricostruito dai byte
del MINI; l'allowlist MIDI di m-flasher non include questo modello.
`tools/probe_mini_recovery.py` produce evidenze e vettori offline, e offre una
API Windows esplicita per trasferimenti limitati a RAM e letture NOR.
Importare il modulo o eseguire la sua CLI non apre un dispositivo.

I test del client usano trasporti in memoria e API Windows sostituite. I risultati
fisici sono registrati separatamente in `analysis/hardware/`: il rapporto
`research/mini-recovery.json` descrive la verifica offline, non certifica
l'avvio hardware né il recupero dopo una flash corrotta.

La successiva prova fisica del 15 novembre 2026 è riportata in
[mini-hardware-rom.json](../research/mini-hardware-rom.json). Sono riusciti
l'ingresso USB nella ROM, l'esecuzione del probe DSP, l'avvio del reader NOR
e il reset verso lo stock. Il ritorno è stato verificato con una nuova
enumerazione `4C4A:C755`, risposta `TANK MINI_009` e doppia lettura dei preset
identica al backup precedente. Dopo una prima acquisizione parziale per
errore USB e un reset dell'hub, sono riuscite due letture integrali da 1 MiB
identiche e con contenuto stock 009 valido. Recupero da flash corrotta e
ripristino NVM restano da provare.

## Comando MINI e percorso verificato nei byte stock

Il contenitore di riferimento è `artifacts/tank-mini/TANK-MINI.fwsc`, SHA256
`13a8c87f5910334eef7c818e2bd5eec41de726e28b0ad02c290ee2095969a209`.
Un contenitore differente viene rifiutato prima dell'analisi.

| Oggetto | Valore |
| --- | --- |
| SysEx | `F0 22 24 35 7D F7` |
| Due pacchetti USB MIDI, cable 0 | `04 F0 22 24 07 35 7D F7` |
| Pattern stock in RAM | `0x01C0AFC4` |
| Guardia del comando | `0x0200869A..0x020086DE` |
| Routine di richiesta download | `0x01C02332..0x01C02382` |
| Stringa conservata | `usb_update_mode\0`, 16 byte |
| Origine/destinazione della stringa | `0x0203FD2A` / `0x01C7FD80` |

La guardia richiede otto byte, confronta i primi sei con il pattern e controlla
separatamente `F7` finale e comando `7D`. Il modello esegue il flusso delle
istruzioni decodificate fino alla chiamata di recupero: un caso positivo e
73 varianti negative, compresi tutti i singoli bit modificati, lunghezze
troncate e un byte in più. `memcmp` è stato ispezionato separatamente.

La routine successiva disabilita gli interrupt, serializza l'accesso, copia il
marker e chiama l'helper P33 `0x01C0108C` con argomenti `(0xA0,4,1,1)`, poi
attende. Il modello offline non esegue tale scrittura né un reset.

La registrazione USB `0x02007ED0` installa la callback `0x02008864`, che legge
i dati USB e li passa a `0x02008784`, quindi alla guardia. Non è stato provato
un percorso BLE equivalente verso questa callback. La possibilità di leggere
i preset BLE non dimostra che il comando di modalità USB sia inoltrabile lì.

## Protocollo ROM e trasformazione dei dati

Le fonti AC791N descrivono due slot RAM, `0x01C20000` e `0x01C28000`, ciascuno
di `0x8000` byte. Uno slot deve essere noto libero oppure contenere un upload
mai eseguito con cronologia completa. La sola risposta INQUIRY non prova che
uno slot sia libero.

Ogni CDB privato è lungo 16 byte, con riempimento `FF`:

| Operazione | CDB e fase dati |
| --- | --- |
| Upload ROM | `FB06`, indirizzo BE32 a +2, lunghezza BE16 a +6, zero a +8, CRC16 LE a +9; OUT massimo 512 byte |
| Lettura ROM | `FD07`, indirizzo BE32 a +2, lunghezza BE16 a +6; IN massimo 512 byte nel client |
| Chiamata RAM | `FB08`, entry BE32 a +2, parametro BE16 `1` a +6; IN 16 byte |
| Identità/selftest HyperRig | `FC60`; IN 16 byte |
| Lettura del plugin HyperRig | `FD61`, indirizzo BE32 e lunghezza BE16; IN massimo 4096 byte per comando, callback in blocchi da 512 |

`FB06` trasmette dati trasformati con `jl_crc_cipher`, chiave `FFFFFFFF`.
Lo stato riparte per ogni comando. Il CRC16/XMODEM del CDB usa seed zero e
copre i byte **trasmessi**, già trasformati. La trasformazione è simmetrica
e distinta dalla cifratura ENC/SFC della flash.

**Anche `FD07` restituisce dati trasformati.** Il client decodifica ogni
risposta separatamente, verifica la lunghezza e confronta l'intera immagine
con il file di SHA256 approvato. Non prova automaticamente altre codifiche
e non accetta una corrispondenza parziale.

Questa distinzione è documentata dalla disassembly dell'installer originale:
`UbootSession.reboot`, linee originali 2786 e 2791, applica `enc(mem_read(...))`
prima di verificare sentinel e immagine. `enc` usa `cipher_bytes(jl_crc_cipher,
b)`, con chiave predefinita `FFFFFFFF`; `JL_LoaderV2.mem_read` restituisce la
risposta grezza.

Nel primo tentativo MINI del 15 novembre 2026, il client precedente ha
confrontato erroneamente la risposta grezza con il file e si è fermato senza
emettere `FB08`. L'analisi offline di `analysis/hardware/rom-probe-trace.jsonl`
ha trovato tutti i dieci hash ricevuti uguali ai blocchi attesi trasformati
(nove blocchi da 512 byte e uno da 320), nessuno uguale al plaintext.
La correzione mantiene la verifica completa prima del salto. Una sessione
con cronologia che prova zero `FB08` può rileggere l'upload già presente;
non occorre sovrascriverlo.

`FD61` appartiene al plugin caricato. m-flasher `run-ram --read` usa `FD61`;
non è una prova che la ROM implementi direttamente tale comando. Dopo un
`FB08` con risposta persa, il codice potrebbe essere già stato eseguito:
il client marca la sessione prima della chiamata e non ripete il salto.

## Contratto del plugin RAM

L'entry è il primo byte del file flat. La ROM lo chiama come funzione C:
`r0` punta a tre word contenenti callback send, callback receive e indirizzo
della variabile ROM che contiene la callback del protocollo.

Il plugin conserva questi valori, inizializza solo il proprio stato, pubblica
il proprio handler con sincronizzazione e ritorna normalmente. Il contratto
mantiene stack ROM, clock, interrupt, servizio USB e RAM degli altri slot.
Non usa lo startup dell'applicazione MINI né azzera tutta la RAM.

L'handler riceve `CBW31 *` in `r0` e un buffer risposta da 16 byte in `r1`;
ritorna uno per comando gestito, zero per delegare alla ROM. Il CBW contiene
firma LE `0x43425355`, tag a +4, conteggio LE a +8, direzione a +12,
lunghezza CDB a +14 e CDB a +15. Il plugin invia i dati con la callback fornita;
la ROM produce il CSW. La semantica esatta dei valori restituiti dalle callback
non è interamente deducibile dalle fonti: il client controlla comunque fase
dati, identità e contenuti.

Il probe HYR1 è costruito da `tools/build_mini_rom_probe.py`. Le risposte `FC60`
contengono conteggio BE32 a +2, `HYR1` a +6, stato BE32 a +10 e versione BE16
a +14. Il client richiede stato zero, versione uno e conteggio positivo.
Il manifest del probe stabilisce gli otto casi e i CRC attesi; un risultato
positivo non equivale all'esecuzione dell'intero motore A2 o del percorso audio.

## Client Windows e sequenza degli slot

`WindowsRomTransport` richiede Python Windows a 64 bit e un percorso esplicito
`\\.\PhysicalDriveN`. Prima di aprirlo controlla che la catena PnP abbia
antenato `USB\VID_4C4A&PID_8057`; dopo l'apertura richiede INQUIRY
`WL82` / `UBOOT1.00`. Una periferica con errore descrittore 43 non soddisfa
queste condizioni.

Il trasferimento usa `SCSI_PASS_THROUGH_DIRECT`, IOCTL `0x4D014`, target 1,
timeout 10 secondi e sense buffer di 32 byte. Su Windows a 64 bit la struttura
SPTD è di 56 byte; il buffer con sense è di 88 byte. Il driver Windows costruisce
il framing USB BOT: il client non aggiunge manualmente un CBW. L'apertura
richiede i diritti di protocollo READ/WRITE del device handle; i CDB rimangono
limitati dall'allowlist. Non esistono elevazione, cambio modalità o retry
automatici nel modulo.

Se `DeviceIoControl` fallisce, `RomCommandError` conserva immediatamente il
codice Win32 e include in `details` stato SCSI, lunghezza trasferimento,
byte restituiti dalla IOCTL e sense buffer. Non include il buffer dati NOR.
Questi campi possono essere incompleti quando la IOCTL fallisce e non vengono
interpretati come prova di un trasferimento riuscito. Per misurare la durata
il chiamante deve registrare un tempo di fine distinto da quello di inizio.

| API | Condizione ed effetto |
| --- | --- |
| `upload_only` | Slot noto libero, hash del manifest verificato; solo `FB06` |
| `verify_upload_only` | Upload noto mai eseguito; solo `FD07`, decodifica e confronto completo |
| `verify_and_start` | Ripete la verifica completa, emette un `FB08`, verifica HYR1/HYRN |
| `upload_and_start` | Combina upload, verifica ed esecuzione |
| `read` | Solo dopo HYR1; espone esclusivamente lo slot del plugin |
| `start_reset_once` | Verifica manifest, ELF e nuova lettura RAM; un salto senza handshake HYR1 |

`known_free_slot=True` e `known_uploaded_unstarted=True` sono dichiarazioni
esplicite basate sulla cronologia del chiamante, reciprocamente esclusive.
Creare un nuovo oggetto Python non rende libero lo slot fisico. Dopo che un
plugin nello slot B ha pubblicato e confermato il proprio handler, lo slot A
del vecchio plugin può essere riutilizzato, purché non siano rimasti altri
puntatori o attività verso di esso. Se il salto a B ha esito ambiguo, non si
deduce quale handler sia attivo e non si sovrascrive nessuno dei due slot.

## Lettura NOR separata, senza scritture non volatili

Il profilo `nor-reader` usa il reader sorgente in
`firmware/mini/recovery_reader/`, manifest `research/mini-flash-reader.json`.
Il caricamento registra il protocollo HYRN senza inizializzare SPI.
`MiniNorSession.initialize_spi()` è una fase successiva esplicita.

| Comando HYRN | Risposta/azione |
| --- | --- |
| `FC70` | Identità `HYRN`, versione 1, flags 3, base e span dello slot; nessun MMIO |
| `FC72` | Setup PIO, uscita continuous-read, JEDEC; stato, capacità e divisore |
| `FD71` | Lettura fisica di 1..512 byte entro la capacità verificata |
| `FC73` | Errore persistente, inizializzazione, snapshot clock e contatore byte letti |

Il reader emette i comandi SPI `FF FF`, `9F` e `03`. Non contiene comandi
write-enable, program, erase o scrittura status. Il setup modifica registri
volatili SFC/SPI/pinmux, mantenendo codice e dati in RAM. La capacità deve
risultare esattamente 1 MiB dal JEDEC, non dalla dimensione del pacchetto FWSC.

Ogni `FD71` è seguito obbligatoriamente da `FC73`. Un errore persistente,
contatore inatteso o trasferimento corto invalida il blocco e la sessione.
Questo impedisce di confondere il riempimento `FF` usato dal reader in caso
di errore con dati flash validi. Le letture successive nella stessa sessione
mantengono il contatore cumulativo, anche tra due passaggi completi.

Un backup completo richiede due letture fisiche da `0x000000` a `0x100000`,
stati validi per ogni blocco, lunghezze esatte e confronto byte per byte/hash.
Né la lettura dello slot RAM, né la finestra CPU SFC, né il file FWSC stock
costituiscono tale backup. Una copia completa non dimostra da sola il recupero
di una flash corrotta: manca ancora la verifica del percorso ROM indipendente
dall'applicazione e della procedura di ripristino.

La SPEC AC791N descrive anche il dongle fisico `USB_KEY` come ingresso nella
mask ROM indipendente dal bootloader. La fonte riguarda FM-1/SMK-37; non è
una prova di funzionamento sul MINI. Non è stata stabilita una combinazione
dei pedali MINI che sostituisca questo percorso quando l'applicazione non parte.

## Reset RAM controllato

Il reset è un artefatto separato (`research/mini-rom-reset.json`), senza
protocollo HYR1. `start_reset_once` richiede il manifest dell'artefatto,
i byte ELF e i byte flat, verifica i digest, l'entry, il singolo segmento
pi32v2 nello slot e l'assenza di BSS/relocation. Il manifest deve provenire
dalla build reset già revisionata: il parser del client prova il collegamento
tra file e layout, non la semantica di codice arbitrario.

Il reset revisionato invalida la prima word del marker `0x01C7FD80`, imposta
il bit 4 di `0x10000` e attende. Dopo una nuova verifica integrale `FD07`,
il client emette un solo `FB08`. Una disconnessione successiva alla chiamata
IOCTL viene registrata come esito ambiguo; non viene convertita in successo.
Gli errori di validazione, lettura o trasporto precedenti all'invio restano
eccezioni. Occorre osservare separatamente la nuova identità USB normale
`4C4A:C755` e identificare `TANK MINI_009`.

## Riproduzione offline e fonti

```powershell
python -X utf8 tools/probe_mini_recovery.py
python -X utf8 -m unittest tests.test_mini_recovery -v
```

I 20 test verificano la guardia MINI, un modello CRC bitwise indipendente,
endianness/CDB, upload e readback nei due slot, mancata esecuzione dopo mismatch,
divieto di retry dopo salto ambiguo, resume con nuova lettura, profilo NOR,
stati per ogni blocco, manifest/reset e layout Windows completamente simulato,
inclusa la conservazione dei dettagli di una IOCTL fallita.
Non modellano elettricamente USB, flash o reset.

Fonti primarie fissate:

- [m-bootloader SPEC, commit 3ac7651](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md), sezioni 6.3 e 10.1; copia locale `upstream/m-bootloader/`.
- [pi32v2 hwtest runner, commit 1f09804](https://github.com/jvitkauskas/pi32v2-isa/blob/1f09804d36ddcba36dbd84cb6242ef88f35f15b7/tools/hwtest/runner.S).
- [m-flasher, commit 8fbece7](https://github.com/jvitkauskas/m-flasher/tree/8fbece7348d758ac284325eed455781675ac95ff), `src/jl.rs`, `usb.rs`, `scsi.rs`, `midi.rs`; hash dei sorgenti nel rapporto.
- Firmware MINI e disassembly dell'installer originale in `recovered/installer/`; nessun installer o loader FM1/SMK37 è stato eseguito per questa analisi.

`ota.bin` ufficiale è un contenitore JLFS con `usb_hid_ota.bin` da 19958 byte
complessivi, SHA256 `9c62bbdfd55f6527a3cffe43abc16c621d0900a8ff47685240abb1ee596eb66e`.
Il suo percorso è un aggiornamento con staging in flash; non corrisponde al
plugin flat con callback ROM e non viene usato per questa prova RAM.
