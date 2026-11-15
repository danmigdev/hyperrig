# Errori Windows durante l'installazione MINI

I tre fallimenti Win32 31 coincidono ciascuno con sei richieste automatiche
`TEST UNIT READY` entro 3 ms. La fonte è il log preesistente
`Microsoft-Windows-Storage-ClassPnP/Operational`, provider StorDiag; l'analisi
non ha inviato comandi al dispositivo. Il filtro richiede `PhysicalDrive4`,
WL82/UBOOT1.00 e lo stesso GUID di dispositivo, non solo il numero del disco.

| Prova | Comando fallito | Inizio UTC | Intervallo dei sei TUR rispetto all'inizio |
| --- | --- | --- | --- |
| Prima installazione | `FD7F`, 256 byte, indirizzo `0x5900` | 20:48:44.774876 | −1,019 .. +1,451 ms |
| Ripresa con pausa 20 ms | `FD7F`, 256 byte, indirizzo `0x5D00` | 21:00:05.537763 | −2,176 .. +0,317 ms |
| Trasporto buffered | `FC7E`, 16 byte | 21:28:00.009604 | −2,134 .. +0,493 ms |

I TUR riportano `NTSTATUS=0xC0000185`, `SrbStatus=0xC4`, stato SCSI 2 e sense
2/3A/00. L'header SDK locale `srb.h` 10.0.19041.0 scompone 0xC4 in errore
0x04, coda congelata 0x40 e autosense valido 0x80. Microsoft descrive il flag
QUEUE_FROZEN come indicazione del port driver che la coda della periferica è
stata congelata. Questo stato è osservato sul TUR, non sul nostro vendor CDB,
il cui SRB non è disponibile nella risposta IOCTL fallita.
[Documentazione Microsoft SCSI_REQUEST_BLOCK](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/srb/ns-srb-_scsi_request_block).

Il terzo IOCTL fallisce in 0,205 ms con zero byte restituiti. I campi SPT ancora
a zero o inizializzati non provano uno stato SCSI positivo né dati sense
ricevuti. Il programma usa IOCTL sincroni e il dispositivo di classe corretto;
la sostituzione del buffer diretto con quello buffered non ha eliminato il
problema. Un solo handle nel programma non elimina il traffico dello stack
storage di Windows.
[Contratto Microsoft IOCTL_SCSI_PASS_THROUGH](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddscsi/ni-ntddscsi-ioctl_scsi_pass_through).

L'audit fresco acquisito da root dopo il terzo errore conferma 32 pagine
programmate, due settori completati, WREN34, erase2, stato NOR libero, zero
errori e contatore letture 598016: l'ultima lettura di 512 byte aveva completato.
Il dump integrale `full-partial3.bin` ha SHA256
`74095e9ae0f69878dd5d708150b419548e28db0cf1dabc0e3076c27cd8873406`;
solo i settori `0x5000` e `0x6000` contengono la candidata. Questo permette un
piano nuovo da dati reali, senza ripetere una mutazione ambigua.

La prova MCN separata ha mantenuto il reader RAM senza modificare il NOR.
Nelle finestre baseline di 16,001 s e pausa di 24,029 s non compaiono TUR.
Neppure nei 16,001 s successivi compaiono TUR; subito dopo la riabilitazione
sono registrate due `READ CAPACITY(10)` e due notifiche StorDiag523. Il confronto
zero/zero non prova la soppressione di richieste presenti prima della pausa.
Dimostra solo il successo del controllo, la continuità delle 239 query
esplicite e il ripristino richiesto dal runner.

L'IOCTL MCN è un meccanismo documentato per sospendere le notifiche sul singolo
handle; il campione Microsoft controlla il contatore DisableCount nel percorso
di notifica. L'efficacia contro questi errori richiede ancora una prova con
traffico sufficiente. Nessuna impostazione di registro è stata cambiata da
questa analisi.
[IOCTL_STORAGE_MCN_CONTROL](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddstor/ni-ntddstor-ioctl_storage_mcn_control),
[campione Microsoft classpnp/autorun.c](https://github.com/microsoft/Windows-driver-samples/blob/main/storage/class/classpnp/src/autorun.c).

La correlazione ripetuta e il flag della coda supportano un problema nel
percorso storage durante i TUR. Non identificano il pacchetto USB causale e
non dimostrano una CSW obsoleta, una sovrapposizione BOT o un difetto preciso
del driver. Non c'è una cattura dei pacchetti USB di queste prove. Microsoft
documenta ETW con eventi di trasferimento per distinguere quel livello.
[Acquisizione tracce USB con Logman](https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/how-to-capture-a-usb-event-trace).

`tools/audit_mini_windows_failures.py` ricostruisce il report
`research/mini-windows-failures.json` esclusivamente dagli export e dai trace
salvati. Conserva i record ID, hash, tempi e risultati anche quando non
sostengono l'ipotesi MCN. Il recupero delle query è separato in
[MINI_READ_RECOVERY_V2.md](MINI_READ_RECOVERY_V2.md).
