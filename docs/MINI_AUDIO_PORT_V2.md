# Shim audio MINI v2

La v2 conserva la preparazione PC5 osservata nel MINI e prosegue dopo un NACK
di un singolo record, come il caller originale. Il codice, il payload e il
manifest v1 restano invariati. Questa revisione non cambia i 22 record del
codec, OSR, ALNK o la configurazione nominale a 48000; non attesta ACK, audio
fisico o avvio completo di HyperRig sul MINI.

Sorgenti: [audio_port_v2](../firmware/mini/audio_port_v2/).
Build e audit offline:

```powershell
python -B -X utf8 firmware/mini/audio_port_v2/verify.py
```

Il risultato e le preimage sono in
[mini-audio-port-v2.json](../research/mini-audio-port-v2.json) e
`build/mini-audio-port-v2/manifest.json`. Il payload XIP contiene 2332 byte,
occupa `[0x02076AAC, 0x020773C8)` e non aggiunge BSS. SHA256:
`cd0d973b76f31afdb20bf591dedbf50b82984ee75fb615e38ce9829957530791`.
Espone gli stessi simboli e i due hook del manifest v1; la guardia di recupero
va rilinkata alla fine effettiva del nuovo append. Questa build non modifica
la candidata integrata o gli artefatti già eseguiti sul pedale.

La preparazione PC5 precede getter del clock, PA9 e bus codec. Il frammento
MINI `[0x02005BCE, 0x02005C62)` è verificato per hash e istruzioni:

| Operazione sul solo bit5 | Binding G usato |
|---|---|
| DIE = 1 | `0x0200187C(37, 1)` |
| OUT = 1, poi DIR = 0 | `0x02004998(37, 1)` |
| HD = 0 | nuova funzione ASM con lock originale G |
| HD0 = 0 | `0x0201B1B6(37)`, un solo argomento |

HD0 e HD sono registri diversi. Non è stato identificato un helper HD
equivalente nell'audit G; `0x0201E09A` modifica DIEH e non viene usato.
La funzione ASM HD modifica solo `0x5009C` bit5, tra le chiamate alla sezione
critica G `0x01C00E2E` / `0x01C00E46` e sotto il byte lock PORTC
`0x01C25CE2`, acquisito con `testset`. Conserva r4 e RETS e usa 8 byte di
stack. Gli helper restanti acquisiscono autonomamente il medesimo lock:
non viene aggiunto un lock esterno che li farebbe attendere indefinitamente.
PU, PD, DIEH e i bit degli altri pin restano invariati.

Queste funzioni richiedono il runtime G e la sua inizializzazione dei lock;
non sono servizi chiamabili dal plugin ROM. Ereditano l'attesa del lock
originale, senza introdurre una garanzia di terminazione non dimostrata.
PC5 non è identificato come alimentazione audio: il suo scopo elettrico
rimane sconosciuto. Il riferimento completo è
[MINI_CODEC_AVAILABILITY.md](MINI_CODEC_AVAILABILITY.md).

La gestione dei NACK deriva dai byte MINI: `0x02006DCE` interrompe il record
al primo byte non riconosciuto; il ciclo a `0x02006DEC` avanza comunque di
quattro byte e tenta tutti i 22 record. Il caller a `0x02007188` prosegue
senza controllare il risultato. La v2 chiama separatamente
`hyperrig_mini_codec_stock_record()` e `hyperrig_mini_codec_write()` e
continua soltanto se il risultato è NACK, STOP è stato tentato, la pulizia
ha restituito zero e il bus resta inizializzato. Errori di clock, timing,
campionamento o pulizia restano fatali e impediscono il successivo avvio G.

Il risultato distingue record tentati, record interamente riconosciuti,
NACK, prosecuzioni dopo NACK e singoli byte riconosciuti. Un ritorno zero
significa che la policy consente di proseguire; non certifica alcun ACK.
Il binding target non conserva questi contatori globalmente e non aggiunge
stato permanente al firmware.

Rimane una differenza esplicita: il writer originale non emette STOP quando
un record riceve NACK; il nostro writer tenta sempre STOP. In entrambi i
casi il record successivo inizia con START e byte indirizzo `0x36`, seguito
dagli stessi dati. I test verificano questa sequenza, ma il nuovo STOP
cambia il confine della transazione fallita: equivalenza elettrica e stato
del dispositivo dopo quella transazione non sono dimostrati.

L'audit dei latch P33 separa l'avvio applicativo dal contesto ROM. Lo SPL
MINI del backup fisico azzera D0..DF e AD/AE/AF a
`[0x01C040CE, 0x01C04142)`, prima del cambio clock e della chiamata all'app
a `0x01C0528C`. L'app G conserva un rilascio equivalente nel normale
percorso `0x020011CE -> 0x02000EE0`, tramite il writer RAM `0x01C00F0C`.
Anche l'app stock MINI contiene i 19 azzeramenti. Il significato dei
registri è corroborato da
[SPEC §3.1 del riferimento fissato](../upstream/m-bootloader/docs/SPEC.md).

Il verificatore confronta i byte della candidata integrata presenti al
momento dell'audit con G per funzione, caller e copia RAM del writer: sono
invariati. Lo SPL è esterno all'area app sostituita. Il percorso ROM dei
probe non attraversa quei due startup, ma non è stato osservato lo stato
effettivo dei latch: questa differenza non prova la causa dei NACK HYC3.
La v2 non aggiunge scritture P33. Il report conserva separatamente l'hash
della candidata controllata; l'integratore dovrà ricontrollare questi
intervalli quando genera la candidata successiva.

Verifiche completate: host ASan/UBSan su tutti i 110 punti NACK singoli,
tutti i 22 address-NACK consecutivi, successo completo e 35 errori di
timing/pulizia; 640 configurazioni/risultati per l'ordine PC5 e i bit estranei;
576 casi sull'ASM HD realmente linkato con lock libero/occupato e diverse
profondità della sezione critica; 42 percorsi degli hook, confrontati con
il disassemblatore vendor. Il wrapper compilato verifica ordine, argomenti
e conservazione di RETS. Le API hardware simulate nei test non costituiscono
una prova di GPIO, lock multicore, clock o audio sul dispositivo.
