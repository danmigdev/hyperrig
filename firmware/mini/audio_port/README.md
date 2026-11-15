# Agganci codec per il port integrale G → MINI

Questo componente mantiene DSP, RTOS, IRQ e driver ALNK della G M5.71 v2.
Aggiunge la sequenza di scheda ricostruita dal MINI. Non contiene un backend
DSP MINI, un plugin ROM o un programma di flash.

```powershell
python -B -X utf8 firmware/mini/audio_port/verify.py
```

La build produce `build/mini-audio-port/hyperrig-mini-g-audio.{elf,bin,asm}`
e `manifest.json`. L'append XIP è di 2068 byte a `0x02076AAC`, senza `.data`
o `.bss`. Il linker rifiuta una necessità di RAM statica o un superamento del
limite riservato alla configurazione. I puntatori originali G sono fissi:
il modulo vale soltanto per gli hash G verificati dal builder.

`audio_patches(g_plain, manifest['elf']['symbols'])` in `patches.py` restituisce
due `BinaryPatch` per il formatter integrale: 34 byte a `0x020053A4` e quattro
byte a `0x0200541E`. Richiede l'immagine G decodificata originale. Il payload
compilato viene passato separatamente come `append_code`; non si scrive
direttamente il payload nella NOR cifrata.

Il preambolo conserva `r6=1`, chiama `hyperrig_mini_g_audio_pre_current_clock`
e salta a `0x02005436` se fallisce. Dopo successo continua il codice G
originale a `0x020053C6`: IRQ, apertura ALNK e selezione nominale 48kHz.
La chiamata post passa da un piccolo stub a `0x020053AE` che salva RETS/r4,
chiama `hyperrig_mini_g_audio_post`, ripristina i registri e controlla l'esito.
Il successo torna a `0x02005422`; un errore salta a `0x02005436`, evitando
il flag di successo originale. Lo stub usa temporaneamente otto byte dello
stack applicativo e ripristina SP al valore entrante. Non scrive esplicitamente
SSP o registri IRQ e conserva la convenzione ABI.

Il pre legge MHz nominali da `0x020057C6`, rifiuta zero e valori superiori a
2147 prima della moltiplicazione per un milione. Porta PA9 basso, attende
100000 iterazioni, configura il bus PA1/PA2 e invia i 22 record originali,
fermando la sequenza al primo errore. Conserva OSR256; non applica una nuova
configurazione di rate o filtri. Il post controlla lo stato software G
`0x01C278DC=1` e il rate `0x01C278E4=48000`, chiama l'originale `0x02005194`,
richiede stato finale 2, attende 100000 iterazioni e porta PA9 alto.

| Operazione GPIO | Helper originale G |
|---|---:|
| OUT e direzione output | `0x02004998` |
| Direzione input | `0x02004AD6` |
| Ingresso digitale | `0x0200187C` |
| Pull-down | `0x02004BAC` |
| Pull-up | `0x02004C9A` |

Questi helper mantengono il protocollo G: critical entry `0x01C00E2E`, lock
del banco a `0x01C25CE0`, critical exit `0x01C00E46`. **Non aggiungere un lock
esterno del banco**, che verrebbe acquisito nuovamente dagli helper. Per DIR=0
il binding legge il latch e usa OUT con quel valore. Questo richiede proprietà
esclusiva dei pin interessati, oltre al lock per la modifica del banco.

Le prove ASan/UBSan controllano ordine PA9/attese/bus/start originale, i 22
record sul bus, 110 posizioni NACK, errore di timing, due errori di avvio e
quattro precondizioni. Il modello dei soli hook percorre 42 combinazioni
ABI/esito; tutti i byte generati sono decodificati anche dal tool vendor.
Tre casi negativi controllano identità sorgente, LMA e memoria non inizializzata.
Non è un bound dell'intero stack G o una simulazione di periferiche/interrupt.

Prima dell'avvio servono la patch pannello che elimina il conflitto PA1/PA2,
la verifica degli altri proprietari GPIO e la stabilità del clock durante
il bus. Il getter non impedisce cambi di clock. Restano inoltre il contratto
boot/storage e la qualifica fisica di codec, OSR256 a rate G, clock e audio.
PA9 basso non dimostra mute analogico; i loop non sono microsecondi calibrati.
Un errore post non annulla i passi G open/clock già eseguiti. Non è stata
composta o eseguita una candidata audio da questo verificatore.
