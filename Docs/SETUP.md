# Audio Recorder & Transcriber - Setup Standalone

## ARCHITETTURA 100% STANDALONE
✅ Niente server esterni
✅ Niente Ollama da installare
✅ Un solo exe che scarica automaticamente i modelli al primo avvio
✅ Tutto rimane sul tuo PC

---

## PREREQUISITI

### 1. Python 3.10 o superiore
- Scarica: https://www.python.org/downloads/
- **IMPORTANTE**: Durante installazione seleziona **"Add Python to PATH"**

### 2. FFmpeg (richiesto da Whisper)
- Scarica: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
- Estrai in `C:\ffmpeg`
- Aggiungi `C:\ffmpeg\bin` al PATH:
  1. Cerca "Variabili d'ambiente" in Windows
  2. Modifica "Path" nelle variabili di sistema
  3. Aggiungi: `C:\ffmpeg\bin`
  4. Clicca OK e riavvia il CMD

---

## INSTALLAZIONE (Metodo Automatico)

### Passo 1: Installa Dipendenze
Doppio click su `install.bat` nella cartella del progetto.

Aspetta 5-10 minuti (scarica ~2 GB di librerie).

### Passo 2: Test
Doppio click su `recorder_app.py` per avviare l'app.

**Al primo avvio** scaricherà automaticamente:
- Modelli Whisper (~150 MB)
- Modello GPT4All Mistral 7B quantizzato (~4 GB)

Totale spazio necessario: ~5 GB

---

## INSTALLAZIONE (Metodo Manuale)

Se `install.bat` non funziona:

```cmd
cd C:\Users\Matteo\Desktop\Desk\Sviluppo\Recorder
pip install -r requirements.txt
```

**Fix PyAudio** (se da errore):
```cmd
pip install pipwin
pipwin install pyaudio
pip install -r requirements.txt
```

---

## CREAZIONE EXE PORTABLE

### Metodo Automatico
Doppio click su `build_exe.bat` → output in `dist\AudioRecorder.exe`

### Metodo Manuale
```cmd
pip install pyinstaller
pyinstaller --onefile --windowed --name="AudioRecorder" recorder_app.py
```

**Dimensione finale exe**: ~200 MB

**Primo avvio**: scarica modelli (4 GB) in `C:\Users\[User]\.recorder_models\`

**Distribuzione**: Per usare su altro PC, copia:
1. `AudioRecorder.exe`
2. Cartella `.recorder_models` (se vuoi evitare il download)

---

## UTILIZZO

### Interfaccia
1. **Dispositivo Audio**: Scegli microfono o loopback per audio interno
2. **Qualità Trascrizione**:
   - Veloce (tiny): ~30 sec per 10 min audio
   - **Bilanciata (base)**: ~1 min per 10 min audio ✅ CONSIGLIATA
   - Alta (small): ~3 min per 10 min audio
   - Massima (medium): ~10 min per 10 min audio (serve GPU)

### Workflow
1. Clicca "🔴 Inizia Registrazione"
2. Parla o avvia la videochiamata
3. Clicca "⏹ Stop" quando finito
4. Aspetta trascrizione (1-3 min)
5. Aspetta analisi (2-5 min)
6. Clicca "💾 Salva Risultati"

---

## CATTURA AUDIO INTERNO (System Audio)

Per registrare audio da Teams, Zoom, Meet, ecc:

### Opzione 1: VB-CABLE (Consigliata)
1. Scarica: https://vb-audio.com/Cable/
2. Installa e riavvia
3. Windows Settings → Audio → Output → VB-Cable
4. Nell'app: seleziona "CABLE Output" come dispositivo
5. Avvia la call e registra

### Opzione 2: Stereo Mix (se disponibile)
1. Tasto destro icona audio → "Impostazioni audio"
2. "Gestisci dispositivi audio"
3. Abilita "Stereo Mix"
4. Nell'app: seleziona "Stereo Mix"

---

## MODELLI UTILIZZATI

### Whisper (OpenAI)
- **tiny**: 72 MB, veloce, accuratezza 80%
- **base**: 142 MB, bilanciato, accuratezza 85% ✅
- **small**: 461 MB, lento, accuratezza 90%
- **medium**: 1.5 GB, molto lento, accuratezza 95%

### GPT4All
- **Mistral-7B-Instruct Q4**: 4 GB quantizzato
- Qualità eccellente per summary/analisi
- Gira su CPU (richiede 8 GB RAM)

---

## PERFORMANCE

### Hardware Minimo
- CPU: Intel i5 / AMD Ryzen 5 (2016+)
- RAM: 8 GB
- Spazio: 6 GB

### Hardware Consigliato
- CPU: Intel i7 / AMD Ryzen 7
- RAM: 16 GB
- GPU: NVIDIA (opzionale, 10x più veloce)

### Tempi Reali (CPU medio)
- 10 min audio → 1 min trascrizione + 3 min analisi
- 30 min audio → 3 min trascrizione + 5 min analisi
- 1 ora audio → 6 min trascrizione + 8 min analisi

---

## TROUBLESHOOTING

### Errore: "No module named 'pyaudio'"
```cmd
pip install pipwin
pipwin install pyaudio
```

### Errore: "FFmpeg not found"
Verifica che `C:\ffmpeg\bin` sia nel PATH. Riavvia CMD dopo modifica.

### Errore: "Model download failed"
Connessione internet necessaria solo per primo download. Verifica firewall.

### L'analisi è lenta
Normale su CPU. Con GPU NVIDIA installa:
```cmd
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### L'exe non si avvia
1. Testa con `python recorder_app.py` prima
2. Verifica antivirus (può bloccare exe)
3. Usa `--debug all` in PyInstaller per log

---

## PRIVACY & SICUREZZA

✅ **Tutti i dati rimangono sul tuo PC**
- Audio salvato temporaneamente e cancellato dopo trascrizione
- Modelli scaricati in `~/.recorder_models/`
- Nessuna connessione a server esterni dopo setup
- Nessun log inviato a terzi

✅ **Open Source**
- Codice ispezionabile
- Librerie verificate
- Nessuna telemetria

---

## MODELLI ALTERNATIVI

### LLM più leggeri
In `recorder_app.py`, classe `SummaryWorker.__init__()`:

```python
# Sostituisci con:
self.model_name = "orca-mini-3b-gguf2-q4_0.gguf"  # Solo 2 GB
# Oppure:
self.model_name = "gpt4all-falcon-q4_0.gguf"  # 4 GB, più veloce
```

Download automatico al primo avvio.

### Whisper più veloce
Nell'UI, seleziona "Veloce (tiny)" invece di "Bilanciata".

---

## SUPPORTO

Problemi? Controlla `Docs/ARCHITECTURE.md` per dettagli tecnici.
