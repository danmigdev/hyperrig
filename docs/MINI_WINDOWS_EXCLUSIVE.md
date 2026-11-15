# Handle Windows con share mode zero

`tools/mini_windows_exclusive.py` espone
`ExclusiveBufferedRomTransport(attestation, slot=..., profile=...)`.
Riusa la selezione immutabile e i controlli CfgMgr di `mini_windows_quiet`,
numero del disco, adapter e INQUIRY; tutte le transazioni ereditano il
buffered SPT congelato. La sola differenza nell'apertura è
`CreateFileW(interface, GENERIC_READ|GENERIC_WRITE, 0, ..., OPEN_EXISTING)`.
Una sharing violation termina il tentativo. Nessun fallback condiviso,
scansione WMI, retry, reset o modifica di servizi/registro/driver.

La documentazione [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
richiede FILE_SHARE_WRITE per volumi e floppy; non formula quel requisito
per un physical disk. Qui viene aperta l'interfaccia disco identificata,
non un volume. Share0 richiede l'esclusione di successive aperture con
accesso dati read/write/delete, ma esenta gli accessi ai soli attributi.
Gli handle dati già esistenti possono far fallire il tentativo. Il modulo
non chiude handle appartenenti ad altri processi.

Non è dimostrato che questo stack raw-device applichi ogni controllo di
sharing. Nel [sample Classpnp Microsoft](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/create.c),
`ClasspCreateClose` prepara il contesto del file e inoltra CREATE al driver
inferiore, senza un controllo ShareAccess nel proprio corpo. È un sample,
non il binario Windows installato. Inoltre l'[esclusività del device object](https://learn.microsoft.com/en-us/windows-hardware/drivers/kernel/specifying-exclusive-access-to-device-objects)
dipende dalla proprietà dell'oggetto nominato e dal suo stack; non viene
aggiunta da questo modulo.

## Prova esplicita della seconda apertura

Il costruttore non esegue una prova di contesa. Il coordinatore può chiamare
separatamente `probe_competing_data_open(transport)`: un solo secondo
CreateFile sulla stessa interfaccia, GENERIC_READ e share READ|WRITE,
senza DeviceIoControl o CDB. La funzione restituisce:

| `data_open_exclusion_result` | Significato osservato |
|---|---|
| `denied32` | Il secondo open è stato negato con ERROR_SHARING_VIOLATION. |
| `not_enforced` | Il secondo open è riuscito ed è stato chiuso subito. |
| `inconclusive` | Errore diverso da32; non prova esclusività. |

Un errore di CloseHandle è propagato; nessun nuovo open/retry viene tentato.
La prova non cambia l'handle principale. Anche CreateFile può generare
attività interna dello stack: l'assenza di CDB espliciti non garantisce
assenza di richieste implicite del driver.

## MCN e polling rimangono distinti

L'handle MCN mantiene FILE_READ_ATTRIBUTES/share3 e il proprio ciclo
disable/enable/close, secondo [IOCTL_STORAGE_MCN_CONTROL](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control).
La sua compatibilità con share0 deriva dall'eccezione per gli attributi;
deve comunque essere osservata sul device. Il nuovo costruttore non lo
crea né lo prende in gestione.

La stessa eccezione impedisce di promettere la scomparsa dei TUR:
[CHECK_VERIFY2](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_check_verify2)
può operare con FILE_READ_ATTRIBUTES. Restano inoltre richieste kernel e
filter driver. Perfino `denied32` qualifica soltanto quella specifica
seconda apertura: `polling_exclusion_proven` resta false.

## Verifica offline

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_exclusive tests.test_mini_windows_quiet tests.test_mini_windows_spt tests.test_mini_windows_mcn
```

72 test PASS, di cui27 sul nuovo modulo. Tutte le API Windows sono mock;
i test verificano share0 esatto, identità/attestation, cleanup, errori senza
fallback, esiti del secondo open, assenza di IOCTL nel probe di contesa e
parametri/cleanup MCN separati. Non sono prove fisiche di esclusione.
Il SDK locale10.0.19041.0 conferma accessi0x80000000/0x40000000,
FILE_READ_ATTRIBUTES0x80 e share1/2; CHECK_VERIFY2 e MCN_CONTROL usano
FILE_ANY_ACCESS. Fonti/hash e limiti sono in
`research/mini-windows-exclusive.json`. Nessuna I/O hardware eseguita.
