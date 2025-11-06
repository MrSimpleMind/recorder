"""
Audio Recorder & Transcriber - 100% Standalone
Registra audio, trascrive con Whisper e genera summary con GPT4All (tutto locale)
Version: 2.0.0 - Bug fixes and improvements
"""

import sys
import os
import wave
import tempfile
import threading
import atexit
import logging
import json
from datetime import datetime
from pathlib import Path

import pyaudio
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QTextEdit, QLabel, QComboBox,
                             QProgressBar, QMessageBox, QFileDialog, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
import whisper
from gpt4all import GPT4All


# Path per cache modelli e logs
MODEL_CACHE_DIR = Path.home() / ".recorder_models"
MODEL_CACHE_DIR.mkdir(exist_ok=True)

LOG_DIR = Path.home() / ".recorder_logs"
LOG_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Lista globale dei file temporanei da pulire
_temp_files = []

def cleanup_temp_files():
    """Pulizia file temporanei all'uscita"""
    global _temp_files
    for f in _temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                logger.info(f"Rimosso file temporaneo: {f}")
            except Exception as e:
                logger.warning(f"Impossibile rimuovere {f}: {e}")
    _temp_files.clear()

atexit.register(cleanup_temp_files)


class AudioRecorder(QThread):
    """Thread per registrazione audio - Fixed: resource leaks, memory leak, race condition"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, device_index, sample_rate=16000):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        # FIX #4: Thread-safe stop event invece di bool
        self.stop_event = threading.Event()

    def run(self):
        global _temp_files
        p = None
        stream = None
        temp_path = None

        try:
            logger.info(f"Avvio registrazione, device {self.device_index}, sample_rate {self.sample_rate}")

            p = pyaudio.PyAudio()

            # Verifica che il device sia valido
            try:
                device_info = p.get_device_info_by_index(self.device_index)
                if device_info['maxInputChannels'] == 0:
                    raise ValueError(f"Device {self.device_index} non ha canali di input")
            except (ValueError, OSError) as e:
                raise ValueError(f"Device audio non valido: {e}")

            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )

            # FIX #3: Scrivi direttamente su file invece di accumulare in memoria
            # Crea file temporaneo
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            _temp_files.append(temp_path)  # Registra per cleanup

            logger.info(f"File temporaneo creato: {temp_path}")

            # FIX #2: Usa context manager per wave.open
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)

                # FIX #4: Usa stop_event invece di bool
                # FIX #3: Scrivi direttamente, nessun accumulo in memoria
                frames_written = 0
                while not self.stop_event.is_set():
                    try:
                        data = stream.read(1024, exception_on_overflow=False)
                        wf.writeframes(data)
                        frames_written += 1024
                    except IOError as e:
                        logger.warning(f"Buffer overflow ignorato: {e}")
                        continue

            logger.info(f"Registrazione completata, {frames_written} frame scritti")
            self.finished.emit(temp_path)

        except ValueError as e:
            # Errori di validazione (device non valido, etc.)
            logger.error(f"Errore validazione: {e}")
            self.error.emit(f"Errore: {str(e)}")
        except (IOError, OSError) as e:
            # Errori I/O (file, audio device)
            logger.error(f"Errore I/O registrazione: {e}", exc_info=True)
            self.error.emit(f"Errore I/O: {str(e)}")
        except Exception as e:
            # Altri errori inaspettati
            logger.exception(f"Errore inaspettato durante registrazione")
            self.error.emit(f"Errore registrazione: {str(e)}")
        finally:
            # FIX #1: Sempre chiudi risorse in finally
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                    logger.debug("Stream audio chiuso")
                except:
                    pass

            if p is not None:
                try:
                    p.terminate()
                    logger.debug("PyAudio terminato")
                except:
                    pass

    def stop(self):
        """Ferma la registrazione in modo thread-safe"""
        logger.info("Richiesta stop registrazione")
        self.stop_event.set()


class TranscriptionWorker(QThread):
    """Thread per trascrizione con Whisper - Fixed: exception handling, configurable language"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, audio_file, model_size="base", language="it"):
        super().__init__()
        self.audio_file = audio_file
        self.model_size = model_size
        self.language = language  # FIX #12: Lingua configurabile

    def run(self):
        try:
            logger.info(f"Avvio trascrizione: file={self.audio_file}, model={self.model_size}, lang={self.language}")

            # Verifica che il file esista
            if not os.path.exists(self.audio_file):
                raise FileNotFoundError(f"File audio non trovato: {self.audio_file}")

            self.progress.emit("Caricamento modello Whisper...")
            model = whisper.load_model(self.model_size)
            logger.info(f"Modello Whisper '{self.model_size}' caricato")

            self.progress.emit("Trascrizione in corso...")
            result = model.transcribe(self.audio_file, language=self.language)

            transcript = result["text"].strip()
            logger.info(f"Trascrizione completata, {len(transcript)} caratteri")

            self.finished.emit(transcript)

        except FileNotFoundError as e:
            logger.error(f"File non trovato: {e}")
            self.error.emit(f"File non trovato: {str(e)}")
        except (IOError, OSError) as e:
            logger.error(f"Errore I/O durante trascrizione: {e}", exc_info=True)
            self.error.emit(f"Errore lettura file: {str(e)}")
        except RuntimeError as e:
            # Errori Whisper (CUDA, modello corrotto, etc.)
            logger.error(f"Errore Whisper runtime: {e}", exc_info=True)
            self.error.emit(f"Errore Whisper: {str(e)}")
        except Exception as e:
            logger.exception("Errore inaspettato durante trascrizione")
            self.error.emit(f"Errore trascrizione: {str(e)}")


class SummaryWorker(QThread):
    """Thread per generazione summary con GPT4All - Fixed: JSON parsing, exception handling"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, transcript, model_name="Mistral-7B-Instruct-v0.2.Q4_0.gguf"):
        super().__init__()
        self.transcript = transcript
        self.model_name = model_name
        self.model_path = MODEL_CACHE_DIR / model_name

    def run(self):
        try:
            logger.info(f"Avvio generazione summary, modello={self.model_name}, transcript_len={len(self.transcript)}")

            # Download modello se non esiste
            if not self.model_path.exists():
                self.progress.emit(f"Download modello {self.model_name} (prima volta, ~4 GB)...")
                self.progress.emit("Questo richiederà alcuni minuti...")
                logger.info(f"Download modello {self.model_name} in corso...")
            else:
                self.progress.emit("Caricamento modello GPT4All...")
                logger.info("Modello GPT4All già presente in cache")

            # Inizializza GPT4All
            gpt = GPT4All(
                model_name=self.model_name,
                model_path=str(MODEL_CACHE_DIR),
                allow_download=True
            )
            logger.info("Modello GPT4All inizializzato")

            self.progress.emit("Generazione summary...")

            # FIX #7: Richiedi formato JSON strutturato per parsing più robusto
            prompt = f"""Analizza questa trascrizione e rispondi SOLO con un oggetto JSON valido.
Non aggiungere testo prima o dopo il JSON.

Formato richiesto:
{{
    "summary": "Riassunto completo in 3-5 frasi",
    "key_points": ["punto chiave 1", "punto chiave 2", "punto chiave 3"],
    "action_items": ["task 1", "task 2"]
}}

Se non ci sono action items, usa array vuoto: "action_items": []

TRASCRIZIONE DA ANALIZZARE:
{self.transcript}

Rispondi SOLO con il JSON, in italiano:"""

            response = gpt.generate(
                prompt,
                max_tokens=1000,
                temp=0.7
            )

            logger.debug(f"Risposta GPT4All ricevuta: {response[:200]}...")

            # Parse risposta con fallback
            parsed = self._parse_response(response)
            logger.info("Summary generato con successo")
            self.finished.emit(parsed)

        except (IOError, OSError) as e:
            logger.error(f"Errore I/O durante download/caricamento modello: {e}", exc_info=True)
            self.error.emit(f"Errore caricamento modello: {str(e)}")
        except RuntimeError as e:
            logger.error(f"Errore runtime GPT4All: {e}", exc_info=True)
            self.error.emit(f"Errore GPT4All: {str(e)}")
        except Exception as e:
            logger.exception("Errore inaspettato durante generazione summary")
            self.error.emit(f"Errore generazione summary: {str(e)}")

    def _parse_response(self, text):
        """Estrae summary, key points e action items dalla risposta - FIX #7: JSON parsing"""
        # Prova prima a parsare come JSON
        try:
            # Trova il JSON nella risposta (potrebbe avere testo prima/dopo)
            text = text.strip()

            # Cerca il primo { e l'ultimo }
            start = text.find('{')
            end = text.rfind('}')

            if start != -1 and end != -1:
                json_str = text[start:end+1]
                data = json.loads(json_str)

                # Valida che contenga i campi richiesti
                if "summary" in data and "key_points" in data and "action_items" in data:
                    logger.info("Parsing JSON riuscito")
                    return {
                        "summary": data["summary"].strip() if data["summary"] else "Analisi non disponibile",
                        "key_points": data["key_points"] if data["key_points"] else ["Nessun punto chiave identificato"],
                        "action_items": data["action_items"] if data["action_items"] else []
                    }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing fallito: {e}, uso fallback")
        except Exception as e:
            logger.warning(f"Errore durante parsing JSON: {e}, uso fallback")

        # Fallback: parsing testuale tradizionale
        logger.info("Uso fallback parsing testuale")
        return self._parse_response_fallback(text)

    def _parse_response_fallback(self, text):
        """Fallback parsing testuale se JSON non funziona"""
        lines = text.strip().split('\n')

        summary = ""
        key_points = []
        action_items = []

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Identifica sezioni - più keyword per robustezza
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ["SUMMARY", "RIASSUNTO", "SINTESI", "RIEPILOGO"]):
                current_section = "summary"
                # Se la linea contiene già testo dopo il marker, estrailo
                for keyword in ["SUMMARY:", "RIASSUNTO:", "SINTESI:", "RIEPILOGO:"]:
                    if keyword in line_upper:
                        idx = line_upper.index(keyword) + len(keyword)
                        remaining = line[idx:].strip()
                        if remaining:
                            summary += remaining + " "
                continue
            elif any(keyword in line_upper for keyword in ["KEY POINT", "PUNTI CHIAVE", "PUNTI PRINCIPALI"]):
                current_section = "key_points"
                continue
            elif any(keyword in line_upper for keyword in ["ACTION", "TASK", "TO-DO", "TODO", "AZIONI"]):
                current_section = "action_items"
                continue

            # Rimuovi bullet points e numerazione
            clean_line = line.lstrip('•-*123456789.() \t')

            if current_section == "summary" and clean_line:
                summary += clean_line + " "
            elif current_section == "key_points" and clean_line:
                # Ignora linee che sono solo keyword
                if clean_line.upper() not in ["KEY POINTS", "PUNTI CHIAVE"]:
                    key_points.append(clean_line)
            elif current_section == "action_items" and clean_line:
                # Ignora "nessuno", "none", etc.
                if not any(skip in clean_line.lower() for skip in ["nessun", "none", "n/a", "non applicabile"]):
                    action_items.append(clean_line)

        # Fallback finale: se parsing non ha funzionato, metti tutto nel summary
        if not summary and not key_points:
            logger.warning("Fallback totale: tutto in summary")
            summary = text

        return {
            "summary": summary.strip() or "Analisi non disponibile",
            "key_points": key_points if key_points else ["Nessun punto chiave identificato"],
            "action_items": action_items if action_items else []
        }


class RecorderApp(QMainWindow):
    """Finestra principale dell'applicazione - Fixed: closeEvent, validazione, path security"""

    # Lingue supportate per trascrizione
    LANGUAGES = [
        ("Italiano", "it"),
        ("English", "en"),
        ("Español", "es"),
        ("Français", "fr"),
        ("Deutsch", "de"),
        ("Português", "pt"),
        ("中文", "zh"),
        ("日本語", "ja"),
        ("한국어", "ko"),
        ("Русский", "ru")
    ]

    def __init__(self):
        super().__init__()
        logger.info("Inizializzazione RecorderApp")
        self.recorder_thread = None
        self.transcription_worker = None
        self.summary_worker = None
        self.current_audio_file = None
        self.init_ui()
        self.load_audio_devices()
        logger.info("RecorderApp inizializzata")
        
    def init_ui(self):
        self.setWindowTitle("Audio Recorder & Transcriber - Standalone v2.0")
        self.setGeometry(100, 100, 900, 750)

        # Widget centrale
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Selezione dispositivo audio
        device_layout = QHBoxLayout()
        device_label = QLabel("Dispositivo Audio:")
        self.device_combo = QComboBox()
        device_layout.addWidget(device_label)
        device_layout.addWidget(self.device_combo)
        layout.addLayout(device_layout)

        # FIX #12: Selezione lingua trascrizione
        language_layout = QHBoxLayout()
        language_label = QLabel("Lingua Trascrizione:")
        self.language_combo = QComboBox()
        for lang_name, lang_code in self.LANGUAGES:
            self.language_combo.addItem(lang_name, lang_code)
        self.language_combo.setCurrentIndex(0)  # Default: Italiano
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)

        # Modello Whisper
        model_layout = QHBoxLayout()
        model_label = QLabel("Qualità Trascrizione:")
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "Veloce (tiny)",
            "Bilanciata (base) - Consigliata",
            "Alta (small)",
            "Massima (medium)"
        ])
        self.model_combo.setCurrentIndex(1)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Pulsanti controllo
        btn_layout = QHBoxLayout()
        self.btn_record = QPushButton("🔴 Inizia Registrazione")
        self.btn_record.setStyleSheet("font-size: 14px; padding: 10px;")
        self.btn_record.clicked.connect(self.toggle_recording)
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setStyleSheet("font-size: 14px; padding: 10px;")
        self.btn_stop.clicked.connect(self.stop_recording)
        self.btn_stop.setEnabled(False)
        btn_layout.addWidget(self.btn_record)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("✅ Pronto - 100% Locale & Privato")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 12px; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Area trascrizione
        transcript_label = QLabel("📝 TRASCRIZIONE:")
        transcript_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(transcript_label)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setPlaceholderText("La trascrizione apparirà qui...")
        layout.addWidget(self.transcript_text)
        
        # Area risultati
        results_label = QLabel("🔍 ANALISI:")
        results_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Summary, key points e action items appariranno qui...")
        layout.addWidget(self.results_text)
        
        # Pulsante salvataggio
        self.btn_save = QPushButton("💾 Salva Risultati")
        self.btn_save.setStyleSheet("font-size: 13px; padding: 8px;")
        self.btn_save.clicked.connect(self.save_results)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)
        
    def load_audio_devices(self):
        """Carica lista dispositivi audio disponibili - Fixed: better error handling"""
        p = None
        try:
            logger.info("Caricamento dispositivi audio...")
            p = pyaudio.PyAudio()
            device_count = 0
            for i in range(p.get_device_count()):
                try:
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_name = info.get('name', f'Device {i}')
                        self.device_combo.addItem(device_name, i)
                        device_count += 1
                        logger.debug(f"Device trovato: {device_name} (index {i})")
                except (OSError, ValueError) as e:
                    logger.warning(f"Impossibile leggere device {i}: {e}")
                    continue

            logger.info(f"Trovati {device_count} dispositivi audio")

            if device_count == 0:
                logger.warning("Nessun dispositivo audio di input trovato")
                QMessageBox.warning(
                    self,
                    "Attenzione",
                    "Nessun dispositivo audio trovato!\n\nVerifica che il microfono sia collegato."
                )

        except (IOError, OSError) as e:
            logger.error(f"Errore I/O durante caricamento dispositivi audio: {e}", exc_info=True)
            QMessageBox.critical(self, "Errore", f"Impossibile accedere ai dispositivi audio: {str(e)}")
        except Exception as e:
            logger.exception("Errore inaspettato durante caricamento dispositivi audio")
            QMessageBox.critical(self, "Errore", f"Impossibile caricare dispositivi audio: {str(e)}")
        finally:
            if p is not None:
                try:
                    p.terminate()
                except:
                    pass
        
    def toggle_recording(self):
        if self.recorder_thread is None or not self.recorder_thread.isRunning():
            self.start_recording()
        
    def start_recording(self):
        """Avvia registrazione con validazione device - FIX #13"""
        device_index = self.device_combo.currentData()

        if device_index is None:
            logger.warning("Tentativo di avviare registrazione senza device selezionato")
            QMessageBox.warning(self, "Errore", "Seleziona un dispositivo audio")
            return

        # FIX #13: Verifica che il device sia ancora valido e disponibile
        p = None
        try:
            p = pyaudio.PyAudio()
            device_info = p.get_device_info_by_index(device_index)

            if device_info['maxInputChannels'] == 0:
                raise ValueError("Il dispositivo non ha canali di input disponibili")

            logger.info(f"Device validato: {device_info.get('name')} (index {device_index})")

        except (ValueError, OSError) as e:
            logger.error(f"Device non valido: {e}")
            QMessageBox.critical(
                self,
                "Errore",
                f"Dispositivo audio non valido o non disponibile:\n{str(e)}\n\nRicarica la lista dei dispositivi."
            )
            return
        finally:
            if p is not None:
                try:
                    p.terminate()
                except:
                    pass

        # Avvia registrazione
        logger.info("Avvio thread di registrazione")
        self.recorder_thread = AudioRecorder(device_index)
        self.recorder_thread.finished.connect(self.on_recording_finished)
        self.recorder_thread.error.connect(self.on_error)
        self.recorder_thread.start()

        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("🔴 Registrazione in corso...")
        self.status_label.setStyleSheet("font-size: 12px; padding: 5px; color: red; font-weight: bold;")
        self.transcript_text.clear()
        self.results_text.clear()
        self.btn_save.setEnabled(False)
        
    def stop_recording(self):
        if self.recorder_thread and self.recorder_thread.isRunning():
            self.recorder_thread.stop()
            self.btn_stop.setEnabled(False)
            self.status_label.setText("⏳ Salvataggio registrazione...")
            self.status_label.setStyleSheet("font-size: 12px; padding: 5px;")
            
    def on_recording_finished(self, audio_file):
        """Callback registrazione completata - avvia trascrizione con lingua selezionata"""
        self.current_audio_file = audio_file
        self.btn_record.setEnabled(True)
        self.status_label.setText("✅ Registrazione salvata. Avvio trascrizione...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminato

        logger.info(f"Registrazione completata: {audio_file}")

        # Avvia trascrizione
        model_mapping = {
            0: "tiny",
            1: "base",
            2: "small",
            3: "medium"
        }
        model_size = model_mapping.get(self.model_combo.currentIndex(), "base")

        # FIX #12: Passa la lingua selezionata
        language_code = self.language_combo.currentData()
        logger.info(f"Avvio trascrizione con model={model_size}, language={language_code}")

        self.transcription_worker = TranscriptionWorker(audio_file, model_size, language_code)
        self.transcription_worker.finished.connect(self.on_transcription_finished)
        self.transcription_worker.error.connect(self.on_error)
        self.transcription_worker.progress.connect(self.update_status)
        self.transcription_worker.start()
        
    def on_transcription_finished(self, transcript):
        self.transcript_text.setText(transcript)
        self.update_status("✅ Trascrizione completata. Generazione analisi...")
        
        # Avvia summary
        self.summary_worker = SummaryWorker(transcript)
        self.summary_worker.finished.connect(self.on_summary_finished)
        self.summary_worker.error.connect(self.on_error)
        self.summary_worker.progress.connect(self.update_status)
        self.summary_worker.start()
        
    def on_summary_finished(self, results):
        # Formatta risultati
        output = "📝 SUMMARY\n"
        output += "=" * 80 + "\n"
        output += results.get("summary", "N/A") + "\n\n"
        
        output += "🔑 KEY POINTS\n"
        output += "=" * 80 + "\n"
        for point in results.get("key_points", []):
            output += f"• {point}\n"
        output += "\n"
        
        output += "✅ ACTION ITEMS\n"
        output += "=" * 80 + "\n"
        action_items = results.get("action_items", [])
        if action_items:
            for item in action_items:
                output += f"☐ {item}\n"
        else:
            output += "Nessun action item identificato\n"
        
        self.results_text.setText(output)
        self.progress_bar.setVisible(False)
        self.update_status("✅ Completato! - Tutti i dati rimangono sul tuo PC")
        self.btn_save.setEnabled(True)
        
        # Pulizia file temporaneo
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.remove(self.current_audio_file)
            except:
                pass
                
    def on_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Errore")
        self.status_label.setStyleSheet("font-size: 12px; padding: 5px; color: red;")
        QMessageBox.critical(self, "Errore", error_msg)
        self.btn_record.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
    def update_status(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("font-size: 12px; padding: 5px;")
        
    def save_results(self):
        """Salva risultati con validazione path - FIX #9"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"recording_{timestamp}.txt"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva Risultati",
            default_name,
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                # FIX #9: Validazione e sanitizzazione path
                file_path = os.path.abspath(file_path)

                # Verifica che il path sia in una directory scrivibile
                parent_dir = os.path.dirname(file_path)
                if not os.path.exists(parent_dir):
                    raise ValueError(f"Directory non esistente: {parent_dir}")

                if not os.access(parent_dir, os.W_OK):
                    raise ValueError(f"Directory non scrivibile: {parent_dir}")

                # Aggiungi estensione .txt se mancante
                if not file_path.endswith('.txt'):
                    file_path += '.txt'

                logger.info(f"Salvataggio risultati in: {file_path}")

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("AUDIO RECORDER & TRANSCRIBER - ANALISI\n")
                    f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")

                    f.write("TRASCRIZIONE\n")
                    f.write("=" * 80 + "\n")
                    f.write(self.transcript_text.toPlainText())
                    f.write("\n\n")
                    f.write(self.results_text.toPlainText())

                logger.info("Risultati salvati con successo")
                QMessageBox.information(self, "Successo", f"Risultati salvati in:\n{file_path}")

            except ValueError as e:
                logger.error(f"Path non valido: {e}")
                QMessageBox.critical(self, "Errore", f"Path non valido:\n{str(e)}")
            except (IOError, OSError) as e:
                logger.error(f"Errore I/O durante salvataggio: {e}", exc_info=True)
                QMessageBox.critical(self, "Errore", f"Impossibile salvare il file:\n{str(e)}")
            except Exception as e:
                logger.exception("Errore inaspettato durante salvataggio")
                QMessageBox.critical(self, "Errore", f"Impossibile salvare: {str(e)}")

    def closeEvent(self, event):
        """Gestisce chiusura app - ferma thread attivi - FIX #14"""
        logger.info("Chiusura applicazione richiesta")

        threads_to_stop = []

        # Ferma thread di registrazione
        if self.recorder_thread and self.recorder_thread.isRunning():
            logger.info("Fermando thread di registrazione...")
            threads_to_stop.append(("Registrazione", self.recorder_thread, True))

        # Ferma thread di trascrizione
        if self.transcription_worker and self.transcription_worker.isRunning():
            logger.info("Fermando thread di trascrizione...")
            threads_to_stop.append(("Trascrizione", self.transcription_worker, False))

        # Ferma thread di summary
        if self.summary_worker and self.summary_worker.isRunning():
            logger.info("Fermando thread di summary...")
            threads_to_stop.append(("Summary", self.summary_worker, False))

        # Ferma tutti i thread
        for name, thread, use_stop in threads_to_stop:
            try:
                if use_stop:
                    # Per AudioRecorder usa il metodo stop()
                    thread.stop()
                else:
                    # Per altri thread usa terminate()
                    thread.terminate()

                # Aspetta max 3 secondi
                if not thread.wait(3000):
                    logger.warning(f"Thread {name} non si è fermato entro 3 secondi")
                    thread.terminate()  # Force terminate
                else:
                    logger.info(f"Thread {name} fermato correttamente")
            except Exception as e:
                logger.error(f"Errore fermando thread {name}: {e}")

        # Cleanup file temporanei
        cleanup_temp_files()

        logger.info("Applicazione chiusa")
        event.accept()


def main():
    # FIX #6: Supporto --version per build_exe.bat
    if len(sys.argv) > 1 and sys.argv[1] in ["--version", "-v"]:
        print("Audio Recorder & Transcriber v2.0.0")
        print("100% Standalone - Local AI Transcription")
        sys.exit(0)

    logger.info("=== Avvio Audio Recorder & Transcriber v2.0 ===")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Stile moderno
    window = RecorderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
