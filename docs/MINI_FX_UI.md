L’editor HyperRig MINI ha superato una prova reale via USB sulla build v3
`9c612d2c60e863511e3c20f801c024ac2d0064cf935cdf1131a2a3b9eea2363c`.
Si riapre con [launch_mini_fx_editor.cmd](../tools/launch_mini_fx_editor.cmd),
che usa il bundle locale [hyperrig-mini-fx-editor](../build/hyperrig-mini-fx-editor).
Non occorre elevazione amministrativa per usare l’editor.

Il 16 novembre 2026 l’interfaccia originale ha eseguito aggiunta seriale di un
Noise Gate in Post, modifica della soglia da −70 a −71 dB, bypass e riattivazione,
salvataggio di un nuovo preset con scena A, rimozione dell’effetto e caricamento
del preset salvato. Quest’ultimo ha ricostruito il gate acceso con soglia −71 dB,
capture A2 nello slot 0 e nessun IR. Il caricamento finale del preset originale
ha ripristinato la catena vuota e i livelli 0/0 dB.

Lo slot **1A, indice 0**, è rimasto invariato. Il nuovo slot **1B, indice 1**, è
stato intenzionalmente conservato e si chiama anch’esso **“Preset 1A”**: l’interfaccia
ha copiato il titolo corrente. Il nome “HyperRig Test” non è stato inviato.

La verifica indipendente è in
[mini-fx-ui-hardware.json](../research/mini-fx-ui-hardware.json).
Collega nove comandi mutanti ai byte USB e agli input UI, ricalcola sette stati
del pedale e verifica il ripristino finale. Sono registrati 13 input trusted
del browser, prodotti dall’operatore tramite CDP, più due click derivati dal
gestore originale del tasto Enter. Il report operativo originale è conservato
senza modificarne l’esito storico.

Il profilo abilita via USB `GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`, `FXA`, `FXP`,
`FXE` e `FXR`. Tipi, parametri e ID seguono il catalogo e lo stato letti dal
pedale; l’aggiunta è seriale e il firmware mantiene l’ammissione CPU/memoria.
Routing, operazioni massive, aggiornamento firmware e assegnazioni del pannello
rimangono fuori da questo profilo.

Questa prova dimostra salvataggio e ricaricamento della catena nella stessa
accensione. Non verifica la conservazione del nuovo slot dopo uno spegnimento,
tutti gli effetti o valori possibili, Android/BLE, qualità acustica o latenza
analogica. L’app è rimasta aperta; è stato staccato soltanto l’osservatore della
prova. Il bundle e la sua qualifica precedente non sono stati riscritti.
