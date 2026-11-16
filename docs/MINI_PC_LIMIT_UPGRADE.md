# Aggiornamento MINI v2 → v3

Il desktop ha comunicato realmente con il MINI su COM3: PONG HyperRig MINI,
37 tipi di effetti, modello e diagnostica. La prima v2 installata era in modalità
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
RAM restano identici. Il 16 novembre 2026 alle 05:00 UTC l'aggiornamento reale
ha completato una cancellazione e 16 programmazioni, con la pagina `0x4000`
per ultima. La verifica indipendente in
[`mini-pc-limit-install-independent.json`](../research/mini-pc-limit-install-independent.json)
conferma l'applicazione esatta e tutti i byte esterni preservati dal dump
fresco; USR era già cambiata durante l'esecuzione della v2.

Il boot v11 ha osservato COM3 alle 05:04 UTC. La successiva sessione
`build/mini-desktop-v3-real-02/` ha ricevuto il PONG reale senza `safe`,
`CLKSTATE safe=0` e `LVL m=2`. Due letture `STAT` hanno osservato
`T.nproc=328986` e `329126`, oltre a input/output e blocchi audio crescenti.
Ascolto analogico, modifica/salvataggio dei preset e recupero integrato con
i footswitch restano prove distinte da completare.

Il launcher congelato aveva un limite di 8 MiB per i file di prova, superato
da due trace chiusi. Il [driver di compatibilità](MINI_V3_EDITOR_DRIVER.md)
legge soltanto quei due file fino a 32 MiB e ne controlla dimensione e SHA256;
registra questa estensione nelle nuove prove dell'editor.

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

I pin del riavvio sono stati completati usando i rapporti hardware conclusi,
i dump e la verifica indipendente. Il preflight del nuovo driver dell'editor
è passato sulle stesse prove reali prima del collegamento.

Il preflight statico dell'installazione era passato con 251 input vincolati
tramite SHA256. Prima dell'esecuzione il manifesto è arrivato a 254 input,
includendo chiusura desktop, selezione UIA e rapporto UBOOT reali. Il preflight
verifica questi file senza accedere al dispositivo.

La precedente sessione amministratore era scaduta alle 00:17:03 UTC.
Al ritorno dell'utente è stata avviata una nuova sessione temporanea alle
04:54 UTC, con la conferma UAC di Windows. Ha eseguito aggiornamento e boot;
l'editor WebSerial funziona senza elevazione. Le impostazioni UAC, i servizi
e le attività pianificate non sono stati modificati.

L'avvio normale e la comunicazione reale dell'editor sono verificati.
Ascolto audio, modifica/salvataggio dall'app e recupero integrato con i
footswitch restano da completare. I test simulati restano distinti dalle
osservazioni hardware.
