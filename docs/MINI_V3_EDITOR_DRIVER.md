# Adattatore locale delle prove v3

`tools/run_mini_v3_editor.py` delega ai launcher congelati. Non modifica file,
protocollo seriale, guard o permessi dell'app. Nel solo modulo desktop sostituisce
temporaneamente il lettore dei file di prova: due trace chiusi già presenti nei
pin del boot ricevono un limite di 32 MiB, con dimensione e SHA256 obbligatori.

| File in `analysis/hardware/` | Byte | SHA256 |
|---|---:|---|
| `mini-pc-limit-install-trace.jsonl` | 17590011 | `2258850d612c9971e251fdcc581db0dc97b2e6cb3f355cd015e204624ea7bde4` |
| `mini-complete-install-trace.jsonl` | 10133042 | `8561aff779032f599f6aa4590b8f8ae2c1b60a58bc2fda67911d6f62914bc501` |

Ogni altra lettura conserva il limite originale di **8 MiB**. Hash errato,
file troncato o percorso diverso non ottengono l'eccezione. I riferimenti in
memoria vengono ripristinati al termine. I nuovi `session.json` e `report.json`
registrano `evidence_io_extension` e l'hash del driver in `source_sha256`, senza
alterare `prepared`, `inputs` o le prove precedenti.

Preflight reale, senza browser/dispositivo:

```powershell
python -X utf8 tools/run_mini_v3_editor.py desktop --check-only --boot-run analysis/hardware/mini-first-boot-v11-released-run.json --boot-sha256 8b91a906bd061952938ce54930eb8d5e0956ace4c4d4465fd8a57da735d88202
```

Per l'avvio autorizzato sostituire `--check-only` con `--execute` e aggiungere
`--output build/mini-desktop-v3-02`, directory nuova. Il sottocomando
`first-preset` inoltra gli stessi argomenti documentati in
[MINI_BROWSER_FIRST_PRESET.md](MINI_BROWSER_FIRST_PRESET.md) al trial congelato;
il validator e il trial condividono il medesimo modulo desktop adattato.

Verifica: `python -X utf8 -m unittest tests.test_mini_v3_editor_driver -v`.
Nove test offline, inclusi i due trace reali e il preflight del vero boot v11;
nessun browser, porta seriale o dispositivo aperto dai test.
