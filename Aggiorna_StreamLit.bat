@echo off
cd /d %~dp0

echo ===============================
echo   One-Click Push + Deploy (Forzato)
echo ===============================
echo.

:: 1️⃣ Aggiorna dal remoto (merge automatico tenendo i file locali)
git fetch origin
git merge -X ours origin/main -m "Merge automatico con priorità ai file locali"

:: 2️⃣ Aggiungi tutti i file modificati e nuovi
git add .

:: 3️⃣ Commit sempre (anche a vuoto) con data e ora
set commitmsg=Aggiornamento automatico %date% %time%
git commit --allow-empty -m "%commitmsg%"

:: 4️⃣ Push forzato su GitHub
git push origin main --force

if %errorlevel% neq 0 (
    echo ❌ Errore durante il push.
    pause
    exit /b
)

echo.
echo ✅ Push completato! Streamlit Cloud aggiornerà l'app nei prossimi minuti.

 
pause


:: 6️⃣ Apri direttamente la pagina dell’app su Streamlit Cloud
start https://wine-lazio-dashboard.streamlit.app
pause
