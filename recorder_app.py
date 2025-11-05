"""
Audio Recorder & Transcriber - 100% Standalone
Registra audio, trascrive con Whisper e genera summary con GPT4All (tutto locale)
"""

import sys
import os
import wave
import tempfile
import threading
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


# Path per cache modelli
MODEL_CACHE_DIR = Path.home() / ".recorder_models"
MODEL_CACHE_DIR.mkdir(exist_ok=True)


class AudioRecorder(QThread):
    """Thread per registrazione audio"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, device_index, sample_rate=16000):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.recording = True
        self.frames = []
        
    def run(self):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            
            while self.recording:
                data = stream.read(1024, exception_on_overflow=False)
                self.frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Salva in file temporaneo
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            self.finished.emit(temp_path)
            
        except Exception as e:
            self.error.emit(f"Errore registrazione: {str(e)}")
    
    def stop(self):
        self.recording = False


class TranscriptionWorker(QThread):
    """Thread per trascrizione con Whisper"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, audio_file, model_size="base"):
        super().__init__()
        self.audio_file = audio_file
        self.model_size = model_size
        
    def run(self):
        try:
            self.progress.emit("Caricamento modello Whisper...")
            model = whisper.load_model(self.model_size)
            
            self.progress.emit("Trascrizione in corso...")
            result = model.transcribe(self.audio_file, language="it")
            
            self.finished.emit(result["text"])
            
        except Exception as e:
            self.error.emit(f"Errore trascrizione: {str(e)}")


class SummaryWorker(QThread):
    """Thread per generazione summary con GPT4All"""
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
            # Download modello se non esiste
            if not self.model_path.exists():
                self.progress.emit(f"Download modello {self.model_name} (prima volta, ~4 GB)...")
                self.progress.emit("Questo richiederà alcuni minuti...")
            else:
                self.progress.emit("Caricamento modello GPT4All...")
            
            # Inizializza GPT4All
            gpt = GPT4All(
                model_name=self.model_name,
                model_path=str(MODEL_CACHE_DIR),
                allow_download=True
            )
            
            self.progress.emit("Generazione summary...")
            
            prompt = f"""Analizza questa trascrizione e fornisci un'analisi strutturata.

TRASCRIZIONE:
{self.transcript}

Fornisci:
1. SUMMARY: Riassunto completo e dettagliato (3-5 frasi)
2. KEY POINTS: 3-5 punti chiave principali
3. ACTION ITEMS: Task e to-do emersi (se presenti, altrimenti scrivi "Nessuno")

Rispondi in italiano, in modo chiaro e conciso."""

            response = gpt.generate(
                prompt,
                max_tokens=1000,
                temp=0.7
            )
            
            # Parse risposta
            parsed = self._parse_response(response)
            self.finished.emit(parsed)
            
        except Exception as e:
            self.error.emit(f"Errore generazione summary: {str(e)}")
    
    def _parse_response(self, text):
        """Estrae summary, key points e action items dalla risposta"""
        lines = text.strip().split('\n')
        
        summary = ""
        key_points = []
        action_items = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identifica sezioni
            if "SUMMARY" in line.upper() or "RIASSUNTO" in line.upper():
                current_section = "summary"
                continue
            elif "KEY POINT" in line.upper() or "PUNTI CHIAVE" in line.upper():
                current_section = "key_points"
                continue
            elif "ACTION" in line.upper() or "TASK" in line.upper() or "TO-DO" in line.upper():
                current_section = "action_items"
                continue
            
            # Rimuovi bullet points e numerazione
            clean_line = line.lstrip('•-*123456789.() ')
            
            if current_section == "summary" and clean_line:
                summary += clean_line + " "
            elif current_section == "key_points" and clean_line:
                key_points.append(clean_line)
            elif current_section == "action_items" and clean_line:
                if "nessun" not in clean_line.lower():
                    action_items.append(clean_line)
        
        # Fallback: se parsing non ha funzionato, metti tutto nel summary
        if not summary and not key_points:
            summary = text
        
        return {
            "summary": summary.strip() or "Analisi non disponibile",
            "key_points": key_points if key_points else ["Analisi in corso..."],
            "action_items": action_items if action_items else []
        }


class RecorderApp(QMainWindow):
    """Finestra principale dell'applicazione"""
    
    def __init__(self):
        super().__init__()
        self.recorder_thread = None
        self.current_audio_file = None
        self.init_ui()
        self.load_audio_devices()
        
    def init_ui(self):
        self.setWindowTitle("Audio Recorder & Transcriber - Standalone")
        self.setGeometry(100, 100, 900, 700)
        
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
        """Carica lista dispositivi audio disponibili"""
        try:
            p = pyaudio.PyAudio()
            device_count = 0
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    self.device_combo.addItem(info['name'], i)
                    device_count += 1
            p.terminate()
            
            if device_count == 0:
                QMessageBox.warning(
                    self, 
                    "Attenzione", 
                    "Nessun dispositivo audio trovato!\n\nVerifica che il microfono sia collegato."
                )
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare dispositivi audio: {str(e)}")
        
    def toggle_recording(self):
        if self.recorder_thread is None or not self.recorder_thread.isRunning():
            self.start_recording()
        
    def start_recording(self):
        device_index = self.device_combo.currentData()
        if device_index is None:
            QMessageBox.warning(self, "Errore", "Seleziona un dispositivo audio")
            return
        
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
        self.current_audio_file = audio_file
        self.btn_record.setEnabled(True)
        self.status_label.setText("✅ Registrazione salvata. Avvio trascrizione...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminato
        
        # Avvia trascrizione
        model_mapping = {
            0: "tiny",
            1: "base",
            2: "small",
            3: "medium"
        }
        model_size = model_mapping.get(self.model_combo.currentIndex(), "base")
        
        self.transcription_worker = TranscriptionWorker(audio_file, model_size)
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
                
                QMessageBox.information(self, "Successo", f"Risultati salvati in:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile salvare: {str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Stile moderno
    window = RecorderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
