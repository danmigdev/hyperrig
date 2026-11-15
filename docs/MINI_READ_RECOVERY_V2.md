# Recupero limitato delle query del writer

`tools/recover_mini_read_v2.py` aggiunge una composizione separata al client
operativo congelato. Non cambia il firmware RAM, il core dell'installer o il
recupero v1. Importare il modulo non apre dispositivi. L'esecuzione richiede
trasporto, factory di riapertura, journal persistente e sessione espliciti.

La terza installazione ha perso una risposta `FC7E`, dopo una lettura `FD7F`
riuscita. In quel punto `session.expected` contiene già il nuovo contatore di
lettura e il CRC dei byte ricevuti; il precedente audit ha ancora il contatore
vecchio. Confrontare sempre con il precedente audit sarebbe scorretto.

| Comando fallito con Win32 31 | Evidenza necessaria dopo riapertura | Risultato |
| --- | --- | --- |
| `FD7F` lettura NOR | Identità HYW1, audit identico nei 128 byte all'audit immediatamente precedente, già validato; tutti i campi uguali a `expected` | Una sola ripetizione della lettura; i contatori provano che la prima non ha avuto effetto |
| `FC7E` stato | Identità HYW1 e audit fresco uguale a tutti i campi correnti di `expected` | Una sola ripetizione della query, priva di effetti sul NOR o sui contatori |
| `FD88` audit | Identità HYW1 e audit fresco uguale a `expected` | Il record fresco viene restituito direttamente al normale validator dell'installer |
| `FD88` subito dopo risposta erase/program validata | Come sopra, con il solo incremento `status_polls` ammesso nell'intervallo 1..65536 già imposto dal core | L'installer riceve e valida il record; il wrapper non modifica i contatori attesi |

CRC, tag della build, slot, gate operativo, stato, token, sequenza, contatori,
bitmap, guardie e stato NOR devono essere validi. Un errore nel recupero termina
la sessione. `FD7F` eseguito ma con risposta persa cambia l'audit e resta un
errore terminale: questo strumento non nasconde una lettura già contabilizzata.

Il budget complessivo è esplicito, da 1 a 8 recuperi. Ogni combinazione di CDB e
stato atteso può usarlo una sola volta. La stessa chiamata non ricorre mai nel
recupero; un errore su identità, audit o ripetizione interrompe il percorso.
La riapertura deve usare la stessa classe di trasporto, path, slot e profilo.
Il runner deve applicare anche logging e pacing alla nuova istanza.

Erase, programmazione, arm, stage, echo, finish, upload, jump e reset non sono
ripetibili da questo wrapper. Un'altra eccezione, Win32 diverso da 31, comando
non inviato, identità diversa, audit incompatibile o journal non persistibile
interrompe la sessione. L'installer congelato resta responsabile dei confronti
esatti dei dati e di tutte le verifiche successive.

`python -B -m unittest tests.test_mini_read_recovery_v2 -v` esegue 20 test con
il vero core Python e un NOR simulato: perdita di risposte prima/dopo query,
audit dopo erase/PP, vincoli sui delta, errori nelle guardie e nell'identità,
esaurimento budget, errore durante il recupero e nessuna mutazione duplicata.
Non costituiscono una prova sul dispositivo. Il report separato
`research/mini-read-recovery-v2.json` vincola sorgenti e dipendenze congelate.

La causa Windows e la correlazione con le richieste automatiche sono descritte
in [MINI_WINDOWS_FAILURES.md](MINI_WINDOWS_FAILURES.md). Il recupero non pretende
di correggere il driver né dimostra l'affidabilità di una futura installazione.
