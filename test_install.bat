@echo off
echo =====================================
echo Test Rapido Installazione
echo =====================================
echo.

echo [1/5] Test Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python non trovato
    exit /b 1
)
echo [OK] Python trovato
echo.

echo [2/5] Test FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [X] FFmpeg non trovato
    echo Installa da: https://www.gyan.dev/ffmpeg/builds/
    exit /b 1
)
echo [OK] FFmpeg trovato
echo.

echo [3/5] Test PyAudio...
python -c "import pyaudio" 2>nul
if errorlevel 1 (
    echo [X] PyAudio non installato
    echo Esegui: install.bat
    exit /b 1
)
echo [OK] PyAudio OK
echo.

echo [4/5] Test Whisper...
python -c "import whisper" 2>nul
if errorlevel 1 (
    echo [X] Whisper non installato
    echo Esegui: install.bat
    exit /b 1
)
echo [OK] Whisper OK
echo.

echo [5/5] Test GPT4All...
python -c "import gpt4all" 2>nul
if errorlevel 1 (
    echo [X] GPT4All non installato
    echo Esegui: install.bat
    exit /b 1
)
echo [OK] GPT4All OK
echo.

echo =====================================
echo [OK] Tutto pronto!
echo =====================================
echo.
echo Puoi avviare l'app con: python recorder_app.py
echo Oppure creare l'exe con: build_exe.bat
echo.
pause
