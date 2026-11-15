# Recupero FINISH con sequenza non consumata

`tools/recover_mini_read_v5.py` espone `FinishCommandRecoveryTransport`,
con costruttore e `bind_session` compatibili con v4. Aggiunge soltanto
FC80/FINISH dopo Win32 31 submitted. Il budget di otto recuperi resta
condiviso con letture, query, echo e richieste erase/program ereditate.
Importare il modulo non apre dispositivi. Writer, installer e v1–v4 sono
immutati.

FINISH non emette WREN, erase o page program. Il dispatcher del writer
consuma la sequenza prima di `run_job`; il ramo FC80 controlla lo stato
NOR, rilegge 4096 byte, confronta il CRC del settore e solo allora pone
`phase=5`, `token=0`, `erased=0`. Anche un errore di stato o una lettura
parziale lascia la sequenza consumata. Il contatore WIP non aumenta.

Nell'ELF operativo A congelato, la scrittura della sequenza è a
`0x01C2097C`, prima della chiamata `run_job` a `0x01C20980`. L'origine C
è `firmware/mini/app_writer/writer.c:268`; il ramo FINISH è a riga183.
Gli hash di C, derivazione operativa ed ELF sono nel report associato.

Il client incrementa soltanto `expected.sequence` prima di FC80.
L'ultima PP è già stata verificata: `mutation_completion_unknown` deve
essere falso. FINISH non viene riclassificato come mutazione della NOR.

Il recupero richiede:

- installer attivo, preimage verificata e settore corrente del piano;
- FD88 immediatamente precedente, identico all'audit già validato;
- sequenza precedente34 e richiesta35, `phase=3`, bitmapFFFF,
  staged0/echoed0, guardie integre e NOR identificata;
- stato host identico all'audit salvo il solo incremento di sequenza;
- ultima pagina nell'ordine del piano, echo e readback identici alla
  candidata, CRC pagina e CRC dei settori vecchio/nuovo coerenti;
- stesso CDB, token e indirizzo del FINISH pendente.

La riapertura usa il backend già scelto, lo stesso slot/percorso, FC78 e
FD88. Tutti i128 byte freschi devono coincidere con l'audit precedente,
compresi stack, CRC e contatori. Qualunque differenza ferma il recupero,
anche se mostra un FINISH completamente riuscito. Nessuna sequenza,
flag o contatore del client viene modificato dal wrapper.

Solo allora viene reinviato una volta il CDB originale. Occorre un ACK
reale FC80 con errore0, fase5, token0, sequenza35 e CRC settore atteso.
Il client originale esegue poi il proprio audit: +4096 byte letti,
contatori WREN/erase/program/poll invariati e stato coerente. Seguono
la rilettura del settore e la verifica finale dell'applicazione.
Una risposta errata, un fallimento durante il recupero o una discrepanza
nel successivo audit terminano la sessione; non parte un secondo recupero.

Il riepilogo distingue `finish_request_reissues` da
`mutation_request_reissues`. `completed_FINISH_requests_repeated=0` e
`synthetic_FINISH_ACK=false` descrivono il comportamento ammesso.
OUT/STAGE, ARM, jump e reset non ricevono nuovi percorsi di retry.

## Verifiche offline riproducibili

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v5 tests.test_mini_complete_install_runner
```

72 test PASS:59 sul wrapper, inclusi tutti i47 casi v4 riapplicati,
e13 sull'orchestrazione dell'ottavo installer. Coprono FINISH non
eseguito sul settore normale e su quello dell'header, richiesta già
completata, sequenza consumata con lettura parziale, ogni word dell'audit
modificata, CRC errato, piano/stato cambiati, ACK reale, audit successivo,
budget condiviso e fallimenti di log/riapertura senza replay.

Il test contiene inoltre `NATIVE_FINISH_HARNESS`, che include direttamente
il C operativo congelato. Le callback simulate di status e lettura
richiedono la sequenza35 già consumata. Sette casi ASan/UBSan verificano
completamento, replay rifiutato e fallimenti di status, prima lettura,
lettura intermedia, CRC e bitmap; nessuno emette nuove operazioni NOR
mutanti durante FINISH.

```powershell
python -B -X utf8 -c "from pathlib import Path; from tests.test_mini_read_recovery_v5 import NATIVE_FINISH_HARNESS; p=Path('build/mini-read-recovery-v5'); p.mkdir(exist_ok=True); (p/'verify_finish.c').write_text(NATIVE_FINISH_HARNESS,encoding='utf-8')"
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational build/mini-read-recovery-v5/verify_finish.c -o build/mini-read-recovery-v5/host-finish
wsl.exe --distribution Ubuntu --exec ./build/mini-read-recovery-v5/host-finish
```

Richiede il build operativo originale già generato e GCC con sanitizers
nella distribuzione WSL Ubuntu. Non ricompila né modifica il payload
target. `research/mini-read-recovery-v5.json` conserva hash e risultati.

Queste prove sono offline. L'audit attesta lo stato osservato dopo il
fallimento, assumendo lo stesso writer identificato e richieste host
serializzate; non dimostra la causa del Win32 31 né l'assenza di una
coda pendente nel driver. Nessun FINISH eseguito o ambiguo viene
ricostruito come ACK. Non sono prove di flash completato, boot o audio.
