# Probe ROM del motore A2L sul MINI

Questo nuovo plugin qualifica il motore ricostruito su un **fixture sintetico
a tre layer**. Non è la capture A2 originale a 23 layer e non è un firmware
installabile. Collega gli stessi componenti `hyperrig_a2l`, `rechannel`, `layer`,
`head` ed `engine` usati per la ricostruzione A2; non introduce un altro DSP.
Il port completo di UltraRig/HyperRig sul MINI, inclusa l'app, resta il risultato
da raggiungere. Questo passo verifica caricamento e calcolo entro lo spazio
RAM disponibile tramite la ROM.

Il [manifest](../research/mini-rom-engine.json) conserva le verifiche offline
della build. La successiva [prova fisica del 15 novembre 2026](../research/mini-engine-hardware.json)
ha eseguito lo slot A sul MINI: 230 frame, sei blocchi e ripetizione dopo reset
in 14 blocchi hanno prodotto i CRC attesi. Entrambe le esecuzioni sono riuscite,
con guard di stack e arena integre e 1.288 byte di stack osservati. Il payload
di 8.560 byte è stato riletto integralmente prima del salto. Il ritorno al
firmware stock è stato verificato tramite USB/MIDI e due letture identiche dei
preset, invariati rispetto al backup. Nessuna scrittura della flash.

## Build riproducibile

```powershell
python -B -X utf8 tools/build_mini_rom_engine.py
```

Il [builder](../tools/build_mini_rom_engine.py) usa toolchain e disassemblati
originali già fissati dal progetto. Non apre USB né altri dispositivi.
Genera `build/mini-rom-engine/synthetic3.a2l`, `fixture.h`, un eseguibile host
ASan/UBSan e due coppie ELF/bin per gli slot `0x01C20000` e `0x01C28000`.
Il manifest conserva hash di sorgenti, header, fixture, kernel oracle e payload.
La build comprende 46 casi di protocollo host e controlli che rifiutano ELF
fuori limite, mapping incoerenti e record alterati anche con CRC ricalcolato.

Il fixture proviene da `synthetic(random.Random(0x48594531))` in
[verify_engine_native.py](../tools/verify_engine_native.py): 728 byte, kernel e
dilatazioni `1/1`, `6/3`, `15/7`, head di quattro tap, campo ricettivo 117 campioni.
Il seed è proprio di questa prova: i golden di altri fixture non sono riusati.
Il CRC fixture nel record è quello del corpo A2L, esclusi i quattro byte CRC
finali; l'hash SHA-256 nel manifest identifica l'intero file.

## Calcolo verificato

Il selftest carica il file con verifica CRC, inizializza il motore e processa
230 campioni deterministici in blocchi `1, 63, 64, 7, 31, 64`. I ring di
64, 79 e 162 frame attraversano tutti almeno una volta il loro termine.
Dopo ogni blocco confronta tre CRC: uscite cumulative, somma cumulativa dei
layer e cronologie/posizioni. Il percorso comprende rechannel, convoluzione,
mix dell'ingresso, attivazione, residuo, somma e head.

Il builder ottiene questi golden eseguendo i byte originali dei kernel G
negli interpreti del progetto. Scheduling e contesti sono ricostruiti, non
emulati dalla funzione originale completa. Anche l'oracle ripete il flusso
con blocchi da 17: in totale sono 100 invocazioni dei kernel di segnale.
Il plugin esegue reset e la stessa ripetizione in 14 blocchi, confrontando
uscita e stato finale. Non memorizza una traccia di uscita attesa generata
dalla propria implementazione C.

## Memoria e stack

| Dato target | Byte |
|---|---:|
| Codice e costanti caricati | 8560 |
| BSS, inclusi stack privato e record | 16328 |
| Occupazione totale nello slot | 24888 |
| Spazio residuo nello slot da 32768 | 7880 |
| Arena modello: query / uso allineato | 895 / 888 |
| Arena motore: query / uso allineato | 9135 / 9128 |
| Stack privato | 4096 |
| Guard sotto / sopra lo stack | 32 / 32 |
| Limite statico della catena interna del selftest | 1288 |

I byte delle strutture ABI sono estratti dall'ELF target e usati per verificare
il layout degli arena. Le query host sono diverse, 967 e 9167 byte, perché
il programma ASan è x86-64. Ogni arena ha guard proprie e allineamento a otto
byte. Il linker e l'ispettore ELF impongono che codice, dati, BSS, stack e
record restino nel singolo slot.

Il [trampolino separato](../firmware/mini/rom_stack/rom_stack_pi32v2.S) salva
otto byte sullo stack entrante, chiama il core con lo stack privato e ripristina
SP, RETS e r4 prima del ritorno. La verifica delle nove istruzioni è descritta
in [mini-rom-stack.json](../research/mini-rom-stack.json). Il core non invoca
servizi ROM: l'invio USB avviene dopo il ritorno allo stack entrante.
Il test host usa lo stack normale di ASan e non esegue il trampolino target.

Il limite statico di 1288 byte comprende i frame e le chiamate dirette del
core compilato; non comprende interrupt, ROM o chiamanti esterni. Il wrapper
misura i byte di riempimento modificati e verifica le guard al ritorno.
Quella misura può sottostimare i byte riservati ma non scritti e non prova
un massimo assoluto. Il cambio stack è stato eseguito nella prova fisica;
resta sconosciuto il massimo uso da parte degli interrupt ereditati.

## Protocollo e record

La ROM usa la stessa struttura di tre puntatori e il normale ABI C del probe
precedente. L'inizializzazione copia il callback d'invio, inizializza soltanto
stato privato, esegue il test e pubblica l'handler. `FC62` riesegue il test;
`FD63` legge soltanto il proprio slot, con invii di massimo 512 byte.
I precedenti `FC60` e `FD61` non sono gestiti da questo plugin.

La risposta `FC62`, di massimo 16 byte, è:
`FC62 | frame BE32 | HYE1 | errori BE32 | 00 | versione 01`.
La semantica dei ritorni d'errore del callback d'invio resta sconosciuta;
l'host deve verificare trasferimento e record intero.

Il record è lungo 128 byte. Le word sono little endian:

| Offset | Campo |
|---:|---|
| 0 | `HYE1` ASCII |
| 4, 8, 12, 16, 20 | Versione 1, base, span 32768, esecuzioni, bit di errore |
| 24, 28, 32 | Frame 230, blocchi 6, layer 3 |
| 36, 40, 44 | CRC uscita, somma e cronologie/posizioni |
| 48 | CRC uscita dopo reset/ripartizione |
| 52, 56, 60, 64 | Query modello, query motore, uso modello, uso motore |
| 68, 72, 76, 80 | Indirizzo record, dimensione 128, build tag, CRC corpo fixture |
| 84, 88, 92 | Stack riservato, byte osservati modificati, guard stack valide |
| 96, 100, 104 | CRC cronologie ripetizione, blocchi 14, frame 230 |
| 108 | Flag: bit 0 indica il percorso target con stack privato |
| 112, 116 | Ultimo risultato API C, guard arena valide |
| 120 | CRC32 dei byte `[0,120)` |
| 124 | `DONE` ASCII |

I bit di errore sono definiti in [rom_engine.h](../firmware/mini/rom_engine/rom_engine.h).
Un risultato valido richiede stato zero e guard valide. Il builder espone
`validate_record(raw, golden, build_tag, base, record_address, runs=..., target=True)`:
verifica tutti i campi, CRC, dimensioni target e un'osservazione stack nell'intervallo
`1..4096`. Golden, tag e indirizzo devono provenire dal manifest dell'immagine
effettivamente caricata; identità del payload e rilettura rimangono verifiche
distinte a carico dell'host.

Questa prova non convalida la capture A2 originale, l'avvio dalla flash,
clock audio, codec, I2S, DMA, latenza o compatibilità con l'app. Non contiene
accesso flash, GPIO o configurazione di periferiche audio.
