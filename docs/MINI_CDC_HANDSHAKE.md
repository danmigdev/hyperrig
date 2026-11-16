# Primo collegamento CDC nella stessa apertura

`tools/probe_mini_app_cdc_handshake.py` è un nuovo diagnostico. Non modifica
i client v1 o i risultati precedenti. Riprende il ciclo originale dell'editor
`tankg.html:10351`: al massimo cinque PING, ciascuno con timeout 700 ms,
nella stessa apertura. DTR=true e RTS=false sono richiesti prima di aprire;
l'attesa iniziale è 1 secondo. Non ci sono riaperture o commutazioni di linea.

```powershell
python tools/probe_mini_app_cdc_handshake.py --check-only --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-handshake-new.jsonl --queries
python tools/probe_mini_app_cdc_handshake.py --execute --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-handshake-new.jsonl --queries
```

La ripetizione richiede una prova precisa: un'unica scrittura nativa completata
di tutti i cinque byte, almeno una lettura dopo la scrittura, zero byte RX
in tutto il tentativo e soltanto il timeout vuoto della risposta. Byte parziali,
testo inatteso, errori di trasporto, scrittura incompleta o che consuma già il
timeout fermano la sessione. Byte tardivi durante il drain prima del prossimo
PING impediscono un altro invio. Il parser fallito non viene riabilitato.

Il nuovo JSONL conserva numero del tentativo, intent/esito nativo TX, byte RX,
motivazione della ripetizione, identità e chiusura. Un PONG tardivo non viene
attribuito causalmente a uno specifico invio. `automatic_retry=true` riguarda
esclusivamente questo handshake limitato; le successive letture consentite
non hanno retry e non esiste API di mutazione. `--queries` vuoto richiede solo
il collegamento; senza l'opzione seguono le letture standard dopo il PONG.
Nessun completamento viene dichiarato prima della chiusura della porta.

Il default e `--check-only` non enumerano dispositivi. I test sono simulati,
non dimostrano che il MINI risponda fisicamente. DTR richiesto non equivale
alla prova della consegna del corrispondente control transfer USB.
