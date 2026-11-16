# Obiettivo HyperRig

Requisiti espliciti dell'utente, aggiornati il 15 novembre 2026.

HyperRig è il port del firmware UltraRig per TANK MINI, insieme alle sue
applicazioni adattate. Il firmware finale sostituisce il firmware stock MINI.
L'applicazione stock MINI non è la base del prodotto, non ospita il motore
HyperRig e non viene conservata come backend. Il campione stock e il dump
dell'esemplare servono per ricostruire le caratteristiche della scheda e per
il ripristino.

## Copia locale e possibilità di modifica

- Conservare copie originali verificate del firmware UltraRig e delle sue app,
  identificando versione, provenienza e SHA-256.
- Conservare il materiale di reverse engineering: estrazioni, disassemblati,
  decompilazione, formati, protocolli, mappe e prove delle ricostruzioni.
- Rendere modificabili firmware e applicazioni attraverso sorgenti recuperati
  o ricostruiti e strumenti riproducibili di compilazione, ricostruzione e patch.
- Distinguere i sorgenti compilabili dal pseudocodice inferito e dai componenti
  ancora binari. Una copia binaria o una decompilazione parziale non certifica
  il recupero completo dei sorgenti originali.
- Conservare gli originali separatamente dalle copie HyperRig e mantenere le
  attribuzioni e licenze dei componenti derivati.

## Minimo funzionante da dimostrare

1. Il TANK MINI avvia stabilmente il port HyperRig dell'applicazione UltraRig.
2. Il percorso audio reale del MINI elabora il segnale attraverso il firmware
   adattato e i componenti DSP UltraRig.
3. L'app HyperRig riconosce il target MINI, legge e modifica i preset del
   firmware adattato, con verifica delle risposte e dello stato effettivo.
4. Il repository locale conserva quanto necessario per ripetere la build e
   apportare ulteriori modifiche, con una descrizione esatta delle parti
   ricostruite e dei componenti ancora da analizzare.

Probe RAM, test sintetici, simulazioni e demo dell'interfaccia sono verifiche
intermedie. Non soddisfano da soli il minimo funzionante.

## Minimo operativo raggiunto il 16 novembre 2026

Il port v3 dell'applicazione UltraRig G è installato sul MINI. Sono verificati
avvio normale, elaborazione A2, conservazione del primo preset dopo il riavvio
dell'utente e audio da lui descritto come regolare. L'editor HyperRig via USB
ha eseguito realmente aggiunta di un effetto, modifica del parametro, bypass,
riattivazione, salvataggio in 1B, rimozione e richiamo di 1B: il Noise Gate
Post è tornato attivo con soglia −71 dB. Infine è stato richiamato il preset
originale 1A, con gain 0/0 e catena FX vuota.

Le prove sono in `build/mini-saved-reload-ui-v2-07/report.json`,
`build/mini-fx-ui-smoke-01/report.json` e nelle verifiche di installazione
collegate dal README. L'app utilizzabile è
`tools/launch_mini_fx_editor.cmd`, con bundle `build/hyperrig-mini-fx-editor`.
Una prova separata con nove effetti attivi ha misurato circa 2,395 ms medi
di elaborazione interna e 2,526 ms di massimo osservato, senza fault segnalati;
la latenza analogica completa non è stata misurata.

Questo completamento riguarda il minimo sopra definito. Il C originale
completo non è recuperato: rimangono pseudocodice inferito e componenti binari,
insieme alle ricostruzioni compilabili e agli strumenti di patch/build locali.
Restano separati la prova del recupero integrato all'accensione, i controlli
fisici completi, il routing e gli altri comandi editor non ancora abilitati,
e l'adattamento completo delle scritture dell'app mobile/BLE.

## Decisioni di implementazione

La candidata integrale usa l'applicazione UltraRig G come base. Le modifiche
al target MINI sono esplicite, controllate rispetto ai byte originali e
documentate. Il ramo sperimentale che avrebbe innestato il DSP nel firmware
stock MINI è stato abbandonato su indicazione dell'utente; non è un prodotto
alternativo accettabile per questo obiettivo.

Il protocollo dell'app finale resta quello UltraRig. Il target MINI viene
identificato mediante `tankm_fw`; il protocollo MIDI del MINI stock resta
uno strumento di diagnosi e accesso al firmware originale durante lo sviluppo.

Il lavoro procede con agenti in parallelo. Il risultato viene dichiarato
completo soltanto dopo le verifiche sul pedale e sull'app, indicando anche
le eventuali limitazioni residue del reverse engineering.

## Recupero scelto e Raspberry Pi dell'utente

L'utente ha escluso la strada USB_KEY con cablaggio GPIO e scelto il
recupero mediante i tre footswitch. Il lavoro prosegue su questa strada:
verifica dei tasti in RAM, marker/reset verso ROM e guard all'ingresso
dell'applicazione UltraRig adattata. USB_KEY e i suoi strumenti restano
materiale sperimentale archiviato, non un prerequisito richiesto all'utente.
Il guard non copre un header o il proprio codice danneggiati; questo limite
resta distinto dal recupero dei blocchi successivi all'ingresso.

Il Raspberry Pi 3 disponibile ha già un sistema installato e viene usato
come MIDI hub. L'utente richiede di preservare questa installazione.
Sono stati eseguiti controlli di compatibilità in sola lettura e una build
con simulazione in una cartella dedicata. Nessuna reinstallazione,
modifica dei servizi MIDI, configurazione di avvio o richiesta di linee
GPIO è stata effettuata. Il Pi non serve al percorso footswitch scelto.
