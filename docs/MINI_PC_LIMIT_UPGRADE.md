# Aggiornamento MINI v2 → v3

Il desktop ha comunicato realmente con il MINI su COM3: PONG HyperRig MINI,
37 tipi di effetti, modello e diagnostica. La v2 installata è in modalità
`safe`, con audio disattivato. La prova è in
`research/mini-desktop-readonly-hardware.json`; non certifica modifiche o
salvataggi dei preset.

La candidata v3 corregge il limite di esecuzione che ha provocato il crash
all'ingresso del codice audio aggiunto. SHA256 dell'area applicazione:

```text
9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c
```

Rispetto alla v2 cambiano 11 byte nel settore fisico `0x4000`, inclusi i CRC
del contenitore. Il codice audio, il recupero tramite footswitch e la copia
RAM restano identici. L'immagine è ricostruita e verificata offline;
l'installazione e l'avvio della v3 non sono ancora avvenuti.

## Sequenza predisposta

1. Conservare la prova del desktop e chiudere la sua porta nativa.
2. Aprire una nuova sessione WebSerial sulla riga esatta
   `Tank-M HyperRig (COM3)`, ricevere il PONG e inviare una sola volta `UBOOT`.
3. Verificare separatamente la nuova enumerazione ROM, il suo orario di
   arrivo e INQUIRY. Un ACK o una disconnessione non provano da soli la ROM.
4. Caricare il lettore B e conservare una nuova lettura completa di 1 MiB.
   L'applicazione deve essere esattamente v2; SPL e keymac devono coincidere
   con il backup della stessa unità. VM, BTIF e USR sono conservati nella
   versione appena letta: dopo l'avvio possono differire dal backup stock.
5. Derivare il piano dal dump fresco, caricare il writer A e verificare
   tutta l'applicazione prima della scrittura. Aggiornare il solo settore
   `0x4000`, programmando la pagina dell'header per ultima.
6. Ricaricare il lettore B ed effettuare una seconda lettura completa.
   Il confronto deve corrispondere esattamente alla v3 più tutti i byte
   esterni dell'immagine appena acquisita. Il verificatore indipendente
   controlla anche il registro grezzo dei comandi.
7. Solo dopo la verifica completa, eseguire un singolo riavvio software e
   aprire l'editor WebSerial v3 come primo client. Nessun PING Python prima
   dell'editor; questo percorso non aveva comunicato con la v2.

Il runner di installazione non riavvia il dispositivo, non ripristina lo
stock automaticamente e non ripete salti o mutazioni dall'esito ignoto.
Riusa i wrapper già verificati per riconciliare errori Win31 con lo stato
esatto del dispositivo. La pausa MCN temporanea viene chiusa su ogni uscita.

## File e verifiche

- `tools/plan_mini_pc_limit_upgrade.py`: piano offline da dump fresco;
  quattro test, più ricomposizione indipendente sulla candidata reale.
- `analysis/hardware/run_mini_pc_limit_install.py`: sequenza controllata;
  otto test con lettore, writer e wrapper reali su protocolli simulati.
- `tools/inspect_mini_pc_limit_upgrade.py`: verifica indipendente di dump,
  CDB e audit grezzi; 13 test, incluso un bundle completo con lettura
  ripetuta giustificata da un errore di trasporto e contatore reale maggiore
  di 1 MiB. Nessun rapporto di successo hardware è stato emesso.
- `tools/enter_mini_rom_webserial.py`: ingresso ROM dall'applicazione;
  nove test Python e 61 condizioni JavaScript, senza prova fisica UBOOT.
- `tools/build_mini_ultrarig_v3.py` e
  `firmware/mini/pc_limit_port/patches.py`: sette test della derivazione e
  14 del limite PC.
- `analysis/hardware/run_mini_first_boot_v11.py`: otto test del riavvio
  separato. Il contatore del lettore deve coincidere con quello realmente
  ricostruito dal verificatore, comprese eventuali letture perse e spiegate.
- `tools/launch_mini_desktop_v3.py`: nove test dell'editor associato alla v3
  e 11 regressioni della base desktop. Attende la selezione UIA della porta
  esatta per 120 secondi; non usa DeviceAccess per il selettore WebSerial.

I pin del riavvio e il preflight dell'editor potranno essere completati solo
dopo aver ottenuto i nuovi rapporti hardware. Non sono stati sostituiti con
risultati simulati.

Il preflight statico dell'installazione è passato con 251 input vincolati
tramite SHA256. Prima dell'esecuzione, il manifesto deve includere anche
il rapporto UBOOT reale completato. Il preflight non produce questa prova
e non accede al dispositivo.

L'ultima sessione amministratore è terminata per scadenza il 16 novembre
2026 alle 00:17:03 UTC. L'editor continua a funzionare senza amministratore;
per aprire la ROM e scrivere la flash Windows richiede una nuova elevazione.
La richiesta di disponibilità dell'utente riguarda quella conferma sul PC.
Non sono state cambiate impostazioni UAC, servizi o attività pianificate.

Avvio normale, audio reale, modifica/salvataggio dall'app e recupero
integrato con i footswitch restano prove fisiche da completare. I test
simulati non vengono registrati come risultati hardware.
