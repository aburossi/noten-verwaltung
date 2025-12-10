@echo off
:: Wechselt in das Verzeichnis der Datei
cd /d "%~dp0"

echo ==========================================
echo 🔎 Diagnose Start...
echo ==========================================

:: 1. PRÜFUNG: Ist Python da?
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ FEHLER: Der Befehl 'python' wurde nicht gefunden!
    echo.
    echo Das bedeutet meistens, dass Python zwar installiert ist, 
    echo aber nicht im Windows "PATH" registriert wurde.
    echo.
    echo LOESUNG: 
    echo Installieren Sie Python neu und setzen Sie den Haken bei "Add Python to PATH".
    echo.
    pause
    exit
) else (
    echo ✅ Python gefunden.
)

:: 2. INSTALLATION
echo.
echo 📦 Prüfe Bibliotheken (Streamlit, etc.)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ FEHLER bei der Installation der Bibliotheken.
    echo Haben Sie Internetverbindung?
    pause
    exit
)

:: 3. START
echo.
echo 🚀 Starte run_app.py ...
python run_app.py

:: 4. ENDE (Falls die App abstürzt)
echo.
echo ⚠️ Die App wurde beendet. Hier ist die Fehlermeldung (falls vorhanden):
pause