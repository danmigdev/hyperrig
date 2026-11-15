# Recupero limitato dell'echo FD87

`tools/recover_mini_read_v3.py` estende il wrapper v2 senza modificarlo.
Importare il modulo non enumera né apre dispositivi. Il coordinatore deve
fornire trasporto già identificato, logger durevole e riapertura esplicita
dello stesso backend; la classe resta `ReadOnlyStateRecoveryTransport`.

La sola nuova operazione recuperabile è un FD87 da 256 byte che fallisce con
Win32 31 dopo la submission. Deve seguire immediatamente l'audit validato
dello staging, durante un'installazione con preimage interamente verificata.
Token, sequenza dello staging, indirizzo e CRC devono coincidere con la
pagina della candidata immutabile già posseduta dall'installer.

Il ramo FD87 del C congelato, `writer.c:257..265`, controlla staging, fase,
token, sequenza, indirizzo, guardie RX e CRC della copia congelata. Poi invia
quella copia e può impostare `echoed=1`. Non chiama `run_job`, non accede
alla NOR e non consuma una sequenza. La build operativa deriva lo stesso
ramo cambiando soltanto il macro del gate; nell'ELF A, a `0x01C207F6`
compare la chiamata `send_data`, seguita a `0x01C207FE` dallo store di
`echoed`. Il ritorno è a `0x01C2081E`. Non è ammessa una variazione del
watermark dello stack: `stack_used` viene assegnato dentro `run_job`.

Dopo la riapertura, FC78 deve identificare lo stesso HYW1 gate1 e FD88
deve restituire un audit valido. I 128 byte devono essere identici al
precedente salvo la word `echoed` a offset104, che può essere zero oppure
uno, e il CRC del record a offset120. Guardie, stato NOR, contatori,
sequenza, CRC pagina e uso dello stack restano invariati. Un callback
send negativo rende il writer fallito: il nuovo audit lo rifiuta.

Solo allora viene reinviato **lo stesso CDB FD87 una volta**. La risposta
deve essere `bytes`, lunga256 e identica a tutti i byte della pagina della
candidata; viene ricontrollato anche il CRC. Il wrapper non aggiorna lo
stato atteso dell'installer e non genera risposte: il core originale
confronta nuovamente l'echo e richiede il suo normale audit successivo
prima di proseguire con erase/program.

Il flag `echoed=1` prova che il ramo target ha accettato il risultato del
proprio callback, non che l'host abbia ricevuto la prima risposta. Proprio
per questo la seconda risposta deve essere verificata integralmente.

Il budget totale rimane massimo8, condiviso con i recuperi v2 di FC7E,
FD88 e FD7F. Un errore durante identità, audit o reinvio termina il
recupero; lo stesso CDB/stato non può aprirne un secondo. OUT/STAGE, ARM,
erase, program, FINISH, jump e reset non sono ripetuti. Un FD7F già
eseguito mantiene il rifiuto v2 quando il contatore letture è cambiato.

## Verifiche locali

La suite usa il vero installer Python con handle/NOR simulati. Include
echo perduto prima e dopo esecuzione, prima dell'erase e a metà settore,
alterazioni di ciascuna word del record, risposta corta/corrotta, audit
successivo del core, errore del logger, budget misto e nessuna ripetizione
di operazioni mutanti. Il report è
`research/mini-read-recovery-v3.json`.

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v3 tests.test_mini_read_recovery_v2 tests.test_mini_read_recovery tests.test_mini_app_install tests.test_mini_quiet_install_runner
```

Risultato:87 test PASS, inclusi33 test v3. Separatamente, otto casi sul C
operativo congelato con ASan/UBSan verificano echo ripetuto, stato/audit
invariati salvo `echoed`, callback send negativo, sequenza errata,
guardia corrotta e separazione fra RX e pagina congelata. Il mock conta
tutti i callback NOR: nessuno viene chiamato dall'echo. Per riprodurre
quest'ultima prova su Windows con il WSL già usato dal progetto:

```powershell
New-Item -ItemType Directory -Path build/mini-read-recovery-v3 -Force | Out-Null
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational build/mini-app-writer-operational/writer.c tests/test_mini_read_recovery_v3.c -o build/mini-read-recovery-v3/host-echo
wsl.exe --distribution Ubuntu --exec build/mini-read-recovery-v3/host-echo
```

Queste sono prove offline. Non provano la causa di Win32 31, non garantiscono
la disponibilità del trasporto e non attestano completamento dell'installazione,
avvio firmware o audio. Non è stato eseguito alcun comando sul dispositivo
durante questa revisione; writer, v2 e installer restano congelati.
