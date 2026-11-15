# Guardia applicativa v2 per recupero tramite footswitch

La v2 rende PA10, PA0 e PA3 ingressi **prima** di richiamare il controllo v1.
Questo rimuove il requisito che il cold SPL li abbia già lasciati input. La
policy appartiene al nuovo firmware HyperRig per MINI: quei pin sono assegnati
ai tre footswitch e rimangono input fino alla successiva inizializzazione del
pannello. Gli altri bit GPIO vengono preservati. V1 e il probe ROM HYK1 non sono
modificati: HYK1 continua a rifiutare direzioni output e a ripristinare lo stato
precedente.

È un componente XIP per l'applicazione UltraRig G completa adattata, non un
plugin eseguibile dalla ROM. Non è stato inviato al dispositivo né inserito
dal presente tool nel candidato integrato. L'esecuzione hardware e il recupero
fisico restano qualifiche separate.

## Innesto e contesto di avvio

La sola patch nel G originale è il blocco di 12 byte a `0x0200018A`:

```text
preimage: eeffb850c301edffb860c301
          sp = 0x01C350B8; ssp = 0x01C360B8
patch:    goto.l <indirizzo assegnato>; quattro nop
```

L'entry `0x02000120`, i vettori e tutti gli altri byte originali restano intatti
per questo componente. Il prefix riproduce esattamente le due istruzioni di
stack, salva PSR/RETS/RETI e tutti i registri r0…r15, quindi esegue:

```text
PORTA.DIR = PORTA.DIR | 0x409
csync
call hyperrig_mini_entry_recovery_check
```

Solo l'esito `ALL_THREE_HELD` raggiunge il reset. Gli altri esiti, compreso
l'errore di configurazione GPIO, ripristinano GPR/PSR/RETS/RETI e proseguono a
`0x02000196`, prima della prima chiamata originale G. R0 conserva quindi il
contesto SPL. Il ramo di reset non ritorna e non ha bisogno di riprendere il
contesto applicativo.

Il callable v1 continua a salvare e ripristinare DIR/DIE/PU/PD nei soli tre bit,
ma ora il DIR salvato è già input: non riattiva una direzione output contro un
tasto premuto. OUT, gli altri pin e i registri di clock/cache/IRQ non vengono
modificati. Il reset è lo stesso v1: marker `usb_update_mode\0`, barriera,
RST_CON bit 4, barriera e attesa. Nessun salto arbitrario alla ROM.

## Allocazione e API per il builder

L'indirizzo non ha un default. Deve seguire gli append già assegnati dal
builder, partendo dalla fine originale di `app.bin`, `0x02076AAC`:

```powershell
python -X utf8 tools/build_mini_entry_recovery_v2.py --address 0x020772C0
```

`0x020772C0` è soltanto il fixture corrispondente all'audio shim da 2068 byte
attualmente disponibile. Un nuovo audio shim richiede un nuovo indirizzo e
una nuova build. Il codice richiede allineamento di quattro byte; eventuali
padding devono già essere parte dell'append precedente. Il limite finale
`0x0207DE81` riserva i 383 byte originali di `cfg_tool.bin` entro l'app-area MINI.

Le API di `tools.build_mini_entry_recovery_v2` sono:

- `build(address)`: compila e verifica; produce payload/ELF/manifest sotto
  `build/mini-entry-recovery-v2/<indirizzo>/` e restituisce il manifest.
- `patches(g_plain, address)`: restituisce una tupla di `BinaryPatch`, previa
  verifica dell'hash del G decodificato originale e della preimage a 12 byte.
- `bind_append(g_plain, preceding_append, payload, manifest)`: verifica che
  l'indirizzo coincida con `0x02076AAC + len(preceding_append)`, controlla hash,
  dimensioni e patch e restituisce l'append concatenato. Non scrive file e non
  accede a dispositivi.

Il manifest di una build isolata dice correttamente
`actual_preceding_payload_validated=false`: un indirizzo di link non dimostra
che lo spazio sia assegnato. L'integratore deve chiamare `bind_append` con i
byte reali precedenti e passare il risultato e la patch al formatter esistente.
Il formatter rimane responsabile di CRC, directory e sovrapposizioni con le
altre patch. Non è stato modificato da questa attività.

## Verifiche riproducibili

Il componente occupa 298 byte: prefix v2 di 54 byte, check v1 di 190 e reset
v1 di 54. Non aggiunge BSS né dati da copiare in RAM. Il massimo stack è
100 byte; i due modelli SP indipendente/alias di SSP vengono verificati.

Per ciascun indirizzo il modello delle **istruzioni effettivamente collegate**
esegue 1280 casi: otto direzioni iniziali, otto combinazioni di livelli, contesti
variabili, i due modelli SP/SSP, errori di readback e rilascio di ciascun tasto
in ogni punto dei 32 campioni. Disturba deliberatamente PSR dopo il salvataggio
per controllarne il ripristino; non simula i flag della CPU. Verifica R0 sia con
il puntatore SPL sia con valori variabili, tutti gli altri registri, i bit GPIO
estranei, l'ordine delle barriere e l'assenza di reset sul ramo normale.

La branch di innesto viene disassemblata anche dal toolchain vendor. Il parser
ELF rifiuta segmenti scrivibili, BSS, simboli irrisolti, indirizzi fuori limite e
modifiche ai callable congelati. I due corpi devono conservare questi hash
anche dopo rilocazione:

| Corpo | SHA256 dei byte |
| --- | --- |
| check v1 | `0872924dc1d476913a441a6d58b83025962a00ca6b9ceb0e8b66e07d8afc045d` |
| reset v1 | `a84be9b34190a67265f001ed328372eaba2c48fcea3111b2ead481a6bb7ee48f` |

È stata verificata anche la rilocazione a `0x0207DD54`, che termina a
`0x0207DE7E`, vicino al limite riservato. Il relativo manifest resta nella sua
directory di build; il report `research/mini-entry-recovery-v2.json` descrive
invece il fixture a `0x020772C0`.

La qualifica fisica HYK1 riguarda tasti e marker/reset in ROM. La v2 rimuove
la dipendenza dalla direzione iniziale del cold SPL, ma non trasforma quella
prova in una prova dell'intero prefix XIP o del boot G. Rimangono da verificare
sull'hardware l'effettivo mux/riconoscimento dei tasti e la durata del controllo
con il clock ereditato. Il conteggio dei loop non è una misura temporale né
un modello elettrico o di debounce continuo.

La guardia è utile per un'immagine valida che si blocchi **dopo** l'entry.
Un header, entry o prefix danneggiato è un caso diverso: non viene dichiarato
un recupero universale di qualsiasi immagine corrotta.
