@echo off
echo Attivazione SMB1 e accesso guest non sicuro...

:: Abilita SMB1 client
dism /online /enable-feature /featurename:SMB1Protocol /all /norestart

:: Abilita accesso guest non sicuro
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" /v AllowInsecureGuestAuth /t REG_DWORD /d 1 /f

:: Imposta SMB1 come attivo
reg add "HKLM\SYSTEM\CurrentControlSet\Services\mrxsmb10" /v Start /t REG_DWORD /d 2 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v SMB1 /t REG_DWORD /d 1 /f

echo Riavvio necessario per completare la configurazione.
pause

:: Mappa il disco (da eseguire dopo il riavvio)
:: Sostituisci IP, NomeDisco, utente e password se necessario
:: net use Z: \\192.168.1.254\TOSHIBA_ExternalUSB30_1_ca4 /user:Bobix "qazxswE1!?"
