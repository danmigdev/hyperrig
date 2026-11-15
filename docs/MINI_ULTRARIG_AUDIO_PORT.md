# Hardware audio per il port integrale G → MINI

L'applicazione UltraRig G mantiene nel port il proprio DSP, scheduler, IRQ e
protocollo. Il firmware MINI stock è usato come fonte per la scheda: non è
il backend del firmware finale. L'audit offline identifica due punti per
adattare l'avvio audio della versione G M5.71 v2 al codec del MINI.
Non applica patch e non dichiara l'immagine pronta al flash.

```powershell
python -B -X utf8 tools/audit_mini_audio_port.py
```

[mini-audio-port.json](../research/mini-audio-port.json) conserva gli hash dei
due contenitori originali, le istruzioni decodificate, i preimage e i requisiti
di ogni punto d'intervento. I preimage appartengono all'app-area **decodificata**:
offset app-area = indirizzo CPU − `0x02000000`; offset `app.bin` = CPU −
`0x02000120`; offset flash logico = offset app-area + `0x4000`. Non sono byte
da scrivere direttamente nella NOR cifrata.

## Percorso ALNK condiviso

| Campo | G e MINI |
|---|---|
| Controller / IRQ | ALNK0 `0x12E00`, IRQ 11 |
| Clock / TX / RX | PA4–PA6 / PA7 canale 0 / PA8 canale 1 |
| Formato controller | I²S, dati 24 bit in slot da 32 |
| Buffer per canale / metà elaborata | 1024 byte / 64 frame |
| LEN / CON0 prima dell'abilitazione / CON1 attivo / CON3 | 128 / `0x180` / `0xD5` / `0x83` |

G usa l'indice 0 della propria tabella a `0x02035360`, ordinata dati poi
clock; MINI usa l'indice 1 della tabella a `0x02035E20`, ordinata clock poi
dati. Le due righe selezionano gli stessi pin: non serve sostituire la tabella
G con quella MINI o cambiare il suo indice. I valori G dei registri sono
derivati dalla configurazione e dalle istruzioni, non letti sul dispositivo.

G seleziona nominalmente 48000 a `0x02005148..5194`. Abilita `PLL_CON1 bit25`
e scrive `CLK_CON2 = (old | 0x100) & ~0x200`. Il ramo 48000 del MINI scrive
`(old & ~0xF00) | 0x500`. **Entrambi impostano allo stesso modo i bit ALNK0
8/9**. I bit 10/11 appartengono ad ALNK1, che il MINI aggiorna insieme ad ALNK0.
Questa differenza non giustifica una patch del selettore G. I nomi dei campi
sono nel [clock_hw.h del SDK fissato](https://raw.githubusercontent.com/amitv87/fw-AC79_AIoT_SDK/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h),
in dichiarazioni `#if 0`, corroborate dalle istruzioni di `iis_set_sample_rate`
nel `cpu.a` fissato. L'esatta frequenza fisica resta da misurare;
la famiglia nominale potrebbe essere circa 48076,923 Hz come spiegato in
[MINI_CLOCK.md](MINI_CLOCK.md).

## Sequenza di scheda da adattare

Il preambolo G a `0x020053A4..53C6` porta PC0, PC1 e PC5 alti e PA9 basso.
Sono quattro chiamate a `0x02004998`, con numeri GPIO 32, 33, 37 e 9.
La tabella del resolver G a `0x0203A2A4` conferma PORTA=`0x50000` e
PORTC=`0x50080`. I ruoli elettrici dei tre PC sul MINI non sono dimostrati:
copiarne le scritture non è un adattamento verificato.

Il MINI porta PA9 basso, attende 100000 iterazioni di un loop con `nop`,
inizializza il codec e ALNK, attende altre 100000 iterazioni e porta PA9 alto.
La funzione elettrica di PA9 e la durata in microsecondi dei loop restano
sconosciute; la transizione alta finale è comunque osservabile nel codice
MINI `0x0200723A..7242` e non è presente nel tratto G analizzato.

Il codec MINI riceve 22 record da quattro byte dalla tabella `0x02035E35`,
preceduti dal byte d'indirizzo `0x36`. Il bus usa PA1=SDA e PA2=SCL; lo stock
pilota anche i livelli alti e rilascia SDA per gli ACK. I record completi e
l'hash della tabella sono nel report. La tabella non compare nell'immagine G,
neppure il prefisso di otto byte; nel percorso G di avvio audio decodificato
non c'è questo replay. La ricerca di un pattern non dimostra l'assenza di
ogni possibile altro percorso codec nel firmware G.

La mappa dei registri è compatibile con NAU88L21/NAU88L21C; non identifica
fisicamente il componente. Il replay stock imposta OSR256. Restano le
incongruenze tra sezioni dei datasheet già documentate in MINI_CLOCK: non si
introduce un cambio OSR silenzioso né si deduce la validità dei clock da un ACK.

| Punto G | Preimage nel report | Adattamento richiesto |
|---|---:|---|
| `0x020053A4` | 34 byte | Hook di inizializzazione scheda MINI: PA9 basso, bus e record codec. Conservare anche l'assegnazione originale `r6=1`. |
| `0x0200541E` | 4 byte, chiamata a `0x02005194` | Conservare l'avvio canali G; aggiungere attesa e transizione PA9 finale soltanto dopo successo della configurazione. |
| `0x02005148` | 76 byte | Punto di ispezione clock; nessuna patch automatica richiesta per il mux ALNK0. |

L'audit registra i punti e i preimage. Il successivo
[modulo audio_port](../firmware/mini/audio_port/README.md) produce gli agganci
linkati: 2068 byte XIP a `0x02076AAC`, senza nuova RAM statica, e due patch
da 34 e quattro byte. Un piccolo stub nel preambolo conserva RETS/r4 per
controllare anche l'esito del post-hook; gli errori saltano a `0x02005436`,
prima dei flag di successo. Il bus usa il getter G `0x020057C6` in MHz con
conversione controllata, non il vecchio globale MINI a `0x01C1E32C`.

Prima della candidata avviabile rimangono da ricostruire la proprietà di
PA1/PA2 tra tutti i task G, i lock GPIO da conservare e il pannello fisico MINI.
Gli ID logici di manopole e switch nell'app non identificano pin. Restano
inoltre da qualificare clock effettivi, configurazione codec, mute analogico
e livelli. Nessuna operazione su hardware, flash o configurazione del pedale
è inclusa in questo audit.

Un conflitto è già dimostrato: `0x02015858..158C2` configura PA0..PA3 come
uscite, serializza 29 bit con clock PA2 e dati invertiti PA3, quindi porta PA0
alto e PA1 basso. Il caller `0x02017568` ha preimage `BF EA 76 F1`; il valore
di ritorno non viene usato e il pattern viene confrontato con la cache
`0x01C1F208`. Questo task G interferirebbe con PA1=SDA/PA2=SCL anche dopo
l'inizializzazione codec. Va adattato nel [port pannello](MINI_PANEL_PORT.md);
filtrare comandi nell'app non impedisce queste scritture firmware.

La [lettura diagnostica codec](../firmware/mini/codec_probe/README.md) prepara
il riscontro dei registri reali senza applicare record audio. I campi letti
possono confermare configurazione e risposta sul bus, ma non misurano i clock
né distinguono automaticamente NAU88L21 da NAU88L21C.
