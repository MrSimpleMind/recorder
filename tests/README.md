# Test Suite - Audio Recorder & Transcriber

## Panoramica

Suite completa di unit test per verificare il corretto funzionamento dell'applicazione dopo i bug fix.

## Prerequisiti

Prima di eseguire i test, assicurati che tutte le dipendenze siano installate:

```bash
pip install -r requirements.txt
```

Oppure usa lo script di installazione automatica:
```bash
install.bat
```

## Eseguire i Test

### Tutti i test
```bash
python tests/run_all_tests.py
```

### Test specifici

**Test parsing LLM:**
```bash
python tests/test_parsing.py
```

**Test AudioRecorder:**
```bash
python tests/test_audio_recorder.py
```

## Test Inclusi

### test_parsing.py
Test per il parsing delle risposte GPT4All:
- ✅ Parsing JSON valido
- ✅ Parsing JSON con testo extra
- ✅ Fallback parsing testuale
- ✅ Keyword italiane
- ✅ Gestione action items vuoti
- ✅ Gestione risposte vuote
- ✅ JSON malformato
- ✅ Diversi stili di bullet points
- ✅ Filtro keyword "nessuno"
- ✅ Edge cases (lunghe risposte, unicode, JSON annidati)

**Totale: 15 test**

### test_audio_recorder.py
Test per la classe AudioRecorder:
- ✅ Thread safety del stop_event
- ✅ Metodo stop() funzionante
- ✅ Chiamate multiple a stop() sicure
- ✅ Inizializzazione corretta
- ✅ Ereditarietà da QThread
- ✅ Presenza dei signals

**Totale: 7 test**

## Risultati Attesi

```
Ran 22 tests in X.XXXs

OK
✅ ALL TESTS PASSED!
```

## Note

- I test sono progettati per essere eseguiti senza hardware audio reale
- I test di AudioRecorder verificano solo la logica, non registrano audio effettivamente
- I test di parsing possono essere eseguiti offline senza modelli AI

## Continuous Integration

Questi test sono pronti per essere integrati in un sistema CI/CD come:
- GitHub Actions
- GitLab CI
- Jenkins

Esempio GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python tests/run_all_tests.py
```

## Contribuire

Per aggiungere nuovi test:
1. Crea un nuovo file `test_*.py` nella directory `tests/`
2. Importa `unittest` e le classi da testare
3. Crea classi di test che ereditano da `unittest.TestCase`
4. Esegui `run_all_tests.py` per verificare

## Troubleshooting

**ModuleNotFoundError: No module named 'pyaudio'**
- Installa le dipendenze: `pip install -r requirements.txt`

**QApplication: invalid style override**
- Normale quando si eseguono test senza display grafico
- I test continuano a funzionare correttamente
