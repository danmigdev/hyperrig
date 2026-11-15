# Controllo temporaneo del polling Windows sul MINI

Nei log Windows della terza installazione compaiono richieste autonome
`TEST UNIT READY` al disco ROM `WL82 / UBOOT1.00`, intercalate alle operazioni
dell'installatore. La coincidenza con Win31 non dimostra da sola un conflitto
USB o la causa dell'errore.

[mini_windows_mcn.py](../tools/mini_windows_mcn.py) apre un secondo handle
del solo MINI già identificato, con `FILE_READ_ATTRIBUTES` (0x80), e richiede
`IOCTL_STORAGE_MCN_CONTROL` (0x2D0944). Il parametro è un BOOLEAN da un byte:
1 sospende la rilevazione del cambio supporto, 0 bilancia la sospensione.
L'handle SCSI dell'installatore rimane distinto. Il contesto chiude sempre
l'handle attributi, anche quando il corpo o il logger falliscono; Windows
associa inoltre il ripristino al cleanup del file object. Non cambia registro,
driver, hub, alimentazione o contenuto della NOR.

Questa procedura segue la
[documentazione Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control).
Il sample Microsoft di
[ClassPnP](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/autorun.c)
mostra il controllo del contatore di sospensione prima del polling. Non ne
deriva che ogni richiesta proveniente da altri processi sia soppressa.
Codice e BOOLEAN sono stati confrontati anche con gli header SDK locali
`10.0.19041.0/shared/ntddstor.h` e `um/winioctl.h`.

Sette test simulati coprono accesso esatto, coppia disable/enable,
chiusura idempotente e pulizia dopo errori di apertura, controllo e logger:

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_mcn
```

La prova fisica `analysis/hardware/mini-mcn-probe-run.json` del 15 novembre
2026 ha completato finestre di 16 secondi prima, 24 durante e 16 dopo la
sospensione. Le 239 query di identità durante la sospensione sono riuscite;
stato e contatore del lettore B sono rimasti invariati. Il controllo è stato
esplicitamente riabilitato e l'handle chiuso. Non sono state eseguite
scritture NOR o reset. La riduzione del polling deve essere valutata sui
log Windows relativi alle tre finestre; il successo dell'IOCTL non basta.
