# USB_KEY sperimentale con Raspberry Pi 3

Il Raspberry Pi 3 può generare il protocollo USB_KEY tramite due GPIO e un
cablaggio dedicato. Il sorgente [usbkey.c](../tools/usbkey_rpi3/usbkey.c) è
compilabile e verificato sul computer di sviluppo, con GPIO simulati.
**Non è ancora una procedura di recupero provata sul Raspberry Pi 3 o sul
TANK MINI.** Il risultato attuale non sblocca l'installazione del firmware.

USB_KEY è una sequenza elettrica sulle linee USB, usata per richiamare il
bootloader contenuto nella ROM del chip. Non è una chiavetta di memoria né
un normale comando USB. Il collegamento di un cavo USB tra PC e Raspberry
non genera questa sequenza: servono il connettore GPIO del Pi e un breakout
che esponga D+, D− e massa del cavo diretto al MINI.

La [descrizione originale del protocollo](https://kagaimiq.github.io/jielie/isp/usb/usb-key.html)
definisce la parola `0x16EF`, inviata dal bit più significativo, con D+
come clock e D− come dato campionato sul fronte di salita. La risposta è
un abbassamento di entrambe le linee per circa 1–2 ms. La tolleranza del
timing non è quantificata: circa 50 kHz è un riferimento, non una garanzia.

La [SPEC fissata di m-bootloader, §4.3](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md#43-recovery-independent-of-a-valid-boot-image)
riporta un'implementazione Pico funzionante su SMK-37 Pro: semiperiodi di
10 µs, pausa di 150 µs, pull-up esterni da 2,2 kΩ a 3,3 V e alimentazione
autonoma del dispositivo. Questa evidenza non riguarda il MINI. La
presenza della ROM WL82 nel MINI rende l'adattamento plausibile; la
ricezione del segnale durante l'avvio resta da verificare fisicamente.

## Cablaggio candidato

I numeri **BCM** usati dal programma e i numeri **fisici** del connettore
sono distinti. La corrispondenza è verificata nel
[pinout ufficiale Raspberry Pi](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pin-layout).
Prima del collegamento si identifica il pin 1 sulla scheda e si controllano
le etichette del breakout e la continuità del cavo; i colori dei fili non
sono una prova sufficiente.

| Raspberry Pi 3 | Pin fisico | Collegamento al breakout USB 2 |
|---|---:|---|
| BCM17 | 11 | D+, clock |
| BCM27 | 13 | D−, dati |
| GND | 6 | GND del segnale USB |
| 3,3 V | 1 | Un resistore da 2,2 kΩ verso D+ e un secondo da 2,2 kΩ verso D− |
| 5 V | 2 e 4 | Nessun collegamento |
| VBUS del breakout | — | Scollegato |

```text
Pi fisico 1 (3,3 V) ── 2,2 kΩ ──┬── USB D+
Pi fisico 11 (BCM17) ────────────┘

Pi fisico 1 (3,3 V) ── 2,2 kΩ ──┬── USB D−
Pi fisico 13 (BCM27) ────────────┘

Pi fisico 6 (GND) ───────────────── USB GND
                                    USB VBUS: non collegato
```

Il Pi usa il proprio alimentatore; il MINI la propria batteria. Il PC
non deve essere collegato contemporaneamente a queste linee. I GPIO sono
a 3,3 V; non si applicano 5 V ai segnali. I due resistori sono separati:
non si collega direttamente il pin 3,3 V a D+ o D−. Le caratteristiche
dei GPIO sono documentate nel
[white paper ufficiale Raspberry Pi](https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-006553-WP-2-A%20history%20of%20GPIO%20usage%20on%20Raspberry%20Pi%20devices,%20and%20current%20best%20practices.pdf).

Il percorso del connettore USB-C del MINI, la rilevazione CC/VBUS e la
finestra di ascolto al suo avvio non sono stati misurati con questo circuito.
Non vengono proposti collegamenti aggiuntivi ai pin CC né un'alimentazione
VBUS improvvisata per aggirare un eventuale mancato riconoscimento.

## Implementazione e comportamento

Il programma C usa direttamente
[GPIO character device API v2 di Linux](https://www.kernel.org/doc/html/latest/userspace-api/gpio/chardev.html),
disponibile dal kernel 5.10, e non richiede una libreria GPIO esterna.
La modalità reale verifica il modello Pi 3, il controller
`pinctrl-bcm2835`, gli offset 17/27 e che le linee siano libere. Un nome
di controller diverso o una configurazione non supportata provoca errore;
non viene tentato un accesso alternativo a `/dev/mem` o sysfs.

La richiesta al kernel è sempre `OUTPUT | OPEN_DRAIN | BIAS_DISABLED`,
senza inversione ACTIVE_LOW. Zero significa pilotare verso massa; uno
significa rilasciare la linea. Non viene richiesta un'uscita HIGH push-pull.
Linux può implementare il rilascio commutando il GPIO in ingresso; il
[contratto del driver](https://docs.kernel.org/driver-api/gpio/driver.html#gpio-electrical-configuration)
segnala che la commutazione può introdurre glitch. Il codice non sostituisce
una misura elettrica con oscilloscopio o analizzatore logico.

Il rilevamento della risposta applica questa politica conservativa,
scelta per l'esperimento e distinta dalla specifica ROM:

1. Entrambe le linee rilasciate devono essere state lette HIGH.
2. Deve essere stato trasmesso almeno un frame completo.
3. Entrambe devono diventare LOW mentre il programma le ha rilasciate.
4. Il LOW deve terminare: durata osservata compresa tra 0,5 e 3 ms.
5. Una pausa tra campioni della possibile risposta oltre 100 µs rende
   l'esito ambiguo.

Un dispositivo spento che mantiene le linee basse non fa partire la
trasmissione e non viene dichiarato una risposta. Una linea bloccata LOW,
un impulso troppo corto o un errore di I/O non producono successo.
La durata predefinita richiesta è 20 secondi, limitata da CLI a 60 secondi.
Sono limiti software: un blocco del kernel o della schedulazione può
ritardare anche il controllo della scadenza e il rilascio.

Il programma intercetta SIGINT/SIGTERM e, quando può eseguire la pulizia,
rilascia entrambe le linee, le configura come ingressi e chiude la richiesta.
SIGKILL, spegnimento del Pi ed errori del kernel non garantiscono questa
pulizia. Il log riporta se rilascio e riconfigurazione sono riusciti.

## Compilazione e prove senza GPIO

Per riprodurre le verifiche sul computer di sviluppo, dalla radice del
repository:

```powershell
python -X utf8 tools/usbkey_rpi3/verify.py
```

Il verificatore usa il compilatore Linux già disponibile, tramite Ubuntu/WSL
su Windows. Non installa pacchetti e non invoca mai `--execute`. I test
coprono ordine dei 16 bit, durata minima, pedale simulato spento, assenza
di risposta, impulsi anomali, ritardo del scheduler, errori I/O a ciascun
passaggio, scadenze e interruzione. ASan/UBSan e compilazione con
`-Wall -Wextra -Werror` sono inclusi. Sono verificati anche la simulazione
predefinita e il rifiuto di sovrascrivere un log esistente.

Il report [mini-usbkey-rpi3.json](../research/mini-usbkey-rpi3.json) contiene
hash, risultati e architettura del compilatore. Il binario prodotto su
WSL x86_64 **non è un eseguibile ARM per il Raspberry**.

Sul Pi, con un compilatore C e gli header Linux già disponibili, il comando
di compilazione locale dalla radice della copia del repository è:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror tools/usbkey_rpi3/usbkey.c -o usbkey-rpi3
./usbkey-rpi3 --log simulazione.json
./usbkey-rpi3 --timing-only --timeout-ms 1000 --log timing-pi.json
```

Entrambe le esecuzioni usano linee fittizie. `--timing-only` ripete i frame
fino alla scadenza e termina intenzionalmente con codice 2 (`timeout`).
Questo misura l'attesa software e il jitter del sistema operativo, senza
misurare ioctl GPIO o fronti elettrici. Non serve collegare il pedale.

## Futuro esperimento fisico, prima di sostituire il firmware

Il comando seguente è documentato per una futura esecuzione manuale con
il cablaggio controllato; non è stato eseguito in questa attività:

```sh
sudo ./usbkey-rpi3 --execute --chip /dev/gpiochip0 --timeout-ms 20000 --log usbkey-prova-01.json
```

Il nome del file deve essere nuovo. Un errore nell'apertura del log
interrompe il programma prima della richiesta GPIO. Il Pi deve essere
già avviato; il collegamento GPIO non va lasciato applicato mentre il Pi
stesso si accende o si riavvia, perché questo programma non controlla la
configurazione dei pin durante il boot del Pi. Il tentativo di ricezione
avviene accendendo il MINI mentre il programma è in esecuzione, mantenendo
inizialmente il firmware originale integro.

`ack_candidate` significa soltanto che le letture soddisfano la politica
indicata. Dopo il rilascio occorre scollegare fisicamente il circuito GPIO,
inclusi i pull-up, e collegare il MINI al PC mantenendolo alimentato.
Il passo di conferma è l'identificazione indipendente USB
`4C4A:8057`, SCSI `WL82` / `UBOOT1.00`, tramite un controllo in sola lettura.
Nessuna scrittura firmware serve a provare questo ingresso.

Il tool non genera un successivo riferimento SOF da 1 ms: le note originali
segnalano che alcune ROM misurano il clock dopo la risposta usando il bus
USB. Il passaggio al PC, la sua latenza e l'enumerazione sul MINI restano
quindi parti della prova, anche quando viene osservato un impulso valido.
Se l'esito è timeout o ambiguo, non si procede a sostituire l'applicazione
facendo affidamento su questa via di recupero.

Il log conserva i timestamp `CLOCK_MONOTONIC` prima/dopo ogni operazione,
il massimo ritardo delle attese, il numero di frame e gli ultimi 4096
eventi. Il conteggio degli eventi omessi resta esplicito. Le attese partono
dopo il completamento dell'operazione precedente: il programma non tenta
di recuperare un ritardo accorciando gli impulsi successivi. Di conseguenza
la frequenza reale può essere inferiore a 50 kHz. Non sono modificati
priorità del processo, interrupt, clock o memoria del dispositivo.
