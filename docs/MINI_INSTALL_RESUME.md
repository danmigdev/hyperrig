# Nuovo piano dalla NOR parzialmente programmata

[resume_mini_install.py](../tools/resume_mini_install.py) prepara un nuovo
piano immutabile dalla lettura completa corrente e dalla stessa candidata
HyperRig gia revisionata. Non accede al pedale, non ripete comandi della
sessione precedente e non esegue installazioni dalla CLI.

Il primo tentativo ha confermato erase e dieci page-program nel settore
`0x5000`. La successiva lettura host `FD7F` di 256 byte a `0x5900` ha
restituito Windows 31 dopo circa 0,51 ms. Una nuova interrogazione esplicita
ha trovato audit identico: sequenza 22, bitmap `0x3FF`, `read_bytes=544000`,
errore target zero. La lettura fallita non aveva incrementato il contatore
del core. Questo non autorizza a ripeterla automaticamente e non sostituisce
una nuova acquisizione della NOR.

La lettura completa separata e stata conservata in
`artifacts/my-mini-flash/first-install/full-partial.bin`:

- 1.048.576 byte, SHA256
  `6072644bf91df5a5f310011835f20f534c9004399fa019ac0db2241ffeea8c87`;
- `[0x5000,0x5A00)` coincide con le prime dieci pagine della candidata;
- `[0x5A00,0x6000)` contiene soltanto `FF`;
- ogni byte esterno al settore `0x5000` coincide con il backup stock fissato.

Il confronto e stato ripetuto offline sui file effettivamente acquisiti.
Il log fisico separato e
`analysis/hardware/mini-partial-inspect-run.json`, terminato il
2026-11-15 alle 20:54:31 UTC con reader B attivo e nessun reset.
Il planner da solo non attesta origine hardware o recenza di un file.

```python
from tools.resume_mini_install import prepare_resume, validate_completed_full

prepared = prepare_resume(
    retained_full_read_path,
    expected_partial_sha256=explicitly_reviewed_hash,
    expected_modified_sectors=(0x5000,),
    slot=0x1C20000,
)
# prepared.installation is a NEW frozen Installation for the bounded client.
# The authorized runner owns slot history, transport and durable journal.
# No old token, sequence number or bitmap is passed to the new client.
```

La factory rifiuta hash, dimensioni o insieme di settori diversi da quelli
esplicitamente accettati. Rifiuta anche qualsiasi differenza esterna
all'app rispetto al backup: SPL/configurazione, VM compresa OTA, BTIF, USR
e key_mac. Accetta solo la candidata app SHA256
`3b0eac3bd14726ed77618d11a10eef2ef8da66563e02e87bf25f4377500a78ff`.
La preimage incompleta non deve essere avviabile o superare il parser app.

Il piano reale conservato in `build/mini-install-resume/resume-plan.json`
ha SHA256
`06d52f30f00cdedd63f4f0e9356b2dd1d6e536841370d976dcf987775d4a3601`.
Contiene 126 settori da portare alla candidata, `0x5000` per primo e
`0x4000` per ultimo. Il CRC32 corrente del settore `0x5000` e `0x0A53DF86`.
Il client verifica l'intera app corrente prima delle mutazioni; quindi
verifica di nuovo ciascun settore, lo cancella e programma tutte le sue
16 pagine. Non prosegue direttamente dalla vecchia pagina `0x5A00`.
La pagina header `0x4000` resta ultima dopo `0x4100..0x4F00`.

La NOR completa attesa dopo una conclusione verificata ha SHA256
`a35868ab3a4beb42454070ce46d67efaf695615a670de177343860e88d107c47`.
`validate_completed_full()` richiede app esatta e regioni esterne identiche
alla lettura precedente. Questa verifica non attesta avvio, audio o
recupero a footswitch. Una perdita di alimentazione durante la scrittura
puo ancora lasciare un'immagine mista; il processo non e atomico.

Il runner separato `analysis/hardware/run_mini_first_resume.py` e stato
revisionato senza eseguirlo: conferma reader B e contatore, carica il nuovo
writer A, verifica la preimage, installa e acquisisce un readback completo
con reader B. Applica una pausa di 20 ms tra comandi; la pausa e una scelta
di prova, non una dimostrazione della causa dell'errore Windows precedente.
Non effettua retry, reset o rollback automatici. Il primo avvio resta una
fase separata, legata all'esito verificato di questo nuovo piano.

Dieci test locali sono passati: hash/settori espliciti, rifiuto di ogni
regione esterna alterata, immutabilita, nuovo erase con CRC corrente,
risposta persa senza retry, completamento simulato, verifica NOR finale e
CLI senza accesso hardware. Le simulazioni non rappresentano esecuzione
fisica. Sorgente congelato SHA256
`4d8b1241440c031e2de35cde8378d9354931aae78406db3a11c4912a1a15cebe`;
test SHA256
`d89fde466816e8d7aea81c5f609dbf47524026bb2185f488b9e9a6a0a8b193c3`.
Il [report locale](../research/mini-install-resume.json) registra la
validazione iniziale; l'esito dell'esecuzione fisica appartiene ai log
del runner e non e anticipato da questo documento.
