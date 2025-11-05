# Audio Recorder & Transcriber - 100% Standalone

Applicazione Windows per registrare, trascrivere e analizzare audio **completamente in locale** con privacy totale.

## 🎯 Caratteristiche

- ✅ Registrazione audio da microfono o sistema (calls, meet, ecc.)
- ✅ Trascrizione automatica con Whisper (modelli locali)
- ✅ Analisi intelligente con GPT4All:
  - **Summary completo** della conversazione
  - **Key points** principali
  - **Action items** e to-do list
- ✅ **100% locale** - nessun cloud, nessun server
- ✅ **Completamente gratuito** e open source
- ✅ **Portable** - exe unico, copiabile su qualsiasi PC
- ✅ **Privacy assoluta** - tutti i dati rimangono sul tuo computer

## 🚀 Quick Start

### Opzione 1: Usa Python (sviluppo)
```batch
1. Doppio click su install.bat
2. Doppio click su recorder_app.py
3. Al primo avvio scarica modelli (~4 GB) automaticamente
```

### Opzione 2: Crea EXE (distribuzione)
```batch
1. Doppio click su install.bat
2. Doppio click su build_exe.bat
3. Usa dist/AudioRecorder.exe su qualsiasi PC
```

## 📋 Requisiti

- **Windows 10/11**
- **Python 3.10+** (solo per sviluppo, non serve per l'exe)
- **RAM**: 8 GB minimo, 16 GB consigliato
- **Spazio**: 6 GB (2 GB librerie + 4 GB modelli)
- **FFmpeg** (solo per sviluppo, incluso nell'exe)

## 🔧 Stack Tecnologico

- **GUI**: PyQt5
- **Audio Recording**: PyAudio
- **Trascrizione**: OpenAI Whisper (locale, modelli quantizzati)
- **Analisi**: GPT4All + Mistral 7B Q4 (4 GB, locale)
- **Packaging**: PyInstaller

## 📁 Struttura Progetto

```
Recorder/
├── recorder_app.py          # App principale
├── requirements.txt         # Dipendenze Python
├── install.bat              # Installer automatico
├── build_exe.bat            # Crea exe standalone
├── README.md                # Questo file
├── .gitignore              
└── Docs/
    ├── SETUP.md             # Istruzioni dettagliate
    └── ARCHITECTURE.md      # Documentazione tecnica
```

## 🎬 Come Usare

1. **Avvia l'app** (exe o Python)
2. **Seleziona dispositivo audio**:
   - Microfono per parlare direttamente
   - VB-CABLE o Stereo Mix per audio sistema (calls)
3. **Scegli qualità trascrizione**:
   - Veloce: 30 sec per 10 min audio
   - **Bilanciata** ✅: 1 min per 10 min audio (consigliata)
   - Alta: 3 min per 10 min audio
   - Massima: 10 min per 10 min audio
4. **Clicca "Inizia Registrazione"**
5. **Parla o avvia call**
6. **Clicca "Stop"** quando finito
7. **Aspetta** trascrizione + analisi (2-8 min)
8. **Salva risultati** in TXT

## 🔒 Privacy & Sicurezza

✅ **Zero Cloud**: Tutti i processi su CPU/GPU locale  
✅ **Nessun tracking**: Nessuna telemetria o log esterni  
✅ **Open Source**: Codice ispezionabile  
✅ **Dati temporanei**: Audio cancellato dopo trascrizione  
✅ **Offline**: Internet serve solo per download iniziale modelli  

## 📊 Performance

### Tempi Reali (Intel i7, 16 GB RAM)
- 10 min audio → 1 min trascrizione + 3 min analisi
- 30 min audio → 3 min trascrizione + 5 min analisi
- 1 ora audio → 6 min trascrizione + 8 min analisi

### Con GPU NVIDIA
- 10x più veloce per trascrizione
- Analisi rimane su CPU (GPT4All)

## ❓ FAQ

### Serve Ollama?
**No.** Questa versione è 100% standalone. GPT4All scarica e gestisce i modelli automaticamente.

### Funziona offline?
**Sì**, dopo il primo avvio (che scarica i modelli). Internet serve solo per download iniziale.

### Posso usare su più PC?
**Sì**, l'exe è portable. Per evitare re-download modelli, copia anche `C:\Users\[User]\.recorder_models\`.

### Come catturare audio da Teams/Zoom?
Installa **VB-CABLE** (gratuito) e usalo come output audio. Dettagli in `Docs/SETUP.md`.

### L'analisi non è buona
Il modello può essere migliorato cambiando LLM. Vedi `Docs/ARCHITECTURE.md` per alternative.

## 🛠️ Troubleshooting

Vedi `Docs/SETUP.md` sezione Troubleshooting.

## 📝 Licenza

Open Source - usa come preferisci.

## 🤝 Contributi

Fork, migliora, condividi. Nessuna restrizione.

---

**Fatto con ❤️ per chi ha bisogno di privacy e controllo totale sui propri dati.**
