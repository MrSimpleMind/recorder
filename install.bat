@echo off
echo =====================================
echo Audio Recorder - Installazione Standalone
echo =====================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo.
    echo Installa Python 3.10+ da https://www.python.org/downloads/
    echo IMPORTANTE: Seleziona "Add Python to PATH" durante installazione
    echo.
    pause
    exit /b 1
)

echo [OK] Python trovato
echo.

REM Verifica FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [!] FFmpeg non trovato
    echo.
    echo FFmpeg e richiesto da Whisper per la trascrizione.
    echo.
    echo COME INSTALLARE:
    echo 1. Scarica: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    echo 2. Estrai in C:\ffmpeg
    echo 3. Aggiungi C:\ffmpeg\bin al PATH di sistema
    echo 4. Riavvia questo script
    echo.
    pause
    exit /b 1
)

echo [OK] FFmpeg trovato
echo.

REM Installa dipendenze
echo Installazione dipendenze Python...
echo Questo richiedera 5-10 minuti (scarica ~2 GB)...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [!] ERRORE durante installazione
    echo.
    echo Tentativo fix PyAudio...
    pip install pipwin
    pipwin install pyaudio
    echo.
    echo Retry installazione completa...
    pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo [X] Installazione fallita
    echo.
    echo Contatta supporto o verifica manualmente i log sopra.
    pause
    exit /b 1
)

echo.
echo =====================================
echo [OK] Installazione completata!
echo =====================================
echo.
echo PROSSIMI PASSI:
echo 1. Avvia l'app: doppio click su recorder_app.py
echo 2. Al primo avvio scarichera automaticamente i modelli (~4 GB)
echo 3. Per creare exe: doppio click su build_exe.bat
echo.
echo NOTA: Tutti i dati rimangono sul tuo PC - nessun cloud
echo.
pause
