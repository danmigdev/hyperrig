# Qualifica del preset conservato: continuazione USB v2

Il modello `browser-retained-save-and-reload-two-sessions-v2` mantiene due
sessioni reali separate. Il report `mini-first-preset-ui-04` resta fallito:
attesta i quattro comandi UI già completati (`GAIN`, ripristino `GAIN`,
`PSAVE`, `SNAPSAVE`), senza affermare un ricaricamento. La continuazione deve
provare un nuovo `GAIN` e `PLOAD`, confrontare lo stato ricaricato e chiudere
la porta nativa. Il validatore non ricostruisce una sessione artificiale di
sei comandi e non modifica i report precedenti.

La v2 riguarda soltanto il collegamento iniziale:

- Una sola apertura Web Serial sul VID/PID `3654:5155`.
- Fino a cinque `PING` del bootstrap originale. La ripetizione è ammessa
  soltanto dopo un timeout interamente vuoto, con scrittura nativa conclusa,
  nessun byte RX e nessun errore di trasporto. Nessuna mutazione è ripetuta.
- Identità ricostruita da `getInfo()`, apertura nativa e PONG esatto presente
  nei byte RX. Quando esiste anche una prova UIA, viene controllata
  separatamente. La sua assenza non viene trasformata in una selezione UIA
  inventata, né viene attribuita la selezione a una persona.

Il modello precedente resta distinto e continua a richiedere la propria
prova UIA. La versione storica del validatore è conservata nel commit
`b8a786e`; il nuovo report registra l'hash effettivo della versione v2 usata.

La creazione del bundle richiede una continuazione fisica riuscita e verifica
una volta l'intera catena locale di fonti, risposte, salvataggio e reload.
Fixture sintetiche e tentativi incompleti non producono capacità. Le sole
famiglie previste sono USB `GAIN`, `PLOAD`, `PSAVE`, `SNAPSAVE`; BLE, upload,
modifiche FX e le altre famiglie rimangono chiuse.

L'avvio normale dell'editor verifica il sigillo e i file locali del bundle,
senza rieseguire la catena storica o dipendere dal percorso del report del
trial. PONG identifica il firmware dichiarato: non attesta il suo hash.
Un reload riuscito non costituisce una misura della qualità audio né una
prova generale di persistenza dopo spegnimento.
