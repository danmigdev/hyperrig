# Trasporto Windows SCSI buffered per il ROM MINI

[mini_windows_spt.py](../tools/mini_windows_spt.py) introduce
`WindowsBufferedRomTransport`, alternativa esplicita al trasporto DIRECT.
Importare il modulo non apre dispositivi. Il costruttore eredita dal client
esistente la selezione `PhysicalDrive`, l'ascendenza USB `4C4A:8057` e
l'INQUIRY esatta `WL82 / UBOOT1.00`; la validazione dei comandi resta quella
dei profili originali, tramite l'helper condiviso
[mini_windows_aligned.py](../tools/mini_windows_aligned.py).

Il nuovo metodo `exchange(cdb, data_out=None, read_length=0)` usa
`IOCTL_SCSI_PASS_THROUGH` (`0x0004D004`), con dati inclusi nel pacchetto.
Microsoft descrive questa richiesta come buffered e indicata per piccoli
trasferimenti; richiede operazioni sincrone e non supporta una fase dati
bidirezionale. L'accesso continua a passare dal device del disco, non da
un adapter che aggiri il class driver.
[Documentazione Microsoft IOCTL_SCSI_PASS_THROUGH](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through).

## Pacchetto e verifiche

| Campo/area, Python Windows 64 bit | Posizione o limite |
|---|---:|
| `SCSI_PASS_THROUGH.Length` | 56 byte |
| `DataTransferLength` | Offset 12, uint32 |
| `TimeOutValue` | Offset 16, 10 secondi |
| `DataBufferOffset` | Offset 24, uint64; è un offset, non un puntatore |
| `SenseInfoOffset` | Offset 32, valore 56 |
| `Cdb[16]` | Offset 36 |
| Buffer sense | `[56,88)` |
| Inizio payload | `align_up(88, AlignmentMask+1)` |
| Dimensione payload | 1..4096 byte, entro `MaximumTransferLength` |
| Dimensione massima del pacchetto | 8192 byte |

Il pacchetto è inizialmente azzerato. Il payload OUT viene copiato nella
sua posizione esatta; IN legge soltanto quella stessa regione. La
lunghezza della fase dati rimane invariata: non vengono aggiunti byte
al comando, al blocco RAM da 512 byte o al pacchetto STAGE da 260 byte.
Gli offset sono relativi all'inizio della struttura e l'offset dati
rispetta la maschera di allineamento dichiarata.
[Struttura Microsoft SCSI_PASS_THROUGH](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ns-ntddscsi-_scsi_pass_through).

Prima dell'INQUIRY, l'helper condiviso legge `StorageAdapterProperty` con
due query limitate: header da 8 byte e descrittore completo, massimo
4096 byte. Non vengono richiesti identificatori del dispositivo. Il
backend usa `AlignmentMask` e `MaximumTransferLength`; conserva gli altri
campi in `adapter_descriptor`. Un descrittore incoerente interrompe il
costruttore prima del comando SCSI.
[Descrittore Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ns-ntddstor-_storage_adapter_descriptor),
[richiesta proprietà Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ns-ntddstor-_storage_property_query).

L'output deve mantenere il layout richiesto, status SCSI zero e la
lunghezza di trasferimento esatta. Per IN, `bytes_returned` deve coprire
anche tutti i dati richiesti; OUT può restituire il solo header perché
non deve effettuare echo. Il parser non segue mai gli offset restituiti:
controlla che coincidano con quelli costruiti e usa gli indici locali.
La sense diagnostica è limitata sia alla sua regione di 32 byte sia ai
byte effettivamente restituiti. `last_transfer` registra CDB, direzione,
offset, lunghezze, durata, status e sense, senza copiare i payload.

Un errore Win32, status SCSI non nullo, trasferimento corto o risposta
incoerente rende terminale quell'handle. Non vengono effettuati retry,
riapertura automatica, reset o fallback a DIRECT. Un secondo exchange
concorrente viene respinto prima dell'I/O. La scelta di un nuovo trasporto
rimane al chiamante che conosce lo stato del plugin e dell'installazione.

## Ambito delle prove

I test sono interamente simulati, comprese apertura disco, query e
INQUIRY. Coprono il layout contro offset indipendenti, IN/OUT, richieste
HYRN e FD7F da 256 byte, upload da 512 byte, STAGE da 260 byte, allowlist,
offset alterati, sense, status, underrun, `bytes_returned`, errore Win32
31, stato terminale e assenza di retry:

```powershell
python -B -X utf8 -m unittest tests.test_mini_windows_spt tests.test_mini_windows_aligned tests.test_mini_recovery
```

Non è una prova che l'allineamento causasse i Win32 31 precedenti. Il
descrittore comunicato dal coordinatore per il MINI riporta
`AlignmentMask=0`, `MaximumTransferLength=65536`,
`MaximumPhysicalPages=17`, `BusType=7`: non dimostra una violazione del
requisito di allineamento. Il buffered permette di provare separatamente
il percorso senza puntatore `DataBuffer` user-space di DIRECT. Solo la
successiva prova fisica del coordinatore può stabilire se questo percorso
funziona per lo stato corrente; il modulo non dichiara il trasporto
qualificato e non esegue da solo alcuna operazione sul pedale.

Le definizioni degli IOCTL sono state controllate anche negli header
Microsoft SDK `10.0.19041.0/shared/ntddscsi.h` e `ntddstor.h` presenti
localmente; il corrispondente
[header Microsoft pubblicato](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/shared/ntddscsi.h)
definisce il codice tramite `CTL_CODE`, con funzione `0x0401` e
`METHOD_BUFFERED`. Nessuna modifica è stata applicata ai client congelati.
