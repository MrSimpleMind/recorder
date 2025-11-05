# 🚀 Quick Start - 5 Minuti

## Installazione Express

### 1. Installa Python
- Vai su: https://www.python.org/downloads/
- Scarica Python 3.10 o superiore
- **IMPORTANTE**: Durante installazione, seleziona "Add Python to PATH"
- Clicca Install

### 2. Installa FFmpeg
- Vai su: https://www.gyan.dev/ffmpeg/builds/
- Scarica "ffmpeg-release-essentials.zip"
- Estrai in `C:\ffmpeg`
- Aggiungi al PATH:
  1. Cerca "Variabili d'ambiente" in Windows
  2. Modifica "Path" → Nuovo → `C:\ffmpeg\bin`
  3. OK e chiudi tutto

### 3. Installa App
Doppio click su: **`install.bat`**

Aspetta 10 minuti mentre scarica le librerie (~2 GB).

### 4. Test Installazione
Doppio click su: **`test_install.bat`**

Se tutto OK, vai al passo 5.

### 5. Avvia App
Doppio click su: **`recorder_app.py`**

**Al primo avvio** scaricherà automaticamente i modelli GPT4All (~4 GB).  
Aspetta 5-10 minuti.

---

## Primo Utilizzo

1. **Seleziona Dispositivo Audio**
   - Per parlare: scegli il tuo microfono
   - Per registrare calls: installa VB-CABLE e selezionalo

2. **Qualità Trascrizione**
   - Lascia su "Bilanciata (base)" (consigliato)

3. **Clicca 🔴 Inizia Registrazione**

4. **Parla** per almeno 10 secondi

5. **Clicca ⏹ Stop**

6. **Aspetta** trascrizione + analisi (2-5 min)

7. **Leggi** i risultati e clicca 💾 Salva se ti piace

---

## Registrare Audio da Teams/Zoom/Meet

### Metodo 1: VB-CABLE (Più Affidabile)

1. **Scarica VB-CABLE**
   - Vai su: https://vb-audio.com/Cable/
   - Clicca "Download"
   - Estrai e installa `VBCABLE_Setup_x64.exe`
   - Riavvia il PC

2. **Configura Windows**
   - Tasto destro su icona audio (barra notifiche)
   - "Impostazioni audio"
   - Output → Seleziona "CABLE Input"

3. **Nell'App**
   - Dispositivo Audio → "CABLE Output"

4. **Avvia Call e Registra**
   - Apri Teams/Zoom/Meet
   - Avvia call
   - Nell'app clicca Inizia Registrazione
   - Al termine clicca Stop

5. **Ripristina Audio Normale**
   - Windows → Output → Torna a Speakers/Cuffie

### Metodo 2: Stereo Mix (Se Disponibile)

1. Tasto destro icona audio → "Impostazioni audio"
2. "Gestisci dispositivi audio" → Abilita "Stereo Mix"
3. Nell'app: seleziona "Stereo Mix"
4. Registra

**Nota**: Stereo Mix non è disponibile su tutti i PC.

---

## Creare EXE Portable

Doppio click su: **`build_exe.bat`**

L'exe sarà in `dist\AudioRecorder.exe` (~200 MB).

**Per usare su altro PC**:
1. Copia `AudioRecorder.exe`
2. Primo avvio: scarica modelli automaticamente
3. Opzionale: copia `C:\Users\[User]\.recorder_models\` per evitare download

---

## Problemi Comuni

### "Python non trovato"
Reinstalla Python e seleziona "Add Python to PATH".

### "FFmpeg non trovato"
Verifica che `C:\ffmpeg\bin` sia nel PATH e riavvia CMD.

### "Errore PyAudio"
```cmd
pip install pipwin
pipwin install pyaudio
```

### "App lenta"
Normale su CPU. Usa modello Whisper "Veloce (tiny)" per velocizzare.

### "Nessun dispositivo audio"
Verifica che il microfono sia collegato e abilitato in Windows.

---

## Supporto

Vedi documentazione completa in `Docs/SETUP.md`

---

**Fatto! Ora hai un recorder privato e locale al 100%.**
