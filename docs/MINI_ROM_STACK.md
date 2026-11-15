# Stack privato per il probe ROM HyperRig

Il bridge in `firmware/mini/rom_stack/rom_stack_pi32v2.S` permette al nuovo
probe DSP di eseguire una normale funzione C su uno stack privato e di
riprendere lo stack della ROM prima di chiamare nuovamente i servizi USB.
Misura **24 byte, nove istruzioni**, senza rilocazioni. Non è un punto di
ingresso ROM e non costituisce un firmware o un payload autonomo.

```c
int hyperrig_mini_rom_run_on_stack(int (*callback)(void *),
                                 void *argument, void *stack_top);
```

Gli argomenti occupano `r0`, `r1`, `r2`; il risultato del callback torna in
`r0`. Il chiamante deve riservare e controllare lo stack, con `stack_top`
all'estremo superiore escluso e allineamento minimo di quattro byte.
Il probe usa un allineamento di otto byte e riserva 4096 byte. Il bridge
non valida puntatori, capacità o sovrapposizioni: questi controlli appartengono
al linker e al verificatore del payload che lo incorpora.

| Offset | Byte | Istruzione | Effetto |
|---:|---|---|---|
| `00` | `74 04` | `[--sp] = {rets, r4}` | Salva otto byte sullo stack entrante |
| `02` | `64 e0 00 4e` | `r4 = sp` | Conserva il puntatore al frame entrante |
| `06` | `03 16` | `r3 = r0` | Conserva il puntatore al callback |
| `08` | `64 e0 80 2e` | `sp = r2` | Seleziona lo stack privato |
| `0c` | `10 16` | `r0 = r1` | Passa l'argomento al callback |
| `0e` | `c3 00` | `call r3` | Invoca una normale funzione C |
| `10` | `64 e0 80 4e` | `sp = r4` | Riprende il frame sullo stack entrante |
| `14` | `34 04` | `{rets, r4} = [sp++]` | Ripristina SP, RETS e r4 |
| `16` | `80 00` | `rts` | Torna al chiamante originale |

Il callback deve preservare `r4..r15`, terminare con un normale ritorno e
non cambiare modalità di esecuzione o stack. Non deve chiamare i servizi
ROM dal nuovo stack: il probe invia la risposta USB soltanto dopo il ritorno.
Il bridge preserva il valore entrante di RETS oltre all'indirizzo di ritorno;
le condizioni aritmetiche e i registri temporanei `r1..r3` possono cambiare
come in una normale chiamata C.

## Evidenza e verifica

La toolchain JieLi fissata alla versione `20260730.1`, con `-target pi32v2
-mcpu=r3`, assembla le istruzioni nella tabella. Il verificatore decodifica
anche i byte con la tabella ISA locale e richiede esattamente questa sequenza.
La build di un piccolo esempio C con `__builtin_alloca` produce autonomamente
`r7 = sp`, uno spostamento di SP, `call r3`, `sp = r7` e il recupero del frame.
Il compilatore quindi usa già lo stesso schema di registro preservato per
salvare uno stack mobile. Il file generato è
`build/mini-rom-stack/abi_frame.asm`.

Le prove originali del compilatore in
[`pi32v2-isa/docs/ABI.md`](../upstream/pi32v2-isa/docs/ABI.md), sezioni 6.2–6.3,
documentano il layout del frame: RETS si trova a `sp_entrante-4`, il registro
salvato a `sp_entrante-8`. La stessa fonte documenta registri preservati,
argomenti, risultato e allineamento. Il runner ROM di riferimento
[`runner.S`](../upstream/pi32v2-isa/tools/hwtest/runner.S) salva lo stack
entrante, esegue casi con un altro SP e torna sullo stack del runner.
Questi riferimenti sono fissati nel lock del progetto e i loro hash entrano
nel report; non sostituiscono una misura sul MINI di questo nuovo bridge.

```powershell
python tools/verify_mini_rom_stack.py
```

Risultato: **240 simulazioni di istruzioni e cinque casi negativi**. Il
modello verifica entrambi gli slot, quattro posizioni dello stack entrante,
cinque profondità del callback fino a 4096 byte e tre valori di ritorno.
Controlla i registri preservati, il ritorno, il solo frame di otto byte
sullo stack entrante e il contenimento delle scritture nello stack privato.
Prova separatamente le due possibili interpretazioni di SP come alias di
SSP o USP; non determina quale sia usata dal silicio in questo contesto.

L'effetto del callback nel simulatore è **un modello che assume il rispetto
dell'ABI**, non l'esecuzione del motore DSP. Il test negativo di overflow
dimostra il controllo del modello, non una protezione implementata sul target.
La profondità della call chain DSP e il controllo dei canary appartengono
alla verifica separata del probe `rom_engine`. I 1228 byte della funzione
di inizializzazione, da soli, non dimostrano che l'intera catena entri in 4 KiB.

Gli ELF `build/mini-rom-stack/audit-*.elf` sono soltanto fixture di link e
**non devono essere caricati sul dispositivo**. Riservano una guardia di
32 byte seguita dallo stack di 4096 byte alla fine di ciascuno slot. La
funzione importabile `validate_stack_layout(base, code_end, guard, bottom,
top)` verifica questo contratto; `code_end` deve includere tutti i dati e
la BSS che precedono la guardia, non soltanto il codice.

## Stato interrupt e memoria della ROM

Il bridge non emette scritture esplicite a SSP, USP, ICFG, registri di
eccezione, clock, cache o periferiche, né `cli`, `sti` o `rti`.
**Non ne consegue che SSP resti fisicamente immutato:** SP può essere un
alias dello stack attivo. Il contratto è il ripristino dello SP entrante,
senza cambiare esplicitamente modalità o politica degli interrupt.
Il comportamento dell'IRQ durante la finestra sullo stack privato,
l'eventuale annidamento e lo stato nascosto dei loop restano da verificare.
Nessun test host li simula.

I due intervalli utilizzati come slot ROM sono:

| Slot | Intervallo esclusivo superiore | Vincolo |
|---|---|---|
| A | `[0x01C20000, 0x01C28000)` | Codice, dati, BSS e stack del plug-in nello stesso intervallo |
| B | `[0x01C28000, 0x01C30000)` | Come A; non sovrascrivere lo slot del gestore attualmente attivo |

La [specifica primaria m-bootloader](../upstream/m-bootloader/docs/SPEC.md),
sezioni 2.1, 10.1 e tabella finale delle limitazioni, dichiara sconosciuti
i confini esatti della RAM posseduta dalla ROM. Il contratto dei plug-in
mantiene quindi ogni allocazione privata dentro il proprio slot da 32 KiB.
Il backup NOR prova i contenuti della flash, non l'occupazione dinamica RAM.
Una lettura RAM piena di zeri non dimostra che la regione sia libera.

Gli intervalli più ampi descritti nella sezione delle applicazioni standalone
della stessa specifica si riferiscono a uno stage che possiede il sistema.
Per l'ingresso diretto `run-ram` quel percorso smonta l'ambiente ROM e termina
con un reset: non offre ritorno alle callback USB ROM. Analogamente, le regioni
`0x01C30000` in avanti del runner `--app` sono lasciate libere da una specifica
applicazione di test, non da una ROM generica. **Non è provata altra RAM libera
per un plug-in MINI che debba restituire alla ROM.**

Nessun comando USB, reset, accesso al pedale o scrittura NVM viene eseguito
dal verificatore. Il report
[`mini-rom-stack.json`](../research/mini-rom-stack.json) mantiene
`hardware_execution_verified: false` finché una prova separata non osserva
il bridge fisico nel nuovo probe.
