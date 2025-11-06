@echo off
echo =====================================
echo Creazione EXE Standalone
echo =====================================
echo.

REM FIX #6: Verifica che l'app funzioni prima con --version corretto
echo [1/4] Verifica app funzionante...
python recorder_app.py --version
if errorlevel 1 (
    echo.
    echo [!] L'app non funziona correttamente
    echo Prima testa con: python recorder_app.py --version
    echo.
    pause
    exit /b 1
)

echo [OK] App funzionante
echo.

REM Verifica PyInstaller
echo [2/4] Verifica PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installazione PyInstaller...
    pip install pyinstaller
)

echo [OK] PyInstaller pronto
echo.

REM Crea exe
echo [3/4] Creazione eseguibile...
echo Questo richiedera alcuni minuti...
echo.

pyinstaller --onefile --windowed --name="AudioRecorder" recorder_app.py

if errorlevel 1 (
    echo.
    echo [X] ERRORE durante creazione exe
    echo.
    echo Verifica i log sopra per dettagli
    pause
    exit /b 1
)

echo.
echo [4/4] Pulizia file temporanei...
if exist "AudioRecorder.spec" del "AudioRecorder.spec"
if exist "build" rmdir /s /q "build"

echo.
echo =====================================
echo [OK] EXE creato con successo!
echo =====================================
echo.
echo FILE: dist\AudioRecorder.exe
echo DIMENSIONE: ~200 MB
echo.
echo DISTRIBUZIONE:
echo - Copia AudioRecorder.exe dove vuoi
echo - Al primo avvio scarica modelli (~4 GB) in C:\Users\[User]\.recorder_models
echo - Opzionale: copia la cartella .recorder_models per evitare download
echo.
echo IMPORTANTE:
echo - Python NON serve sul PC target
echo - FFmpeg NON serve sul PC target (gia incluso)
echo - 100%% standalone e portabile
echo.
pause
