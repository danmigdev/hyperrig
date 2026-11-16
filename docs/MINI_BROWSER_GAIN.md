# Trial grafico GAIN del MINI

`tools/probe_mini_browser_gain.py` prepara una prova strettamente limitata del
vero editor generato. Il comando senza opzioni stampa soltanto il piano: non
legge prove, non avvia server o browser, non enumera dispositivi. In questa
consegna sono stati eseguiti soltanto test offline; non esiste un esito fisico
del trial GAIN.

La prova eseguita usa un nuovo profilo Chromium e il server localhost, CDP e
chooser dei moduli readonly già congelati. Seleziona soltanto il COM della
prova PONG fornita, richiede VID:PID `3654:5155` prima dell'unica apertura a
115200 baud e non permette reconnect. USB diretto, Bluetooth e MIDI sono
inibiti. Nessun file dell'editor viene modificato.

## Prerequisiti

- Una **nuova** manifest della candidata `3b0eac3b…00a78ff`, con qualifica
  fisica USB read e famiglia `GAIN`, senza permesso write generale, panel o
  famiglie BLE. La manifest frozen `audio-v2` resta immutata.
- Il report fisico first-preset referenziato dalla manifest, con roundtrip
  GAIN terminato, preset intenzionalmente conservato e traccia conclusa da
  `port_closed`. Il loader originale delle famiglie ripete il replay dei byte
  della traccia; i flag di un mock non bastano.
- `browser-evidence.json` con COM/PONG esatti e SHA256, riferito alla medesima
  qualifica USB. La prova precedente deve aver chiuso la seriale e nessun
  altro programma deve averla riaperta.
- Editor generato da quella manifest: HTML e script sono confrontati con la
  derivazione originale. Il guadagno ripristinato dalla prova first-preset deve
  avere uscita maggiore di `-30 dB`.

Il binder precedente richiede prove held/released. Un eventuale nuovo binder
di avvio normale deve registrare esplicitamente che il recupero con tasti non
è stato provato; questo strumento non fabbrica una prova held né cambia quel
binder. L'editor USB readonly già disponibile è indipendente da questo trial.

## Comandi, da eseguire soltanto dopo la qualifica reale

I percorsi seguenti sono esempi di nuovi output; i file di prova devono già
esistere ed essere reali. Il preflight non avvia browser o dispositivi.

```powershell
python -B -X utf8 tools/probe_mini_browser_gain.py

$evidenceHash = (Get-FileHash -Algorithm SHA256 build/hyperrig-mini-usb-qualified-01/browser-evidence.json).Hash.ToLowerInvariant()
python -B -X utf8 tools/probe_mini_browser_gain.py --check-only `
  --firmware-manifest build/hyperrig-mini-usb-qualified-01/firmware-families.json `
  --family-report build/mini-first-preset-01/report.json `
  --evidence build/hyperrig-mini-usb-qualified-01/browser-evidence.json `
  --evidence-sha256 $evidenceHash `
  --app-dir build/hyperrig-mini-usb-qualified-01/editor/web
```

Per la prova fisica, sostituire `--check-only` con `--execute` e aggiungere un
percorso nuovo, per esempio `--output build/mini-browser-gain-01`. Non usare
questo comando mentre un altro helper comunica col pedale.

## Sequenza verificata dal guard

1. PONG esatto e letture iniziali dell'app; letture fresche `GAIN`, `LVL`,
   `FXS`, `PLIST`, `SNAPS` tramite la coda originale.
2. Confronto con lo stato finale della prova first-preset. `GAIN` e `LVL`
   devono coincidere; catena, inventario preset e scena devono essere gli
   stessi. Controllo del valore in `S.gain` e nell'attributo ARIA del vero
   selettore `#gOut .knob[role="slider"]`.
3. Apertura del popup `#meters`, focus sul selettore Output, eventi CDP
   `keyDown`/`keyUp` `ArrowDown`. Il listener dell'editor produce l'unico
   `GAIN in out-1` ammesso. Il guard esige un evento trusted sul selettore
   corretto e registra l'origine UI prima di lasciar passare la scrittura.
4. ACK reale esatto e nuove letture complete. Soltanto dopo questi controlli
   viene armato `ArrowUp`, che invia `GAIN in out` attraverso lo stesso
   listener dell'editor.
5. Nuove letture devono mostrare lo stato iniziale. La normale disconnessione
   dell'app deve completare il `close()` nativo della porta; controllare solo
   `SerialTransport.isOpen()` non basterebbe perché il frontend intercetta
   alcuni errori di chiusura.

Il guard alla funzione di scrittura blocca ogni altra mutazione, comandi GAIN
duplicati o fuori ordine, framing aggiuntivo e tentativi di ripetere un
comando fallito. Non esegue `PSAVE`, `SNAPSAVE`, `PDEL` o comandi firmware.
I tentativi automatici dell'editor di usare `LVLSUB`/`BLEKEY`, già negati
localmente dal profilo MINI, sono registrati separatamente e non trattati
come risposte del dispositivo.

`report.json`, scritto una volta dopo la chiusura del browser, contiene
hash degli input e sorgenti, screenshot prima/durante/dopo, eventi UI,
scritture ASCII e byte TX, byte RX del reader nativo, righe e risultati della
coda originale, letture prima/dopo e prova della chiusura nativa. Un errore
interrompe la sequenza: non avviene un ripristino automatico non verificato.
Se l'errore segue la prima modifica, il report può quindi mostrare un'uscita
ancora ridotta di 1 dB.

La strumentazione prova il percorso editor→protocollo→readback; non è
un'autenticazione contro modifiche malevole della pagina. Una qualifica
riuscita non dimostra audio analogico, BLE o persistenza dopo spegnimento.
La persistenza resta documentata separatamente dal trial first-preset.

## Test offline

```powershell
python -B -X utf8 -m unittest tests.test_mini_browser_gain -v
node tests/mini_browser_gain_guard_test.js tools/mini_browser_gain_guard.js
```

Dieci test Python e 120 condizioni del guard JS passano con porte e tasti
finti. Coprono replay delle prove, derivazione esatta dell'app, default senza
I/O, letture incomplete/incoerenti, origine UI, ordine e duplicati delle
mutazioni, ACK errato, ripristino senza lettura fresca e chiusura fallita.
Questi risultati non vengono pubblicati come evidenza hardware.
