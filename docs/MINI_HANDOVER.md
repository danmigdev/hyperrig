# Handover MINI e probe interamente XIP

Il linker `firmware/mini/handover/mini_xip.ld` produce due diagnostici con
**tutte le istruzioni nella flash mappata**. Rimuove il requisito di rendere
visibile alla CPU il codice appena copiato in RAM. Non configura cache, MMU,
PLL, codec o periferiche. Sono applicazioni per l'ingresso dal bootloader
stock, non programmi da caricare mediante l'ABI USB della ROM.

`python tools/verify_mini_handover.py` ricontrolla il firmware MINI 009,
ricostruisce i frammenti del bootloader, compila tramite JieLi/WSL e scrive
`research/mini-handover.json`. Non apre dispositivi e non produce pacchetti
di aggiornamento. Non sono stati eseguiti questi ELF sul MINI.

## Prova nel bootloader originale

Il contenitore `uboot.boot` è estratto dal `flash.bin` del FWSC verificato;
header e payload vengono decifrati separatamente con ENC FFFF. Sono
verificati i CRC della directory, del contenitore e delle due parti BANKCB.
Il payload è lungo `0x3820`, caricato a `0x01C02000`, con SHA256
`fcaf033c5e10526353ecb11279a7556ac8645026d370c0267912cb4bfa7c7e4d`.
Header CRC `BCF5`, payload CRC `81A2`, contenitore CRC `71C8` coincidono con
il formato del riferimento AC791N, ma le prove qui usano i byte MINI.

| Istruzioni MINI | Effetto osservato |
|---|---|
| `0x01C02000..2046` | Ingresso ROM in contesto eccezione: salva r0 sulla pila ereditata, azzera BSS privata, `rete=0`, `reti=0x01C02036`, `rti`; poi SSP/SP privati. |
| `0x01C024E4..2532` | Cancella bit8/9 di `0x01EEE008`, azzera quattro intervalli interni, rimette bit8/9. |
| `0x01C032E4..32F6` | Scrive la chiave in `0x13004` e `0x40304`. |
| `0x01C050C6..51A2` | Disabilita SPI0, seleziona SFC, azzera/configura SFC e baud, imposta la base fisica dell'applicazione. |
| `0x01C051BE` | Chiama nuovamente la pulizia cache `0x01C024E4`. |
| `0x01C051C2..51D8` | `cli`, attesa bit14 cache, ENC control `0x40300=1`, cache control OR `0x300`. |
| `0x01C05284..528E` | Carica entry dal descrittore, prepara `r0=0x01C7FE08`, esegue `call r1`. |
| `0x0200019E` | Dopo la copia RAM, il reset dell'applicazione stock chiama RAM `0x01C00E8C`. |

Il trace del ciclo originale verifica esattamente 6.402 store word: due al
registro di controllo e 6.400 alle seguenti aree, per 25.600 byte azzerati:

* `[0x01F00000,0x01F04000)`;
* `[0x01F08000,0x01F0A000)`;
* `[0x01F0A000,0x01F0A200)`;
* `[0x01F0B000,0x01F0B200)`.

Il trace prova indirizzi, ordine, ampiezza e valori delle scritture, con due
valori iniziali diversi del controllo; non simula la cache fisica. Il listing
limitato ai frammenti identificati è `build/mini-handover/stock-handover.asm`.

Il reset dell'applicazione stock non pubblica esplicitamente istruzioni tra
la copia RAM e quella prima chiamata. Questo indica una dipendenza dal
contesto preparato in precedenza; non dimostra un'operazione generale di
invalidazione I-cache, né lo stato MMU a qualsiasi possibile ingresso.
Il solo `csync` di HyperRig non è presentato come una tale operazione.

## Varianti compilate

| ELF in `build/mini-handover/` | Byte caricabili | Funzioni in XIP | Copia RAM |
|---|---:|---:|---:|
| `hyperrig-mini-xip-minimal.elf` | 476 | 7 | 4 byte dati |
| `hyperrig-mini-xip-runtime.elf` | 13.624 | 63 | 4 byte dati |

La variante runtime sposta in flash anche 234 byte delle sezioni `.ramtext`
del componente runtime. Include il percorso evento simulato → worker → A2
→ conversione TX già verificato sull'host. Le callback di ownership restano
quelle per buffer privati; non sono registrati IRQ reali, avviata DMA o
chiamate funzioni di configurazione ALNK/codec. Non sono collegati i
componenti hardware platform/codec. Il vecchio replay tabellare presente
nell'oggetto audio rimane inattivo.

L'audit richiede tutti i segmenti e tutte le sezioni eseguibili in
`[0x02000120,0x0207E000)`, e tutti i simboli ELF `STT_FUNC` nella stessa
regione. I segmenti RAM sono RW. Nessuna istruzione viene copiata dal reset.
I vincoli ELF esistenti, le riserve superiori RAM e le due simulazioni del
reset sono mantenuti. Le simulazioni si fermano prima del C.

I sorgenti del probe sono quelli già verificati, senza modifiche: il report
controlla i loro hash e quelli degli oggetti core/audio/runtime. Riporta la
prova host ASan/UBSan esistente con CRC DSP `f10b5e4c` e TX `f0a44a06`,
senza attribuirla all'esecuzione del nuovo ELF sul target.

## Sequenza e limiti

1. È necessario il normale ingresso applicazione del bootloader stock:
   SFC mappata/decifrata, cache predisposta e `r0` valido come sopra.
2. Il reset HyperRig disabilita IRQ, copia il descrittore prima di azzerare
   RAM, imposta le pile private, azzera BSS e copia un word di dati.
3. Il marcatore minimo scrive il mailbox a `0x01C00020` e termina nel loop
   diagnostico con stato hook `-100`. La variante runtime usa il mailbox a
   `0x01C35580`, attende stato applicazione/audio `0` e i due CRC indicati.
4. Non vengono modificati SFC, ENC, PLL, partizione cache o MMU. La routine
   stock di cambio clock `0x01C03352`, che spegne SFC, non è compatibile con
   questo percorso XIP e non deve essere aggiunta al linker per richiamarla.

Restano da dimostrare sul dispositivo: ingresso reale e trasporto per
osservare il mailbox, stato MMU/alias RAM, CPU1, durata watchdog, IRQ/DMA e
timing audio. Il bootloader cancella l'enable watchdog all'inizio della sua
inizializzazione; questo non sostituisce una misura della durata del probe
in ogni percorso possibile. Un programma ROM USB deve invece conservare
stack, ritorno e callback della ROM e confinare memoria ai suoi slot: non
può riusare questo reset che occupa la RAM applicativa.

Il reset software è attestato anche nel MINI a `0x01C028F4..28FE`:
`0x10000 |= 0x10`, poi loop. Non è una scrittura NVM. La presenza del marker
RAM `usb_update_mode` può cambiare il boot successivo; questa analisi non
prova che il marker sia già cancellato all'ingresso ROM e non fornisce una
procedura hardware automatica di ritorno.

Riferimento indipendente: [m-bootloader, SPEC §§3.6 e 4.1](https://github.com/jvitkauskas/m-bootloader/blob/3ac7651a019fa44daba061b05654278496477b64/docs/SPEC.md).
Il suo hardware di prova è FM1/SMK37; non viene trasferita al MINI alcuna
affermazione di avvio fisico.
