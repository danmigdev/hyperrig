# Enumerazione WebSerial su Windows

Il selettore Chrome 157 può restare su “Finding devices” prima di aprire la
seriale. Nella revisione Chromium `0985600c06a688b9c669e74afde7dacd5aaed047`,
`SerialUsbDisplayNameWin` è abilitato per default: legge descrittori USB tramite
chiamate sincrone al driver hub per ricavare il nome della porta. Il percorso
alternativo usa le proprietà del dispositivo già registrate in Windows.
Fonti: [definizione del feature](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/public/cpp/device_features.cc)
e [enumeratore Windows](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/serial/serial_device_enumerator_win.cc).

`tools/mini_browser_windows.py` aggiunge soltanto `SerialUsbDisplayNameWin`
all'unico `--disable-features` esistente, esclusivamente su Windows. Il probe
saved-reload v2 e il launcher normale registrano gli argomenti effettivi, il
motivo e l'hash dell'helper prima di avviare il processo isolato. Permessi,
identificazione VID/PID, guard e protocollo rimangono quelli già verificati.
Nessuna impostazione di sistema viene modificata.

Questa modifica elimina un percorso bloccante documentato; non dimostra che
fosse la causa del tentativo fallito. Chrome attende anche l'inizializzazione
dell'adattatore Bluetooth prima di completare l'elenco: il filtro USB non
salta tale attesa ([gestore delle porte nella stessa revisione](https://raw.githubusercontent.com/chromium/chromium/0985600c06a688b9c669e74afde7dacd5aaed047/services/device/serial/serial_port_manager_impl.cc)).
I test qui verificano solo la configurazione e i flussi
simulati; l'esito del selettore e del PONG richiede una sessione reale separata.

Il tentativo Chrome v2-02 ha registrato COM3 in `chrome://device-log` ma il
selettore non ha completato l'elenco. La successiva prova reale di root con
Edge installato ha mostrato COM3 e restituito il suo `getInfo`, senza aprire
la seriale. Per questo l'helper ora sceglie Edge su Windows, con gli stessi
argomenti e un profilo isolato. Registra l'eseguibile scelto; non sostituisce
silenziosamente Edge con Chrome se manca. Altrove resta la selezione originale.
Il risultato del chooser non è ancora una prova di apertura, PONG o preset.
