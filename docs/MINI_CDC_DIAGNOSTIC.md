# Diagnostico CDC con DTR attivo

Il nuovo `tools/probe_mini_app_cdc.py` lascia immutati i client e i log storici.
Usa il manifesto indicato, verifica il relativo file firmware e richiede la
versione `tankm_fw` esatta nel PONG. Il PONG non attesta l'hash del binario.

```powershell
python tools/probe_mini_app_cdc.py --check-only --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-new-session.jsonl --queries
python tools/probe_mini_app_cdc.py --execute --port COM3 --firmware-manifest build/hyperrig-mini-audio-v3/firmware-manifest.json --log analysis/hardware/mini-cdc-new-session.jsonl --queries
```

`--queries` senza nomi invia soltanto PING. Senza l'opzione viene usato
l'insieme di letture del client originale. Nessun argomento accetta comandi
arbitrari, mutazioni, reset, retry o commutazioni delle linee.

L'apertura richiede DTR=true e RTS=false prima di `open`, attende 1 secondo
e invia un singolo PING con timeout 3 secondi. I byte TX/RX e gli errori sono
registrati in un nuovo JSONL; `session_complete` viene scritto soltanto dopo
la chiusura della porta. Default e `--check-only` non enumerano dispositivi.

L'handler originale CDC richiede DTR per abilitare RX/TX: gli otto frammenti
di `research/mini-cdc-host-open.json` sono identici anche nel firmware v3
`9c612d2c…e2363c`. I timeout del vecchio `probe_mini_app.py`, che richiede
DTR=false, non dimostrano un blocco del task applicativo. DTR=true resta una
precondizione, non una garanzia di risposta: il log attesta la richiesta del
client, non l'effettiva consegna del control transfer USB. I vecchi CLI
`probe_mini_app.py` e `probe_mini_app_host_open.py` restano congelati; il secondo
ha un preflight legato al v2 e non deve essere usato direttamente per il v3.
