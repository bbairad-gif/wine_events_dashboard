@echo off
echo Connessione al disco Fastgate via FTP...

:: Apri collegamento FTP in Esplora file
start explorer ftp://192.168.1.254

:: Se serve autentificazione:
:: start explorer ftp://Bobix:qazxswE1!?@192.168.1.254

pause
