# Apertura Windows da dispositivo attestato

`tools/mini_windows_quiet.py` elimina la nuova enumerazione `Win32_DiskDrive`
da ogni apertura e riapertura. Eredita senza modifiche `exchange`,
`_exchange_once`, `close` e il context manager del trasporto SPT buffered.
Il costruttore precedente e tutti i protocolli congelati restano invariati.

L'importazione e `RomDiskAttestation.from_discovery()` non eseguono I/O.
La costruzione esplicita di `QuietBufferedRomTransport` apre il dispositivo
selezionato e legge la sua INQUIRY; non installa, ritenta o resetta nulla.

```python
from tools.mini_windows_quiet import RomDiskAttestation, QuietBufferedRomTransport

# disk è un unico descrittore già scelto dal chiamante, oppure un descrittore
# conservato e verificato nel proprio piano. Qui non viene eseguita discovery.
attestation = RomDiskAttestation.from_discovery(disk)
with QuietBufferedRomTransport(attestation, slot=0x01C20000,
                               profile="app-writer-operational") as transport:
    attestation = transport.attestation
    journal(transport.open_metadata)
    # Il chiamante verifica ancora HYW1, slot, build e audit del writer.

# Ogni riapertura deve riutilizzare attestation, non ricrearla da disk:
# così conserva anche interfaccia esatta e LastArrivalDate dell'antenato USB.
```

La selezione impone una catena immutabile di 2–12 devnode, terminata dal
dispositivo USB `4C4A:8057`. Configuration Manager localizza soltanto il
`pnp_id` attestato con `CM_LOCATE_DEVNODE_NORMAL`, confronta ogni genitore e
richiede nodi avviati senza problemi. Ricava soltanto l'interfaccia disco di
quell'istanza, usando `CM_GET_DEVICE_INTERFACE_LIST_PRESENT`; non enumera tutti
i dischi. Sono accettati un solo nome e al massimo 8192 caratteri. Qualunque
errore, ambiguità o cambiamento termina l'apertura senza fallback. Questi
filtri seguono i contratti Microsoft di [CM_Locate_DevNodeW](https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_locate_devnodew)
e [CM_Get_Device_Interface_ListW](https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_get_device_interface_listw).

La prima apertura lega `interface_path` e `last_arrival_filetime` all'oggetto
restituito. Le successive li confrontano esattamente. La proprietà è
`DEVPKEY_Device_LastArrivalDate`, GUID `83da6326-97a6-4088-9453-a1923f573b29`,
PID 102, tipo FILETIME 16, otto byte, come negli header SDK Windows
10.0.19041.0 `shared/devpkey.h` e `shared/devpropdef.h`.
Una nuova enumerazione USB richiede una nuova selezione esplicita.

Il codice apre il nome dell'interfaccia disco, quindi usa
`IOCTL_STORAGE_GET_DEVICE_NUMBER` (`0x002D1080`) e accetta esattamente 12 byte:
tipo disco 7, numero uguale all'alias `PhysicalDrive` attestato, partizione
0 oppure `0xffffffff`. Questo controllo mantiene compatibile il controllo
MCN congelato, che apre l'alias PhysicalDrive. L'IOCTL recupera il numero
assegnato dal driver, senza chiedere dimensioni o geometria del supporto.
[Contratto Microsoft](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_get_device_number).

Seguono le due query del descrittore adattatore già usate dal backend e una
INQUIRY buffered di 36 byte, con vendor `WL82` e prodotto `UBOOT1.00` esatti.
La catena PnP, l'interfaccia e LastArrivalDate vengono controllate nuovamente
dopo INQUIRY. Un cambiamento chiude l'handle. Il record `open_metadata`
conserva interfaccia effettiva, numero del disco, attestazione e durata.
`transport.disk['path']` resta l'alias originale; `opened_interface` indica
il percorso realmente aperto.

Il nuovo costruttore rimuove un comportamento osservato: nelle prime quattro
riaperture del quarto tentativo, la precedente discovery coincideva con una
READ CAPACITY, due TUR e circa 11,1 secondi prima della nuova identità HYW1.
L'esportazione locale è
`build/mini-windows-diagnostics/stordiag-mcn-install-initial.json`.
Separati gruppi di sei TUR coincidevano con Win31 già prima della riapertura.
Quindi questa modifica non dimostra di eliminare tutti i Win31 o il traffico
di altri componenti Windows. L'attestazione identifica la continuità della
selezione PnP; non è autenticazione crittografica del pedale.

La verifica offline ha superato 20 test nuovi e 58 test complessivi con
backend e recupero v2. Tutte le API native sono simulate. I test coprono
dispositivo assente/sostituito, cambio di enumerazione durante l'apertura,
catena errata, interfacce multiple/troncate, limiti, errore INQUIRY, numero
disco differente, chiusura degli handle e identità delle funzioni ereditate.
Non è stata eseguita alcuna prova fisica da questo strumento. La prima
qualifica reale deve precedere ogni WREN: INQUIRY, identità del plugin
atteso e lettura completa della preimage prevista restano gate del runner.

```text
python -B -X utf8 -m unittest tests.test_mini_windows_quiet tests.test_mini_windows_spt tests.test_mini_read_recovery_v2 -q
```
