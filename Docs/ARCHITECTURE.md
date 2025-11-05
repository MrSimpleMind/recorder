# Architettura Tecnica - Audio Recorder Standalone

## Overview

App desktop standalone che registra audio, trascrive con Whisper, e analizza con GPT4All.

**Zero dipendenze esterne**: Niente server, niente Ollama, niente cloud.

---

## Struttura del Codice

### Classe `AudioRecorder` (QThread)
**Responsabilità**: Registrazione audio in background

**Parametri**:
- `device_index`: ID dispositivo PyAudio
- `sample_rate`: 16000 Hz (ottimale per Whisper)

**Flusso**:
1. Apre stream PyAudio
2. Cattura audio in loop fino a `stop()`
3. Salva in WAV temporaneo
4. Emette `finished(file_path)`

**Note**: Thread separato per non bloccare UI.

---

### Classe `TranscriptionWorker` (QThread)
**Responsabilità**: Trascrizione con Whisper

**Parametri**:
- `audio_file`: Path WAV
- `model_size`: tiny/base/small/medium

**Flusso**:
1. Carica modello (cache in `~/.cache/whisper/`)
2. Esegue `model.transcribe(language="it")`
3. Emette `finished(text)`

**Performance**:
| Modello | Dimensione | Tempo (10 min audio) | Accuratezza |
|---------|-----------|---------------------|-------------|
| tiny    | 72 MB     | ~30 sec             | 80%         |
| base    | 142 MB    | ~1 min              | 85% ✅       |
| small   | 461 MB    | ~3 min              | 90%         |
| medium  | 1.5 GB    | ~10 min             | 95%         |

---

### Classe `SummaryWorker` (QThread)
**Responsabilità**: Analisi con GPT4All

**Parametri**:
- `transcript`: Testo da analizzare
- `model_name`: Default "Mistral-7B-Instruct-v0.2.Q4_0.gguf"

**Flusso**:
1. Verifica se modello esiste in `~/.recorder_models/`
2. Se no, scarica automaticamente (~4 GB)
3. Inizializza GPT4All
4. Genera risposta con prompt strutturato
5. Parse risposta in: summary, key_points, action_items
6. Emette `finished(dict)`

**Prompt Usato**:
```
Analizza questa trascrizione e fornisci un'analisi strutturata.

TRASCRIZIONE:
[testo]

Fornisci:
1. SUMMARY: Riassunto completo (3-5 frasi)
2. KEY POINTS: 3-5 punti chiave
3. ACTION ITEMS: Task emersi (se presenti)
```

**Output**:
```python
{
    "summary": str,           # Riassunto completo
    "key_points": list[str],  # Lista punti chiave
    "action_items": list[str] # Lista to-do
}
```

**Performance**: ~2-5 min su CPU medio (Intel i7)

---

### Classe `RecorderApp` (QMainWindow)
**Responsabilità**: UI e orchestrazione

**Componenti**:
- ComboBox dispositivi audio
- ComboBox qualità trascrizione
- Pulsanti start/stop
- ProgressBar animata
- TextEdit trascrizione
- TextEdit risultati
- Pulsante salvataggio

**Flusso Completo**:
```
1. User click "Inizia Registrazione"
   → AudioRecorder.start()
   → Cattura audio in background

2. User click "Stop"
   → AudioRecorder.stop()
   → Salva WAV temporaneo
   → on_recording_finished(path)

3. Auto: Trascrizione
   → TranscriptionWorker.start()
   → Whisper processa audio
   → on_transcription_finished(text)
   → Mostra in UI

4. Auto: Analisi
   → SummaryWorker.start()
   → GPT4All genera analisi
   → on_summary_finished(dict)
   → Formatta e mostra in UI

5. User: Salvataggio
   → QFileDialog
   → Scrive TXT con timestamp
```

---

## Dipendenze Critiche

### PyAudio
- **Scopo**: Cattura audio da dispositivi
- **Problema Windows**: Manca binary wheel ufficiale
- **Fix**: `pipwin install pyaudio` o usa `sounddevice`

### Whisper (OpenAI)
- **Scopo**: Speech-to-text locale
- **Cache**: `~/.cache/whisper/`
- **GPU**: Usa CUDA se disponibile (10x velocità)
- **Lingue**: Supporta 99+ lingue, default "it"

### GPT4All
- **Scopo**: LLM locale per analisi
- **Modelli**: GGUF quantizzati Q4
- **Cache**: `~/.recorder_models/` (configurabile)
- **CPU Only**: Ottimizzato per inferenza CPU
- **Alternative**:
  - Mistral-7B-Instruct: 4 GB, accurato ✅
  - Orca-Mini-3B: 2 GB, più veloce
  - GPT4All-Falcon: 4 GB, bilanciato

---

## Modifiche Comuni

### Cambiare lingua trascrizione
`TranscriptionWorker.run()`:
```python
result = model.transcribe(self.audio_file, language="en")
```

### Cambiare modello LLM
`SummaryWorker.__init__()`:
```python
self.model_name = "orca-mini-3b-gguf2-q4_0.gguf"  # Più veloce
```

Lista modelli: https://gpt4all.io/index.html

### Personalizzare prompt analisi
`SummaryWorker.run()`, modifica variabile `prompt`:
```python
prompt = f"""Analizza come [stile personalizzato]:
{self.transcript}

Fornisci...
"""
```

### Export JSON
`RecorderApp.save_results()`:
```python
import json

data = {
    "timestamp": datetime.now().isoformat(),
    "transcript": self.transcript_text.toPlainText(),
    "analysis": {
        "summary": results["summary"],
        "key_points": results["key_points"],
        "action_items": results["action_items"]
    }
}

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## PyInstaller: Dettagli Creazione EXE

### Comando Base
```bash
pyinstaller --onefile --windowed --name="AudioRecorder" recorder_app.py
```

**Parametri**:
- `--onefile`: EXE singolo (~200 MB)
- `--windowed`: No console
- `--name`: Nome output

### Hidden Imports
Se l'exe non funziona, aggiungi:
```bash
pyinstaller --onefile --windowed \
  --hidden-import=whisper \
  --hidden-import=gpt4all \
  --name="AudioRecorder" \
  recorder_app.py
```

### Dimensioni
- **EXE**: ~200 MB (Python + PyQt5 + Torch)
- **Primo avvio**: Scarica modelli (~4 GB)
- **Totale finale**: ~4.2 GB

### Distribuzione Completa
```
AudioRecorder_Portable/
├── AudioRecorder.exe        # App
├── .recorder_models/        # Modelli (opzionale, evita download)
│   └── Mistral-7B-Instruct-v0.2.Q4_0.gguf
└── README.txt               # Istruzioni
```

---

## Cache e Storage

### Whisper Models
- **Path**: `C:\Users\[User]\.cache\whisper\`
- **Dimensioni**: 72 MB - 1.5 GB (dipende da modello)
- **Download**: Automatico al primo uso

### GPT4All Models
- **Path**: `C:\Users\[User]\.recorder_models\`
- **Dimensioni**: 2-4 GB (dipende da modello)
- **Download**: Automatico al primo uso
- **Modificabile**: Cambia `MODEL_CACHE_DIR` in codice

### Audio Temporanei
- **Path**: `%TEMP%\[random].wav`
- **Pulizia**: Automatica dopo trascrizione
- **Dimensione**: ~10 MB per 10 min audio

---

## Performance Optimization

### GPU Acceleration (Whisper)
Installa PyTorch con CUDA:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Risultato**: 10x più veloce per trascrizione.

### Ridurre RAM Usage
1. Usa modello Whisper più piccolo (tiny)
2. Usa LLM più leggero (Orca-Mini-3B)
3. Riduci `max_tokens` in GPT4All

### Ridurre Dimensioni EXE
```bash
pyinstaller --onefile --windowed \
  --exclude-module matplotlib \
  --exclude-module scipy \
  recorder_app.py
```

---

## Troubleshooting

### Audio Distorto
- Aumenta `frames_per_buffer` (1024 → 2048)
- Riduci `sample_rate` (16000 → 8000)

### Trascrizione Errata
- Usa modello più grande (medium)
- Verifica qualità registrazione
- Controlla lingua impostata

### GPT4All Crash/Lento
- Verifica RAM libera (serve 8 GB)
- Usa modello più piccolo
- Aumenta timeout

### PyInstaller: EXE Non Funziona
1. Testa con `python recorder_app.py`
2. Controlla antivirus
3. Usa `--debug all` per log:
```bash
pyinstaller --onefile --windowed --debug all recorder_app.py
```

---

## Estensioni Future

### Streaming Transcription
Implementa trascrizione in real-time con Whisper Streaming.

### Speaker Diarization
Identifica chi parla:
```python
from pyannote.audio import Pipeline
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
```

### Multi-lingua Auto-detect
```python
result = model.transcribe(audio_file, language=None)  # Auto-detect
```

### Cloud Backup Opzionale
Aggiungi sync con Google Drive/Dropbox via API.

### Hotkey Globali
```python
from pynput import keyboard
# Start/stop con Ctrl+Shift+R
```

### Dark Mode
```python
app.setStyleSheet("""
    QMainWindow { background-color: #2b2b2b; color: white; }
    QPushButton { background-color: #3c3c3c; }
""")
```

---

## Modelli Alternativi Testati

### LLM
| Modello | Dimensione | Velocità | Qualità |
|---------|-----------|----------|---------|
| Mistral-7B Q4 | 4 GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ ✅ |
| Orca-Mini-3B | 2 GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| GPT4All-Falcon | 4 GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| TinyLlama-1.1B | 1 GB | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### Whisper
| Modello | Dimensione | Velocità | WER |
|---------|-----------|----------|-----|
| tiny | 72 MB | ⭐⭐⭐⭐⭐ | 15% |
| base | 142 MB | ⭐⭐⭐⭐ | 12% ✅ |
| small | 461 MB | ⭐⭐⭐ | 8% |
| medium | 1.5 GB | ⭐⭐ | 5% |

---

## Security & Privacy

✅ **No Network After Setup**: App funziona offline dopo download modelli  
✅ **No Telemetry**: Zero tracking, zero log  
✅ **Local Only**: Dati mai escono dal PC  
✅ **Temp Cleanup**: Audio auto-cancellato  
✅ **Open Source**: Codice auditabile  

---

## License

Open Source - usa come vuoi.
