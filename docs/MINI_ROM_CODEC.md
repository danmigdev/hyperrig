# Diagnostico codec in RAM

Il 15 novembre 2026 il MINI ha eseguito il diagnostico `HYC1`. Upload e
rilettura dei 3.376 byte sono riusciti; il programma ha completato la prima
transazione e ripristinato i bit GPIO di PA1/PA2. Il codec ha risposto con
**NACK al primo byte, indirizzo `0x36`**, nella lettura del registro `0x58`.
Non è stato ottenuto alcun valore. Le altre nove letture sono state omesse,
senza ritentare né modificare alimentazione o clock.

Le [osservazioni fisiche](../research/mini-codec-hardware.json) conservano hash,
record completo, stato GPIO e ritorno allo stock. Lo stack privato ha mostrato
256 byte modificati, con guard integre. Il pedale è tornato a `TANK MINI_009`;
due letture dei preset erano uguali al backup precedente. La flash non è
stata scritta dal diagnostico.

Il NACK in ROM non identifica il componente e non dimostra un guasto. Lo
stato di alimentazione, reset e MCLK in questa modalità non è qualificato.
Il programma non applica la sequenza di inizializzazione audio del firmware.

## Sorgenti e protocollo

```powershell
python -B -X utf8 tools/build_mini_rom_codec.py
python -B -X utf8 -m unittest tests.test_mini_codec_protocol
```

Il [builder](../tools/build_mini_rom_codec.py) non apre dispositivi. Compila
gli slot RAM `0x01C20000` e `0x01C28000`, ciascuno da 32 KiB. Codice e stato
occupano 7.704 byte, inclusi 4 KiB di stack privato. La build usa soltanto
quattro funzioni del componente codec: inizializzazione bus, allowlist,
lettura e attesa finita. Scrittura dei registri codec e reset sono esclusi
dal link. Il [manifest](../research/mini-rom-codec.json) conserva i test offline
separatamente dalla prova fisica.

| Comando | Fase IN | Effetto |
|---|---:|---|
| `FC64` | 16 byte | Identità `HYC1`, versione e slot; nessun accesso GPIO |
| `FC65 reg_BE16` | 16 byte | Una lettura, con snapshot e ripristino PA1/PA2 |
| `FD66` | 128 byte | Record dell'ultima transazione; nessun nuovo accesso GPIO |

Le CDB hanno 16 byte e padding `FF` esatto. Le letture sono limitate a
`01,03,1C,1D,2B,2C,31,32,58,59`. La fase di selezione invia soltanto
`36 reg_hi reg_lo`, poi repeated START e `37`; seguono due byte letti e STOP.
Non vengono inviati dati di configurazione al codec. Ogni lettura conserva
cinque registri GPIO e ripristina soltanto i bit 1/2, lasciando agli altri
pin il loro stato corrente. Le attese sono finite, `units × 1024` iterazioni,
senza attribuzione di una durata in microsecondi.

Il client [probe_mini_codec.py](../tools/probe_mini_codec.py) verifica risposta,
sequenza, registro, build tag, CRC, contatori e ripristino. Una risposta persa
o incoerente invalida la sessione e non viene ripetuta. Un NACK completo viene
registrato come tale. Il profilo USB `ram-codec` rifiuta gli altri comandi
diagnostici e non dispone di comandi di scrittura della flash.

I test ASan/UBSan comprendono guardie del protocollo, tutti i registri esclusi,
NACK nelle quattro posizioni, ripristino fallito e rientro durante l'operazione.
Il decoder indipendente delle transizioni sul bus prova tutti i 65.536 valori
di ritorno e 221 errori. Questi controlli non sostituiscono una prova elettrica
né qualificano il percorso audio a 48 kHz.

## Seconda prova: HYC2 e clock della ROM

Il 15 novembre 2026 è stato eseguito anche il diagnostico HYC2 separato:
5.856 byte caricati e riletti, build tag `0x71A0F2B7`. La prima snapshot
dei 17 registri è stabile e il record di 512 byte supera la validazione.
Lo stack privato mostra 472 byte modificati e guard integre.

La configurazione `CLK_CON0=0x1C1`, `CLK_CON2=0x80`,
`PLL_CON0=0x0940022B`, `PLL_CON1=0x3F5030EE` non soddisfa il controllo
del riferimento PLL basato sul boot dell'applicazione. HYC2 restituisce
`gate=4`, `status=-3`; non è stato inviato alcun comando `FC69`.
Non ci sono state operazioni GPIO né transazioni codec. Questi valori
sono registri osservati, non una misura della frequenza.

Il ritorno a MINI_009 e l'uguaglianza dei preset sono verificati per la
quinta volta. Il [resoconto fisico HYC2](../research/mini-codec-board-hardware.json)
conserva record, pin dei sorgenti e log; il
[manifest offline](../research/mini-rom-codec-board.json) resta separato.
La prova chiarisce il contesto ROM ma non risolve il NACK HYC1 né qualifica
audio, identità codec o avvio della candidata integrale.
