# Disponibilità del codec MINI: evidenza dopo HYC1

Il primo NACK HYC1 non identifica il codec e non ne dimostra l'assenza.
Il report [mini-codec-availability.json](../research/mini-codec-availability.json)
conserva hash, preimage e limiti dell'analisi. HYC1 e lo shim audio v1 sono
rimasti invariati. La prova fisica del 15 novembre 2026 è documentata in
`analysis/hardware/mini-codec-run.json`: il primo byte indirizzo riceve NACK,
con ACK=0, nessun dato ricevuto, un campionamento SDA e 35 attese. Stack,
ripristino PA1/PA2, ritorno a MINI_009 e preset invariati risultano verificati
nel resoconto; nessun registro del codec è stato identificato.

Payload HYC1 eseguito: SHA256
`084ca247eeb53c5ab165dec62059ca0a0022ab7719c9975a5efd3db97da184fa`.
Record128: SHA256
`9736667745a0c7b8ad5628f694a0dd8df0979b151b9e4b09d6f710dc76381ca8`.

`0x02006DD6` carica **54 decimale = 0x36**, poi chiama il trasmettitore
`0x02006C6A`: nessuno shift dell'indirizzo. Il trasmettitore usa maschera
`0x80 >> bit_index`, quindi il byte sul filo è `00110110`, indirizzo a sette
bit `0x1B`. L'interpretazione indipendente dei byte stock e del payload HYC1
eseguito conferma lo stesso START, gli stessi otto bit e il rilascio di SDA
prima del nono clock. Il campionamento avviene con SCL alto. Le 57 operazioni
normalizzate fino a quel campionamento coincidono; hash traccia
`07059f8581420830b4431cb832f02c72dccd55d1ef2ca3af195d7847fd5309f1`.
La normalizzazione rimuove soltanto scritture OUT identiche consecutive e
confronta unità di attesa, senza simulare durata, GPIO elettrici o interrupt.

Lo stock ripete un OUT(SCL,0) già basso prima dell'ACK. Dopo il campionamento
riprende SDA come output; read16 la lascia rilasciata per la lettura e tenta
STOP anche su errore. Queste differenze successive non spiegano il primo NACK.

Le durate invece differiscono: stock usa
`units * floor(sys_hz / (SFCbit0 ? 8000000 : 4000000))`; HYC1 usava
`units * 1024`. A 360 MHz nominali lo stock usa 45 o 90 iterazioni per unità.
Non abbiamo misurato gli edge fisici. La tabella 13 del
[datasheet Nuvoton rev3.1](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.1.pdf)
specifica anche limiti massimi di hold DATA e rise/fall: rallentare non
costituisce automaticamente una qualifica temporale.

La sequenza di alimentazione documentata dal
[datasheet rev2.7, §2.1–2.2](https://www.nuvoton.com/export/resource-files/DS_NAU88L21_DataSheet_EN_Rev2.7.pdf)
colloca la configurazione I²C prima dell'applicazione dei clock I²S.
Non giustifica quindi l'ipotesi che MCLK sia necessario per il primo ACK.
Lo stock MINI chiama la tabella codec a `0x02007188` e l'apertura ALNK soltanto
a `0x020071E6`; ciò non prova che nessun clock fosse già ereditato dal boot.
Le fonti Nuvoton descrivono un candidato compatibile: l'identità fisica sul
MINI rimane sconosciuta.

PC5 è inizializzato prima del codec, nella catena
`020071FE → 020067F2 → 020060D0 → 02005BCE`. L'ultimo frammento, 148 byte,
ha SHA256 `216b7f3a3e475bafaecd0e2eccddad0655f4aa8275cd841b38ae991e42c4b733`.
Tocca soltanto GPIO37/PC5 e i lock RAM/IRQ delle API originali:

| Ordine | Registro | Operazione su PC5 |
|---|---|---|
| 1 | DIE `0x5008C` | imposta bit5 |
| 2 | OUT `0x50080` | imposta bit5 |
| 3 | DIR `0x50088` | azzera bit5, output |
| 4 | HD `0x5009C` | azzera bit5 |
| 5 | HD0 `0x50098` | azzera bit5 |

PU, PD e DIEH restano invariati. Il solo caller diretto dell'init è
`0x020060D2`. Dopo la configurazione pannello, `0x02007218` mette PA9 basso;
segue un ciclo da 100000 iterazioni e un `delay(10)` RTOS prima della tabella
codec. L'unità temporale di quel delay non è ricostruita qui.

**PC5 non è una rail audio dimostrata.** Il writer `0x0200AF46` lo porta alto
con argomento zero e basso altrimenti. Il task `0x0200BDEC` lo richiama a
`0x0200BF78` alternando soglie 13/26 oppure 25/51; il ramo inattività
`0x0200B6DA` lo forza alto e continua l'applicazione. Il comportamento è
compatibile con un indicatore, come inferenza. Non sono emersi comandi
poweroff/storage nei frammenti PC5. Il boot usa PORTD `0x500C0` per NOR/SPI0,
quindi PC5 non appartiene a quel bus; ciò non sostituisce uno schema elettrico
e non esclude tutte le possibili connessioni esterne. I percorsi generici di
sleep/restore delle porte non sono stati esauriti da questo audit.

Gli altri setup immediatamente vicini riguardano PC9/ADC8, PC0/ADC6,
PA10/PA0/PA3 come ingressi, PB7 come ingresso e PC10/SPI1. Non sono stati
inclusi in un probe minimo senza una dipendenza audio dimostrata.

Per il clock principale, il ramo **attivo** dell'header
[clock_hw.h fissato al commit SDK](https://github.com/amitv87/fw-AC79_AIoT_SDK/blob/ffbb2a8d925682ba6880d643a83a63ee0691ec09/include_lib/driver/cpu/wl82/clock_hw.h)
definisce `CLK_CON0[8:6]`: RC=0, BTOSC=4, riservato=5, RTOSC_L=6, PLL=7.
`TEST_SEL[3:2]=0` seleziona l'ingresso normale. Il boot MINI a `0x01C04582`
imposta `0xC0`, poi a `0x01C045B6` imposta `0x100`, dopo aver preparato PLL
e divisori: selettore finale 7. Questo chiude il significato del mux, senza
trasformare il valore nominale ricavato dai registri in una misura.

È quindi ragionevole un diagnostico **HYC2 separato**, prima snapshot-only e
poi una sola lettura esplicita con PC5/PA9 nello stato stock osservato.
L'implementazione e lo schema sono in
[rom_codec_board/rom_codec.h](../firmware/mini/rom_codec_board/rom_codec.h);
[build_mini_rom_codec_board.py](../tools/build_mini_rom_codec_board.py) produce
il manifest [mini-rom-codec-board.json](../research/mini-rom-codec-board.json).
Non modifica PLL, USB, NOR o dati del codec. Se sorgente/reference non sono
riconosciuti, resta alla snapshot. Ripristina tutti i bit GPIO toccati, inclusi
PC5 HD/HD0. Replica il ciclo da 100000 iterazioni e la scala aritmetica del
bus; il delay RTOS, l'overhead RAM e gli edge elettrici non diventano per
questo equivalenti allo stock. Nessuna esecuzione HYC2 è attestata qui.

Una futura revisione dello shim integrale G deve mantenere separatamente il
setup PC5 osservato, senza cancellarlo insieme agli output G PC0/PC1 non
adatti al MINI. Il v1 resta congelato e questa indicazione non promette ACK,
48 kHz, mute o avvio audio funzionante.
