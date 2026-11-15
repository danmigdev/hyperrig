# Lettura diagnostica del codec MINI

`read16.c` aggiunge letture finite al bus ricostruito. Non invia valori ai
registri codec: la fase write contiene soltanto indirizzo dispositivo e
indirizzo registro. Il chiamante possiede PA1/PA2, configura il bus e fornisce
callback con durata finita. Non vengono cambiati MCLK, ALNK, reset o mute.

```powershell
python -B -X utf8 firmware/mini/codec_probe/verify.py
```

Produce `build/mini-codec-probe/read16.pi32v2.o` e `manifest.json`.
Il decoder host osserva fronti GPIO, byte trasmessi, due START, quattro ACK
slave, due byte ricevuti, ACK/NACK master e STOP. Verifica tutti i 65536 valori
possibili sotto ASan/UBSan, ogni registro dell'allowlist e ogni possibile
errore di timing/lettura della transazione. Queste sono prove software;
non simulano tensioni, ritardi elettrici o il componente fisico.

L'allowlist comprende `01,03,1C,1D,2B,2C,31,32,58,59`. Il protocollo è
`START 36 reg_hi reg_lo repeated-START 37 data_hi ACK data_lo NACK STOP`,
con byte più significativo per primo. Il valore viene pubblicato solo dopo
due byte completi e STOP riuscito; su errore rimane invariato. Il risultato
conserva errore principale, errore di cleanup, numero di ACK, byte e campioni.
SDA resta rilasciata dopo l'ACK del read-address e durante il NACK finale.
Non ci sono retry o loop in attesa del codec; al massimo 20 letture SDA e
193 callback delay. Un callback che non termina resta responsabilità del
chiamante. Il cleanup dopo errore è un tentativo, non prova uno STOP elettrico.

La sequenza è documentata da Nuvoton, [NAU88L21 rev.3.1, §7.4 pagina35](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21_DataSheet_EN_Rev3.1.pdf).
Il [datasheet NAU88L21C rev.1.6, pagina69](https://www.nuvoton.com/export/resource-files/en-us--DS_NAU88L21C_DataSheet_EN_Rev1.6.pdf)
definisce `0x58` ID/stato e `0x59` stato RAM/mute in sola lettura. Non accede
a registri clear IRQ, fuse, OTP o test. La costante software-ID `00` compare
nelle documentazioni L21 e L21C: non viene usata per distinguerli.
Il [driver Nuvoton/Linux v6.12](https://raw.githubusercontent.com/torvalds/linux/v6.12/sound/soc/codecs/nau8821.h)
conferma per `0x58` KEYDET bit7, MICDET bit6 e software-ID bit1:0.
Le fonti sono documentarie; il verificatore non scarica né richiede i PDF.

Un NACK in ROM **non prova l'assenza del codec**: alimentazione, reset e MCLK
sono ereditati. Leggere i campi di clock non misura MCLK/BCLK/LRCK, né verifica
48kHz. Il componente non contiene un plugin USB/ROM; il wrapper deve gestire
snapshot/ripristino dei soli GPIO posseduti e conservare i valori grezzi e gli
errori. Nessuna identità fisica o prova audio è dichiarata da questi test.
