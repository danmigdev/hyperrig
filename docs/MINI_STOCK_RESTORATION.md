# Ripristino esplicito della sola app stock MINI

[restore_mini_stock.py](../tools/restore_mini_stock.py) prepara e riusa il
writer limitato per il verso HyperRig/app incompleta→app stock. L'intervallo
scrivibile rimane esclusivamente `[0x4000,0x82000)`. Non riavvia il pedale,
non ripete comandi ambigui e non ripristina automaticamente altre partizioni.
Import e CLI fanno soltanto operazioni su file locali.

La destinazione è l'app estratta dal backup completo di questa unità,
SHA256 `72db5e70b301e7b88ab5d22c2def1ec869fd5fd84b86c032abd01e38b5f8a180`.
SHA256 dell'app stock:
`11ade0ace13c48d1b633669ee8beae71d98a269690f1ffb93eb2c6ce14922eda`.
La preimage è una nuova lettura completa della NOR, fornita come file locale
e SHA256 atteso esplicito. Il chiamante deve provarne origine hardware e
recenza; il planner non le deduce dal nome o dalla data del file.

SPL/configurazione e key_mac devono coincidere con il backup fissato.
Un'app con header o codice corrotti è accettata: richiederne un CRC valido
impedirebbe il recupero. VM, OTA, BTIF e USR possono differire; il piano ne
elenca hash, numero di byte diversi e settori interessati, poi conserva
esattamente i byte della lettura corrente. Non equivale a riportare la NOR
intera o i preset allo stato del backup storico.

La factory verifica prima gli artefatti operativi tramite
`prepare_installation()`, poi crea una `Installation` immutabile con
`purpose='restore-stock'`, preimage corrente e destinazione stock. Il piano
canonico ha un hash indipendente dal piano stock→HyperRig e può essere
conservato con scrittura esclusiva, flush e fsync. Nessun file esistente
viene sovrascritto da `retain_plan()`.

API per un runner esplicitamente autorizzato e revisionato:

```python
from tools.restore_mini_stock import (
    prepare_stock_restoration, MiniStockRestorationSession,
    validate_restored_full,
)

prepared = prepare_stock_restoration(
    retained_fresh_full_dump_path,
    expected_sha256=accepted_fresh_full_sha256,
    slot=known_inactive_slot,
)
prepared.retain_plan(new_plan_path)

# transport, ROM entry, slot history and durable journal belong to the runner.
session = MiniStockRestorationSession(
    transport, prepared, journal=durable_journal, known_free_slot=True,
)
session.upload_and_start(
    prepared.installation.image,
    expected_sha256=prepared.installation.image_sha256,
)
session.initialize_spi()
session.verify_complete_preimage()
result = session.restore_application()  # leaves ROM active

# A separate read-only lifecycle acquires all 1MiB after the writer finishes.
validation = validate_restored_full(prepared, independently_read_full_nor)
```

Il client verifica l'intera app prima della prima mutazione, nuovamente il settore
prima di armarlo, la pagina congelata tramite echo, erase, ogni PP, settore e
app completa. Il settore header va per ultimo e la sua pagina `0x4000`
segue `0x4100..0x4F00`. Non si invalida l'header all'inizio. Una perdita di
alimentazione può ancora lasciare codice misto: l'ordine non è atomico e il
fallback OTA MINI non è qualificato. Un errore termina la sessione senza
reset o tentativi automatici.

`restore_application()` attesta soltanto il readback dell'app stock e lascia
non verificate le regioni esterne. `validate_restored_full()` controlla
successivamente app stock più tutte le regioni esterne contro la preimage
fresca e distingue l'eventuale uguaglianza con l'intero backup storico.
L'avvio stock e l'identità/preset osservati restano prove hardware separate.

Verifica locale:

```powershell
python -B -X utf8 -m unittest tests.test_restore_mini_stock -v
python -B -X utf8 tools/restore_mini_stock.py
```

16 test passati: app illeggibile o totalmente sconosciuta, estremi della
partizione, dati esterni diversi, rifiuto di SPL/key_mac estranei,
immutabilità della preimage, log durevole, header-page-last, perdita di
risposta erase/program, mancata preimage e verifica finale indipendente.
Il test di trasferimento usa esclusivamente NOR simulata. La factory è stata
anche verificata sui veri artefatti locali, usando il backup storico come
fixture senza differenze; ciò non è una lettura hardware recente.

Sorgente congelato SHA256
`aca0b65237210b5cd30a9363e66d72cc22dc5f77c0cb0ef8ddceed0653f22324`;
test SHA256
`93880e8fcc758f4d56cd6b27734c92e9741454a700f198c72a6908b2b45e46a6`.
Il [report dedicato](../research/mini-stock-restoration.json) distingue
queste verifiche dall'esecuzione fisica del ripristino, non effettuata.
