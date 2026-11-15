# Pannello HyperRig MINI: adattamento del firmware G intero

`tools/audit_mini_panel_port.py` prepara dieci patch locali, per 53 byte di
intervalli, sull'applicazione UltraRig G M5.71 originale. Non produce un file
installabile e non accede al pedale. Il firmware MINI stock è soltanto la fonte
per i collegamenti della scheda. DSP, eventi, azioni, preset e protocollo restano
quelli dell'applicazione G.

```powershell
python -X utf8 tools/audit_mini_panel_port.py
```

Il report riproducibile è `research/mini-panel-port.json`. Comprende hash delle
fonti, indirizzi, preimmagini, nuove istruzioni, controlli e limiti della prova.
L'API per il formatter è:

```python
from tools.audit_mini_panel_port import panel_patches
from tools.audit_mini_ultrarig_port import compose_candidate

# g_plain è l'app-area G originale decodificata da unpack_app(g_container).
patches = panel_patches(g_plain)
candidate, report = compose_candidate(
    g_container, mini_fwsc, additional_patches=patches)
```

Tutte le patch hanno lunghezza invariata e richiedono l'hash G esatto. Le patch
per codice/dati copiati in RAM usano l'indirizzo **di caricamento flash**; il
report indica anche l'indirizzo di esecuzione. Non vanno applicate direttamente
ai byte cifrati della NOR.

## Writer incompatibile e ritorno al chiamante

La funzione G `0x02015858..0x020158C2` configura PA0, PA1, PA2 e PA3 come uscite
e serializza 29 bit. PA2 svolge il ruolo di clock, PA3 quello di dati, PA0 quello
di latch; PA1 viene abbassato a fine trasmissione. La struttura è compatibile
con un registro a scorrimento con enable; il componente 74HC595 e le sue
connessioni elettriche non sono stati verificati sulla scheda.

Sul MINI PA1 e PA2 sono SDA/SCL del codec, mentre PA0 e PA3 sono ingressi dei
switch. Lasciare il writer attivo comprometterebbe entrambi i percorsi.

Il chiamante diretto verificato `0x02017568` confronta il nuovo frame con
`0x01C1F208`, chiama il writer quando differisce e termina senza usare il valore
di ritorno. Lo stub di 12 byte scrive il nuovo frame in quella stessa word RAM
e ritorna. Non modifica lo stack, i registri callee-saved o registri speciali;
usa soltanto `r1` come temporaneo e conserva `r0`. Le istruzioni originali dopo
lo stub restano nel file, irraggiungibili dall'ingresso normale.

Il pannello LED è quindi **disabilitato**, non portato. L'editor MINI mantiene
disabilitate le proprie capacità per il pannello finché l'intero percorso non
sarà verificato. Bloccare i comandi nell'app, da solo, non avrebbe neutralizzato
questo writer periodico del firmware.

## Tre ingressi, due scanner e mappa logica

| Percorso | G originale | Adattamento MINI |
| --- | --- | --- |
| Tabelle fisiche | PH6, PH7, PH8, PH9, PA10 | Primi tre: PA10, PA0, PA3 |
| Inizializzazione `0x0201599C` | 5 ingressi | 3 ingressi |
| Polling principale `0x02015AD0` | 5 ingressi | 3 ingressi |
| IRQ RAM `0x01C03338` | 5 ingressi | 3 ingressi |
| Mappa logica A/B/C/D | 4, 3, 1, 0 | 0, 1, 2, 3 |

Il MINI stock inizializza PA10, PA0 e PA3 a `0x02006096`; lo scanner
`0x0200A060` legge `PORTA.IN` e costruisce i tre bit in questo ordine. Entrambi
i firmware interpretano il livello basso come pressione. L'ordine delle
etichette fisiche sulla pedaliera non è ancora stato verificato: assegnare
PA10/PA0/PA3 ad A/B/C è una politica esplicita del port.

La sola modifica delle tabelle GPIO sarebbe insufficiente: con la mappa G
originale l'indice fisico 2 non corrisponde ad alcuno switch logico. Il port
modifica i quattro byte iniziali a `0x02075974`, copiati a `0x01C1F1F4`, e il
loader di configurazione a `0x02003F32` per mantenere la mappa identity anche
quando legge una vecchia permutazione salvata. Conserva quattro slot di azioni:
D usa lo stato valido 3, inizialmente rilasciato, senza scanner fisico.

Gli stati 3 e 4 ricadono nella BSS azzerata dal reset originale
`[0x01C2030C, 0x01C38050)`. La patch non inventa un indice `0xFF`, che vari
consumatori G userebbero senza controllo come offset di memoria. Il dispatch
originale `0x02014C04`, i timer e le azioni rimangono invariati. Non si dichiara
la funzionalità dei gesti del quarto switch su tre pulsanti.

Lo scanner RAM è parte dell'IRQ registrato dall'inizializzazione audio G.
Legge le tabelle IN/mask predisposte dal pannello e accoda eventi; la patch del
suo limite deve essere applicata alla **LMA `0x02059AB8`**, non alla VMA RAM.
Il flag che abilita lo scanner è impostato soltanto dopo il completamento
dell'inizializzazione delle tre coppie pointer/mask.

## Potenziometri G e altri proprietari dei GPIO

Il G usa PB1 e PC6..9 per controlli analogici/multiplexer. Non esiste ancora una
mappa elettrica MINI dimostrata per questi controlli. La patch salta
l'inizializzazione G `0x020159C2..0x020159FC` e lascia zero il flag
`state+832`. Questo flag protegge sia il blocco periodico del pannello
`0x02015CC6..0x02016150`, sia il percorso `0x0200CE8E → 0x0200CDE0`.

Nei percorsi decodificati ciò esclude i writer `0x0201453A` (PB1/PC6..8),
`0x02014578` (pull di PB1), `0x0200CC1A` (PC9) e `0x0200CC40` (mux PC6..8).
L'inizializzazione dei dati RAM precedente al salto e l'aggiornamento finale
degli stati restano. I controlli analogici fisici ed eventuale expression
rimangono pendenti; i parametri DSP continuano a essere quelli dell'editor G.

Questa patch non sostituisce il driver GPIO condiviso `0x02004998`. Il preambolo
audio G su PC0/PC1/PC5/PA9 appartiene al port audio. I percorsi generici di
risparmio energetico a `0x0201D40E` e ripristino a `0x0201D95A` possono
riconfigurare interi port e richiedono una verifica separata dell'ownership
MINI. Il report non dichiara completata l'analisi di tutti gli alias o delle
chiamate indirette del binario.

## Prove e limiti

Il verificatore esegue le istruzioni reali dello stub, dell'init input, della
parte modificata del restore e della lookup logica originale usando un
interprete limitato e memoria Python. Le istruzioni non supportate causano un
errore; non esiste accesso MMIO reale. Verifica:

- 5 valori frame: una sola scrittura alla cache RAM, nessuna lettura o GPIO;
- 4 pattern iniziali GPIO: cambiano soltanto PA10/PA0/PA3, preservati PA1/PA2;
- 32 combinazioni di pressioni e altri bit di ingresso;
- 1024 coppie indice/byte di configurazione, sempre mappatura identity;
- 10 lookup fisico→logico nelle mappe G e MINI;
- 3 limiti di loop con target invariati, fonti errate rifiutate e inversione
  delle patch che recupera ogni byte del G originale.

Non vengono emulati l'intero IRQ, il task scheduler, l'elettronica o le
tempistiche di debounce. I quattro campioni del polling e i trenta campioni
dell'IRQ restano quelli del G; la loro durata sul MINI non è misurata. Il
confronto di riferimenti diretti comprende flash e RAM, ma una scansione
lineare può includere dati e non dimostra l'assenza di ingressi indiretti.

`hardware_verified`, `flashable` e la capacità pannello dell'app rimangono
`false`. L'adattamento è un componente verificato offline della candidata
completa, non una dichiarazione di avvio o di compatibilità fisica completa.
