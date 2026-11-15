# Ricezione ROM HYRX sul TANK MINI

Il 15 novembre 2026 HYRX ha ricevuto sul MINI **260 byte esatti**, con
ritorno grezzo della callback pari a **260**. Due record successivi conservano
gli stessi dati, CRC e guard intatti. È una prova fisica di questa singola
transazione; non qualifica una convenzione generale per i ritorni della ROM,
il writer NOR o l'avvio dell'applicazione HyperRig.

Il resoconto sigillato è
[mini-receive-hardware.json](../research/mini-receive-hardware.json). Include
entrambi i record completi, il payload diagnostico e gli hash dei log originali.
Il [manifest di compilazione](../research/mini-rom-receive.json) rimane
immutato: il suo `hardware_executed: false` descrive il lavoro offline del
builder, mentre la prova fisica è attestata dal resoconto separato.

## Artefatto e protocollo

| Elemento | Valore |
|---|---|
| Manifest SHA256 | `a2528e6019de515b9d06055127e93cfc01a3e6d6773fbbee4179e83290feed07` |
| Builder SHA256 | `d5081295beb2785904088e2b08056c746321b1ff2c4fbff44ebac13389fec6c6` |
| Dispatcher alla prova SHA256 | `1d512173776f5f87424e7870731df2871cdf1f9293636765a6371c7bb44191e8` |
| Slot eseguito | `0x01C20000`, estensione massima 32 KiB |
| Build tag | `0xE539470B` |
| Immagine / RAM propria | 2.160 / 3.304 byte; stato privato 628 byte |
| Payload eseguito SHA256 | `ae427be74db2b12e2170713e6600f19d3c8b8ab1f396040d48fadd687caff403` |
| ELF SHA256 | `339d715b6597402d165d3e2e5bf04ebe385e7dfff7fe12f80004ea75d5462cd7` |

La ROM fornisce le callback `send`, `receive` e il puntatore allo slot del
gestore. HYRX inizializza esplicitamente lo stato privato, registra il gestore
e ritorna. Entry e handshake non chiamano `receive`. Le callback usano lo
stack ROM entrante: i frame generati esaminati arrivano a 68 byte per
dispatcher più helper, escludendo il consumo interno della ROM. Non è una
misura della capacità dello stack né un limite completo della catena.

Il [contratto C](../firmware/mini/rom_receive/rom_receive.h) e il
[README del componente](../firmware/mini/rom_receive/README.md) descrivono i
campi esatti. `FC82` identifica HYRX; `FC83` associa sequenza, lunghezza,
nonce, CRC e seed; un solo `FB84` trasferisce i dati OUT; `FD85` restituisce
un record LE da 512 byte. Il record termina con CRC32 a offset 504 e `DONE`
a 508. Il nonce previene invii accidentali, non autentica il comando.
Il client consuma l'autorizzazione prima dell'OUT e non ritenta una
transazione ambigua. Il componente non contiene accesso SPI, GPIO o NOR.

## Osservazione fisica

La lettura FD07 dei 2.160 byte caricati coincide con il payload dell'ELF,
dopo la trasformazione USB originale riavviata per ogni comando. Questa
corrispondenza è stata ricontrollata offline sul trace, senza ricompilare.

Il singolo OUT del `2026-11-15T19:45:27.556347Z` usa sequenza 1,
nonce `0x1234ABCD`, seed `0x55` e CRC atteso `0xA14F7A5A`. Il payload è il
complemento bit per bit del pattern iniziale; SHA256
`10d2653bf84c5e82647589c1efb0111ea72918d3a6fd1fcd6c9fe4d0feb0081e`.

| Record | SHA256 |
|---|---|
| Campione 1 | `ae29db1045ffcfd9693a495b0f983539438f76909662cf4dc0a8469e299127de` |
| Campione 2 | `8a544e62f4862be688b2e8a5b8be49f6fc4b45727e278894a60f068d4e51e216` |

Entrambi attestano una chiamata alla callback, stato `RETURNED`, errore 0,
dati attesi e guard integri. Differiscono soltanto nel contatore campioni
a offset 92 e nel CRC finale. Il conteggio di 260 byte diversi dal pattern
iniziale è una misura dei dati, distinta dal ritorno grezzo 260. Due campioni
stabili non provano sincronicità della callback o coerenza DMA/cache generale.

| Puntatore registrato | Valore osservato |
|---|---|
| `send` | `0x01E008E4` |
| `receive` | `0x01E0089A` |
| `handler_slot` | `0x01C01264` |

Sono nuovi valori osservati in questa sessione fisica, non una mappa ROM
presunta. Il probe non legge né disassembla la memoria puntata. I valori
troncati dei test host nel manifest non rappresentano indirizzi della ROM.

## Reset e ritorno allo stock

La ricezione era già riuscita quando è stato caricato e riletto nello slot B
`0x01C28000` il reset separato da 26 byte, SHA256
`cf3526d914eef007649f88f1f22e085a908359b9ad0e9f4743427b4757c0540f`.
Il suo unico salto ha prodotto un errore di trasporto 121. Il run originale
termina con `stock_return_verified: false` e rimane immutato: la risposta
al salto non dimostra il completamento del reset.

Il successivo riavvio dell'hub è registrato separatamente. Il helper fissato
può eseguirlo soltanto dopo aver trovato il problema USB 43 su un dispositivo
figlio di quell'hub; questo è il supporto documentale per il codice 43,
senza presumere un ulteriore snapshot PnP. Non è stato ritentato né il reset
del pedale né l'OUT HYRX.

Solo il resoconto `mini-receive-stock-return.json`, completato alle
`2026-11-15T19:51:35.367773Z`, attesta il ritorno a `TANK MINI_009` e due
letture uguali dei preset: 1.942 byte, SHA256
`c6216783618016998488515ecf4272a78ace8e82ca22e3a27a42bc2d76100427`,
invariato rispetto al backup. È il sesto ritorno allo stock verificato;
questo episodio comprende il riavvio dell'hub. Non prova il recupero da
flash corrotta né un reset autonomo sempre funzionante.

## Verifiche offline

Il manifest già fissato attesta 291 casi C con ASan/UBSan, inclusi tutti i
260 prefissi parziali da 0 a 259 byte, ritorni differenti, guard corrotti,
scritture tardive e comandi malformati. Questi test non sono stati
ricompilati durante la sigillatura. La nuova verifica ha controllato
14 file fissati da hash, il layout ELF, il payload riletto dal trace,
entrambi i record e 19 coppie comando/esito; nessun accesso al dispositivo.

Per ricontrollare i record inclusi nel report, dalla radice del repository
si può eseguire questo codice Python. Non chiama il builder né richiede
i log privati in `analysis/hardware`:

```python
import hashlib
import json
from pathlib import Path

report = json.loads(Path("research/mini-receive-hardware.json").read_text(encoding="utf-8"))
builder = Path("tools/build_mini_rom_receive.py")
expected = report["execution_pins"][builder.as_posix()]
assert hashlib.sha256(builder.read_bytes()).hexdigest() == expected
from tools.build_mini_rom_receive import validate_record

request = report["diagnostic_payload"]
for sample in report["records"]:
    checked = validate_record(
        bytes.fromhex(sample["record_hex"]),
        base=report["target_artifact"]["base"], build_tag=report["build_tag"],
        sequence=1, nonce=request["nonce"],
        payload=bytes.fromhex(request["hex"]), seed=request["seed"],
    )
    assert checked["record_sha256"] == sample["record_sha256"]
    assert checked["observed_complete_and_stable"]
    assert checked["raw_return"] == 260
```

La prova non abilita scritture NOR, non installa firmware e non convalida
avvio applicativo o audio. Un callback ROM bloccato resta non interrompibile
da HYRX; i casi di errore e le altre lunghezze non sono qualificati sul pedale.
