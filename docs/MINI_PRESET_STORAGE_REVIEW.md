# Persistenza dei preset G adattati al MINI

Review statica della candidata audio v2, eseguita il 15 novembre 2026.
I percorsi `PSAVE`, `SNAPSAVE` e `PDEL` esaminati usano il journal dei
preset nell'area USR, con indirizzi ammessi dal controllo NOR originale G.
Non è stato trovato un disallineamento di geometria che indirizzi questi
tre comandi verso OTA, BTIF o il settore finale dei dati unitari.

La riduzione della VM da 64 a 16 KiB non costituisce, da sola, questa
prova. Esiste anche un ramo di migrazione dopo aggiornamento, condizionato
dal tipo di avvio `0x5A02`. Sono state verificate sia tale condizione sia
le protezioni dei suoi helper finali. Il primo backend syscfg è inoltre
basato su BTIF: non va descritto come una semplice cache RAM.

Questa review non esegue codice sul pedale. Al suo completamento non c'è
ancora un avvio G né un salvataggio fisico HyperRig verificato. Il
[resoconto del primo tentativo](../analysis/hardware/mini-first-install-run.json)
riporta `RomCommandError`, `installed_image_verified=false`,
`full_NOR_verified=false` e `automatic_reset=false`. Le prove precedenti
dei plugin ROM non sostituiscono la prova della persistenza nell'app G.

## Immagine e fonti esaminate

| Input | SHA256 |
|---|---|
| `build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin` | `3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff` |
| `artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin` | `2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059` |
| Area G decodificata | `2694429beca4065ce2eb66f052a9e3c1dd71a0ec8c89865783aa1a1ffcd2b334` |
| Backup completo `artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin` | `72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180` |

Le istruzioni provengono da
[flash.asm G](../analysis/firmware/m571_g_app/flash.asm), confrontate con
i byte originali e quelli della candidata, non dalla sola ricerca di
costanti in una disassemblazione lineare. La geometria è quella realmente
decodificata dalla directory JLFS della candidata. La patch è `VM_PATCH`
in [audit_mini_ultrarig_port.py](../tools/audit_mini_ultrarig_port.py).
Gli offset nella tabella seguente sono indirizzi fisici NOR; gli indirizzi
`0x020xxxxx` citati nel testo sono invece indirizzi CPU dell'applicazione.
Tutti gli intervalli sono semiaperti: l'estremo finale è escluso.

| Oggetto | Intervallo fisico |
|---|---|
| Descrittore JLFS VM MINI | `[0x82000,0xBE000)` |
| Due banchi VM dopo il clamp | `[0x82000,0x84000)`, `[0x84000,0x86000)` |
| Area OTA da conservare, inclusi metadata | `[0xB7000,0xBD000)` |
| BTIF MINI | `[0xBE000,0xBF000)` |
| USR MINI | `[0xBF000,0xFF000)` |
| Settore finale dei dati unitari | `[0xFF000,0x100000)` |
| Settori utilizzabili dal journal preset | `[0xBF000,0xCF000)`, `[0xDD000,0xDF000)` |

Il descrittore VM resta deliberatamente più grande della VM effettiva:
comprende l'area in cui lo stock conserva l'updater. Non va interpretato
come un'autorizzazione a usare l'intero intervallo per i record runtime.

## Percorsi dei tre comandi

| Comando | Catena G rilevante |
|---|---|
| `PSAVE` | Dispatcher `0x0200B834`, ramo `0x0200BA86`, chiamata a `0x020077EC` da `0x0200BAC0` |
| `SNAPSAVE` | Ramo `0x0200BB78`; cattura scena RAM `0x0200A256`; con preset corrente valido, `0x0200A312` chiama `0x020077EC` da `0x0200A36C` |
| `PDEL` | Ramo `0x0200C06E`; chiamata a `0x020077EC` da `0x0200C084` con record vuoto |

`PSAVE` e `PDEL` accettano indici preset 0..31. `SNAPSAVE` accetta
indici scena 0..3; la persistenza usa il preset corrente, nuovamente
validato nell'intervallo 0..31 da `0x0200A312`. Una scena catturata soltanto
in RAM, senza preset corrente valido, non dimostra un salvataggio NOR.

Il writer comune `0x020077EC` conserva anche il preset vicino nella stessa
coppia e chiama `0x02003040` da `0x02007936`. Quest'ultimo valida l'indice
della coppia 0..15 e due lunghezze non superiori a 1920 byte. La rotazione
usa 18 settori fisici. Il mapper `0x020026BA` restituisce:

```text
indice 0..15: 0xBF000 + indice * 0x1000
indice 16:    0xDD000
indice 17:    0xDE000
```

Il resolver `0x0200777A` aggiunge alla base 0 oppure `0x800` per le due
metà del settore. I metadata arrivano fino al marker a settore+4092,
restando entro i 4096 byte. La scansione di avvio `0x020031D4` percorre
gli stessi 18 settori; rifiuta gli identificatori di coppia maggiori di 15
a `0x020032A2`. Le dimensioni G residue in questo journal coincidono
quindi con USR del MINI, senza passare per il descrittore VM.

Il writer può ruotare e riscrivere un settore contenente anche il preset
vicino. La prova applicativa deve quindi confrontare il contenuto logico
conservato, non presumere che cambi soltanto la pagina dello slot scelto.

## Controlli finali di erase e program

L'erase USR `0x02002D9E` richiede base almeno `0xBF000`, allineamento
4096 e fine non superiore a `0xFF000`. Il program USR `0x02002F16`
controlla base e fine nello stesso intervallo e suddivide la scrittura
secondo il limite delle pagine da 256 byte.

Un secondo controllo, già presente nel G originale e non introdotto dal
port, è `0x02002994`. Per i valori limitati dei percorsi esaminati ammette:

```c
base >= 0xBF000 && length <= 0x40000 && base + length <= 0xFF000
```

Il wrapper erase `0x02002B80` lo invoca con 4096 byte per opcode 200,
65536 per opcode 201 e 256 per opcode 204. Il wrapper program
`0x02002EF2` lo invoca prima del callee NOR `0x02002E6A`. Un rifiuto
registra l'indirizzo tramite `0x020029B0` e restituisce `-1`.

Questo dimostra il confine per le chiamate ricostruite, con basi e
lunghezze valide e senza overflow. Non è una verifica formale di puntatori
arbitrari, di ogni entrypoint NOR o di tutti gli aggiornatori del firmware.
I callee più bassi esistono ancora: il controllo va seguito nella catena
effettiva, non attribuito indistintamente a qualunque operazione flash.

## VM: geometria e limiti della persistenza

`0x020221E4` cerca il nome JLFS `vm` e ricava la base dalla directory;
non conserva la base G precedente come costante. Nell'init `0x02020664`,
la patch a `0x0202067E` cambia il clamp da `0x10000` a `0x4000`:

```text
prima: 20 e9 80 0b 60 e0 80 0b
dopo:  20 e9 80 0c 60 e0 80 0c
```

Nel ramo NOR, `0x02020732..0x02020742` produce due descrittori da
`0x2000` byte, alle basi `0x82000` e `0x84000`. Il writer
`0x02020A5A` controlla offset e spazio residuo del banco, mentre
`0x02020376` ricava il numero di erase dalla sua dimensione. La
geometria non invade OTA, BTIF o dati unitari.

C'è però una distinzione ulteriore: questi helper VM usano
`0x020201A2` per erase e `0x020201CE` per program, che raggiungono
rispettivamente `0x02002B80` e `0x02002EF2`. Le basi VM sono sotto
`0xBF000`, quindi il controllo originale G rifiuta tali richieste.
`0x020201A2` ignora l'esito dell'ioctl e ritorna 1; anche il percorso
`0x02020A5A` può avanzare lo stato RAM senza propagare l'errore dei
program a `0x02020BBE/0x02020BCE`. Non si deve pertanto promuovere
un esito syscfg positivo a prova di persistenza VM. Questo comportamento
era già nel G esaminato; i tre comandi preset usano il journal USR
separato e indirizzi ammessi. La review non propone un nuovo blocco.

## Ramo OTA e tipo di avvio della nostra sequenza

L'init VM chiama `0x02020210` da `0x0202074E`. Il primo controllo,
`0x02020100`, restituisce vero esclusivamente quando
`h[0x01C21CB4] == 0x5A02`; in caso contrario si ritorna a
`0x02020350` prima di scandire i record OTA.

Se il tipo è `0x5A02`, il codice cerca un record valido nell'estensione
JLFS VM, oppure a ritroso nella flash; verifica il tipo, il marker
`0x5441`, l'header CRC e il nome `LOADER.BIN`. Il backup contiene il
loader a `0xB7000` e il record di 80 byte a `0xBCF00`, documentati in
[MINI_BOOT_CONTRACT.md](MINI_BOOT_CONTRACT.md). In quel percorso sono
calcolate richieste di copia verso la VM, erase del loader a
`0x0202033E` e riscrittura del record a `0x0202034C`.

Sono **richieste**, non una prova di modifiche riuscite: entrambi gli
helper finali passano il controllo `0x02002994`. Gli indirizzi VM,
`0xB7000` e `0xBCF00` sono inferiori a `0xBF000` e vengono rifiutati.
Il solo clamp non avrebbe escluso il calcolo di questi indirizzi; la
catena completa esclude le scritture tramite gli helper esaminati.
Non è stata qualificata una migrazione OTA funzionante del G adattato.

Il parser d'avvio G `0x020017F6`, chiamato dall'entry a `0x02000216`,
calcola il CRC su 78 byte a `0x01C7FD8A`. Se il CRC è non nullo e
corrisponde all'halfword a `0x01C7FD88`, carica il tipo da
`0x01C7FD8C`; altrimenti usa `0x5A00`. Dopo aver salvato il tipo a
`0x01C21CB4`, azzera 80 byte `[0x01C7FD88,0x01C7FDD8)`.

La nostra sequenza software di ingresso ROM usa il marker di 16 byte
`usb_update_mode\0` a `0x01C7FD80`. È presente nella routine stock
MINI `0x01C02362..0x01C02372` e riprodotto in
[entry_recovery/reset.S](../firmware/mini/entry_recovery/reset.S).
Il plugin di ritorno [rom_reset/startup.S](../firmware/mini/rom_reset/startup.S)
azzera **solo la prima word**, non tutti i 16 byte. L'halfword a
`0x01C7FD8C` rimane dunque `0x646F`. Per questo marker, qualunque sia
l'esito del CRC della coda, il parser restituisce `0x5A00` oppure
`0x646F`, mai `0x5A02`.

L'esclusione riguarda il marker scritto dalla sequenza nota, mantenuto
fino all'entry normale. Non è una lettura fisica recente della retention
né una proprietà di ogni reset. Lo SPL copia gli 80 byte a RAM e azzera
`h[0x01C7FD82]` nei frammenti `0x01C04DEC` e `0x01C04E66`; ciò
non equivale ad azzerare il tipo a `0x01C7FD8C`. Un aggiornamento vero
può scrivere `0x5A02`: lo stock MINI lo fa a `0x0206DA62..0x0206DA78`.
Questa review non generalizza la sequenza a cold boot, updater interposto
o applicazione parziale che prenda un diverso ramo SPL.

## BTIF: controllo del formato, non promessa di immutabilità

La tabella syscfg a `0x020558F4` ha come primo backend l'init
`0x0201FEA4`, il reader `0x0201FF2A` e il writer `0x0201FFD2`.
`0x0201FD6C` apre per nome `mnt/sdfile/app/btif`, stringa a
`0x0203660C`. La tabella a `0x02033B40` contiene ID102/104/110/111,
ciascuno con payload di 6 byte. Il backend verifica lunghezza e CRC
low8; non è una cache soltanto volatile.

Sul backup fissato, senza pubblicare i valori dei payload:

| Record | Offset | Risultato del controllo G |
|---|---:|---|
| ID102 | `0xBE000` | ID e lunghezza corretti, CRC low8 valido |
| ID104 | `0xBE00A` | Header vuoto `0xFFFFFFFF` |
| ID110 | `0xBE014` | Header vuoto `0xFFFFFFFF` |
| ID111 | `0xBE01E` | Header vuoto `0xFFFFFFFF` |

L'init salta la riparazione per record validi o vuoti. Nessuno dei quattro
attiva quindi il ramo di repair `0x0201FEE4..0x0201FF04` sul backup
esaminato. Quel ramo tenta un erase attraverso `0x0201FE92` e
`0x02002B80`, anch'esso soggetto al controllo di indirizzo già descritto.
Il terzo backend, che legge cfg_tool e la tabella BTIF+512, ha invece
puntatore di scrittura nullo nella tabella; la lunghezza zero del fallback
BTIF+512 del backup viene rifiutata a `0x0201FB26`.

Non è stato trovato un mismatch di formato che renda necessaria una
cancellazione BTIF all'avvio della candidata con questi dati. Il normale
uso runtime dei propri record di configurazione o bonding va distinto
da una scrittura indebita in un'altra partizione. `preserved_regions`
del piano installer attesta la conservazione durante l'installazione,
prima dell'app boot; non promette che ogni dato runtime resti immutabile
per tutta la vita dell'applicazione.

## Verifica ripetibile senza build o hardware

Sono stati confrontati 25 frammenti, inclusi dispatcher, journal, guard,
VM, parser d'avvio e tabelle. Tutti corrispondono al G originale, con la
sola sostituzione prevista della costante VM in questi intervalli.
Sono stati inoltre verificati gli header/CRC JLFS, i quattro record
BTIF, 18 settori preset ammessi e sei richieste fuori area rifiutate
dal modello aritmetico dei limiti. Il modello non è un'esecuzione ISA.

Il seguente comando PowerShell ripete i confronti; legge soltanto gli
artefatti locali già dichiarati e non mostra payload unitari:

```powershell
@'
from pathlib import Path
import hashlib, struct
from hyperrig.jieli import crc16, unpack_app
from tools.audit_mini_ultrarig_port import VM_PATCH

def load(path, digest):
    data = Path(path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, path
    return data

image = load('build/hyperrig-mini-audio-v2/hyperrig-mini.app-area.bin',
    '3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff')
original = load('artifacts/alpha11/v2/UltraRig-alpha11-v2-win/m571_g_app.bin',
    '2a314010a4ccf90daa62a9797588218634e2c2957e9fe908875665c828897059')
backup = load('artifacts/my-mini-flash/20261115-paced-resume/flash-a.bin',
    '72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180')
candidate, entries, _ = unpack_app(image)
expected, _, _ = unpack_app(original)
expected = bytearray(expected)
at = VM_PATCH.address - 0x02000000
assert expected[at:at+8] == VM_PATCH.before
expected[at:at+8] = VM_PATCH.after
spans = [(0x026BA,0x026D6),(0x02D9E,0x02E08),(0x02F16,0x02FF6),
 (0x03040,0x031BE),(0x031D4,0x03388),(0x0777A,0x07966),
 (0x0A312,0x0A37E),(0x0B834,0x0C28C),(0x20100,0x20354),
 (0x20376,0x20450),(0x20664,0x20750),(0x20A5A,0x20C50),
 (0x221E4,0x2225E),(0x017F6,0x0182E),(0x01776,0x017F6),
 (0x02994,0x029B0),(0x02B80,0x02BCC),(0x1FAAA,0x1FB6C),
 (0x1FD6C,0x200EA),(0x33B40,0x33B54),(0x3660C,0x3661E),
 (0x558F4,0x55948),(0x02EF2,0x02F16),(0x1F2BA,0x1F2DA),
 (0x35F74,0x35F8C)]
for begin, end in spans:
    assert candidate[begin:end] == expected[begin:end], hex(begin)
geometry = {e.name:(e.offset,e.size) for e in entries
            if e.name in ('VM','BTIF','USR')}
assert geometry == {'VM':(0x82000,0x3C000),'BTIF':(0xBE000,0x1000),
                    'USR':(0xBF000,0x40000)}
for i, record_id in enumerate((102,104,110,111)):
    at = 0xBE000 + 10*i
    header = struct.unpack_from('<I', backup, at)[0]
    assert header == 0xFFFFFFFF or (header >> 20 == 6 and
        ((header >> 8) & 4095) == record_id and
        (crc16(backup[at+4:at+10]) & 255) == (header & 255))
def permitted(base, length):
    return base >= 0xBF000 and length <= 0x40000 and base+length <= 0xFF000
sectors = [0xBF000+i*4096 for i in range(16)] + [0xDD000,0xDE000]
assert all(permitted(base,4096) for base in sectors)
for base, length in [(0x82000,4096),(0x84000,4096),(0xB7000,4096),
                     (0xBCF00,80),(0xBE000,4096),(0xFF000,1)]:
    assert not permitted(base,length)
assert int.from_bytes(b'usb_update_mode\0'[12:14],'little') == 0x646F
print('PASS: 25 frammenti, geometria, BTIF, limiti e marker; solo offline')
'@ | python -B -X utf8 -
```

Gli indirizzi validi, il successo di un comando e la persistenza dopo
reload sono prove diverse. Il ciclo applicativo preparato in
[MINI_APP_MUTATION.md](MINI_APP_MUTATION.md) dovrà ancora verificare
salvataggio, ricaricamento, scene e ripristino sul firmware G avviato.
Nessun risultato di questa review abilita da solo una capacità USB o BLE.
