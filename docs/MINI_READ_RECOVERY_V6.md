# Budget finito di 32 recuperi per il writer

`tools/recover_mini_read_v6.py` espone
`BoundedCommandRecoveryTransport`, sottoclasse diretta del wrapper v5.
Accetta `max_recoveries` intero da1 a32, con default32. Esegue tutte le
inizializzazioni originali con `min(max_recoveries,8)`, poi assegna il
limite alla singola istanza. Non modifica variabili globali, writer C,
installer o wrapper precedenti.

La revisione risponde all'esaurimento reale del limite8 nell'ottava
installazione: il report completato
`analysis/hardware/mini-complete-install-run.json` registra otto recuperi
(due letture, una query, cinque audit) e il successivo Win32 31 che ferma
la sessione, con `mutation_completion_unknown=false`. Il suo SHA256 è
`53ba43c881e1bd812dbe1c922214693573171a98213fd1653f73218a0b20c188`.
Questo è il motivo dell'aumento; non è una prova hardware di v6.

Il limite32 copre una sola sessione writer, condiviso fra preimage,
installazione e verifica finale, e fra tutte le famiglie ammesse da v5.
Non introduce nuovi comandi recuperabili. `exchange`, tutte le witness,
i percorsi di recupero e `close` sono ereditati senza override:

- lo stesso comando/stato può usare una sola witness;
- il recupero richiede ancora Win32 31 submitted e tutte le verifiche v5;
- una riapertura, query o riemissione fallita non genera recuperi annidati;
- comandi eseguiti o ambigui non vengono ripetuti;
- ACK reali e audit/readback successivi restano obbligatori;
- OUT/STAGE, ARM, jump e reset non acquisiscono nuovi retry.

La trentatreesima richiesta di recupero termina prima di un'altra
riapertura. Il reader NOR indipendente mantiene il proprio limite8;
anche una nuova istanza v5 continua ad avere massimo8.

Il riepilogo espone versione6, `max_recoveries`,
`recovery_limit_scope`, `command_witness_policy_version=5`,
`command_witness_policy_unchanged_from_v5=true` e
`separate_NOR_reader_budget_unchanged=8`.

```powershell
python -B -X utf8 -m unittest tests.test_mini_read_recovery_v6 tests.test_mini_final_install_runner
```

79 test PASS:66 sul wrapper, inclusi i59 casi v5 riapplicati, e13
sull'orchestrazione del nono installer. Una prova attraversa tutte le
fasi con32 stati distinti:12 recuperi durante la preimage,10 durante
l'installazione e10 nella lettura finale. Un'altra si ferma al
trentatreesimo errore, prima di nuove operazioni. I test verificano anche
tipo/range del parametro, assenza di effetti sulle altre classi, riuso
della witness rifiutato, errori annidati terminali e PP/FINISH già eseguiti
non ripetuti con budget32.

`research/mini-read-recovery-v6.json` conserva hash, risultati e review.
Le prove v6 sono offline con NOR e handle simulati. Il limite maggiore
non qualifica la causa del Win32 31, non garantisce che bastino32 recuperi
e non attesta completamento del flash, avvio o audio.
