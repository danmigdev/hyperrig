# Riconciliazione dei comandi NOR non eseguiti

`tools/recover_mini_read_v4.py` espone
`AuditedCommandRecoveryTransport`, con la stessa interfaccia di costruzione
e `bind_session` del wrapper v3. Aggiunge soltanto FC7B/erase e FC7D/program
quando falliscono con Win32 31 dopo submission e una lettura fresca prova
che la sequenza non è stata consumata. Writer, installer e wrapper v1..v3
restano invariati. Importare il modulo non apre dispositivi.

Il writer consuma `state.sequence` nel dispatcher prima di `run_job`,
quindi prima dei controlli NOR e di WREN. Un errore prima di WREN può
avere contatori ancora invariati, ma la sequenza risulta già diversa.
Non basta perciò confrontare WREN/erase/program: è obbligatoria l'identità
di tutti i128 byte dell'audit precedente.

Prima della riapertura vengono richiesti:

- installer attivo, preimage interamente verificata, settore pendente e
  operazione mutante marcata incerta;
- FD88 immediatamente precedente, identico al record già validato dal core;
- stato STAGED, echo verificato, guardie integre, CRC pagina della candidata;
- stesso token/indirizzo e sequenza richiesta uguale alla precedente+1;
- stato atteso host invariato rispetto all'audit salvo quel solo incremento.

Il primo PP dopo erase mantiene il CRC dell'ultima lettura della NOR
cancellata in `last_crc32`: non viene confuso con il CRC della pagina
congelata, che resta verificato separatamente contro la candidata.

La riapertura usa lo stesso backend/slot/percorso, FC78 e FD88. Il record
fresco deve essere identico byte per byte al precedente, compresi CRC,
stack, contatori e flag. Qualunque delta termina la procedura, anche se
sembra indicare un'operazione completata correttamente. Nessun ACK viene
dedotto dall'audit o sintetizzato.

Solo con stato identico viene reinviato una volta lo stesso CDB. Il
risultato deve essere un ACK reale con opcode, fase, token, nuova sequenza
e CRC corretti. Il core originale aggiorna poi i propri contatori e
richiede il normale audit di completamento, inclusi i polling WIP. Il
wrapper non cancella `mutation_completion_unknown`: lo fa soltanto il
core dopo tale verifica. Un errore nel reinvio non apre un altro recupero.

Il budget totale rimane8, condiviso con i percorsi v3. Non vengono
reinviati OUT/STAGE, ARM, FINISH, jump o reset. Il contatore
`mutation_request_reissues` descrive richieste ritenute non eseguite;
`completed_NOR_mutations_repeated=0` descrive le mutazioni completate
che questo wrapper non ripete. `mutation_retries_allowed=true` è ora
dichiarato insieme alla condizione esatta, senza riusare il precedente
claim assoluto di v3.

## Prove offline

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v4 tests.test_mini_read_recovery_v3 tests.test_mini_read_recovery_v2 tests.test_mini_read_recovery tests.test_mini_app_install tests.test_mini_quiet_install_runner
```

134 test PASS, di cui47 sul modulo v4, inclusi casi precedenti riapplicati.
Sono verificati erase e PP non eseguiti, header ultimo, ACK reale, audit
successivo obbligatorio, operazione già eseguita rifiutata, sequenza
consumata senza WREN, ogni word modificata, CRC corrotto, candidata
diversa, budget condiviso ed errori di logger/riapertura senza replay.

Otto ulteriori casi ASan/UBSan includono direttamente il C operativo
congelato. I callback WREN simulati leggono la sequenza interna e
richiedono che sia stata incrementata prima della chiamata. Le prove
coprono anche fallimento preimage prima di WREN, fallimento WREN,
programmazione parziale simulata e reinvio di un CDB già eseguito:
quest'ultimo viene rifiutato senza un secondo WREN.

```powershell
New-Item -ItemType Directory -Path build/mini-read-recovery-v4 -Force | Out-Null
wsl.exe --distribution Ubuntu --exec gcc -std=c99 -Wall -Wextra -Werror -O1 -g '-fsanitize=address,undefined' -fno-sanitize-recover=all -DHYPERRIG_WRITER_HOST_MUTATIONS -Ifirmware/mini/app_writer -Ibuild/mini-app-writer-operational tests/test_mini_read_recovery_v4.c -o build/mini-read-recovery-v4/host-sequence
wsl.exe --distribution Ubuntu --exec build/mini-read-recovery-v4/host-sequence
```

`research/mini-read-recovery-v4.json` conserva gli hash e le verifiche.
Nessuna prova hardware è stata eseguita da questa revisione. La
riconciliazione dimostra lo stato osservato dopo il fallimento; presuppone
lo stesso writer identificato e richieste sincrone senza operazioni
concorrenti dell'host. Non prova la causa di Win32 31 né l'assenza di
interferenze del driver, non garantisce disponibilità USB o completamento
del flash e non qualifica avvio/audio. Una mutazione eseguita o incerta
continua a richiedere ispezione separata.
