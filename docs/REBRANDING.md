# Pacchetti locali HyperRig

La richiesta di rinominare firmware e applicazioni è applicata alle copie
derivate prodotte in `build/hyperrig/`. I campioni pubblicati dal progetto
originale rimangono in `artifacts/` per verificare hash, indirizzi e risultati
del reverse engineering. Licenze, attribuzioni e riferimenti di provenienza
restano riconoscibili come tali.

## Risultati

| File/cartella locale | Contenuto |
|---|---|
| `build/hyperrig/HyperRig-alpha11-v1-win.zip` | Pacchetto G/B v1, installer Windows e firmware rinominati |
| `build/hyperrig/HyperRig-alpha11-v2-win.zip` | Pacchetto G/B v2, installer Windows e firmware rinominati |
| `build/hyperrig/HyperRig-local-android.apk` | App `com.hyperrig.app`, etichetta HyperRig e icona H |
| `build/hyperrig/web/tankg.html` | Editor web HyperRig |
| `build/hyperrig/windows/` | Pacchetti Windows già estratti |
| `build/hyperrig/rebranding-report.json` | SHA-256 delle copie e dei campioni di origine |

Questi pacchetti derivano da UltraRig per **TANK-G/TANK-B**. Non sono il port
per TANK MINI. Il port nativo è separato in `firmware/src/hyperrig_dot.c` e
`hyperrig_head.c`, con API `hyperrig_*`; resta incompleto.

## Cosa viene modificato

Il firmware viene prima decodificato. Le sostituzioni ASCII/UTF-16 conservano
la lunghezza: UltraRig e HyperRig hanno entrambi otto caratteri. I CRC di ogni
payload modificato, della directory JLFS e dell'area applicativa vengono
ricalcolati; l'area viene poi ricodificata SFC e riletta per controllarla.
Indirizzi, dimensioni e mappa flash rimangono quelli del relativo campione G/B.
I metadati JSON ricevono gli hash nuovi. Non viene inventato l'hash di una
flash completa che non è stata prodotta.

L'installer Windows viene trattato come archivio PyInstaller: codice Python
3.12 e costanti vengono letti come dati, nomi e testi vengono rinominati,
PYZ e CArchive ricostruiti. Gli opcode e le tabelle delle eccezioni dei moduli
vengono confrontati con gli originali. L'installer non è stato avviato per
questa verifica e la sua operatività con un pedale non è stata provata.

L'app Android viene decodificata e ricostruita con
[Apktool](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3): manifest,
package, classi Smali, risorse, bridge nativo e pagina web usano HyperRig.
La ricostruzione DEX aggiorna gli indici delle stringhe e i checksum. Un nuovo
vettore H è usato come icona. L'APK contiene anche LICENSE, NOTICE e licenze
dei componenti originali tra gli asset.

La firma viene creata con una chiave **locale di sviluppo**, distinta da quella
del produttore originale, e verificata con
[Uber APK Signer](https://github.com/patrickfav/uber-apk-signer/releases/tag/v1.3.0).
La verifica ha confermato allineamento e firme APK v2/v3. La chiave si trova
in `build/signing/`, esclusa da Git; non è una chiave di pubblicazione.
L'app non è stata installata su un telefono durante questa sessione.

Anche prefissi di file, chiavi applicative e identificatori dei formati che
contengono il nome originale vengono rinominati: la compatibilità con file
esportati da UltraRig non è automaticamente garantita. Endpoint del vecchio
progetto per telemetria, aggiornamenti e donazioni sono sostituiti con il
dominio riservato `hyperrig.invalid`; non viene attribuito al fork un sito o
un servizio di supporto inesistente. I riferimenti M-VAVE per il ripristino e
le licenze dei componenti restano quelli originali.

## Riprodurre

Servono i pacchetti fissati in `research/input-manifest.json`, Python 3.12
e, per Android, Java con `keytool`. Le versioni degli strumenti e i relativi
hash sono in `research/sources.lock.json`.

```powershell
python tools/rebrand.py
python tools/rebrand.py --android --keytool "C:/Program Files/Android/Android Studio/jbr/bin/keytool.exe"
python -m unittest discover -s tests -v
```

Il primo comando produce Windows e web; il secondo aggiunge Android. La
directory `build/android-hyperrig` conserva Smali e risorse ricostruibili.
Lo script non pubblica pacchetti, non esegue installer e non accede al pedale.

Validazione locale: 54 test superati, compresi CRC delle quattro immagini,
integrità del bytecode Windows, checksum DEX, identità e risorse Android.
I quattro script inline delle due pagine web controllate passano `node --check`.
La decodifica dell'APK finale conferma `com.hyperrig.app` e la nuova icona.
La ricerca del vecchio nome nei payload prodotti non trova occorrenze di
prodotto; restano le attribuzioni e la documentazione di derivazione.
