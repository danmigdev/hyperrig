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
